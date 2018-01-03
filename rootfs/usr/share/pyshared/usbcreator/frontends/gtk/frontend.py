# Copyright (C) 2008-2009 Canonical Ltd.

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3,
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess, sys
import os

import gettext
import locale
import pygtk
import gobject
import gtk
import gio
import glib
import logging
import pango
from gnome import help_display_uri

from usbcreator.frontends.base import Frontend
from usbcreator.misc import *

if 'USBCREATOR_LOCAL' in os.environ:
    ui_path = os.path.join(os.getcwd(), 'gui/usbcreator-gtk.ui')
else:
    ui_path = '/usr/share/usb-creator/usbcreator-gtk.ui'

gtk.gdk.threads_init()

def thread_wrap(func):
    '''Decorator for functions that will be called by another thread.'''
    def wrap(*args):
        gtk.gdk.threads_enter()
        try:
            return func(*args)
        finally:
            gtk.gdk.threads_leave()
    return wrap

def wrap_fix(w, allocation):
    # Until the extended layout branch of GTK+ gets merged (bgo #101968).
    layout = w.get_layout()
    old_width, old_height = layout.get_size()
    if old_width / pango.SCALE == allocation.width:
        return
    layout.set_width(allocation.width * pango.SCALE)
    unused, height = layout.get_size()
    if old_height != height:
        w.set_size_request(-1, height / pango.SCALE)

def process_labels(w):
    if isinstance(w, gtk.Container):
        children = w.get_children()
        for c in children:
            process_labels(c)
    elif isinstance(w, gtk.Label):
        if w.get_line_wrap():
            w.connect_after('size-allocate', wrap_fix)
        w.set_property('can-focus', False)

