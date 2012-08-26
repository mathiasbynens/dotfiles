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


#import htmlentitydefs
import re, string, sys
import mimetools, StringIO
from elementtree import ElementTree

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

collector = recollector()
a = collector.add

a("TextSE" , "[^<]+")
a("UntilHyphen" , "[^-]*-")
a("Until2Hyphens" , "%(UntilHyphen)s(?:[^-]%(UntilHyphen)s)*-")
a("CommentCE" , "%(Until2Hyphens)s>?") 
a("UntilRSBs" , "[^\\]]*](?:[^\\]]+])*]+")
a("CDATA_CE" , "%(UntilRSBs)s(?:[^\\]>]%(UntilRSBs)s)*>" )
a("S" , "[ \\n\\t\\r]+")
a("NameStrt" , "[A-Za-z_:]|[^\\x00-\\x7F]")
a("NameChar" , "[A-Za-z0-9_:.-]|[^\\x00-\\x7F]")
a("Name" , "(?:%(NameStrt)s)(?:%(NameChar)s)*")
a("QuoteSE" , "\"[^\"]*\"|'[^']*'")
a("DT_IdentSE" , "%(S)s%(Name)s(?:%(S)s(?:%(Name)s|%(QuoteSE)s))*" )

# http://bugs.activestate.com/show_bug.cgi?id=28765
#a("MarkupDeclCE" , "(?:[^\\]\"'><]+|%(QuoteSE)s)*>" )
a("MarkupDeclCE" , "(?:[^\\]\"'> \\n\\t\\r<]+|%(QuoteSE)s)*>" )

a("S1" , "[\\n\\r\\t ]")
a("UntilQMs" , "[^?]*\\?+")
a("PI_Tail" , "\\?>|%(S1)s%(UntilQMs)s(?:[^>?]%(UntilQMs)s)*>" )
a("DT_ItemSE" ,
    "<(?:!(?:--%(Until2Hyphens)s>|[^-]%(MarkupDeclCE)s)|\\?%(Name)s(?:%(PI_Tail)s))|%%%(Name)s;|%(S)s"
)
a("DocTypeCE" ,
"%(DT_IdentSE)s(?:%(S)s)?(?:\\[(?:%(DT_ItemSE)s)*](?:%(S)s)?)?>?" )
a("DeclCE" ,
    "--(?:%(CommentCE)s)?|\\[CDATA\\[(?:%(CDATA_CE)s)?|DOCTYPE(?:%(DocTypeCE)s)?")
a("PI_CE" , "%(Name)s(?:%(PI_Tail)s)?")
a("EndTagCE" , "(?P<endtag>%(Name)s)(?:%(S)s)?>?")
a("AttValSE" , "\"[^<\"]*\"|'[^<']*'")
a("ElemTagCE" ,
    "(?P<tag>%(Name)s)(?P<attrs>(?:%(S)s%(Name)s(?:%(S)s)?=(?:%(S)s)?(?:%(AttValSE)s))*)(?:%(S)s)?/?>?")

a("MarkupSPE" ,
    "<(?:!(?:%(DeclCE)s)?|\\?(?:%(PI_CE)s)?|/(?:%(EndTagCE)s)?|(?:%(ElemTagCE)s)?)")
a("XML_SPE" , "%(TextSE)s|%(MarkupSPE)s")
a("XML_MARKUP_ONLY_SPE" , "%(MarkupSPE)s")

a("DOCTYPE",        r'<!DOCTYPE\s+(?P<type>\S+)\s+(?P<ident>PUBLIC|SYSTEM)\s+(?P<data1>%(QuoteSE)s)\s*(?P<data2>%(QuoteSE)s)?\s*(?:\[|>)', re.S)

a("attrfinderRE" , "(?:[\n \t]*)(%(Name)s)(?:%(S)s)?=(?:%(S)s)?(%(AttValSE)s)", re.S|re.U)
attrfinder = collector.res["attrfinderRE"]

is_not_ascii = re.compile(eval(r'u"[\u0080-\uffff]"')).search

