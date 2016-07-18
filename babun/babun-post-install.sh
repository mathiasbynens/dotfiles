successfully() {
	$* || (echo "\nfailed" 1>&2 && exit 1)
}

fancy_echo() {
	echo "\n$1"
}

fancy_echo "Updating babun"
	successfully pact update

fancy_echo "Updating babun HOME"
	#successfully curl -k https://raw.githubusercontent.com/joshball/dot-files/master/files/babun-home/.zshrc -o ~/.zshrc
    # Need to rsync the necessary files from the babun folder over to the HOME directory
    #   vim config
    #   mintty.rc
    #   zshrc
    #   Anything else I'm missing...
	successfully rsync -azh --include='.minttyrc' --include='.zshrc' ~
    successfully rsync -azh --include='../.extra-orig' ~

fancy_echo "Updating VIM Configuration"
    successfully rsync -azh --include='../.vim.*' ~

fancy_echo "Retrieving powerline fonts"
	successfully curl -k https://github.com/powerline/fonts.git -o ~/powerline-fonts


echo "babun bootstrap complete!"
echo "You will need to install the DejaVu Sans Mono for Powerline font from the ~/powerline-fonts directory"