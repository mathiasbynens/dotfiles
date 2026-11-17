#!/usr/bin/env bash

# Install essential applications & tools on Ubuntu/Debian using apt

set -e

SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Ensure core prerequisites (git, curl, zsh, stow, Oh My Zsh) are installed
bash "$SOURCE_DIR/core.sh"

echo "📦 Updating apt package index and upgrading installed packages..."
sudo apt update
sudo apt upgrade -y

echo "🚀 Installing packages via apt..."

PACKAGES=(
  # Shell & Dotfiles management
  zsh
  stow
  curl

  # Git
  git
  git-lfs

  # File Processing
  ffmpeg
  gifsicle
  libimage-exiftool-perl

  # Development Tools & Fonts
  golang-go
  jq
  libnss3-tools
  mkcert
  python3
  tree
  fonts-firacode

  # Containers
  # docker.io # for now disabled
)

sudo apt install -y "${PACKAGES[@]}"

# Clean up unused packages
sudo apt autoremove -y

echo "Finished apt setup! 🎉"
