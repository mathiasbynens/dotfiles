#!/bin/bash

local="@genomeweb.local"
remote="@pantheon.genomeweb.small-db"

if [[ $1 == "y" ]]; then
  drush $local sql-drop -y
  drush sql-sync $remote $local -y
fi

drush $local dev \
  && drush $local en -y devel stage_file_proxy views_ui field_ui \