def parseiter(data, markuponly=0):
    if markuponly:
        reg = "XML_MARKUP_ONLY_SPE"
    else:
        reg = "XML_SPE"
    regex = collector.res[reg]
    return regex.finditer(data)

def strip_quotes(str):
    if not str:
        return None
    if str[0] in ["'",'"']:
        return str[1:-1]
    return str


# XXX this should realy be done via DTD/Schema, but that would be a major
# pain.  For general purposes, this will work fine and be faster

# these tags are defined to NOT ALLOW end tags at all in html.  They never
# have children and never have end tags
# defined in dtd as ELEMENT NAME - O EMPTY
html_no_close_tags = set([
    "basefont", "br", "area", "link", "img", "param", "hr", "input",
    "col", "frame", "isindex", "base", "meta"
])
# defined in dtd as ELEMENT NAME - O *
html_optional_close_tags = set([
    "p", "dt", "dd", "li", "option", "thead", "tfoot", "colgroup",
    "col", "tr", "th", "td"
])

html_block_tags = set([
    "p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "pre", "dl", "div", "noscript", 
    "blockquote", "form", "hr", "table", "fieldset", "address"
])

# these are optional end tag and cannot contain other block tags defined above
html_cannot_contain_block_tags = set([
    "p", "dt"
])

html_close_tag_unnecessary = html_no_close_tags.union(html_optional_close_tags)

class HTMLTreeBuilder(ElementTree.TreeBuilder):

    def __init__(self, encoding="iso-8859-1"):
        ElementTree.TreeBuilder.__init__(self)
        self.encoding = encoding
        self.nodes = []
        self.nodemap = {} # {child_elem: parent_elem, ... }
        self._rootnodes = []
        self.current = None

    def start(self, tag, attrs, loc_start, loc_end):
        if not tag:
            return
        #print loc
        if tag == "meta":
            # look for encoding directives
            http_equiv = content = None
            for k, v in attrs:
                if k == "http-equiv":
                    http_equiv = string.lower(v)
                elif k == "content":
                    content = v
            if http_equiv == "content-type" and content:
                # use mimetools to parse the http header
                header = mimetools.Message(
                    StringIO.StringIO("%s: %s\n\n" % (http_equiv, content))
                    )
                encoding = header.getparam("charset")
                if encoding:
                    self.encoding = encoding
        l_tag = tag.lower()
        if self._elem:
            p_tag = self._elem[-1].tag.lower()
            # if the parent and child are the same tag, then close the
            # parent if it uses optional close tags
            if l_tag in html_optional_close_tags and p_tag == l_tag:
                self.end(tag)
            # special case table tags that should be autoclosed only when
            # hitting a new table row
            elif p_tag in ("td","th") and l_tag == "tr":
                self.end_tag(p_tag)
            # if the parent and child are block tags, close the parent
            elif p_tag in html_cannot_contain_block_tags and l_tag in html_block_tags:
                self.end_tag(p_tag)
        attrib = {}
        for attr in attrs:
            attrib[attr[0]] = strip_quotes(attr[1])
        ElementTree.TreeBuilder.start(self, tag, attrib)
        el = self._elem[-1]
        self.current = el
        el.ns = None
        el.localName = el.tag
        el.start = loc_start
        el.end = None
        self.nodes.append(el)
        if len(self._elem) > 1:
            self.nodemap[el] = self._elem[-2]
        else:
            self.nodemap[el] = None
        if l_tag in html_no_close_tags:
            self.end_tag(tag, loc_end)

    def end(self, tag, loc=None):
        if not self._elem:
            return None
        l_tag = tag
        l_lasttag = lasttag = self._elem[-1].tag
        if l_tag:
            l_tag = l_tag.lower()
        if l_lasttag:
            l_lasttag = lasttag.lower()
        while (l_tag != l_lasttag
               and l_lasttag in html_optional_close_tags
               and len(self._elem) > 1
               and self._last.start[2] < self._elem[-1].start[2]):
            self.end_tag(lasttag)
            if self._elem:
                lasttag = self._elem[-1].tag
                l_lasttag = lasttag.lower()
            else:
                self.current = self._last
                return self._last

        # protect against a previous close of this tag
        if l_tag in html_close_tag_unnecessary and l_tag != self._elem[-1].tag.lower():
            return None
        return self.end_tag(tag, loc)

    def end_tag(self, tag, loc=None):
        if not tag: return None
        self._flush()
        # find this tag:
        tags = [e.localName for e in self._elem]
        if tag not in tags:
            # invalid end tag?
            return None
        last = self._elem.pop()
        while last.tag != tag:
            last = self._elem.pop()
        self._last = last
        if not self._elem:
            self._rootnodes.append(self._last)
        if loc:
            self._last.end = loc

        self._tail = 1
        self.current = self._last
        return self._last

    def data(self, data):
        if isinstance(data, type('')) and is_not_ascii(data):
            # convert to unicode, but only if necessary
            data = unicode(data, self.encoding, "ignore")
        ElementTree.TreeBuilder.data(self, data)

    def close(self):
        if self._elem:
            return self._elem[0]
        return self._last
        
