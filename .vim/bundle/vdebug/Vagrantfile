# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  # Use Debian 7 64-bit as our operating system, same as production
  config.vm.box = "debian/wheezy7.6"
  config.vm.box_url = "https://github.com/jose-lpa/packer-debian_7.6.0/releases/download/1.0/packer_virtualbox-iso_virtualbox.box"

  # Configure the virtual machine to use 1GB of RAM
  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--memory", "1024"]
  end

  # Forward the vdebug server port to the host
  config.vm.network :forwarded_port, guest: 9000, host: 9000
  config.vm.network :forwarded_port, guest: 5900, host: 5901

  # Use a shell script to provision
  config.vm.provision :shell, path: "bootstrap.sh"
end
