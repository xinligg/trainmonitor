# Orca
#
# Copyright 2004-2009 Sun Microsystems Inc.
# Copyright 2010 Joanmarie Diggs, Mesar Hameed
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., Franklin Street, Fifth Floor,
# Boston MA  02110-1301 USA.

"""The main module for the Orca screen reader."""

__id__        = "$Id$"
__version__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2004-2009 Sun Microsystems Inc." \
                "Copyright (c) 2010 Joanmarie Diggs, Mesar Hameed."
__license__   = "LGPL"

# We're going to force the name of the app to "orca" so pygtk
# will end up showing us as "orca" to the AT-SPI.  If we don't
# do this, the name can end up being "-c".  See bug 364452 at
# http://bugzilla.gnome.org/show_bug.cgi?id=364452 for more
# information.
#
import sys
sys.argv[0] = "orca"

# Tell Orca to find/use the right version of pygtk.
#
import pygtk
pygtk.require('2.0')

try:
    # This can fail due to gtk not being available.  We want to
    # be able to recover from that if possible.  The main driver
    # for this is to allow "orca --text-setup" to work even if
    # the desktop is not running.
    #
    import gtk
except:
    pass

try:
    # If we don't have an active desktop, we will get a RuntimeError.
    import mouse_review
except RuntimeError:
    pass

import getopt
import os
import signal
import time
import unicodedata
import shutil

import settings
if settings.useDBus:
    import dbus.mainloop.glib
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    import dbusserver
    try:
        import gsmag as mag
    except:
        import mag
else:
    import mag

import pyatspi
import braille
import debug
import httpserver
import keynames
import keybindings
import orca_state
import orca_platform
import speech
import notification_messages

from input_event import BrailleEvent
from input_event import KeyboardEvent
from input_event import MouseButtonEvent
from input_event import keyEventToString

from orca_i18n import _           # for gettext support
from orca_i18n import ngettext

if settings.debugMemoryUsage:
    import gc
    gc.set_debug(gc.DEBUG_UNCOLLECTABLE
                 | gc.DEBUG_COLLECTABLE
                 | gc.DEBUG_INSTANCES
                 | gc.DEBUG_OBJECTS
                 | gc.DEBUG_SAVEALL)


EXIT_CODE_HANG = 50

# The user-settings module (see loadUserSettings).
#
_userSettings = None

# Command line options that override any other settings.
#
_commandLineSettings = {}

# True if --debug is used on the command line.
#
_debugSwitch = False

# Filename of the debug file to use if --debug or --debug-file is
# used on the command line.
#
_debugFile = None

# A subset of the original Xmodmap info prior to our stomping on it.
# Right now, this is just for the user's chosen Orca modifier(s).
#
_originalXmodmap = ""
_orcaModifiers = settings.DESKTOP_MODIFIER_KEYS + settings.LAPTOP_MODIFIER_KEYS
_capsLockCleared = False
_restoreOrcaKeys = False

########################################################################
#                                                                      #
# METHODS FOR HANDLING PRESENTATION MANAGERS                           #
#                                                                      #
# A presentation manager is what reacts to AT-SPI object events as     #
# well as user input events (keyboard and Braille) to present info     #
# to the user.                                                         #
#                                                                      #
########################################################################

# The known presentation managers (set up in start())
#
_PRESENTATION_MANAGERS = None

# The current presentation manager, which is an index into the
# _PRESENTATION_MANAGERS list.
#
_currentPresentationManager = -1

def _switchToPresentationManager(index):
    """Switches to the given presentation manager.

    Arguments:
    - index: an index into _PRESENTATION_MANAGERS
    """

    global _currentPresentationManager

    if _currentPresentationManager >= 0:
        _PRESENTATION_MANAGERS[_currentPresentationManager].deactivate()

    _currentPresentationManager = index

    # Wrap the presenter index around.
    #
    if _currentPresentationManager >= len(_PRESENTATION_MANAGERS):
        _currentPresentationManager = 0
    elif _currentPresentationManager < 0:
        _currentPresentationManager = len(_PRESENTATION_MANAGERS) - 1

    _PRESENTATION_MANAGERS[_currentPresentationManager].activate()

def _switchToNextPresentationManager(script=None, inputEvent=None):
    """Switches to the next presentation manager.

    Arguments:
    - inputEvent: the InputEvent instance that caused this to be called.

    Returns True indicating the event should be consumed.
    """

    _switchToPresentationManager(_currentPresentationManager + 1)
    return True

def getScriptForApp(app):
    """Get the script for the given application object from the current
    presentation manager.

    Arguments:
    - app: An application accessible.

    Returns a Script instance.
    """

    script = None
    if _currentPresentationManager >= 0:
        script = \
            _PRESENTATION_MANAGERS[_currentPresentationManager].getScript(app)
    return script

########################################################################
#                                                                      #
# METHODS TO HANDLE APPLICATION LIST AND FOCUSED OBJECTS               #
#                                                                      #
########################################################################

def setLocusOfFocus(event, obj, notifyPresentationManager=True, force=False):
    """Sets the locus of focus (i.e., the object with visual focus) and
    notifies the current presentation manager of the change.

    Arguments:
    - event: if not None, the Event that caused this to happen
    - obj: the Accessible with the new locus of focus.
    - notifyPresentationManager: if True, propagate this event
    - force: if True, don't worry if this is the same object as the
      current locusOfFocus
    """

    if not force and obj == orca_state.locusOfFocus:
        return

    # If this event is not for the currently active script, then just return.
    #
    if event and event.source and \
       event.host_application and orca_state.activeScript:
        currentApp = orca_state.activeScript.app
        if currentApp != event.host_application and \
           currentApp != event.source.getApplication():
            return

    oldLocusOfFocus = orca_state.locusOfFocus
    try:
        # Just to see if we have a valid object.
        oldLocusOfFocus.getRole()
    except:
        # Either it's None or it's an invalid remote object.
        oldLocusOfFocus = None

    orca_state.focusHistory = \
        orca_state.focusHistory[:settings.focusHistoryLength - 1]
    orca_state.focusHistory.insert(0, oldLocusOfFocus)

    orca_state.locusOfFocus = obj
    try:
        app = orca_state.locusOfFocus.getApplication()
    except:
        orca_state.locusOfFocus = None
        if event:
            debug.println(debug.LEVEL_FINE,
                          "LOCUS OF FOCUS: None event='%s'" % event.type)
        else:
            debug.println(debug.LEVEL_FINE,
                          "LOCUS OF FOCUS: None event=None")
    else:
        if not app:
            appname = "None"
        else:
            appname = "'" + app.name + "'"
        debug.println(debug.LEVEL_FINE,
                      "LOCUS OF FOCUS: app=%s name='%s' role='%s'" \
                      % (appname,
                         orca_state.locusOfFocus.name,
                         orca_state.locusOfFocus.getRoleName()))

        if event:
            debug.println(debug.LEVEL_FINE,
                          "                event='%s'" % event.type)
        else:
            debug.println(debug.LEVEL_FINE,
                          "                event=None")

    if notifyPresentationManager and _currentPresentationManager >= 0:
        _PRESENTATION_MANAGERS[_currentPresentationManager].\
            locusOfFocusChanged(event,
                                oldLocusOfFocus,
                                orca_state.locusOfFocus)

def visualAppearanceChanged(event, obj):
    """Called (typically by scripts) when the visual appearance of an object
    changes and notifies the current presentation manager of the change.  This
    method should not be called for objects whose visual appearance changes
    solely because of focus -- setLocusOfFocus is used for that.  Instead, it
    is intended mostly for objects whose notional 'value' has changed, such as
    a checkbox changing state, a progress bar advancing, a slider moving, text
    inserted, caret moved, etc.

    Arguments:
    - event: if not None, the Event that caused this to happen
    - obj: the Accessible whose visual appearance changed.
    """

    if _currentPresentationManager >= 0:
        _PRESENTATION_MANAGERS[_currentPresentationManager].\
            visualAppearanceChanged(event, obj)

def _onChildrenChanged(e):
    """Tracks children-changed events on the desktop to determine when
    apps start and stop.

    Arguments:
    - e: at-spi event from the at-api registry
    """

    desktop = pyatspi.Registry.getDesktop(0)
    if e.source == desktop:

        # If the desktop is empty, the user has logged out-- shutdown Orca
        #
        try:
            if desktop.childCount == 0:
                if not settings.onlySpeakDisplayedText:
                    speech.speak(_("Goodbye."))
                shutdown()
                return
        except: # could be a CORBA.COMM_FAILURE
            debug.printException(debug.LEVEL_FINEST)
            shutdown()
            return

def _onMouseButton(e):
    """Tracks mouse button events, stopping any speech in progress.

    Arguments:
    - e: at-spi event from the at-api registry
    """

    mouse_event = MouseButtonEvent(e)
    orca_state.lastInputEvent = mouse_event

    # A mouse button event looks like: mouse:button:1p, where the
    # number is the button number and the 'p' is either 'p' or 'r',
    # meaning pressed or released.  We only want to stop speech on
    # button presses.
    #
    if mouse_event.pressed:
        speech.stop()

########################################################################
#                                                                      #
# DEBUG support.                                                       #
#                                                                      #
########################################################################

def cycleDebugLevel(script=None, inputEvent=None):
    levels = [debug.LEVEL_ALL, "all",
              debug.LEVEL_FINEST, "finest",
              debug.LEVEL_FINER, "finer",
              debug.LEVEL_FINE, "fine",
              debug.LEVEL_CONFIGURATION, "configuration",
              debug.LEVEL_INFO, "info",
              debug.LEVEL_WARNING, "warning",
              debug.LEVEL_SEVERE, "severe",
              debug.LEVEL_OFF, "off"]

    try:
        levelIndex = levels.index(debug.debugLevel) + 2
    except:
        levelIndex = 0
    else:
        if levelIndex >= len(levels):
            levelIndex = 0

    debug.debugLevel = levels[levelIndex]

    briefMessage = levels[levelIndex + 1]
    fullMessage =  "Debug level %s." % briefMessage
    orca_state.activeScript.presentMessage(fullMessage, briefMessage)

    return True

def exitLearnMode(self, inputEvent=None):
    """Turns learn mode off.

    Returns True to indicate the input event has been consumed.
    """

    # Translators: Orca has a "Learn Mode" that will allow
    # the user to type any key on the keyboard and hear what
    # the effects of that key would be.  The effects might
    # be what Orca would do if it had a handler for the
    # particular key combination, or they might just be to
    # echo the name of the key if Orca doesn't have a handler.
    # Exiting learn mode puts the user back in normal operating
    # mode.
    #
    message = _("Exiting learn mode.")
    orca_state.activeScript.presentMessage(message)
    settings.learnModeEnabled = False
    return True

def exitListShortcutsMode(self, inputEvent=None):
    """Turns list shortcuts mode off.

    Returns True to indicate the input event has been consumed.
    """

    orca_state.listOfShortcuts = []
    orca_state.typeOfShortcuts = ""
    orca_state.ptrToShortcut = -1
    settings.listShortcutsModeEnabled = False

    # Translators: Orca has a "List Shortcuts Mode" that allows the user to
    # list a group of keyboard shortcuts. Pressing 1 makes it possible for
    # the user to navigate amongst a list of global ("default") commands.
    # Pressing 2 allows the user to navigate amongst Orca commands specific
    # to the application with focus. Escape exists this mode. This string
    # is the prompt which will be presented to the user in both speech and
    # braille upon exiting this mode.
    #
    message = _("Exiting list shortcuts mode.")
    orca_state.activeScript.presentMessage(message)
    return True

########################################################################
#                                                                      #
# METHODS FOR PRE-PROCESSING AND MASSAGING KEYBOARD EVENTS.            #
#                                                                      #
# All keyboard events are funnelled through here first.  Orca itself   #
# might have global keybindings (e.g., to switch between presenters),  #
# but it will typically pass the event onto the currently active       #
# active presentation manager.                                         #
#                                                                      #
########################################################################

# Keybindings that Orca itself cares about.
#
_keyBindings = None

# True if the orca modifier key is currently pressed.
#
_orcaModifierPressed = False

def isPrintableKey(event_string):
    """Return an indication of whether this is an alphanumeric or
       punctuation key.

    Arguments:
    - event: the event string

    Returns True if this is an alphanumeric or punctuation key.
    """

    if event_string == "space":
        reply = True
    else:
        unicodeString = event_string.decode("UTF-8")
        reply = (len(unicodeString) == 1) \
                and (unicodeString.isalnum() or unicodeString.isspace()
                or unicodedata.category(unicodeString)[0] in ('P', 'S'))
    debug.println(debug.LEVEL_FINEST,
                  "orca.isPrintableKey: returning: %s" % reply)
    return reply

def isModifierKey(event_string):
    """Return an indication of whether this is a modifier key.

    Arguments:
    - event: the event string

    Returns True if this is a modifier key
    """

    modifierKeys = [ 'Alt_L', 'Alt_R', 'Control_L', 'Control_R', \
                     'Shift_L', 'Shift_R', 'Meta_L', 'Meta_R' ]

    if not orca_state.bypassNextCommand:
        modifierKeys.extend(settings.orcaModifierKeys)

    reply = event_string in modifierKeys
    debug.println(debug.LEVEL_FINEST,
                  "orca.isModifierKey: returning: %s" % reply)
    return reply

def isLockingKey(event_string):
    """Return an indication of whether this is a locking key.

    Arguments:
    - event: the event string

    Returns True if this is a locking key.
    """

    lockingKeys = [ "Caps_Lock", "Num_Lock", "Scroll_Lock" ]

    reply = event_string in lockingKeys
    if not orca_state.bypassNextCommand:
        reply = reply and not event_string in settings.orcaModifierKeys
    debug.println(debug.LEVEL_FINEST,
                  "orca.isLockingKey: returning: %s" % reply)
    return reply

def isFunctionKey(event_string):
    """Return an indication of whether this is a function key.

    Arguments:
    - event: the event string

    Returns True if this is a function key.
    """

    # [[[TODO:richb - what should be done about the function keys on the left
    #    side of my Sun keyboard and the other keys (like Scroll Lock), which
    #    generate "Fn" key events?]]]

    functionKeys = [ "F1", "F2", "F3", "F4", "F5", "F6",
                     "F7", "F8", "F9", "F10", "F11", "F12" ]

    reply = event_string in functionKeys
    debug.println(debug.LEVEL_FINEST,
                  "orca.isFunctionKey: returning: %s" % reply)
    return reply

def isActionKey(event_string):
    """Return an indication of whether this is an action key.

    Arguments:
    - event: the event string

    Returns True if this is an action key.
    """

    actionKeys = [ "Return", "Escape", "Tab", "BackSpace", "Delete",
                   "Page_Up", "Page_Down", "Home", "End" ]

    reply = event_string in actionKeys
    debug.println(debug.LEVEL_FINEST,
                  "orca.isActionKey: returning: %s" % reply)
    return reply

def isNavigationKey(event_string):
    """Return an indication of whether this is a navigation (arrow) key
    or if the user has the Orca modifier key held done.

    Arguments:
    - event: the event string
    - modifiers: key modifiers state

    Returns True if this is a navigation key.
    """

    navigationKeys = [ "Left", "Right", "Up", "Down" ]

    reply = event_string in navigationKeys
    if not reply and not orca_state.bypassNextCommand:
        reply = _orcaModifierPressed

    debug.println(debug.LEVEL_FINEST,
                  "orca.isNavigationKey: returning: %s" % reply)
    return reply

def isDiacriticalKey(event_string):
    """Return an indication of whether this is a non-spacing diacritical key

    Arguments:
    - event: the event string
    - modifiers: key modifiers state

    Returns True if this is a non-spacing diacritical key
    """

    reply = event_string.startswith("dead_")

    debug.println(debug.LEVEL_FINEST,
                  "orca.isDiacriticalKey: returning: %s" % reply)
    return reply

class KeyEventType:
    """Definition of available key event types."""

    # An alphanumeric or punctuation key event.
    PRINTABLE = 'PRINTABLE'

    # A modifier key event.
    MODIFIER = 'MODIFIER'

    # A locking key event.
    LOCKING = 'LOCKING'

    # A locking key lock event.
    LOCKING_LOCKED = 'LOCKING_LOCKED'

    # A locking key unlock event.
    LOCKING_UNLOCKED = 'LOCKING_UNLOCKED'

    # A function key event.
    FUNCTION = 'FUNCTION'

    # An action key event.
    ACTION = 'ACTION'

    # A navigation key event.
    NAVIGATION = 'NAVIGATION'

    # A diacritical key event.
    DIACRITICAL = 'DIACRITICAL'

    def __init__(self):
        pass

def keyEcho(event):
    """If the keyEcho setting is enabled, check to see what type of key
    event it is and echo it via speech, if the user wants that type of
    key echoed.

    Uppercase keys will be spoken using the "uppercase" voice style,
    whereas lowercase keys will be spoken using the "default" voice style.

    Arguments:
    - event: an AT-SPI DeviceEvent
    """

    # If this keyboard event was for an object like a password text
    # field, then don't echo it.
    #
    if orca_state.locusOfFocus \
        and (orca_state.locusOfFocus.getRole() == pyatspi.ROLE_PASSWORD_TEXT):
        return False

    event_string = event.event_string
    debug.println(debug.LEVEL_FINEST,
                  "orca.keyEcho: string to echo: %s" % event_string)

    # If key echo is enabled, then check to see what type of key event
    # it is and echo it via speech, if the user wants that type of key
    # echoed.
    #
    if settings.enableKeyEcho:

        if isModifierKey(event_string):
            if not settings.enableModifierKeys:
                return False
            eventType = KeyEventType.MODIFIER

        elif isNavigationKey(event_string):
            if not settings.enableNavigationKeys:
                return False
            eventType = KeyEventType.NAVIGATION

        elif isDiacriticalKey(event_string):
            if not settings.enableDiacriticalKeys:
                return False
            eventType = KeyEventType.DIACRITICAL

        elif isPrintableKey(event_string):
            if not (settings.enablePrintableKeys \
                    or settings.enableEchoByCharacter):
                return False
            eventType = KeyEventType.PRINTABLE

        elif isLockingKey(event_string):
            if not settings.enableLockingKeys:
                return False
            eventType = KeyEventType.LOCKING

            modifiers = event.modifiers

            brailleMessage = None
            if event_string == "Caps_Lock":
                if modifiers & (1 << pyatspi.MODIFIER_SHIFTLOCK):
                    eventType = KeyEventType.LOCKING_UNLOCKED
                    brailleMessage = keynames.getKeyName(event_string) \
                                     + " " + _("off")
                else:
                    eventType = KeyEventType.LOCKING_LOCKED
                    brailleMessage = keynames.getKeyName(event_string) \
                                     + " " + _("on")

            elif event_string == "Num_Lock":
                # [[[TODO: richb - we are not getting a correct modifier
                # state value returned when Num Lock is turned off.
                # Commenting out the speaking of the bogus on/off state
                # until this can be fixed.]]]
                #
                #if modifiers & (1 << pyatspi.MODIFIER_NUMLOCK):
                #    eventType = KeyEventType.LOCKING_UNLOCKED
                #else:
                #    eventType = KeyEventType.LOCKING_LOCKED
                pass

            if brailleMessage:
                braille.displayMessage(brailleMessage,
                                       flashTime=settings.brailleFlashTime)

        elif isFunctionKey(event_string):
            if not settings.enableFunctionKeys:
                return False
            eventType = KeyEventType.FUNCTION

        elif isActionKey(event_string):
            if not settings.enableActionKeys:
                return False
            eventType = KeyEventType.ACTION

        else:
            debug.println(debug.LEVEL_FINEST,
                  "orca.keyEcho: event string not handled: %s" % event_string)
            return False

        # We keep track of the time as means to let others know that
        # we are probably echoing a key and should not be interrupted.
        #
        orca_state.lastKeyEchoTime = time.time()

        # Before we echo printable keys, let's try to make sure the
        # character echo isn't going to also echo something.
        #
        characterEcho = \
            eventType == KeyEventType.PRINTABLE \
            and not _orcaModifierPressed \
            and orca_state.activeScript \
            and orca_state.activeScript.utilities.willEchoCharacter(event)

        # One last check for echoing -- a PRINTABLE key may have squeaked
        # through due to the enableEchoByCharacter check above.  We only
        # want to echo PRINTABLE keys if enablePrintableKeys is True.
        #
        if not (characterEcho or
                (eventType == KeyEventType.PRINTABLE \
                 and not settings.enablePrintableKeys)):
            debug.println(debug.LEVEL_FINEST,
                          "orca.keyEcho: speaking: %s" % event_string)
            speech.speakKeyEvent(event_string, eventType)
            return True
        elif characterEcho:
            debug.println(debug.LEVEL_FINEST,
                          "orca.keyEcho: letting character echo handle: %s" \
                          % event_string)
            return False

def _setClickCount(inputEvent):
    """Sets the count of the number of clicks a user has made to one
    of the non-modifier keys on the keyboard.  Note that this looks at
    the event_string (keysym) instead of hw_code (keycode) because
    the Java platform gives us completely different keycodes for keys.

    Arguments:
    - inputEvent: the current input event.
    """

    lastInputEvent = orca_state.lastNonModifierKeyEvent

    if inputEvent.type == pyatspi.KEY_RELEASED_EVENT:
        pass
    elif not isinstance(inputEvent, KeyboardEvent):
        orca_state.clickCount = 0
    elif not isinstance(lastInputEvent, KeyboardEvent):
        orca_state.clickCount = 1
    elif (lastInputEvent.event_string != inputEvent.event_string) or \
         (lastInputEvent.modifiers != inputEvent.modifiers):
        orca_state.clickCount = 1
    elif (inputEvent.time - lastInputEvent.time) < \
           settings.doubleClickTimeout:
        # Cap the possible number of clicks at 3.
        #
        if orca_state.clickCount < 3:
            orca_state.clickCount += 1
    else:
        orca_state.clickCount = 1

def _processKeyCaptured(event):
    """Called when a new key event arrives and orca_state.capturingKeys=True.
    (used for key bindings redefinition)
    """

    if event.type == 0:
        if isModifierKey(event.event_string) \
           or isLockingKey(event.event_string):
            return True
        else:
            # We want the keyname rather than the printable character.
            # If it's not on the keypad, get the name of the unshifted
            # character. (i.e. "1" instead of "!")
            #
            keymap = gtk.gdk.keymap_get_default()
            entries = keymap.get_entries_for_keycode(event.hw_code)
            event.event_string = gtk.gdk.keyval_name(entries[0][0])
            if event.event_string.startswith("KP") and \
               event.event_string != "KP_Enter":
                name = gtk.gdk.keyval_name(entries[1][0])
                if name.startswith("KP"):
                    event.event_string = name

            orca_state.lastCapturedKey = event
    else:
        pass

    return False

