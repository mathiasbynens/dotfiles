# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

Fork of [mathiasbynens/dotfiles](https://github.com/mathiasbynens/dotfiles). Shell config files are synced to `$HOME` via rsync.

## Common Commands

```bash
./bootstrap.sh        # Sync dotfiles to ~ (shows diff, prompts before overwrite)
./brew.sh             # Install Homebrew formulae (run on new Mac setup)
./.macos              # Apply macOS system preferences
```

## File Structure

- **Shell config**: `.bash_profile`, `.zshrc`, `.bashrc` - entry points that source other files
- **Sourced by shell**: `.path`, `.exports`, `.aliases`, `.functions`, `.extra` (in that order)
- **`.extra`**: Local overrides not committed (git credentials, machine-specific config)
- **`.path`**: Extend `$PATH` without forking
- **`init/`**: Editor/terminal themes (Sublime, iTerm, Terminal.app, Spectacle)

## Shell Loading Order

Both bash and zsh source: `~/.path` → `~/.bash_prompt` → `~/.exports` → `~/.aliases` → `~/.functions` → `~/.extra`

## Notes

- zsh uses [Pure prompt](https://github.com/sindresorhus/pure) (requires manual install: `git clone https://github.com/sindresorhus/pure.git ~/.zsh/pure`)
- Completion depends on Homebrew's bash-completion2