class Parser:
    def __init__(self, builder=None):
        if not builder:
            builder = ElementTree.TreeBuilder()
        self._builder = builder
        self.doctype = None
        self.publicId = None
        self.systemId = None
        self.locator = {}
        self._lastloc = None
        self.data = None

    def parse_doctype(self, data):
        m = collector.res["DOCTYPE"].match(data)
        if m is None:
            return
        result = m.groupdict()
        self.doctype = result
        self.publicId = None
        if result['ident'] == "PUBLIC":
            self.publicId = strip_quotes(result['data1'])
            self.systemId = strip_quotes(result['data2'])
        else:
            self.systemId = strip_quotes(result['data1'])

    def getLocation(self, loc):
        pos = 0
        last_lines = 0
        if self._lastloc:
            pos = self._lastloc
            last_lines = self.locator[pos][0]
        lines = last_lines + self.data.count("\n",pos,loc)
        col =  0
        if lines > last_lines:
            col = loc - self.data.rfind("\n",pos,loc) - 1
        elif pos in self.locator:
            col = loc - pos + self.locator[pos][1]
        self.locator[loc] = [lines, col]
        self._lastloc = loc
        return (lines + 1, col, loc)
        
    def feed(self, data, markuponly=0):
        no_close_tag = []
        opt_close_tag = []
        self.data = data
        for matchObj in parseiter(data, markuponly):
            x = matchObj.group(0)
            m = matchObj.groupdict()
            if x.startswith("<!"):
                continue
            # XXX
                if x.startswith("<!DOCTYPE"):
                    self.parse_doctype(x)
            elif x.startswith("<?"):
                # processing tag
                continue
            elif x.startswith("</"):
                self._builder.end(m["endtag"], self.getLocation(matchObj.end(0)))
            elif x.startswith("<"):
                # get the tag and attrs
                attrs = []
                if "attrs" in m and m["attrs"] is not None:
                    attrs = attrfinder.findall(m["attrs"])
                start = self.getLocation(matchObj.start(0))
                end = self.getLocation(matchObj.end(0))
                self._builder.start(m["tag"], attrs, start, end)
                if x.endswith("/>"):
                    self._builder.end(m["tag"], end)
            else:
                self._builder.data(x)

    def close(self):
        return self._builder.close()

try:
    import sgmlop
    ReParser = Parser
    class SgmlopParser(ReParser):
        def __init__(self, builder=None):
            ReParser.__init__(self, builder)
            self.__parser = sgmlop.XMLParser()
            self.__parser.register(self)

        def finish_starttag(self, tag, attrib, loc_start, loc_end):
            # builder expects a list of tuples
            attrs = list(attrib.items())
            self._builder.start(tag, attrs, self.getLocation(loc_start), self.getLocation(loc_end))
    
        def finish_endtag(self, tag, loc):
            self._builder.end(tag, self.getLocation(loc))
    
        def handle_data(self, data):
            self._builder.data(data)
            
        def handle_special(self, data, token_type):
            # here's where we figure out if we've got a doctype
            if token_type == 0x105: # from sgmlop.c
                # we get everything inside <!...>
                self.parse_doctype("<!%s>" % data)

        def feed(self, data, markuponly=0):
            self.data = data
            return self.__parser.feed(data)

        def close(self):
            if self.__parser:
                self.__parser.close()
                self.__parser = None
            return ReParser.close(self)

    Parser = SgmlopParser
