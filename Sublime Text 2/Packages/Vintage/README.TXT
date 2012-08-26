Overview:
--------

Vintage is a vi editing package for Sublime Text 2. It's not quite a faithful recreation, and not all details match up. On the other hand, you do get multiple selections.


Enabling Vintage:
--------

Vintage is disabled by default, via the ignored_packages global setting. If you remove "Vintage" from the list of ignored packages, you'll be able to edit with vi keys.

Vintage starts in insert mode by default. This can be changed by adding:

	"vintage_start_in_command_mode": true

to your User File Settings.


Major Differences From vi:
--------

Insert mode is plain Sublime Text 2 editing, with the usual Sublime Text 2 key bindings: vi insert mode key bindings are not emulated.

Ex commands are not implemented, apart from :w and :e, which work via the command palette.


Extending Vintage:
--------

Vintage is implemented entirely in Python. Extending it, for example, to add additional motions, is a matter of writing the relevant plugin (see vintage_motions.py for the existing ones), and adding a key binding for it.

Motions are normal commands that work by selecting the range of text that they move over. The end of the selection (.b), is considered the active end. Motions are either inclusive, or exclusive (the default). Exclusive motions will move the caret to the right of the last selected character, inclusive motions will move it to the left. Motions are considered inclusive if the inclusive flag is passed to the set_motion command.
