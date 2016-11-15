History
=======

Sets [history][1] options and defines history aliases.

Variables
---------

  - `HISTFILE` stores the path to the history file.
  - `HISTSIZE` stores the maximum number of events to save in the internal history.
  - `SAVEHIST` stores the maximum number of events to save in the history file.

Options
-------

  - `BANG_HIST` treats the **!** character specially during expansion.
  - `EXTENDED_HISTORY` writes the history file in the *:start:elapsed;command* format.
  - `INC_APPEND_HISTORY` writes to the history file immediately, not when the shell exits.
  - `SHARE_HISTORY` shares history between all sessions.
  - `HIST_EXPIRE_DUPS_FIRST` expires a duplicate event first when trimming history.
  - `HIST_IGNORE_DUPS` does not record an event that was just recorded again.
  - `HIST_IGNORE_ALL_DUPS` deletes an old recorded event if a new event is a duplicate.
  - `HIST_FIND_NO_DUPS` does not display a previously found event.
  - `HIST_IGNORE_SPACE` does not record an event starting with a space.
  - `HIST_SAVE_NO_DUPS` does not write a duplicate event to the history file.
  - `HIST_VERIFY` does not execute immediately upon history expansion.
  - `HIST_BEEP` beeps when accessing non-existent history.

Aliases
-------

  - `history-stat` lists the ten most used commands

Authors
-------

*The authors of this module should be contacted via the [issue tracker][2].*

  - [Robby Russell](https://github.com/robbyrussell)
  - [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: http://zsh.sourceforge.net/Guide/zshguide02.html#l16
[2]: https://github.com/sorin-ionescu/prezto/issues
