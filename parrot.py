#!/usr/bin/env python

import bluetooth
import dbus
import logging
import struct
from xml.etree import ElementTree


class ParrotException(Exception):
	pass


class ParrotAPIError(ParrotException):
	pass


class Parrot(object):
	UUID = "0ef0f502-f0ee-46c9-986c-54ed027807fb"

	def __init__(self):
		self.bus = dbus.SystemBus()
		manager = dbus.Interface(self.bus.get_object("org.bluez", "/"), "org.bluez.Manager")
		adapter_path = manager.DefaultAdapter()
		self.adapter = dbus.Interface(self.bus.get_object("org.bluez", adapter_path), "org.bluez.Adapter")

	def _get_mac(self):
		for path in self.adapter.ListDevices():
			device = dbus.Interface(self.bus.get_object("org.bluez", path), "org.bluez.Device")
			properties = device.GetProperties()
			if "Parrot Zik" in properties["Name"]:
				return properties["Address"]
			raise RuntimeError

	def connect(self):
		services = bluetooth.find_service(uuid=self.UUID, address=self._get_mac())
		if not services:
			raise EndangeredSpeciesException("Could not find a Parrot Zik.")
		parrot = services[0]
		print("Connecting: ", parrot["name"], parrot["port"], parrot["host"])

		assert parrot["protocol"] == "RFCOMM"
		socket = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
		socket.connect((parrot["host"], parrot["port"]))
		socket.send(b"\x00\x03\x00")
		data = socket.recv(1024)
		assert data == b"\x00\x03\x02"
		self.sock = socket

	def _request(self, r):
		header = (0, len(r) + 3, 0x80)
		message = struct.pack("3B", *header)
		# Header
		message += bytes(r, "utf-8")
		self.sock.send(message)
		_, sz, *_ = self.sock.recv(7)
		data = self.sock.recv(sz - 7)
		# print(data)
		answer = ElementTree.fromstring(data)
		if answer.attrib.get("error") == "true":
			raise ParrotAPIError("Received an error from Parrot: %r" % (data))
		return answer

	def get(self, path):
		return self._request("GET %s" % (path))

	def set(self, path, value):
		if value is True:
			value = "true"
		elif value is False:
			value = "false"
		return self._request("SET %s?arg=%s" % (path, value))


def enforce_type(func):
	def wrapped(*args, **kwargs):
		ret = func(*args, **kwargs)
		type = func.__annotations__["return"]
		if type is bool:
			return "true" if ret is True else "false"
		elif type is int:
			return int(ret or -1)
		return type(ret)
	return wrapped


def _boolean(path):
	api_path = "/api/" + path

	@enforce_type
	def _getter(self) -> bool:
		e = self.get(api_path + "/enabled/get")
		return e.find(path).attrib["enabled"]

	def _setter(self, value):
		return self.set(api_path + "/enabled/set", value)

	return property(_getter, _setter)


class ParrotZik(Parrot):
	@property
	@enforce_type
	def battery(self) -> int:
		e = self.get("/api/system/battery/get")
		return e.find("system/battery").attrib["level"]

	@property
	def friendly_name(self) -> str:
		e = self.get("/api/bluetooth/friendlyname/get")
		return e.find("bluetooth").attrib["friendlyname"]

	@property
	def version(self) -> str:
		e = self.get("/api/software/version/get")
		return e.find("software").attrib["version"]

	auto_connection = _boolean("system/auto_connection")
	anc_phone_mode = _boolean("system/anc_phone_mode")
	noise_cancellation = _boolean("audio/noise_cancellation")
	specific_mode = _boolean("audio/specific_mode")
	sound_effect = _boolean("audio/sound_effect")


def main():
	parrot = ParrotZik()
	parrot.connect()
	print(parrot.friendly_name)
	print(parrot.version)
	print(parrot.battery)
	print(parrot.auto_connection)

if __name__ == "__main__":
	main()
