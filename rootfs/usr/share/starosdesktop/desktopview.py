#!/usr/bin/python
# -*- coding: utf-8 -*-
# Filename: desktopview.py

import sys
import os
import ConfigParser
import pygtk
import glib
import gtkdialogs
import eyeD3
pygtk.require('2.0')
try:
	import gtk
	import gobject
except:
	print("error: import 'gtk' failed!")
	sys.exit(1)
import commands



#black_listStore = gtk.ListStore(str)
#white_listStore = gtk.ListStore(str)
PATH = '/usr/share/starosdesktop/'
gtkrc_file = PATH+'gtk_font_rc'
gladefile = PATH+'desktop.xml'
screenshot_file = os.environ['HOME'] + '/.cache/bg.png'
etc_file = os.environ['HOME'] + '/.starosdesktop.conf'
#etc_file = '/tmp/.starosdesktop.conf' #for programming test
fengmianfile = '/dev/shm/fengmian.dat'
video_screenshot_file = '/dev/shm/00000001.jpg'
baiduword = '&ch=1&tn=fulide_2_pg&bar='
backgroundrun = ' > /dev/null 2>1 &'
image_none_music_file = PATH+'image_entertainment/none_music.png'
image_has_music_file = PATH+'image_entertainment/has_music.png'
image_none_video_file = PATH+'image_entertainment/none_video.png'
image_has_video_file = PATH+'image_entertainment/has_video.png'
image_none_pic_file = PATH+'image_entertainment/none_pic.png'
image_has_pic_file = PATH+'image_entertainment/has_pic.png'

image_web1_file = PATH+'image_web/265g.jpg'
image_web2_file = PATH+'image_web/m1905.jpg'
image_web3_file = PATH+'image_web/shenzhouzuche.jpg'
image_web4_file = PATH+'image_web/xiecheng.jpg'
image_background_file = PATH+'bg_1366.png'
email_button_name = 'email_button.web_app'
search_button_name = 'search_button'
search_entry_name = 'search_entry'
choose_fileing = 0 #0: not choose file 1:choosing file
#starcenter_button_name = 'starcenter_button'
music_image_list = ['', '', '', '', '', '']
video_image_list = ['', '', '', '', '', '']
picture_image_list = ['', '', '']#, '', '', '']

#music_image_icon_status = [0, 0, 0, 0, 0, 0]
#video_image_icon_status = [0, 0, 0, 0, 0, 0]
#picture_image_icon_status = [0, 0, 0]
music_image_icon_status = [False, False, False, False, False, False]
video_image_icon_status = [False, False, False, False, False, False]
picture_image_icon_status = [False, False, False]

###############
##global data
###############

x = gtk.gdk.screen_width()
y = gtk.gdk.screen_height()

gtk.rc_parse(gtkrc_file)
	

class MainWindow:
#	pixbuf = gtk.gdk.pixbuf_new_from_file(image_background_file)
#	pixbuf = pixbuf.scale_simple(x, y, gtk.gdk.INTERP_HYPER)

	def __init__(self):
#		print('create mainWindow')

		builder = gtk.Builder()
		builder.add_from_file(gladefile)

		self.main_window = builder.get_object("main_window")
		self.alignment = builder.get_object("alignment1")
		self.label_server = builder.get_object("label_server")
		self.label_email = builder.get_object("label_email")
		self.label_netapp = builder.get_object("label_netapp")
		self.label_localapp = builder.get_object("label_localapp")
		self.label_myapp = builder.get_object("label_myapp")
		self.label_website = builder.get_object("label_website")
		self.label_mail = builder.get_object("label_mail")
		self.label_hpintroduce = builder.get_object("label_hpintroduce")
		self.label_music = builder.get_object("label_music")
		self.label_enterainment = builder.get_object("label_enterainment")
		self.label_myapp_text1 = builder.get_object("label_myapp_text1")
		self.label_myapp_text2 = builder.get_object("label_myapp_text2")
		self.label_myapp_text3 = builder.get_object("label_myapp_text3")
		self.label_picture = builder.get_object("label_picture")
		self.button_netapp1 = builder.get_object("button_netapp1")
		self.button_netapp2 = builder.get_object("button_netapp2")
		self.button_netapp3 = builder.get_object("button_netapp3")
		self.button_netapp4 = builder.get_object("button_netapp4")
		self.button_netapp5 = builder.get_object("button_netapp5")
		self.button_netapp6 = builder.get_object("button_netapp6")
		self.button_localapp1 = builder.get_object("button_localapp1")
		self.button_localapp2 = builder.get_object("button_localapp2")
		self.button_localapp3 = builder.get_object("button_localapp3")
		self.button_myapp1 = builder.get_object("button_myapp1")
		self.button_myapp2 = builder.get_object("button_myapp2")
		self.button_myapp3 = builder.get_object("button_myapp3")
		self.image_web1 = builder.get_object("image_web1")
		self.image_web2 = builder.get_object("image_web2")
		self.image_web3 = builder.get_object("image_web3")
		self.image_web4 = builder.get_object("image_web4")
		self.button_web1 = builder.get_object("button_web1")
		self.button_web2 = builder.get_object("button_web2")
		self.button_web3 = builder.get_object("button_web3")
		self.button_web4 = builder.get_object("button_web4")
		self.button_music1 = builder.get_object("button_music1")
		self.button_music2 = builder.get_object("button_music2")
		self.button_music3 = builder.get_object("button_music3")
		self.button_music4 = builder.get_object("button_music4")
		self.button_music5 = builder.get_object("button_music5")
		self.button_music6 = builder.get_object("button_music6")
		self.music_image1 = builder.get_object("music_image1")
		self.music_image2 = builder.get_object("music_image2")
		self.music_image3 = builder.get_object("music_image3")
		self.music_image4 = builder.get_object("music_image4")
		self.music_image5 = builder.get_object("music_image5")
		self.music_image6 = builder.get_object("music_image6")
		self.button_video1 = builder.get_object("button_video1")
		self.button_video2 = builder.get_object("button_video2")
		self.button_video3 = builder.get_object("button_video3")
		self.button_video4 = builder.get_object("button_video4")
		self.button_video5 = builder.get_object("button_video5")
		self.button_video6 = builder.get_object("button_video6")
		self.video_image1 = builder.get_object("video_image1")
		self.video_image2 = builder.get_object("video_image2")
		self.video_image3 = builder.get_object("video_image3")
		self.video_image4 = builder.get_object("video_image4")
		self.video_image5 = builder.get_object("video_image5")
		self.video_image6 = builder.get_object("video_image6")
		self.button_pic1 = builder.get_object("button_pic1")
		self.button_pic2 = builder.get_object("button_pic2")
		self.button_pic3 = builder.get_object("button_pic3")
		self.pic_image1 = builder.get_object("pic_image1")
		self.pic_image2 = builder.get_object("pic_image2")
		self.pic_image3 = builder.get_object("pic_image3")
		self.button_music_launcher = builder.get_object("button_music_launcher")
		self.button_video_launcher = builder.get_object("button_video_launcher")
		self.button_pic_launcher = builder.get_object("button_pic_launcher")
		self.entry = builder.get_object("entry")
		self.button_search = builder.get_object("button_search")
		self.button_email = builder.get_object("button_email")
		self.button_search = builder.get_object("button_search")
