GNU Utility
===========

Provides for the interactive use of GNU utilities on BSD systems.

Installing GNU utilities on non-GNU systems in `$PATH` without a prefix, i.e.
`ls` instead of `gls`, is not recommended since scripts that target other
utilities will be broken.

This module wraps GNU utilities in functions without a prefix for interactive
use.

This module must be loaded **before** the *utility* module.

Settings
--------

### Prefix

To use a different prefix, add the following to *zpreztorc*, and replace 'g' with
the desired prefix:

    zstyle ':prezto:module:gnu-utility' prefix 'g'

Authors
-------

*The authors of this module should be contacted via the [issue tracker][1].*

  - [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: https://github.com/sorin-ionescu/prezto/issues
