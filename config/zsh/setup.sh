#! /bin/sh
echo "================================================="
echo "ZSH - INSTALLING - CONFIGURING"
echo "================================================="
echo ""

CDIR=$(dirname $0)
CPATH="$(pwd)/${CDIR#./}"

$CPATH/antigen.sh

echo ""
echo "DONE"
echo ""