#		self.button_starcenter = builder.get_object("button_starcenter")

		self.music_image = [self.music_image1, self.music_image2, self.music_image3, self.music_image4, self.music_image5, self.music_image6]
		self.video_image = [self.video_image1, self.video_image2, self.video_image3, self.video_image4, self.video_image5, self.video_image6]
		self.pic_image = [self.pic_image1, self.pic_image2, self.pic_image3]

		builder.connect_signals(self)

		self.button_email.set_name(email_button_name)
		self.button_search.set_name(search_button_name)
#		self.button_starcenter.set_name(starcenter_button_name)
		self.entry.set_name(search_entry_name)
		self.label_server.set_name('label_server')
		self.label_server.set_size_request(int(x / 3.5), -1)
		self.label_email.set_name('label_server')
		self.label_netapp.set_name('label_netapp.label_title')
		self.label_localapp.set_name('label_localapp.label_title')
		self.label_myapp.set_name('label_myapp.label_title')
		self.label_website.set_name('label_website.label_title')
		self.label_mail.set_name('label_mail.label_title')
		self.label_hpintroduce.set_name('label_hpintroduce.label_title')
		self.label_music.set_name('label_music.label_title')
		self.label_enterainment.set_name('label_enterainment.label_title')
		self.label_picture.set_name('label_picture.label_title')

		self.button_netapp1.set_name('button_netapp1.app_button')
		self.button_netapp2.set_name('button_netapp2.app_button')
		self.button_netapp3.set_name('button_netapp3.app_button')
		self.button_netapp4.set_name('button_netapp4.app_button')
		self.button_netapp5.set_name('button_netapp5.app_button')
		self.button_netapp6.set_name('button_netapp6.app_button')
		self.button_localapp1.set_name('button_localapp1.app_button')
		self.button_localapp2.set_name('button_localapp2.app_button')
		self.button_localapp3.set_name('button_localapp3.app_button')
		self.button_myapp1.set_name('button_myapp1.app_button')
		self.button_myapp2.set_name('button_myapp2.app_button')
		self.button_myapp3.set_name('button_myapp3.app_button')
		self.label_myapp_text1.set_name('label_myapp_text1.label_app')
		self.label_myapp_text2.set_name('label_myapp_text2.label_app')
		self.label_myapp_text3.set_name('label_myapp_text3.label_app')

		self.button_web1.set_name('button_web1.web_app')
		self.button_web2.set_name('button_web2.web_app')
		self.button_web3.set_name('button_web3.web_app')
		self.button_web4.set_name('button_web4.web_app')

		self.button_music_launcher.set_name('button_music_launcher.web_app')
		self.button_video_launcher.set_name('button_video_launcher.web_app')
		self.button_pic_launcher.set_name('button_pic_launcher.web_app')
		self.button_music1.set_name('button_music1.web_app')
		self.button_music2.set_name('button_music2.web_app')
		self.button_music3.set_name('button_music3.web_app')
		self.button_music4.set_name('button_music4.web_app')
		self.button_music5.set_name('button_music5.web_app')
		self.button_music6.set_name('button_music6.web_app')
		self.button_video1.set_name('button_video1.web_app')
		self.button_video2.set_name('button_video2.web_app')
		self.button_video3.set_name('button_video3.web_app')
		self.button_video4.set_name('button_video4.web_app')
		self.button_video5.set_name('button_video5.web_app')
		self.button_video6.set_name('button_video6.web_app')
		self.button_pic1.set_name('button_pic1.web_app')
		self.button_pic2.set_name('button_pic2.web_app')
		self.button_pic3.set_name('button_pic3.web_app')

		pixbuf = gtk.gdk.pixbuf_new_from_file(image_background_file)
		pixbuf = pixbuf.scale_simple(x, y, gtk.gdk.INTERP_HYPER)
		pixmap, mask = pixbuf.render_pixmap_and_mask()

		self.main_window.resize(x, y)
		self.main_window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DESKTOP)

		self.main_window.set_app_paintable(True)
		self.main_window.realize()
		
		self.main_window.window.set_back_pixmap(pixmap, False)

		self.main_window.show_now()
		while gtk.events_pending():
			gtk.main_iteration(True)

		self.check_music_and_video_image(0)

