#!/usr/bin/env python3

color_groups = [
    [('red', None), ('green', None), ('yellow', None), ('magenta', None),
     ('cyan', None)],
    [('black', 'light_red'), ('black', 'light_green'),
     ('black', 'light_yellow'), ('black', 'light_magenta'),
     ('black', 'light_cyan')]
]
cmd = ['git', 'blame', '--line-porcelain']


###############################################
# START Base16 Tomorrow Dark style for Pygments
###############################################
# https://github.com/idleberg/base16-pygments/blob/master/base16-tomorrow.dark.py

from pygments.style import Style
from pygments.token import Keyword, Name, Comment, String, Error, Text, \
     Number, Operator, Generic, Whitespace, Punctuation, Other, Literal


BACKGROUND = "#1d1f21"
CURRENT_LINE = "#282a2e"
SELECTION = "#373b41"
FOREGROUND = "#ffffff"
COMMENT = "#969896"
RED = "#cc6666"
ORANGE = "#de935f"
YELLOW = "#f0c674"
GREEN = "#b5bd68"
AQUA = "#8abeb7"
BLUE = "#81a2be"
PURPLE = "#b294bb"


class base16_tomorrow_dark(Style):

    default_style = ''

    background_color = BACKGROUND
    highlight_color = SELECTION

    background_color = BACKGROUND
    highlight_color = SELECTION

    styles = {
        # No corresponding class for the following:
        Text:                      FOREGROUND,  # class:  ''
        Whitespace:                "",          # class: 'w'
        Error:                     RED,         # class: 'err'
        Other:                     "",          # class 'x'

        Comment:                   COMMENT,   # class: 'c'
        Comment.Multiline:         "",        # class: 'cm'
        Comment.Preproc:           "",        # class: 'cp'
        Comment.Single:            "",        # class: 'c1'
        Comment.Special:           "",        # class: 'cs'

        Keyword:                   PURPLE,    # class: 'k'
        Keyword.Constant:          "",        # class: 'kc'
        Keyword.Declaration:       "",        # class: 'kd'
        Keyword.Namespace:         AQUA,      # class: 'kn'
        Keyword.Pseudo:            "",        # class: 'kp'
        Keyword.Reserved:          "",        # class: 'kr'
        Keyword.Type:              YELLOW,    # class: 'kt'

        Operator:                  AQUA,      # class: 'o'
        Operator.Word:             "",        # class: 'ow' - like keywords

        Punctuation:               FOREGROUND,  # class: 'p'

        Name:                      FOREGROUND,  # class: 'n'
        Name.Attribute:            BLUE,        # class: 'na' - to be revised
        Name.Builtin:              "",          # class: 'nb'
        Name.Builtin.Pseudo:       "",          # class: 'bp'
        Name.Class:                YELLOW,      # class: 'nc' - to be revised
        Name.Constant:             RED,         # class: 'no' - to be revised
        Name.Decorator:            AQUA,        # class: 'nd' - to be revised
        Name.Entity:               "",          # class: 'ni'
        Name.Exception:            RED,         # class: 'ne'
        Name.Function:             BLUE,        # class: 'nf'
        Name.Property:             "",          # class: 'py'
        Name.Label:                "",          # class: 'nl'
        Name.Namespace:            YELLOW,      # class: 'nn' - to be revised
        Name.Other:                BLUE,        # class: 'nx'
        Name.Tag:                  AQUA,        # class: 'nt' - like a keyword
        Name.Variable:             RED,         # class: 'nv' - to be revised
        Name.Variable.Class:       "",          # class: 'vc' - to be revised
        Name.Variable.Global:      "",          # class: 'vg' - to be revised
        Name.Variable.Instance:    "",          # class: 'vi' - to be revised

        Number:                    ORANGE,    # class: 'm'
        Number.Float:              "",        # class: 'mf'
        Number.Hex:                "",        # class: 'mh'
        Number.Integer:            "",        # class: 'mi'
        Number.Integer.Long:       "",        # class: 'il'
        Number.Oct:                "",        # class: 'mo'

        Literal:                   ORANGE,    # class: 'l'
        Literal.Date:              GREEN,     # class: 'ld'

        String:                    GREEN,       # class: 's'
        String.Backtick:           "",          # class: 'sb'
        String.Char:               FOREGROUND,  # class: 'sc'
        String.Doc:                COMMENT,     # class: 'sd' - like a comment
        String.Double:             "",          # class: 's2'
        String.Escape:             ORANGE,      # class: 'se'
        String.Heredoc:            "",          # class: 'sh'
        String.Interpol:           ORANGE,      # class: 'si'
        String.Other:              "",          # class: 'sx'
        String.Regex:              "",          # class: 'sr'
        String.Single:             "",          # class: 's1'
        String.Symbol:             "",          # class: 'ss'

        Generic:                   "",                    # class: 'g'
        Generic.Deleted:           RED,                   # class: 'gd',
        Generic.Emph:              "italic",              # class: 'ge'
        Generic.Error:             "",                    # class: 'gr'
        Generic.Heading:           "bold " + FOREGROUND,  # class: 'gh'
        Generic.Inserted:          GREEN,                 # class: 'gi'
        Generic.Output:            "",                    # class: 'go'
        Generic.Prompt:            "bold " + COMMENT,     # class: 'gp'
        Generic.Strong:            "bold",                # class: 'gs'
        Generic.Subheading:        "bold " + AQUA,        # class: 'gu'
        Generic.Traceback:         "",                    # class: 'gt'
    }

#############################################
# END Base16 Tomorrow Dark style for Pygments
#############################################


from pygments import highlight
from pygments.lexers import guess_lexer
from pygments.formatters import Terminal256Formatter
from tabulate import tabulate
from colored import fg, bg, attr

import subprocess
from sys import argv


def lines_starting_with(all_lines, prefix):
    grepped = [l for l in all_lines if l.startswith(prefix)]
    stripped = [l.split(prefix)[1] for l in grepped]
    return stripped


def main():
    cmd.extend(argv[1:])

    gbl_raw = (subprocess.run(cmd, stdout=subprocess.PIPE).stdout
               .decode().split('\n'))
    code = '\n'.join(lines_starting_with(gbl_raw, '\t'))
    authors_by_line = lines_starting_with(gbl_raw, 'author ')
    authors_unique = sorted(list(set(authors_by_line)))

    formatter = Terminal256Formatter(style=base16_tomorrow_dark)
    highlighted_raw = highlight(code, guess_lexer(code), formatter)
    highlighted = highlighted_raw.split('\n')

    color_codes = []
    for group in color_groups:
        for fg_color, bg_color in group:
            color_code = fg(fg_color)
            if bg_color:
                color_code += bg(bg_color)
            color_codes.append(color_code)

    author_color_codes = {author: color_codes.pop(0)
                          for author in authors_unique}

    pretty_blame = []
    for i in range(min(len(authors_by_line), len(highlighted))):
        author = authors_by_line[i]
        pretty_blame.append((
            author_color_codes[author] + author,
            fg('dark_gray') + str(i),
            attr('reset') + highlighted[i]
        ))

    print(tabulate(pretty_blame, tablefmt='plain'))


if __name__ == '__main__':
    main()