class GtkFrontend(Frontend):
    @classmethod
    def startup_failure(cls, message):
        dialog = gtk.MessageDialog(None, 0, gtk.MESSAGE_ERROR,
            gtk.BUTTONS_CLOSE, message)
        dialog.run()
        dialog.destroy()
        
    @classmethod
    def DBusMainLoop(cls):
        from dbus.mainloop.glib import DBusGMainLoop
        DBusGMainLoop(set_as_default=True)

    def __init__(self, backend, img=None, persistent=True,
                 allow_system_internal=False):

        self.allow_system_internal = allow_system_internal

        self.all_widgets = set()

        self.builder = gtk.Builder()
        self.builder.set_translation_domain('usbcreator')
        self.builder.add_from_file(ui_path)
        # A cache of the icon names and display names for the individual
        # devices.
        self.icons = {}
        self.names = {}

        for widget in self.builder.get_objects():
            # Taken from ubiquity:
            # We generally want labels to be selectable so that people can
            # easily report problems in them
            # (https://launchpad.net/bugs/41618), but GTK+ likes to put
            # selectable labels in the focus chain, and I can't seem to turn
            # this off in glade and have it stick. Accordingly, make sure
            # labels are unfocusable here.
            if isinstance(widget, gtk.Label):
                widget.set_property('can-focus', False)
            if issubclass(type(widget), gtk.Widget):
                self.all_widgets.add(widget)
                widget.set_name(gtk.Buildable.get_name(widget))
                setattr(self, gtk.Widget.get_name(widget), widget)

        gtk.window_set_default_icon_name('usb-creator-gtk')
        for w in self.all_widgets:
            process_labels(w)

        # Connect signals to widgets
        self.builder.connect_signals (self, None)
        self.cancelbutton.connect('clicked', lambda x: self.warning_dialog.hide())
        self.finished_exit.connect('clicked', lambda x: self.finished_dialog.hide())
        self.failed_exit.connect('clicked', lambda x: self.failed_exit.hide())
        self.progress_cancel_button.connect('clicked', lambda x: self.warning_dialog.show())
        self.button_help.connect('clicked', lambda x: help_display_uri('ghelp:usb-creator'))

        def format_value(scale, value):
            return format_mb_size(value)
        self.persist_value.set_adjustment(
            gtk.Adjustment(0, 0, 100, 1, 10, 0))
        self.persist_value.connect('format-value', format_value)

        # Connect to backend signals.
        self.backend = backend
        self.backend.source_added_cb = self.add_source
        self.backend.target_added_cb = self.add_target
        self.backend.source_removed_cb = self.remove_source
        self.backend.target_removed_cb = self.remove_target
        self.backend.failure_cb = self.failure
        self.backend.success_cb = self.success
        self.backend.install_progress_cb = self.progress
        self.backend.install_progress_message_cb = self.progress_message
        self.backend.install_progress_pulse_cb = self.progress_pulse
        self.backend.install_progress_pulse_stop_cb = self.progress_pulse_stop
        self.backend.retry_cb = self.retry
        self.backend.target_changed_cb = self.update_target
        self.backend.format_ended_cb = self.format_ended
        self.backend.format_failed_cb = self.format_failed

        # Pulse state.
        self.pulsing = False

        self.setup_sources_treeview()
        self.setup_targets_treeview()
        self.persist_vbox.set_sensitive(False)

        # Pre-populate the source view.
        if img is not None:
            self.backend.add_image(img)
            self.source_vbox.hide()

        download_dir = glib.get_user_special_dir(glib.USER_DIRECTORY_DOWNLOAD)
        if download_dir and os.path.isdir(download_dir):
            # TODO evand 2009-10-22: File type detection based on file(1).
            for fname in os.listdir(download_dir):
                if fname.endswith('.iso') or fname.endswith('.img'):
                    self.backend.add_image(os.path.join(download_dir, fname))

        # Sets first pre-populated image as current in the backend
        self.selection_changed_source(self.source_treeview.get_selection())

        if not persistent:
            self.persist_disabled.set_active(True)
            self.persist_vbox.hide()
        
        self.window.show()
        # Continued from above; hack around GTK's lack of good label wrapping.
        self.window.set_size_request(self.window.get_allocation().width, -1)
        selection = self.source_treeview.get_selection()
        selection.connect('changed', self.selection_changed_source)
        selection = self.dest_treeview.get_selection()
        selection.connect('changed', self.selection_changed_target)

        self.backend.detect_devices()
        
        self.update_loop = self.add_timeout(2000, self.backend.update_free)
        gtk.gdk.threads_enter()
        try:
            gtk.main()
        except KeyboardInterrupt:
            self.quit()
        gtk.gdk.threads_leave()

    def add_timeout(self, interval, func, *args):
        '''Add a new timer for function 'func' with optional arguments. Wraps a
        similar gobject call timeout_add.'''

        timer = gobject.timeout_add(interval, func, *args)

        return timer
    def delete_timeout(self, timer):
        '''Remove the specified timer. Wraps gobject source_remove call.'''

        return gobject.source_remove(timer)

    def add_source(self, source):
        logging.debug('add_source: %s' % str(source))
        _append_to_list_and_select(self.source_treeview, [source],
            force_selection=False)
        
        # XXX evand 2009-09-17: Find a label and icon for the device, if we
        # don't already have one.  This will go away when the code for the
        # presentation-name and presentation-icon properties in udisks
        # is written.
        t = self.backend.sources[source]['type']
        l = self.backend.sources[source]['label']
        d = self.backend.sources[source]['device']
        if not (t == SOURCE_ISO or t == SOURCE_IMG):
            name, icon = self.get_gnome_drive(d)
            if icon:
                self.icons[source] = icon
            if not l and name:
                self.names[source] = name

    def add_target(self, target):
        logging.debug('add_target: %s' % str(target))
        _append_to_list_and_select(self.dest_treeview, [target],
            force_selection=False)

        # XXX evand 2009-09-17: Find a label and icon for the device.
        d = self.backend.targets[target]['device']
        l = self.backend.targets[target]['label']
        name, icon = self.get_gnome_drive(d)
        if icon:
            self.icons[target] = icon
        if not l and name:
            self.names[target] = name

    def remove_source(self, source):
        model = self.source_treeview.get_model()
        iterator = model.get_iter_first()
        to_delete = None
        while iterator is not None:
            if model.get_value(iterator, 0) == source:
                to_delete = iterator
            iterator = model.iter_next(iterator)
        if to_delete is not None:
            model.remove(to_delete)
        
        if source in self.names:
            self.names.pop(source)
        if source in self.icons:
            self.icons.pop(source)
        
        sel = self.source_treeview.get_selection()
        m, i = sel.get_selected()
        if not i:
            sel.select_path(0)

    def remove_target(self, target):
        model = self.dest_treeview.get_model()
        iterator = model.get_iter_first()
        to_delete = None
        while iterator is not None:
            if model.get_value(iterator, 0) == target:
                to_delete = iterator
            iterator = model.iter_next(iterator)
        if to_delete is not None:
            model.remove(to_delete)
        
        if target in self.names:
            self.names.pop(target)
        if target in self.icons:
            self.icons.pop(target)
        
        sel = self.dest_treeview.get_selection()
        m, i = sel.get_selected()
        if not i:
            sel.select_path(0)

    def get_source(self):
        '''Returns the UDI of the selected source image.'''
        sel = self.source_treeview.get_selection()
        m, i = sel.get_selected()
        if i:
            return m[i][0]
        else:
            logging.debug('No source selected.')
            return ''

    def get_target(self):
        '''Returns the UDI of the selected target disk or partition.'''
        sel = self.dest_treeview.get_selection()
        m, i = sel.get_selected()
        if i:
            return m[i][0]
        else:
            logging.debug('No target selected.')
            return ''
    
    def get_persistence(self):
        if self.persist_enabled.get_active() and \
            self.persist_enabled.state != gtk.STATE_INSENSITIVE:
            val = self.persist_value.get_value()
            return int(val)
        else:
            return 0

    def get_gnome_drive(self, dev):
        try:
            monitor = gio.volume_monitor_get()
            for drive in monitor.get_volumes():
                if 'unix-device' in drive.enumerate_identifiers():
                    if drive.get_identifier('unix-device') == dev:
                        name = drive.get_name()
                        icon = drive.get_icon().get_names()[0]
                        return (name, icon)
            for drive in monitor.get_connected_drives():
                if 'unix-device' in drive.enumerate_identifiers():
                    if drive.get_identifier('unix-device') == dev:
                        name = drive.get_name()
                        icon = drive.get_icon().get_names()[0]
                        return (name, icon)
        except Exception:
            logging.exception('Could not determine GNOME drive:')
        return ('', '')

    def setup_sources_treeview(self):
        def column_data_func(layout, cell, model, iterator, column):
            if not self.backend:
                return
            udi = model[iterator][0]
            dev = self.backend.sources[udi]
            t = dev['type']
            if column == 0:
                if udi in self.names:
                    cell.set_property('text', self.names[udi])
                else:
                    cell.set_property('text', dev['device'])
            elif column == 1:
                cell.set_property('text', dev['label'])
            elif column == 2:
                cell.set_property('text', format_size(dev['size']))

        def pixbuf_data_func(column, cell, model, iterator):
            if not self.backend:
                return
            udi = model[iterator][0]
            dev = self.backend.sources[udi]
            source_type = dev['type']
            if source_type == SOURCE_ISO:
                cell.set_property('stock-id', gtk.STOCK_CDROM)
            elif source_type == SOURCE_IMG:
                cell.set_property('stock-id', gtk.STOCK_HARDDISK)
            else:
                if udi in self.icons:
                    cell.set_property('icon-name', self.icons[udi])
                else:
                    cell.set_property('stock-id', None)

        list_store = gtk.ListStore(str)
        self.source_treeview.set_model(list_store)

        cell_name = gtk.CellRendererText()
        cell_name.set_property('ellipsize', pango.ELLIPSIZE_END)
        cell_pixbuf = gtk.CellRendererPixbuf()
        column_name = gtk.TreeViewColumn(_('CD-Drive/Image'))
        column_name.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        column_name.set_resizable(True)
        column_name.set_expand(True)
        column_name.set_min_width(75)
        column_name.pack_start(cell_pixbuf, expand=False)
        column_name.pack_start(cell_name, expand=True)
        self.source_treeview.append_column(column_name)
        column_name.set_cell_data_func(cell_name, column_data_func, 0)
        column_name.set_cell_data_func(cell_pixbuf, pixbuf_data_func)

        cell_version = gtk.CellRendererText()
        cell_version.set_property('ellipsize', pango.ELLIPSIZE_END)
        column_name = gtk.TreeViewColumn(_('OS Version'), cell_version)
        column_name.set_cell_data_func(cell_version, column_data_func, 1)
        column_name.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        column_name.set_resizable(True)
        column_name.set_expand(True)
        column_name.set_min_width(75)
        self.source_treeview.append_column(column_name)

        cell_size = gtk.CellRendererText()
        cell_size.set_property('ellipsize', pango.ELLIPSIZE_END)
        column_name = gtk.TreeViewColumn(_('Size'), cell_size)
        column_name.set_cell_data_func(cell_size, column_data_func, 2)
        column_name.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        column_name.set_resizable(True)
        column_name.set_expand(False)
        column_name.set_min_width(75)
        self.source_treeview.append_column(column_name)

        # Drag and drop support.
        # FIXME evand 2009-04-28: Anything can be dropped on the source
        # treeview.  Ideally, the user should only be able to drop ISO and IMG
        # files.

        def motion_cb(wid, context, x, y, time):
            context.drag_status(gtk.gdk.ACTION_COPY, time)
            return True
        
        def drop_cb(w, context, x, y, time):
            target_list = w.drag_dest_get_target_list()
            target = w.drag_dest_find_target(context, target_list)
            selection = w.drag_get_data(context, target)
            context.finish(True, True)
            return True

        def data_received_cb(w, context, x, y, selection, target_type, timestamp):
            # FIXME evand 2009-04-28: Use the GNOME VFS?  Test with a sshfs
            # nautilus window.
            file = selection.data.strip('\r\n\x00')
            if file.startswith('file://'):
                file = file[7:]
            elif file.startswith('file:'):
                file = file[5:]
            self.backend.add_image(file)
            
        self.source_treeview.drag_dest_set(gtk.gdk.ACTION_DEFAULT,
            [('text/uri-list', 0, 600)], gtk.gdk.ACTION_COPY)
        self.source_treeview.connect('drag_motion', motion_cb)
        self.source_treeview.connect('drag_drop', drop_cb)
        self.source_treeview.connect('drag-data-received', data_received_cb)

    def update_target(self, udi):
        m = self.dest_treeview.get_model()
        iterator = m.get_iter_first()
        # Update the warning / error icon in the treeview.
        while iterator is not None:
            if m.get_value(iterator, 0) == udi:
                m.row_changed(m.get_path(iterator), iterator)
                break
            iterator = m.iter_next(iterator)
        # Update persistence maximum value.
        self.persist_vbox.set_sensitive(False)
        self.persist_enabled_vbox.set_sensitive(False)
        target = self.backend.targets[udi]
        persist_mb = target['persist'] / 1024 / 1024
        if persist_mb > MIN_PERSISTENCE:
                self.persist_vbox.set_sensitive(True)
                self.persist_enabled_vbox.set_sensitive(True)
                self.persist_value.set_range(MIN_PERSISTENCE, persist_mb)
                self.persist_value.set_value(MIN_PERSISTENCE)
        # Update install button state.
        status = target['status']
        source = self.backend.get_current_source()
        if not source:
            self.button_install.set_sensitive(False)
            return
        stype = self.backend.sources[source]['type']
        if status == CAN_USE:
            self.button_install.set_sensitive(True)
        else:
            self.button_install.set_sensitive(False)
        # Update the destination status message.
        self.open_dest.hide()
        if status == CANNOT_USE:
            msg = _('The device is not large enough to hold this image.')
        elif status == NEED_SPACE:
            msg = _('There is not enough free space for this image.')
            self.open_dest.show()
        else:
            msg = ''
        self.dest_status.set_text(msg)
        
    def selection_changed_source(self, selection):
        model, iterator = selection.get_selected()
        if not iterator:
            return
        udi = model[iterator][0]
        self.backend.set_current_source(udi)
        self.selection_changed_target(self.dest_treeview.get_selection())

    def selection_changed_target(self, selection):
        '''The selected partition has changed and the bounds on the persistence
        slider need to be changed, or the slider needs to be disabled, to
        reflect the amount of free space on the partition.'''
        
        model, iterator = selection.get_selected()
        if not iterator:
            return
        udi = model[iterator][0]
        self.update_target(udi)

    def setup_targets_treeview(self):
        def column_data_func(layout, cell, model, iterator, column):
            if not self.backend:
                return
            udi = model[iterator][0]
            dev = self.backend.targets[udi]
            
            if column == 0:
                cell.set_property('text', dev['device'])
            elif column == 1:
                if udi in self.names:
                    cell.set_property('text', self.names[udi])
                else:
                    cell.set_property('text', dev['label'])
            elif column == 2:
                cell.set_property('text', format_size(dev['capacity']))
            elif column == 3:
                free = dev['free']
                if free >= 0:
                    cell.set_property('text', format_size(free))
                else:
                    cell.set_property('text', '')

        def pixbuf_data_func(column, cell, model, iterator):
            if not self.backend:
                return
            udi = model[iterator][0]
            dev = self.backend.targets[udi]
            status = dev['status']

            if status == NEED_SPACE:
                cell.set_property('stock-id', gtk.STOCK_DIALOG_WARNING)
            elif status == CANNOT_USE:
                # TODO evand 2009-05-05: Implement disabled rows as a
                # replacement?
                cell.set_property('stock-id', gtk.STOCK_DIALOG_ERROR)
            else:
                if udi in self.icons:
                    cell.set_property('icon-name', self.icons[udi])
                else:
                    cell.set_property('stock-id', None)

        list_store = gtk.ListStore(str)
        list_store.set_sort_column_id(0, gtk.SORT_ASCENDING)
        self.dest_treeview.set_model(list_store)

        column_name = gtk.TreeViewColumn()
        column_name.set_title(_('Device'))
        cell_name = gtk.CellRendererText()
        cell_name.set_property('ellipsize', pango.ELLIPSIZE_END)
        cell_pixbuf = gtk.CellRendererPixbuf()
        column_name.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        column_name.set_resizable(True)
        column_name.set_expand(True)
        column_name.set_min_width(75)
        column_name.pack_start(cell_pixbuf, expand=False)
        column_name.pack_start(cell_name, expand=True)
        self.dest_treeview.append_column(column_name)
        column_name.set_cell_data_func(cell_name, column_data_func, 0)
        column_name.set_cell_data_func(cell_pixbuf, pixbuf_data_func)
        
        cell_name = gtk.CellRendererText()
        cell_name.set_property('ellipsize', pango.ELLIPSIZE_END)
        column_name = gtk.TreeViewColumn(_('Label'), cell_name)
        column_name.set_cell_data_func(cell_name, column_data_func, 1)
        column_name.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        column_name.set_resizable(True)
        column_name.set_expand(True)
        column_name.set_min_width(75)
        self.dest_treeview.append_column(column_name)

        cell_capacity = gtk.CellRendererText()
        cell_capacity.set_property('ellipsize', pango.ELLIPSIZE_END)
        column_name = gtk.TreeViewColumn(_('Capacity'), cell_capacity)
        column_name.set_cell_data_func(cell_capacity, column_data_func, 2)
        column_name.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        column_name.set_resizable(True)
        column_name.set_expand(False)
        column_name.set_min_width(75)
        self.dest_treeview.append_column(column_name)

        cell_free = gtk.CellRendererText()
        cell_free.set_property('ellipsize', pango.ELLIPSIZE_END)
        column_name = gtk.TreeViewColumn(_('Free Space'), cell_free)
        column_name.set_cell_data_func(cell_free, column_data_func, 3)
        column_name.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        column_name.set_resizable(True)
        column_name.set_expand(False)
        column_name.set_min_width(75)
        self.dest_treeview.append_column(column_name)

    def add_file_source_dialog(self, *args):
        filename = ''
        chooser = gtk.FileChooserDialog(title=None,action=gtk.FILE_CHOOSER_ACTION_OPEN,
            buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        for p, n in (('*.iso', _('CD Images')), ('*.img', _('Disk Images'))):
            filter = gtk.FileFilter()
            filter.add_pattern(p)
            filter.set_name(n)
            chooser.add_filter(filter)
        folder = os.path.expanduser('~')
        chooser.set_current_folder(folder)
        response = chooser.run()
        if response == gtk.RESPONSE_OK:
            filename = chooser.get_filename()
            chooser.destroy()
            self.backend.add_image(filename)
        elif response == gtk.RESPONSE_CANCEL:
            chooser.destroy()

    def install(self, widget):
        source = self.get_source()
        target = self.get_target()
        persist = self.get_persistence()
        # TODO evand 2009-07-31: Make these the default values in the
        # GtkBuilder file.
        starting_up = _('Starting up...')
        self.progress_title.set_markup('<big><b>' + starting_up + '</b></big>')
        self.progress_info.set_text('')
        if source and target:
            self.install_window.show()
            self.window.hide()
            self.delete_timeout(self.update_loop)
            try:
                self.backend.install(source, target, persist,
                                     allow_system_internal=self.allow_system_internal)
            except:
                self._fail()

    @thread_wrap
    def progress(self, complete, remaining, speed):
        if self.pulsing:
            self.progress_info.set_text('')
            return
        # Ahem.
        if complete > 100:
            complete = 100
        self.progress_bar.set_fraction(complete / 100.0)
        if remaining and speed:
            # TODO evand 2009-07-24: Could use a time formatting function
            # like our human size function.
            mins = int(remaining / 60)
            secs = int(remaining % 60)
            text = _('%d%% complete (%dm%ss remaining)') % \
                    (complete, mins, secs)
            self.progress_info.set_text(text)
        else:
            self.progress_info.set_text(_('%d%% complete') % complete)

    @thread_wrap
    def progress_message(self, message):
        self.progress_title.set_markup('<big><b>' + message + '</b></big>')

    @thread_wrap
    def progress_pulse(self):
        def pulse():
            self.progress_bar.pulse()
            return True
        self.pulsing = self.add_timeout(100, pulse)

    @thread_wrap
    def progress_pulse_stop(self):
        if self.pulsing:
            self.delete_timeout(self.pulsing)
            self.pulsing = False

    @thread_wrap
    def retry(self, message):
        retry_dialog = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL |
                                         gtk.DIALOG_DESTROY_WITH_PARENT,
                                         gtk.MESSAGE_ERROR, gtk.BUTTONS_YES_NO,
                                         message)
        response = retry_dialog.run()
        retry_dialog.destroy()
        return response == gtk.RESPONSE_YES

    
    def quit(self, *args):
        self.backend.cancel_install()
        if gtk.main_level() > 0:
            gtk.main_quit()

    @thread_wrap
    def failure(self, message=None):
        self._fail(message)
    
    def _fail(self, message=None):
        logging.exception('Installation failed.')
        # FIXME: evand 2009-07-28: Do we need this?
        self.warning_dialog.hide()
        self.install_window.hide()
        if not message:
            message = _('Installation failed.')
        self.failed_dialog_label.set_text(message)
        self.failed_dialog.run()
        gtk.main_quit()
    
    @thread_wrap
    def success(self):
        self.backend.unmount()
        self.warning_dialog.hide()
        self.install_window.hide()
        self.finished_dialog.run()
        gtk.main_quit()

    def notify(self, message):
        dialog = gtk.MessageDialog(self.window, 0, gtk.DIALOG_MODAL |
                                   gtk.DIALOG_DESTROY_WITH_PARENT,
                                   gtk.MESSAGE_WARNING, gtk.BUTTONS_CLOSE,
                                   message)
        dialog.run()
        dialog.destroy()

    def format_ended(self):
        self.backend.formatting = None
        self.window.window.set_cursor(None)
        self.format_dest.set_sensitive(True)

    @thread_wrap
    def format_failed(self, message):
        self.backend.formatting = None
        self.window.window.set_cursor(None)
        self.format_dest.set_sensitive(True)
        # TODO sort through error types (message.get_dbus_name()) in backend,
        # individual functions in frontend for each error type.
        d = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL,
                              type=gtk.MESSAGE_ERROR,
                              buttons=gtk.BUTTONS_CLOSE)
        d.set_markup(str(message))
        d.run()
        d.destroy()

    def format_dest_clicked(self, *args):
        model, iterator = self.dest_treeview.get_selection().get_selected()
        if not iterator:
            return
        udi = model[iterator][0]
        d = gtk.MessageDialog(self.window, gtk.DIALOG_MODAL,
                type=gtk.MESSAGE_QUESTION, buttons=gtk.BUTTONS_YES_NO)
        # TODO information about the device we're about to format.
        d.set_markup(_('Are you sure you want to erase the entire disk?'))
        response = d.run()
        d.destroy()
        if response == gtk.RESPONSE_YES:
            self.window.window.set_cursor(gtk.gdk.Cursor(gtk.gdk.WATCH))
            # While we can support formatting multiple devices at once, lets
            # not for simplicity's sake.
            self.format_dest.set_sensitive(False)
            self.backend.format(udi)

    def open_dest_folder(self, *args):
        model, iterator = self.dest_treeview.get_selection().get_selected()
        if not iterator:
            logging.error('Open button pressed but there was no selection.')
            return
        disk = model[iterator][0]
        dir = self.backend.open(disk)
        if dir:
            subprocess.Popen(['gnome-open', dir])

def _append_to_list_and_select(treeview, new_row, force_selection):
    model = treeview.get_model()
    new_iter = model.append(new_row)
    if force_selection or (treeview.get_selection().get_selected()[1] is None):
        treeview.set_cursor(model.get_path(new_iter))

# vim: set ai et sts=4 tabstop=4 sw=4:
