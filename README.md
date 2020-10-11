# dotfiles

## Installation


## Updates

## Linking Files

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
# Git credentials
# Not in the repository, to prevent people from accidentally committing under my name
# Git credentials 
# Not in the repository, to prevent people from accidentally committing under my name 
GIT_AUTHOR_NAME="John Doe"
GIT_COMMITTER_NAME="$GIT_AUTHOR_NAME" 
git config --global user.name "$GIT_AUTHOR_NAME" 
GIT_AUTHOR_EMAIL="user@example.com"
GIT_COMMITTER_EMAIL="$GIT_AUTHOR_EMAIL" 
git config --global user.email "$GIT_AUTHOR_EMAIL
```
## Applications Bootstrapped
* [fzf|https://github.com/junegunn/fzf] command-line fuzzy finder
* [bat|https://github.com/sharkdp/bat] `cat` clone with syntax highlighting

### `zsh` bootstrapped
* [oh-my-zsh|https://ohmyz.sh/] zsh framework
* [antigen|https://github.com/zsh-users/antigen] zsh plugin manager

#### plugins
* [zsh-autosuggestions|https://github.com/zsh-users/zsh-autosuggestions.git]
* [zsh-syntax-highlighting|https://github.com/zsh-users/zsh-syntax-highlighting.git]
*

#### themes
* dracula (default)
* powerlevel10k

### `vim` plugins
Current list of VIM plugins which are installed
* [vim-plug|https://github.com/junegunn/vim-plug]
* [nerdtree|https://github.com/preservim/nerdtree]
* [vim-airline|https://github.com/vim-airline/vim-airline]
** vim-airline-theme
* [vim-fugitive|https://github.com/tpope/vim-fugitive]
* [Conquer of Completion|https://github.com/neoclide/coc.nvim]

### `starship`
[starship|https://starship.rs/] can be optionally installed and configuration bootstrapped.
