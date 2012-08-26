Patches applied to 3rd-party modules to be used by SublimeCodeIntel.

* cElementTree patched to be ciElementTree (to add Komodo CodeIntel2 features)
* elementtree patched to have "iElementTree" features in the pure python version
	of ElementTree (not really needed if using ciElementTree)
* SilverCity patched to compile with scintilla 210
* scintilla patched to add User Language Definitions and XML, using 210 instead
	of the older bundled version with SilverCity.
* sgmlop patched to have '%' symbol as PI and send positions to Parsers.

For platforms with a *nix shell, use ./build.sh to build and "deploy" the needed
binary files (_SilverCity.so and ciElementTree.so) for SublimeCodeIntel to work.
The built .so files will be copied to `SublimeCodeIntel/libs/_local_arch/`

The other provided patches are here for reference later upgrading of codeintel2
and other Open Komodo modules.

Open Komodo's codeintel2 source from:
http://svn.openkomodo.com/repos/openkomodo/trunk/src/codeintel/lib/codeintel2/

Open Komodo's extra needed libraries from:
http://svn.openkomodo.com/repos/openkomodo/trunk/src/python-sitelib/
http://svn.openkomodo.com/repos/openkomodo/src/schemes/styles.py
http://svn.openkomodo.com/repos/openkomodo/src/udl/skel/MXML/langinfo_mxml.py

Universal Encoding Detector (chardet, GNU LGPL) from:
http://chardet.feedparser.org/

Other extra lib needed for windows, winprocess.py, from:
http://benjamin.smedbergs.us/blog/2006-12-11/killableprocesspy/

Lexers (codeintel2/lexers) from UDL languages at:
http://svn.openkomodo.com/repos/openkomodo/src/udl/
Using: `find udl -name '*-mainlex.udl' -exec python luddite.py just_compile {} \;`