#		self.alignment.connect('expose_event', self.expose)
		self.button_netapp1.connect('clicked', self.button_netapp1_launcher)
		self.button_netapp2.connect('clicked', self.button_netapp2_launcher)
		self.button_netapp3.connect('clicked', self.button_netapp3_launcher)
		self.button_netapp4.connect('clicked', self.button_netapp4_launcher)
		self.button_netapp5.connect('clicked', self.button_netapp5_launcher)
		self.button_netapp6.connect('clicked', self.button_netapp6_launcher)

		self.button_localapp1.connect('clicked', self.button_localapp1_launcher)
		self.button_localapp2.connect('clicked', self.button_localapp2_launcher)
		self.button_localapp3.connect('clicked', self.button_localapp3_launcher)

		self.button_myapp1.connect('clicked', self.button_myapp1_launcher)
		self.button_myapp2.connect('clicked', self.button_myapp2_launcher)
		self.button_myapp3.connect('clicked', self.button_myapp3_launcher)

		self.button_web1.connect('clicked', self.open_browser_url, "http://www.youku.com")
		self.button_web2.connect('clicked', self.open_browser_url, "http://www.zuche.com")
		self.button_web3.connect('clicked', self.open_browser_url, "http://www.ctrip.com")
		self.button_web4.connect('clicked', self.open_browser_url, "http://www.3366.com")

		self.button_music1.connect('clicked', self.open_music_file, 1)#, music_image_list[0])
		self.button_music2.connect('clicked', self.open_music_file, 2)#, music_image_list[1])
		self.button_music3.connect('clicked', self.open_music_file, 3)#, music_image_list[2])
		self.button_music4.connect('clicked', self.open_music_file, 4)#, music_image_list[3])
		self.button_music5.connect('clicked', self.open_music_file, 5)#, music_image_list[4])
		self.button_music6.connect('clicked', self.open_music_file, 6)#, music_image_list[5])

		self.button_video1.connect('clicked', self.open_video_file, 1)#, PATH+"music/*.mp3")
		self.button_video2.connect('clicked', self.open_video_file, 2)#, PATH+"music/*.mp3")
		self.button_video3.connect('clicked', self.open_video_file, 3)#, PATH+"music/*.mp3")
		self.button_video4.connect('clicked', self.open_video_file, 4)#, PATH+"music/*.mp3")
		self.button_video5.connect('clicked', self.open_video_file, 5)#, PATH+"music/*.mp3")
		self.button_video6.connect('clicked', self.open_video_file, 6)#, PATH+"music/*.mp3")

		self.button_pic1.connect('clicked', self.open_pic_file, 1)#, PATH+"music/*.mp3")
		self.button_pic2.connect('clicked', self.open_pic_file, 2)#, PATH+"music/*.mp3")
		self.button_pic3.connect('clicked', self.open_pic_file, 3)#, PATH+"music/*.mp3")

		self.button_music1.connect('button-press-event', self.pop_music_menu, 1)
		self.button_music2.connect('button-press-event', self.pop_music_menu, 2)
		self.button_music3.connect('button-press-event', self.pop_music_menu, 3)
		self.button_music4.connect('button-press-event', self.pop_music_menu, 4)
		self.button_music5.connect('button-press-event', self.pop_music_menu, 5)
		self.button_music6.connect('button-press-event', self.pop_music_menu, 6)

		self.button_video1.connect('button-press-event', self.pop_video_menu, 1)
		self.button_video2.connect('button-press-event', self.pop_video_menu, 2)
		self.button_video3.connect('button-press-event', self.pop_video_menu, 3)
		self.button_video4.connect('button-press-event', self.pop_video_menu, 4)
		self.button_video5.connect('button-press-event', self.pop_video_menu, 5)
		self.button_video6.connect('button-press-event', self.pop_video_menu, 6)

		self.button_pic1.connect('button-press-event', self.pop_pic_menu, 1)
		self.button_pic2.connect('button-press-event', self.pop_pic_menu, 2)
		self.button_pic3.connect('button-press-event', self.pop_pic_menu, 3)

		self.button_music_launcher.connect('clicked', self.music_launcher)
		self.button_video_launcher.connect('clicked', self.video_launcher)
		self.button_pic_launcher.connect('clicked', self.pic_launcher)

		self.button_search.connect('clicked', self.open_baidu_search, self.entry)
		self.entry.connect('activate', self.open_baidu_search, self.entry)
		self.button_email.connect('clicked', self.open_email)
