#!/bin/bash

# Make sure we’re using the latest Homebrew
brew update

# Upgrade any already-installed formulae
brew upgrade

# Install GNU core utilities (those that come with OS X are outdated)
brew install coreutils

# Install GNU `find`, `locate`, `updatedb`, and `xargs`, g-prefixed
brew install findutils
# Install Bash 4
brew install bash

# Install wget with IRI support
brew install wget --enable-iri

# Install more recent versions of some OS X tools
brew tap     homebrew/dupes
brew install homebrew/dupes/grep

# databases
brew install mysql

unset TMPDIR
mysql_install_db --verbose --user=`brunogermano` --basedir="$(brew --prefix mysql)" --datadir=/usr/local/var/mysql --tmpdir=/tmp

mkdir -p ~/Library/LaunchAgents
cp /usr/local/Cellar/mysql/5.5.27/homebrew.mxcl.mysql.plist ~/Library/LaunchAgents/
launchctl load -w ~/Library/LaunchAgents/homebrew.mxcl.mysql.plist

#setting a password root:root
echo "Setting mysql password root/root."
$(brew --prefix mysql)/bin/mysqladmin -u root password root

echo "Start mysql"
mysql.server start

brew install mongodb

mkdir -p ~/Library/LaunchAgents
cp /usr/local/Cellar/mongodb/2.2.0-x86_64/homebrew.mxcl.mongodb.plist ~/Library/LaunchAgents/
launchctl load -w ~/Library/LaunchAgents/homebrew.mxcl.mongodb.plist

echo "Start mongodb"
mongod run --config /usr/local/etc/mongod.conf

#php
brew tap     josegonzalez/homebrew-php
brew install php54 --without-apache --with-mysql

chmod -R ug+w /usr/local/Cellar/php54/5.4.6/lib/php
pear config-set php_ini /usr/local/etc/php/5.4/php.ini

echo "To enable PHP in Apache add the following to httpd.conf and restart Apache:"
echo "    LoadModule php5_module    /usr/local/Cellar/php54/5.4.6/libexec/apache2/libphp5.so"

sublime -w /etc/apache2/httpd.conf 

sudo apachectl restart
brew install xdebug

# Install everything else
brew install git
brew install graphicsmagick
brew install node

# install git and bash-completion 
brew install bash-completion git

# Remove outdated versions from the cellar
brew cleanup