def _processKeyboardEvent(event):
    """The primary key event handler for Orca.  Keeps track of various
    attributes, such as the lastInputEvent.  Also calls keyEcho as well
    as any local keybindings before passing the event on to the active
    presentation manager.  This method is called synchronously from the
    AT-SPI registry and should be performant.  In addition, it
    must return True if it has consumed the event (and False if not).

    Arguments:
    - event: an AT-SPI DeviceEvent

    Returns True if the event should be consumed.
    """
    global _orcaModifierPressed

    # Input methods appear to play games with repeating events
    # and also making up events with no timestamps.  We try
    # to handle that here. See bug #589504.
    #
    if (event.timestamp == 0) \
       or (event.timestamp == orca_state.lastInputEventTimestamp \
           and orca_state.lastInputEvent \
           and orca_state.lastInputEvent.hw_code == event.hw_code \
           and orca_state.lastInputEvent.type == event.type):
        debug.println(debug.LEVEL_FINE, keyEventToString(event))
        debug.println(debug.LEVEL_FINE, "IGNORING EVENT DUE TO TIMESTAMP")
        return

    orca_state.lastInputEventTimestamp = event.timestamp

    # Log the keyboard event for future playback, if desired.
    # Note here that the key event_string being output is
    # exactly what we received.  The KeyboardEvent object,
    # however, will translate the event_string for control
    # characters to their upper case ASCII equivalent.
    #
    string = keyEventToString(event)
    debug.printInputEvent(debug.LEVEL_FINE, string)

    keyboardEvent = KeyboardEvent(event)

    # Log the KeyboardEvent translated from the pyatspi keyboardEvent.
    #
    string = keyboardEvent.toString()
    debug.printInputEvent(debug.LEVEL_FINE, string)

    if keyboardEvent.type == pyatspi.KEY_PRESSED_EVENT:
        braille.killFlash()

    # See if this is one of our special Orca modifier keys.
    #
    # Just looking at the keycode should suffice, but there is a
    # "feature" in the Java Access Bridge where it chooses to emit
    # Java platform-independent keycodes instead of the keycodes
    # for the base platform:
    #
    # http://bugzilla.gnome.org/show_bug.cgi?id=106004
    # http://bugzilla.gnome.org/show_bug.cgi?id=318615
    #
    # So...we need to workaround this problem.
    #
    # If you make the following expression True we will get a positive
    # match for all keysyms associated with a given keysym specified
    # as an Orca modifier key.
    #
    # For example, assume the Orca modifier is set to \ for some
    # reason.  The key that has \ on it produces \ without the Shift
    # key and | with the Shift key.  If the following expression is
    # True, both the \ and | will be viewed as the Orca modifier.  If
    # the following expression is False, only the \ will be viewed as
    # the Orca modifier (i.e., Shift+\ will still function as the |
    # character).  In general, I think we want to avoid sucking in all
    # possible keysyms because it can have unexpected results.
    #
    if False:
        allPossibleKeysyms = []
        for keysym in settings.orcaModifierKeys:
            allPossibleKeysyms.extend(keybindings.getAllKeysyms(keysym))
    else:
        allPossibleKeysyms = settings.orcaModifierKeys

    isOrcaModifier = allPossibleKeysyms.count(keyboardEvent.event_string) > 0

    if event.type == pyatspi.KEY_PRESSED_EVENT:
        # Key presses always interrupt speech.
        #
        speech.stop()

        # We treat the Insert key as a modifier - so just swallow it and
        # set our internal state.
        #
        if isOrcaModifier:
            _orcaModifierPressed = True

        # If learn mode is enabled, it will echo the keys.
        #
        if not settings.learnModeEnabled and \
           orca_state.activeScript.echoKey(keyboardEvent):
            try:
                keyEcho(keyboardEvent)
            except:
                debug.printException(debug.LEVEL_SEVERE)

    elif isOrcaModifier \
        and (keyboardEvent.type == pyatspi.KEY_RELEASED_EVENT):
        _orcaModifierPressed = False

    if _orcaModifierPressed:
        keyboardEvent.modifiers = keyboardEvent.modifiers \
                                  | settings.ORCA_MODIFIER_MASK

    orca_state.lastInputEvent = keyboardEvent

    # If this is a key event for a non-modifier key, save a handle to it.
    # This is needed to help determine user actions when a multi-key chord
    # has been pressed, and we might get the key events in different orders.
    # See comment #15 of bug #435201 for more details.  We also want to
    # store the "click count" for the purpose of supporting keybindings
    # with unique behaviors when double- or triple-clicked.
    #
    if not isModifierKey(keyboardEvent.event_string):
        _setClickCount(keyboardEvent)
        orca_state.lastNonModifierKeyEvent = keyboardEvent

    # Orca gets first stab at the event.  Then, the presenter gets
    # a shot. [[[TODO: WDW - might want to let the presenter try first?
    # The main reason this is staying as is is that we may not want
    # scripts to override fundamental Orca key bindings.]]]
    #
    consumed = False
    try:
        if orca_state.capturingKeys:
            consumed = _processKeyCaptured(keyboardEvent)
        else:
            if settings.listShortcutsModeEnabled:
                consumed = listShortcuts(keyboardEvent)
            elif notification_messages.listNotificationMessagesModeEnabled:
                consumed = notification_messages.listNotificationMessages(keyboardEvent)
            if (not consumed):
                consumed = _keyBindings.consumeKeyboardEvent( \
                  None, keyboardEvent)
            if (not consumed) and (_currentPresentationManager >= 0):
                consumed = _PRESENTATION_MANAGERS[_currentPresentationManager].\
                           processKeyboardEvent(keyboardEvent)
            if (not consumed) and settings.learnModeEnabled:
                if keyboardEvent.type == pyatspi.KEY_PRESSED_EVENT:
                    clickCount = orca_state.activeScript.getClickCount()
                    if isPrintableKey(keyboardEvent.event_string) \
                       and clickCount == 2:
                        orca_state.activeScript.phoneticSpellCurrentItem(\
                            keyboardEvent.event_string)
                    else:
                        # Check to see if there are localized words to be
                        # spoken for this key event.
                        #
                        braille.displayMessage(keyboardEvent.event_string)
                        event_string = keyboardEvent.event_string
                        event_string = keynames.getKeyName(event_string)
                        speech.speak(event_string)
                elif (event.type == pyatspi.KEY_RELEASED_EVENT) and \
                     (keyboardEvent.event_string == "Escape"):
                    exitLearnMode(keyboardEvent)

                consumed = True

            global _restoreOrcaKeys
            if not consumed \
               and keyboardEvent.type == pyatspi.KEY_RELEASED_EVENT:
                if isOrcaModifier and orca_state.bypassNextCommand:
                    _restoreXmodmap()
                    _restoreOrcaKeys = True
                elif _restoreOrcaKeys and not orca_state.bypassNextCommand:
                    _createOrcaXmodmap()
                    _restoreOrcaKeys = False

            if not consumed \
               and not isModifierKey(keyboardEvent.event_string) \
               and keyboardEvent.type == pyatspi.KEY_PRESSED_EVENT:
                orca_state.bypassNextCommand = False
    except:
        debug.printException(debug.LEVEL_SEVERE)

    return consumed or isOrcaModifier

########################################################################
#                                                                      #
# METHODS FOR PRE-PROCESSING AND MASSAGING BRAILLE EVENTS.             #
#                                                                      #
########################################################################

def _processBrailleEvent(event):
    """Called whenever a  key is pressed on the Braille display.

    Arguments:
    - command: the BrlAPI event for the key that was pressed.

    Returns True if the event was consumed; otherwise False
    """

    consumed = False

    # Braille key presses always interrupt speech.
    #
    event = BrailleEvent(event)
    if event.event['command'] not in braille.dontInteruptSpeechKeys:
        speech.stop()
    orca_state.lastInputEvent = event

    try:
        consumed = _PRESENTATION_MANAGERS[_currentPresentationManager].\
                   processBrailleEvent(event)
    except:
        debug.printException(debug.LEVEL_SEVERE)

    if (not consumed) and settings.learnModeEnabled:
        consumed = True

    return consumed

########################################################################
#                                                                      #
# METHODS FOR HANDLING INITIALIZATION, SHUTDOWN, AND USE.              #
#                                                                      #
########################################################################

def toggleSilenceSpeech(script=None, inputEvent=None):
    """Toggle the silencing of speech.

    Returns True to indicate the input event has been consumed.
    """
    speech.stop()
    if settings.silenceSpeech:
        settings.silenceSpeech = False
        # Translators: this is a spoken prompt letting the user know
        # that speech synthesis has been turned back on.
        #
        orca_state.activeScript.presentMessage(_("Speech enabled."))
    else:
        # Translators: this is a spoken prompt letting the user know
        # that speech synthesis has been temporarily turned off.
        #
        orca_state.activeScript.presentMessage(_("Speech disabled."))
        settings.silenceSpeech = True
    return True

def _createOrcaXmodmap():
    """Makes an Orca-specific Xmodmap so that the keys behave as we
    need them to do. This is especially the case for the Orca modifier.
    """

    global _capsLockCleared

    cmd = []
    if "Caps_Lock" in settings.orcaModifierKeys:
        cmd.append("clear Lock")
        _capsLockCleared = True
    elif _capsLockCleared:
        cmd.append("add Lock = Caps_Lock")
        _capsLockCleared = False

    # Clear other keysyms so that we always treat the Orca modifier as
    # the Orca modifier (e.g. remove KP_0 from KP_Insert).
    #
    for keyName in settings.orcaModifierKeys:
        if keyName in ["Caps_Lock", "KP_Insert", "Insert"]:
            cmd.append("keysym %s = %s" % (keyName, keyName))

    os.system("echo '%s' | xmodmap - > /dev/null 2>&1" % "\n".join(cmd))

def _storeXmodmap(keyList):
    """Save the original xmodmap for the keys in keyList before we alter it.

    Arguments:
    - keyList: A list of named keys to look for.
    """

    global _originalXmodmap

    items = "|".join(keyList)
    cmd = "xmodmap -pke | grep -E '(%s)'" % items
    filehandle = os.popen(cmd)
    _originalXmodmap = filehandle.read()
    filehandle.close()

def _restoreXmodmap(keyList=[]):
    """Restore the original xmodmap values for the keys in keyList.

    Arguments:
    - keyList: A list of named keys to look for. An empty list means
      to restore the entire saved xmodmap.
    """

    toRestore = []
    lines = _originalXmodmap.split("\n")
    if not keyList:
        toRestore = lines

    for key in keyList:
        line = filter(lambda k: " %s" % key in k, lines)
        toRestore.extend(line)

    global _capsLockCleared
    if _capsLockCleared:
        toRestore.append("add Lock = Caps_Lock")
        _capsLockCleared = False

    os.system("echo '%s' | xmodmap - > /dev/null 2>&1" % "\n".join(toRestore))

