# Prerequisites:
# install iTerm
# Install sublime


# Ask for the administrator password upfront.
sudo -v

# Keep-alive: update existing `sudo` time stamp until `.osx` has finished.
while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done 2>/dev/null &

# install oh-my-zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
cp -a ./dotfiles_tmp/zsh/. ~/.oh-my-zsh/custom/

# set up sublime symlink
ln -sf /Applications/Sublime\ Text.app/Contents/SharedSupport/bin/subl ~/bin/s

# copy my standard settings into sublime
cp -a ./dotfiles_tmp/sublime/. ~/Library/Application\ Support/Sublime\ Text\ 3/Packages/User/


# install nvm
if [ ! -d "$HOME/.volta	" ]; then
	curl https://get.volta.sh | bash
fi


# install homebrew
if ! type "$brew" > /dev/null; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
	echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> /Users/rhys.evans/.zprofile
	eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# Make sure we’re using the latest Homebrew.
brew update

# Upgrade any already-installed formulae.
brew upgrade

brew install wget
brew install jq
brew install watchman
brew install awscli
brew tap heroku/brew && brew install heroku
brew install terraform
brew install circleci
brew install vault
brew install gh

# Remove outdated versions from the cellar.
brew cleanup

# NVM & node & tldr & other global packages
# inconsolata for powerline
