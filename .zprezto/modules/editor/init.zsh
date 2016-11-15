#
# Sets key bindings.
#
# Authors:
#   Sorin Ionescu <sorin.ionescu@gmail.com>
#

# Return if requirements are not found.
if [[ "$TERM" == 'dumb' ]]; then
  return 1
fi

#
# Options
#

# Beep on error in line editor.
setopt BEEP

#
# Variables
#

# Treat these characters as part of a word.
WORDCHARS='*?_-.[]~&;!#$%^(){}<>'

# Use human-friendly identifiers.
zmodload zsh/terminfo
typeset -gA key_info
key_info=(
  'Control'      '\C-'
  'ControlLeft'  '\e[1;5D \e[5D \e\e[D \eOd'
  'ControlRight' '\e[1;5C \e[5C \e\e[C \eOc'
  'Escape'       '\e'
  'Meta'         '\M-'
  'Backspace'    "^?"
  'Delete'       "^[[3~"
  'F1'           "$terminfo[kf1]"
  'F2'           "$terminfo[kf2]"
  'F3'           "$terminfo[kf3]"
  'F4'           "$terminfo[kf4]"
  'F5'           "$terminfo[kf5]"
  'F6'           "$terminfo[kf6]"
  'F7'           "$terminfo[kf7]"
  'F8'           "$terminfo[kf8]"
  'F9'           "$terminfo[kf9]"
  'F10'          "$terminfo[kf10]"
  'F11'          "$terminfo[kf11]"
  'F12'          "$terminfo[kf12]"
  'Insert'       "$terminfo[kich1]"
  'Home'         "$terminfo[khome]"
  'PageUp'       "$terminfo[kpp]"
  'End'          "$terminfo[kend]"
  'PageDown'     "$terminfo[knp]"
  'Up'           "$terminfo[kcuu1]"
  'Left'         "$terminfo[kcub1]"
  'Down'         "$terminfo[kcud1]"
  'Right'        "$terminfo[kcuf1]"
  'BackTab'      "$terminfo[kcbt]"
)

# Set empty $key_info values to an invalid UTF-8 sequence to induce silent
# bindkey failure.
for key in "${(k)key_info[@]}"; do
  if [[ -z "$key_info[$key]" ]]; then
    key_info[$key]='�'
  fi
done

#
# External Editor
#

# Allow command line editing in an external editor.
autoload -Uz edit-command-line
zle -N edit-command-line

#
# Functions
#

# Exposes information about the Zsh Line Editor via the $editor_info associative
# array.
function editor-info {
  # Clean up previous $editor_info.
  unset editor_info
  typeset -gA editor_info

  if [[ "$KEYMAP" == 'vicmd' ]]; then
    zstyle -s ':prezto:module:editor:info:keymap:alternate' format 'REPLY'
    editor_info[keymap]="$REPLY"
  else
    zstyle -s ':prezto:module:editor:info:keymap:primary' format 'REPLY'
    editor_info[keymap]="$REPLY"

    if [[ "$ZLE_STATE" == *overwrite* ]]; then
      zstyle -s ':prezto:module:editor:info:keymap:primary:overwrite' format 'REPLY'
      editor_info[overwrite]="$REPLY"
    else
      zstyle -s ':prezto:module:editor:info:keymap:primary:insert' format 'REPLY'
      editor_info[overwrite]="$REPLY"
    fi
  fi

  unset REPLY

  zle reset-prompt
  zle -R
}
zle -N editor-info

# Updates editor information when the keymap changes.
function zle-keymap-select {
  zle editor-info
}
zle -N zle-keymap-select

# Enables terminal application mode and updates editor information.
function zle-line-init {
  # The terminal must be in application mode when ZLE is active for $terminfo
  # values to be valid.
  if (( $+terminfo[smkx] )); then
    # Enable terminal application mode.
    echoti smkx
  fi

  # Update editor information.
  zle editor-info
}
zle -N zle-line-init

# Disables terminal application mode and updates editor information.
function zle-line-finish {
  # The terminal must be in application mode when ZLE is active for $terminfo
  # values to be valid.
  if (( $+terminfo[rmkx] )); then
    # Disable terminal application mode.
    echoti rmkx
  fi

  # Update editor information.
  zle editor-info
}
zle -N zle-line-finish

# Toggles emacs overwrite mode and updates editor information.
function overwrite-mode {
  zle .overwrite-mode
  zle editor-info
}
zle -N overwrite-mode

# Enters vi insert mode and updates editor information.
function vi-insert {
  zle .vi-insert
  zle editor-info
}
zle -N vi-insert

# Moves to the first non-blank character then enters vi insert mode and updates
# editor information.
function vi-insert-bol {
  zle .vi-insert-bol
  zle editor-info
}
zle -N vi-insert-bol

# Enters vi replace mode and updates editor information.
function vi-replace  {
  zle .vi-replace
  zle editor-info
}
zle -N vi-replace

# Expands .... to ../..
function expand-dot-to-parent-directory-path {
  if [[ $LBUFFER = *.. ]]; then
    LBUFFER+='/..'
  else
    LBUFFER+='.'
  fi
}
zle -N expand-dot-to-parent-directory-path