def loadUserSettings(script=None, inputEvent=None):
    """Loads (and reloads) the user settings module, reinitializing
    things such as speech if necessary.

    Returns True to indicate the input event has been consumed.
    """

    global _userSettings

    # Shutdown the output drivers and give them a chance to die.

    # Only exit the D-Bus server if we're in an environment where there 
    # is a D-Bus session bus already running.  This helps prevent nastiness
    # on the login screen.
    #
    if settings.useDBus:
        dbusserver.shutdown()

    httpserver.shutdown()
    speech.shutdown()
    braille.shutdown()
    mag.shutdown()

    if _currentPresentationManager >= 0:
        _PRESENTATION_MANAGERS[_currentPresentationManager].deactivate()

    time.sleep(1)

    reloaded = False
    if _userSettings:
        try:
            reload(_userSettings)
            reloaded = True
        except ImportError:
            debug.printException(debug.LEVEL_FINEST)
        except:
            debug.printException(debug.LEVEL_SEVERE)
    else:
        try:
            _userSettings = __import__("user-settings")
            if _debugSwitch:
                debug.debugLevel = debug.LEVEL_ALL
                debug.eventDebugLevel = debug.LEVEL_OFF
                debug.debugFile = open(_debugFile, 'w', 0)
        except ImportError:
            debug.printException(debug.LEVEL_FINEST)
        except:
            debug.printException(debug.LEVEL_SEVERE)

    # If any settings were added to the command line, they take
    # precedence over everything else.
    #
    for key in _commandLineSettings:
        setattr(settings, key, _commandLineSettings[key])

    if settings.enableSpeech:
        try:
            speech.init()
            if reloaded:
                # Translators: there is a keystroke to reload the user
                # preferences.  This is a spoken prompt to let the user
                # know when the preferences has been reloaded.
                #
                msg = _("Orca user settings reloaded.")
                speech.speak(msg, settings.voices.get(settings.SYSTEM_VOICE))
            debug.println(debug.LEVEL_CONFIGURATION,
                          "Speech module has been initialized.")
        except:
            debug.printException(debug.LEVEL_SEVERE)
            debug.println(debug.LEVEL_SEVERE,
                          "Could not initialize connection to speech.")
    else:
        debug.println(debug.LEVEL_CONFIGURATION,
                      "Speech module has NOT been initialized.")

    if settings.enableBraille:
        try:
            braille.init(_processBrailleEvent, settings.tty)
        except:
            debug.printException(debug.LEVEL_WARNING)
            debug.println(debug.LEVEL_WARNING,
                          "Could not initialize connection to braille.")

    if settings.enableMagnifier:
        try:
            mag.init()
            debug.println(debug.LEVEL_CONFIGURATION,
                          "Magnification module has been initialized.")
        except:
            debug.printException(debug.LEVEL_SEVERE)
            debug.println(debug.LEVEL_SEVERE,
                          "Could not initialize connection to magnifier.")
    else:
        debug.println(debug.LEVEL_CONFIGURATION,
                      "Magnification module has NOT been initialized.")

    # I'm not sure where else this should go. But it doesn't really look
    # right here.
    try:
        mouse_review.mouse_reviewer.toggle(on=settings.enableMouseReview)
    except NameError:
        pass

    global _orcaModifiers
    custom = [k for k in settings.orcaModifierKeys if k not in _orcaModifiers]
    _orcaModifiers += custom
    # Handle the case where a change was made in the Orca Preferences dialog.
    #
    if _originalXmodmap:
        _restoreXmodmap(_orcaModifiers)

    _storeXmodmap(_orcaModifiers)
    _createOrcaXmodmap()

    if _currentPresentationManager >= 0:
        _PRESENTATION_MANAGERS[_currentPresentationManager].activate()

    showMainWindowGUI()

    # Only start the D-Bus server if we're in an environment where there 
    # is a D-Bus session bus already running.  This helps prevent nastiness
    # on the login screen.
    #
    if settings.useDBus:
        dbusserver.init()
    httpserver.init()

    return True

def showAppPreferencesGUI(script=None, inputEvent=None):
    """Displays the user interace to configure the settings for a
    specific applications within Orca and set up those app-specific
    user preferences using a GUI.

    Returns True to indicate the input event has been consumed.
    """

    try:
        module = __import__(settings.appGuiPreferencesModule,
                            globals(),
                            locals(),
                            [''])
        module.showPreferencesUI()
    except:
        debug.printException(debug.LEVEL_SEVERE)

    return True

def showPreferencesGUI(script=None, inputEvent=None):
    """Displays the user interace to configure Orca and set up
    user preferences using a GUI.

    Returns True to indicate the input event has been consumed.
    """

    try:
        module = __import__(settings.guiPreferencesModule,
                            globals(),
                            locals(),
                            [''])
        module.showPreferencesUI()
    except:
        debug.printException(debug.LEVEL_SEVERE)

    return True

def showMainWindowGUI(script=None, inputEvent=None):
    """Displays the Orca main window.

    Returns True to indicate the input event has been consumed.
    """

    try:
        module = __import__(settings.mainWindowModule,
                            globals(),
                            locals(),
                            [''])
        if settings.showMainWindow:
            module.showMainUI()
        else:
            module.hideMainUI()
    except:
        debug.printException(debug.LEVEL_SEVERE)

    return True

def _showPreferencesConsole(script=None, inputEvent=None):
    """Displays the user interace to configure Orca and set up
    user preferences via a command line interface.

    Returns True to indicate the input event has been consumed.
    """

    try:
        module = __import__(settings.consolePreferencesModule,
                            globals(),
                            locals(),
                            [''])
        module.showPreferencesUI(_commandLineSettings)
    except:
        debug.printException(debug.LEVEL_SEVERE)

    return True

def helpForOrca(script=None, inputEvent=None):
    """Show Orca Help window (part of the GNOME Access Guide).

    Returns True to indicate the input event has been consumed.
    """
    gtk.show_uri(gtk.gdk.screen_get_default(),
                 "ghelp:gnome-access-guide#ats-2",
                 gtk.get_current_event_time())
    return True

def listShortcuts(event):
    """When list shortcuts mode is enabled, this function provides a means
    by which users can navigate through Orca bound Orca commands. Pressing
    1 results in a list of the default shortcuts; pressing 2 results in a
    list of shortcuts for the focused application, should one exist. List
    navigation is accomplished through the Up and Down Arrow keys. Escape
    exits the list. In this mode, other keys are disabled.

    Arguments:
    - event: an AT-SPI DeviceEvent

    Returns True if the event is consumed (and False if not).
    """

    numShortcuts = len(orca_state.listOfShortcuts)
    consumed = False
    clickCount = 0
    message = ""

    # Translators: The following string instructs the user how to navigate
    # amongst the list of commands presented in 'list shortcuts' mode as
    # well as how to exit the list when finished.
    #
    navigation = \
        _("Use Up and Down Arrow to navigate the list. Press Escape to exit.")

    if event.type == pyatspi.KEY_PRESSED_EVENT:
        clickCount = orca_state.activeScript.getClickCount()
        if (event.event_string == "1"):
            if not numShortcuts or orca_state.typeOfShortcuts != "default":
                orca_state.listOfShortcuts = getListOfShortcuts("default")
                orca_state.typeOfShortcuts = "default"
                numShortcuts = len(orca_state.listOfShortcuts)
            orca_state.ptrToShortcut = 0
            # Translators: This message is presented when the user is in
            # 'list of shortcuts mode'. In this messsage, we present the
            # number of shortcuts found.
            #
            message = ngettext("%d Orca default shortcut found.",
                               "%d Orca default shortcuts found.",
                               numShortcuts) % numShortcuts
            message = message + " " + navigation
            orca_state.activeScript.presentMessage(message)
            message = orca_state.listOfShortcuts[orca_state.ptrToShortcut][0]+ \
              " " + orca_state.listOfShortcuts[orca_state.ptrToShortcut][1]
            orca_state.activeScript.speakMessage(message)
            orca_state.activeScript.displayBrailleMessage(message, -1, -1)
            consumed = True
        elif (event.event_string == "2"):
            if not numShortcuts or orca_state.typeOfShortcuts != "application":
                orca_state.listOfShortcuts = getListOfShortcuts("application")
                orca_state.typeOfShortcuts = "application"
                numShortcuts = len(orca_state.listOfShortcuts)
            if numShortcuts > 0: 
                orca_state.ptrToShortcut = 0
                # Translators: This message is presented when the user is in
                # 'list of shortcuts mode'. In this message, we present the
                # number of shortcuts found for the named application.
                #
                message = ngettext( \
                    "%(count)d Orca shortcut for %(application)s found.",
                    "%(count)d Orca shortcuts for %(application)s found.",
                    numShortcuts) % \
                    {"count" : numShortcuts,
                     "application" : orca_state.activeScript.app.name}
                message = message + " " + navigation
                orca_state.activeScript.presentMessage(message)
                message = \
                  orca_state.listOfShortcuts[orca_state.ptrToShortcut][0] + \
                  " " + orca_state.listOfShortcuts[orca_state.ptrToShortcut][1]
                orca_state.activeScript.speakMessage(message)
                orca_state.activeScript.displayBrailleMessage(message, -1, -1)
            else:
                # Translators: This message is presented when the user is in
                # 'list of shortcuts mode'. This is the message we present
                # when the user requested a list of application-specific
                # shortcuts, but none could be found for that application.
                #
                message = _("No Orca shortcuts for %s found.") % \
                    (orca_state.activeScript.app.name)
                orca_state.activeScript.speakMessage(message)
                orca_state.activeScript.displayBrailleMessage(message, -1, -1)
            consumed = True
        elif (event.event_string == "Up"):
            if (numShortcuts > 0):
                if orca_state.ptrToShortcut > 0: 
                    orca_state.ptrToShortcut = orca_state.ptrToShortcut-1
                else:
                    orca_state.ptrToShortcut = numShortcuts-1 
                    # Translators: when the user is attempting to locate a
                    # particular object and the top of a page or list is
                    # reached without that object being found, we "wrap" to
                    # the bottom and continue looking upwards. We need to
                    # inform the user when this is taking place.
                    #
                    orca_state.activeScript.\
                        presentMessage(_("Wrapping to bottom."))

                message = \
                  orca_state.listOfShortcuts[orca_state.ptrToShortcut][0] + \
                  " " + orca_state.listOfShortcuts[orca_state.ptrToShortcut][1]
                orca_state.activeScript.speakMessage(message)
                orca_state.activeScript.displayBrailleMessage(message, -1, -1)
            consumed = True
        elif (event.event_string == "Down"):
            if (numShortcuts > 0): 
                if orca_state.ptrToShortcut < numShortcuts-1: 
                    orca_state.ptrToShortcut = orca_state.ptrToShortcut+1
                else:
                    orca_state.ptrToShortcut = 0 
                    # Translators: when the user is attempting to locate a
                    # particular object and the bottom of a page or list is
                    # reached without that object being found, we "wrap" to the
                    # top and continue looking downwards. We need to inform the
                    # user when this is taking place.
                    #
                    orca_state.activeScript.\
                        presentMessage(_("Wrapping to top."))
                message = \
                  orca_state.listOfShortcuts[orca_state.ptrToShortcut][0] + \
                  " " + orca_state.listOfShortcuts[orca_state.ptrToShortcut][1]
                orca_state.activeScript.speakMessage(message)
                orca_state.activeScript.displayBrailleMessage(message, -1, -1)
            consumed = True
        elif (event.event_string == "Escape"):
            exitListShortcutsMode(event)
            consumed = True 
        else:
            # Translators: Orca has a 'List Shortcuts' mode by which a user can
            # navigate through a list of the bound commands in Orca. Pressing 1
            # presents the commands/shortcuts available for all applications.
            # These are the "default" commands/shortcuts. Pressing 2 presents
            # commands/shortcuts Orca provides for the application with focus.
            # The following message is presented to the user upon entering this
            # mode.
            #
            message = _("Press 1 for Orca's default shortcuts. Press 2 for " \
                        "Orca's shortcuts for the current application. " \
                        "Press escape to exit.")
            orca_state.activeScript.speakMessage(message)
            orca_state.activeScript.displayBrailleMessage(message, -1, -1)
            consumed = True
    elif (event.type == pyatspi.KEY_RELEASED_EVENT) and (event.event_string \
      == "Escape"):
        consumed = True
    return consumed


