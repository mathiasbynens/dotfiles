SublimeLinter
=============

SublimeLinter is a plugin that supports "lint" programs (known as "linters"). SublimeLinter highlights
lines of code the linter deems to contain (potential) errors. It also
supports highlighting special annotations (for example: TODO) so that they
can be quickly located.

SublimeLinter has built in linters for the following languages:

* C/C++ - lint via `cppcheck`
* CoffeeScript - lint via `coffee -s -l`
* CSS - lint via built-in [csslint](http://csslint.net)
* Git Commit Messages - lint via built-in module based on [A Note About Git Commit Messages](http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html).
* Haml - syntax check via `haml -c`
* HTML - lint via `tidy` (actually [tidy for HTML5](http://w3c.github.com/tidy-html5/))
* Java - lint via `javac -Xlint`
* Javascript - lint via built in [jshint](http://jshint.org), [jslint](http://jslint.com), or the [closure linter (gjslint)](https://developers.google.com/closure/utilities/docs/linter_howto) (if installed)
* Lua - syntax check via `luac`
* Objective-J - lint via built-in [capp_lint](https://github.com/aparajita/capp_lint)
* Perl - lint via [Perl:Critic](http://perlcritic.com/) or syntax+deprecation check via `perl -c`
* PHP - syntax check via `php -l`
* Puppet - syntax check via `puppet parser validate`
* Python - native, moderately-complete lint
* Ruby - syntax check via `ruby -wc`
* XML - lint via `xmllint`


Installing
----------
**With the Package Control plugin:** The easiest way to install SublimeLinter is through Package Control, which can be found at this site: http://wbond.net/sublime_packages/package_control

Once you install Package Control, restart ST2 and bring up the Command Palette (`Command+Shift+P` on OS X, `Control+Shift+P` on Linux/Windows). Select "Package Control: Install Package", wait while Package Control fetches the latest package list, then select SublimeLinter when the list appears. The advantage of using this method is that Package Control will automatically keep SublimeLinter up to date with the latest version.

**Without Git:** Download the latest source from [GitHub](https://github.com/SublimeLinter/SublimeLinter) and copy the SublimeLinter folder to your Sublime Text "Packages" directory.

**With Git:** Clone the repository in your Sublime Text "Packages" directory:

    git clone https://github.com/SublimeLinter/SublimeLinter.git


The "Packages" directory is located at:

* OS X:

        ~/Library/Application Support/Sublime Text 2/Packages/

* Linux:

        ~/.config/sublime-text-2/Packages/

* Windows:

        %APPDATA%/Sublime Text 2/Packages/

### Javascript-based linters
If you plan to edit files that use a Javascript-based linter (Javascript, CSS), your system
must have a Javascript engine installed. Mac OS X comes with a preinstalled Javascript engine called
JavaScriptCore, which is used if Node.js is not installed. On Windows, you **must** install the
Javascript engine Node.js, which can be downloaded from [the Node.js site](http://nodejs.org/#download).

On Mac OS X, you **must** install Node.js if you plan to edit Javascript or CSS files that
use non-ASCII characters in strings or comments, because JavaScriptCore is not Unicode-aware.

After installing Node.js, if the Node.js executable ("node" on Mac OS X, "node.exe" on Windows)
cannot be found by SublimeLinter, you may have to set the path to the executable in the
"sublimelinter\_executable\_map" setting. See the "Configuring" section below for info on
SublimeLinter settings.

Configuring
-----------
There are a number of settings available to customize the behavior of SublimeLinter and its linters. For the latest information on what settings are available, select the menu item `Preferences->Package Settings->SublimeLinter->Settings - Default`.

Do **NOT** edit the default SublimeLinter settings. Your changes will be lost when SublimeLinter is updated. ALWAYS edit the user SublimeLinter settings by selecting `Preferences->Package Settings->SublimeLinter->Settings - User`. Note that individual settings you include in your user settings will _completely_ replace the corresponding default setting, so you must provide that setting in its entirety.

### Linter-specific notes
Following are notes specific to individual linters that you should be aware of:

* **C/C++** - The default C/C++ linter is [cppcheck](http://cppcheck.sourceforge.net/), however Google's [cpplint.py](http://google-styleguide.googlecode.com/svn/trunk/cpplint/) is also supported.

  To swap `cppcheck` out for `cpplint.py` you will need to adjust `sublimelinter_syntax_map` and possibly `sublimelinter_executable_map` also. First change the _linter language_ for `C` and `C++` to `c_cpplint` via `sublimelinter_syntax_map`. If `cpplint.py` is not on your system `PATH`, then add an entry for `c_cpplint` into `sublimelinter_executable_map` with the path to the file. As usual add these adjustments to the SublimeLinter **User Settings** file. An example:

      "sublimelinter_syntax_map":
      {
	"Python Django": "python",
	"Ruby on Rails": "ruby",
	"C++": "c_cpplint",
	"C": "c_cpplint"
      },
      "sublimelinter_executable_map":
      {
	"c_cpplint": "/Users/[my username]/Desktop/cpplint.py"
      }

* **CSS** - This linter runs [csslint](http://csslint.net). This linter requires a Javascript engine (like Node.js) to be installed (see notes above for the JavaScript linters: "jshint" or "jslint").

  By default all CSSLint settings are turned on. You may customize CSSLint behavior with the "csslint_options" setting. Please select `Preferences->Package Settings->SublimeLinter->Settings - Default` for more information on turning off or adjusting severity of tests. For more information about options available to CSSLint, see https://github.com/stubbornella/csslint/wiki/Rules.

* **HTML** - This linter will not run unless you have a version of tidy with HTML5 support. To use this linter, please see: https://github.com/w3c/tidy-html5

* **Java** - Because it uses `javac` to do linting, each time you run the linter the entire dependency graph of the current file will be checked. Depending on the number of classes you import, this can be **extremely** slow. Also note that you **must** provide the `-sourcepath`, `-classpath`, `-Xlint` and `{filename}` arguments to `javac` in your per-project settings. See "Per-project settings" below for more information.

* **JavaScript** - If the "javascript_linter" setting is "jshint" or "jslint", this linter runs [jshint](http://jshint.org) (or [jslint](http://jslint.com) respectively) using Node.js. See "Javascript-based linters" above for information on how to install Node.js.

  If the "javascript_linter" setting is "gjslint", this linter runs the [closure linter (gjslint)](https://developers.google.com/closure/utilities/docs/linter_howto). After installation, if gjslint cannot be found by SublimeLinter, you may have to set the path to gjslint in the "sublimelinter\_executable\_map" setting.

  You may want to modify the options passed to jshint, jslint, or gjslint. This can be done by using the **jshint_options**, **jslint_options**, or **gjslint_options** setting. Refer to the jshint.org site, the jslint.com site, or run `gjslint --help` for more information on the configuration options available.

  SublimeLinter supports `.jshintrc` files. If using JSHint, SublimeLinter will recursively search the directory tree (from the file location to the file-system root directory). This functionality is specified in the [JSHint README](https://github.com/jshint/node-jshint/#within-your-projects-directory-tree).

* **Perl** - Due to a vulnerability (issue [#77](https://github.com/SublimeLinter/SublimeLinter/issues/77)) with the Perl linter, Perl syntax checking is no longer enabled by default. The default linter for Perl has been replaced by Perl::Critic. The standard Perl syntax checker can still be invoked by switching the "perl_linter" setting to "perl".

* **Ruby** - If you are using rvm or rbenv, you will probably have to specify the full path to the ruby you are using in the "sublimelinter_executable_map" setting. See "Configuring" below for more info.

### Per-project settings
SublimeLinter supports per-project/per-language settings. This is useful if a linter requires path configuration on a per-project basis. To edit your project settings, select the menu item `Project->Edit Project`. If there is no "settings" object at the top level, add one and then add a "SublimeLinter" sub-object, like this:

    {
        "folders":
        [
            {
                "path": "/Users/aparajita/Projects/foo/src"
            }
        ],
        "settings":
        {
            "SublimeLinter":
            {
            }
        }
    }

Within the "SublimeLinter" object, you can add a settings object for each language. The language name must match the language item in the linter's CONFIG object, which can be found in the linter's source file in the SublimeLinter/sublimelinter/modules folder. Each language can have two settings:

* "working_directory" - If present and a valid absolute directory path, the working directory is set to this path before the linter executes. This is useful if you are providing linter arguments that contain paths and you want to use working directory-relative paths instead of absolute paths.
* "lint_args" - If present, it must be a sequence of string arguments to pass to the linter. If your linter expects a filename as an argument, use the argument "{filename}" as a placeholder. Note that if you provide this item, you are responsible for passing **all** required arguments to the linter.

For example, let's say we are editing a Java project and want to use the "java" linter, which requires a source path and class path. In addition, we want to ignore serialization errors. Our project settings might look like this:

    {
        "folders":
        [
            {
                "path": "/Users/aparajita/Projects/foo/src"
            }
        ],
        "settings":
        {
            "SublimeLinter":
            {
                "java":
                {
                    "working_directory": "/Users/aparajita/Projects/foo",

                    "lint_args":
                    [
                        "-sourcepath", "src",
                        "-classpath", "libs/log4j-1.2.9.jar:libs/commons-logging-1.1.jar",
                        "-Xlint", "-Xlint:-serial",
                        "{filename}"
                    ]
                }
            }
        }
    }

The jshint follows convention set by node-jshint (though node is not required) and will attempt to locate the configuration file for you starting in pwd. (or "present working directory") If this does not yield a .jshintrc file, it will move one level up (..) the directory tree all the way up to the filesystem root. If a file is found, it stops immediately and uses that set of configuration instead of "jshint_options".

### Customizing colors
**IMPORTANT** - The theme style names have recently changed. The old and new color
names are:

    Old                     New
    ---------------------   -----------------------------
    sublimelinter.<type>    sublimelinter.outline.<type>
    invalid.<type>          sublimelinter.underline.<type>

Please change the names in your color themes accordingly.

There are three types of "errors" flagged by SublimeLinter: illegal,
violation, and warning. For each type, SublimeLinter will indicate the offending
line and the character position at which the error occurred on the line.

By default SublimeLinter will outline offending lines using the background color
of the "sublimelinter.outline.<type>" theme style, and underline the character position
using the background color of the "sublimelinter.underline.<type>" theme style, where <type>
is one of the three error types.

If these styles are not defined, the color will be black when there is a light
background color and black when there is a dark background color. You may
define a single "sublimelinter.outline" or "sublimelinter.underline" style to color all three types,
or define separate substyles for one or more types to color them differently.

If you want to make the offending lines glaringly obvious (perhaps for those
who tend to ignore lint errors), you can set the user setting:

    "sublimelinter_mark_style": "fill"

When this is set true, lines that have errors will be colored with the background
and foreground color of the "sublime.outline.<type>" theme style. Unless you have defined
those styles, this setting should be left as "outline".

You may want to disable drawing of outline boxes entirely. If so, change
using the user setting to:

    "sublimelinter_mark_style": "none"

You may also mark lines with errors by putting an "x" in the gutter with the user setting:

    "sublimelinter_gutter_marks": true

To customize the colors used for highlighting errors and user notes, add the following
to your theme (adapting the color to your liking):

    <dict>
        <key>name</key>
        <string>SublimeLinter Annotations</string>
        <key>scope</key>
        <string>sublimelinter.notes</string>
        <key>settings</key>
        <dict>
            <key>background</key>
            <string>#FFFFAA</string>
            <key>foreground</key>
            <string>#FFFFFF</string>
        </dict>
    </dict>
    <dict>
        <key>name</key>
        <string>SublimeLinter Error Outline</string>
        <key>scope</key>
        <string>sublimelinter.outline.illegal</string>
        <key>settings</key>
        <dict>
            <key>background</key>
            <string>#FF4A52</string>
            <key>foreground</key>
            <string>#FFFFFF</string>
        </dict>
    </dict>
    <dict>
        <key>name</key>
        <string>SublimeLinter Error Underline</string>
        <key>scope</key>
        <string>sublimelinter.underline.illegal</string>
        <key>settings</key>
        <dict>
            <key>background</key>
            <string>#FF0000</string>
        </dict>
    </dict>
    <dict>
        <key>name</key>
        <string>SublimeLinter Warning Outline</string>
        <key>scope</key>
        <string>sublimelinter.outline.warning</string>
        <key>settings</key>
        <dict>
            <key>background</key>
            <string>#DF9400</string>
            <key>foreground</key>
            <string>#FFFFFF</string>
        </dict>
    </dict>
    <dict>
        <key>name</key>
        <string>SublimeLinter Warning Underline</string>
        <key>scope</key>
        <string>sublimelinter.underline.warning</string>
        <key>settings</key>
        <dict>
            <key>background</key>
            <string>#FF0000</string>
        </dict>
    </dict>
    <dict>
        <key>name</key>
        <string>SublimeLinter Violation Outline</string>
        <key>scope</key>
        <string>sublimelinter.outline.violation</string>
        <key>settings</key>
        <dict>
            <key>background</key>
            <string>#ffffff33</string>
            <key>foreground</key>
            <string>#FFFFFF</string>
        </dict>
    </dict>
    <dict>
        <key>name</key>
        <string>SublimeLinter Violation Underline</string>
        <key>scope</key>
        <string>sublimelinter.underline.violation</string>
        <key>settings</key>
        <dict>
            <key>background</key>
            <string>#FF0000</string>
        </dict>
    </dict>

Using
-----
SublimeLinter runs in one of three modes, which is determined by the "sublimelinter" user setting:

* **Background mode (the default)** - When the "sublimelinter" setting is true, linting is performed in the background as you modify a file (if the relevant linter supports it). If you like instant feedback, this is the best way to use SublimeLinter. If you want feedback, but not instantly, you can try another mode or set a minimum queue delay with the "sublimelinter_delay" setting, so that the linter will only run after a certain amount of idle time.
* **Load-save mode** - When the "sublimelinter" setting is "load-save", linting is performed only when a file is loaded and after saving. Errors are cleared as soon as the file is modified.
* **Save-only mode** - When the "sublimelinter" setting is "save-only", linting is performed only after a file is saved. Errors are cleared as soon as the file is modified.
* **On demand mode** - When the "sublimelinter" setting is false, linting is performed only when initiated by you. Use the `Control+Command+L` (OS X) or `Control+Alt+L` (Linux/Windows) key equivalent or the Command Palette to lint the current file. If the current file has no associated linter, the command will not be available.

Within a file whose language/syntax is supported by SublimeLinter, you can control SublimeLinter via the Command Palette (`Command+Shift+P` on OS X, `Control+Shift+P` on Linux/Windows). The available commands are:

* **SublimeLinter: Lint Current File** - Lints the current file, highlights any errors and displays how many errors were found.
* **SublimeLinter: Show Error List** - Lints the current file, highlights any errors and displays a quick panel with any errors that are found. Selecting an item from the quick panel jumps to that line.
* **SublimeLinter: Background Linting** - Enables background linting mode for the current view and lints it.
* **SublimeLinter: Disable Linting** - Disables linting mode for the current view and clears all lint errors.
* **SublimeLinter: Load-Save Linting** - Enables load-save linting mode for the current view and clears all lint errors.
* **SublimeLinter: Save-Only Linting** - Enables save-only linting mode for the current view and clears all lint errors.
* **SublimeLinter: Reset** - Clears all lint errors and sets the linting mode to the value in the SublimeLinter.sublime-settings file.

Depending on the file and the current state of background enabling, some of the commands will not be available.

When an error is highlighted by the linter, putting the cursor on the offending line will result in the error message being displayed on the status bar.

If you want to be shown a popup list of all errors whenever a file is saved, modify the user setting:

    "sublimelinter_popup_errors_on_save": true

If there are errors in the file, a quick panel will appear which shows the error message, line number and source code for each error. The starting location of all errors on the line are marked with "^". Selecting an error in the quick panel jumps directly to the location of the first error on that line.

While editing a file, you can quickly move to the next/previous lint error with the following key equivalents:

* **OS X**:

        next: Control+Command+E
        prev: Control+Command+Shift+E

* **Linux, Windows**:

        next: Control+Alt+E
        prev: Control+Alt+Shift+E

By default the search will wrap. You can turn wrapping off with the user setting:

    "sublimelinter_wrap_find": false

Please note: these key commands may conflict with other important cmds (such as generating the € character - this was discussed in issue [#182](https://github.com/SublimeLinter/SublimeLinter/issues/182)). If these controls are problematic, you may always adjust your settings by copying the defaults stored in `Preferences->Package Settings->SublimeLinter->Key Bindings - Default` into `Preferences->Key Bindings - User` and then modifying the values appropriately.

Troubleshooting
---------------
If a linter does not seem to be working, you can check the ST2 console to see if it was enabled. When SublimeLinter is loaded, you will see messages in the console like this:

    Reloading plugin /Users/aparajita/Library/Application Support/Sublime Text 2/Packages/SublimeLinter/sublimelinter_plugin.py
    SublimeLinter: JavaScript loaded
    SublimeLinter: annotations loaded
    SublimeLinter: Objective-J loaded
    SublimeLinter: perl loaded
    SublimeLinter: php loaded
    SublimeLinter: python loaded
    SublimeLinter: ruby loaded
    SublimeLinter: pylint loaded

The first time a linter is asked to lint, it will check to see if it can be enabled. You will then see messages like this:

    SublimeLinter: JavaScript enabled (using JavaScriptCore)
    SublimeLinter: Ruby enabled (using "ruby" for executable)

Let's say the ruby linter is not working. If you look at the console, you may see a message like this:

    SublimeLinter: ruby disabled ("ruby" cannot be found)

This means that the ruby executable cannot be found on your system, which means it is not installed or not in your executable path.

Creating New Linters
--------------------
If you wish to create a new linter to support a new language, SublimeLinter makes it easy. Here are the steps involved:

* Create a new file in sublimelinter/modules. If your linter uses an external executable, you will probably want to copy perl.py. If your linter uses built in code, copy objective-j.py. The convention is to name the file the same as the language that will be linted.

* Configure the CONFIG dict in your module. See the comments in base\_linter.py for information on the values in that dict. You only need to set the values in your module that differ from the defaults in base\_linter.py, as your module's CONFIG is merged with the default. Note that if your linter uses an external executable that does not take stdin, setting 'input\_method' to INPUT\_METHOD\_TEMP\_FILE will allow interactive linting with that executable.

* If your linter uses built in code, override `built_in_check()` and return the errors found.

* Override `parse_errors()` and process the errors. If your linter overrides `built_in_check()`, `parse_errors()` will receive the result of that method. If your linter uses an external executable, `parse_errors()` receives the raw output of the executable, stripped of leading and trailing whitespace.

* If you linter is powered via Javascript (eg. Node.js), there are few steps that will simplify the integration.

  Create a folder matching your linter name in the `SublimeLinter/sublimelinter/modules/lib` directory. This folder should include the linting library JS file (eg. jshint.js, csslint-Node.js) and a **linter.js** file. The **linter.js** file should `require()` the actual linter library file and export a `lint()` function. The `lint()` function should return a list of errors back to the python language handler file (via the `errors` parameter to the `parse_errors()` method).

  Although **linter.js** should follow the Node.js api, the linter may also be run via JavaScriptCore on OS X if Node.js is not installed. In the case where JavaScriptCore is used, require + export are shimmed to keep things consistent. However, it is important not to assume that a full Node.js api is available. If you must know what JS engine you are using, you may check for `USING_JSC` to be set as `true` when JavaScriptCore is used.

  For examples of using the JS engines, see **csslint**, **jslint**, and **jshint** in `SublimeLinter/sublimelinter/modules/libs` and the respective python code of **css.py** and **javascript.py** in `SublimeLinter/sublimelinter/modules`.


If your linter has more complex requirements, see the comments for CONFIG in base\_linter.py, and use the existing linters as guides.

Beta
----
The SublimeLinter Beta package is available via Package Control. The beta version is considered unstable and should only be used for testing the next release. If you like living on the edge, please report any bugs you find on the [SublimeLinter issues](https://github.com/SublimeLinter/SublimeLinter/issues) page.
