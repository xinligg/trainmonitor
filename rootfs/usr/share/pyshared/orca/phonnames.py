# Orca
#
# Copyright 2006-2008 Sun Microsystems Inc.
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

"""Provides getPhoneticName method that maps each letter of the
alphabet into its localized phonetic equivalent."""

__id__        = "$Id$"
__version__   = "$Revision$"
__date__      = "$Date$"
__copyright__ = "Copyright (c) 2006-2008 Sun Microsystems Inc."
__license__   = "LGPL"

from orca_i18n import _ # for gettext support

# Translators: this is a structure to assist in the generation of
# spoken military-style spelling.  For example, 'abc' becomes 'alpha
# bravo charlie'.
#
# It is a simple structure that consists of pairs of
#
# letter : word(s)
#
# where the letter and word(s) are separate by colons and each
# pair is separated by commas.  For example, we see:
#
# a : alpha, b : bravo, c : charlie,
#
# And so on.  The complete set should consist of all the letters from
# the alphabet for your language paired with the common
# military/phonetic word(s) used to describe that letter.
#
# The Wikipedia entry
# http://en.wikipedia.org/wiki/NATO_phonetic_alphabet has a few
# interesting tidbits about local conventions in the sections
# "Additions in German, Danish and Norwegian" and "Variants".
#
__phonlist = _("a : alpha, b : bravo, c : charlie, "
               "d : delta, e : echo, f : foxtrot, "
               "g : golf, h : hotel, i : india, "
               "j : juliet, k : kilo, l : lima, "
               "m : mike, n : november, o : oscar, "
               "p : papa, q : quebec, r : romeo, "
               "s : sierra, t : tango, u : uniform, "
               "v : victor, w : whiskey, x : xray, "
               "y : yankee, z : zulu")

__phonnames = {}

for __pair in __phonlist.split(','):
    __w = __pair.split(':')
    __phonnames [__w[0].strip()] = __w[1].strip()

def getPhoneticName(character):
    """Given a character, return its phonetic name, which is typically
    the 'military' term used for the character.

    Arguments:
    - character: the character to get the military name for

    Returns a string representing the military name for the character
    """

    if isinstance(character, unicode):
        character = character.encode("UTF-8")

    try:
        return __phonnames[character]
    except:
        return character
