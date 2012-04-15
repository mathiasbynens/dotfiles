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

function process () {
  # Create a backup file if one doesn't exists
  if [[ ! -e '.osx_settings_backup' ]]; then
    echo "Backup Settings" > .osx_settings_backup
  else
    # If a backup already exists, the script exits to prevent
    # the backup being overwrittern with the modified values
    echo "Backup already created. Cancelling operation..."
    exit
  fi

  # Bash workaround to enable iteration over array values that have whitespace
  oldifs=$IFS
  IFS=$(echo -en "\n\b")

  # Iterate over the OSX settings array - storing the current value in .osx_settings_backup
  for s in ${settings[*]}; do
    t=`eval "defaults read $s 2>/dev/null"`
    if [[ $t ]]; then
      echo $s ":" $t >> .osx_settings_backup
    else
      echo $s ": default" >> .osx_settings_backup
    fi
  done
  IFS=$oldifs

  # Backup Launchpad DB
  for file in ~/Library/Application\ Support/Dock/*.db; do
    cp "$file" "$file.bak";
  done
}

process

exit