# won't last long but will give you 1G.
sudo rm /private/var/vm/sleepimage

# Clean up system logs and temporary files
#   http://www.thexlab.com/faqs/maintscripts.html
sudo periodic daily weekly monthly


# remove old homebrew versions
#  https://github.com/Homebrew/homebrew/blob/master/share/doc/homebrew/FAQ.md#how-do-i-uninstall-old-versions-of-a-formula
brew cleanup -n  # to see what would get cleaned up
brew cleanup   # to do it.

cask cleanup


~/Library/Caches/Google/Chrome Canary/Default
~/Library/Caches/Google/Chrome/Default
~/Library/Application Support/stremio/stremio-cache

# diskexplorer X is good for big files
# daisy disk is good for big folders

# XCODE is enormous
#   kill cache
rm -rf ~/Library/Caches/com.apple.dt.Xcode
#   appears that XCode can survive deleting ALL documentation sets!
~/Library/Developer/Shared/Documentation/DocSets
/Applications/Xcode.app/Contents/Developer/Documentation/DocSets
# other simulators can be here.
/Library/Developer/CoreSimulator/Profiles/Runtimes

# use appcleaner to remove weird shit

emptytrash

