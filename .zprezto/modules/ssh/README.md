SSH
===

Provides for an easier use of [SSH][1] by setting up [ssh-agent][2].

This module is disabled on Mac OS X due to custom Apple SSH support rendering it
unnecessary. Use `ssh-add -K` to store identities in Keychain; they will be
added to `ssh-agent` automatically and persist between reboots.

Settings
--------

### Identities

To load multiple identities, add the following line to *zpreztorc*:

    zstyle ':prezto:module:ssh:load' identities 'id_rsa' 'id_dsa' 'id_github'

Authors
-------

*The authors of this module should be contacted via the [issue tracker][3].*

  - [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: http://www.openssh.com
[2]: http://www.openbsd.org/cgi-bin/man.cgi?query=ssh-agent&sektion=1
[3]: https://github.com/sorin-ionescu/prezto/issues
