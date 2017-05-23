#/bin/bash -e
# Hostname
hostname vdebug
echo vdebug > /etc/hostname

# Set password to 'vdebug'
echo "vagrant:vdebug" | chpasswd

# Allow passwordless sudo
if grep "vagrant" /etc/sudoers
then
    echo "vagrant group already a sudoer"
else
    echo "%vagrant ALL=(ALL) NOPASSWD:ALL"
fi

# Install packages
apt-get update
apt-get install locales-all git-core vim vim-nox php5 php5-cli php5-xdebug -y

# Fix locale
/usr/sbin/update-locale LANG=en_US LC_ALL=en_US

# Install ruby (http://blog.packager.io/post/101342252191/one-liner-to-get-a-precompiled-ruby-on-your-own)
curl -s https://s3.amazonaws.com/pkgr-buildpack-ruby/current/debian-7/ruby-2.1.5.tgz -o - | sudo tar xzf - -C /usr/local
gem install bundler

cat <<'EOF' >> /etc/php5/conf.d/*-xdebug.ini
xdebug.remote_enable=on
xdebug.remote_handler=dbgp
xdebug.remote_host=localhost
xdebug.remote_port=9000
EOF

cat <<'EOF' > /usr/local/bin/php-xdebug
#!/bin/bash
export XDEBUG_CONFIG="idekey=vdebug"
/usr/bin/env php "$@"
EOF

chmod +x /usr/local/bin/php-xdebug

cat <<EOF > /home/vagrant/.vimrc
set nocompatible
filetype off

"<Leader> key is ,
let mapleader=","

" Vundle init
set rtp+=~/.vim/bundle/Vundle.vim/

" Require Vundle
try
    call vundle#begin()
catch
    echohl Error | echo "Vundle is not installed." | echohl None
    finish
endtry

Plugin 'gmarik/Vundle.vim'
Plugin 'joonty/vdebug.git'

call vundle#end()

filetype plugin indent on
syntax enable

"{{{ Settings
set ttyscroll=0
set hidden
set history=1000
set ruler
set ignorecase
set smartcase
set title
set scrolloff=3
set backupdir=~/.vim-tmp,/tmp
set directory=~/.vim-tmp,/tmp
set wrapscan
set visualbell
set backspace=indent,eol,start
"Status line coolness
set laststatus=2
set showcmd
" Search things
set hlsearch
set incsearch " ...dynamically as they are typed.
" Folds
set foldmethod=marker
set wildmenu
set wildmode=list:longest,full
set nohidden
set shortmess+=filmnrxoOt
set viewoptions=folds,options,cursor,unix,slash
set virtualedit=onemore
set shell=bash\ --login
set nocursorcolumn
set nocursorline
syntax sync minlines=256
"Spaces, not tabs
set shiftwidth=4
set tabstop=4
set expandtab
" Line numbers
set relativenumber
"}}}
EOF

chown vagrant:vagrant /home/vagrant/.vimrc

# Do things as the vagrant user
sudo -u vagrant bash << EOF
mkdir -p /home/vagrant/.vim-tmp /home/vagrant/.vim/bundle
git clone https://github.com/gmarik/Vundle.vim.git ~/.vim/bundle/Vundle.vim
git clone https://github.com/joonty/vdebug.git ~/.vim/bundle/vdebug
cd /vagrant
bundle install
EOF
