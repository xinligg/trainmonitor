import sys
import os
import pygtk
import gtk
#import gtkdialogs
pygtk.require('2.0')

PATH = '/usr/share/weibo/'
HOMEPATH = '/tmp/'
#PATH = '/usr/share/howtododialog/'
#HOMEPATH = os.environ['HOME'] + '/.cache/'
#gtkrc_file = PATH+'gtk_font_rc'
gladefile = PATH+'main.xml'
notes_message=''
PAGES = 6

class main_window:
	def __init__(self):

		builder = gtk.Builder()
		builder.add_from_file(gladefile)
		
		self.main_window = builder.get_object("main_window")

		self.button_send_to_sina = builder.get_object("button_send_to_sina")
		self.notebook = builder.get_object("notebook")
		self.textview1 = builder.get_object("textview1")
		self.textview2 = builder.get_object("textview2")
		self.textview3 = builder.get_object("textview3")
		self.textview4 = builder.get_object("textview4")
		self.textview5 = builder.get_object("textview5")
		self.textview6 = builder.get_object("textview6")
		self.textbuffer1 = builder.get_object("textbuffer1")
		self.textbuffer2 = builder.get_object("textbuffer2")
		self.textbuffer3 = builder.get_object("textbuffer3")
		self.textbuffer4 = builder.get_object("textbuffer4")
		self.textbuffer5 = builder.get_object("textbuffer5")
		self.textbuffer6 = builder.get_object("textbuffer6")
		

		self.main_window.connect('destroy', self.window_destroy)
		self.button_send_to_sina.connect('clicked', self.send_to_sina)
#		self.button_shutdown.connect('clicked', self.howtodo_dialog_shutdown)
#		self.button_cancel.connect('clicked', self.howtodo_dialog_quit, self.howtodo_dialog)


		self.main_window.set_gravity(gtk.gdk.GRAVITY_SOUTH_EAST)
		width, height = self.main_window.get_size()
#		self.howtodo_dialog.move(gtk.gdk.screen_width() / 2 - width, gtk.gdk.screen_height() / 2 - height)
		self.main_window.move(gtk.gdk.screen_width() - width, 0)
		self.load_cache_file()

#		self.main_window.resize(400, 300)
		self.main_window.set_default_size(400, 300)
		self.main_window.set_title('Notes')
		self.main_window.show()

	def send_to_sina(self, widget):
		page_num = self.notebook.get_current_page()
		if page_num == 0:
			message_buffer = self.textview1.get_buffer()
		elif page_num == 1:
			message_buffer = self.textview2.get_buffer()
		elif page_num == 2:
			message_buffer = self.textview3.get_buffer()
		elif page_num == 3:
			message_buffer = self.textview4.get_buffer()
		elif page_num == 4:
			message_buffer = self.textview5.get_buffer()
		elif page_num == 5:
			message_buffer = self.textview6.get_buffer()
		else:
			pass
		notes_message = message_buffer.get_text(message_buffer.get_start_iter(), message_buffer.get_end_iter())
#		notes_message = ''.join(notes_message.split())
		notes_message = notes_message.replace('\r','')
		notes_message = notes_message.replace('\n',' ')
		notes_message = notes_message.replace(' ','%20')
#		for fiter in range(0,len(notes_message)):
#			if notes_message[fiter] == '
#			fileName = fileName.replace('\r','')
#			fileName = fileName.replace('\n','')
#				fileName = fileName[0:-1]
#		print notes_message
		os.system("www-browser http://service.t.sina.com.cn/share/share.php?title="+ notes_message +" &")


	def window_destroy(self, widget):
		self.save_all_change()
		gtk.main_quit()

	def save_all_change(self):
		for page_num in range(6):
			if page_num == 0:
				message_save_text = self.textbuffer1.get_text(self.textbuffer1.get_start_iter(), self.textbuffer1.get_end_iter())
				file(HOMEPATH + 'note1', 'w+').write(message_save_text)
#				file = open("/tmp/note1", "w")
#				file.write(message_save_text)
#				file.close()
			elif page_num == 1:
				message_save_text = self.textbuffer2.get_text(self.textbuffer2.get_start_iter(), self.textbuffer2.get_end_iter())
				file(HOMEPATH + 'note2', 'w+').write(message_save_text)
			elif page_num == 2:
				message_save_text = self.textbuffer3.get_text(self.textbuffer3.get_start_iter(), self.textbuffer3.get_end_iter())
				file(HOMEPATH + 'note3', 'w+').write(message_save_text)
			elif page_num == 3:
				message_save_text = self.textbuffer4.get_text(self.textbuffer4.get_start_iter(), self.textbuffer4.get_end_iter())
				file(HOMEPATH + 'note4', 'w+').write(message_save_text)
			elif page_num == 4:
				message_save_text = self.textbuffer5.get_text(self.textbuffer5.get_start_iter(), self.textbuffer5.get_end_iter())
				file(HOMEPATH + 'note5', 'w+').write(message_save_text)
			elif page_num == 5:
				message_save_text = self.textbuffer6.get_text(self.textbuffer6.get_start_iter(), self.textbuffer6.get_end_iter())
				file(HOMEPATH + 'note6', 'w+').write(message_save_text)
			else:
				pass

	def load_cache_file(self):
		for page_num in range(6):
			if page_num == 0:
				try:
					file = open(HOMEPATH + 'note1', 'r+')
					message_save_text = file.read()
					self.textbuffer1.set_text(message_save_text)
					file.close()
				except:
					pass
			elif page_num == 1:
				try:
					file = open(HOMEPATH + 'note2', 'r+')
					message_save_text = file.read()
					self.textbuffer2.set_text(message_save_text)
					file.close()
				except:
					pass
			elif page_num == 2:
				try:
					file = open(HOMEPATH + 'note3', 'r+')
					message_save_text = file.read()
					self.textbuffer3.set_text(message_save_text)
					file.close()
				except:
					pass
			elif page_num == 3:
				try:
					file = open(HOMEPATH + 'note4', 'r+')
					message_save_text = file.read()
					self.textbuffer4.set_text(message_save_text)
					file.close()
				except:
					pass
			elif page_num == 4:
				try:
					file = open(HOMEPATH + 'note5', 'r+')
					message_save_text = file.read()
					self.textbuffer5.set_text(message_save_text)
					file.close()
				except:
					pass
			elif page_num == 5:
				try:
					file = open(HOMEPATH + 'note6', 'r+')
					message_save_text = file.read()
					self.textbuffer6.set_text(message_save_text)
					file.close()
				except:
					pass
			else:
				pass

if __name__ == '__main__':
	main_window()
	gtk.main()
