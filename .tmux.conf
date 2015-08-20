# Ring the bell if any background window rang a bell
set -g bell-action any

# Default termtype. If the rcfile sets $TERM, that overrides this value.
set -g default-terminal screen-256color

# Keep your finger on ctrl, or don't
bind-key ^D detach-client

# Create splits and vertical splits
bind-key v split-window -h -p 50 -c "#{pane_current_path}"
bind-key ^V split-window -h -p 50 -c "#{pane_current_path}"
bind-key s split-window -p 50 -c "#{pane_current_path}"
bind-key ^S split-window -p 50 -c "#{pane_current_path}"

# Pane resize in all four directions using vi bindings.
# Can use these raw but I map them to shift-ctrl-<h,j,k,l> in iTerm.
bind -r H resize-pane -L 5
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 5

# Smart pane switching with awareness of vim splits.
# Source: https://github.com/christoomey/vim-tmux-navigator
bind -n C-h run "(tmux display-message -p '#{pane_current_command}' | grep -iqE '(^|\/)g?(view|vim?)(diff)?$' && tmux send-keys C-h) || tmux select-pane -L"
bind -n C-j run "(tmux display-message -p '#{pane_current_command}' | grep -iqE '(^|\/)g?(view|vim?)(diff)?$' && tmux send-keys C-j) || tmux select-pane -D"
bind -n C-k run "(tmux display-message -p '#{pane_current_command}' | grep -iqE '(^|\/)g?(view|vim?)(diff)?$' && tmux send-keys C-k) || tmux select-pane -U"
bind -n C-l run "(tmux display-message -p '#{pane_current_command}' | grep -iqE '(^|\/)g?(view|vim?)(diff)?$' && tmux send-keys C-l) || tmux select-pane -R"
bind -n C-\ run "(tmux display-message -p '#{pane_current_command}' | grep -iqE '(^|\/)g?(view|vim?)(diff)?$' && tmux send-keys 'C-\\') || tmux select-pane -l"

# Use vi keybindings for tmux commandline input.
# Note that to get command mode you need to hit ESC twice...
set -g status-keys vi

# Use vi keybindings in copy and choice modes
setw -g mode-keys vi

# easily toggle synchronization (mnemonic: e is for echo)
# sends input to all panes in a given window.
bind e setw synchronize-panes on
bind E setw synchronize-panes off

# set first window to index 1 (not 0) to map more to the keyboard layout...
set-option -g base-index 1
set-window-option -g pane-base-index 1

# color scheme (styled as vim-powerline)
set -g status-left-length 52
set -g status-right-length 451
set -g status-fg white
set -g status-bg colour234
set -g pane-border-fg colour245
set -g pane-active-border-fg colour39
set -g message-fg colour16
set -g message-bg colour221
set -g message-attr bold
set -g status-left '#[fg=colour235,bg=colour252,bold] ❐ #S #[fg=colour252,bg=colour238,nobold]⮀#[fg=colour245,bg=colour238,bold] #(whoami) #[fg=colour238,bg=colour234,nobold]⮀'
set -g window-status-format "#[fg=colour235,bg=colour252,bold] #I #W "
set -g window-status-current-format "#[fg=colour234,bg=colour39]⮀#[fg=black,bg=colour39,noreverse,bold] #I: #W #[fg=colour39,bg=colour234,nobold]⮀"

# Patch for OS X pbpaste and pbcopy under tmux.
set-option -g default-command "which reattach-to-user-namespace > /dev/null && reattach-to-user-namespace -l $SHELL || $SHELL"

# Screen like binding
unbind C-b
set -g prefix C-a
bind a send-prefix

# No escape time for vi mode
set -sg escape-time 0

# Screen like binding for last window
unbind l
bind C-a last-window

# Bigger history
set -g history-limit 10000

# New windows/pane in $PWD
bind c new-window -c "#{pane_current_path}"

# force a reload of the config file
unbind r
bind r source-file ~/.tmux.conf \; display "Reloaded!"

# Local config
if-shell "[ -f ~/.tmux.conf.user ]" 'source ~/.tmux.conf.user'
