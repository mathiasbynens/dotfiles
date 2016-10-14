#!/usr/bin/env bash

# UTI script
# Requires Homebrew!
# Set macOS file associations (UTI) via Terminal

# Preparation
brew install duti
sed -n 24,50p ~/Dropbox/dotfiles/duti.sh > /tmp/duti_list

# Set associations
duti /tmp/duti_list

# Cleanup
brew uninstall duti

# Exit
echo "File types succesfully associated!"
return

# Bundle id             UTI/.ext/MIME-type  role

# Sublime Text
com.sublimetext.3       public.plain-text   all
com.sublimetext.3       public.source-code  all

# The Unarchiver
cx.c3.theunarchiver     .7z                 all
cx.c3.theunarchiver     .cab                all
cx.c3.theunarchiver     .gtar               all
cx.c3.theunarchiver     .gz                 all
cx.c3.theunarchiver     .hqx                all
cx.c3.theunarchiver     .jar                all
cx.c3.theunarchiver     .msi                all
cx.c3.theunarchiver     .rar                all
cx.c3.theunarchiver     .sit                all
cx.c3.theunarchiver     .sit                all
cx.c3.theunarchiver     .tar                all
cx.c3.theunarchiver     .tar.gz             all
cx.c3.theunarchiver     .tar.xz             all
cx.c3.theunarchiver     .tgz                all
cx.c3.theunarchiver     .zip                all

# Transmission
org.m0k.transmission    .torrent            all

# VLC
org.videolan.vlc        .avi                all
org.videolan.vlc        .mp4                all
org.videolan.vlc        .mkv                all
