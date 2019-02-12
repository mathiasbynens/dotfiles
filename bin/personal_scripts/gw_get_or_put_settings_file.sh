#!/bin/bash

env="$1"
op="$2"
filename="dev.settings.php"
container=/Users/chill/temp/gw-pantheon-settings

if [[ -z $env || -z $op ]]; then
  >&2 echo "Error: Missing required arguments."
  >&2 echo "Usage: $0 [environment] [get|put]"
  >&2 echo "Example: $0 gw-123 get"
  exit 1
fi

if [[ $op != "get" && $op != "put" ]]; then
  >&2 echo "Error: The operation must be either 'get' or 'put'."
  exit 1
fi

if [[ $op == "put" && ! -f $container/$filename ]]; then
  >&2 echo "Error: Missing upload file: $container/$filename"
  exit 1
fi

env="genomeweb.$env"
terminus env:info $env --field=id > /dev/null
if [ $? -ne 0 ]; then
  >&2 echo "Error: Invalid environment: $env."
  exit 1
fi

if [ ! -d $container ]; then
  mkdir $container
fi
chown `whoami` $container
chmod 700 $container
cd $container

if [[ $op == "get" ]]; then

  rm -rf $container/*
  (
    echo "
    cd files/private/settings
    get $filename
    ls
    quit
      "
  ) | `terminus connection:info $env --field=sftp_command` > /dev/null

  echo "Fetched:"
  realpath $container/$filename
  echo ""

elif [[ $op == "put" ]]; then

  (
    echo "
    cd files/private/settings
    put $filename
    ls
    quit
      "
  ) | `terminus connection:info $env --field=sftp_command`
fi