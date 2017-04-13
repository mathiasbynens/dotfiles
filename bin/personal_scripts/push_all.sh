#!/bin/bash

# Pushes all configs to a remote server. 
~/scripts/push_bonnier_public_key_to_remote.sh "$1"
~/scripts/push_personal_settings.sh "$1"
