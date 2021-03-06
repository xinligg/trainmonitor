# (c) 2006 Canonical
# Author: Michael Vogt <michael.vogt@ubuntu.com>
#
# Released under the GPL
#

import warnings
warnings.filterwarnings("ignore", "apt API not stable yet", FutureWarning)
import apt
import apt_pkg
import dbus
import gettext
import os
import re
import shutil
import subprocess
import string
import tempfile
import time
import thread
import sys

import FontConfig
from gettext import gettext as _
from LocaleInfo import LocaleInfo

from LangCache import *
from utils import *
import macros

# the language-selector abstraction
class LanguageSelectorBase(object):
    """ base class for language-selector code """

    def __init__(self, datadir=""):
        self._datadir = datadir
        # load the localeinfo "database"
        self._localeinfo = LocaleInfo("languagelist", self._datadir)
        self._cache = None

    def openCache(self, progress):
        self._cache = LanguageSelectorPkgCache(self._localeinfo, progress)

    def getMissingLangPacks(self):
        """
        return a list of language packs that are not installed
        but should be installed
        """
        missing = []
        for langInfo in  self._cache.getLanguageInformation():
            #print langInfo.languageCode
            trans_package = "language-pack-%s" % langInfo.languageCode
            # we have a langpack installed, see if we have all of them
            if (trans_package in self._cache and \
               (self._cache[trans_package].is_installed or \
               self._cache[trans_package].marked_install or \
               self._cache[trans_package].marked_upgrade) and \
               not self._cache[trans_package].marked_delete):
                #print "IsInstalled: %s " % trans_package
                #print self._cache.pkg_translations[langInfo.languageCode]
                if langInfo.languageCode in self._cache.pkg_translations:
                    for (pkg, translation) in self._cache.pkg_translations[langInfo.languageCode]:
                        if (pkg in self._cache and \
                           (self._cache[pkg].is_installed or \
                           self._cache[pkg].marked_install or \
                           self._cache[pkg].marked_upgrade) and \
                           not self._cache[pkg].marked_delete and \
                           translation in self._cache and \
                           ((not self._cache[translation].is_installed and \
                           not self._cache[translation].marked_install and \
                           not self._cache[translation].marked_upgrade) or \
                           self._cache[translation].marked_delete) and \
                           not translation in missing):
                            missing.append(translation)
            trans_package = "language-support-writing-%s" % langInfo.languageCode
            # we have a langsupport-writing installed, see if we have all of them
            if (trans_package in self._cache and 
               (self._cache[trans_package].is_installed or \
               self._cache[trans_package].marked_install or \
               self._cache[trans_package].marked_upgrade)):
                #print "IsInstalled: %s " % trans_package
                #print self._cache.pkg_writing[langInfo.languageCode]
                if langInfo.languageCode in self._cache.pkg_writing:
                    for (pkg, pull_pkg) in self._cache.pkg_writing[langInfo.languageCode]:
                        if '|' in pkg:
                            # multiple dependencies, if one of them is installed, pull the pull_pkg
                            for p in pkg.split('|'):
                                if self._cache[p] and \
                                   (self._cache[p].is_installed or \
                                   self._cache[p].marked_install or \
                                   self._cache[p].marked_upgrade) and \
                                   not self._cache[p].marked_delete and \
                                   pull_pkg in self._cache and \
                                   ((not self._cache[pull_pkg].is_installed and \
                                   not self._cache[pull_pkg].marked_install and \
                                   not self._cache[pull_pkg].marked_upgrade) or \
                                   self._cache[pull_pkg].marked_delete) and \
                                   not pull_pkg in missing:
                                    missing.append(pull_pkg)
                        else:
                            if pkg in self._cache and \
                               (self._cache[pkg].is_installed or \
                               self._cache[pkg].marked_install or \
                               self._cache[pkg].marked_upgrade) and \
                               not self._cache[pkg].marked_delete and \
                               pull_pkg in self._cache and \
                               ((not self._cache[pull_pkg].is_installed and \
                               not self._cache[pull_pkg].marked_install and \
                               not self._cache[pull_pkg].marked_upgrade) or \
                               self._cache[pull_pkg].marked_delete) and \
                               not pull_pkg in missing:
                                missing.append(pull_pkg)

        # now check for a missing default language support
        default_lang = self._localeinfo.getSystemDefaultLanguage()[0]
        macr = macros.LangpackMacros(self._datadir, default_lang)
        default_lang = macr["LOCALE"]
        pkgcode = macr["PKGCODE"]
