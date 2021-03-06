# Liblouis Python ctypes bindings
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

"""Liblouis Python ctypes bindings
These bindings allow you to use the liblouis braille translator and back-translator library from within Python.
This documentation is only a Python helper.
Please see the liblouis documentation for more information.
@note: Back-translation is not currently supported.
@author: Michael Curran
@author: James Teh
@author: Eitan Isaacson

>>> import louis

Show a US grade2 translation of a unicode string with no typeform 
information:
>>> louis.translateString(['en-us-g2.ctb'], u'Hello world', None, 0)
u',hello _w'

Now do a translation using bold for the string:
>>> louis.translateString(['en-us-g2.ctb'], u'Hello world', 
[louis.bold]*11, 0)
u',hello __w'

Now do a translation using cursor position:
>>> louis.translate(['en-us-g2.ctb'], u'Hello world', None, 5, 0)
(u',hello _w', [0, 0, 1, 2, 3, 4, 5, 6, 6], [1, 2, 3, 4, 5, 6, 7, 7, 7, 
7, 7], 6)
"""

from ctypes import *
import struct
import atexit

try:
    # Native win32
    _loader = windll
except NameError:
    # Unix/Cygwin
    _loader = cdll
liblouis = _loader["liblouis.so.2"]

atexit.register(liblouis.lou_free)

liblouis.lou_version.restype = c_char_p

liblouis.lou_translateString.argtypes = (
    c_char_p, c_wchar_p, POINTER(c_int), c_wchar_p, 
         POINTER(c_int), POINTER(c_char), POINTER(c_char), c_int)

liblouis.lou_translate.argtypes = (
    c_char_p, c_wchar_p, POINTER(c_int), c_wchar_p, 
         POINTER(c_int), POINTER(c_char), POINTER(c_char), 
         POINTER(c_int), POINTER(c_int), POINTER(c_int), c_int)

liblouis.lou_backTranslateString.argtypes = (
         c_char_p, c_wchar_p, POINTER(c_int), c_wchar_p,
         POINTER(c_int), POINTER(c_char), POINTER(c_char), c_int)

liblouis.lou_backTranslate.argtypes = (
         c_char_p, c_wchar_p, POINTER(c_int), c_wchar_p, POINTER(c_int),
         POINTER(c_char), POINTER(c_char), POINTER(c_int), POINTER(c_int),
         POINTER(c_int), c_int)

liblouis.lou_hyphenate.argtypes = (
         c_char_p, c_wchar_p, c_int, POINTER(c_char), c_int)

def version():
    """Obtain version information for liblouis.
    @return: The version of liblouis, plus other information, such as
        the release date and perhaps notable changes.
    @rtype: str
    """
    return liblouis.lou_version()

def translate(tran_tables, inbuf, typeform=None,cursorPos=0, mode=0):
    """Translate a string of characters, providing position information.
    @param tran_tables: A list of translation tables.
        The first table in the list must be a full pathname, unless the tables are in the current directory.
    @type tran_tables: list of str
    @param inbuf: The string to translate.
    @type inbuf: unicode
    @param typeform: A list of typeform constants indicating the typeform for each position in inbuf,
        C{None} for no typeform information.
    @type typeform: list of int
    @param cursorPos: The position of the cursor in inbuf.
    @type cursorPos: int
    @param mode: The translation mode; add multiple values for a combined mode.
    @type mode: int
    @return: A tuple of: the translated string,
        a list of input positions for each position in the output,
        a list of output positions for each position in the input, and
        the position of the cursor in the output.
    @rtype: (unicode, list of int, list of int, int)
    @raise RuntimeError: If a complete translation could not be done.
    @see: lou_translate in the liblouis documentation
    """
    tablesString = ",".join([str(x) for x in tran_tables])
    inbuf = unicode(inbuf)
    inlen = c_int(len(inbuf))
    outlen = c_int(inlen.value*2)
    outbuf = create_unicode_buffer(outlen.value)
    typeformbuf = None
    if typeform:
        typeformbuf = create_string_buffer(struct.pack('B'*len(typeform),*typeform), size=outlen.value)
    inPos = (c_int*outlen.value)()
    outPos = (c_int*inlen.value)()
    cursorPos = c_int(cursorPos)
    if not liblouis.lou_translate(tablesString, inbuf, byref(inlen), 
                                  outbuf, byref(outlen),  typeformbuf, 
                                  None, outPos, inPos, byref(cursorPos), mode):
        raise RuntimeError("can't translate: tables %s, inbuf %s, typeform %s, cursorPos %s, mode %s"%(tran_tables, inbuf, typeform, cursorPos, mode))
    if isinstance(typeform, list):
        typeform[:] = typeformbuf.value
    return outbuf.value, inPos[:outlen.value], outPos[:inlen.value], cursorPos.value

def translateString(tran_tables, inbuf, typeform = None, mode = 0):
    """Translate a string of characters.
    @param tran_tables: A list of translation tables.
        The first table in the list must be a full pathname, unless the tables are in the current directory.
    @type tran_tables: list of str
    @param inbuf: The string to translate.
    @type inbuf: unicode
    @param typeform: A list of typeform constants indicating the typeform for each position in inbuf,
        C{None} for no typeform information.
    @type typeform: list of int
    @param mode: The translation mode; add multiple values for a combined mode.
    @type mode: int
    @return: The translated string.
    @rtype: unicode
    @raise RuntimeError: If a complete translation could not be done.
    @see: lou_translateString in the liblouis documentation
    """
    tablesString = ",".join([str(x) for x in tran_tables])
    inbuf = unicode(inbuf)
    inlen = c_int(len(inbuf))
    outlen = c_int(inlen.value*2)
    outbuf = create_unicode_buffer(outlen.value)
    typeformbuf = None
    if typeform:
        typeformbuf = create_string_buffer(struct.pack('B'*len(typeform),*typeform), size=outlen.value)
    if not liblouis.lou_translateString(tablesString, inbuf, byref(inlen), 
                                        outbuf, byref(outlen),  typeformbuf, 
                                        None, mode):
        raise RuntimeError("can't translate: tables %s, inbuf %s, typeform %s, mode %s"%(tran_tables, inbuf, typeform, mode))
    if isinstance(typeform, list):
        typeform[:] = typeformbuf.value
    return outbuf.value

