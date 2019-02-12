#!/bin/bash

if [ $# -lt 2 ]; then
  >&2 echo "Usage: $0 [environment] [file]"
  >&2 echo "Example: $0 gw-720 /path/to/upload-file.txt"
  exit 1
fi

env="$1"
file="$2"

echo "put $file files/private/settings/" | $(terminus connection:info genomeweb.$env --field=sftp_command)
