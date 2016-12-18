#!/usr/bin/env bash

#Vettery, Should run on all unix based systems.

#move to home.
cd

#Clone the Repo
git clone git@github.com:vettery/vettery.git vettery;

#Shortcut to vettery
alias vv='cd ~/vettery'

#Install virtualbox and vagrant.
brew cask install virtualbox

brew cask install vagrant

brew cask install vagrant-manager

#Frontend dev in order...
cd ~/vettery

brew install ruby
gem install bundler
bundle install

brew install node@6
npm install

./node_modules/protractor/bin/webdriver-manager update

cd

#Change hosts file

echo "192.168.33.23 dev.vettery.local" | sudo tee -a /etc/hosts;
echo "54.84.82.141   tools" | sudo tee -a /etc/hosts;






