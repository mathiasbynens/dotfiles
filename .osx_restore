#!/bin/bash

# Settings - Check .osx for description of modification
declare -a settings=( "NSGlobalDomain AppleKeyboardUIMode" \
                      "NSGlobalDomain AppleFontSmoothing" \
                      "com.apple.dock no-glass" \
                      "com.apple.dock autohide" \
                      "com.apple.dock showhidden" \
                      "com.apple.dock itunes-notifications" \
                      "NSGlobalDomain AppleEnableMenuBarTransparency" \
                      "com.apple.menuextra.battery ShowPercent" \
                      "com.apple.menuextra.battery ShowTime" \
                      "NSGlobalDomain AppleShowScrollBars" \
                      "com.apple.finder QuitMenuItem" \
                      "com.apple.finder DisableAllAnimations" \
                      "NSGlobalDomain AppleShowAllExtensions" \
                      "com.apple.finder ShowStatusBar" \
                      "NSGlobalDomain NSNavPanelExpandedStateForSaveMode" \
                      "NSGlobalDomain PMPrintingExpandedStateForPrint" \
                      "com.apple.LaunchServices LSQuarantine" \
                      "com.apple.screencapture disable-shadow" \
                      "com.apple.dock mouse-over-hilte-stack" \
                      "com.apple.dock enable-spring-load-actions-on-all-items" \
                      "com.apple.dock show-process-indicators" \
                      "com.apple.dock launchanim" \
                      "com.apple.Dock autohide-delay" \
                      "NSGlobalDomain NSTextShowsControlCharacters" \
                      "NSGlobalDomain ApplePressAndHoldEnabled" \
                      "NSGlobalDomain KeyRepeat" \
                      "NSGlobalDomain NSAutomaticSpellingCorrectionEnabled" \
                      "NSGlobalDomain NSAutomaticWindowAnimationsEnabled" \
                      "com.apple.NetworkBrowser BrowseAllInterfaces" \
                      "com.apple.frameworks.diskimages skip-verify" \
                      "com.apple.frameworks.diskimages skip-verify-locked" \
                      "com.apple.frameworks.diskimages skip-verify-remote" \
                      "com.apple.frameworks.diskimages auto-open-ro-root" \
                      "com.apple.frameworks.diskimages auto-open-rw-root" \
                      "com.apple.finder OpenWindowForNewRemovableDisk" \
                      "com.apple.finder _FXShowPosixPathInTitle" \
                      "NSGlobalDomain NSWindowResizeTime" \
                      "com.apple.desktopservices DSDontWriteNetworkStores" \
                      "com.apple.finder FXEnableExtensionChangeWarning" \
                      "com.apple.finder WarnOnEmptyTrash" \
                      "com.apple.finder EmptyTrashSecurely" \
                      "com.apple.screensaver askForPassword" \
                      "com.apple.screensaver askForPasswordDelay" \
                      "com.apple.driver.AppleBluetoothMultitouch.trackpad Clicking" \
                      "com.apple.driver.AppleBluetoothMultitouch.trackpad TrackpadCornerSecondaryClick" \
                      "com.apple.driver.AppleBluetoothMultitouch.trackpad TrackpadRightClick" \
                      "com.apple.Safari DebugSnapshotsUpdatePolicy" \
                      "com.apple.Safari IncludeInternalDebugMenu" \
                      "com.apple.Safari FindOnPageMatchesWordStartsOnly" \
                      "com.apple.Safari ProxiesInBookmarksBar" \
                      "NSGlobalDomain WebKitDeveloperExtras" \
                      "com.apple.addressbook ABShowDebugMenu" \
                      "com.apple.iCal IncludeDebugMenu" \
                      "com.apple.terminal StringEncodings" \
                      "com.apple.iTunes disablePingSidebar" \
                      "com.apple.iTunes disablePing" \
                      "com.apple.iTunes NSUserKeyEquivalents" \
                      "com.apple.Mail DisableReplyAnimations" \
                      "com.apple.Mail DisableSendAnimations" \
                      "com.apple.mail AddressesIncludeNameOnPasteboard" \
                      "NSGlobalDomain NSQuitAlwaysKeepsWindows" \
                      "com.apple.loginwindow TALLogoutSavesState" \
                      "com.apple.loginwindow LoginwindowLaunchesRelaunchApps" \
                      "com.apple.dashboard devmode" \
                    )


function restore () {
  # Check that there are backup settings to restore from
  if [[ ! -e ".osx_settings_backup" ]]; then
    echo "Cannot find backup. Exiting..."
    exit
  fi

  # Bash workaround to enable iteration over array values that have whitespace
  oldifs=$IFS
  IFS=$(echo -en "\n\b")

  # Iterate over the OSX settings array - storing the current value in .osx_settings_backup
  for s in ${settings[*]}; do
    # extract the current setting value from .osx_settings_backup
    value=`grep "$s : .*" .osx_settings_backup | sed "s/.* : //"`

    # if the backed up setting is 'default', the modified setting is removed which
    # causes OSX to revert to the default settings
    if [[ $value = 'default' ]]; then
      eval "defaults delete $s"
    else
      eval "defaults write $s '$value'"
    fi
    unset value
  done
  IFS=$oldifs
  unset oldifs

  # Don't show item info below desktop icons
  /usr/libexec/PlistBuddy -c "Set :DesktopViewSettings:IconViewSettings:showItemInfo false" ~/Library/Preferences/com.apple.finder.plist

  # Disable snap-to-grid for desktop icons
  /usr/libexec/PlistBuddy -c "Set :DesktopViewSettings:IconViewSettings:arrangeBy kind" ~/Library/Preferences/com.apple.finder.plist

  # Hide the ~/Library folder
  chflags hidden ~/Library

  # Enable local Time Machine backups
  echo "Enabling Time Machine... (may require password or ctrl + c to skip)"
  sudo tmutil enablelocal

  # Restore Dropbox’s green checkmark icons in Finder
  file=/Applications/Dropbox.app/Contents/Resources/check.icns
  [ -e "$file.bak" ] && mv -f "$file.bak" "$file" $$ rm -f "$file.bak"
  unset file

  # Backup Launchpad DB
  for file in ~/Library/Application\ Support/Dock/*.db.bak; do
    # copy the backup andremove .bak
    cp "$file" "${file//.bak/}"
    rm -f "$file"
  done

  # Kill affected applications
  for app in Safari Finder Dock Mail SystemUIServer; do killall "$app" >/dev/null 2>&1; done
}

restore

exit