except:
    pass

def HTML(data, ParserClass=Parser):
    p = ParserClass(HTMLTreeBuilder())
    p.feed(data)
    return p.close()

if __name__=="__main__":
    import sys
    
    if len(sys.argv) > 1:
        import time
        # read the file and parse it to get a time.
        f = open(sys.argv[1])
        data = f.read()
        f.close()
        t1 = time.time()
        tree = HTML(data, ReParser)
        t2 = time.time()
        print "RE parsing took %s" % (t2-t1)
        t1 = time.time()
        tree = HTML(data, SgmlopParser)
        t2 = time.time()
        print "sgmlop parsing took %s" % (t2-t1)
        sys.exit(0)
    
    data = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html>
<head> <title>my title</title> </head>
<body>
    <p>blah blah...
    <img src="somefile.jpg" alt="blah">
    </img>
    </p>
</body>
</html>"""
    tree = HTML(data)
    print ElementTree.tostring(tree)
    sys.exit(0)
    

    data = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en">

<head>
"""
    tree = HTML(data)
    print ElementTree.tostring(tree)
    sys.exit(0)

    data = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">

    <HTML lang="en">
    <BODY>
    <p>
        <img>
        <p>
            <br>
        </p>
        <hr>
        <p>"""
    #        <br>
    #    <dl>
    #        <li>
    #        <li>
    #        <li>
    #    </dl>
    #    <p>
    #    <hr>
    #</p>
    #</BODY>
    #</HTML>
    #"""
    data = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
            "http://www.w3.org/TR/html4/strict.dtd">
<!-- Copyright (c) 2000-2006 ActiveState Software Inc. -->
<!-- See the file LICENSE.txt for licensing information. -->


<html>
<head>
<link rel="stylesheet" type="text/css" href="aspn.css">
<script language="JavaScript" src="displayToc.js"></script>
<script language="JavaScript" src="tocParas.js"></script>
<script language="JavaScript" src="tocTab.js"></script>
<link rel="icon" href="favicon.ico" type="image/x-icon"/>
<link rel="shortcut icon" href="favicon.ico" type="image/x-icon"/>
<title>XML Catalogs</title>
</head>

<body>

<table>
<tr>
<td>



<h1><a name="xml_catalogs_top">XML Catalogs</a></h1>

<p>Komodo can add <a href=komodo-doc-editor.html#XML_AutoComplete">XML
autocompletion</a> support for any XML dialect with a DTD or RelaxNG Schema.
This is done by mapping external identifier entries to local copies of the DTD
or RelaxNG Schema for that document type using <a target="_blank"
href="http://www.oasis-open.org/committees/entity/spec.html">XML
Catalogs</a>.</p>

<p><script>writelinks('xml_catalogs_top');</script>&nbsp;</p>

<h2><a name="using_xml_catalogs">Using an Existing XML Catalog</a></h2>

<p>Some toolkits bundle DTDs or RelaxNG Schemas with their own XML
catalogs. As long as the relative path from the catalog to the .dtd or
.rng file is preserved on the local filesystem, you can add support for
the dialect by specifying the catalog file in Preferences under <a
href="komodo-doc-prefs.html#xml_catalogs">SGML/XML Catalogs</a>.</p>

<p><script>writelinks('using_xml_catalogs');</script>&nbsp;</p>

<h2><a name="creating_xml_catalogs">Creating an XML Catalog</a></h2>

<p>If the DTD or RelaxNG Schema for the dialect does not have a catalog
file, you can create one by mapping the external identifiers and URI
references in the document's namespace declaration to a local filesystem
URI. For example, the <a target="_blank"
href="http://www.xspf.org/specs/">
<acronym title="XML Shareable Playlist Format">XSPF</acronym></a>
playlist format uses the following namespace declaration:</p>