#		self.button_starcenter.connect('clicked', self.open_CooCare)
		self.button_netapp1.connect("enter", self.change_cursor_to_hand ,self.button_netapp1)
		self.button_netapp1.connect("leave", self.change_cursor_to_normal ,self.button_netapp1)
		self.button_netapp2.connect("enter", self.change_cursor_to_hand ,self.button_netapp2)
		self.button_netapp2.connect("leave", self.change_cursor_to_normal ,self.button_netapp2)
		self.button_netapp3.connect("enter", self.change_cursor_to_hand ,self.button_netapp3)
		self.button_netapp3.connect("leave", self.change_cursor_to_normal ,self.button_netapp3)
		self.button_netapp4.connect("enter", self.change_cursor_to_hand ,self.button_netapp4)
		self.button_netapp4.connect("leave", self.change_cursor_to_normal ,self.button_netapp4)
		self.button_netapp5.connect("enter", self.change_cursor_to_hand ,self.button_netapp5)
		self.button_netapp5.connect("leave", self.change_cursor_to_normal ,self.button_netapp5)
		self.button_netapp6.connect("enter", self.change_cursor_to_hand ,self.button_netapp6)
		self.button_netapp6.connect("leave", self.change_cursor_to_normal ,self.button_netapp6)
		self.button_localapp1.connect("enter", self.change_cursor_to_hand ,self.button_localapp1)
		self.button_localapp1.connect("leave", self.change_cursor_to_normal ,self.button_localapp1)
		self.button_localapp2.connect("enter", self.change_cursor_to_hand ,self.button_localapp2)
		self.button_localapp2.connect("leave", self.change_cursor_to_normal ,self.button_localapp2)
		self.button_localapp3.connect("enter", self.change_cursor_to_hand ,self.button_localapp3)
		self.button_localapp3.connect("leave", self.change_cursor_to_normal ,self.button_localapp3)
		self.button_myapp1.connect("enter", self.change_cursor_to_hand ,self.button_myapp1)
		self.button_myapp1.connect("leave", self.change_cursor_to_normal ,self.button_myapp1)
		self.button_myapp2.connect("enter", self.change_cursor_to_hand ,self.button_myapp2)
		self.button_myapp2.connect("leave", self.change_cursor_to_normal ,self.button_myapp2)
		self.button_myapp3.connect("enter", self.change_cursor_to_hand ,self.button_myapp3)
		self.button_myapp3.connect("leave", self.change_cursor_to_normal ,self.button_myapp3)

		self.button_search.connect("enter", self.change_cursor_to_hand ,self.button_search)
		self.button_search.connect("leave", self.change_cursor_to_normal ,self.button_search)

		self.button_web1.connect("enter", self.change_cursor_to_hand ,self.button_web1)
		self.button_web1.connect("leave", self.change_cursor_to_normal ,self.button_web1)
		self.button_web2.connect("enter", self.change_cursor_to_hand ,self.button_web2)
		self.button_web2.connect("leave", self.change_cursor_to_normal ,self.button_web2)
		self.button_web3.connect("enter", self.change_cursor_to_hand ,self.button_web3)
		self.button_web3.connect("leave", self.change_cursor_to_normal ,self.button_web3)
		self.button_web4.connect("enter", self.change_cursor_to_hand ,self.button_web4)
		self.button_web4.connect("leave", self.change_cursor_to_normal ,self.button_web4)
		self.button_email.connect("enter", self.change_cursor_to_hand ,self.button_email)
		self.button_email.connect("leave", self.change_cursor_to_normal ,self.button_email)
		self.button_music_launcher.connect("enter", self.change_cursor_to_hand ,self.button_music_launcher)
		self.button_music_launcher.connect("leave", self.change_cursor_to_normal ,self.button_music_launcher)
		self.button_video_launcher.connect("enter", self.change_cursor_to_hand ,self.button_video_launcher)
		self.button_video_launcher.connect("leave", self.change_cursor_to_normal ,self.button_video_launcher)
		self.button_pic_launcher.connect("enter", self.change_cursor_to_hand ,self.button_pic_launcher)
		self.button_pic_launcher.connect("leave", self.change_cursor_to_normal ,self.button_pic_launcher)
		self.button_music1.connect("enter", self.change_cursor_to_hand ,self.button_music1)
		self.button_music1.connect("leave", self.change_cursor_to_normal ,self.button_music1)
		self.button_music2.connect("enter", self.change_cursor_to_hand ,self.button_music2)
		self.button_music2.connect("leave", self.change_cursor_to_normal ,self.button_music2)
		self.button_music3.connect("enter", self.change_cursor_to_hand ,self.button_music3)
		self.button_music3.connect("leave", self.change_cursor_to_normal ,self.button_music3)
		self.button_music4.connect("enter", self.change_cursor_to_hand ,self.button_music4)
		self.button_music4.connect("leave", self.change_cursor_to_normal ,self.button_music4)
		self.button_music5.connect("enter", self.change_cursor_to_hand ,self.button_music5)
		self.button_music5.connect("leave", self.change_cursor_to_normal ,self.button_music5)
		self.button_music6.connect("enter", self.change_cursor_to_hand ,self.button_music6)
		self.button_music6.connect("leave", self.change_cursor_to_normal ,self.button_music6)
		self.button_video1.connect("enter", self.change_cursor_to_hand ,self.button_video1)
		self.button_video1.connect("leave", self.change_cursor_to_normal ,self.button_video1)
		self.button_video2.connect("enter", self.change_cursor_to_hand ,self.button_video2)
		self.button_video2.connect("leave", self.change_cursor_to_normal ,self.button_video2)
		self.button_video3.connect("enter", self.change_cursor_to_hand ,self.button_video3)
		self.button_video3.connect("leave", self.change_cursor_to_normal ,self.button_video3)
		self.button_video4.connect("enter", self.change_cursor_to_hand ,self.button_video4)
		self.button_video4.connect("leave", self.change_cursor_to_normal ,self.button_video4)
		self.button_video5.connect("enter", self.change_cursor_to_hand ,self.button_video5)
		self.button_video5.connect("leave", self.change_cursor_to_normal ,self.button_video5)
		self.button_video6.connect("enter", self.change_cursor_to_hand ,self.button_video6)
		self.button_video6.connect("leave", self.change_cursor_to_normal ,self.button_video6)
		self.button_pic1.connect("enter", self.change_cursor_to_hand ,self.button_pic1)
		self.button_pic1.connect("leave", self.change_cursor_to_normal ,self.button_pic1)
		self.button_pic2.connect("enter", self.change_cursor_to_hand ,self.button_pic2)
		self.button_pic2.connect("leave", self.change_cursor_to_normal ,self.button_pic2)
		self.button_pic3.connect("enter", self.change_cursor_to_hand ,self.button_pic3)
		self.button_pic3.connect("leave", self.change_cursor_to_normal ,self.button_pic3)