def backTranslate(tran_tables, inbuf, typeform=None, cursorPos=0, mode=0):
    """Back translates a string of characters, providing position information.
    @param tran_tables: A list of translation tables.
    @type tran_tables: list of str
    @param inbuf: Braille to back translate.
    @type inbuf: unicode
    @param typeform: List where typeform constants will be placed.
    @type typeform: list
    @param cursorPos: Position of cursor.
    @type cursorPos: int
    @param mode: Translation mode.
    @type mode: int
    @return: A tuple: A string of the back translation,
        a list of input positions for each position in the output,
        a list of the output positions for each position in the input and
        the position of the cursor in the output.
    @rtype: (unicode, list of int, list of int, int)
    @raises RuntimeError: If back translation could not be completed.
    @see: lou_backTranslate in the liblouis documentation.
    """
    tablestring = ','.join([str(x) for x in tran_tables])
    inbuf = unicode(inbuf)
    inlen = c_int(len(inbuf))
    outlen = c_int(inlen.value * 2)
    outbuf = create_unicode_buffer(outlen.value)
    typeformbuf = None
    if isinstance(typeform, list):
        typeformbuf = create_string_buffer(outlen.value)
    inPos = (c_int*outlen.value)()
    outPos = (c_int*inlen.value)()
    cursorPos = c_int(cursorPos)
    if not liblouis.lou_backTranslate(tablestring, inbuf, byref(inlen),
                    outbuf, byref(outlen), typeformbuf, None,
                    outPos, inPos, byref(cursorPos), mode):
        raise RuntimeError("Can't back translate tran_tables %s, inbuf %s, typeform %s, cursorPos %d, mode %d" % (tran_tables, inbuf, typeform, cursorPos, mode))
    if isinstance(typeform, list):
        typeform[:] = typeformbuf.value
    return outbuf.value, inPos[:outlen.value], outPos[:inlen.value], cursorPos.value

def backTranslateString(tran_tables, inbuf, typeform=None, mode=0):
    """Back translate from Braille.
    @param tran_tables: A list of translation tables.
    @type tran_tables: list of str
    @param inbuf: The Braille to back translate.
    @type inbuf: unicode
    @param typeform: List for typeform constants to be put in.
        If you don't want typeform data then give None
    @type typeform: list
    @param mode: The translation mode
    @type mode: int
    @return: The back translation of inbuf.
    @rtype: unicode
    @raises RuntimeError: If a full back translation could not be done.
    @see: lou_backTranslateString in the liblouis documentation.
    """
    tablestring = ','.join([str(x) for x in tran_tables])
    inbuf = unicode(inbuf)
    inlen = c_int(len(inbuf))
    outlen = c_int(inlen.value * 2)
    outbuf = create_unicode_buffer(outlen.value)
    typeformbuf = None
    if isinstance(typeform, list):
        typeformbuf = create_string_buffer(outlen.value)
    if not liblouis.lou_backTranslateString(tablestring, inbuf, byref(inlen), outbuf,
                    byref(outlen), typeformbuf, None, mode):
        raise RuntimeError("Can't back translate tables %s, inbuf %s, mode %d" %(tablestring, inbuf, mode))
    if isinstance(typeform, list):
        typeform[:] = typeformbuf.value[:outlen.value]
    return outbuf.value

def hyphenate(tran_tables, inbuf, mode=0):
    """Get information for hyphenation.
    @param tran_tables: A list of translation tables and hyphenation
        dictionaries. The first filename should be a full path name otherwise
        the liblouis table directory is assumed.
    @type tran_tables: list of str
    @param inbuf: The text to get hyphenation information about.
        This should be a single word and leading/trailing whitespace
        and punctuation is ignored.
    @type inbuf: unicode
    @param mode: Lets liblouis know if inbuf is plain text or Braille.
        Set to 0 for text and anyother value for Braille.
    @type mode: int
    @return: A string with '1' at the beginning of every syllable
        and '0' elsewhere.
    @rtype: str
    @raises RuntimeError: If hyphenation data could not be produced.
    @see: lou_hyphenate in the liblouis documentation.
    """
    tablestring = ','.join([str(x) for x in tran_tables])
    inbuf = unicode(inbuf)
    inlen = c_int(len(inbuf))
    hyphen_string = create_string_buffer(inlen.value)
    if not liblouis.lou_hyphenate(tablestring, inbuf, inlen, hyphen_string, mode):
        raise RuntimeError("Can't hyphenate tables %s, inbuf %s, mode %d" %(tablestring, inbuf, mode))
    return hyphen_string.value

#{ Typeforms
plain_text = 0
italic = 1
underline = 2
bold = 4
computer_braille = 8

#{ Translation modes
noContractions = 1
compbrlAtCursor = 2
dotsIO = 4
comp8Dots = 8
pass1Only = 16
#}

if __name__ == '__main__':
    # Just some common tests.
    print version()
    print translate(['../tables/en-us-g2.ctb'], u'Hello world!', cursorPos=5)
