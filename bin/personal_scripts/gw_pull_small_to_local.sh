#!/bin/bash

set -e

local="@gw.local"
site="genomeweb"
env="$1"
rebuild_caches="$2"

if [ $# -ne 2 ]; then
  >&2 echo "Usage: $0 [environment] [rebuild-caches?]"
  >&2 echo "Example: $0 gw-720 yes"
  exit 1
fi

dump_file=/tmp/dump_$site-$env.sql
dump_file_compressed=/tmp/dump_$site-$env.sql.gz
rm -f $dump_file
rm -f $dump_file_compressed

terminus backup:create "$site.$env" --element=db --keep-for=7
dump_url=$(terminus backup:get $site.$env --element=db)

curl "$dump_url" > $dump_file_compressed
# Will rename file to $dump_file value.
gzip -d $dump_file_compressed

drush $local sql-drop -y
drush $local sqlc < $dump_file

if [[ $rebuild_caches == "y" || $rebuild_caches == "yes" ]]; then
  drush $local local
fi
