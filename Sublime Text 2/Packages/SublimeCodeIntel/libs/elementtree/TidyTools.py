#
# ElementTree
# $Id: TidyTools.py 1862 2004-06-18 07:31:02Z Fredrik $
#
# tools to run the "tidy" command on an HTML or XHTML file, and return
# the contents as an XHTML element tree.
#
# history:
# 2002-10-19 fl   added to ElementTree library; added getzonebody function
#
# Copyright (c) 1999-2004 by Fredrik Lundh.  All rights reserved.
#
# fredrik@pythonware.com
# http://www.pythonware.com
#

##
# Tools to build element trees from HTML, using the external <b>tidy</b>
# utility.
##

import glob, string, os, sys

from ElementTree import ElementTree, Element

NS_XHTML = "{http://www.w3.org/1999/xhtml}"

##
# Convert an HTML or HTML-like file to XHTML, using the <b>tidy</b>
# command line utility.
#
# @param file Filename.
# @param new_inline_tags An optional list of valid but non-standard
#     inline tags.
# @return An element tree, or None if not successful.

def tidy(file, new_inline_tags=None):

    command = ["tidy", "-qn", "-asxml"]

    if new_inline_tags:
        command.append("--new-inline-tags")
        command.append(string.join(new_inline_tags, ","))

    # FIXME: support more tidy options!

    # convert
    os.system(
        "%s %s >%s.out 2>%s.err" % (string.join(command), file, file, file)
        )
    # check that the result is valid XML
    try:
        tree = ElementTree()
        tree.parse(file + ".out")
    except:
        print "*** %s:%s" % sys.exc_info()[:2]
        print ("*** %s is not valid XML "
               "(check %s.err for info)" % (file, file))
        tree = None
    else:
        if os.path.isfile(file + ".out"):
            os.remove(file + ".out")
        if os.path.isfile(file + ".err"):
            os.remove(file + ".err")

    return tree

##
# Get document body from a an HTML or HTML-like file.  This function
# uses the <b>tidy</b> function to convert HTML to XHTML, and cleans
# up the resulting XML tree.
#
# @param file Filename.
# @return A <b>body</b> element, or None if not successful.

def getbody(file, **options):
    # get clean body from text file

    # get xhtml tree
    try:
        tree = apply(tidy, (file,), options)
        if tree is None:
            return
    except IOError, v:
        print "***", v
        return None

    NS = NS_XHTML

    # remove namespace uris
    for node in tree.getiterator():
        if node.tag.startswith(NS):
            node.tag = node.tag[len(NS):]

    body = tree.getroot().find("body")

    return body

##
# Same as <b>getbody</b>, but turns plain text at the start of the
# document into an H1 tag.  This function can be used to parse zone
# documents.
#
# @param file Filename.
# @return A <b>body</b> element, or None if not successful.

def getzonebody(file, **options):

    body = getbody(file, **options)
    if body is None:
        return

    if body.text and string.strip(body.text):
        title = Element("h1")
        title.text = string.strip(body.text)
        title.tail = "\n\n"
        body.insert(0, title)

    body.text = None

    return body

if __name__ == "__main__":

    import sys
    for arg in sys.argv[1:]:
        for file in glob.glob(arg):
            print file, "...", tidy(file)
