echo "================================================="
echo "ALIASES - INSTALLING"
echo "================================================="
echo ""

CDIR=$(dirname $0)
CPATH="$(pwd)/${CDIR#./}"

echo "creating symlink at ~/.aliases"
rm -rf ~/.aliases
ln -s $CPATH/.aliases ~/.aliases

echo ""
echo "DONE"
echo ""
