#!/usr/bin/env bash

# Interactive dotfiles installer.
# Can be run directly from a cloned repo (`./install.sh`) or bootstrapped on a
# fresh machine via:
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/melledijkstra/dotfiles/main/install.sh)"

set -eo pipefail

DOTFILES_REPO="${DOTFILES_REPO:-https://github.com/melledijkstra/dotfiles.git}"
DOTFILES_DIR="${DOTFILES:-$HOME/projects/dotfiles}"

# ------------------------------------------------------------------------------
# 1. Self-Bootstrap (when piped via curl or run outside the cloned repository)
# ------------------------------------------------------------------------------
SCRIPT_DIR=""
if [[ -n "${BASH_SOURCE[0]:-}" && -f "${BASH_SOURCE[0]}" ]]; then
  SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
fi

if [[ -z "$SCRIPT_DIR" || ! -f "$SCRIPT_DIR/lib/os.sh" ]]; then
  echo "🚀 Bootstrapping dotfiles onto this machine..."
  OS_NAME="$(uname -s)"

  if [[ "$OS_NAME" == "Darwin" ]]; then
    if ! xcode-select -p &>/dev/null; then
      echo "🛠️  Installing Xcode Command Line Tools (required for git)..."
      xcode-select --install || true
      echo "⏳ Waiting for Xcode Command Line Tools installation to finish..."
      until xcode-select -p &>/dev/null; do
        sleep 5
      done
    fi
  elif [[ "$OS_NAME" == "Linux" ]]; then
    if ! command -v git &>/dev/null || ! command -v curl &>/dev/null; then
      echo "📦 Installing git and curl via apt..."
      sudo apt update
      sudo apt install -y git curl
    fi
  else
    echo "❌ Error: Unsupported OS ($OS_NAME). Only macOS and Linux (Ubuntu/Debian) are supported."
    exit 1
  fi

  if [[ ! -d "$DOTFILES_DIR/.git" ]]; then
    echo "📥 Cloning dotfiles repository into $DOTFILES_DIR..."
    mkdir -p "$(dirname "$DOTFILES_DIR")"
    git clone "$DOTFILES_REPO" "$DOTFILES_DIR"
  fi

  echo "➡️  Handing off to local installer in $DOTFILES_DIR..."
  exec bash "$DOTFILES_DIR/install.sh"
fi

# ------------------------------------------------------------------------------
# 2. Local Repository Setup
# ------------------------------------------------------------------------------
SOURCE_DIR="$SCRIPT_DIR"
cd "$SOURCE_DIR"

source "$SOURCE_DIR/lib/os.sh"

# OS Validation
if ! is_macos && ! is_linux; then
  echo "❌ Error: This dotfiles setup only supports macOS and Linux (Ubuntu)."
  echo "Detected OS: $(get_os)"
  echo "Aborting installation."
  exit 1
fi

if git rev-parse --is-inside-work-tree &>/dev/null; then
  echo "🌐 Pulling latest changes from GitHub..."
  git pull --ff-only origin main 2>/dev/null || echo "ℹ️  Skipping git pull (local branch or uncommitted changes present)."
fi

# ------------------------------------------------------------------------------
# 3. Upfront Interactive Selection
# ------------------------------------------------------------------------------
echo ""
echo "🚀 Dotfiles Installation for $(get_os)"
echo "--------------------------------------------------------"
echo "  [✓] Core prerequisites (git, curl, zsh, stow, Oh My Zsh) [Required]"

RUN_BREW=0
RUN_APPS_MACOS=0
RUN_APT=0
RUN_APPS_LINUX=0
RUN_BOOTSTRAP=0
RUN_VSCODE=0
RUN_SYNC_REPOS=0
RUN_MACOS=0
RUN_UBUNTU=0

if is_macos; then
  if ask_yes_no "📦 Install/Upgrade Homebrew packages (brew.sh)?"; then
    RUN_BREW=1
  fi
  if ask_yes_no "🖥️  Install macOS applications & dev tools (apps-macos.sh)?"; then
    RUN_APPS_MACOS=1
  fi
elif is_linux; then
  if ask_yes_no "📦 Install/Upgrade Ubuntu CLI packages (apt.sh)?"; then
    RUN_APT=1
  fi
  if ask_yes_no "🖥️  Install Linux applications & dev tools (apps-linux.sh)?"; then
    RUN_APPS_LINUX=1
  fi
fi

