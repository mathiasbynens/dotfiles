#!/bin/bash

function restore () {
  # Check that there are backup settings to restore from
  if [[ ! -e ".osx_settings_backup" ]]; then
    echo "Cannot find backup. Exiting..."
    exit
  fi

  echo "Restoring backup..."

  # extract the backup settings from .osx_settings_backup
  settings=`egrep "^defaults (-currentHost )?:action: [[:alnum:][:punct:]]+ [[:alnum:][:punct:]]+" .osx_settings_backup`

  # Bash workaround to enable iteration over array values that have whitespace
  oldifs=$IFS
  IFS=$(echo -en "\n\b")

  # Iterate over the OSX settings array - storing the current value in .osx_settings_backup
  for s in ${settings[*]}; do

    # get the value
    value=`echo $s | sed "s/.* : //"`

    # get the command
    com=`echo $s | sed "s/ : .*//"`

    # if the backed up setting is 'default', the modified setting is removed which
    # causes OSX to revert to the default settings
    if [[ $value = 'default' ]]; then
      com=`echo $com | sed "s/ :action: / delete /"`
      eval "$com"
    else
      com=`echo $com | sed "s/ :action: / write /"`
      eval "$com '$value'"
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

  echo "Backup restored."
}

restore

exit