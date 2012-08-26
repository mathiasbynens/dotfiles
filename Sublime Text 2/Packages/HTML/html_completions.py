import sublime, sublime_plugin
import re

def match(rex, str):
    m = rex.match(str)
    if m:
        return m.group(0)
    else:
        return None

# This responds to on_query_completions, but conceptually it's expanding
# expressions, rather than completing words.
#
# It expands these simple expressions:
# tag.class
# tag#id
class HtmlCompletions(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        # Only trigger within HTML
        if not view.match_selector(locations[0],
                "text.html - source - meta.tag, punctuation.definition.tag.begin"):
            return []

        # Get the contents of each line, from the beginning of the line to
        # each point
        lines = [view.substr(sublime.Region(view.line(l).a, l))
            for l in locations]

        # Reverse the contents of each line, to simulate having the regex
        # match backwards
        lines = [l[::-1] for l in lines]

        # Check the first location looks like an expression
        rex = re.compile("([\w-]+)([.#])(\w+)")
        expr = match(rex, lines[0])
        if not expr:
            return []

        # Ensure that all other lines have identical expressions
        for i in xrange(1, len(lines)):
            ex = match(rex, lines[i])
            if ex != expr:
                return []

        # Return the completions
        arg, op, tag = rex.match(expr).groups()

        arg = arg[::-1]
        tag = tag[::-1]
        expr = expr[::-1]

        if op == '.':
            snippet = "<{0} class=\"{1}\">$1</{0}>$0".format(tag, arg)
        else:
            snippet = "<{0} id=\"{1}\">$1</{0}>$0".format(tag, arg)

        return [(expr, snippet)]


# Provide completions that match just after typing an opening angle bracket
class TagCompletions(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        # Only trigger within HTML
        if not view.match_selector(locations[0],
                "text.html - source"):
            return []

        pt = locations[0] - len(prefix) - 1
        ch = view.substr(sublime.Region(pt, pt + 1))
        if ch != '<':
            return []

        return ([
            ("a\tTag", "a href=\"$1\">$2</a>"),
            ("abbr\tTag", "abbr>$1</abbr>"),
            ("acronym\tTag", "acronym>$1</acronym>"),
            ("address\tTag", "address>$1</address>"),
            ("applet\tTag", "applet>$1</applet>"),
            ("area\tTag", "area>$1</area>"),
            ("b\tTag", "b>$1</b>"),
            ("base\tTag", "base>$1</base>"),
            ("big\tTag", "big>$1</big>"),
            ("blockquote\tTag", "blockquote>$1</blockquote>"),
            ("body\tTag", "body>$1</body>"),
            ("button\tTag", "button>$1</button>"),
            ("center\tTag", "center>$1</center>"),
            ("caption\tTag", "caption>$1</caption>"),
            ("cdata\tTag", "cdata>$1</cdata>"),
            ("cite\tTag", "cite>$1</cite>"),
            ("col\tTag", "col>$1</col>"),
            ("colgroup\tTag", "colgroup>$1</colgroup>"),
            ("code\tTag", "code>$1</code>"),
            ("div\tTag", "div>$1</div>"),
            ("dd\tTag", "dd>$1</dd>"),
            ("del\tTag", "del>$1</del>"),
            ("dfn\tTag", "dfn>$1</dfn>"),
            ("dl\tTag", "dl>$1</dl>"),
            ("dt\tTag", "dt>$1</dt>"),
            ("em\tTag", "em>$1</em>"),
            ("fieldset\tTag", "fieldset>$1</fieldset>"),
            ("font\tTag", "font>$1</font>"),
            ("form\tTag", "form>$1</form>"),
            ("frame\tTag", "frame>$1</frame>"),
            ("frameset\tTag", "frameset>$1</frameset>"),
            ("head\tTag", "head>$1</head>"),
            ("h1\tTag", "h1>$1</h1>"),
            ("h2\tTag", "h2>$1</h2>"),
            ("h3\tTag", "h3>$1</h3>"),
            ("h4\tTag", "h4>$1</h4>"),
            ("h5\tTag", "h5>$1</h5>"),
            ("h6\tTag", "h6>$1</h6>"),
            ("i\tTag", "i>$1</i>"),
            ("iframe\tTag", "iframe src=\"$1\"></iframe>"),
            ("ins\tTag", "ins>$1</ins>"),
            ("kbd\tTag", "kbd>$1</kbd>"),
            ("li\tTag", "li>$1</li>"),
            ("label\tTag", "label>$1</label>"),
            ("legend\tTag", "legend>$1</legend>"),
            ("link\tTag", "link rel=\"stylesheet\" type=\"text/css\" href=\"$1\">"),
            ("map\tTag", "map>$1</map>"),
            ("noframes\tTag", "noframes>$1</noframes>"),
            ("object\tTag", "object>$1</object>"),
            ("ol\tTag", "ol>$1</ol>"),
            ("optgroup\tTag", "optgroup>$1</optgroup>"),
            ("option\tTag", "option>$0</option>"),
            ("p\tTag", "p>$1</p>"),
            ("pre\tTag", "pre>$1</pre>"),
            ("span\tTag", "span>$1</span>"),
            ("samp\tTag", "samp>$1</samp>"),
            ("script\tTag", "script type=\"${1:text/javascript}\">$0</script>"),
            ("style\tTag", "style type=\"${1:text/css}\">$0</style>"),
            ("select\tTag", "select>$1</select>"),
            ("small\tTag", "small>$1</small>"),
            ("strong\tTag", "strong>$1</strong>"),
            ("sub\tTag", "sub>$1</sub>"),
            ("sup\tTag", "sup>$1</sup>"),
            ("table\tTag", "table>$1</table>"),
            ("tbody\tTag", "tbody>$1</tbody>"),
            ("td\tTag", "td>$1</td>"),
            ("textarea\tTag", "textarea>$1</textarea>"),
            ("tfoot\tTag", "tfoot>$1</tfoot>"),
            ("th\tTag", "th>$1</th>"),
            ("thead\tTag", "thead>$1</thead>"),
            ("title\tTag", "title>$1</title>"),
            ("tr\tTag", "tr>$1</tr>"),
            ("tt\tTag", "tt>$1</tt>"),
            ("u\tTag", "u>$1</u>"),
            ("ul\tTag", "ul>$1</ul>"),
            ("var\tTag", "var>$1</var>"),

            ("br\tTag", "br>"),
            ("embed\tTag", "embed>"),
            ("hr\tTag", "hr>"),
            ("img\tTag", "img src=\"$1\">"),
            ("input\tTag", "input>"),
            ("meta\tTag", "meta>"),
            ("param\tTag", "param name=\"$1\" value=\"$2\">"),

            ("article\tTag", "article>$1</article>"),
            ("aside\tTag", "aside>$1</aside>"),
            ("audio\tTag", "audio>$1</audio>"),
            ("canvas\tTag", "canvas>$1</canvas>"),
            ("footer\tTag", "footer>$1</footer>"),
            ("header\tTag", "header>$1</header>"),
            ("nav\tTag", "nav>$1</nav>"),
            ("section\tTag", "section>$1</section>"),
            ("video\tTag", "video>$1</video>"),

            ("A\tTag", "A HREF=\"$1\">$2</A>"),
            ("ABBR\tTag", "ABBR>$1</ABBR>"),
            ("ACRONYM\tTag", "ACRONYM>$1</ACRONYM>"),
            ("ADDRESS\tTag", "ADDRESS>$1</ADDRESS>"),
            ("APPLET\tTag", "APPLET>$1</APPLET>"),
            ("AREA\tTag", "AREA>$1</AREA>"),
            ("B\tTag", "B>$1</B>"),
            ("BASE\tTag", "BASE>$1</BASE>"),
            ("BIG\tTag", "BIG>$1</BIG>"),
            ("BLOCKQUOTE\tTag", "BLOCKQUOTE>$1</BLOCKQUOTE>"),
            ("BODY\tTag", "BODY>$1</BODY>"),
            ("BUTTON\tTag", "BUTTON>$1</BUTTON>"),
            ("CENTER\tTag", "CENTER>$1</CENTER>"),
            ("CAPTION\tTag", "CAPTION>$1</CAPTION>"),
            ("CDATA\tTag", "CDATA>$1</CDATA>"),
            ("CITE\tTag", "CITE>$1</CITE>"),
            ("COL\tTag", "COL>$1</COL>"),
            ("COLGROUP\tTag", "COLGROUP>$1</COLGROUP>"),
            ("CODE\tTag", "CODE>$1</CODE>"),
            ("DIV\tTag", "DIV>$1</DIV>"),
            ("DD\tTag", "DD>$1</DD>"),
            ("DEL\tTag", "DEL>$1</DEL>"),
            ("DFN\tTag", "DFN>$1</DFN>"),
            ("DL\tTag", "DL>$1</DL>"),
            ("DT\tTag", "DT>$1</DT>"),
            ("EM\tTag", "EM>$1</EM>"),
            ("FIELDSET\tTag", "FIELDSET>$1</FIELDSET>"),
            ("FONT\tTag", "FONT>$1</FONT>"),
            ("FORM\tTag", "FORM>$1</FORM>"),
            ("FRAME\tTag", "FRAME>$1</FRAME>"),
            ("FRAMESET\tTag", "FRAMESET>$1</FRAMESET>"),
            ("HEAD\tTag", "HEAD>$1</HEAD>"),
            ("H1\tTag", "H1>$1</H1>"),
            ("H2\tTag", "H2>$1</H2>"),
            ("H3\tTag", "H3>$1</H3>"),
            ("H4\tTag", "H4>$1</H4>"),
            ("H5\tTag", "H5>$1</H5>"),
            ("H6\tTag", "H6>$1</H6>"),
            ("I\tTag", "I>$1</I>"),
            ("IFRAME\tTag", "IFRAME src=\"$1\"></IFRAME>"),
            ("INS\tTag", "INS>$1</INS>"),
            ("KBD\tTag", "KBD>$1</KBD>"),
            ("LI\tTag", "LI>$1</LI>"),
            ("LABEL\tTag", "LABEL>$1</LABEL>"),
            ("LEGEND\tTag", "LEGEND>$1</LEGEND>"),
            ("LINK\tTag", "LINK>$1</LINK>"),
            ("MAP\tTag", "MAP>$1</MAP>"),
            ("NOFRAMES\tTag", "NOFRAMES>$1</NOFRAMES>"),
            ("OBJECT\tTag", "OBJECT>$1</OBJECT>"),
            ("OL\tTag", "OL>$1</OL>"),
            ("OPTGROUP\tTag", "OPTGROUP>$1</OPTGROUP>"),
            ("OPTION\tTag", "OPTION>$1</OPTION>"),
            ("P\tTag", "P>$1</P>"),
            ("PRE\tTag", "PRE>$1</PRE>"),
            ("SPAN\tTag", "SPAN>$1</SPAN>"),
            ("SAMP\tTag", "SAMP>$1</SAMP>"),
            ("SCRIPT\tTag", "SCRIPT TYPE=\"${1:text/javascript}\">$0</SCRIPT>"),
            ("STYLE\tTag", "STYLE TYPE=\"${1:text/css}\">$0</STYLE>"),
            ("SELECT\tTag", "SELECT>$1</SELECT>"),
            ("SMALL\tTag", "SMALL>$1</SMALL>"),
            ("STRONG\tTag", "STRONG>$1</STRONG>"),
            ("SUB\tTag", "SUB>$1</SUB>"),
            ("SUP\tTag", "SUP>$1</SUP>"),
            ("TABLE\tTag", "TABLE>$1</TABLE>"),
            ("TBODY\tTag", "TBODY>$1</TBODY>"),
            ("TD\tTag", "TD>$1</TD>"),
            ("TEXTAREA\tTag", "TEXTAREA>$1</TEXTAREA>"),
            ("TFOOT\tTag", "TFOOT>$1</TFOOT>"),
            ("TH\tTag", "TH>$1</TH>"),
            ("THEAD\tTag", "THEAD>$1</THEAD>"),
            ("TITLE\tTag", "TITLE>$1</TITLE>"),
            ("TR\tTag", "TR>$1</TR>"),
            ("TT\tTag", "TT>$1</TT>"),
            ("U\tTag", "U>$1</U>"),
            ("UL\tTag", "UL>$1</UL>"),
            ("VAR\tTag", "VAR>$1</VAR>"),

            ("BR\tTag", "BR>"),
            ("EMBED\tTag", "EMBED>"),
            ("HR\tTag", "HR>"),
            ("IMG\tTag", "IMG SRC=\"$1\">"),
            ("INPUT\tTag", "INPUT>"),
            ("META\tTag", "META>"),
            ("PARAM\tTag", "PARAM NAME=\"$1\" VALUE=\"$2\">)"),

            ("ARTICLE\tTag", "ARTICLE>$1</ARTICLE>"),
            ("ASIDE\tTag", "ASIDE>$1</ASIDE>"),
            ("AUDIO\tTag", "AUDIO>$1</AUDIO>"),
            ("CANVAS\tTag", "CANVAS>$1</CANVAS>"),
            ("FOOTER\tTag", "FOOTER>$1</FOOTER>"),
            ("HEADER\tTag", "HEADER>$1</HEADER>"),
            ("NAV\tTag", "NAV>$1</NAV>"),
            ("SECTION\tTag", "SECTION>$1</SECTION>"),
            ("VIDEO\tTag", "VIDEO>$1</VIDEO>")
        ], sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)
