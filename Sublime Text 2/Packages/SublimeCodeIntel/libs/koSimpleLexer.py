# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
# 
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
# 
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
# License for the specific language governing rights and limitations
# under the License.
# 
# The Original Code is Komodo code.
# 
# The Initial Developer of the Original Code is ActiveState Software Inc.
# Portions created by ActiveState Software Inc are Copyright (C) 2000-2007
# ActiveState Software Inc. All Rights Reserved.
# 
# Contributor(s):
#   ActiveState Software Inc
# 
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
# 
# ***** END LICENSE BLOCK *****

import os
import logging
import re

log = logging.getLogger("koSimpleLexer")
# XXX duplicated in codeintel.parseutil, present here to make this entirely
# independent

SKIPTOK = 0x01 # don't consider this a token that is to be considered a part of the grammar, like '\n'
MAPTOK = 0x02  # use the token associated with the pattern when it matches
EXECFN= 0x04   # execute the function associated with the pattern when it matches
USETXT = 0x08  # if you match a single character and want its ascii value to be the token

# Lexer class borrowed from the PyLRd project,
# http://starship.python.net/crew/scott/PyLR.html
class Lexer:
    eof = -1

    def __init__(self, filename=None):
        self.filename = filename
        self.tokenmap = {}
        self.prgmap = {}
        self.prglist = []
        self.lasttok = -1
        self.text = ""
        self.textindex = 0
        self.tokennum2name = {}

    def nexttok(self):
        self.lasttok = self.lasttok + 1
        return self.lasttok

    def settext(self, t):
        self.text = t
        self.textindex = 0

    def addmatch(self, prg, func=None, tokname="", attributes=MAPTOK|EXECFN):
        self.prglist.append(prg)
        tok = -2
        if not func:
            attributes = attributes & ~EXECFN
        if not tokname:
            attributes = attributes & ~MAPTOK
        if attributes & MAPTOK:
            self.tokenmap[tokname] = tok = self.nexttok()
        else:
            tok = self.nexttok()
        self.prgmap[prg] = tok, attributes, func
        self.tokennum2name[tok] = tokname

    def scan(self):
        x = ""
        for prg in self.prglist:
            #x = "TEXT TO MATCH {%s<|>%s}"% (self.text[self.textindex-10:self.textindex],self.text[self.textindex:self.textindex+20])
            #print x
            mo = prg.match(self.text, self.textindex)
            if not mo: 
                continue
            self.textindex = self.textindex + len(mo.group(0))
            tmpres = mo.group(0)
            t, attributes, fn = self.prgmap[prg]
            #log.info("'%s' token: %r", self.tokennum2name[t], tmpres)
            if attributes & EXECFN:
                try:
                    tmpres = apply(fn, (mo,))
                except Exception, e:
                    log.exception(e)
                    line = len(re.split('\r|\n|\r\n', self.text[:self.textindex]))
                    raise Exception("Syntax Error in lexer at file %s line %d positon %d text[%s]" % (self.filename, line, self.textindex, self.text[self.textindex:self.textindex+300]))
            if attributes & USETXT:
                t = ord(mo.group(0)[0])
            return (t, tmpres)
        if self.textindex >= len(self.text):
            return (self.eof, "")
        
        line = len(re.split('\r|\n|\r\n', self.text[:self.textindex]))
        raise Exception("Syntax Error in lexer at file %s line %d positon %d text[%s]" % (self.filename, line, self.textindex, self.text[self.textindex-20:self.textindex+300]))


# regular expressions used in parsing SGML related documents
class recollector:
    def __init__(self):
        self.res = {}
        self.regs = {}
        
    def add(self, name, reg, mods=None ):
        self.regs[name] = reg % self.regs
        #print "%s = %s" % (name, self.regs[name])
        if mods:
            self.res[name] = re.compile(self.regs[name], mods) # check that it is valid
        else:
            self.res[name] = re.compile(self.regs[name]) # check that it is valid
