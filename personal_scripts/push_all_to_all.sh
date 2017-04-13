#!/bin/bash

for server in `grep -v '^#' /Users/chill/scripts/var/lib/servers.list`; do
  # Pushes all configs to a remote server. 
  ~/scripts/push_bonnier_public_key_to_remote.sh "$server"
  ~/scripts/push_personal_settings.sh "$server"
done
