#!/bin/bash

# Pushes public key to authorized_keys on remote server.
# If ~/.ssh directory does not yet exist, create it.
cat ~/.ssh/bonnier/id_rsa_bonnier.pub | ssh "$1" '[ -d ~/.ssh ] || mkdir ~/.ssh; cat >> ~/.ssh/authorized_keys'
