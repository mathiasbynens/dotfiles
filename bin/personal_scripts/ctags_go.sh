#!/bin/bash

# Go to docroot and re-build ctags list.
cd $1
/usr/local/bin/ctags --langmap=php:.engine.inc.module.theme.install.php --php-kinds=cdfi --languages=php --recurse --sort=foldcase
