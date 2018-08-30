#! /bin/sh
echo "================================================="
echo "EXPORTS - UNINSTALLING PREFERENCES"
echo "================================================="
echo ""

echo "removing symlink at ~/.gitattributes"
rm -rf ~/.gitattributes

echo "removing symlink at ~/.gitconfig"
rm -rf ~/.gitconfig

echo "removing symlink at ~/.gitignore"
rm -rf ~/.gitignore

echo ""
echo "REMOVED"
echo ""

