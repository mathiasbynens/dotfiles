Syntax Highlighting
===================

Integrates [zsh-syntax-highlighting][1] into Prezto.

This module should be loaded *second to last*, where last is the *prompt*
module, unless used in conjuncture with the *history-substring-search* module
where it must be loaded **before** it.

Contributors
------------

New features and bug fixes should be submitted to the
[zsh-syntax-highlighting][1] project according to its rules and regulations.
This module will be synchronized against it.

Settings
--------

### Highlighting

To enable highlighting for this module only, add the following line to
*zpreztorc*:

    zstyle ':prezto:module:syntax-highlighting' color 'yes'

### Highlighters

Syntax highlighting is accomplished by pluggable [highlighters][2]. This module
only enables the *main* highlighter by default.

To enable all highlighters, add the following to *zpreztorc*:

    zstyle ':prezto:module:syntax-highlighting' highlighters \
      'main' \
      'brackets' \
      'pattern' \
      'cursor' \
      'root'

### Highlighting Styles

Each syntax highlighter defines styles used to highlight tokens.

To highlight, for example, builtins, commands, and functions in blue instead of
green, add the following to *zpreztorc*:

    zstyle ':prezto:module:syntax-highlighting' styles \
      'builtin' 'bg=blue' \
      'command' 'bg=blue' \
      'function' 'bg=blue'

Authors
-------

*The authors of this module should be contacted via the [issue tracker][3].*

  - [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: https://github.com/zsh-users/zsh-syntax-highlighting
[2]: https://github.com/zsh-users/zsh-syntax-highlighting/tree/master/highlighters
[3]: https://github.com/sorin-ionescu/prezto/issues
