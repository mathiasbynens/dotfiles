# This is a Brewfile for Homebrew, which lists the packages and applications to be installed on the system.
# It includes both command-line tools and GUI applications, as well as VS Code extensions and global NPM packages.

# To create Brewfile run this command
# !⚠️! CAUTION !⚠️! This will overwrite the existing Brewfile with the currently installed packages on your system.
# brew bundle dump --file=./Brewfile.new

## Shell
brew "zsh"

## Git + Github
# brew "git"
# brew "gh"
brew "git-lfs"

## File Processing
brew "ffmpeg"
brew "gifsicle"
brew "exiftool"

## Development Tools
# Install GNU core utilities (those that come with macOS are outdated).
# Don’t forget to add `$(brew --prefix coreutils)/libexec/gnubin` to `$PATH`.
brew "coreutils"
brew "go"
brew "jq"
brew "mkcert"
brew "python@3.14"
brew "stow"
brew "tree"

# install using standalone script instead, see: https://pnpm.io/installation
# brew "pnpm"


# AI Tools
# brew "gemini-cli" # outdated, use Antigravity instead
cask "copilot-cli"

## Other
brew "googleworkspace-cli"

## GUI Applications
cask "visual-studio-code"
cask "iterm2"
cask "stats"
cask "bruno"

## Fonts
cask "font-fira-code"
# Popular alternatives / Nerd Font options:
# cask "font-fira-code-nerd-font"
# cask "font-jetbrains-mono-nerd-font"
# cask "font-meslo-lg-nerd-font"
# cask "font-hack-nerd-font"

## VS Code Extensions
# Managed centrally across macOS & Linux via ./vscode.sh


## Global NPM Packages
npm "@google/jules"
# npm "corepack"
# npm "deno"

## Work Related
brew "colima", restart_service: :changed
brew "docker"
