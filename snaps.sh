# Access as root
sudo -u

sudo snap install brave
sudo snap install darktable
sudo snap install gimp
sudo snap install slack --classic
sudo snap install spotify
sudo snap install telegram-desktop
sudo snap install discord
sudo snap install htop
sudo snap install mqtt-explorer
sudo snap install okular
sudo snap install postman
sudo snap install skype --classic
sudo snap install gnome-clocks
sudo snap install gitkraken

# theme
sudo sh -c "echo 'deb http://download.opensuse.org/repositories/home:/Horst3180/xUbuntu_16.04/ /' > /etc/apt/sources.list.d/home:Horst3180.list"
wget -nv https://download.opensuse.org/repositories/home:Horst3180/xUbuntu_16.04/Release.key -O Release.key
sudo apt-key add - < Release.key
sudo apt-get update
sudo apt-get install arc-theme

# flat remix gtk blue dark
# https://www.gnome-look.org/p/1214931/
# Icons tela black dark
# https://www.gnome-look.org/p/1279924/

# extensions
# Emoji Selector
# Panel World Clock lite
# Ubuntu appindicators
# Ubuntu dock
# Unite
# User themes