def getListOfShortcuts(typeOfShortcuts):
    """This function returns a list of Orca default shortcuts if the argument
    is 'default'. It returns a list of Orca shortcuts which are specific to
    the focused application, if the argument is "application". Orca default
    shortcuts are those found in the default script. Application-specific
    shortcuts are those which are present in the active script, but not in
    the default script. Only one shortcut per handler is listed. The list is
    sorted on shortcuts.

    Arguments:
    - typeOfShortcuts: a string specifying the desired type of shortcuts.

    Returns a list of shortcuts; depending on the value of argument.
    """

    import default

    numShortcuts = len(orca_state.listOfShortcuts)
    shortcuts = []
    shortcut = ""
    clickCount = ""
    brlKeyName = ""     
    brlHandler = None
    defScript = default.Script(None)
    defKeyBindings = defScript.getKeyBindings()
    defBrlBindings = defScript.getBrailleBindings()
    kbindings = keybindings.KeyBindings()
    if typeOfShortcuts == "default":
        for kb in defKeyBindings.keyBindings:
            if kb.keysymstring:
                if not kbindings.hasKeyBinding(kb,"description"):
                    kbindings.add(kb)
    elif typeOfShortcuts == "application":
        for kb in orca_state.activeScript.keyBindings.keyBindings:
            if kb.keysymstring:
                if not (defKeyBindings.hasKeyBinding(kb,"description") or \
                kbindings.hasKeyBinding(kb,"description")):
                    kbindings.add(kb)

    for kb in kbindings.keyBindings:
        keysymString = kb.keysymstring.replace("KP_", _("keypad "))
        clickCount = ""
        if kb.click_count == 2:
            # Translators: Orca keybindings support double
            # and triple "clicks" or key presses, similar to
            # using a mouse.
            #
            clickCount = _("double click")
        elif kb.click_count == 3:
            # Translators: Orca keybindings support double
            # and triple "clicks" or key presses, similar to
            # using a mouse.
            #
            clickCount = _("triple click")
        shortcut = (kb.handler.description, keybindings.getModifierNames\
        (kb.modifiers) + keysymString.upper() + " " + clickCount)
        shortcuts.append(shortcut)
        shortcuts = sorted(shortcuts, key=lambda shortcut: shortcut[1])

    if typeOfShortcuts == "orcaDefault":
        for bb in defBrlBindings.keys():
            brlKeyName = braille.command_name[bb]
            brlHandler = defBrlBindings[bb]
            shortcut = (brlHandler.description, brlKeyName)
            shortcuts.append(shortcut) 
    return shortcuts

def quitOrca(script=None, inputEvent=None):
    """Quit Orca. Check if the user wants to confirm this action.
    If so, show the confirmation GUI otherwise just shutdown.

    Returns True to indicate the input event has been consumed.
    """

    if settings.quitOrcaNoConfirmation:
        shutdown()
    else:
        try:
            module = __import__(settings.quitModule,
                                globals(),
                                locals(),
                                [''])
            module.showQuitUI()
        except:
            debug.printException(debug.LEVEL_SEVERE)

    return True

def showFindGUI(script=None, inputEvent=None):
    """Displays the user interace to perform an Orca Find.

    Returns True to indicate the input event has been consumed.
    """

    try:
        module = __import__(settings.findModule,
                            globals(),
                            locals(),
                            [''])
        module.showFindUI()
    except:
        debug.printException(debug.LEVEL_SEVERE)

def showSplashGUI(script=None, inputEvent=None):
    """Displays a splash screen.

    Returns True to indicate the input event has been consumed.
    """

    try:
        module = __import__(settings.splashModule,
                            globals(),
                            locals(),
                            [''])
        if _commandLineSettings.get("showSplashWindow", True):
            module.showSplashUI()
        else:
            module.hideSplashUI()

    except:
        debug.printException(debug.LEVEL_SEVERE)

    return True


# If True, this module has been initialized.
#
_initialized = False

def init(registry):
    """Initialize the orca module, which initializes speech, braille,
    and mag modules.  Also builds up the application list, registers
    for AT-SPI events, and creates scripts for all known applications.

    Returns True if the initialization procedure has run, or False if this
    module has already been initialized.
    """

    global _initialized
    global _keyBindings

    if _initialized:
        return False

    # Do not hang on initialization if we can help it.
    #
    if settings.timeoutCallback and (settings.timeoutTime > 0):
        signal.signal(signal.SIGALRM, settings.timeoutCallback)
        signal.alarm(settings.timeoutTime)

    # Note that we have moved the Orca specific keybindings to the default
    # script, so _keyBindings is currently empty. The logic is retained
    # here, just in case we wish to reinstate them in the future.
    #
    _keyBindings = keybindings.KeyBindings()

    # Create and load an app's script when it is added to the desktop
    #
    registry.registerEventListener(_onChildrenChanged,
                                   "object:children-changed")

    # We also want to stop speech when a mouse button is pressed.
    #
    registry.registerEventListener(_onMouseButton,
                                   "mouse:button")

    showSplashGUI()

    loadUserSettings()

    masks = []
    mask = 0
    # Cover all masks in 8 bits.
    while mask <= 255:
        masks.append(mask)
        mask += 1
    pyatspi.Registry.registerKeystrokeListener(
        _processKeyboardEvent,
        mask=masks,
        kind=(pyatspi.KEY_PRESSED_EVENT, pyatspi.KEY_RELEASED_EVENT))

    if settings.timeoutCallback and (settings.timeoutTime > 0):
        signal.alarm(0)

    _initialized = True
    return True

def start(registry):
    """Starts Orca.
    """

    global _PRESENTATION_MANAGERS

    if not _initialized:
        init(registry)

    # Do not hang on startup if we can help it.
    #
    if settings.timeoutCallback and (settings.timeoutTime > 0):
        signal.signal(signal.SIGALRM, settings.timeoutCallback)
        signal.alarm(settings.timeoutTime)

    if not _PRESENTATION_MANAGERS:
        import focus_tracking_presenter
        _PRESENTATION_MANAGERS = \
            [focus_tracking_presenter.FocusTrackingPresenter()]

    _switchToPresentationManager(0) # focus_tracking_presenter

    if settings.timeoutCallback and (settings.timeoutTime > 0):
        signal.alarm(0)

    if settings.cacheValues:
        pyatspi.setCacheLevel(pyatspi.CACHE_PROPERTIES)

    registry.start(gil=settings.useGILIdleHandler)

def die(exitCode=1):
    pid = os.getpid()
    if exitCode == EXIT_CODE_HANG:
        # Someting is hung and we wish to abort.
        os.kill(pid, signal.SIGKILL)
        return

    shutdown()
    sys.exit(exitCode)
    if exitCode > 1:
        os.kill(pid, signal.SIGTERM)

