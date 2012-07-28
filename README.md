# Roderik's dotfiles

This is a fork of Mathias’s dotfiles customised for my use.

## Installation

### Using Git and the bootstrap script

You can clone the repository wherever you want. (I like to keep it in `~/Projects/dotfiles`, with `~/dotfiles` as a symlink.) The bootstrapper script will pull in the latest version and copy the files to your home folder.

```bash
git clone https://github.com/roderik/dotfiles.git && cd dotfiles && ./bootstrap.sh
```

To update, `cd` into your local `dotfiles` repository and then:

```bash
./bootstrap.sh
```

Alternatively, to update while avoiding the confirmation prompt:

```bash
./bootstrap.sh -f
```

### Sensible OS X defaults

When setting up a new Mac, you may want to set some sensible OS X defaults:

```bash
./.osx
```

## More help

Check out [this blog post about my development environment](http://vanderveer.be/blog/2012/04/21/setting-up-my-perfect-developer-environment-on-osx-10-dot-8-mountain-lion-dp3-edition/) where i detail how i use this repo.