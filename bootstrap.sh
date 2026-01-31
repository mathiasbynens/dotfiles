#!/usr/bin/env bash

# Prevent script from being sourced
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
	echo "Error: This script should be executed, not sourced."
	echo "Use: ./bootstrap.sh instead of source bootstrap.sh"
	return 1
fi
cd "$(dirname "${BASH_SOURCE[0]}")"
git pull origin main

# Check if rsync is installed
if ! command -v rsync &>/dev/null; then
	echo "Error: rsync is required but not installed."

	echo " - Install from: https://brew.sh/"
	echo " - Then: brew install rsync"
	exit 1
fi

# Define excluded files/patterns
EXCLUDES=(
	".git*"
	".vscode"
	".DS_Store"
	".osx"
	"bootstrap.sh"
	"README.md"
	"LICENSE-MIT.txt"
	"brew.sh"
	"CLAUDE.md"
	"AGENTS.md"
)

# Build exclude parameters for rsync
EXCLUDE_PARAMS=""
for item in "${EXCLUDES[@]}"; do
	EXCLUDE_PARAMS="$EXCLUDE_PARAMS --exclude=$item"
done

# Show diffs before syncing
rsync -avhn --itemize-changes $EXCLUDE_PARAMS --out-format="%f" ./ "$HOME/"
echo ""

# For each file that would be transferred, show diff
while IFS= read -r file; do
	if [[ -f "$HOME/$file" && -f "$file" ]]; then
		echo "Differences in $file:"
		diff -u "$HOME/$file" "$file" | grep -v "^Only in" || echo "No differences"
		echo ""
	fi
done < <(rsync -avhn --itemize-changes $EXCLUDE_PARAMS --out-format="%f" ./ "$HOME/" | grep -v "/$" | grep -v "^sending" | grep -v "^sent" | grep -v "^total")

# Prompt for confirmation
read -p "This may overwrite existing files in your home directory. Proceed? (Y/n) " -n 1 -r
echo ""
if [[ -z $REPLY || $REPLY =~ ^[Yy]$ ]]; then
	rsync -av $EXCLUDE_PARAMS ./ "$HOME/"
	echo "Sync complete."

	# Source appropriate shell configuration
	if [ -n "$ZSH_VERSION" ]; then
		source "$HOME/.zshrc"
	elif [ -n "$BASH_VERSION" ]; then
		source "$HOME/.bash_profile"
	else
		echo "Unknown shell, please restart your terminal for changes to take effect."
	fi
else
	echo "Sync cancelled."
fi