#		self.main_window.resize(x, y)
#		self.main_window.set_type_hint(gtk.gdk.WINDOW_TYPE_HINT_DESKTOP)

		self.main_window.show_now()
		while gtk.events_pending():
			gtk.main_iteration(True)
#		pixbuf = gtk.gdk.pixbuf_new_from_file("./bg_new_img.jpg")
#		self.gdk.draw_pixbuf(self.style.bg_gc[gtk.STATE_INSENSITIVE], pixbuf, 0, 0, 0, 0)
		self.screenshot()
#		glib.timeout_add_seconds(5, self.flash_media)
#		gtk.main()

	def change_cursor_to_hand(self, widget, button_widget):
		button_widget.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.HAND2))

	def change_cursor_to_normal(self, widget, button_widget):
		button_widget.window.set_cursor(None)

	def button_netapp1_launcher(self, widget):
		os.system("openfetion"+backgroundrun)

	def button_netapp2_launcher(self, widget):
		os.system("qq"+backgroundrun)

	def button_netapp3_launcher(self, widget):
		os.system("weibo_notes"+backgroundrun)

	def button_netapp4_launcher(self, widget):
		os.system("skype"+backgroundrun)

	def button_netapp5_launcher(self, widget):
		os.system("douban"+backgroundrun)

	def button_netapp6_launcher(self, widget):
		os.system("msc"+backgroundrun)

	def button_localapp1_launcher(self, widget):
		os.system("abiword"+backgroundrun)

	def button_localapp2_launcher(self, widget):
		os.system("gnumeric"+backgroundrun)

	def button_localapp3_launcher(self, widget):
		os.system("gcalctool"+backgroundrun)

	def button_myapp1_launcher(self, widget):
		os.system("/usr/local/jre/bin/java -jar /usr/local/bin/LinuxCooCare.jar"+backgroundrun)

	def button_myapp2_launcher(self, widget):
		os.system("/opt/wsysrt/client"+backgroundrun)

	def button_myapp3_launcher(self, widget):
		os.system("emelfm2"+backgroundrun)

	def open_browser_url(self, widget, data = None):
		os.system("www-browser "+data+backgroundrun)

	def music_launcher(self, widget):
#		os.system("gnome-mplayer &")
		os.system("gnome-mplayer"+backgroundrun)

	def video_launcher(self, widget):
		os.system("gnome-mplayer"+backgroundrun)

	def pic_launcher(self, widget):
		os.system("gpicview"+backgroundrun)

	def do_music_remove(self, widget, selected):
		def remove_music_image(selected):
			Nomusic = selected - 1
			music_image_list[Nomusic] = ''
			self.music_image[Nomusic].set_from_file(image_none_music_file)
			self.music_image[Nomusic].set_tooltip_text(None)
			music_image_icon_status[Nomusic] = False

		remove_music_image(selected)
		self.write_config_file(etc_file)

	def do_video_remove(self, widget, selected):
		Novideo = selected - 1
		video_image_list[Novideo] = ''
		self.video_image[Novideo].set_from_file(image_none_video_file)
		self.video_image[Novideo].set_tooltip_text(None)
		video_image_icon_status[Novideo] = False
		self.write_config_file(etc_file)

	def do_pic_remove(self, widget, selected):
		Nopic = selected - 1
		picture_image_list[Nopic] = ''
		self.pic_image[Nopic].set_from_file(image_none_pic_file)
		self.pic_image[Nopic].set_tooltip_text(None)
		picture_image_icon_status[Nopic] = False
		self.write_config_file(etc_file)

	def pop_music_menu(self, widget, event, selected):
        #-print self, widget, event, editbox, args
		if event.button == 3:
			menu = gtk.Menu()

			menuitem_new = gtk.ImageMenuItem("Remove")
			menuitem_new.show()
			menuitem_new.connect("activate", self.do_music_remove, selected)
			menu.append(menuitem_new)

			menu.show_all()
			menu.popup(None, None, None, event.button, event.time)
			return True

	def pop_video_menu(self, widget, event, selected):
		if event.button == 3:
			menu = gtk.Menu()

			menuitem_new = gtk.ImageMenuItem("Remove")
			menuitem_new.show()
			menuitem_new.connect("activate", self.do_video_remove, selected)
			menu.append(menuitem_new)

			menu.show_all()
			menu.popup(None, None, None, event.button, event.time)
			return True

	def pop_pic_menu(self, widget, event, selected):
		if event.button == 3:
			menu = gtk.Menu()

			menuitem_new = gtk.ImageMenuItem("Remove")
			menuitem_new.show()
			menuitem_new.connect("activate", self.do_pic_remove, selected)
			menu.append(menuitem_new)

			menu.show_all()
			menu.popup(None, None, None, event.button, event.time)
			return True

	def open_music_file(self, widget, selected):
		choose_fileing = 1
		Nomusic = selected - 1
		if music_image_list[Nomusic] != '' and os.path.isfile(music_image_list[Nomusic]):
			os.system("gnome-mplayer "+"\""+music_image_list[Nomusic]+"\""+backgroundrun)
		else:
			temp_file_chooser_name = gtkdialogs.open(title='选择音乐文件', name_mimes={_("MP3"):"audio/mp3"})
			if temp_file_chooser_name:
				music_image_list[Nomusic] = temp_file_chooser_name
				temp_file_chooser_icon_name = self.get_mp3_fengmian(temp_file_chooser_name)
