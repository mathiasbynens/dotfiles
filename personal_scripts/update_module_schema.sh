#!/bin/bash

alias="$1"
module="$2"
schema="$3"

if [[ -z $alias || -z $module || -z $schema ]]; then
  echo "Missing a required parameter."
  echo "Usage: $0 [Drush alias] [module name] [schema version] ..."
  exit 1
fi

drush $alias sql-query "UPDATE system SET schema_version = $schema WHERE name = '$module'"
