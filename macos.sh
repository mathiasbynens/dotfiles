#!/usr/bin/env bash

set -euo pipefail

if [[ "$OSTYPE" != darwin* ]]; then
	echo "macos.sh is only supported on macOS." >&2
	exit 1
fi

if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
	C_RESET=$'\033[0m'
	C_BOLD=$'\033[1m'
	C_DIM=$'\033[2m'
	C_RED=$'\033[31m'
	C_GREEN=$'\033[32m'
	C_YELLOW=$'\033[33m'
	C_BLUE=$'\033[34m'
else
	C_RESET=""
	C_BOLD=""
	C_DIM=""
	C_RED=""
	C_GREEN=""
	C_YELLOW=""
	C_BLUE=""
fi

log_info() {
	printf '%s==>%s %s\n' "$C_BLUE" "$C_RESET" "$1"
}

log_success() {
	printf '%s==>%s %s\n' "$C_GREEN" "$C_RESET" "$1"
}

log_warn() {
	printf '%s==>%s %s\n' "$C_YELLOW" "$C_RESET" "$1"
}

log_error() {
	printf '%s==>%s %s\n' "$C_RED" "$C_RESET" "$1" >&2
}

log_section() {
	printf '\n%s%s%s\n' "$C_BOLD" "$1" "$C_RESET"
}

log_skip() {
	printf '%s->%s %s\n' "$C_DIM" "$C_RESET" "$1"
}

append_line_if_missing() {
	local line="$1"
	local file="$2"
	local header="${3:-}"

	if grep -qF "$line" "$file" 2>/dev/null; then
		return
	fi

	{
		printf '\n'
		if [[ -n "$header" ]]; then
			printf '%s\n' "$header"
		fi
		printf '%s\n' "$line"
	} >> "$file"
}

install_formula() {
	local formula="$1"

	if brew list --formula --versions "$formula" >/dev/null 2>&1; then
		log_skip "Already installed: ${formula}"
		return
	fi

	log_info "Installing formula: ${formula}"
	brew install "$formula"
	log_success "Installed formula: ${formula}"
}

install_formulas() {
	local formula

	for formula in "$@"; do
		install_formula "$formula"
	done
}

install_cask() {
	local cask="$1"
	local app_path="${2:-}"

	if brew list --cask --versions "$cask" >/dev/null 2>&1; then
		log_skip "Already installed cask: ${cask}"
		return
	fi

	if [[ -n "$app_path" && -d "$app_path" ]]; then
		log_warn "Skipping cask ${cask} because ${app_path} already exists."
		return
	fi

	log_info "Installing cask: ${cask}"
	brew install --cask "$cask"
	log_success "Installed cask: ${cask}"
}

install_casks() {
	local cask

	for cask in "$@"; do
		install_cask "$cask"
	done
}

ensure_brew_bash_shell() {
	local brew_bash="${BREW_PREFIX}/bin/bash"

	if ! grep -qF "$brew_bash" /etc/shells; then
		log_info "Adding ${brew_bash} to /etc/shells"
		echo "$brew_bash" | sudo tee -a /etc/shells >/dev/null
	fi

	if [[ "${SHELL:-}" != "$brew_bash" ]]; then
		log_info "Switching default shell to ${brew_bash}"
		chsh -s "$brew_bash"
	fi
}

configure_stats() {
	log_section "Configuring Stats"

	defaults write eu.exelban.Stats CPU_state -bool true
	defaults write eu.exelban.Stats GPU_state -bool true
	defaults write eu.exelban.Stats RAM_state -bool true
	defaults write eu.exelban.Stats Disk_state -bool true
	defaults write eu.exelban.Stats Network_state -bool true
	defaults write eu.exelban.Stats Battery_state -bool true
	defaults write eu.exelban.Stats Sensors_state -bool false
	defaults write eu.exelban.Stats Bluetooth_state -bool false
	defaults write eu.exelban.Stats CombinedModules -bool false
	defaults write eu.exelban.Stats update_interval -int 3
	defaults write eu.exelban.Stats CPU_widget -string "mini"
	defaults write eu.exelban.Stats RAM_widget -string "mini"
	defaults write eu.exelban.Stats Network_widget -string "speed"
	defaults write eu.exelban.Stats Battery_widget -string "percentage"
	defaults write eu.exelban.Stats SUEnableAutomaticChecks -bool true
	defaults write eu.exelban.Stats runAtLoginInitialized -bool true

	log_success "Configured Stats"
}

configure_little_snitch_mini() {
	log_section "Configuring Little Snitch Mini"
	defaults write at.obdev.LittleSnitchMini SUEnableAutomaticChecks -bool true
	log_success "Configured Little Snitch Mini"
}