# Displays an indicator when completing.
function expand-or-complete-with-indicator {
  local indicator
  zstyle -s ':prezto:module:editor:info:completing' format 'indicator'
  print -Pn "$indicator"
  zle expand-or-complete
  zle redisplay
}
zle -N expand-or-complete-with-indicator

# Inserts 'sudo ' at the beginning of the line.
function prepend-sudo {
  if [[ "$BUFFER" != su(do|)\ * ]]; then
    BUFFER="sudo $BUFFER"
    (( CURSOR += 5 ))
  fi
}
zle -N prepend-sudo

# Reset to default key bindings.
bindkey -d

#
# Emacs Key Bindings
#

for key in "$key_info[Escape]"{B,b} "${(s: :)key_info[ControlLeft]}"
  bindkey -M emacs "$key" emacs-backward-word
for key in "$key_info[Escape]"{F,f} "${(s: :)key_info[ControlRight]}"
  bindkey -M emacs "$key" emacs-forward-word

# Kill to the beginning of the line.
for key in "$key_info[Escape]"{K,k}
  bindkey -M emacs "$key" backward-kill-line

# Redo.
bindkey -M emacs "$key_info[Escape]_" redo

# Search previous character.
bindkey -M emacs "$key_info[Control]X$key_info[Control]B" vi-find-prev-char

# Match bracket.
bindkey -M emacs "$key_info[Control]X$key_info[Control]]" vi-match-bracket

# Edit command in an external editor.
bindkey -M emacs "$key_info[Control]X$key_info[Control]E" edit-command-line

if (( $+widgets[history-incremental-pattern-search-backward] )); then
  bindkey -M emacs "$key_info[Control]R" \
    history-incremental-pattern-search-backward
  bindkey -M emacs "$key_info[Control]S" \
    history-incremental-pattern-search-forward
fi

#
# Vi Key Bindings
#

# Edit command in an external editor.
bindkey -M vicmd "v" edit-command-line

# Undo/Redo
bindkey -M vicmd "u" undo
bindkey -M vicmd "$key_info[Control]R" redo

if (( $+widgets[history-incremental-pattern-search-backward] )); then
  bindkey -M vicmd "?" history-incremental-pattern-search-backward
  bindkey -M vicmd "/" history-incremental-pattern-search-forward
else
  bindkey -M vicmd "?" history-incremental-search-backward
  bindkey -M vicmd "/" history-incremental-search-forward
fi

#
# Emacs and Vi Key Bindings
#

for keymap in 'emacs' 'viins'; do
  bindkey -M "$keymap" "$key_info[Home]" beginning-of-line
  bindkey -M "$keymap" "$key_info[End]" end-of-line

  bindkey -M "$keymap" "$key_info[Insert]" overwrite-mode
  bindkey -M "$keymap" "$key_info[Delete]" delete-char
  bindkey -M "$keymap" "$key_info[Backspace]" backward-delete-char

  bindkey -M "$keymap" "$key_info[Left]" backward-char
  bindkey -M "$keymap" "$key_info[Right]" forward-char

  # Expand history on space.
  bindkey -M "$keymap" ' ' magic-space

  # Clear screen.
  bindkey -M "$keymap" "$key_info[Control]L" clear-screen

  # Expand command name to full path.
  for key in "$key_info[Escape]"{E,e}
    bindkey -M "$keymap" "$key" expand-cmd-path

  # Duplicate the previous word.
  for key in "$key_info[Escape]"{M,m}
    bindkey -M "$keymap" "$key" copy-prev-shell-word

  # Use a more flexible push-line.
  for key in "$key_info[Control]Q" "$key_info[Escape]"{q,Q}
    bindkey -M "$keymap" "$key" push-line-or-edit

  # Bind Shift + Tab to go to the previous menu item.
  bindkey -M "$keymap" "$key_info[BackTab]" reverse-menu-complete

  # Complete in the middle of word.
  bindkey -M "$keymap" "$key_info[Control]I" expand-or-complete

  # Expand .... to ../..
  if zstyle -t ':prezto:module:editor' dot-expansion; then
    bindkey -M "$keymap" "." expand-dot-to-parent-directory-path
  fi

  # Display an indicator when completing.
  bindkey -M "$keymap" "$key_info[Control]I" \
    expand-or-complete-with-indicator

  # Insert 'sudo ' at the beginning of the line.
  bindkey -M "$keymap" "$key_info[Control]X$key_info[Control]S" prepend-sudo
done

# Do not expand .... to ../.. during incremental search.
if zstyle -t ':prezto:module:editor' dot-expansion; then
  bindkey -M isearch . self-insert 2> /dev/null
fi

#
# Layout
#

# Set the key layout.
zstyle -s ':prezto:module:editor' key-bindings 'key_bindings'
if [[ "$key_bindings" == (emacs|) ]]; then
  bindkey -e
elif [[ "$key_bindings" == vi ]]; then
  bindkey -v
else
  print "prezto: editor: invalid key bindings: $key_bindings" >&2
fi

unset key{,map,bindings}
