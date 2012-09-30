from os.path import basename, exists, join, normpath
from Elements import is_tag, match
import sublime
import sublime_plugin
from bracket_plugin import BracketPlugin
from time import time, sleep
import thread

BH_MATCH_TYPE_NONE = 0
BH_MATCH_TYPE_SELECTION = 1
BH_MATCH_TYPE_EDIT = 2


class Pref(object):
    @classmethod
    def load(cls):
        cls.wait_time = 0.12
        cls.time = time()
        cls.modified = False
        cls.type = BH_MATCH_TYPE_SELECTION
        cls.ignore_all = False

Pref.load()


class ToggleBracketStringEscapeModeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        default_mode = sublime.load_settings("BracketHighlighter.sublime-settings").get('default_bracket_string_escape_mode', 'regex')
        if self.view.settings().get('bracket_string_escape_mode', default_mode) == "regex":
            self.view.settings().set('bracket_string_escape_mode', "string")
            sublime.status_message("Bracket String Escape Mode: string")
        else:
            self.view.settings().set('bracket_string_escape_mode', "regex")
            sublime.status_message("Bracket String Escape Mode: regex")


class ShowBracketStringEscapeModeCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        default_mode = sublime.load_settings("BracketHighlighter.sublime-settings").get('default_bracket_string_escape_mode', 'regex')
        sublime.status_message("Bracket String Escape Mode: %s" % self.view.settings().get('bracket_string_escape_mode', default_mode))


class BracketHighlighterKeyCommand(sublime_plugin.WindowCommand):
    def run(self, threshold=True, lines=False, adjacent=False, ignore={}, plugin={}):
        # Override events
        Pref.ignore_all = True
        Pref.modified = False
        BracketHighlighter(
            threshold,
            lines,
            adjacent,
            ignore,
            plugin
        ).match(self.window.active_view())
        # Reset event settings
        Pref.ignore_all = False
        Pref.time = time()


