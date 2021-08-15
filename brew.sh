#!/usr/bin/env bash

# Install command-line tools using Homebrew.

# Make sure we’re using the latest Homebrew.
brew update

# Upgrade any already-installed formulae.
brew upgrade

BREW_PREFIX=$(brew --prefix)

brew install tree
brew install wget
brew install rename
brew install hyperfine