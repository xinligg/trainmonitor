#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This module provides widgets to use aptdaemon in a GTK application.
"""
# Copyright (C) 2008-2009 Sebastian Heinlein <devel@glatzor.de>
#
# Licensed under the GNU General Public License Version 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

__author__ = "Sebastian Heinlein <devel@glatzor.de>"

__all__ = ("AptConfigFileConflictDialog", "AptCancelButton", "AptConfirmDialog",
           "AptProgressDialog", "AptTerminalExpander", "AptStatusIcon",
           "AptRoleIcon", "AptStatusAnimation", "AptRoleLabel",
           "AptStatusLabel", "AptMediumRequiredDialog", "AptMessageDialog",
           "AptErrorDialog", "AptProgressBar", "DiffView", "AptTerminal")

import difflib
import gettext
import os
import pty
import re

import apt_pkg
import dbus
import dbus.mainloop.glib
import gobject
import gtk
import pango
import pygtk
import vte

import client
from enums import *
from defer import inline_callbacks, return_value

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

_ = lambda msg: gettext.dgettext("aptdaemon", msg)

(COLUMN_ID,
 COLUMN_PACKAGE) = range(2)


class AptStatusIcon(gtk.Image):
    """
    Provides a gtk.Image which shows an icon representing the status of a
    aptdaemon transaction
    """
    def __init__(self, transaction=None, size=gtk.ICON_SIZE_DIALOG):
        gtk.Image.__init__(self)
        self.icon_size = size
        self.icon_name = None
        self._signals = []
        self.set_alignment(0, 0)
        if transaction != None:
            self.set_transaction(transaction)

    def set_transaction(self, transaction):
        """Connect to the given transaction"""
        for sig in self._signals:
            gobject.source_remove(sig)
        self._signals = []
        self._signals.append(transaction.connect("status-changed",
                                                 self._on_status_changed))

    def set_icon_size(self, size):
        """Set the icon size to gtk stock icon size value"""
        self.icon_size = size

    def _on_status_changed(self, transaction, status):
        """Set the status icon according to the changed status"""
        icon_name = get_status_icon_name_from_enum(status)
        if icon_name is None:
            icon_name = gtk.STOCK_MISSING_IMAGE
        if icon_name != self.icon_name:
            self.set_from_icon_name(icon_name, self.icon_size)
            self.icon_name = icon_name


class AptRoleIcon(AptStatusIcon):
    """
    Provides a gtk.Image which shows an icon representing the role of an
    aptdaemon transaction
    """
    def set_transaction(self, transaction):
        for sig in self._signals:
            gobject.source_remove(sig)
        self._signals = []
        self._signals.append(transaction.connect("role-changed",
                                                 self._on_role_changed))
        self._on_role_changed(transaction, transaction.role)

    def _on_role_changed(self, transaction, role_enum):
        """Show an icon representing the role"""
        icon_name = get_role_icon_name_from_enum(role_enum)
        if icon_name is None:
            icon_name = gtk.STOCK_MISSING_IMAGE
        if icon_name != self.icon_name:
            self.set_from_icon_name(icon_name, self.icon_size)
            self.icon_name = icon_name


class AptStatusAnimation(AptStatusIcon):
    """
    Provides a gtk.Image which shows an animation representing the 
    transaction status
    """
    def __init__(self, transaction=None, size=gtk.ICON_SIZE_DIALOG):
        AptStatusIcon.__init__(self, transaction, size)
        self.animation = []
        self.ticker = 0
        self.frame_counter = 0
        self.iter = 0
        name = get_status_animation_name_from_enum(STATUS_WAITING)
        fallback = get_status_icon_name_from_enum(STATUS_WAITING)
        self.set_animation(name, fallback)

    def set_animation(self, name, fallback=None, size=None):
        """Show and start the animation of the given name and size"""
        if name == self.icon_name:
            return
        if size is not None:
            self.icon_size = size
        self.stop_animation()
        animation = []
        (width, height) = gtk.icon_size_lookup(self.icon_size)
        theme = gtk.icon_theme_get_default()
        if name is not None and theme.has_icon(name):
            pixbuf = theme.load_icon(name, width, 0)
            rows = pixbuf.get_height() / height
            cols = pixbuf.get_width() / width
            for r in range(rows):
                for c in range(cols):
                    animation.append(pixbuf.subpixbuf(c * width, r * height, 
                                                      width, height))
            if len(animation) > 0:
                self.animation = animation
                self.iter = 0
                self.set_from_pixbuf(self.animation[0])
                self.start_animation()
            else:
                self.set_from_pixbuf(pixbuf)
            self.icon_name = name
        elif fallback is not None and theme.has_icon(fallback):
            self.set_from_icon_name(fallback, self.icon_size)
            self.icon_name = fallback
        else:
            self.set_from_icon_name(gtk.STOCK_MISSING_IMAGE)

    def start_animation(self):
        """Start the animation"""
        if self.ticker == 0:
            self.ticker = gobject.timeout_add(200, self._advance)

    def stop_animation(self):
        """Stop the animation"""
        if self.ticker != 0:
            gobject.source_remove(self.ticker)
            self.ticker = 0

    def _advance(self):
        """
        Show the next frame of the animation and stop the animation if the
        widget is no longer visible
        """
        if self.get_property("visible") == False:
            self.ticker = 0
            return False
        self.iter = self.iter + 1
        if self.iter >= len(self.animation):
            self.iter = 0
        self.set_from_pixbuf(self.animation[self.iter])
        return True

    def _on_status_changed(self, transaction, status):
        """
        Set the animation according to the changed status
        """
        name = get_status_animation_name_from_enum(status)
        fallback = get_status_icon_name_from_enum(status)
        self.set_animation(name, fallback)


class AptRoleLabel(gtk.Label):
    """
    Status label for the running aptdaemon transaction
    """
    def __init__(self, transaction=None):
        gtk.Label.__init__(self)
        self.set_alignment(0, 0)
        self.set_ellipsize(pango.ELLIPSIZE_END)
        self._signals = []
        if transaction != None:
            self.set_transaction(transaction)

    def set_transaction(self, transaction):
        """Connect the status label to the given aptdaemon transaction"""
        for sig in self._signals:
            gobject.source_remove(sig)
        self._signals = []
        self._on_role_changed(transaction, transaction.role)
        self._signals.append(transaction.connect("role-changed",
                                                 self._on_role_changed))

    def _on_role_changed(self, transaction, role):
        """Set the role text."""
        self.set_markup(get_role_localised_present_from_enum(role))


class AptStatusLabel(gtk.Label):
    """
    Status label for the running aptdaemon transaction
    """
    def __init__(self, transaction=None):
        gtk.Label.__init__(self)
        self.set_alignment(0, 0)
        self.set_ellipsize(pango.ELLIPSIZE_END)
        self._signals = []
        if transaction != None:
            self.set_transaction(transaction)

    def set_transaction(self, transaction):
        """Connect the status label to the given aptdaemon transaction"""
        for sig in self._signals:
            gobject.source_remove(sig)
        self._signals = []
        self._signals.append(transaction.connect("status-changed",
                                                 self._on_status_changed))
        self._signals.append(transaction.connect("status-details-changed",
                                               self._on_status_details_changed))

    def _on_status_changed(self, transaction, status):
        """Set the status text according to the changed status"""
        self.set_markup(get_status_string_from_enum(status))

    def _on_status_details_changed(self, transaction, text):
        """Set the status text to the one reported by apt"""
        self.set_markup(text)


class AptProgressBar(gtk.ProgressBar):
    """
    Provides a gtk.Progress which represents the progress of an aptdaemon
    transactions
    """
    def __init__(self, transaction=None):
        gtk.ProgressBar.__init__(self)
        self.set_ellipsize(pango.ELLIPSIZE_END)
        self.set_text(" ")
        self.set_pulse_step(0.05)
        self._signals = []
        if transaction != None:
            self.set_transaction(transaction)

    def set_transaction(self, transaction):
        """Connect the progress bar to the given aptdaemon transaction"""
        for sig in self._signals:
            gobject.source_remove(sig)
        self._signals = []
        self._signals.append(transaction.connect("finished", self._on_finished))
        self._signals.append(transaction.connect("progress-changed",
                                                 self._on_progress_changed))
        self._signals.append(transaction.connect("progress-details-changed",
                                                 self._on_progress_details))

    def _on_progress_changed(self, transaction, progress):
        """
        Update the progress according to the latest progress information
        """
        if progress > 100:
            self.pulse()
        else:
            self.set_fraction(progress/100.0)

    def _on_progress_details(self, transaction, items_done, items_total,
                             bytes_done, bytes_total, speed, eta):
        """
        Update the progress bar text according to the latest progress details
        """
        if items_total == 0 and bytes_total == 0:
            self.set_text(" ")
            return
        if speed != 0:
            self.set_text(_("Downloaded %sB of %sB "
                            "at %sB/s") % (apt_pkg.size_to_str(bytes_done),
                                          apt_pkg.size_to_str(bytes_total),
                                          apt_pkg.size_to_str(speed)))
        else:
            self.set_text(_("Downloaded %sB "
                            "of %sB") % (apt_pkg.size_to_str(bytes_done),
                                         apt_pkg.size_to_str(bytes_total)))

    def _on_finished(self, transaction, exit):
        """Set the progress to 100% when the transaction is complete"""
        self.set_fraction(1)


class AptDetailsExpander(gtk.Expander):

    def __init__(self, transaction=None, terminal=True):
        gtk.Expander.__init__(self, _("Details"))
        self.show_terminal = terminal
        self._signals = []
        self.set_sensitive(False)
        self.set_expanded(False)
        if self.show_terminal:
            self.terminal = AptTerminal()
        else:
            self.terminal = None
        self.download_view = AptDownloadsView()
        self.download_scrolled = gtk.ScrolledWindow()
        self.download_scrolled.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.download_scrolled.set_policy(gtk.POLICY_NEVER,
                                          gtk.POLICY_AUTOMATIC)
        self.download_scrolled.add(self.download_view)
        hbox = gtk.HBox()
        hbox.pack_start(self.download_scrolled, True, True)
        hbox.pack_start(self.terminal, True, True)
        self.add(hbox)
        if transaction != None:
            self.set_transaction(transaction)

    def set_transaction(self, transaction):
        """Connect the status label to the given aptdaemon transaction"""
        for sig in self._signals:
            gobject.source_remove(sig)
        self._signals.append(transaction.connect("status-changed",
                                          self._on_status_changed))
        self._signals.append(transaction.connect("terminal-attached-changed",
                                          self._on_terminal_attached_changed))
        self.terminal.set_transaction(transaction)
        self.download_view.set_transaction(transaction)

    def _on_status_changed(self, trans, status):
        if status == STATUS_DOWNLOADING:
            self.set_sensitive(True)
            self.download_scrolled.show()
            if self.terminal:
                self.terminal.hide()
        elif status == STATUS_COMMITTING:
            self.download_scrolled.hide()
            if self.terminal:
                self.terminal.show()
                self.set_sensitive(True)
            else:
                self.set_expanded(False)
                self.set_sensitive(False)
        else:
            self.download_scrolled.hide()
            if self.terminal:
                self.terminal.hide()
            self.set_sensitive(False)
            self.set_expanded(False)

    def _on_terminal_attached_changed(self, transaction, attached):
        """Connect the terminal to the pty device"""
        if attached and self.terminal:
            self.set_sensitive(True)


class AptTerminal(vte.Terminal):

    def __init__(self, transaction=None):
        vte.Terminal.__init__(self)
        self._signals = []
        self._master, self._slave = pty.openpty()
        self._ttyname = os.ttyname(self._slave)
        self.set_size(80, 24)
        self.set_pty(self._master)
        if transaction != None:
            self.set_transaction(transaction)

    def set_transaction(self, transaction):
        """Connect the status label to the given aptdaemon transaction"""
        for sig in self._signals:
            gobject.source_remove(sig)
        self._signals.append(transaction.connect("terminal-attached-changed",
                                          self._on_terminal_attached_changed))
        self._transaction = transaction
        self._transaction.set_terminal(self._ttyname)

    def _on_terminal_attached_changed(self, transaction, attached):
        """Show the terminal"""
        self.set_sensitive(attached)

class AptCancelButton(gtk.Button):
    """
    Provides a gtk.Button which allows to cancel a running aptdaemon
    transaction
    """
    def __init__(self, transaction=None):
        gtk.Button.__init__(self, stock=gtk.STOCK_CANCEL)
        self.set_sensitive(True)
        self._signals = []
        if transaction != None:
            self.set_transaction(transaction)

    def set_transaction(self, transaction):
        """Connect the status label to the given aptdaemon transaction"""
        for sig in self._signals:
            gobject.source_remove(sig)
        self._signals = []
        self._signals.append(transaction.connect("finished", self._on_finished))
        self._signals.append(transaction.connect("cancellable-changed",
                                                 self._on_cancellable_changed))
        self.connect("clicked", self._on_clicked, transaction)

    def _on_cancellable_changed(self, transaction, cancellable):
        """
        Enable the button if cancel is allowed and disable it in the other case
        """
        self.set_sensitive(cancellable)

    def _on_finished(self, transaction, status):
        self.set_sensitive(False)

    def _on_clicked(self, button, transaction):
        transaction.cancel()
        self.set_sensitive(False)


class AptDownloadsView(gtk.TreeView):

    """A gtk.TreeView which displays the progress and status of each dowload
    of a transaction.
    """

    COL_TEXT, COL_PROGRESS, COL_URI = range(3)

    def __init__(self, transaction=None):
        gtk.TreeView.__init__(self)
        model = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_INT,
                              gobject.TYPE_STRING)
        self.set_model(model)
        self.props.headers_visible = False
        self.set_rules_hint(True)
        self._download_map = {}
        self._signals = []
        if transaction != None:
            self.set_transaction(transaction)
        cell_uri = gtk.CellRendererText()
        cell_uri.props.ellipsize = pango.ELLIPSIZE_END
        column_download = gtk.TreeViewColumn(_("File"))
        column_download.pack_start(cell_uri, True)
        column_download.add_attribute(cell_uri, "markup", self.COL_TEXT)
        cell_progress = gtk.CellRendererProgress()
        #TRANSLATORS: header of the progress download column
        column_progress = gtk.TreeViewColumn(_("%"))
        column_progress.pack_start(cell_progress, True)
        column_progress.set_cell_data_func(cell_progress, self._data_progress)
        self.append_column(column_progress)
        self.append_column(column_download)
        self.set_tooltip_column(self.COL_URI)

    def set_transaction(self, transaction):
        """Connect the download view to the given aptdaemon transaction"""
        for sig in self._signals:
            gobject.source_remove(sig)
        self._signals = []
        self._signals.append(transaction.connect("progress-download-changed",
                                                 self._on_download_changed))

    def _on_download_changed(self, transaction, uri, status, desc, full_size,
                             downloaded, message):
        """Callback for a changed download progress."""
        try:
            progress = downloaded * 100 / full_size
        except ZeroDivisionError:
            progress = -1
        if status == DOWNLOAD_DONE:
            progress = 100
        if progress > 100:
            progress = 100
        text = desc[:]
        text += "\n<small>"
        #TRANSLATORS: %s is the full size in Bytes, e.g. 198M
        if status == DOWNLOAD_FETCHING:
            text += _("Downloaded %sB of %sB") % \
                    (apt_pkg.size_to_str(downloaded),
                     apt_pkg.size_to_str(full_size))
        elif status == DOWNLOAD_DONE:
            if full_size != 0:
                text += _("Downloaded %sB") % apt_pkg.size_to_str(full_size)
            else:
                text += _("Downloaded")
        else:
            text += get_download_status_from_enum(status)
        text += "</small>"
        model = self.get_model()
        try:
            iter = self._download_map[uri]
        except KeyError:
            adj = self.get_vadjustment()
            is_scrolled_down = adj.value + adj.page_size == adj.upper
            iter = model.append((text, progress, uri))
            self._download_map[uri] = iter
            if is_scrolled_down:
                # If the treeview was scrolled to the end, do this again
                # after appending a new item
                self.scroll_to_cell(model.get_path(iter))
        else:
            model.set(iter, self.COL_TEXT, text)
            model.set(iter, self.COL_PROGRESS, progress)

    def _data_progress(self, column, cell, model, iter):
        progress = model.get_value(iter, self.COL_PROGRESS)
        if progress == -1:
            cell.props.pulse = progress
        else:
            cell.props.value = progress


class AptProgressDialog(gtk.Dialog):
    """
    Complete progress dialog for long taking aptdaemon transactions, which
    features a progress bar, cancel button, status icon and label
    """

    __gsignals__ = {"finished": (gobject.SIGNAL_RUN_FIRST,
                                 gobject.TYPE_NONE, ())}

    def __init__(self, transaction=None, parent=None, terminal=True,
                 debconf=True):
        gtk.Dialog.__init__(self, buttons=None, parent=parent)
        self._expanded_size = None
        self.debconf = debconf
        # Setup the dialog
        self.set_border_width(6)
        self.set_has_separator(False)
        self.set_resizable(False)
        self.vbox.set_spacing(6)
        # Setup the cancel button
        self.button_cancel = AptCancelButton(transaction)
        self.action_area.pack_start(self.button_cancel, False, False, 0)
        # Setup the status icon, label and progressbar
        hbox = gtk.HBox()
        hbox.set_spacing(12)
        hbox.set_border_width(6)
        self.icon = AptRoleIcon()
        hbox.pack_start(self.icon, False, True, 0)
        vbox = gtk.VBox()
        vbox.set_spacing(12)
        self.label_role = gtk.Label()
        self.label_role.set_alignment(0, 0)
        vbox.pack_start(self.label_role, False, True, 0)
        vbox_progress = gtk.VBox()
        vbox_progress.set_spacing(6)
        self.progress = AptProgressBar()
        vbox_progress.pack_start(self.progress, False, True, 0)
        self.label = AptStatusLabel()
        self.label._on_status_changed(None, STATUS_WAITING)
        vbox_progress.pack_start(self.label, False, True, 0)
        vbox.pack_start(vbox_progress, False, True, 0)
        hbox.pack_start(vbox, True, True, 0)
        self.expander = AptDetailsExpander(terminal=terminal)
        self.expander.connect("notify::expanded", self._on_expanded)
        vbox.pack_start(self.expander, True, True, 0)
        self.vbox.pack_start(hbox, True, True, 0)
        self._transaction = None
        self._signals = []
        self.set_title("")
        self.realize()
        self.progress.set_size_request(350, -1)
        self.window.set_functions(gtk.gdk.FUNC_MOVE|gtk.gdk.FUNC_RESIZE)
        if transaction != None:
            self.set_transaction(transaction)
        # catch ESC and behave as if cancel was clicked
        self.connect("delete-event", self._on_dialog_delete_event)

    def _on_dialog_delete_event(self, dialog, event):
        self.button_cancel.clicked()
        return True

    def _on_expanded(self, expander, param):
        # Make the dialog resizable if the expander is expanded
        # try to restore a previous size
        if not expander.get_expanded():
            self._expanded_size = self.get_size()
            self.set_resizable(False)
        elif self._expanded_size:
            self.set_resizable(True)
            self.resize(*self._expanded_size)
        else:
            self.set_resizable(True)

    def run(self, attach=False, close_on_finished=True, show_error=True,
            reply_handler=None, error_handler=None):
        """Run the transaction and show the progress in the dialog.

        Keyword arguments:
        attach -- do not start the transaction but instead only monitor
                  an already running one
        close_on_finished -- if the dialog should be closed when the
                  transaction is complete
        show_error -- show a dialog with the error message
        """
        try:
            self._run(attach, close_on_finished, show_error)
        except Exception, error:
            if error_handler:
                error_handler(error)
            else:
                raise
        if reply_handler:
            reply_handler()

    @inline_callbacks
    def _run(self, attach, close_on_finished, show_error):
        parent = self.get_transient_for()
        sig = self._transaction.connect("finished", self._on_finished,
                                        close_on_finished, show_error)
        self._signals.append(sig)
        if attach:
            yield self._transaction.attach()
        else:
            if self.debconf:
                yield self._transaction.set_debconf_frontend("gnome")
            yield self._transaction.run()
        self.show_all()

    def _on_role_changed(self, transaction, role_enum):
        """Show the role of the transaction in the dialog interface"""
        role = get_role_localised_present_from_enum(role_enum)
        self.set_title(role)
        self.label_role.set_markup("<big><b>%s</b></big>" % role)

    def set_transaction(self, transaction):
        """Connect the dialog to the given aptdaemon transaction"""
        for sig in self._signals:
            gobject.source_remove(sig)
        self._signals = []
        self._signals.append(transaction.connect("role-changed",
                                                 self._on_role_changed))
        self._signals.append(transaction.connect("medium-required",
                                                 self._on_medium_required))
        self._signals.append(transaction.connect("config-file-conflict",
                             self._on_config_file_conflict))
        self._on_role_changed(transaction, transaction.role)
        self.progress.set_transaction(transaction)
        self.icon.set_transaction(transaction)
        self.label.set_transaction(transaction)
        self.expander.set_transaction(transaction)
        self._transaction = transaction

    def _on_medium_required(self, transaction, medium, drive):
        dialog = AptMediumRequiredDialog(medium, drive, self)
        res = dialog.run()
        dialog.hide()
        if res == gtk.RESPONSE_OK:
            self._transaction.provide_medium(medium)
        else:
            self._transaction.cancel()

    def _on_config_file_conflict(self, transaction, old, new):
        dialog = AptConfigFileConflictDialog(old, new, self)
        res = dialog.run()
        dialog.hide()
        if res == gtk.RESPONSE_YES:
            self._transaction.resolve_config_file_conflict(old, "replace")
        else:
            self._transaction.resolve_config_file_conflict(old, "keep")

    def _on_finished(self, transaction, status, close, show_error):
        if close:
            self.hide()
        if status == EXIT_FAILED and show_error:
            err_dia = AptErrorDialog(self._transaction.error, self)
            err_dia.run()
            err_dia.hide()
        self.emit("finished")


class _ExpandableDialog(gtk.Dialog):

    """Dialog with an expander."""

    def __init__(self, parent=None, stock_type=None, expanded_child=None,
                 expander_label=None, title=None, message=None, buttons=None):
        """Return an _AptDaemonDialog instance.

        Keyword arguments:
        parent -- set the dialog transient for the given gtk.Window
        stock_type -- type of the Dialog, defaults to gtk.STOCK_DIALOG_QUESTION
        expanded_child -- Widget which should be expanded
        expander_label -- label for the expander
        title -- a news header like title of the dialog
        message -- the message which should be shown in the dialog
        buttons -- tuple containing button text/reponse id pairs, defaults
                   to a close button
        """
        if not buttons:
            buttons = (gtk.STOCK_CLOSE, gtk.RESPONSE_CLOSE)
        gtk.Dialog.__init__(self, parent=parent, buttons=buttons)
        self.set_resizable(True)
        self.set_border_width(6)
        self.vbox.set_spacing(12)
        if not stock_type:
            stock_type = gtk.STOCK_DIALOG_QUESTION
        icon = gtk.image_new_from_stock(stock_type, gtk.ICON_SIZE_DIALOG)
        icon.set_alignment(0 ,0)
        hbox_base = gtk.HBox()
        hbox_base.set_spacing(12)
        hbox_base.set_border_width(6)
        vbox_left = gtk.VBox()
        vbox_left.set_spacing(12)
        hbox_base.pack_start(icon, False, True)
        hbox_base.pack_start(vbox_left, True, True)
        self.label = gtk.Label()
        self.label.set_selectable(True)
        self.label.set_alignment(0, 0)
        self.label.set_line_wrap(True)
        vbox_left.pack_start(self.label, False, True)
        self.set_has_separator(False)
        self.vbox.pack_start(hbox_base, True, True)
        # The expander widget
        self.expander = gtk.Expander(label=expander_label)
        self.expander.set_spacing(6)
        self.expander.set_use_underline(True)
        self.expander.connect("notify::expanded", self._on_expanded)
        vbox_left.pack_start(self.expander, True, True)
        self._expanded_size = self.get_size()
        # Set some initial data
        text = ""
        if title:
            text = "<b><big>%s</big></b>" % title
        if message:
            if text:
                text += "\n\n"
            text += message
        self.label.set_markup(text)
        if expanded_child:
            self.expander.add(expanded_child)

    def _on_expanded(self, expander, param):
        if expander.get_expanded():
            self.set_resizable(True)
            self.resize(*self._expanded_size)
        else:
            self._expanded_size = self.get_size()
            self.set_resizable(False)


class AptMediumRequiredDialog(gtk.MessageDialog):

    """Dialog to ask for medium change."""

    def __init__(self, medium, drive, parent=None):
        gtk.MessageDialog.__init__(self, parent=parent,
                                   type=gtk.MESSAGE_INFO)
        #TRANSLATORS: %s represents the name of a CD or DVD
        text = _("CD/DVD '%s' is required") % medium
        #TRANSLATORS: %s is the name of the CD/DVD drive
        desc = _("Please insert the above CD/DVD into the drive '%s' to "
                 "install software packages from it.") % drive
        self.set_markup("<big><b>%s</b></big>\n\n%s" % (text, desc))
        self.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                         _("C_ontinue"), gtk.RESPONSE_OK)
        self.set_default_response(gtk.RESPONSE_OK)


class AptConfirmDialog(gtk.Dialog):

    """Dialog to confirm the changes that would be required by a transaction."""

    def __init__(self, trans, cache=None, parent=None):
        """Return an AptConfirmDialog instance.

        Keyword arguments:
        trans -- the transaction of which the dependencies should be shown
        cache -- an optional apt.cache.Cache() instance to provide more details
                 about packages
        parent -- set the dialog transient for the given gtk.Window
        """
        self.cache = cache
        self.trans = trans
        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                 _("C_ontinue"), gtk.RESPONSE_OK)
        gtk.Dialog.__init__(self, buttons=buttons)
        if isinstance(parent, gtk.gdk.Window):
            self.realize()
            self.window.set_transient_for(parent)
        else:
            self.set_transient_for(parent)
        self.set_resizable(True)
        self.set_border_width(6)
        self.vbox.set_spacing(12)
        icon = gtk.image_new_from_stock(gtk.STOCK_DIALOG_QUESTION,
                                        gtk.ICON_SIZE_DIALOG)
        icon.set_alignment(0 ,0)
        hbox_base = gtk.HBox()
        hbox_base.set_spacing(12)
        hbox_base.set_border_width(6)
        vbox_left = gtk.VBox()
        vbox_left.set_spacing(12)
        hbox_base.pack_start(icon, False, True)
        hbox_base.pack_start(vbox_left, True, True)
        self.label = gtk.Label()
        self.label.set_selectable(True)
        self.label.set_alignment(0, 0)
        self.label.set_line_wrap(True)
        vbox_left.pack_start(self.label, False, True)
        self.set_has_separator(False)
        self.vbox.pack_start(hbox_base, True, True)
        self.treestore = gtk.TreeStore(str)
        self.treeview = gtk.TreeView(self.treestore)
        self.treeview.set_headers_visible(False)
        self.treeview.set_rules_hint(True)
        self.column = gtk.TreeViewColumn()
        self.treeview.append_column(self.column)
        cell_icon = gtk.CellRendererPixbuf()
        self.column.pack_start(cell_icon, expand=False)
        self.column.set_cell_data_func(cell_icon, self.render_package_icon)
        cell_desc = gtk.CellRendererText()
        self.column.pack_start(cell_desc, expand=True)
        self.column.set_cell_data_func(cell_desc, self.render_package_desc)
        self.scrolled = gtk.ScrolledWindow()
        self.scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.scrolled.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.scrolled.add(self.treeview)
        vbox_left.pack_start(self.scrolled, True, True)
        self.set_default_response(gtk.RESPONSE_CANCEL)

    def _show_changes(self):
        """Show a message and the dependencies in the dialog."""
        self.treestore.clear()
        for index, msg in enumerate([_("Install"),
                                     _("Reinstall"),
                                     _("Remove"),
                                     _("Purge"),
                                     _("Upgrade"),
                                     _("Downgrade"),
                                     _("Skip upgrade")]):
            if self.trans.dependencies[index]:
                piter = self.treestore.append(None, ["<b>%s</b>" % msg])
                for pkg in self.trans.dependencies[index]:
                    for object in self.map_package(pkg):
                        self.treestore.append(piter, [object])
        # If there is only one type of changes (e.g. only installs) expand the
        # tree
        #FIXME: adapt the title and message accordingly
        #FIXME: Should we have different modes? Only show dependencies, only
        #       initial packages or both?
        msg = _("Please take a look at the list of changes below.")
        if len(self.treestore) == 1:
            filtered_store = self.treestore.filter_new(root=(0))
            self.treeview.expand_all()
            self.treeview.set_model(filtered_store)
            self.treeview.set_show_expanders(False)
            if self.trans.dependencies[PKGS_INSTALL]:
                title = _("Additional software has to be installed")
            elif self.trans.dependencies[PKGS_REINSTALL]:
                title = _("Additional software has to be re-installed")
            elif self.trans.dependencies[PKGS_REMOVE]:
                title = _("Additional software has to be removed")
            elif self.trans.dependencies[PKGS_PURGE]:
                title = _("Additional software has to be purged")
            elif self.trans.dependencies[PKGS_UPGRADE]:
                title = _("Additional software has to be upgraded")
            elif self.trans.dependencies[PKGS_DOWNGRADE]:
                title = _("Additional software has to be downgraded")
            elif self.trans.dependencies[PKGS_KEEP]:
                title = _("Updates will be skipped")
            if len(filtered_store) < 6:
                self.set_resizable(False)
                self.scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_NEVER)
            else:
                self.treeview.set_size_request(350, 200)
        else:
            title = _("Additional changes are required")
            self.treeview.set_size_request(350, 200)
            self.treeview.collapse_all()
        if self.trans.download:
            msg += "\n"
            msg += _("%sB will be downloaded in total.") % \
                    apt_pkg.size_to_str(self.trans.download)
        if self.trans.space < 0:
            msg += "\n"
            msg += _("%sB of disk space will be freed.") % \
                    apt_pkg.size_to_str(self.trans.space)
        elif self.trans.space > 0:
            msg += "\n"
            msg += _("%sB more disk space will be used.") % \
                    apt_pkg.size_to_str(self.trans.space)
        self.label.set_markup("<b><big>%s</big></b>\n\n%s" % (title, msg))


    def map_package(self, pkg):
        """Map a package to a different object type, e.g. applications
        and return a list of those.

        By default return the package itself inside a list.

        Override this method if you don't want to store package names
        in the treeview.
        """
        return [pkg]

    def render_package_icon(self, column, cell, model, iter):
        """Data func for the gtk.CellRendererPixbuf which shows the package.

        Override this method if you want to show custom icons for
        a package or map it to applications.
        """
        path = model.get_path(iter)
        if len(path) == 1:
            cell.props.visible = False
        else:
            cell.props.visible = True
        cell.props.icon_name = "applications-other"

    def render_package_desc(self, column, cell, model, iter):
        """Data func for the gtk.CellRendererText which shows the package.

        Override this method if you want to show more information about
        a package or map it to applications.
        """
        pkg_name = model.get_value(iter, 0)
        try:
            text = "%s\n<small>%s</small>" % (pkg_name,
                                              self.cache[pkg_name].summary)
        except (KeyError, TypeError):
            text = "%s" % pkg_name
        cell.set_property("markup", text)

    def run(self):
        self._show_changes()
        self.show_all()
        return gtk.Dialog.run(self)


class AptConfigFileConflictDialog(_ExpandableDialog):

    """Dialog to resolve conflicts between local and shipped
    configuration files.
    """

    def __init__(self, from_path, to_path, parent=None):
        self.from_path = from_path
        self.to_path = to_path
        #TRANSLATORS: %s is a file path
        title = _("Replace your changes in '%s' with a later version of "
                  "the configuration file?") % from_path
        msg = _("If you don't know why the file is there already, it is "
                "usually safe to replace it.")
        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        self.diffview = DiffView()
        self.diffview.set_size_request(-1, 200)
        scrolled.add(self.diffview)
        _ExpandableDialog.__init__(self, parent=parent,
                                   expander_label=_("_Changes"),
                                   expanded_child=scrolled,
                                   title=title, message=msg,
                                   buttons=(_("_Keep"), gtk.RESPONSE_NO,
                                            _("_Replace"), gtk.RESPONSE_YES))
        self.set_default_response(gtk.RESPONSE_NO)
 
    def run(self):
        self.show_all()
        self.diffview.show_diff(self.from_path, self.to_path)
        return _ExpandableDialog.run(self)


class DiffView(gtk.TextView):

    """Shows the difference between two files."""

    REGEX_RANGE = "^@@ \-(?P<from_start>[0-9]+),(?P<from_context>[0-9]+) " \
                  "\+(?P<to_start>[0-9]+),(?P<to_context>[0-9]+) @@"
    ELLIPSIS = "[…]\n"

    def __init__(self):
        self.buffer = gtk.TextBuffer()
        gtk.TextView.__init__(self, self.buffer)
        self.set_property("editable", False)
        self.set_cursor_visible(False)
        tags = self.buffer.get_tag_table()
        #FIXME: How to get better colors?
        tag_default = gtk.TextTag("default")
        tag_default.set_properties(font="Mono")
        tags.add(tag_default)
        tag_add = gtk.TextTag("add")
        tag_add.set_properties(font="Mono",
                               background='#8ae234')
        tags.add(tag_add)
        tag_remove = gtk.TextTag("remove")
        tag_remove.set_properties(font="Mono",
                                  background='#ef2929')
        tags.add(tag_remove)
        tag_num = gtk.TextTag("number")
        tag_num.set_properties(font="Mono",
                               background='#eee')
        tags.add(tag_num)

    def show_diff(self, from_path, to_path):
        """Show the difference between two files."""
        #FIXME: Use gio
        try:
            from_lines = open(from_path).readlines()
            to_lines = open(to_path).readlines()
        except IOError:
            return
        iter = self.buffer.get_start_iter()
        for line in difflib.unified_diff(from_lines, to_lines, lineterm=""):
            if line.startswith("@@"):
                match = re.match(self.REGEX_RANGE, line)
                line_number = int(match.group("from_start"))
                if line_number > 1:
                    self.buffer.insert_with_tags_by_name(iter, self.ELLIPSIS,
                                                         "default")
            elif line.startswith("---") or line.startswith("+++"):
                continue
            elif line.startswith(" "):
                line_number += 1
                self.buffer.insert_with_tags_by_name(iter, str(line_number),
                                                     "number")
                self.buffer.insert_with_tags_by_name(iter, line, "default")
            elif line.startswith("-"):
                line_number += 1
                self.buffer.insert_with_tags_by_name(iter, str(line_number),
                                                     "number")
                self.buffer.insert_with_tags_by_name(iter, line, "remove")
            elif line.startswith("+"):
                spaces = " " * len(str(line_number))
                self.buffer.insert_with_tags_by_name(iter, spaces, "number")
                self.buffer.insert_with_tags_by_name(iter, line, "add")


class AptMessageDialog(gtk.MessageDialog):
    """
    Dialog for aptdaemon messages with details in an expandable text view
    """
    def __init__(self, enum, details=None, parent=None):
        gtk.MessageDialog.__init__(self, parent=parent,
                                   type=gtk.MESSAGE_INFO,
                                   buttons=gtk.BUTTONS_CLOSE)
        text = get_msg_string_from_enum(enum)
        desc = get_msg_description_from_enum(enum)
        self.set_markup("<big><b>%s</b></big>\n\n%s" % (text, desc))
        self.set_details(details)

    def set_details(self, details):
        if details == "":
            return
        #TRANSLATORS: expander label in the error dialog
        expander = gtk.expander_new_with_mnemonic(_("_Details"))
        expander.set_spacing(6)
        scrolled = gtk.ScrolledWindow()
        scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        textview = gtk.TextView()
        buffer = textview.get_buffer()
        buffer.insert_at_cursor(details)
        scrolled.add(textview)
        expander.add(scrolled)
        box = self.label.get_parent()
        box.add(expander)
        expander.show_all()


class AptErrorDialog(AptMessageDialog):
    """
    Dialog for aptdaemon errors with details in an expandable text view
    """
    def __init__(self, error=None, parent=None):
        gtk.MessageDialog.__init__(self, parent=parent,
                                   type=gtk.MESSAGE_ERROR,
                                   buttons=gtk.BUTTONS_CLOSE)
        text = get_error_string_from_enum(error.code)
        desc = get_error_description_from_enum(error.code)
        self.set_markup("<big><b>%s</b></big>\n\n%s" % (text, desc))
        self.set_details(error.details)
