#
# ElementTree
# $Id: SimpleXMLTreeBuilder.py 1862 2004-06-18 07:31:02Z Fredrik $
#
# A simple XML tree builder, based on Python's xmllib
#
# Note that due to bugs in xmllib, this builder does not fully support
# namespaces (unqualified attributes are put in the default namespace,
# instead of being left as is).  Run this module as a script to find
# out if this affects your Python version.
#
# history:
# 2001-10-20 fl   created
# 2002-05-01 fl   added namespace support for xmllib
# 2002-08-17 fl   added xmllib sanity test
#
# Copyright (c) 1999-2004 by Fredrik Lundh.  All rights reserved.
#
# fredrik@pythonware.com
# http://www.pythonware.com
#
# --------------------------------------------------------------------
# The ElementTree toolkit is
#
# Copyright (c) 1999-2004 by Fredrik Lundh
#
# By obtaining, using, and/or copying this software and/or its
# associated documentation, you agree that you have read, understood,
# and will comply with the following terms and conditions:
#
# Permission to use, copy, modify, and distribute this software and
# its associated documentation for any purpose and without fee is
# hereby granted, provided that the above copyright notice appears in
# all copies, and that both that copyright notice and this permission
# notice appear in supporting documentation, and that the name of
# Secret Labs AB or the author not be used in advertising or publicity
# pertaining to distribution of the software without specific, written
# prior permission.
#
# SECRET LABS AB AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH REGARD
# TO THIS SOFTWARE, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANT-
# ABILITY AND FITNESS.  IN NO EVENT SHALL SECRET LABS AB OR THE AUTHOR
# BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR ANY
# DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THIS SOFTWARE.
# --------------------------------------------------------------------

##
# Tools to build element trees from XML files, using <b>xmllib</b>.
# This module can be used instead of the standard tree builder, for
# Python versions where "expat" is not available (such as 1.5.2).
# <p>
# Note that due to bugs in <b>xmllib</b>, the namespace support is
# not reliable (you can run the module as a script to find out exactly
# how unreliable it is on your Python version).
##

import xmllib, string

import ElementTree

##
# ElementTree builder for XML source data.
#
# @see elementtree.ElementTree

class TreeBuilder(xmllib.XMLParser):

    def __init__(self, html=0):
        self.__builder = ElementTree.TreeBuilder()
        if html:
            import htmlentitydefs
            self.entitydefs.update(htmlentitydefs.entitydefs)
        xmllib.XMLParser.__init__(self)

    ##
    # Feeds data to the parser.
    #
    # @param data Encoded data.

    def feed(self, data):
        xmllib.XMLParser.feed(self, data)

    ##
    # Finishes feeding data to the parser.
    #
    # @return An element structure.
    # @defreturn Element

    def close(self):
        xmllib.XMLParser.close(self)
        return self.__builder.close()

    def handle_data(self, data):
        self.__builder.data(data)

    handle_cdata = handle_data

    def unknown_starttag(self, tag, attrs):
        attrib = {}
        for key, value in attrs.items():
            attrib[fixname(key)] = value
        self.__builder.start(fixname(tag), attrib)

    def unknown_endtag(self, tag):
        self.__builder.end(fixname(tag))


def fixname(name, split=string.split):
    # xmllib in 2.0 and later provides limited (and slightly broken)
    # support for XML namespaces.
    if " " not in name:
        return name
    return "{%s}%s" % tuple(split(name, " ", 1))


if __name__ == "__main__":
    import sys
    # sanity check: look for known namespace bugs in xmllib
    p = TreeBuilder()
    text = """\
    <root xmlns='default'>
       <tag attribute='value' />
    </root>
    """
    p.feed(text)
    tree = p.close()
    status = []
    # check for bugs in the xmllib implementation
    tag = tree.find("{default}tag")
    if tag is None:
        status.append("namespaces not supported")
    if tag is not None and tag.get("{default}attribute"):
        status.append("default namespace applied to unqualified attribute")
    # report bugs
    if status:
        print "xmllib doesn't work properly in this Python version:"
        for bug in status:
            print "-", bug
    else:
        print "congratulations; no problems found in xmllib"

