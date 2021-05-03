# Access as root
sudo -u

apt-get update

# install tools
sudo apt-get install \
   curl \
   coreutils \
   net-tools \
   apt-transport-https \
   ca-certificates \
   software-properties-common \
   ubuntu-restricted-extras \
   gnome-tweak-tool \
   gnome-shell-extensions \
   network-manager-openvpn-gnome \
   libxss1 \
   libappindicator1 \
   libindicator7 \
   vim \
   nfs-common \
   nfs-kernel-server \
   psensor \
   -y

# install cafeine repository
# sudo add-apt-repository ppa:caffeine-developers/ppa

# install stacer monitor repository
# sudo add-apt-repository ppa:oguzhaninan/stacer

# install enpass repository
echo "deb http://repo.sinew.in/ stable main" > sudo tee /etc/apt/sources.list.d/enpass.list
wget -O - https://dl.sinew.in/keys/enpass-linux.key | apt-key add -

# install peek (screnshoot gif) repository
sudo add-apt-repository ppa:peek-developers/stable

# Install NVM
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.38.0/install.sh | bash
export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" # This loads nvm

# install docker repository
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo apt-key fingerprint 0EBFCD88
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

sudo apt remove cmdtest
sudo apt-get update

sudo apt-get install -y \
   git \
   sublime-text \
   shutter \
   peek \
   enpass \
   snapd

# docker
apt-get install docker-ce -y
groupadd docker
usermod -aG docker germano

systemctl enable docker
systemctl disable docker

sudo curl -L "https://github.com/docker/compose/releases/download/1.29.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
docker-compose --version

docker run hello-world

chown germano:germano /home/germano/.docker -R
chmod g+rwx "/home/germano/.docker" -R

# ctop
sudo wget https://github.com/bcicen/ctop/releases/download/v0.7.1/ctop-0.7.1-linux-amd64 -O /usr/local/bin/ctop
sudo chmod +x /usr/local/bin/ctop

# setup bash prompt
(cd /tmp && git clone --depth 1 --config core.autocrlf=false https://github.com/twolfson/sexy-bash-prompt && cd sexy-bash-prompt && make install) && source ~/.bashrc

#  node
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.35.0/install.sh | bash

. ./google-fonts.sh
. ./snaps.sh