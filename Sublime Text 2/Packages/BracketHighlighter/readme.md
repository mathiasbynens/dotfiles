# About
This is a fork of pyparadigm's SublimeBrackets and SublimeTagmatcher (both are no longer available).  I forked this to fix some issues I had and to add some features I wanted.  I also wanted to improve the efficiency of the matching.  This cuts down on the parallel searching that is now streamlined in one search.  Since then, many new features have been added as well.

![Options Screenshot](https://github.com/facelessuser/BracketHighlighter/raw/master/example.png)

# Installation
- Download is available in Package Control or you can [download](https://github.com/facelessuser/BracketHighlighter/zipball/master "download") or clone directly and drop into your Sublime Text 2 packages directory (plugin folder must be named BracketHighlighter)
- You may need to restart Sublime Text 2 after installation

# Features
- Customizable highlighting of brackets (),[],<>,{}
- Customizable highlighting of Tags (supports unary tags and supports self closing /> (HTML5 coming))
- Customizable highlighting of quotes
- Selectively disable or enable specific matching of tags, brackets, or quotes
- Selectively whitelist or blacklist matching of specific tags, brackets, or quotes based on language
- When using on demand shortcut, show line count and char count between match in the status bar
- Shortcuts for moving cursor to beginning or end of bracketed content (will focus on beginning or end bracket if not currently multi-selecting)
- Shortcut for selecting all of the bracketed content
- Shortcut for chaning quote style (accounts for escaped quotes as well)
- Works with multi-select
- Bracket related plugins
- Configurable custom gutter icons
- Highlight brackets within strings
- Toggle bracket escape mode for string brackets (regex|string)
- Experimental CFML support (read below for more info)

# Included Plugins
- bracketselect: move cursor to opening bracket or closing bracket or select all content between brackets
- foldbracket: fold according to brackets
- swapbrackets: change the current selected brackets to another bracket type
- swapquotes: change the currently selected quotes from single to double or double to single (scope based)
- tagattrselect: cycle through selecting html tags
- tagnameselect: select the name in the opening and closing tag

# Options
- Open BracketHighlighter.sublime-settings and configure your preferences (can be accessed from menu).
- Change the scope, highlight style, icon for bracket types, which brackets to match, set search thresholds, etc.
- Save the file and your options should take effect immediately.

# CFML support
CFML support is currently experimental.  In order to enable it, you must add the CFML lanugage name to the whitelist (or exclude it from the list if using blacklist).  If using the ColdFusion from https://github.com/SublimeText/ColdFusion, you can follow the example below:

```js
"angle_language_list" : ["HTML","HTML 5","XML","PHP", "ColdFusion", "ColdFusionCFC"],
"tag_language_list"   : ["HTML","HTML 5","XML","PHP", "ColdFusion", "ColdFusionCFC"],
```

After that, you must make sure ```tag_type``` is set to ```cmfl``` like below:

```js
"tag_type" : "cfml",
```

It is also good to make sure that self-closing detection is enalbed (this is also experimental):

```js
"detect_self_closing_tags": true,
```

#Changing Colors
The color is based on the scope you assign to the highlight. The color of the scope is defined by your theme file.  By default, the scope is "entity.name.class", but you could change it to "keyword" or any other scope in your theme.

```js
//Scope? (Defined in theme files.)
//Examples: (keyword|string|number)
"quote_scope" : "entity.name.class",
"curly_scope" : "entity.name.class",
"round_scope" : "entity.name.class",
"square_scope": "entity.name.class",
"angle_scope" : "entity.name.class",
"tag_scope"   : "entity.name.class",
```

If you want more control of the colors, you can define your own scopes.

```xml
<dict>
    <key>name</key>
    <string>Bracket Tag</string>
    <key>scope</key>
    <string>brackethighlighter.tag</string>
    <key>settings</key>
    <dict>
        <key>foreground</key>
        <string>#FD971F</string>
    </dict>
</dict>
<dict>
    <key>name</key>
    <string>Bracket Curly</string>
    <key>scope</key>
    <string>brackethighlighter.curly</string>
    <key>settings</key>
    <dict>
        <key>foreground</key>
        <string>#66D9EF</string>
    </dict>
</dict>
<dict>
    <key>name</key>
    <string>Bracket Round</string>
    <key>scope</key>
    <string>brackethighlighter.round</string>
    <key>settings</key>
    <dict>
        <key>foreground</key>
        <string>#F92672</string>
    </dict>
</dict>
<dict>
    <key>name</key>
    <string>Bracket Square</string>
    <key>scope</key>
    <string>brackethighlighter.square</string>
    <key>settings</key>
    <dict>
        <key>foreground</key>
        <string>#A6E22E</string>
    </dict>
</dict>
<dict>
    <key>name</key>
    <string>Bracket Angle</string>
    <key>scope</key>
    <string>brackethighlighter.angle</string>
    <key>settings</key>
    <dict>
        <key>foreground</key>
        <string>#AE81FF</string>
    </dict>
</dict>
<dict>
    <key>name</key>
    <string>Bracket Quote</string>
    <key>scope</key>
    <string>brackethighlighter.quote</string>
    <key>settings</key>
    <dict>
        <key>foreground</key>
        <string>#FAF60A</string>
    </dict>
</dict>
```

# Version 1.9.0
- Add experimental CFML support (defaulted off)
- Add auto-detection of self-closing tags (defaulted on)

# Version 1.8.0
- Add new commands: "Show Bracket String Escape Mode" and "Toggle Bracket String Escape Mode".  Default is "regex"

# Version 1.7.2
- Feed general bracket type to bracket plugins
- Adjust bracket select plugin to better handle HTML tags

# Version 1.7.1
- Reorganize some settings
- Limit auto-highlight selections by configurable threshold setting

# Version 1.7.0
- Hide parent quote highlighting when child quotes are highlighted
- Allow the searching for brackets in non-quoted code scoped as strings (like regex)
- Add setting "highlight_string_brackets_only" which allows never highlighting quotes but leaves internal string bracket highlighting on
- deprecate "enable_forward_slash_regex_strings" in favor of "find_brackets_in any_strings"

# Version 1.6.2
- Fix adjacent_only with multi_select

# Version 1.6.1
- Suppress string highlighting when adjacent_only is set, but allow internal string brackets to still get highlighted with adjacent_only settings if match_string_brackets is true

# Version 1.6.0
- Add setting to match only when cursor is between brackets

# Version 1.5.3
- Allow turning off gutter icons for multi-select via settings
- Fix multi-select detection
- Default the internal settings if setting is not found

# Version 1.5.2
- Use tiny icons when line height is less than 16
- Use no icon if icon cannot be found
- Optimize png icons

# Version 1.5.1
- Ignore selection/edit events inside the main routine

# Version 1.5.0
- More responsive highlighting (thanks tito); delay setting no longer needed
- Organize bracket plugins
- Included more configurable custom gutter icons

# Version 1.4.1
- Make adjusment to regex modifier code to correctly count back modifiers in perl

# Version 1.4.0
- Account for perl regex, substitutions, and translations surrounded by "/" for string bracket matching
- Account for regex modifiers when matching regex surrounded by "/" in javascript and perl

# Version 1.3.0
- Fixed escaped brackets in string handling.  Also a bit more efficient.

# Version 1.2.0
- Fix angle bracket avoidance when finding brackets inside strings, and make it cleaner

# Version 1.1.0
- Add python raw string support for quote highlighting
- Add highlighting of brackets in strings; will work in all strings, but mainly meant for regex.  True by default
- Add support for targetting regex strings like in javascript that are scoped as strings, but are not quoted, but use '/'s. True by default

# Version 1.0.0
- All previous work and releases
