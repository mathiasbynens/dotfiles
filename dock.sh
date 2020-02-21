#!/bin/sh

dockutil --no-restart --remove all
dockutil --no-restart --add "/Applications/finder"
dockutil --no-restart --add "/Applications/Google Chrome.app"
dockutil --no-restart --add "/Applications/Mail.app"
dockutil --no-restart --add "/Applications/Calendar.app"
dockutil --no-restart --add "/Applications/System Preferences.app"
dockutil --no-restart --add "/Applications/Spotify.app"
dockutil --no-restart --add "/Applications/iTerm.app"
dockutil --no-restart --add "/Applications/Rambox.app"
dockutil --no-restart --add "/Applications/Sublime\ Text.app"

killall Dock
