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

start_tag = r'<([\w\:\-]+)((?:\s+[\w\-:]+(?:\s*=\s*(?:(?:"[^"]*")|(?:\'[^\']*\')|[^>\s]+))?)*)\s*(\/?)>'
end_tag = r'<\/([\w\:\-]+)[^>]*>'
attr = r'([\w\-:]+)(?:\s*=\s*(?:(?:"((?:\\.|[^"])*)")|(?:\'((?:\\.|[^\'])*)\')|([^>\s]+)))?'

"Last matched HTML pair"
last_match = {
    'opening_tag': None,  # Tag() or Comment() object
    'closing_tag': None,  # Tag() or Comment() object
    'start_ix': -1,
    'end_ix': -1
}

cur_mode = 'xhtml'
"Current matching mode"


def set_mode(new_mode):
    global cur_mode
    if new_mode != 'html':
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
            (name in empty and cur_mode == 'html')
        )
        self.type = 'tag'
        self.close_self = (name in close_self and cur_mode == 'html')


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


def match(html, start_ix, mode='xhtml', use_threshold=True, search_thresh=2000):
    """
    Search for matching tags in <code>html</code>, starting from
    <code>start_ix</code> position. The result is automatically saved
    in <code>last_match</code> property
    """
    return _find_pair(html, start_ix, use_threshold, search_thresh, mode, save_match)


def find(html, start_ix, mode='xhtml', use_threshold=True, search_thresh=2000):
    """
    Search for matching tags in <code>html</code>, starting from
    <code>start_ix</code> position.
    """
    return _find_pair(html, start_ix, use_threshold, search_thresh, mode)


def get_tags(html, start_ix, mode='xhtml', use_threshold=True, search_thresh=2000):
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
        use_threshold,
        search_thresh, mode,
        lambda op, cl=None, ix=0: (op, cl) if op and op.type == 'tag' else None
    )


def is_tag(substr):
    return (re.match(start_tag, substr) or re.match(end_tag, substr))


def _find_pair(html, start_ix, use_threshold, search_threshold, mode='xhtml', action=make_range):
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

    set_mode(mode)

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
                m = re.match(start_tag, check_str)
                if m:  # found opening tag
                    tmp_tag = Tag(m, ix)
                    if tmp_tag.unary:
                        if (  # exact match
                            tmp_tag.start < start_ix and
                            tmp_tag.end > start_ix
                        ):
                            return action(tmp_tag, None, start_ix)
                    elif (
                        backward_stack and
                        backward_stack[-1].name == tmp_tag.name
                    ):
                        backward_stack.pop()
                    else:  # found nearest unclosed tag
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
                    return action(None)
            ch = html[ix]
            if ch == '<':
                check_str = html[ix:]
                m = re.match(start_tag, check_str)
                if m:  # found opening tag
                    tmp_tag = Tag(m, ix)
                    if not tmp_tag.unary:
                        forward_stack.append(tmp_tag)
                else:
                    m = re.match(end_tag, check_str)
                    if m:  # found closing tag
                        tmp_tag = Tag(m, ix)
                        if (
                            forward_stack and
                            forward_stack[-1].name == tmp_tag.name
                        ):
                            forward_stack.pop()
                        else:  # found matched closing tag
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
        return action(None)
    return action(opening_tag, closing_tag, start_ix)
