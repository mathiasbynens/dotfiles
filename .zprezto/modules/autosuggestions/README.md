Autosuggestions
---------------

Integrates zsh-autosuggestions into Prezto.

Autosuggestions
===============

Integrates [zsh-autosuggestions][1] into Prezto, which implements the
[Fish shell][2]'s autosuggestions feature, where the user can type in any part
of a previously entered command and Zsh suggests commands as you type based on
history and completions.

If this module is used in conjuncture with the *syntax-highlighting* module, it
must be loaded **after** it.

If this module is used in conjuncture with the *history-substring-search*
module, it must be loaded **after** it.

Contributors
------------

New features and bug fixes should be submitted to the [zsh-autosuggestions][1]
project according to its rules and regulations. This module will be synchronized
against it.

Settings
--------

### Highlighting

If colors are enabled, *autosuggestions* will automatically highlight
positive results.

To enable highlighting for this module only, add the following line to
*zpreztorc*:

    zstyle ':prezto:module:autosuggestions' color 'yes'

To set the query found color, add the following line to *zpreztorc*:

    zstyle ':prezto:module:autosuggestions:color' found ''

Authors
-------

*The authors of this module should be contacted via the [issue tracker][3].*

  - [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: https://github.com/tarruda/zsh-autosuggestions
[2]: http://fishshell.com
[3]: https://github.com/sorin-ionescu/prezto/issues
