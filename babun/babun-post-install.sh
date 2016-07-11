successfully() {
	$* || (echo "\nfailed" 1>&2 && exit 1)
}

fancy_echo() {
	echo "\n$1"
}

fancy_echo "Updating babun"
	successfully pact update

fancy_echo "Updating babun HOME ~/.zshrc"
	#successfully curl -k https://raw.githubusercontent.com/joshball/dot-files/master/files/babun-home/.zshrc -o ~/.zshrc
