# Paul's dotfiles.. a fork of mathias's..

[mathias's readme](https://github.com/mathiasbynens/dotfiles/) is awesome. go read it.

## Installation

### Using Git and the bootstrap script

```bash
git clone https://github.com/paulirish/dotfiles.git && cd dotfiles && ./sync.sh
```

To update later on, just run the sync again.


### private config

Toss it into a file called `.extra` which you do not commit to this repo and just keep in your `~/`

I do something nice with my `PATH` there:

```shell
# PATH like a bawss
      PATH=/opt/local/bin
PATH=$PATH:/opt/local/sbin
PATH=$PATH:/bin
PATH=$PATH:~/.rvm/bin
PATH=$PATH:~/code/git-friendly
# ...

export PATH
```



### Sensible OS X defaults

When setting up a new Mac, you may want to set some sensible OS X defaults:

```bash
./.osx
```

## upstream

Suggestions/improvements [welcome back upstream](https://github.com/mathiasbynens/dotfiles/issues)!
