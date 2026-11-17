#!/usr/bin/env bash

# Setup Visual Studio Code:
# - Ensures `code` CLI is available in PATH across macOS and Linux
# - Symlinks settings.json and keybindings.json (compatible with macOS Application Support)
# - Idempotently installs required VS Code extensions (including Antigravity)

set -eo pipefail

SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SOURCE_DIR/lib/os.sh"

echo "💻 Setting up Visual Studio Code..."

# ------------------------------------------------------------------------------
# 1. Ensure `code` CLI is available
# ------------------------------------------------------------------------------
ensure_code_cli() {
  if command -v code &>/dev/null; then
    echo "✅ 'code' CLI is available: $(which code)"
    return 0
  fi

  # On macOS, if the GUI app is installed but 'code' CLI isn't in PATH, symlink it to ~/.local/bin/code
  if is_macos; then
    local mac_code_bin="/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
    if [[ -f "$mac_code_bin" ]]; then
      echo "🔗 Symlinking macOS VS Code CLI to ~/.local/bin/code..."
      mkdir -p "$HOME/.local/bin"
      ln -sf "$mac_code_bin" "$HOME/.local/bin/code"
      export PATH="$HOME/.local/bin:$PATH"
    fi
  fi

  if command -v code &>/dev/null; then
    echo "✅ 'code' CLI is now available: $(which code)"
    return 0
  fi

  echo "ℹ️  Visual Studio Code is not installed (or 'code' is not in PATH)."
  echo "   Install it via brew.sh (macOS) or apps-linux.sh (Linux) first."
  return 1
}


# ------------------------------------------------------------------------------
# 2. Sync Settings and Keybindings
# ------------------------------------------------------------------------------
sync_configs() {
  local config_source="$SOURCE_DIR/home/.config/Code/User"

  if is_macos; then
    local mac_user_dir="$HOME/Library/Application Support/Code/User"
    mkdir -p "$mac_user_dir"

    for file in settings.json keybindings.json; do
      local src="$config_source/$file"
      local dest="$mac_user_dir/$file"

      if [[ -f "$src" ]]; then
        if [[ -f "$dest" && ! -L "$dest" ]]; then
          echo "📦 Backing up existing macOS $file to ${dest}.backup..."
          mv "$dest" "${dest}.backup"
        fi
        ln -sf "$src" "$dest"
        echo "  [✓] Linked $file -> $mac_user_dir/$file"
      fi
    done
  elif is_linux; then
    local linux_user_dir="$HOME/.config/Code/User"
    mkdir -p "$linux_user_dir"

    for file in settings.json keybindings.json; do
      local src="$config_source/$file"
      local dest="$linux_user_dir/$file"

      if [[ -f "$src" && ! -e "$dest" ]]; then
        ln -sf "$src" "$dest"
        echo "  [✓] Linked $file -> $linux_user_dir/$file"
      fi
    done
  fi
}

# ------------------------------------------------------------------------------
# 3. Idempotently Install Extensions
# ------------------------------------------------------------------------------
install_extensions() {
  if ! command -v code &>/dev/null; then
    echo "ℹ️  Skipping extension installation because 'code' is not available."
    return 0
  fi

  local extensions=(
    "Google.google-antigravity"
    "ai-engineer-coach.ai-engineer-coach"
    "akamud.vscode-theme-onedark"
    "akamud.vscode-theme-onelight"
    "dbaeumer.vscode-eslint"
    "google.gemini-cli-vscode-ide-companion"
    "vitest.explorer"
  )

  echo "🔌 Checking and installing VS Code extensions..."
  local installed
  installed="$(code --list-extensions 2>/dev/null | tr '[:upper:]' '[:lower:]' || true)"

  for ext in "${extensions[@]}"; do
    local ext_lower
    ext_lower="$(echo "$ext" | tr '[:upper:]' '[:lower:]')"
    if echo "$installed" | grep -qx "$ext_lower"; then
      echo "  [✓] $ext is already installed"
    else
      echo "  [+] Installing $ext..."
      code --install-extension "$ext" --force || echo "  [!] Failed to install $ext"
    fi
  done
}

ensure_code_cli || true
sync_configs
install_extensions

echo "✨ Visual Studio Code setup completed!"
