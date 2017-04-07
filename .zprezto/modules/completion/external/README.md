zsh-completions
===============

**Additional completion definitions for [Zsh](http://www.zsh.org).**

*This projects aims at gathering/developing new completion scripts that are not available in Zsh yet. The scripts are meant to be contributed to the Zsh project when stable enough.*


Status
------
See [issues](https://github.com/zsh-users/zsh-completions/issues) for details on each completion definition.

Gentoo's completions have been removed, as they are maintained upstream. See: [Gentoo zsh-completions](https://github.com/radhermit/gentoo-zsh-completions)

Usage
-----

#### Using packages

* Arch Linux: [community/zsh-completions](https://www.archlinux.org/packages/zsh-completions) / [AUR/zsh-completions-git](https://aur.archlinux.org/packages/zsh-completions-git/)
* [Gentoo](http://packages.gentoo.org/package/app-shells/zsh-completions)
* Mac OS: [Homebrew](https://github.com/mxcl/homebrew/blob/master/Library/Formula/zsh-completions.rb)
* Debian based distributions (Debian/Ubuntu/Linux Mint...): Packager needed, please get in touch !
* RPM based distributions (Fedora/RHEL/CentOS...): Packager needed, please get in touch !

#### Using frameworks

* If you're using [antigen](https://github.com/zsh-users/antigen), just add `antigen bundle zsh-users/zsh-completions src` to your .zshrc where you're loading your other zsh plugins.


#### Manual installation

* Clone the repository:

        git clone git://github.com/zsh-users/zsh-completions.git

* Include the directory in your `$fpath`, for example by adding in `~/.zshrc`:

        fpath=(path/to/zsh-completions/src $fpath)

* You may have to force rebuild `zcompdump`:

        rm -f ~/.zcompdump; compinit

#### oh-my-zsh

If you use [oh-my-zsh][] then just clone the repository inside your oh-my-zsh repo:

```Shell
git clone https://github.com/zsh-users/zsh-completions ~/.oh-my-zsh/custom/plugins/zsh-completions
```

and enable it in your `.zshrc`:

```zsh
plugins+=(zsh-completions)
autoload -U compinit && compinit
```

[oh-my-zsh]: http://github.com/robbyrussell/oh-my-zsh

Contributing
------------

Contributions are welcome, just make sure you follow the guidelines:

 * Completions are not accepted when already available in zsh.
 * Completions are not accepted when already available in their original project.
 * Please do not just copy/paste someone else completion, ask before.
 * Completions only partially implemented are not accepted.
 * Please add a header containing authors, license info, status and origin of the script (example [here](src/_ack)).
 * Please try to follow [Zsh completion style guide](https://github.com/zsh-users/zsh/blob/master/Etc/completion-style-guide).
 * Please send one separate pull request per file.
 * Send a pull request or ask for committer access.


License
-------
See each file for license details.
