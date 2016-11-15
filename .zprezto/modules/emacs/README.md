Emacs
=====

Enables Emacs dependency management.

Dependency management
---------------------

[Carton][1] installs and manages Emacs packages for Emacs package development
and Emacs configuration.

This module prepends the Carton directory to the path variable to enable the
execution of `carton`.

Aliases
-------

### Carton

  - `cai` installs dependencies.
  - `cau` updates dependencies.
  - `caI` initializes the current directory for dependency management.
  - `cae` executes a command which correct dependencies.

Authors
-------

*The authors of this module should be contacted via the [issue tracker][2].*

  - [Sebastian Wiesner](https://github.com/lunaryorn)

[1]: https://github.com/rejeep/carton
[2]: https://github.com/sorin-ionescu/prezto/issues
