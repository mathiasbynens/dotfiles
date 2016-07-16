#!/usr/bin/env bash

solarized_prompt=$(ls .solarized_prompt 2> /dev/null | wc -l)
smyck_prompt=$(ls .smyck_prompt 2> /dev/null | wc-l)

if [ $solarized_prompt = 0 ] && [ $smyck_prompt = 1 ]; then
        mv ~/.bash_prompt ~/.solarized_prompt
        mv ~/.smyck_prompt ~/.bash_prompt
elif [ $solarized_prompt = 1 ] && [ $smyck_prompt = 0 ]; then
        mv ~/.bash_prompt ~/.smyck_prompt
        mv ~/.solarized_prompt ~/.bash_prompt
else
        echo You are missing at least one prompt file.
        echo Run ~/dotfiles/bootstrap.sh