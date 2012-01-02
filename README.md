# Mathias’s dotfiles

## Installation

### Using Git and the bootstrap script

```bash
git clone https://github.com/mathiasbynens/dotfiles.git && cd dotfiles && ./bootstrap.sh
```

To update, `cd` into your local `dotfiles` repository and then:

```bash
./bootstrap.sh
```

Alternatively, to update while avoiding the confirmation prompt:

```bash
./bootstrap.sh -f
```

### Git-free install

To install these dotfiles without Git:

```bash
cd; curl -#L https://github.com/mathiasbynens/dotfiles/tarball/master | tar -xzv --strip-components 1 --exclude={README.md,bootstrap.sh}
```

To update later on, just run that command again.

### Sensible OS X defaults

When setting up a new Mac, you may want to set some sensible OS X defaults:

```bash
./.osx
```

## Feedback

Suggestions/improvements
[welcome](https://github.com/mathiasbynens/dotfiles/issues)!

## Thanks to…

* [Gianni Chiappetta](http://gf3.ca/) for sharing his [amazing collection of dotfiles](https://github.com/gf3/dotfiles)
* [Matijs Brinkhuis](http://hotfusion.nl/) and his [homedir repository](https://github.com/matijs/homedir)
* [Jan Moesen](http://jan.moesen.nu/) and his [ancient `.bash_profile`](https://gist.github.com/1156154) + [shiny tilde repository](https://github.com/janmoesen/tilde)
* [Ben Alman](http://benalman.com/) and his [dotfiles repository](https://github.com/cowboy/dotfiles)
* [Tim Esselens](http://devel.datif.be/)
* anyone who [contributed a patch](https://github.com/mathiasbynens/dotfiles/contributors) or [made a helpful suggestion](https://github.com/mathiasbynens/dotfiles/issues)