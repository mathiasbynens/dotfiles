#!/bin/bash

local="@genomeweb.local"
remote="@pantheon.genomeweb.small-db"

if [[ $1 == "y" || $1 == "yes" ]]; then
  drush $local sql-drop -y
  drush sql-sync $remote $local -y
fi

drush $local local
