# Access as root
sudo -u

apt-get update

# install tools
sudo apt-get install curl coreutils net-tools apt-transport-https ca-certificates software-properties-common ubuntu-restricted-extras gnome-tweak-tool tlp tlp-rdw thermald laptop-mode-tools indicator-cpufreq psensor -y

# install cafeine repository
sudo add-apt-repository ppa:caffeine-developers/ppa

# install stacer monitor repository
sudo add-apt-repository ppa:oguzhaninan/stacer

# install enpass repository
echo "deb http://repo.sinew.in/ stable main" >   /etc/apt/sources.list.d/enpass.list
wget -O - https://dl.sinew.in/keys/enpass-linux.key | apt-key add -

# install node repository
curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -
curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list


# install docker repository
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo apt-key fingerprint 0EBFCD88
sudo add-apt-repository \
   "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
   $(lsb_release -cs) \
   stable"

apt remove cmdtest
apt-get update

apt-get install nodejs yarn -y
apt-get install stacer -y
apt-get install enpass -y
apt-get install git-all -y

# docker
apt-get install docker-ce -y
groupadd docker
usermod -aG docker germano

systemctl enable docker
systemctl disable docker

curl -L https://github.com/docker/compose/releases/download/1.20.1/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
docker-compose --version

docker run hello-world

chown germano:germano /home/germano/.docker -R
chmod g+rwx "/home/germano/.docker" -R

# ctop
sudo wget https://github.com/bcicen/ctop/releases/download/v0.7.1/ctop-0.7.1-linux-amd64 -O /usr/local/bin/ctop
sudo chmod +x /usr/local/bin/ctop
