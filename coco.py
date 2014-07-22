#!/usr/bin/env python

import parrot
import signal
import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QApplication, QMenu, QSystemTrayIcon, QAction


class ParrotMenu(QMenu):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.addSection("Parrot Companion")

		# Battery level
		icon = QIcon.fromTheme("battery")
		self.battery = QAction(icon, "Battery: Unknown", self)
		self.battery.setEnabled(False)
		self.addAction(self.battery)

		# Quit
		icon = QIcon.fromTheme("application-exit")
		action = QAction(icon, "&Quit", self)
		action.triggered.connect(lambda: QApplication.exit(0))
		self.addAction(action)


class ParrotTrayIcon(QSystemTrayIcon):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.menu = ParrotMenu()
		self.setContextMenu(self.menu)
		self.activated.connect(lambda: self.menu.show())


if __name__ == "__main__":
	app = QApplication(sys.argv)
	icon = QIcon.fromTheme("audio-headphones")
	tray = ParrotTrayIcon(icon)
	tray.show()

	signal.signal(signal.SIGINT, signal.SIG_DFL)
	app.exec_()