def timeout(signum=None, frame=None):
    debug.println(debug.LEVEL_SEVERE,
                  "TIMEOUT: something has hung.  Aborting.")
    debug.printStack(debug.LEVEL_ALL)
    die(EXIT_CODE_HANG)

def shutdown(script=None, inputEvent=None):
    """Exits Orca.  Unregisters any event listeners and cleans up.  Also
    quits the bonobo main loop and resets the initialized state to False.

    Returns True if the shutdown procedure ran or False if this module
    was never initialized.
    """

    global _initialized

    if not _initialized:
        return False

    # Try to say goodbye, but be defensive if something has hung.
    #
    if settings.timeoutCallback and (settings.timeoutTime > 0):
        signal.signal(signal.SIGALRM, settings.timeoutCallback)
        signal.alarm(settings.timeoutTime)

    # Translators: this is what Orca speaks and brailles when it quits.
    #
    orca_state.activeScript.presentMessage(_("Goodbye."))

    # Deregister our event listeners
    #
    pyatspi.Registry.deregisterEventListener(_onChildrenChanged,
                                             "object:children-changed")
    pyatspi.Registry.deregisterEventListener(_onMouseButton,
                                             "mouse:button")

    if _currentPresentationManager >= 0:
        _PRESENTATION_MANAGERS[_currentPresentationManager].deactivate()

    # Shutdown all the other support.
    #
    if settings.enableSpeech:
        speech.shutdown()
    if settings.enableBraille:
        braille.shutdown()
    if settings.enableMagnifier or settings.enableMagLiveUpdating:
        mag.shutdown()

    if settings.timeoutCallback and (settings.timeoutTime > 0):
        signal.alarm(0)

    _initialized = False
    _restoreXmodmap(_orcaModifiers)

    pyatspi.Registry.stop()

    return True

exitCount = 0
def shutdownOnSignal(signum, frame):
    global exitCount

    debug.println(debug.LEVEL_ALL,
                  "Shutting down and exiting due to signal = %d" \
                  % signum)

    debug.println(debug.LEVEL_ALL, "Current stack is:")
    debug.printStack(debug.LEVEL_ALL)

    # Well...we'll try to exit nicely, but if we keep getting called,
    # something bad is happening, so just quit.
    #
    if exitCount:
        die(signum)
    else:
        exitCount += 1

    # Try to do a graceful shutdown if we can.
    #
    if settings.timeoutCallback and (settings.timeoutTime > 0):
        signal.signal(signal.SIGALRM, settings.timeoutCallback)
        signal.alarm(settings.timeoutTime)

    try:
        if _initialized:
            shutdown()
        else:
            # We always want to try to shutdown speech since the
            # speech servers are very persistent about living.
            #
            speech.shutdown()
            shutdown()
        cleanExit = True
    except:
        cleanExit = False

    if settings.timeoutCallback and (settings.timeoutTime > 0):
        signal.alarm(0)

    if not cleanExit:
        die(EXIT_CODE_HANG)

def abortOnSignal(signum, frame):
    debug.println(debug.LEVEL_ALL,
                  "Aborting due to signal = %d" \
                  % signum)
    die(signum)

def usage():
    """Prints out usage information."""
    print(usageString())

def usageString():
    """Generates the usage information string."""
    info = []
    info.append(_("Usage: orca [OPTION...]"))

    # Translators: this is the description of the command line option
    # '-?, --help' that is used to display usage information.
    #
    info.append("-?, --help                   " + _("Show this help message"))
    info.append("-v, --version                %s" % orca_platform.version)

    # Translators: this is a testing option for the command line.  It prints
    # the names of the applications known to the accessibility infrastructure
    # to stdout and then exits.
    #
    info.append("-l, --list-apps              " + \
                _("Print the known running applications"))

    # Translators: this enables debug output for Orca.  The
    # YYYY-MM-DD-HH:MM:SS portion is a shorthand way of saying that
    # the file name will be formed from the current date and time with
    # 'debug' in front and '.out' at the end.  The 'debug' and '.out'
    # portions of this string should not be translated (i.e., it will
    # always start with 'debug' and end with '.out', regardless of the
    # locale.).
    #
    info.append("--debug                      " + \
                _("Send debug output to debug-YYYY-MM-DD-HH:MM:SS.out"))

    # Translators: this enables debug output for Orca and overrides
    # the name of the debug file Orca will use for debug output if the
    # --debug option is used.
    #
    info.append("--debug-file=filename        " + \
                _("Send debug output to the specified file"))

    # Translators: this is the description of the command line option
    # '-s, --setup, --gui-setup' that will initially display a GUI dialog
    # that would allow the user to set their Orca preferences.
    #
    info.append("-s, --setup, --gui-setup     " + _("Set up user preferences"))

    # Translators: this is the description of the command line option
    # '-t, --text-setup' that will initially display a list of questions
    # in text form, that the user will need to answer, before Orca will
    # startup. For this to happen properly, Orca will need to be run
    # from a terminal window.
    #
    info.append("-t, --text-setup             " + \
                _("Set up user preferences (text version)"))

    # Translators: this is the description of the command line option
    # '-n, --no-setup' that means that Orca will startup without setting
    # up any user preferences.
    #
    info.append("-n, --no-setup               " +  \
                _("Skip set up of user preferences"))

    # Translators: this is the description of the command line option
    # '-u, --user-prefs-dir=dirname' that allows you to specify an alternate
    # location for the user preferences.
    #
    info.append("-u, --user-prefs-dir=dirname " + \
                _("Use alternate directory for user preferences"))

    info.append("-e, --enable=[" \
        + "speech" + "|" \
        + "braille" + "|" \
        + "braille-monitor" + "|" \
        + "magnifier" + "|" \
        + "main-window" + "|" \
        + "splash-window" + "] ")

    # Translators: if the user supplies an option via the '-e, --enable'
    # command line option, it will be automatically enabled as Orca is
    # started.
    #
    info[-1] += _("Force use of option")

    info.append("-d, --disable=[" \
        + "speech" + "|" \
        + "braille" + "|" \
        + "braille-monitor" + "|" \
        + "magnifier" + "|" \
        + "main-window" + "|" \
        + "splash-window" + "] ")

    # Translators: if the user supplies an option via the '-d, --disable'
    # command line option, it will be automatically disabled as Orca is
    # started.
    #
    info[-1] += _("Prevent use of option")

    # Translators: this is the Orca command line option that will quit Orca.
    # The user would run the Orca shell script again from a terminal window.
    # If this command line option is specified, the script will quit any
    # instances of Orca that are already running.
    #
    info.append("-q, --quit                   " + \
                _("Quits Orca (if shell script used)"))

    # Translators: this is the Orca command line option that will force 
    # the termination of Orca.
    # The user would run the Orca shell script again from a terminal window.
    # If this command line option is specified, the script will quit any
    # instances of Orca that are already running.
    #
    info.append("-f, --forcequit              " + \
                _("Forces orca to be terminated immediately."))

    # Translators: this is the Orca command line option to tell Orca to
    # replace any existing Orca process(es) that might be running.
    #
    info.append("--replace                    " +\
                _("Replace a currently running Orca"))

    # Translators: this is text being sent to a terminal and we want to
    # keep the text lines within terminal boundaries.
    #
    info.append("\n" + \
                _("If Orca has not been previously set up by the user, Orca\n" \
                  "will automatically launch the preferences set up unless\n" \
                  "the -n or --no-setup option is used."))

    # Translators: this is more text being sent to a terminal and we want to
    # keep the text lines within terminal boundaries.
    #
    info.append("\n" + \
        _("WARNING: suspending Orca, e.g. by pressing Control-Z, from\n" \
          "an AT-SPI enabled shell (such as gnome-terminal), can also\n" \
          "suspend the desktop until Orca is killed."))

    info.append("\n" + _("Report bugs to orca-list@gnome.org."))

    return ("\n".join(info))

def printMessageAndExit(msg):
    # The use of os._exit() to immediately kill a child process
    # after a fork() is documented at docs.python.org.
    #
    # pylint: disable-msg=W0212
    #
    pid = os.fork()
    if pid:
        os.waitpid(pid, 0)
        os._exit(0)
    else:
        print msg
        os._exit(0)

def validateOptions(arglist, invalid=[]):
    """Parses the list of options in arglist and removes those
    which are not valid so that typos do not prevent the user
    from starting Orca.

    Arguments:
    - arglist: The list of options and arguments provided by
      the user.
    - invalid: Options which have already been identified as
      being invalid.

    Returns: A list containing validated options, valided
    arguments, and any items which were deemed invalid.
    """

    opts = []
    args = []

    # ? is for help
    # e is for enabling a feature
    # d is for disabling a feature
    # h is for help
    # u is for alternate user preferences location
    # s is for setup
    # n is for no setup
    # t is for text setup
    # v is for version
    #
    shortopts = "?stnvlmd:e:u:"
    longopts = ["help",
                "user-prefs-dir=",
                "enable=",
                "disable=",
                "setup",
                "gui-setup",
                "text-setup",
                "no-setup",
                "list-apps",
                "debug",
                "debug-file=",
                "version",
                "replace"]

    try:
        opts, args = getopt.getopt(arglist, shortopts, longopts)
    except getopt.GetoptError as ex:
        bogusOption = "-%s" % ex.opt
        if len(bogusOption) >= 2:
            bogusOption = "-%s" % bogusOption
        invalid.append(bogusOption)
        try:
            arglist.remove(bogusOption)
        except:
            pass
        else:
            return validateOptions(arglist, invalid)
    except:
        pass

    return opts, args, invalid

