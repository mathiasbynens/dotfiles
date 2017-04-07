GPG
===

Provides for an easier use of [GPG][1] by setting up [gpg-agent][2].

### SSH

To enable OpenSSH Agent protocol emulation, and make `gpg-agent` a drop-in
replacement for `ssh-agent`, add the following line to
*~/.gnupg/gpg-agent.conf*:

    enable-ssh-support

When OpenSSH Agent protocol emulation is enabled, this module will load the SSH
module for additional processing.

Authors
-------

*The authors of this module should be contacted via the [issue tracker][3].*

  - [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: http://www.gnupg.org
[2]: http://linux.die.net/man/1/gpg-agent
[3]: https://github.com/sorin-ionescu/prezto/issues
