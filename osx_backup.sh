#!/bin/bash

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

  echo "Creating backup..."

  # extract the settings being modified by .osx
  settings=`egrep "^defaults (-currentHost )?write [[:alnum:][:punct:]]+ [[:alnum:][:punct:]]+ (-array |-bool |-int |-string |-dict-add |-array-add )?.*" .osx | sed "s/write/read/" | sed "s/\(defaults\)\(.*\)\(read [a-zA-Z[:punct:] ]*\) -.*/\1\2\3/"`

  # Bash workaround to enable iteration over array values that have whitespace
  oldifs=$IFS
  IFS=$(echo -en "\n\b")

  # Iterate over the OSX settings array - storing the current value in .osx_settings_backup
  for s in ${settings[*]}; do
    t=`eval "$s 2>/dev/null"`

    # replace the action with a placeholder
    # to easily swap it out during settings restore
    c=`echo $s | sed "s/ read / :action: /"`
    if [[ $t ]]; then
      echo $c ":" $t >> .osx_settings_backup
    else
      echo $c ": default" >> .osx_settings_backup
    fi
  done
  IFS=$oldifs

  # Backup Launchpad DB
  for file in ~/Library/Application\ Support/Dock/*.db; do
    cp "$file" "$file.bak";
  done

  echo "Settings backed up to .osx_settings_backup"
}

process

exit