def multipleOrcas():
    """Returns True if multiple instances of Orca are running
    which are owned by the same user."""

    openFile = os.popen('pgrep -u %s orca' % os.getuid())
    pids = openFile.read()
    openFile.close()
    orcas = [int(p) for p in pids.split()]

    pid = os.getpid()
    ppid = os.getppid()
    return len(filter(lambda p: p not in [pid, ppid], orcas)) > 0

def main():
    """The main entry point for Orca.  The exit codes for Orca will
    loosely be based on signals, where the exit code will be the
    signal used to terminate Orca (if a signal was used).  Otherwise,
    an exit code of 0 means normal completion and an exit code of 50
    means Orca exited because of a hang."""

    global _debugSwitch
    global _debugFile

    # Method to call when we think something might be hung.
    #
    settings.timeoutCallback = timeout

    # Various signal handlers we want to listen for.
    #
    signal.signal(signal.SIGHUP, shutdownOnSignal)
    signal.signal(signal.SIGINT, shutdownOnSignal)
    signal.signal(signal.SIGTERM, shutdownOnSignal)
    signal.signal(signal.SIGQUIT, shutdownOnSignal)
    signal.signal(signal.SIGSEGV, abortOnSignal)

    # See if the desktop is running.  If it is, the import of gtk will
    # succeed.  If it isn't, the import will fail.
    #
    desktopRunning = False
    try:
        if gtk.gdk.display_get_default():
            desktopRunning = True
    except:
        pass

    # Parse the command line options.
    #
    # Run the preferences setup if the user has specified
    # "--setup" or "--text-setup" on the command line.  If the
    # desktop is not running, we will fallback to the console-based
    # method as appropriate.
    #
    bypassSetup     = False
    setupRequested  = False
    showGUI         = False

    # We hack a little here because the shell script to start orca can
    # conflate all of command line arguments into one string, which is
    # not what we want.  We detect this by seeing if the length of the
    # argument list is 1.
    #
    arglist = sys.argv[1:]
    if len(arglist) == 1:
        arglist = arglist[0].split()

    validOpts, validArgs, invalidOpts = validateOptions(arglist)
    validFeaturesListed = False
    if invalidOpts:
        # Translators: This message is displayed when the user tries
        # to start Orca and includes an invalid option as an argument.
        # After the message, the list of arguments, as typed by the
        # user, is displayed.
        #
        msg = _("The following arguments are not valid: ")
        print (msg + " ".join(invalidOpts))
        if multipleOrcas():
            die(0)

    try:
        for opt, val in validOpts:
            if opt in ("-u", "--user-prefs-dir"):
                userPrefsDir = val.strip()
                try:
                    os.chdir(userPrefsDir)
                    settings.userPrefsDir = userPrefsDir
                except:
                    debug.printException(debug.LEVEL_FINEST)

            if opt in ("-e", "--enable", "-d", "--disable"):
                feature = val.strip()
                enable = opt in ("-e", "--enable")
                if feature == "speech":
                    _commandLineSettings["enableSpeech"] = enable
                elif feature == "braille":
                    _commandLineSettings["enableBraille"] = enable
                elif feature == "braille-monitor":
                    _commandLineSettings["enableBrailleMonitor"] = enable
                elif feature == "magnifier":
                    _commandLineSettings["enableMagnifier"] = enable
                elif feature == "main-window":
                    _commandLineSettings["showMainWindow"] = enable
                elif feature == "splash-window":
                    _commandLineSettings["showSplashWindow"] = enable
                else:
                    valid = "\nspeech, braille, braille-monitor, magnifier, " \
                            "main-window, splash-window"
                    # Translators: This message is displayed when the user
                    # tries to enable or disable a feature via an argument,
                    # but specified an invalid feature. Valid features are:
                    # speech, braille, braille-monitor, magnifier, main-window,
                    # and splash-window. These items are not localized and are
                    # presented in a list after this message.
                    #
                    msg = _("The following items can be enabled or disabled:")
                    if not validFeaturesListed:
                        print (msg + valid)
                        validFeaturesListed = True

            if opt in ("-s", "--gui-setup", "--setup"):
                setupRequested = True
                showGUI = desktopRunning
            if opt in ("-t", "--text-setup"):
                setupRequested = True
                showGUI = False
            if opt in ("-n", "--no-setup"):
                bypassSetup = True
            if opt in ("-?", "--help"):
                printMessageAndExit(usageString())
            if opt in ("-v", "--version"):
                printMessageAndExit("Orca %s" % orca_platform.version)
            if opt == "--debug":
                _debugSwitch = True
                if not _debugFile:
                    _debugFile = time.strftime('debug-%Y-%m-%d-%H:%M:%S.out')
            if opt == "--debug-file":
                _debugSwitch = True
                _debugFile = val.strip()
            if opt in ("-l", "--list-apps"):
                apps = filter(lambda x: x is not None,
                              pyatspi.Registry.getDesktop(0))
                names = [app.name for app in apps]
                printMessageAndExit("\n".join(names))
    except:
        debug.printException(debug.LEVEL_OFF)
        usage()
        die(2)

    # Check if old config location exists, try to copy all 
    # the data from old location to the new location.
    #
    from xdg.BaseDirectory import xdg_data_home
    userPrefsDir = os.path.join(xdg_data_home, "orca")
    oldUserPrefsDir = os.path.join(os.environ["HOME"], ".orca")

    if not os.path.exists(userPrefsDir):
        os.mkdir(userPrefsDir)

    for baseDirName, dirNames, fileNames in os.walk(oldUserPrefsDir):

        for dirName in dirNames:
            relPath = os.path.relpath(baseDirName, oldUserPrefsDir)
            dstDir = os.path.join(os.path.join(userPrefsDir, relPath), dirName)
            if not os.path.exists(dstDir):
                os.mkdir(dstDir)

        for fileName in fileNames:
            srcFile = os.path.join(baseDirName, fileName)
            relPath = os.path.relpath(baseDirName, oldUserPrefsDir)
            dstFile = os.path.join(os.path.join(userPrefsDir, relPath), fileName)
            if not os.path.exists(dstFile):
                shutil.copy(srcFile, dstFile)

    settings.userPrefsDir = userPrefsDir

    # Do not run Orca if accessibility has not been enabled.
    # We do allow, however, one to force Orca to run via the
    # "-n" switch.  The main reason is so that things such
    # as accessible login can work -- in those cases, the gconf
    # setting is typically not set since the gdm user does not
    # have a home.
    #
    a11yEnabled = settings.isAccessibilityEnabled()
    if (not bypassSetup) and (not a11yEnabled):
        _showPreferencesConsole()
        die()

    if setupRequested and (not bypassSetup) and (not showGUI):
        _showPreferencesConsole()

    if not desktopRunning:
        print "Cannot start Orca because it cannot connect"
        print "to the Desktop.  Please make sure the DISPLAY"
        print "environment variable has been set."
        return 1

    userprefs = settings.userPrefsDir
    sys.path.insert(0, userprefs)
    sys.path.insert(0, '') # current directory

    init(pyatspi.Registry)

    try:
        message = _("Welcome to Orca.")
        if not settings.onlySpeakDisplayedText:
            speech.speak(message, settings.voices.get(settings.SYSTEM_VOICE))
        braille.displayMessage(message)
    except:
        debug.printException(debug.LEVEL_SEVERE)

    # Check to see if the user wants the configuration GUI. It's
    # done here so that the user's existing preferences can be used
    # to set the initial GUI state.  We'll also force the set to
    # be run if the preferences file doesn't exist, unless the
    # user has bypassed any setup via the --no-setup switch.
    #
    if setupRequested and (not bypassSetup) and showGUI:
        showPreferencesGUI()
    elif (not _userSettings) and (not bypassSetup):
        if desktopRunning:
            if not os.path.exists(userprefs):
                # Hack to work around b.g.o. 601657.
                #
                try:
                    os.mkdir(userprefs)
                except:
                    debug.printException(debug.LEVEL_FINEST)
            showPreferencesGUI()
        else:
            _showPreferencesConsole()

    try:
        start(pyatspi.Registry) # waits until we stop the registry
    except:
        die(EXIT_CODE_HANG)
    return 0

if __name__ == "__main__":
    sys.exit(main())
