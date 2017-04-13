#!/bin/bash

[ ! -z $1 ] && BRANCH="$1" || BRANCH=$(git rev-parse --abbrev-ref HEAD)

# If branch is numeric, we should assume it's for Sandcastle queue, so prepend
# "SAN-".
RE='^[0-9]+$'
if [[ $BRANCH =~ $RE ]]; then
  BRANCH="SAN-$BRANCH"
fi

# The origin name could be passed in, but defaults to "origin"
[ ! -z $2 ] && ORIGIN="$2" || ORIGIN="origin"

git fetch --all
git checkout $BRANCH
git rebase $ORIGIN/$BRANCH
