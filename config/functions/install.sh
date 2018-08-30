echo "================================================="
echo "FUNCTIONS - INSTALLING"
echo "================================================="
echo ""

CDIR=$(dirname $0)
CPATH="$(pwd)/${CDIR#./}"

echo "creating symlink at ~/.functions"
rm -rf ~/.functions
ln -s $CPATH/.functions ~/.functions

echo ""
echo "DONE"
echo ""
