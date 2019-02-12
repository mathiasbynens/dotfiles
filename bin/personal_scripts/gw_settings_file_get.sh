#!/bin/bash

if [ $# -lt 2 ]; then
  >&2 echo "Usage: $0 [environment] [category]"
  >&2 echo "Example: $0 gw-720 dev"
  exit 1
fi

env="$1"
category="$2"
file="$category.settings.php"

echo "get files/private/settings/$file" | $(terminus connection:info genomeweb.$env --field=sftp_command)
mv -v $file $HOME/temp/