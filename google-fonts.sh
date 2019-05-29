#!/bin/sh

# Written by: Keefer Rourke <https://krourke.org>
# Based on AUR package <https://aur.archlinux.org/cgit/aur.git/tree/PKGBUILD?h=ttf-google-fonts-git>
# ref: https://gist.github.com/keeferrourke/d29bf364bd292c78cf774a5c37a791db

# dependancies: fonts-cantarell, ttf-ubuntu-font-family, git
sudo apt-get install fonts-cantarell, ttf-ubuntu-font-family, git
srcdir="/tmp/google-fonts"
pkgdir="/usr/share/fonts/truetype/google-fonts"
giturl="git://github.com/google/fonts.git"

mkdir $srcdir
cd $srcdir
echo "Cloning Git repository..."
git clone $giturl

echo "Installing fonts..."
sudo mkdir -p $pkgdir
sudo find $srcdir -type f -name "*.ttf" -exec install -Dm644 {} $pkgdir \;

echo "Cleaning up..."
sudo find $pkgdir -type f -name "Cantarell-*.tff" -delete \;
sudo find $pkgdir -type f -name "Ubuntu-*.tff" -delete \;

# provides roboto
sudo apt-get --purge remove fonts-roboto

echo "Updating font-cache..."
sudo fc-cache -f > /dev/null

echo "Done!"