class BracketHighlighter(object):
    # Initialize
    def __init__(self, override_thresh=False, count_lines=False, adj_only=None, ignore={}, plugin={}):
        self.settings = sublime.load_settings("BracketHighlighter.sublime-settings")
        self.settings.add_on_change('reload', lambda: self.setup())
        self.setup(override_thresh, count_lines, adj_only, ignore, plugin)

    def setup(self, override_thresh=False, count_lines=False, adj_only=None, ignore={}, plugin={}):
        self.last_id_view = None
        self.last_id_sel = None
        self.targets = []
        self.sels = []
        self.highlight_us = {}
        self.brackets = self.init_brackets()
        self.lines = 0
        self.chars = 0
        self.count_lines = count_lines
        self.new_select = False

        # On demand ignore
        self.ignore = ignore

        # Setup for bracket plugins
        self.transform = {
            'quote':   False,
            'bracket': False,
            'tag':     False
        }

        if 'command' in plugin:
            self.plugin = BracketPlugin(plugin)
            self.new_select = True
            if 'type' in plugin:
                if 'quote' in plugin['type']:
                    self.transform['quote'] = True
                if 'bracket' in plugin['type']:
                    self.transform['bracket'] = True
                if 'tag' in plugin['type']:
                    self.transform['tag'] = True

        # General search options
        self.adj_only = adj_only if adj_only != None else bool(self.settings.get('match_adjacent_only', False))
        self.use_threshold = False if override_thresh else bool(self.settings.get('use_search_threshold', True))
        self.tag_use_threshold = False if override_thresh else bool(self.settings.get('tag_use_search_threshold', True))
        self.use_selection_threshold = False if override_thresh else True
        self.search_threshold = int(self.settings.get('search_threshold', 2000))
        self.tag_search_threshold = int(self.settings.get('tag_search_threshold', 2000))
        self.selection_threshold = int(self.settings.get('auto_selection_threshold', 10))
        self.no_multi_select_icons = bool(self.settings.get('no_multi_select_icons', False))

        # Match convention
        match_between = bool(self.settings.get('match_brackets_only_when_between', True))
        self.adj_adjust = self.adjacent_adjust_inside if match_between else self.adjacent_adjust
        self.string_adj_adjust = self.string_adjacent_adjust_inside if match_between else self.string_adjacent_adjust

        # Tag special options
        self.brackets_only = bool(self.settings.get('tag_brackets_only', False))
        self.ignore_angle = bool(self.settings.get('ignore_non_tags', False))
        self.tag_type = self.settings.get('tag_type', 'html')

        # String Options
        self.match_string_brackets = bool(self.settings.get('match_string_brackets', True))
        self.find_brackets_in_any_string = bool(self.settings.get('find_brackets_in_any_string', False))
        self.ignore_string_bracket_parent = bool(self.settings.get('highlight_string_brackets_only', False))

    def init_brackets(self):
        quote_open = "r ' \""
        quote_close = "' \""
        return {
            'bh_curly':  self.get_bracket_settings('curly', '{', '}'),
            'bh_round':  self.get_bracket_settings('round', '(', ')'),
            'bh_square': self.get_bracket_settings('square', '[', ']'),
            'bh_angle':  self.get_bracket_settings('angle', '<', '>'),
            'bh_tag':    self.get_bracket_settings('tag', '<', '>'),
            'bh_quote':  self.get_bracket_settings('quote', quote_open, quote_close)
        }

    def get_bracket_settings(self, bracket, opening, closing):
        # Style
        highlight_style = self.settings.get(bracket + '_style', "none")
        style = sublime.HIDE_ON_MINIMAP
        if highlight_style == "outline":
            style |= sublime.DRAW_OUTLINED
        elif highlight_style == "none":
            style |= sublime.HIDDEN
        elif highlight_style == "underline":
            style |= sublime.DRAW_EMPTY_AS_OVERWRITE

        # Icon
        highlight_icon = self.settings.get(bracket + '_icon', "")
        icon = ""
        small_icon = ""
        icon_path = self.settings.get("icon_path", "Theme - Default").replace('\\', '/').strip('/')
        # Icon exist?
        if (
            exists(normpath(join(sublime.packages_path(), icon_path, highlight_icon + ".png"))) and
            not highlight_icon == "none" and not highlight_icon == ""
        ):
            icon = "../%s/%s" % (icon_path, highlight_icon)
            if exists(normpath(join(sublime.packages_path(), icon_path, highlight_icon + "_small.png"))):
                small_icon = "../%s/%s" % (icon_path, highlight_icon + "_small")

        return {
            'enable':     bool(self.settings.get(bracket + '_enable', True)),
            'scope':      self.settings.get(bracket + '_scope'),
            'style':      style,
            'underline':  (highlight_style == "underline"),
            'icon':       icon,
            'small_icon': small_icon,
            'no_icon':    "",
            'list':       map(lambda x: x.lower(), self.settings.get(bracket + '_language_list', [])),
            'filter':     self.settings.get(bracket + '_language_filter', []),
            'open':       opening,
            'close':      closing
        }

    def init_match(self):
        # Current language
        syntax = self.view.settings().get('syntax')
        language = basename(syntax).replace('.tmLanguage', '').lower() if syntax != None else "plain text"
        # Reset objects
        self.sels = []
        self.targets = []
        self.highlight_us = {}
        self.lines = 0

        # Standard Brackets
        if self.exclude_bracket('bh_curly', language) == False:
            self.add_bracket('bh_curly')
        if self.exclude_bracket('bh_round', language) == False:
            self.add_bracket('bh_round')
        if self.exclude_bracket('bh_square', language) == False:
            self.add_bracket('bh_square')
        if self.exclude_bracket('bh_angle', language) == False:
            self.add_bracket('bh_angle')
        # Tags
        if self.exclude_bracket('bh_tag', language) == False:
            self.tag_enable = True
            self.highlight_us['bh_tag'] = []
        else:
            self.tag_enable = False
        # Quotes
        if self.exclude_bracket('bh_quote', language) == False:
            self.quote_enable = True
            self.highlight_us['bh_quote'] = []
        else:
            self.quote_enable = False

    def add_bracket(self, bracket):
        self.highlight_us[bracket] = []
        self.targets.append(bracket)

    def exclude_bracket(self, bracket, language):
        exclude = True
        if bracket.replace('bh_', '') in self.ignore:
            return exclude
        if self.brackets[bracket]['enable']:
            # Black list languages
            if self.brackets[bracket]['filter'] == 'blacklist':
                exclude = False
                if language != None:
                    for item in self.brackets[bracket]['list']:
                        if language == item:
                            exclude = True
                            break
            #White list languages
            elif self.brackets[bracket]['filter'] == 'whitelist':
                if language != None:
                    for item in self.brackets[bracket]['list']:
                        if language == item:
                            exclude = False
                            break
        return exclude

    def unique(self):
        id_view = self.view.id()
        id_sel = ''
        is_unique = False
        for sel in self.view.sel():
            id_sel += str(sel.a)
        if id_view != self.last_id_view or id_sel != self.last_id_sel:
            self.last_id_view = id_view
            self.last_id_sel = id_sel
            is_unique = True
        return is_unique

    def highlight(self, view):
        # Perform highlight on brackets and tags
        icon_type = "no_icon"
        if not self.no_multi_select_icons or not self.multi_select:
            icon_type = "small_icon" if view.line_height() < 16 else "icon"
        for bracket in self.brackets:
            if bracket in self.highlight_us:
                view.add_regions(
                    bracket,
                    self.highlight_us[bracket],
                    self.brackets[bracket]['scope'],
                    self.brackets[bracket][icon_type],
                    self.brackets[bracket]['style']
                )
            else:
                view.erase_regions(bracket)

    def store_sel(self, regions):
        if self.new_select == True:
            for region in regions:
                self.sels.append(region)

    def change_sel(self):
        if self.new_select != None and len(self.sels) > 0:
            if self.multi_select == False:
                self.view.show(self.sels[0])
            self.view.sel().clear()
            map(lambda x: self.view.sel().add(x), self.sels)

    def adjacent_adjust_inside(self, scout):
        # Offset cursor
        offset = 0
        self.adj_bracket = False
        allow_quote_match = True
        # If quotes enbaled, kick out of adjacent check if in middle of string
        if (
            self.view.score_selector(scout, 'string') > 0 and
            self.view.score_selector(scout - 1, 'string') > 0 and
            self.quote_enable
        ):
            return (offset, allow_quote_match)
        allow_quote_match = False
        char1 = self.view.substr(scout - 1)
        char2 = self.view.substr(scout)
        for bracket in self.targets:
            if char2 == self.brackets[bracket]['close']:
                offset = -1
                self.adj_bracket = True
                break
            if char2 == self.brackets[bracket]['open'] and offset != -1:
                offset = -1
            if char1 == self.brackets[bracket]['open']:
                if offset != -1:
                    offset = -1
                self.adj_bracket = True
                break
        return (offset, allow_quote_match)

    def adjacent_adjust(self, scout):
        # Offset cursor
        offset = 0
        self.adj_bracket = False
        allow_quote_match = True
        # If quotes enbaled, kick out of adjacent check if in middle of string
        if (
            self.view.score_selector(scout, 'string') > 0 and
            self.view.score_selector(scout - 1, 'string') > 0 and
            self.quote_enable
        ):
            return (offset, allow_quote_match)
        char1 = self.view.substr(scout - 1)
        char2 = self.view.substr(scout)
        for bracket in self.targets:
            if char2 == self.brackets[bracket]['open']:
                self.adj_bracket = True
            if char1 == self.brackets[bracket]['open']:
                offset = -1
                self.adj_bracket = True
                allow_quote_match = False
                break
            elif char1 == self.brackets[bracket]['close']:
                offset = -2
                self.adj_bracket = True
                allow_quote_match = False
            elif char2 == self.brackets[bracket]['close'] and offset != -2:
                offset = -1
                self.adj_bracket = True
                allow_quote_match = True
        if offset == 0:
            allow_quote_match = True
        return (offset, allow_quote_match)

    def match(self, view, force_match=True):
        if view == None:
            return
        # Setup views
        self.view = view
        self.last_view = view
        num_sels = len(view.sel())
        self.multi_select = (num_sels > 1)

        if self.unique() or force_match:
            # Initialize
            self.init_match()

            # Abort if selections are beyond the threshold
            if self.use_selection_threshold and num_sels >= self.selection_threshold:
                self.highlight(view)
                return

            # Process selections.
            for sel in view.sel():
                self.find_matches(sel)

        # Highlight, focus, and display lines etc.
        self.change_sel()
        self.highlight(view)
        if self.count_lines:
            sublime.status_message('In Block: Lines ' + str(self.lines) + ', Chars ' + str(self.chars))

    def find_matches(self, sel):
        (offset, allow_quote_match) = self.adj_adjust(sel.a)
        start = sel.a
        matched = False
        is_string = False
        self.search_left = self.search_threshold

        # Match quotes if enabled
        if self.quote_enable and allow_quote_match:
            (matched, start, is_string) = self.match_quotes(sel)
            # Found quotes; exit
            if matched:
                return

        # Special considerations for cusrsor adjacent to bracket
        if matched == False and is_string == False:
            start += offset
        # If not adjacent to bracket and adjacent enabled, exit
        if self.adj_only:
            if not self.adj_bracket:
                return

        # Find left brace
        left = self.scout_left(start)
        if left != None:
            # Find right brace
            right = self.scout_right(start + 1)

        regions = [sublime.Region(sel.a, sel.b)]

        # Bracket Matches found
        if left != None and right != None:
            # Angle specific
            if self.bracket_type == 'bh_angle':
                # Find tags if required
                if (
                    self.tag_enable and
                    is_tag(self.view.substr(sublime.Region(left, right + 1)))
                ):
                    # Found tag; quit
                    if self.match_tags(left, right, sel):
                        return
                # Continue higlighting angle unless required not to
                if self.ignore_angle:
                    self.store_sel(regions)
                    return

            # Set higlight regions
            if (
                self.transform['bracket'] and
                self.plugin != None and
                self.plugin.is_enabled()
            ):
                (b_region, c_region, regions) = self.plugin.run_command(
                    sublime.Region(left, right + 1),
                    sublime.Region(left + 1, right),
                    regions,
                    "bracket"
                )
                left = b_region.a
                right = b_region.b - 1
            if self.brackets[self.bracket_type]['underline']:
                self.highlight_us[self.bracket_type].append(sublime.Region(left))
                self.highlight_us[self.bracket_type].append(sublime.Region(right))
            else:
                self.highlight_us[self.bracket_type].append(sublime.Region(left, left + 1))
                self.highlight_us[self.bracket_type].append(sublime.Region(right, right + 1))
            if self.count_lines:
                self.lines += self.view.rowcol(right)[0] - self.view.rowcol(left)[0] + 1
                self.chars += right - 1 - left
        self.store_sel(regions)

    def scout_left(self, scout):
        count = {}
        for bracket in self.targets:
            count[bracket] = 0

        while scout >= 0:
            if self.use_threshold:
                self.search_left -= 1
                if self.search_left < 0:
                    return None

            # Are we in a string or comment?
            if (
                self.view.score_selector(scout, 'string') == 0 and
                self.view.score_selector(scout, 'comment') == 0 and
                self.view.score_selector(scout, 'keyword.operator') == 0
            ):
                # Assign char.
                char = self.view.substr(scout)
                # Hit brackets.
                foundBracket = False
                for bracket in self.targets:
                    if char == self.brackets[bracket]['open']:
                        if count[bracket] > 0:
                            count[bracket] -= 1
                            foundBracket = True
                            break
                        else:
                            self.bracket_type = bracket
                            self.bracket_open = self.brackets[bracket]['open']
                            self.bracket_close = self.brackets[bracket]['close']
                            return scout

                if foundBracket == False:
                    for bracket in self.targets:
                        if char == self.brackets[bracket]['close']:
                            count[bracket] += 1
                            break
            scout -= 1

    def scout_right(self, scout):
        brackets = 0
        viewSize = self.view.size()

        while scout < viewSize:
            if self.use_threshold:
                self.search_left -= 1
                if self.search_left < 0:
                    return None
            # Are we in a string or comment?
            if (
                self.view.score_selector(scout, 'string') == 0 and
                self.view.score_selector(scout, 'comment') == 0 and
                self.view.score_selector(scout, 'keyword.operator') == 0
            ):

                # Assign char.
                char = self.view.substr(scout)
                # Hit brackets.
                if char == self.bracket_close:
                    if brackets > 0:
                        brackets -= 1
                    else:
                        return scout
                elif char == self.bracket_open:
                    brackets += 1
            scout += 1

    def match_tags(self, start, end, sel):
        self.search_left = self.tag_search_threshold
        matched = False
        tag_highlights = []

        # Go find tags. Limit search with threshold if required
        bufferSize = self.view.size()
        bufferRegion = sublime.Region(0, bufferSize)
        bufferText = self.view.substr(bufferRegion)
        curPosition = start + 1
        foundTags = match(
            bufferText,
            curPosition,
            self.tag_type,
            self.tag_use_threshold,
            self.search_left
        )

        # Find brackets inside tags
        tag1 = {"match": foundTags[0]}
        tag2 = {"match": foundTags[1]}
        if (
            str(tag1['match']) != 'None' and
            self.view.substr(tag1['match'] + 1) != '!' and
            self.view.substr(tag1['match'] - 1) != '`' and
            self.view.substr(tag1['match']) == '<' and
            self.view.substr(curPosition) != '<'
        ):

            # Get 1st Tag
            matched = True
            # Already have end points?
            if tag1['match'] == start:
                tag1['begin'] = start
                tag1['end'] = end
            # Calculate end points
            else:
                tag1['begin'] = tag1['match']
                tag1['end'] = tag1['match']
                while (
                    self.view.substr(tag1['end']) != '>' or
                    self.view.score_selector(tag1['end'], 'string')
                ):
                    tag1['end'] = tag1['end'] + 1
                    if (
                        self.view.substr(tag1['end']) == '<' and
                        self.view.score_selector(tag1['end'], 'string') == 0
                    ):
                        matched = False

            # Get 2nd Tag
            # Already have end points?
            if tag2['match'] == end + 1:
                tag2['end'] = end
                tag2['begin'] = start
            # Calculate end points
            else:
                tag2['end'] = tag2['match'] - 1
                tag2['begin'] = tag2['end']
                while (
                    self.view.substr(tag2['begin']) != '<' or
                    self.view.score_selector(tag2['begin'], 'string')
                ):
                    tag2['begin'] = tag2['begin'] - 1

            # Set Highlight Region
            if matched:
                regions = [sublime.Region(sel.a, sel.b)]
                if (
                    self.transform['tag'] and
                    self.plugin != None and
                    self.plugin.is_enabled()
                ):
                    (b_region, c_region, regions) = self.plugin.run_command(
                        sublime.Region(tag1['begin'], tag2['end'] + 1),
                        sublime.Region(tag1['end'] + 1, tag2['begin']),
                        regions,
                        "tag"
                    )
                    tag1['begin'] = b_region.a
                    tag2['end'] = b_region.b - 1
                    tag1['end'] = c_region.a - 1
                    tag2['begin'] = c_region.b

                # Set highlight regions
                if self.brackets_only:
                    tag_highlights = [
                        sublime.Region(tag1['begin'], tag1['begin'] + 1),
                        sublime.Region(tag1['end'], tag1['end'] + 1),
                        sublime.Region(tag2['begin'], tag2['begin'] + 1),
                        sublime.Region(tag2['end'], tag2['end'] + 1)
                    ]
                else:
                    tag_highlights = [
                        sublime.Region(tag1['begin'], tag1['end'] + 1),
                        sublime.Region(tag2['begin'], tag2['end'] + 1)
                    ]

                # Add highlight regions
                if self.brackets['bh_tag']['underline']:
                    self.underline_tag(tag_highlights)
                else:
                    for highlight in tag_highlights:
                        self.highlight_us['bh_tag'].append(highlight)

                if self.count_lines:
                    self.lines += self.view.rowcol(tag2['begin'])[0] - self.view.rowcol(tag1['end'])[0] + 1
                    self.chars += tag2['begin'] - 1 - tag1['end']
                self.store_sel(regions)
        return matched

    def underline_tag(self, regions):
        for region in regions:
            start = region.begin()
            end = region.end()
            while start < end:
                self.highlight_us['bh_tag'].append(sublime.Region(start))
                start += 1

    def match_quotes(self, sel):
        start = sel.a
        matched = False
        bail = False
        suppress = False
        is_string = False
        #Check if likely a string
        left_side_match = (self.view.score_selector(start, 'string') > 0)
        right_side_match = (self.view.score_selector(start - 1, 'string') > 0)
        if self.adj_only:
            far_left_side_match = (self.view.score_selector(start - 2, 'string') > 0)
            far_right_side_match = (self.view.score_selector(start + 1, 'string') > 0)
            bail = not (
                (left_side_match or right_side_match) and
                (
                    (left_side_match != right_side_match) or
                    not far_left_side_match or
                    not far_right_side_match
                )
            )
            if bail and self.match_string_brackets:
                suppress = True
        if self.ignore_string_bracket_parent and not suppress:
            suppress = True
        if (left_side_match or right_side_match) and (bail == False or suppress == True):
            # Calculate offset
            is_string = True
            offset = -1 if left_side_match == False else 0
            (matched, start) = self.find_quotes(start, offset, sel, suppress)
        return (matched, start, is_string)

    def find_quotes(self, start, offset, sel, suppress):
        actual_start = start
        start += offset
        begin = start
        end = start
        scout = start
        quote = None
        lastChar = None
        matched = False
        viewSize = self.view.size()
        not_quoted = False

        # Left quote
        while scout >= 0:
            if self.use_threshold:
                self.search_left -= 1
                if self.search_left < 0:
                    return (matched, scout)
            char = self.view.substr(scout)
            if self.view.score_selector(scout, 'string') > 0:
                if scout == 0:
                    begin = scout
                    for char_type in self.brackets['bh_quote']['open'].split(' '):
                        if char == char_type:
                            quote, begin = self.check_special_strings_start(lastChar, begin, viewSize)
                            break
                    if quote == None and self.find_brackets_in_any_string:
                        # Not a quoted string
                        not_quoted = True
                    break
                else:
                    scout -= 1
                    lastChar = char
            else:
                begin = scout + 1
                for char_type in self.brackets['bh_quote']['open'].split(' '):
                    if lastChar == char_type:
                        quote, begin = self.check_special_strings_start(lastChar, begin, viewSize)
                        break
                if quote == None and self.find_brackets_in_any_string:
                    # Not a quoted string
                    not_quoted = True
                break

        # If quote fails continue off from furthest left
        # to find other brackets
        search_left = self.search_left
        self.search_left += 1

        # Right quote
        if quote != None or not_quoted:
            scout = start
            lastChar = None
            while scout <= viewSize:
                if self.use_threshold:
                    search_left -= 1
                    if search_left < 0:
                        self.search_left = -1
                        return (matched, begin - 1)
                char = self.view.substr(scout)
                if self.view.score_selector(scout, 'string') > 0:
                    if scout == viewSize:
                        if not_quoted:
                            # Not a quoted string; don't highlight string quotes
                            suppress = True
                            matched = True
                            end = scout
                        else:
                            matched = True
                            end = scout
                        break
                    else:
                        scout += 1
                        lastChar = char
                else:
                    if not_quoted:
                        # Not a quoted string; don't highlight string quotes
                        suppress = True
                        matched = True
                        end = scout
                    else:
                        matched = True
                        end = scout
                    break

        if matched:
            regions = [sublime.Region(sel.a, sel.b)]
            if self.match_string_brackets and start != begin and start != end + 1:
                start = actual_start
                offset = self.string_adj_adjust(start)
                start += offset
                if (self.adj_only and self.adj_bracket) or not self.adj_only:
                    left = self.string_scout_left(start, begin)
                    if left != None:
                        right = self.string_scout_right(start + 1, end)
                        if right != None:
                            # Need to run plugin?
                            if (
                                self.transform['bracket'] and
                                self.plugin != None and
                                self.plugin.is_enabled()
                            ):
                                (b_region, c_region, regions) = self.plugin.run_command(
                                    sublime.Region(left, right + 1),
                                    sublime.Region(left + 1, right),
                                    regions,
                                    "bracket"
                                )
                                begin = b_region.a
                                end = b_region.b - 1
                            else:
                                # Copy range over
                                begin = left
                                end = right
                            # Highlighting
                            if self.brackets[self.bracket_type]['underline']:
                                self.highlight_us[self.bracket_type].append(sublime.Region(begin))
                                self.highlight_us[self.bracket_type].append(sublime.Region(end))
                            else:
                                self.highlight_us[self.bracket_type].append(sublime.Region(begin, begin + 1))
                                self.highlight_us[self.bracket_type].append(sublime.Region(end, end + 1))
                            # Line and char counts
                            if self.count_lines:
                                self.lines += self.view.rowcol(end)[0] - self.view.rowcol(begin)[0] + 1
                                self.chars += end - 1 - begin
                            # Don't highlight string quotes
                            suppress = True
                        elif self.ignore_string_bracket_parent or not_quoted:
                            matched = False
                    elif self.ignore_string_bracket_parent or not_quoted:
                        matched = False

            if not suppress:
                if (
                    self.transform['quote'] and
                    self.plugin != None and
                    self.plugin.is_enabled()
                ):
                    (b_region, c_region, regions) = self.plugin.run_command(
                        sublime.Region(begin, end),
                        sublime.Region(begin + 1, end - 1),
                        regions,
                        "string"
                    )
                    begin = b_region.a
                    end = b_region.b
                if self.brackets['bh_quote']['underline']:
                    self.highlight_us['bh_quote'].append(sublime.Region(begin))
                    self.highlight_us['bh_quote'].append(sublime.Region(end - 1))
                else:
                    self.highlight_us['bh_quote'].append(sublime.Region(begin, begin + 1))
                    self.highlight_us['bh_quote'].append(sublime.Region(end - 1, end))
                if self.count_lines:
                    self.lines += self.view.rowcol(end)[0] - self.view.rowcol(begin)[0] + 1
                    self.chars += end - 2 - begin

            self.store_sel(regions)
        return (matched, begin - 1)

    def check_special_strings_start(self, char, begin, view_size):
        quote = None
        pt = begin + 1
        if char == 'r':
            if self.view.score_selector(begin, 'source.python'):
                # Python raw string support
                if pt <= view_size:
                    char = self.view.substr(pt)
                    if char == "'" or char == '"':
                        begin += 1
                        quote = char
        else:
            quote = char
        return quote, begin

    def string_adjacent_adjust_inside(self, scout):
        # Offset cursor
        offset = 0
        self.adj_bracket = False
        char1 = self.view.substr(scout - 1)
        char1_escaped = self.string_escaped(scout - 1)
        char2 = self.view.substr(scout)
        char2_escaped = self.string_escaped(scout)
        for bracket in self.targets:
            if char2 == self.brackets[bracket]['close'] and not char2_escaped:
                offset = -1
                self.adj_bracket = True
                break
            if char2 == self.brackets[bracket]['open'] and not char2_escaped and offset != -1:
                offset = -1
            if char1 == self.brackets[bracket]['open'] and not char1_escaped:
                if offset != -1:
                    offset = -1
                self.adj_bracket = True
                break
        return offset

    def string_adjacent_adjust(self, scout):
        # Offset cursor
        offset = 0
        self.adj_bracket = False
        char1 = self.view.substr(scout - 1)
        char1_escaped = self.string_escaped(scout - 1)
        char2 = self.view.substr(scout)
        char2_escaped = self.string_escaped(scout)
        for bracket in self.targets:
            if bracket == "bh_angle":
                continue
            if char2 == self.brackets[bracket]['open'] and not char2_escaped:
                self.adj_bracket = True
            if char1 == self.brackets[bracket]['open'] and not char1_escaped:
                offset = -1
                self.adj_bracket = True
                break
            elif char1 == self.brackets[bracket]['close'] and not char1_escaped:
                offset = -2
                self.adj_bracket = True
            elif char2 == self.brackets[bracket]['close'] and not char2_escaped and offset != -2:
                offset = -1
                self.adj_bracket = True
        return offset

    def string_escaped(self, scout):
        escaped = False
        start = scout
        start -= 1
        first = False
        if self.view.settings().get('bracket_string_escape_mode', "regex") == "regex":
            first = True
        while self.view.substr(start) == "\\":
            if not first:
                first = True
            else:
                escaped = False if escaped else True
            start -= 1
        return escaped

    def string_scout_left(self, scout, limit):
        count = {}
        for bracket in self.targets:
            count[bracket] = 0

        while scout >= limit:
            if self.use_threshold:
                self.search_left -= 1
                if self.search_left < 0:
                    return None

            # Assign char.
            char = self.view.substr(scout)
            char_escaped = self.string_escaped(scout)
            # Hit brackets.
            foundBracket = False
            for bracket in self.targets:
                if bracket == "bh_angle":
                    continue
                if char == self.brackets[bracket]['open'] and not char_escaped:
                    if count[bracket] > 0:
                        count[bracket] -= 1
                        foundBracket = True
                        break
                    else:
                        self.bracket_type = bracket
                        self.bracket_open = self.brackets[bracket]['open']
                        self.bracket_close = self.brackets[bracket]['close']
                        return scout

            if foundBracket == False:
                for bracket in self.targets:
                    if bracket == "bh_angle":
                        continue
                    if char == self.brackets[bracket]['close'] and not char_escaped:
                        count[bracket] += 1
                        break
            scout -= 1
        return None

    def string_scout_right(self, scout, limit):
        brackets = 0

        while scout < limit:
            if self.use_threshold:
                self.search_left -= 1
                if self.search_left < 0:
                    return None

            # Assign char.
            char = self.view.substr(scout)
            char_escaped = self.string_escaped(scout)
            # Hit brackets.
            if char == self.bracket_close and not char_escaped:
                if brackets > 0:
                    brackets -= 1
                else:
                    return scout
            elif char == self.bracket_open and not char_escaped:
                brackets += 1
            scout += 1
        return None

