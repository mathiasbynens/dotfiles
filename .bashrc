[ -n "$PS1" ] && source ~/.bash_profile;

# added by travis gem
[ -f /Users/zwang/.travis/travis.sh ] && source /Users/zwang/.travis/travis.sh

#export PATH="$HOME/.yarn/bin:$HOME/.config/yarn/global/node_modules/.bin:$PATH"

# tabtab source for serverless package
# uninstall by removing these lines or running `tabtab uninstall serverless`
[ -f /Users/zwang/Projects/localz/hiring/serverless-gps-tracking/node_modules/tabtab/.completions/serverless.bash ] && . /Users/zwang/Projects/localz/hiring/serverless-gps-tracking/node_modules/tabtab/.completions/serverless.bash
# tabtab source for sls package
# uninstall by removing these lines or running `tabtab uninstall sls`
[ -f /Users/zwang/Projects/localz/hiring/serverless-gps-tracking/node_modules/tabtab/.completions/sls.bash ] && . /Users/zwang/Projects/localz/hiring/serverless-gps-tracking/node_modules/tabtab/.completions/sls.bash
# tabtab source for slss package
# uninstall by removing these lines or running `tabtab uninstall slss`
[ -f /Users/zwang/Projects/localz/hiring/serverless-gps-tracking/node_modules/tabtab/.completions/slss.bash ] && . /Users/zwang/Projects/localz/hiring/serverless-gps-tracking/node_modules/tabtab/.completions/slss.bash
# Add RVM to PATH for scripting. Make sure this is the last PATH variable change.
export PATH="$PATH:$HOME/.rvm/bin"
