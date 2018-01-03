#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import pygtk
import gtk
#import gtkdialogs
pygtk.require('2.0')

#PATH = ''
PATH = '/usr/share/howtododialog/'
#gtkrc_file = PATH+'gtk_font_rc'
gladefile = PATH+'howtododialog.xml'

class howtodo_Dialog:
	def __init__(self):

		builder = gtk.Builder()
		builder.add_from_file(gladefile)
		
		self.howtodo_dialog = builder.get_object("howtodo_window")

		self.button_reboot = builder.get_object("button_reboot")
		self.button_shutdown = builder.get_object("button_shutdown")
		self.button_cancel = builder.get_object("button_cancel")
		

		self.button_reboot.connect('clicked', self.howtodo_dialog_reboot)
		self.button_shutdown.connect('clicked', self.howtodo_dialog_shutdown)
		self.button_cancel.connect('clicked', self.howtodo_dialog_quit, self.howtodo_dialog)


		self.howtodo_dialog.set_gravity(gtk.gdk.GRAVITY_SOUTH_EAST)
		width, height = self.howtodo_dialog.get_size()
		self.howtodo_dialog.move(gtk.gdk.screen_width() / 2 - width, gtk.gdk.screen_height() / 2 - height)



		self.howtodo_dialog.set_icon_from_file('/usr/share/pixmaps/staros-shutdown.png')
		self.howtodo_dialog.set_title('关机')
		self.howtodo_dialog.resize(400, 150)
		self.howtodo_dialog.show()

	def howtodo_dialog_reboot(self, widget):
		#for clear screen
		for o in range(1,25):
			print("\n")
		os.system("reboot &")

	def howtodo_dialog_shutdown(self, widget):
		for o in range(1,25):
			print("\n")
		os.system("poweroff &")

	def howtodo_dialog_quit(self, widget, data=None):
		gtk.main_quit()



if __name__ == '__main__':
	system_option_dialog = howtodo_Dialog()
	gtk.main()
