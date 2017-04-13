#!/bin/bash

local="@sc.local"
remote="$1"
run_updates="$2"
drush=drush

$drush $local sql-drop -y
$drush sql-sync $remote $local -y

#$drush $local rr
$drush $local cc all
$drush $local en -y devel 
#stage_file_proxy

if [[ $run_updates == "yes" ]]; then
  $drush $local updb -y
fi

$drush $local uli
