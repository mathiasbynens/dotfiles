Configuration Files
===================

Zsh has several system-wide and user-local configuration files.

Prezto has one user-local configuration file.

System-wide configuration files are installation-dependent but are installed
in */etc* by default.

User-local configuration files have the same name as their global counterparts
but are prefixed with a dot (hidden). Zsh looks for these files in the path
stored in the `$ZDOTDIR` environmental variable. However, if said variable is
not defined, Zsh will use the user's home directory.

File Descriptions
-----------------

The configuration files are read in the following order:

  01. /etc/zshenv
  02. ~/.zshenv
  03. /etc/zprofile
  04. ~/.zprofile
  05. /etc/zshrc
  06. ~/.zshrc
  07. ~/.zpreztorc
  08. /etc/zlogin
  09. ~/.zlogin
  10. ~/.zlogout
  11. /etc/zlogout

### zshenv

This file is sourced by all instances of Zsh, and thus, it should be kept as
small as possible and should only define environment variables.

### zprofile

This file is similar to zlogin, but it is sourced before zshrc. It was added
for [KornShell][1] fans. See the description of zlogin below for what it may
contain.

zprofile and zlogin are not meant to be used concurrently but can be done so.

### zshrc

This file is sourced by interactive shells. It should define aliases,
functions, shell options, and key bindings.

### zpreztorc

This file configures Prezto.

### zlogin

This file is sourced by login shells after zshrc, and thus, it should contain
commands that need to execute at login. It is usually used for messages such as
[fortune][2], [msgs][3], or for the creation of files.

This is not the file to define aliases, functions, shell options, and key
bindings. It should not change the shell environment.

### zlogout

This file is sourced by login shells during logout. It should be used for
displaying messages and the deletion of files.

Authors
-------

*The authors of these files should be contacted via the [issue tracker][4].*

  - [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: http://www.kornshell.com
[2]: http://en.wikipedia.org/wiki/Fortune_(Unix)
[3]: http://www.manpagez.com/man/1/msgs
[4]: https://github.com/sorin-ionescu/prezto/issues
