###################################################
#                     MY STUFF                    #
###################################################
jdk() {
	version=$1
    export JAVA_HOME=$(/usr/libexec/java_home -v"$version");
    java -version
 }


for file in ~/.{path,aliases,functions,extra}; do
	[ -r "$file" ] && [ -f "$file" ] && source "$file";

    # Local version of file
    local="${file}.local"
	[ -r "$local" ]  && [ -f "$local" ] && source "$local";
done;
unset file;

# Setup directory colors
eval `gdircolors -b ~/dircolors-solarized/dircolors.ansi-light`


export PATH=/usr/local/opt/gnu-sed/libexec/gnubin:~/.local/bin:$PATH
export PATH=$PATH:$HOME/workspace/commure/bin
export PATH=$PATH:$HOME/workspace/commure/tools/sebastian
export fend="~/workspace/commure"

# virtualenvwrapper
export WORKON_HOME=$HOME/.virtualenvs   # Optional
export PROJECT_HOME=$HOME/dev_python     # Optional
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
export VIRTUALENVWRAPPER_VIRTUALENV=/usr/local/bin/virtualenv
source /usr/local/bin/virtualenvwrapper.sh

## Source the functions directory
#if [ -d ~/.functions ]; then
#    for F in ~/.functions/*; do
#        source $F
#    done
#fi
