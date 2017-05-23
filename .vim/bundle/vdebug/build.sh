#!/bin/bash
version=`cat VERSION`
echo "Building vdebug version $version"
tar -cvzf vdebug-$version.tar.gz doc/Vdebug.txt plugin syntax tests CHANGELOG LICENCE README.md requirements.txt vdebugtests.py VERSION