<pre>
  &lt;playlist version="1" xmlns="http://xspf.org/ns/0/"&gt;
</pre>

<p>A simple catalog for this XML dialect would look like this:</p>

<pre>
  &lt;?xml version='1.0'?&gt;
  &lt;catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog"
  prefer="public"&gt;

    &lt;uri name="http://xspf.org/ns/0/" uri="xspf-draft8.rng"/&gt;

  &lt;/catalog&gt;
</pre>

<p>If your documents use the DOCTYPE declaration, you can add support
for that in the catalog by using the public and system identifier. For
example, <a target="_blank" href="http://www.mozilla.org/projects/xul/">
<acronym title="XML User Interface Language">XUL</acronym></a> uses
DOCTYPE declarations like this one:</p>

<pre>
  &lt;!DOCTYPE overlay PUBLIC "-//MOZILLA//DTD XUL V1.0//EN"
  "http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul"&gt;
</pre>

<p>Komodo's catalog for XUL uses <code>publicId</code> and
<code>systemId</code> in addition to <code>uri</code> for the
mapping.</p>

<pre>
  &lt;?xml version='1.0'?&gt;
  &lt;catalog xmlns="urn:oasis:names:tc:entity:xmlns:xml:catalog" prefer="public"&gt;

      &lt;public publicId="-//MOZILLA//DTD XUL V1.0//EN"
              uri="xul.dtd"/&gt;
      &lt;system systemId="http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul"
              uri="xul.dtd"/&gt;
      &lt;uri name="http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul"
           uri="xul.dtd"/&gt;

  &lt;/catalog&gt;
</pre>

<p><script>writelinks('creating_xml_catalogs');</script>&nbsp;</p>

<h2><a name="xml_catalog_resources">XML Catalog Resources</a></h2>

<p>The XML Catalog specification can be found at:</p>

<ul>
  <li><a target="_blank"
  href="http://www.oasis-open.org/committees/entity/spec.html">
  http://www.oasis-open.org/committees/entity/spec.html</a></li>
</ul>

<p>Examples of XML catalog files can be found in the Komodo installation
under:</p>

<ul>
  <li><em>&lt;komodo-install-directory&gt;\lib\support\catalogs</em>
  (Windows)</li>
  <li><em>/Applications/Komodo.app/Contents/SharedSupport/catalogs/ (OS
  X)</em></li>
  <li><em>&lt;komodo-install-directory&gt;/lib/support/catalogs</em>
  (Linux)</li>
</ul>

<p><script>writelinks('xml_catalog_resources');</script>&nbsp;</p>

<!-- Footer Start -->
<hr>

</td>
</tr>
</table>

</body>
</html>

"""
    tree = HTML(data)
    #print ElementTree.tostring(tree)

    data = """<html>
<HEAD>
<?php print $javascript->link('calendar') ?>
    
    <?php $othAuth->init($othAuth->data);?>
<!--[if lte IE 6]-->
    <?php echo $html->css{'hack'};?>
        <!--[endif]-->
<script type="text/javascript">
function fadeTableRow(rowid, opts) {
    if (!spts) {
        opts = {};
    }
}
</script>
</head>
<body>"""
    tree = HTML(data)
    #print ElementTree.tostring(tree)

    data = """<%= error_messages_for 'product' %>

<!--[form:product]-->
<p><label for="product_title">Title</label><br/>
<%= text_field 'product', 'title'  %></p>

<p><label for="product_description">Description</label><br/>
<%= text_area 'product', 'description'  %></p>

<p><label for="product_image_url">Image url</label><br/>
<%= text_field 'product', 'image_url'  %></p>

<p><label for="product_price">Price</label><br/>
<%= text_field 'product', 'price'  %></p>

<p><label for="product_date_available">Date available</label><br/>
<%= datetime_select 'product', 'date_available'  %></p>
<!--[eoform:product]-->

"""
    tree = HTML(data)
    print ElementTree.tostring(tree)
    p = Parser(HTMLTreeBuilder())
    p.feed(data)
    p.close()
   
