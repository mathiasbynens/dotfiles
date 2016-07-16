#!/usr/local/env bash

# This file will prompt the user for input and build the .extra file
# The .extra file will hold tmux & possibly other redentials

echo "Hi,"
echo "\tThis program will promopt you for some information, and use your responses to build some configurations for you."
echo
echo "Please enter a tmux alias:"
read tmux_alias
echo
echo "Please enter a default tmux session name"
echo
read tmux_session

rm ~/.extra 2> /dev/null

cat << EOT >> ~/.extra
# This file contains additional configurations
alias $tmux_alias="tmux a -t $tmux_session || tmux new -s $tmux_session"

