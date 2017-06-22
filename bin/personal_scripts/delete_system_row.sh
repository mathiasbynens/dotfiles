#!/bin/bash

alias="$1"
name="$2"

if [[ -z $alias || -z $name ]]; then
  echo "Missing a required parameter."
  echo "Usage: $0 [Drush alias] [project name]"
  exit 1
fi

drush $alias sql-query "DELETE FROM system WHERE name = '$name'"