# On Apple Silicon, /usr/local Homebrew may be a stale Intel install from
# migration, or it may be intentionally kept for Rosetta-only formulae.
if [[ "$(uname -m)" == "arm64" && -x /usr/local/bin/brew ]]; then
	if [[ "${REMOVE_INTEL_HOMEBREW:-0}" == "1" ]]; then
		log_warn "Detected Intel Homebrew at /usr/local on Apple Silicon; removing it."
		NONINTERACTIVE=1 /bin/bash -c \
			"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/uninstall.sh)" \
			-- --path=/usr/local --force
	else
		log_warn "Detected Intel Homebrew at /usr/local; leaving it in place."
		log_skip "Set REMOVE_INTEL_HOMEBREW=1 to remove it during bootstrap."
	fi
fi

# Resolve Homebrew even when it exists but is not yet on PATH.
if command -v brew >/dev/null 2>&1; then
	BREW_BIN="$(command -v brew)"
elif [[ -x /opt/homebrew/bin/brew ]]; then
	BREW_BIN="/opt/homebrew/bin/brew"
elif [[ -x /usr/local/bin/brew ]]; then
	BREW_BIN="/usr/local/bin/brew"
else
	log_section "Homebrew"
	log_info "Installing Homebrew"
	/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

	if [[ -x /opt/homebrew/bin/brew ]]; then
		BREW_BIN="/opt/homebrew/bin/brew"
	elif [[ -x /usr/local/bin/brew ]]; then
		BREW_BIN="/usr/local/bin/brew"
	else
		log_error "Homebrew installation not found."
		exit 1
	fi
fi

# Persist Homebrew shellenv in ~/.bash_profile so future shells have it.
SHELLENV_LINE="eval \"\$(${BREW_BIN} shellenv)\""
append_line_if_missing "$SHELLENV_LINE" "${HOME}/.bash_profile" "# Homebrew"

# Use Homebrew in the current shell without sourcing the full profile.
eval "$("$BREW_BIN" shellenv)"

# Fix Homebrew permissions for multi-user setups.
# When multiple admin users share a Mac, /opt/homebrew must be group-writable
# by the "admin" group so any admin user can run brew.
fix_brew_permissions() {
	local brew_prefix
	brew_prefix="$(brew --prefix)"

	if [[ ! -w "$brew_prefix" ]]; then
		log_info "Fixing Homebrew permissions for multi-user setup"
		sudo chgrp -R admin "$brew_prefix"
		sudo chmod -R g+w "$brew_prefix"
		sudo find "$brew_prefix" -type d -exec chmod g+s {} +
		log_success "Homebrew permissions fixed"
	fi
}
fix_brew_permissions

log_section "Updating Homebrew"
brew update

log_section "Upgrading Installed Formulae"
brew upgrade

BREW_PREFIX="$(brew --prefix)"

export HOMEBREW_NO_INSTALL_CLEANUP=1
export HOMEBREW_NO_ENV_HINTS=1

gnu_formulae=(
	coreutils
	moreutils
	findutils
	gnu-sed
	bash
	bash-completion@2
	wget
	gnupg
	vim
	grep
	openssh
)

modern_cli_formulae=(
	ripgrep
	fd
	bat
	fzf
	eza
	jq
	gh
	git-delta
	htop
	tlrc
)

ctf_formulae=(
	aircrack-ng
	bfg
	binutils
	binwalk
	dns2tcp
	fcrackzip
	hydra
	john
	nmap
	pngcheck
	socat
	sqlmap
	tcpflow
	tcpreplay
	xz
)

other_formulae=(
	git
	git-lfs
	pinentry-mac
	ghostscript
	imagemagick
	lua
	pigz
	pv
	rename
	rlwrap
	ssh-copy-id
	tree
	vbindiff
	zopfli
	woff2
	shfmt
)

version_manager_formulae=(
	jenv
	pyenv
	rbenv
	nvm
)

macos_formulae=(
	stats
	btop
)

macos_casks=(
	malwarebytes
	rectangle
	appcleaner
)

log_section "GNU Tools"
install_formulas "${gnu_formulae[@]}"
ln -sf "${BREW_PREFIX}/bin/gsha256sum" "${BREW_PREFIX}/bin/sha256sum"

ensure_brew_bash_shell

log_section "Modern CLI"
install_formulas "${modern_cli_formulae[@]}"

log_section "CTF Tools"
# Homebrew disabled tcptrace, so it is intentionally omitted here.
install_formulas "${ctf_formulae[@]}"

log_section "Other Tools"
install_formulas "${other_formulae[@]}"

log_section "Version Managers"
install_formulas "${version_manager_formulae[@]}"

log_section "AI Apps"
install_cask codex
install_cask claude "/Applications/Claude.app"

log_section "macOS Apps"
install_formulas "${macos_formulae[@]}"
install_casks "${macos_casks[@]}"

configure_stats
configure_little_snitch_mini

log_section "Cleanup"
brew cleanup
log_success "macOS bootstrap complete"
