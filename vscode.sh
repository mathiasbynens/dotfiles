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
    echo "✅ 'code' CLI is already available: $(which code)"
    return 0
  fi

  if is_macos; then
    local mac_code_bin="/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code"
    if [[ -f "$mac_code_bin" ]]; then
      echo "🔗 Symlinking macOS VS Code CLI to ~/.local/bin/code..."
      mkdir -p "$HOME/.local/bin"
      ln -sf "$mac_code_bin" "$HOME/.local/bin/code"
      export PATH="$HOME/.local/bin:$PATH"
    elif command -v brew &>/dev/null; then
      echo "📦 Installing Visual Studio Code via Homebrew..."
      brew install --cask visual-studio-code
      if [[ -f "$mac_code_bin" ]]; then
        mkdir -p "$HOME/.local/bin"
        ln -sf "$mac_code_bin" "$HOME/.local/bin/code"
        export PATH="$HOME/.local/bin:$PATH"
      fi
    fi
  elif is_linux; then
    echo "📦 Installing Visual Studio Code via apt..."
    sudo apt install -y wget gpg apt-transport-https
    wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /tmp/packages.microsoft.gpg
    sudo install -D -o root -g root -m 644 /tmp/packages.microsoft.gpg /usr/share/keyrings/microsoft.gpg
    rm -f /tmp/packages.microsoft.gpg
    echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/repos/code stable main" | sudo tee /etc/apt/sources.list.d/vscode.list > /dev/null
    sudo apt update
    sudo apt install -y code
  fi

  if ! command -v code &>/dev/null; then
    echo "⚠️  Warning: 'code' CLI is not found on PATH."
    echo "   If VS Code is already installed, ensure the 'code' command is in your PATH."
    return 1
  fi
  echo "✅ 'code' CLI is now available."
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
