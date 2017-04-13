#!/bin/bash

## Returns the web URL to Gitlab for a git repo.

# The origin name could be passed in, but defaults to "origin"
[ ! -z $1 ] && ORIGIN="$1" || ORIGIN="origin"

# Steps:
# If SSH URL, replace with HTTP equivalent.
# If was SSH URL, fix the URL so it doesn't contain the colon.
# Finally, strip ".git" from end of URL.
git remote -v | grep "^$ORIGIN[[:space:]]" | grep '(fetch)$' | awk '{print $2}' \
  | sed 's/git@/http:\/\//' \
  | sed 's/gitlab.bonniercorp.local:/gitlab.bonniercorp.local\//' \
  | sed 's/\.git$//' \