if ask_yes_no "🔗 Sync dotfiles to home directory (bootstrap.sh)?"; then
  RUN_BOOTSTRAP=1
fi

if ask_yes_no "💻 Setup VS Code extensions & settings (vscode.sh)?"; then
  RUN_VSCODE=1
fi

if ask_yes_no "📂 Clone/update development repositories (sync-repos)?"; then
  RUN_SYNC_REPOS=1
fi

if is_macos; then
  if ask_yes_no "💻 Apply macOS system defaults (macos.sh)?"; then
    RUN_MACOS=1
  fi
elif is_ubuntu && ! is_wsl; then
  if ask_yes_no "💻 Apply Ubuntu desktop defaults (ubuntu.sh)?"; then
    RUN_UBUNTU=1
  fi
fi

echo ""
echo "📋 Summary of planned actions:"
echo "   • Ensure core prerequisites (core.sh)"
[[ $RUN_BREW -eq 1 ]]       && echo "   • Install/upgrade Homebrew packages (brew.sh)"
[[ $RUN_APPS_MACOS -eq 1 ]] && echo "   • Install macOS apps & dev tools (apps-macos.sh)"
[[ $RUN_APT -eq 1 ]]        && echo "   • Install/upgrade Ubuntu packages (apt.sh)"
[[ $RUN_APPS_LINUX -eq 1 ]] && echo "   • Install Linux GUI apps & dev tools (apps-linux.sh)"
[[ $RUN_BOOTSTRAP -eq 1 ]]  && echo "   • Back up conflicts & symlink dotfiles to \$HOME (bootstrap.sh)"
[[ $RUN_VSCODE -eq 1 ]]     && echo "   • Configure VS Code extensions & settings (vscode.sh)"
[[ $RUN_SYNC_REPOS -eq 1 ]] && echo "   • Clone/update development repositories (sync-repos)"
[[ $RUN_MACOS -eq 1 ]]      && echo "   • Apply macOS system defaults (macos.sh)"
[[ $RUN_UBUNTU -eq 1 ]]     && echo "   • Apply Ubuntu desktop defaults (ubuntu.sh)"
echo ""

if ! ask_yes_no "Proceed with installation?"; then
  echo "Installation cancelled."
  exit 0
fi

# ------------------------------------------------------------------------------
# 4. Keep sudo Alive During Execution
# ------------------------------------------------------------------------------
if command -v sudo &>/dev/null; then
  echo "🔐 Requesting administrator privileges (if needed)..."
  sudo -v
  ( while true; do sudo -n true; sleep 60; kill -0 "$$" || exit; done ) 2>/dev/null &
  SUDO_KEEPALIVE_PID=$!
  trap 'kill "$SUDO_KEEPALIVE_PID" 2>/dev/null || true' EXIT
fi

# ------------------------------------------------------------------------------
# 5. Execute Selected Steps
# ------------------------------------------------------------------------------
echo ""
bash "$SOURCE_DIR/core.sh"

if [[ $RUN_BREW -eq 1 ]]; then
  echo ""
  bash "$SOURCE_DIR/brew.sh"
fi

if [[ $RUN_APPS_MACOS -eq 1 ]]; then
  echo ""
  bash "$SOURCE_DIR/apps-macos.sh"
fi

if [[ $RUN_APT -eq 1 ]]; then
  echo ""
  bash "$SOURCE_DIR/apt.sh"
fi

if [[ $RUN_APPS_LINUX -eq 1 ]]; then
  echo ""
  bash "$SOURCE_DIR/apps-linux.sh"
fi

if [[ $RUN_BOOTSTRAP -eq 1 ]]; then
  echo ""
  bash "$SOURCE_DIR/bootstrap.sh" --force
fi

if [[ $RUN_VSCODE -eq 1 ]]; then
  echo ""
  bash "$SOURCE_DIR/vscode.sh"
fi

if [[ $RUN_SYNC_REPOS -eq 1 ]]; then
  echo ""
  bash "$SOURCE_DIR/home/bin/sync-repos"
fi

if [[ $RUN_MACOS -eq 1 ]]; then
  echo ""
  bash "$SOURCE_DIR/macos.sh"
fi

if [[ $RUN_UBUNTU -eq 1 ]]; then
  echo ""
  bash "$SOURCE_DIR/ubuntu.sh"
fi

echo ""
echo "✨ Installation steps completed!"
echo "Note: Some changes may require a logout or restart to take effect."
