# Melle’s dotfiles

![Screenshot of included dot files](./meta/image.png)

## Installation

**Warning:** If you want to give these dotfiles a try, you should first fork this repository, review the code, and remove things you don’t want or need. Don’t blindly use my settings unless you know what that entails. Use at your own risk!

## Requirements

- **macOS:** macOS (Xcode Command Line Tools & [Homebrew](https://brew.sh/) will be installed automatically if missing)
- **Linux (Ubuntu/Debian):** `apt` (built-in)

## Installation

### Quick Install (One-Liner on a Fresh Machine)

On a fresh macOS or Ubuntu/Debian installation, run:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/melledijkstra/dotfiles/main/install.sh)"
```

This will ensure `git` (and Xcode Command Line Tools on macOS) is installed, clone the repository to `~/projects/dotfiles`, and launch the interactive installer.

### Using Git and the install script

Alternatively, you can clone the repository manually (recommended: `~/projects/dotfiles`). The interactive `install.sh` script asks upfront which steps you want to run, ensures core prerequisites (`git`, `curl`, `zsh`, `stow`, `Oh My Zsh`) are installed, and executes your selected steps.

```bash
git clone https://github.com/melledijkstra/dotfiles.git ~/projects/dotfiles
cd ~/projects/dotfiles
./install.sh
```

You can also run individual steps manually:

```bash
# Core prerequisites (git, curl, zsh, stow, Oh My Zsh, zsh-autosuggestions):
./core.sh

# On Ubuntu / Debian:
./apt.sh
# optional: installs GUI apps, e.g. Google Chrome, VS Code, Spotify and various dev tools
./apps-linux.sh
# optional: applies sensible Ubuntu (GNOME) desktop defaults
./ubuntu.sh

# On macOS:
./brew.sh
# optional: installs standalone macOS tools (e.g. Antigravity CLI)
./apps-macos.sh
# optional: applies sensible macOS defaults
./macos.sh

# Symlink dotfiles to $HOME (automatically backs up existing conflicts to ~/.dotfiles-backup):
./bootstrap.sh

# Cross-platform: Configure VS Code settings & install extensions:
./vscode.sh

# Clone or pull your development repositories from config/repos/*.txt:
./home/bin/sync-repos
```

## Updating the dotfiles

All scripts are idempotent and safe to run multiple times. To update at any time, just run `./install.sh` and it will pull the latest changes and update the components you select.

### Update only the dotfiles

To only update the home directory (~/) dot files (.zshrc, .path, .exports, etc.)
run the following command:

```bash
./bootstrap.sh
```

## Configurations

### Specify the `$PATH`

Here’s an example `~/.path` file that adds `/usr/local/bin` to the `$PATH`:

```bash
export PATH="/usr/local/bin:$PATH"
```

### Add secret configurations

In order to keep sensitive data safe, you can put any of that information in the .secrets file.
e.g. personal access tokens, emails, passwords, api keys, etc.

An example of my `.secrets` file can be found in `home/.secrets.example`

You could also use `~/.secrets` to override settings, functions and aliases from my dotfiles repository. It’s probably better to [fork this repository](https://github.com/melledijkstra/dotfiles/fork) instead, though.

### Sensible macOS defaults

When setting up a new Mac, you may want to set some sensible macOS defaults:

```bash
./macos.sh
```

### Install Homebrew formulae

When setting up a new Mac, you may want to install some common [Homebrew](https://brew.sh/) formulae (after installing Homebrew, of course):

```bash
./brew.sh
```

Some of the functionality of these dotfiles depends on formulae installed by `brew.sh`. If you don’t plan to run `brew.sh`, you should look carefully through the script and manually install any particularly important ones.
