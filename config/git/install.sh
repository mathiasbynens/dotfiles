echo "================================================="
echo "GIT - INSTALLING PREFERENCES"
echo "================================================="
echo ""

CDIR=$(dirname $0)
CPATH="$(pwd)/${CDIR#./}"

echo "creating symlink at ~/.gitattributes"
rm -rf ~/.gitattributes
ln -s $CPATH/.gitattributes ~/.gitattributes

echo "creating symlink at ~/.gitconfig"
rm -rf ~/.gitconfig
ln -s $CPATH/.gitconfig ~/.gitconfig

echo "creating symlink at ~/.gitignore"
rm -rf ~/.gitignore
ln -s $CPATH/.gitignore ~/.gitignore

echo ""
echo "DONE"
echo ""