bh_match = BracketHighlighter().match


class BracketHighlighterListenerCommand(sublime_plugin.EventListener):
    # Manage when to kick off bracket matching.
    # Try and reduce redundant requests by letting the
    # background thread ensure certain needed match occurs
    def on_load(self, view):
        if self.ignore_event(view):
            return
        Pref.type = BH_MATCH_TYPE_SELECTION
        sublime.set_timeout(lambda: bh_run(), 0)

    def on_modified(self, view):
        if self.ignore_event(view):
            return
        Pref.type = BH_MATCH_TYPE_EDIT
        Pref.modified = True
        Pref.time = time()

    def on_activated(self, view):
        if self.ignore_event(view):
            return
        Pref.type = BH_MATCH_TYPE_SELECTION
        sublime.set_timeout(lambda: bh_run(), 0)

    def on_selection_modified(self, view):
        if self.ignore_event(view):
            return
        if Pref.type != BH_MATCH_TYPE_EDIT:
            Pref.type = BH_MATCH_TYPE_SELECTION
        now = time()
        if now - Pref.time > Pref.wait_time:
            sublime.set_timeout(lambda: bh_run(), 0)
        else:
            Pref.modified = True
            Pref.time = now

    def ignore_event(self, view):
        return (view.settings().get('is_widget') or Pref.ignore_all)


# Kick off matching of brackets
def bh_run():
    Pref.modified = False
    window = sublime.active_window()
    view = window.active_view() if window != None else None
    Pref.ignore_all = True
    bh_match(view, True if Pref.type == BH_MATCH_TYPE_EDIT else False)
    Pref.ignore_all = False
    Pref.time = time()


# Start thread that will ensure highlighting happens after a barage of events
# Initial highlight is instant, but subsequent events in close succession will
# be ignored and then accounted for with one match by this thread
def bh_loop():
    while True:
        if Pref.modified == True and time() - Pref.time > Pref.wait_time:
            sublime.set_timeout(lambda: bh_run(), 0)
        sleep(0.5)

if not 'running_bh_loop' in globals():
    running_bh_loop = True
    thread.start_new_thread(bh_loop, ())
