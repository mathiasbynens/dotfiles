for file in ~/.{path,aliases,functions}; do
	[ -r "$file" ] && [ -f "$file" ] && source "$file";

    # Local version of file
    local="${file}.local"
	[ -r "$local" ]  && [ -f "$local" ] && source "$local";
done;
unset file;

if [ -d ~/.functions ]; then
	for F in ~/.functions/*; do
		source $F
	done
fi

# mac specific
# Setup directory colors
if [[ "$OSTYPE" == "darwin*" ]]; then
    eval `gdircolors -b ~/dircolors-solarized/dircolors.ansi-light`
else
    eval `dircolors -b ~/dircolors-solarized/dircolors.ansi-light`
fi
# End mac specific

# virtualenvwrapper
export WORKON_HOME=$HOME/.virtualenvs   # Optional
export PROJECT_HOME=$HOME/dev_python     # Optional
export VIRTUALENVWRAPPER_PYTHON=/usr/local/bin/python3
export VIRTUALENVWRAPPER_VIRTUALENV=/usr/local/bin/virtualenv
source /usr/local/bin/virtualenvwrapper.sh