#				temp_file_chooser_icon_name = gtkdialogs.open(title='选择封面文件', name_mimes={_("Image files"):"image/*"})
				if temp_file_chooser_icon_name:
#					music_image_icon_list[Nomusic] = temp_file_chooser_icon_name
#					temp_pixbuf = gtk.gdk.pixbuf_new_from_file(music_image_icon_list[Nomusic])
					temp_pixbuf = gtk.gdk.pixbuf_new_from_file(temp_file_chooser_icon_name)
					temp_pixbuf = temp_pixbuf.scale_simple(82, 82, gtk.gdk.INTERP_HYPER)
					self.music_image[Nomusic].set_from_pixbuf(temp_pixbuf)
				else:
#					music_image_icon_list[Nomusic] = image_has_music_file
					self.music_image[Nomusic].set_from_file(image_has_music_file)					
				self.music_image[Nomusic].set_tooltip_text(os.path.basename(music_image_list[Nomusic]))
				self.write_config_file(etc_file)
		choose_fileing = 0

	def open_video_file(self, widget, selected):
		choose_fileing = 1
		Novideo = selected - 1
		if video_image_list[Novideo] != '' and os.path.isfile(video_image_list[Novideo]):
			os.system("gnome-mplayer "+"\""+video_image_list[Novideo]+"\""+backgroundrun)
		else:
			temp_file_chooser_name = gtkdialogs.open(title='选择媒体文件', name_mimes={_("AVI MPEG"):"video/*"})
			if temp_file_chooser_name:
				video_image_list[Novideo] = temp_file_chooser_name
#				print 'video_image_list[0] is'+video_image_list[0]
				temp_file_chooser_icon_name = self.get_video_jietu(temp_file_chooser_name)
#				print temp_file_chooser_icon_name
#				temp_file_chooser_icon_name = gtkdialogs.open(title='选择封面文件', name_mimes={_("Image files"):"image/*"})
				if temp_file_chooser_icon_name:
					temp_pixbuf = gtk.gdk.pixbuf_new_from_file(temp_file_chooser_icon_name)
#					video_image_icon_list[Novideo] = temp_file_chooser_icon_name
#					temp_pixbuf = gtk.gdk.pixbuf_new_from_file(video_image_icon_list[Novideo])
					temp_pixbuf = temp_pixbuf.scale_simple(82, 82, gtk.gdk.INTERP_HYPER)
					self.video_image[Novideo].set_from_pixbuf(temp_pixbuf)
				else:
#					video_image_icon_list[Novideo] = image_has_video_file
					self.video_image[Novideo].set_from_file(image_has_video_file)
				self.video_image[Novideo].set_tooltip_text(os.path.basename(video_image_list[Novideo]))
				self.write_config_file(etc_file)
		choose_fileing = 0

	def open_pic_file(self, widget, selected):
		choose_fileing = 1
		Nopic = selected - 1
		if picture_image_list[Nopic] != '' and os.path.isfile(picture_image_list[Nopic]):
			os.system("gpicview "+"\""+picture_image_list[Nopic]+"\""+backgroundrun)
		else:
			temp_file_chooser_name = gtkdialogs.open(title='选择图片文件', name_mimes={_("Image files"):"image/*"})
			if temp_file_chooser_name:
				picture_image_list[Nopic] = temp_file_chooser_name
				temp_pixbuf = gtk.gdk.pixbuf_new_from_file(picture_image_list[Nopic])
				temp_pixbuf = temp_pixbuf.scale_simple(82, 82, gtk.gdk.INTERP_HYPER)
				self.pic_image[Nopic].set_from_pixbuf(temp_pixbuf)
				self.pic_image[Nopic].set_tooltip_text(os.path.basename(picture_image_list[Nopic]))
				self.write_config_file(etc_file)
		choose_fileing = 0

	def open_baidu_search(self, widget, entry):
		text = entry.get_text()
		os.system('www-browser "http://www.baidu.com/s?wd='+text+baiduword+'"'+backgroundrun)

	def open_email(self, widget):
		os.system("claws-mail"+backgroundrun)
		
#	def open_CooCare(sefl, widget):
#		os.system("/usr/local/jre/bin/java -jar /usr/local/bin/LinuxCooCare.jar &")

	def expose(self, widget, ev):
