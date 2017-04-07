Directory
=========

Sets directory options and defines directory aliases.

Options
-------

  - `AUTO_CD` auto changes to a directory without typing `cd`.
  - `AUTO_PUSHD` pushes the old directory onto the stack on `cd`.
  - `PUSHD_IGNORE_DUPS` does not store duplicates in the stack.
  - `PUSHD_SILENT` does not print the directory stack after `pushd` or `popd`.
  - `PUSHD_TO_HOME` pushes to the home directory when no argument is given.
  - `CDABLE_VARS` changes directory to a path stored in a variable.
  - `AUTO_NAME_DIRS` auto adds variable-stored paths to `~` list.
  - `MULTIOS` writes to multiple descriptors.
  - `EXTENDED_GLOB` uses extended globbing syntax.
  - `CLOBBER` does not overwrite existing files with `>` and `>>`. Use `>!` and
    `>>!` to bypass.

Aliases
-------

  - `d` prints the contents of the directory stack.
  - `1 ... 9` changes the directory to the **n** previous one.

Authors
-------

*The authors of this module should be contacted via the [issue tracker][1].*

  - [James Cox](https://github.com/imajes)
  - [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: https://github.com/sorin-ionescu/prezto/issues
