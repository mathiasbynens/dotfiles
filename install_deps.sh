# https://rvm.io
# rvm for the rubiess
curl -L https://get.rvm.io | bash -s stable --ruby

# homebrew!
# you need the code CLI tools YOU FOOL.
ruby <(curl -fsSkL raw.github.com/mxcl/homebrew/go)

# https://github.com/rupa/z
# z, oh how i love you
curl https://raw.github.com/rupa/z/master/z.sh > ~/bin/z.sh
chmod +x ~/bin/z.sh
# also consider moving over your current .z file if possible. it's painful to rebuild :)

# CLI syntax highlight
sudo easy_install Pygments
