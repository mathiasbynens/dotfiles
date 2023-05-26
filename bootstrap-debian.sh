sudo apt update
sudo apt install htop iftop zsh neofetch build-essential

# Powerline Fonts
sudo apt-get install fonts-powerline

sudo apt install jo tmate hexyl glances

# Install go packages
go install github.com/rs/curlie@latest # httpie / curl replacement
CGO_ENABLED=0 go install github.com/liamg/traitor/cmd/traitor@latest # password exfiltration
