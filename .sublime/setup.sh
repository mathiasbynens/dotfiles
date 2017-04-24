# create symbolic link to sublime config files
cd ~/Library/Application\ Support/Sublime\ Text\ 3/Packages/
rm -r User
ln -s ~/.sublime/User

echo "Start sublime text and install package control, see https://packagecontrol.io/"
echo "When installed restart Sublime"