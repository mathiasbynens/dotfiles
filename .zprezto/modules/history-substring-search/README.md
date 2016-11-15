History Substring Search
========================

Integrates [zsh-history-substring-search][1] into Prezto, which implements
the [Fish shell][2]'s history search feature, where the user can type in any
part of a previously entered command and press up and down to cycle through
matching commands.

If this module is used in conjuncture with the *syntax-highlighting* module, it
must be loaded **after** it.

Contributors
------------

New features and bug fixes should be submitted to the
[zsh-history-substring-search][1] project according to its rules and
regulations. This module will be synchronized against it.

Settings
--------

### Case Sensitivity

To enable case-sensitivity for this module only, add the following line to
*zpreztorc*:

    zstyle ':prezto:module:history-substring-search' case-sensitive 'yes'

### Highlighting

If colors are enabled, *history-substring-search* will automatically highlight
positive results.

To enable highlighting for this module only, add the following line to
*zpreztorc*:

    zstyle ':prezto:module:history-substring-search' color 'yes'

To set the query found color, add the following line to *zpreztorc*:

    zstyle ':prezto:module:history-substring-search:color' found ''

To set the query not found color, add the following line to *zpreztorc*:

    zstyle ':prezto:module:history-substring-search:color' not-found ''

To set the search globbing flags, add the following line to *zpreztorc*:

    zstyle ':prezto:module:history-substring-search' globbing-flags ''

Authors
-------

*The authors of this module should be contacted via the [issue tracker][3].*

  - [Suraj N. Kurapati](https://github.com/sunaku)
  - [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: https://github.com/zsh-users/zsh-history-substring-search
[2]: http://fishshell.com
[3]: https://github.com/sorin-ionescu/prezto/issues
