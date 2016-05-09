# Dougie’s dotfiles

This is a fork of Mathias [dotfiles] (https://github.com/mathiasbynens/dotfiles)

![Screenshot of my shell prompt](http://s32.postimg.org/u5j7aop6t/dougie_shell.png)

## Installation

**Warning:** If you want to give these dotfiles a try, you should first fork this repository, review the code, and remove things you don’t want or need. Don’t blindly use my settings unless you know what that entails. Use at your own risk!

### Using Git and the bootstrap script

You can clone the repository wherever you want. (I like to keep it in `~/.dotfiles`) The bootstrapper script will pull in the latest version and copy the files to your home folder.

```bash
git clone https://github.com/dmorand17/dotfiles.git && cd dotfiles && source bootstrap.sh
```

To update, `cd` into your local `dotfiles` repository and then:

```bash
source bootstrap.sh
```

Alternatively, to update while avoiding the confirmation prompt:

```bash
set -- -f; source bootstrap.sh
```

### Git-free install

To install these dotfiles without Git:

```bash
cd; curl -#L https://github.com/dmorand17/dotfiles/tarball/master | tar -xzv --strip-components 1 --exclude={README.md,bootstrap.sh,LICENSE-MIT.txt}
```

To update later on, just run that command again.

### Specify the `$PATH`

If `~/.path` exists, it will be sourced along with the other files, before any feature testing (such as [detecting which version of `ls` is being used](https://github.com/mathiasbynens/dotfiles/blob/aff769fd75225d8f2e481185a71d5e05b76002dc/.aliases#L21-26)) takes place.

Here’s an example `~/.path` file that adds `/usr/local/bin` to the `$PATH`:

```bash
export PATH="/usr/local/bin:$PATH"
```

### Add custom commands without creating a new fork

If `~/.extra` exists, it will be sourced along with the other files. You can use this to add a few custom commands without the need to fork this entire repository, or to add commands you don’t want to commit to a public repository.

My `~/.extra` looks something like this:

```bash
# Git credentials
# Not in the repository, to prevent people from accidentally committing under my name
# Git credentials 
# Not in the repository, to prevent people from accidentally committing under my name 
GIT_AUTHOR_NAME="Douglas Morand" 
GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME" 
git config --global user.name "$GIT_AUTHOR_NAME" 
GIT_AUTHOR_EMAIL="douglas.morand@orionhealth.com" 
GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL" 
git config --global user.email "$GIT_AUTHOR_EMAIL
```

You could also use `~/.extra` to override settings, functions and aliases from my dotfiles repository. It’s probably better to [fork this repository](https://github.com/dmorand17/dotfiles/fork) instead, though.

### Sensible OS X defaults

When setting up a new Mac, you may want to set some sensible OS X defaults:

```bash
./.osx
```

## Feedback

Suggestions/improvements
[welcome](https://github.com/dmorand17/dotfiles/issues)!

## Acknowledgements

* [Mathias Bynens](https://mathiasbynens.be/) and this [dotfiles repository](https://github.com/mathiasbynens/dotfiles)
* Solarized [color theme] (http://ethanschoonover.com/solarized)
* Solarized [directory colors] (https://github.com/seebi/dircolors-solarized)
