# Marcus’ OSX setup

## Installation

Download and bootstrap:

```bash
git clone https://github/mstade/dotfiles.git ~/dotfiles && cd ~/dotfiles && source bootstrap.sh
```

If setting up a machine for the first time, run this after the bootstrap:

```bash
setup/new-machine
```

Optionally install [Homebrew](http://brew.sh/) and some nice packages, by running:

```bash
setup/homebrew
```

Optionally setup Sublime Text, by running:
```bash
setup/sublime
```

Finally, remove `dotfiles` if it's no longer necessary. If you wish to update, just run `source bootstrap.sh` again at a later date.

## Thanks to…

Original author:

| [![twitter/mathias](http://gravatar.com/avatar/24e08a9ea84deb17ae121074d0f17125?s=70)](http://twitter.com/mathias "Follow @mathias on Twitter") |
|---|
| [Mathias Bynens](http://mathiasbynens.be/) |

Forked from [mathiasbynens/dotfiles](https://github.com/mathiasbynens/dotfiles).
