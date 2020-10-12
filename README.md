# dotfiles

## Installation
1.  Clone repository
```bash
git clone https://github.com/dmorand17/dotfiles.git && cd dotfiles
```
2.  Run bootstrap: `make bootstrap`

## Upgrade
Run `make upgrade` to upgrade existing solution

## Additional Commands
Output from `make help`
```
bootstrap              Bootstrap system (install/configure apps, link dotfiles)
docker_build           Build dotfiles container. \n[BRANCH]=branch to build (defaults to 'master')
docker_clean           Clean dotfiles docker containers/images
docker_test            Test dotfiles using docker
function               Perform 1..n functions defined from bootstrap script
link                   Links files for shell
upgrade                Upgrade the local repository, and run any updates
update_submodules      Update submodules
```

### Linking Files
**Shell**: Any linked shell configuration can be extended by creating a `.local` version (e.g. .alias.local)

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

## Testing using `docker`
A docker image can be created with the repository to be used for testing out the configuration.

`make docker_build [BRANCH='branch']` to build an image.
    Default `BRANCH=master`
`make docker_test` to launch docker container to perform necessary tests
`make docker_clean` to clean any unused images/containers

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
