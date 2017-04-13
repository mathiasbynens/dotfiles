#!/bin/bash

HOST="devphp53.bonniercorp.local"
#HOST="prodphp53-srv1.ec2.bonniercorp.local"

cd /Users/chill/Sites/sc/docroot/sites/vm.sandcastle.bonniercorp.com/files

rsync -av \
  --exclude 'js' \
  --exclude 'css' \
  --exclude 'styles' \
  $HOST:/var/www/sandcastle-locals/sandcastle.bonniercorp.com/files/ \
  .

chown -R chill .
chmod -R 777 .
