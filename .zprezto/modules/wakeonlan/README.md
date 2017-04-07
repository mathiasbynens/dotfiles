Wake-on-LAN
===========

This module provides a wrapper around the [wakeonlan][1] tool.

Usage
-----

To use this wrapper, create the *~/.wakeonlan* directory, and place in it one
file for each device you would like to be able to wake. Give the file a name
that describes the device, such as its hostname.

Each file should contain a line with the MAC address of the target device and
the network broadcast address. For instance, there might be a file
*~/.wakeonlan/leto* with the following contents:

    00:11:22:33:44:55:66 192.168.0.255

To wake that device, use the following command:

    wake leto

For more information on the configuration file format, read the
[wakeonlan man page][2].

Authors
-------

*The authors of this module should be contacted via [issue tracker][3].*

  - [Paul Dann](https://github.com/giddie)
  - [Sorin Ionescu](https://github.com/sorin-ionescu)

[1]: http://gsd.di.uminho.pt/jpo/software/wakeonlan/
[2]: http://man.cx/wakeonlan
[3]: https://github.com/sorin-ionescu/prezto/issues
