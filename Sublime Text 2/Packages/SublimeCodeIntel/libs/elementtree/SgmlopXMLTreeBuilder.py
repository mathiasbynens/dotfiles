#
# ElementTree
# $Id$
#
# A simple XML tree builder, based on the sgmlop library.
#
# Note that this version does not support namespaces.  This may be
# changed in future versions.
#
# history:
# 2004-03-28 fl   created
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
# Tools to build element trees from XML, based on the SGMLOP parser.
# <p>
# The current version does not support XML namespaces.
# <p>
# This tree builder requires the <b>sgmlop</b> extension module
# (available from
# <a href='http://effbot.org/downloads'>http://effbot.org/downloads</a>).
##

import ElementTree

##
# ElementTree builder for XML source data, based on the SGMLOP parser.
#
# @see elementtree.ElementTree

class TreeBuilder:

    def __init__(self, html=0):
        try:
            import sgmlop
        except ImportError:
            raise RuntimeError("sgmlop parser not available")
        self.__builder = ElementTree.TreeBuilder()
        if html:
            import htmlentitydefs
            self.entitydefs.update(htmlentitydefs.entitydefs)
        self.__parser = sgmlop.XMLParser()
        self.__parser.register(self)

    ##
    # Feeds data to the parser.
    #
    # @param data Encoded data.

    def feed(self, data):
        self.__parser.feed(data)

    ##
    # Finishes feeding data to the parser.
    #
    # @return An element structure.
    # @defreturn Element

    def close(self):
        self.__parser.close()
        self.__parser = None
        return self.__builder.close()

    def finish_starttag(self, tag, attrib):
        self.__builder.start(tag, attrib)

    def finish_endtag(self, tag):
        self.__builder.end(tag)

    def handle_data(self, data):
        self.__builder.data(data)
