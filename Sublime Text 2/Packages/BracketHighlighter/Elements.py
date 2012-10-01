#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Context-independent xHTML pair matcher
Use method <code>match(html, start_ix)</code> to find matching pair.
If pair was found, this function returns a list of indexes where tag pair
starts and ends. If pair wasn't found, <code>None</code> will be returned.

The last matched (or unmatched) result is saved in <code>last_match</code>
dictionary for later use.

@author: Sergey Chikuyonok (serge.che@gmail.com)
'''
import re

html_start_tag = [r'<([\w\:\-]+)((?:\s+[\w\-:]+(?:\s*=\s*(?:(?:"[^"]*")|(?:\'[^\']*\')|[^>\s]+))?)*)\s*(\/?)>']
cf_start_tag = [
    r'<([\w\:\-]+)((?:\s+[\w\-\.:]+(?:\s*=\s*(?:(?:"[^"]*")|(?:\'[^\']*\')|[^>\s]+))?)*)\s*(\/?)>',
    r'(?i)<(cfif|cfelseif)((?:[^>]+))\s*(\/?)>'
]
start_tag = html_start_tag
end_tag = r'<\/([\w\:\-]+)[^>]*>'
attr = r'([\w\-:]+)(?:\s*=\s*(?:(?:"((?:\\.|[^"])*)")|(?:\'((?:\\.|[^\'])*)\')|([^>\s]+)))?'

"Last matched HTML pair"
last_match = {
    'opening_tag': None,  # Tag() or Comment() object
    'closing_tag': None,  # Tag() or Comment() object
    'start_ix': -1,
    'end_ix': -1
}

"Current matching mode"
cur_mode = 'xhtml'
detect_self_closing = False


def set_mode(new_mode, find_self_closing=False):
    global cur_mode
    global start_tag
    global detect_self_closing
    detect_self_closing = bool(find_self_closing)
    start_tag = cf_start_tag if new_mode == 'cfml' else html_start_tag
    if new_mode not in ['html', 'cfml']:
        new_mode = 'xhtml'
    cur_mode = new_mode


def make_map(elems):
    """
    Create dictionary of elements for faster searching
    @param elems: Elements, separated by comma
    @type elems: str
    """
    obj = {}
    for elem in elems.split(','):
            obj[elem] = True

    return obj


# Empty Elements - HTML 4.01
empty = make_map("area,base,basefont,br,col,frame,hr,img,input,isindex,link,meta,param,embed")

# Block Elements - HTML 4.01
block = make_map("address,applet,blockquote,button,center,dd,dir,div,dl,dt,fieldset,form,frameset,hr,iframe,isindex,li,map,menu,noframes,noscript,object,ol,p,pre,script,table,tbody,td,tfoot,th,thead,tr,ul")

# Inline Elements - HTML 4.01
inline = make_map("a,abbr,acronym,applet,b,basefont,bdo,big,br,button,cite,code,del,dfn,em,font,i,iframe,img,input,ins,kbd,label,map,object,q,s,samp,select,small,span,strike,strong,sub,sup,textarea,tt,u,var")

# Elements that you can, intentionally, leave open
# (and which close themselves)
close_self = make_map("colgroup,dd,dt,li,options,p,td,tfoot,th,thead,tr")

# Attributes that have their values filled in disabled="disabled"
fill_attrs = make_map("checked,compact,declare,defer,disabled,ismap,multiple,nohref,noresize,noshade,nowrap,readonly,selected")

#Special Elements (can contain anything)
# serge.che: parsing data inside <scipt> elements is a "feature"
special = make_map("style")


class Tag():
    """Matched tag"""
    def __init__(self, match, ix):
        """
        @type match: MatchObject
        @param match: Matched HTML tag
        @type ix: int
        @param ix: Tag's position
        """
        global cur_mode

        name = match.group(1).lower()
        self.name = name
        self.full_tag = match.group(0)
        self.start = ix
        self.end = ix + len(self.full_tag)

        self.unary = (
            (len(match.groups()) > 2 and bool(match.group(3))) or
            (name in empty and (cur_mode in ['html', 'cfml']))
        )
        self.type = 'tag'
        self.close_self = (
            (
                (name in close_self and cur_mode == 'html') or
                (name.lower().startswith("cf") and cur_mode == 'cfml')
            ) and
            detect_self_closing
        )


class Comment():
    "Matched comment"
    def __init__(self, start, end):
        self.start = start
        self.end = end
        self.type = 'comment'


def make_range(opening_tag=None, closing_tag=None, ix=0):
    """
    Makes selection ranges for matched tag pair
    @type opening_tag: Tag
    @type closing_tag: Tag
    @type ix: int
    @return list
    """
    start_ix, end_ix = -1, -1

    if opening_tag and not closing_tag:  # unary element
        start_ix = opening_tag.start
        end_ix = opening_tag.end
    elif opening_tag and closing_tag:  # complete element
        if (
            (opening_tag.start < ix and opening_tag.end > ix) or
            (closing_tag.start <= ix and closing_tag.end > ix)
        ):
            start_ix = opening_tag.start
            end_ix = closing_tag.end
        else:
            start_ix = opening_tag.end
            end_ix = closing_tag.start
    return start_ix, end_ix


def save_match(opening_tag=None, closing_tag=None, ix=0):
    """
    Save matched tag for later use and return found indexes
    @type opening_tag: Tag
    @type closing_tag: Tag
    @type ix: int
    @return list
    """
    last_match['opening_tag'] = opening_tag
    last_match['closing_tag'] = closing_tag

    (last_match['start_ix'], last_match['end_ix']) = make_range(opening_tag, closing_tag, ix)

    return (
        last_match['start_ix'] != -1 and
        (last_match['start_ix'], last_match['end_ix']) or
        (None, None)
    )


def match(html, start_ix, mode='xhtml', find_self_closing=False, use_threshold=True, search_thresh=2000):
    """
    Search for matching tags in <code>html</code>, starting from
    <code>start_ix</code> position. The result is automatically saved
    in <code>last_match</code> property
    """
    return _find_pair(html, start_ix, find_self_closing, use_threshold, search_thresh, mode, save_match)


def find(html, start_ix, mode='xhtml', find_self_closing=False, use_threshold=True, search_thresh=2000):
    """
    Search for matching tags in <code>html</code>, starting from
    <code>start_ix</code> position.
    """
    return _find_pair(html, start_ix, find_self_closing, use_threshold, search_thresh, mode)


def get_tags(html, start_ix, mode='xhtml', find_self_closing=False, use_threshold=True, search_thresh=2000):
    """
    Search for matching tags in <code>html</code>, starting from
    <code>start_ix</code> position. The difference between
    <code>match</code> function itself is that <code>get_tags</code>
    method doesn't save matched result in <code>last_match</code> property
    and returns array of opening and closing tags
    This method is generally used for lookups
    """
    return _find_pair(
        html,
        start_ix,
        find_self_closing,
        use_threshold,
        search_thresh, mode,
        lambda op, cl=None, ix=0: (op, cl) if op and op.type == 'tag' else None
    )


def is_tag(substr, cf_enable=False):
    found_tag = False
    patterns = cf_start_tag if cf_enable else html_start_tag
    for pattern in patterns:
        found_tag |= bool(re.match(pattern, substr) or re.match(end_tag, substr))
    return found_tag


def _find_pair(html, start_ix, find_self_closing, use_threshold, search_threshold, mode='xhtml', action=make_range):
    """
    Search for matching tags in <code>html</code>, starting from
    <code>start_ix</code> position

    @param html: Code to search
    @type html: str

    @param start_ix: Character index where to start searching pair
    (commonly, current caret position)
    @type start_ix: int

    @param action: Function that creates selection range
    @type action: function

    @return: list
    """

    forward_stack = []
    backward_stack = []
    opening_name = None
    closing_name = None
    opening_tag = None
    closing_tag = None
    html_len = len(html)

    set_mode(mode, find_self_closing)

    def has_match(substr, start=None):
        if start is None:
            start = ix

        return html.find(substr, start) == start

    def find_comment_start(start_pos):
        while start_pos:
            if html[start_pos] == '<' and has_match('<!--', start_pos):
                break

            start_pos -= 1

        return start_pos

#    find opening tag
    ix = start_ix - 1
    while ix >= 0:
        if (use_threshold == True):
            search_threshold -= 1
            if(search_threshold < 0):
                return action(None)
        ch = html[ix]
        if ch == '<':
            check_str = html[ix:]
            m = re.match(end_tag, check_str)
            if m:  # found closing tag
                tmp_tag = Tag(m, ix)
                if (  # direct hit on searched closing tag
                    tmp_tag.start < start_ix and
                    tmp_tag.end > start_ix
                ):
                    closing_tag = tmp_tag
                    closing_name = tmp_tag.name
                else:
                    backward_stack.append(tmp_tag)
            else:
                for pattern in start_tag:
                    m = re.match(pattern, check_str)
                    if m:
                        break
                if m:  # found opening tag
                    tmp_tag = Tag(m, ix)
                    if tmp_tag.unary:
                        if (  # exact match
                            tmp_tag.start < start_ix and
                            tmp_tag.end > start_ix
                        ):
                            return action(tmp_tag, None, start_ix)
                    elif (  # Match sub tag
                        backward_stack and
                        backward_stack[-1].name == tmp_tag.name
                    ):
                        backward_stack.pop()
                    elif (  # Pass over self-closing tag
                        tmp_tag.close_self and
                        closing_tag and
                        closing_name != tmp_tag.name
                    ):
                        pass
                    elif len(backward_stack) == 0:  # found nearest unclosed tag
                        opening_tag = tmp_tag
                        opening_name = tmp_tag.name
                        break
                elif check_str.startswith('<!--'):  # found comment start
                    end_ix = check_str.find('-->') + ix + 3
                    if ix < start_ix and end_ix >= start_ix:
                        return action(Comment(ix, end_ix))
        elif ch == '-' and has_match('-->'):  # found comment end
            # search left until comment start is reached
            ix = find_comment_start(ix)

        ix -= 1

    if not opening_tag:
        return action(None)

    # find closing tag
    if not closing_tag:
        ix = start_ix
        while ix < html_len:
            if (use_threshold == True):
                search_threshold -= 1
                if(search_threshold < 0):
                    if opening_tag.close_self:
                        return action(opening_tag, None, start_ix)
                    else:
                        return action(None)
            ch = html[ix]
            if ch == '<':
                check_str = html[ix:]
                for pattern in start_tag:
                    m = re.match(pattern, check_str)
                    if m:
                        break
                if m:  # found opening tag
                    tmp_tag = Tag(m, ix)
                    if not tmp_tag.unary:
                        forward_stack.append(tmp_tag)
                else:
                    m = re.match(end_tag, check_str)
                    if m:  # found closing tag
                        tmp_tag = Tag(m, ix)
                        # Navigate stack to match the sub tag
                        # and/or remove sub tags that are optionally self-closing.
                        if forward_stack:
                            if forward_stack[-1].name == tmp_tag.name:
                                # Normal tag match
                                forward_stack.pop()
                            else:
                                # Stack probably has self closing tags in on top
                                # Pop off tags that are self-closing (assume they weren't matched)
                                found_in_stack = False
                                while forward_stack and forward_stack[-1].close_self:
                                    forward_stack.pop()
                                    # Check if the the next element matches the sub tag
                                    if forward_stack and forward_stack[-1].name == tmp_tag.name:
                                        # Found match, no need to look further in the stack
                                        forward_stack.pop()
                                        found_in_stack = True
                                        break
                                # If no match was found, and the stack is empty,
                                # it can be assumed that this tag is the main match
                                if not found_in_stack and len(forward_stack) == 0:
                                    closing_tag = tmp_tag
                                    closing_name = tmp_tag.name
                                    break
                        elif len(forward_stack) == 0:  # found matched closing tag
                            closing_tag = tmp_tag
                            closing_name = tmp_tag.name
                            break
                    elif has_match('<!--'):  # found comment
                        ix += check_str.find('-->') + 2
                        continue
            elif ch == '-' and has_match('-->'):
                # looks like cursor was inside comment with invalid HTML
                if not forward_stack or forward_stack[-1].type != 'comment':
                    end_ix = ix + 3
                    return action(Comment(find_comment_start(ix), end_ix))

            ix += 1
    if(opening_name != closing_name):
        if opening_tag.close_self:
            return action(opening_tag, None, start_ix)
        else:
            return action(None)
    return action(opening_tag, closing_tag, start_ix)
