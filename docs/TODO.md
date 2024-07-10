# On fresh install...

- Install Command Line Tools: `xcode-select --install`

- clone this project and run the bootstrap script

```bash
git clone https://github.com/haneen-ahemed/dotfiles.git && cd dotfiles && source bootstrap.sh
```

- Install [Homebrew](https://brew.sh) and run [brew.sh](https://github.com/haneen-ahemed/dotfiles/blob/master/.brew/brew.sh)

```bash
/usr/bin/ruby -e "$(curl -fsSL https:/raw.githubusercontent.com/Homebrew/install/master/install)"
&& cd dotfiles && source brew.sh
```


  - [create access token](https://github.com/settings/tokens/new)
  - Gist ID is `92968648b5ea54edbee216e87e52c15e`

- run `mackup` if you have used it to back up settings

- [set up ad-blocking](https://jspenguin2017.github.io/uBlockProtector/#extra-installation-steps-for-ublock-origin)

- [Add SSH keys to GitHub](https://github.com/settings/ssh) and [other](https://docs.gitlab.com/ee/gitlab-basics/create-your-ssh-keys.html) version control systems (also [GPG](https://gpgtools.org/))

* init [`spicetify`](https://github.com/khanhas/spicetify-cli/wiki/Basic-Usage)

# init

The init script will:

- Install NVM

  ```bash
  curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
  ```

- Install [Oh My Zsh](https://ohmyz.sh/)

  ```bash
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh)"
  ```

  - custom plugins
    - [zsh-nvm](https://github.com/lukechilds/zsh-nvm#as-an-oh-my-zsh-custom-plugin)

- Install Mac-CLI

  ```bash
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/guarinogabriel/mac-cli/master/mac-cli/tools/install)"
  ```

# Adding Apps, Aliases or Functions

To maintain the list of your installed apps, add them to their corresponding place in [`brew.sh`](https://github.com/haneen-ahemed/dotfiles/blob/master/.brew/brew.sh). Aliases and functions can be added to their respective files.
After changing any of these files, remember to run [`bootstrap.sh`](https://github.com/haneen-ahemed/dotfiles/blob/master/.setup/bootstrap.sh), which can be done most quickly with the alias [`sd`](https://github.com/haneen-ahemed/dotfiles/blob/43094a112e0fd11fbda5eff82b408f3071e2c976/.aliases#L17) (source dotfiles).

# Updating

The [`.aliases`](https://github.com/haneen-ahemed/dotfiles/blob/master/.aliases) include an `update` alias that will run all kinds of updaters. (even shorter: `ud`)
Alternative: [`mac update`](https://github.com/guarinogabriel/Mac-CLI#general-commands)

# Troubleshooting

- brew permissions broken

```
sudo chown -R $(whoami) $(brew --prefix)/*
```

- [SourceTree GPG signing](https://community.atlassian.com/t5/Sourcetree-questions/Why-is-quot-Enable-GPG-key-signing-for-commit-quot-is-greyed-out/qaq-p/249852)

```
// get current gpg version path
ls -la /usr/local/bin/gpg
// symlink gpg2
ln -s ../Cellar/gnupg/{version}/bin/gpg /usr/local/bin/gpg2
```

[<- Back](index.md)
