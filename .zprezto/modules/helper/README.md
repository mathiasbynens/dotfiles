Helper
======

Provides helper functions for developing modules.

Functions
---------

  - `add-zsh-trap` adds a function name to a list to be called when a trap is
    triggered.
  - `is-autoloadable` checks if a file can be autoloaded by trying to load it
    in a subshell.
  - `is-callable` checks if a name is a command, function, or alias.
  - `is-true` checks a boolean variable for "true".
  - `coalesce` prints the first non-empty string in the arguments array.

Authors
-------

*The authors of this module should be contacted via the [issue tracker][1].*

  - [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: https://github.com/sorin-ionescu/prezto/issues
