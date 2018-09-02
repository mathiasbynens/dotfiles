function cleanBrewCache {
    brew cleanup
    rm -f -r /Library/Caches/Homebrew/*
}

if ! brew help > /dev/null; then
    echo "Missing homebrew, let's install it"
    # ask password upfront
    sudo -v

    #Install Homebrew
    /usr/bin/ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    brew update
    brew upgrade

    # deactive OSX GateKeeper
    sudo spctl --master-disable
      # The package is not installed
fi