#		pixbuf = gtk.gdk.pixbuf_new_from_file(image_background_file)
#		pixbuf = pixbuf.scale_simple(x, y, gtk.gdk.INTERP_HYPER)
		widget.window.draw_pixbuf(widget.style.bg_gc[gtk.STATE_INSENSITIVE], self.pixbuf, 0, 0, 0, 0)
		if widget.get_child() != None:
			widget.propagate_expose(widget.get_child(), ev)
		return True

	def on_window_destroy(self, widget, data=None):
		gtk.main_quit()

	def input_list_to_file(self, listStore, fileName):
		treeModel = listStore.filter_new()
		listfile = open(fileName, 'w')
		if (fileName == blacklist):
			num = black_num
		else:
			num = white_num
		print num
		for i in range(0, num):
			treeIter = treeModel.get_iter(i)
			address = treeModel.get_value(treeIter, 0)
			print(address)	
			listfile.write(address)
			listfile.write('\n')	
		listfile.close()


	def input_file_to_list(self, fileName, listStore):
		listfile = file(fileName, 'r')
		address_list = listfile.read().split('\n')
		address_list.pop()
		global black_num
		global white_num
		for address in address_list:
			listStore.append([address])
			if(fileName == blacklist):
				black_num = black_num + 1
			else:
				white_num = white_num + 1
		listfile.close()

	def read_config_file(self, filename):
		if os.path.isfile(filename):
			config = ConfigParser.RawConfigParser()
			config.read(filename)

			# getfloat() raises an exception if the value is not a float  
			# getint() and getboolean() also do this for their respective types  
			music_image_list[0] = config.get('Music Section', 'music_image1')
			music_image_list[1] = config.get('Music Section', 'music_image2')
			music_image_list[2] = config.get('Music Section', 'music_image3')
			music_image_list[3] = config.get('Music Section', 'music_image4')
			music_image_list[4] = config.get('Music Section', 'music_image5')
			music_image_list[5] = config.get('Music Section', 'music_image6')
#			music_image_icon_list[0] = config.get('Music Section', 'music_image_icon1')
#			music_image_icon_list[1] = config.get('Music Section', 'music_image_icon2')
#			music_image_icon_list[2] = config.get('Music Section', 'music_image_icon3')
#			music_image_icon_list[3] = config.get('Music Section', 'music_image_icon4')
#			music_image_icon_list[4] = config.get('Music Section', 'music_image_icon5')
#			music_image_icon_list[5] = config.get('Music Section', 'music_image_icon6')

			video_image_list[0] = config.get('Video Section', 'video_image1')
			video_image_list[1] = config.get('Video Section', 'video_image2')
			video_image_list[2] = config.get('Video Section', 'video_image3')
			video_image_list[3] = config.get('Video Section', 'video_image4')
			video_image_list[4] = config.get('Video Section', 'video_image5')
			video_image_list[5] = config.get('Video Section', 'video_image6')
#			video_image_icon_list[0] = config.get('Video Section', 'video_image_icon1')
#			video_image_icon_list[1] = config.get('Video Section', 'video_image_icon2')
#			video_image_icon_list[2] = config.get('Video Section', 'video_image_icon3')
#			video_image_icon_list[3] = config.get('Video Section', 'video_image_icon4')
#			video_image_icon_list[4] = config.get('Video Section', 'video_image_icon5')
#			video_image_icon_list[5] = config.get('Video Section', 'video_image_icon6')

			picture_image_list[0] = config.get('Picture Section', 'picture_image1')
			picture_image_list[1] = config.get('Picture Section', 'picture_image2')
			picture_image_list[2] = config.get('Picture Section', 'picture_image3')

	def write_config_file(self, filename):
		config = ConfigParser.RawConfigParser()

		# When adding sections or items, add them in the reverse order of  
		# how you want them to be displayed in the actual file.  
		# In addition, please note that using RawConfigParser's and the raw  
		# mode of ConfigParser's respective set functions, you can assign  
		# non-string values to keys internally, but will receive an error  
		# when attempting to write to a file or when you get it in non-raw  
		# mode. SafeConfigParser does not allow such assignments to take place.  
		config.add_section('Music Section')
		config.set('Music Section', 'music_image1', music_image_list[0])
		config.set('Music Section', 'music_image2', music_image_list[1])
		config.set('Music Section', 'music_image3', music_image_list[2])
		config.set('Music Section', 'music_image4', music_image_list[3])
		config.set('Music Section', 'music_image5', music_image_list[4])
		config.set('Music Section', 'music_image6', music_image_list[5])
#		config.set('Music Section', 'music_image_icon1', music_image_icon_list[0])
#		config.set('Music Section', 'music_image_icon2', music_image_icon_list[1])
#		config.set('Music Section', 'music_image_icon3', music_image_icon_list[2])
#		config.set('Music Section', 'music_image_icon4', music_image_icon_list[3])
#		config.set('Music Section', 'music_image_icon5', music_image_icon_list[4])
#		config.set('Music Section', 'music_image_icon6', music_image_icon_list[5])

		config.add_section('Video Section')
		config.set('Video Section', 'video_image1', video_image_list[0])
		config.set('Video Section', 'video_image2', video_image_list[1])
		config.set('Video Section', 'video_image3', video_image_list[2])
		config.set('Video Section', 'video_image4', video_image_list[3])
		config.set('Video Section', 'video_image5', video_image_list[4])
		config.set('Video Section', 'video_image6', video_image_list[5])
