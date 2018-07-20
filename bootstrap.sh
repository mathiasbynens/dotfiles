#!/usr/bin/env bash

# Ensure we are using the most up-to-date version
git pull origin master;

currentDirectory=$(dirname $0)

if [[ ! -f bootstrap.sh ]]; then
	echo "Bootstrap must be run from dotfiles directory ..."
	exit 1
fi

dir=~/dotfiles
cat extras/dougie-bootstrap

cd "$(dirname "${BASH_SOURCE}")";

# Enable this if I need to check if this is being run as sudo
#if [[ "$EUID" -ne 0 ]]; then
#	echo "Please run this script with sudo or root user ..."
#	exit 1
#fi

successfully() {
	$* || (echo "failed" 1>&2 && exit 1)
}

fancy_echo() {
	echo "$1"
}

exe() { echo "\$ $@" ; "$@" ; }

function installApps() {
	sudo apt-get install -y \
		curl \
		git \
		vim \
		rsync \
        ssh

	cp extras/.bash* ~/
}

function doIt() {
    # Check for Windows Ubuntu
    if [[ $(cat /proc/version | grep Microsoft) ]]; then
        echo -ne "\nEnter home directory (if installing on windows) or press enter if none: "
        read windowsDir
        windowsHome=/mnt/c/Users/$windowsDir
        
        if [[ ! -d "$windowsHome" ]]; then
            echo "$windowsHome does not exist ... "
            exit 1
        fi
        echo -e "Creating link to $windowsHome ...\n"
        exe ln -s $windowsHome ~/$windowsDir
        echo "Copying hyper properties ..."
        exe cp ./extras/.hyper.js $windowsHome
        echo ""
    fi 

    if [[ $operating_sys == "nix" ]]; then
        installApps;
    fi

    rsync --filter="merge rsync-filter" -ah --no-perms . ~;
    
    #source ~/.bash_profile;

    echo "Installing oh-my-zsh ..."
    successfully sudo apt-get install zsh
    successfully curl -L https://raw.githubusercontent.com/robbyrussell/oh-my-zsh/master/tools/install.sh | bash
    
    echo -e "\nInstalling powerline-fonts ..."
    currDir=`pwd`
    cd powerline-fonts
    ./install.sh
    cd $currDir		
    
    echo -e "\nUpdating ~/.bashrc to run oh-my-zsh ..."
    cat > $HOME/.bashrc <<EOF
if test -t 1; then
# ...start zsh
exec zsh
fi
EOF
    if ! grep -q dougie_profile $HOME/.zshrc ; then	
        echo "Updating .zshrc ..."
    cat >> ${HOME}/.zshrc <<EOF
if [[ -f "\${HOME}/.dougie_profile" ]]; then
source \${HOME}/.dougie_profile
fi
EOF
    fi
    if ! grep -q DEFAULT_USER $HOME/.zshrc ; then	
        echo "Updating DEAFULT_USER in .zshrc ..."
    cat >> ${HOME}/.zshrc <<EOF
DEFAULT_USER="\$USER"
EOF
    fi
    sed -i 's/ZSH_THEME=.*/ZSH_THEME=dracula/' $HOME/.zshrc
    
    ln -fs $dir/dracula/dracula-zsh/dracula.zsh-theme ~/.oh-my-zsh/themes/dracula.zsh-theme

    if [[ ! -d ~/.oh-my-zsh/custom/plugins/zsh-autosuggestions ]]; then 
        git clone https://github.com/zsh-users/zsh-autosuggestions.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
        else
            echo "zsh-autosuggestions already installed ..."
    fi
    
    if [[ ! -d ~/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting ]]; then 
        git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
        else
            echo "zsh-syntax-highlighting already installed ..."
    fi
    
    sed -i 's/plugins=.*/plugins=(git zsh-syntax-highlighting zsh-autosuggestions)/' $HOME/.zshrc

    chmod -R g-w,o-w ~/.oh-my-zsh/custom/plugins/
    
    # install Vundle if necessary
    if [[ ! -d ~/.vim/bundle/Vundle.vim ]]; then
        git clone https://github.com/VundleVim/Vundle.vim.git ~/.vim/bundle/Vundle.vim
    fi

	# Additional handling if work flag was passed
	if [[ "$workflag" -eq "1" ]]; then
	    echo "Using .extra-work"
	    successfully cp ./extras/.work-extra ~/.extra
	fi
}

workflag=""
forceflag=""

case "$(uname -s)" in
   Darwin)
     #echo 'Mac OS X'
	 operating_sys='mac'
     ;;
   Linux)
     #echo 'Linux'
	 operating_sys='nix'
     ;;
   CYGWIN*|MINGW*|MSYS*)
     #echo 'MS Windows'
	 operating_sys='win'
     ;;
   *)
	 exit 1
     ;;
esac


while getopts "fwh" opt; do
  case $opt in
    f)
        echo "-f was triggered" >&2
        forceflag=1
        ;;
    w)
        echo "-w was triggered" >&2
        workflag=1
        ;;
	h)
		echo "Usage: bootstrap.sh [-h] [-w] [-f]"
		exit 1
		;;
    \?)
        echo "Invalid option" >&2
        exit 1
        ;;
    :)
        echo "Option -$OPTARG requires an argument." >&2
        exit 1
        ;;
  esac
done


if [[ $forceflag -eq 1 ]]; then
	doIt;
else
	read -p "This may overwrite existing files in your home directory. Are you sure? (y/n) " -n 1;
	echo "";
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		echo -e "Initializing submodules...\n"
		git submodule update --init

		# Backup the current dotfiles
		DATE=$(date +"%Y%m%d-%H%M")
		olddir=~/dotfiles-$DATE.old
		echo "re-creating backup directory [$olddir]"
		if [[ -d "$olddir" ]]; then
			rm -rf $olddir
			mkdir -p $olddir
		else
			mkdir -p $olddir
		fi

		echo "Backing up original files..."
		find ~ -maxdepth 1 -name ".[^.]*" -exec echo "backing up {} ..." \; -exec cp -rf "{}" $olddir \;
		echo ""
		doIt;
	fi;
fi;

echo -e "\nBoostrapping complete, please exit the shell ..."

unset doIt;
