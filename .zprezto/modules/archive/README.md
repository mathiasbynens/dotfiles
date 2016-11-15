Archive
=======

Provides functions to list and extract archives.

Functions
---------

  - `lsarchive` lists the contents of one or more archives.
  - `unarchive` extracts the contents of one or more archives.

Supported Formats
-----------------

The following archive formats are supported when the required utilities are
installed:

  - *.tar.gz*, *.tgz* require `tar`.
  - *.tar.bz2*, *.tbz* require `tar`.
  - *.tar.xz*, *.txz* require `tar` with *xz* support.
  - *.tar.zma*, *.tlz* require `tar` with *lzma* support.
  - *.tar* requires `tar`.
  - *.gz* requires `gunzip`.
  - *.bz2* requires `bunzip2`.
  - *.xz* requires `unxz`.
  - *.lzma* requires `unlzma`.
  - *.Z* requires `uncompress`.
  - *.zip* requires `unzip`.
  - *.rar* requires `unrar` or `rar`.
  - *.7z* requires `7za`.
  - *.deb* requires `ar`, `tar`.

Authors
-------

*The authors of this module should be contacted via the [issue tracker][1].*

  - [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: https://github.com/sorin-ionescu/prezto/issues
