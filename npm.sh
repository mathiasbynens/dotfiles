#!/usr/bin/env bash

installed_packages=$(npm list --global --depth=0 | tail -n +2 | awk '{print $2}' | sed -n -r 's/^(.*)@.*$/\1/p')

is-installed() {
	local pkg=$1;
	for installed_pkg in $installed_packages; do
		[[ $installed_pkg == $pkg ]] && return 0;
	done
	return 1;
}

npm-install() {
	local pkg=$1;
	is-installed "$pkg" && echo "$pkg is already installed." || npm i -g "$pkg@latest";
}

npm-install "trash-cli"