#        # if there is no default lang, return early
#        if default_lang is None:
#            return missing
#        # Fallback is English
#        pkgcode = 'en'
#        if default_lang in self._cache.langpack_locales:
#            pkgcode = self._cache.langpack_locales[default_lang]
        trans_package = "language-pack-%s" % pkgcode
        if (trans_package in self._cache and 
            not self._cache[trans_package].is_installed):
            missing += [trans_package]
            if pkgcode in self._cache.pkg_translations:
                for (pkg, translation) in self._cache.pkg_translations[pkgcode]:
                    if (self._cache[pkg].is_installed and not self._cache[translation].is_installed):
                        missing.append(translation)
        support_packages = LanguageSelectorPkgCache._getPkgList(self._cache, pkgcode)
        for support_package in support_packages:
            if (support_package in self._cache and 
                not self._cache[support_package].is_installed):
                missing.append(support_package)

        if pkgcode in self._cache.pkg_writing:
            for (pkg, pull_pkg) in self._cache.pkg_writing[pkgcode]:
                if '|' in pkg:
                    # multiple dependencies, if one of them is installed, pull the pull_pkg
                    for p in pkg.split('|'):
                        if self._cache[p] and \
                           (self._cache[p].is_installed or \
                           self._cache[p].marked_install or \
                           self._cache[p].marked_upgrade) and \
                           not self._cache[p].marked_delete and \
                           pull_pkg in self._cache and \
                           ((not self._cache[pull_pkg].is_installed and \
                           not self._cache[pull_pkg].marked_install and \
                           not self._cache[pull_pkg].marked_upgrade) or \
                           self._cache[pull_pkg].marked_delete) and \
                           not pull_pkg in missing:
                            missing.append(pull_pkg)
                else:
                    if pkg in self._cache and \
                       (self._cache[pkg].is_installed or \
                       self._cache[pkg].marked_install or \
                       self._cache[pkg].marked_upgrade) and \
                       not self._cache[pkg].marked_delete and \
                       pull_pkg in self._cache and \
                       ((not self._cache[pull_pkg].is_installed and \
                       not self._cache[pull_pkg].marked_install and \
                       not self._cache[pull_pkg].marked_upgrade) or \
                       self._cache[pull_pkg].marked_delete) and \
                       not pull_pkg in missing:
                        missing.append(pull_pkg)

        return missing

    def writeSysLangSetting(self, sysLang):
        """ write the system "LANG" variable (e.g. de_DE.UTF-8) """
        bus = dbus.SystemBus()
        obj = bus.get_object('com.ubuntu.LanguageSelector','/')
        iface = dbus.Interface(obj,dbus_interface="com.ubuntu.LanguageSelector")
        iface.SetSystemDefaultLangEnv(sysLang)

    def writeSysLanguageSetting(self, sysLanguage):
        """ write the system "LANGUAGE" variable (e.g. de) """
        bus = dbus.SystemBus()
        obj = bus.get_object('com.ubuntu.LanguageSelector','/')
        iface = dbus.Interface(obj,dbus_interface="com.ubuntu.LanguageSelector")
        iface.SetSystemDefaultLanguageEnv(sysLanguage)

    def writeUserLangSetting(self, userLang):
        """ write the user "LANG" variable (e.g. de_DE.UTF-8) """
        conffiles = [ os.path.expanduser("~/.profile") ]
        macr = macros.LangpackMacros(self._datadir, userLang)
        findString = "export LANG="
        setString = "export LANG=\"%s\"\n" % macr["SYSLOCALE"]
        find_string_and_replace(findString, setString, conffiles)
        self._update_gdm_dmrc(userLang)

    def writeUserLanguageSetting(self, userLanguage):
        """ write the user "LANGUAGE" variable (e.g. de) """
        conffiles = [ os.path.expanduser("~/.profile") ]
        findString = "export LANGUAGE="
        setString = "export LANGUAGE=\"%s\"\n" % userLanguage
        find_string_and_replace(findString, setString, conffiles)

    def _update_gdm_dmrc(self, userLang):
        if userLang:
            gdmscript = "/etc/init.d/gdm"
            if os.path.exists("/var/run/gdm.pid") and os.path.exists(gdmscript):
                fname = os.path.expanduser("~/.dmrc")
                out = tempfile.NamedTemporaryFile()
                foundLang = False      # the Language var
                foundDesktop = False   # the [Desktop] entry
                filebuffer = []
                macr = macros.LangpackMacros(self._datadir, userLang)
                if os.path.exists(fname):
                    # look for the line
                    for line in open(fname):
                        tmp = string.strip(line)
                        if len(tmp) > 0:
                            filebuffer.append(tmp)
                        if tmp == '[Desktop]':
                            foundDesktop = True
                        if tmp.startswith("Language="):
                            foundLang = True
                # if we have not found them add them
                if foundDesktop == False:
                    line="\n[Desktop]\n"
                    out.write(line)
                if foundLang == False:
                    line="Language=%s\n" % macr["SYSLOCALE"]
                    out.write(line)
                for line in filebuffer:
                    if line.startswith("Language="):
                        line = "Language=%s\n" % macr["SYSLOCALE"]
                    else:
                        line = line+"\n"
                    out.write(line)
                out.flush()
                shutil.copy(out.name, fname)
                os.chmod(fname, 0644)
                if 'USER' in os.environ:
                    userid = os.environ["USER"]
                    path = '/var/cache/gdm/%s' % userid
                    if os.path.exists(path):
                        shutil.copy(fname, "%s/dmrc" % path)
                        os.chmod("%s/dmrc" % path, 0644)


if __name__ == "__main__":
    lsb = LanguageSelectorBase(datadir="..")
    lsb.openCache(apt.progress.OpProgress())
    print lsb.verifyPackageLists()


