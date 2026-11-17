#!/usr/bin/env bash

# Install macOS applications and CLI tools not managed by Homebrew

set -eo pipefail

SOURCE_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
source "$SOURCE_DIR/lib/os.sh"

if ! is_macos; then
  echo "❌ Error: apps-macos.sh is only intended for macOS systems."
  exit 1
fi

echo "🚀 Installing standalone macOS applications & tools..."

# 1. Antigravity CLI (agy)
if command -v agy &>/dev/null; then
  echo "✅ Antigravity CLI (agy) is already installed."
else
  echo "🤖 Installing Antigravity CLI (agy)..."
  curl -fsSL https://antigravity.google/cli/install.sh | bash
fi

echo "✨ macOS applications and tools setup completed!"
