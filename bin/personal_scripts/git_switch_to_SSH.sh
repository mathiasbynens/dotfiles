#!/bin/bash

# The origin name could be passed in, but defaults to "origin"
[ ! -z $1 ] && ORIGIN="$1" || ORIGIN="origin"

# Steps:
# If HTTP URL, replace with SSH equivalent.
# Fix the URL so it does contain the colon.
# Finally, set this URL to be the git remote.
NEW_URL=$(git remote -v | grep "^$ORIGIN[[:space:]]" | grep '(fetch)$' | awk '{print $2}' \
  | sed 's/http:\/\//git@/' \
  | sed 's/gitlab.bonniercorp.local\//gitlab.bonniercorp.local:/')
git remote set-url $ORIGIN $NEW_URL
