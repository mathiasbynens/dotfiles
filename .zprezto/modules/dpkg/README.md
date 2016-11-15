Dpkg
====

Defines [dpkg][1] aliases and functions.

Aliases
-------

- `debc` cleans the cache.
- `debf` displays a file's package.
- `debi` installs packages from repositories.
- `debI` installs packages from files.
- `debq` displays package information.
- `debu` updates the package lists.
- `debU` upgrades outdated packages.
- `debx` removes packages.
- `debX` removes packages, their configuration, and unneeded dependencies.
- `debs` searches for packages.
- `deb-build` creates a basic deb package.
- `deb-kclean` removes all kernel images and headers, except for the ones in
  use.

Functions
---------

- `deb-clone` generates a script that can be used to duplicate a dpkg-based
  system.
- `deb-history` displays dpkg history.
- `deb-kbuild` makes a dpkg Linux kernel package.

Authors
-------

*The authors of this module should be contacted via the [issue tracker][2].*

  - [Daniel Bolton](https://github.com/dbb)
  - [Benjamin Boudreau](https://github.com/dreur)
  - [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: http://wiki.debian.org/Teams/Dpkg
[2]: https://github.com/sorin-ionescu/prezto/issues
