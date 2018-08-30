echo "================================================="
echo "EXPORTS - INSTALLING"
echo "================================================="
echo ""

CDIR=$(dirname $0)
CPATH="$(pwd)/${CDIR#./}"

echo "creating symlink at ~/.exports"
rm -rf ~/.exports
ln -s $CPATH/.exports ~/.exports

echo ""
echo "DONE"
echo ""