#		config.set('Video Section', 'video_image_icon1', video_image_icon_list[0])
#		config.set('Video Section', 'video_image_icon2', video_image_icon_list[1])
#		config.set('Video Section', 'video_image_icon3', video_image_icon_list[2])
#		config.set('Video Section', 'video_image_icon4', video_image_icon_list[3])
#		config.set('Video Section', 'video_image_icon5', video_image_icon_list[4])
#		config.set('Video Section', 'video_image_icon6', video_image_icon_list[5])

		config.add_section('Picture Section')
		config.set('Picture Section', 'picture_image1', picture_image_list[0])
		config.set('Picture Section', 'picture_image2', picture_image_list[1])
		config.set('Picture Section', 'picture_image3', picture_image_list[2])

		# Writing our configuration file to 'example.cfg'  
		with open(filename, 'wb') as configfile:
			config.write(configfile)

	def check_music_and_video_image(self, weather_choose):
		if weather_choose == 0:
			self.read_config_file(etc_file)
#		for i in music_image_list:
#			if i == '':
#				self.music_image1.set_from_file(image_none_music_file)
#			else:
#				self.music_image1.set_from_file(i)
		for i in range(6):
			if music_image_list[i] == '' or not os.path.isfile(music_image_list[i]):
				self.music_image[i].set_from_file(image_none_music_file)
			else:
				if music_image_icon_status[i] == False:
					temp_music_fengmian_file = self.get_mp3_fengmian(music_image_list[i])
					if not temp_music_fengmian_file:
						self.music_image[i].set_from_file(image_has_music_file)
					else:
						temp_pixbuf = gtk.gdk.pixbuf_new_from_file(temp_music_fengmian_file)
						temp_pixbuf = temp_pixbuf.scale_simple(82, 82, gtk.gdk.INTERP_HYPER)
						self.music_image[i].set_from_pixbuf(temp_pixbuf)				
					self.music_image[i].set_tooltip_text(glib.filename_display_basename(music_image_list[i]))
				music_image_icon_status[i] == True

#		for i in range(6):
			if video_image_list[i] == '' or not os.path.isfile(video_image_list[i]):
				self.video_image[i].set_from_file(image_none_video_file)
			else:
				if video_image_icon_status[i] == False:
					temp_video_jietu_file = self.get_video_jietu(video_image_list[i])
	#				print temp_video_jietu_file
	#				if video_image_icon_list[i] == '' or not os.path.isfile(video_image_icon_list[i]):
					if not temp_video_jietu_file:
						self.video_image[i].set_from_file(image_has_video_file)
					else:
						temp_pixbuf = gtk.gdk.pixbuf_new_from_file(temp_video_jietu_file)
						temp_pixbuf = temp_pixbuf.scale_simple(82, 82, gtk.gdk.INTERP_HYPER)
						self.video_image[i].set_from_pixbuf(temp_pixbuf)				
					self.video_image[i].set_tooltip_text(glib.filename_display_basename(video_image_list[i]))
					video_image_icon_status[i] = True

		for i in range(3):
			if picture_image_list[i] == '' or not os.path.isfile(picture_image_list[i]):
				self.pic_image[i].set_from_file(image_none_pic_file)
			else:
				if picture_image_icon_status[i] == False:
					temp_pixbuf = gtk.gdk.pixbuf_new_from_file(picture_image_list[i])
					temp_pixbuf = temp_pixbuf.scale_simple(82, 82, gtk.gdk.INTERP_HYPER)
					self.pic_image[i].set_from_pixbuf(temp_pixbuf)
				picture_image_icon_status[i] = True

	def flash_media(self):
		if choose_fileing == 0:
			self.check_music_and_video_image(1) #0:init 1:normal
		return True

	def get_mp3_fengmian(self, filename):
		tag = eyeD3.Tag()
		tag.link(filename)
		imgs = tag.getImages()
		img = None
		if len(imgs)>0:
			img = imgs[0]
		if img:
			open (fengmianfile,'w').write(img.imageData)
			return fengmianfile
#			print img.mimeType
	#		if not RESPONSE:
	#			RESPONSE = self.REQUEST.RESPONSE
	#		RESPONSE.setHeader('Content-Type', img.mimeType)
	#		return img.imageData
#			return img
#		print 'None has image!'
		return None

	def get_video_jietu(self, filename):
		cmd="rm %s;mplayer -ss 00:00:03 -noframedrop -nosound -vo jpeg:outdir=/dev/shm/ -frames 1 \"%s\" > /dev/null 2>&1" % (video_screenshot_file, filename)
		os.system(cmd)
#		os.system("rm "+video_screenshot_file+";mplayer -ss 00:00:03 -noframedrop -nosound -vo jpeg:outdir=/dev/shm/ -frames 1 "+'"'+filename+'"')
		if os.path.isfile(video_screenshot_file):
			return video_screenshot_file
		return None

	def screenshot(self):

		w = gtk.gdk.get_default_root_window()
#		self.main_window.realize()
#		w = self.main_window.window
#		sz = w.get_size()
#		print "The size of the window is %d x %d" % sz
		pb = gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB,False,8,x,y)
#		pb = pb.get_from_drawable(self.main_window.realize,self.main_window.realize.get_colormap(),0,0,0,0,sz[0],sz[1])
		pb = pb.get_from_drawable(w,w.get_colormap(),0,0,0,0,x,y)
		if (pb != None):
			pb.save(screenshot_file, "png")
#			print "Screenshot saved to screenshot.png."
#		else:
#			print "Unable to get the screenshot."

		return False


if __name__ == '__main__':
	desktop_main_window = MainWindow()
	glib.timeout_add_seconds(5, desktop_main_window.flash_media)
#	glib.timeout_add_seconds(5, desktop_main_window.screenshot)
	gtk.main()
