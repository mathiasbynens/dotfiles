#
# Defines Ruby on Rails aliases.
#
# Authors:
#   Robby Russell <robby@planetargon.com>
#   Jake Bell <jake.b.bell@gmail.com>
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# Load dependencies.
pmodload 'ruby'

# Return if requirements are not found.
if (( ! $+commands[bundle] )); then
  return 1
fi

#
# Aliases
#

alias ror='bundle exec rails'
alias rorc='bundle exec rails console'
alias rordc='bundle exec rails dbconsole'
alias rordm='bundle exec rake db:migrate'
alias rordM='bundle exec rake db:migrate db:test:clone'
alias rordr='bundle exec rake db:rollback'
alias rorg='bundle exec rails generate'
alias rorl='tail -f "$(ruby-app-root)/log/development.log"'
alias rorlc='bundle exec rake log:clear'
alias rorp='bundle exec rails plugin'
alias rorr='bundle exec rails runner'
alias rors='bundle exec rails server'
alias rorsd='bundle exec rails server --debugger'
alias rorx='bundle exec rails destroy'
