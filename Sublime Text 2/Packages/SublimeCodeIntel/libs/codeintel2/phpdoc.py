#!/usr/bin/env python

""" Utility class used for the parsing of PHPDocumenter comments, aka PHPDoc.

PHPDocumenter is documented online here:
http://manual.phpdoc.org/HTMLSmartyConverter/HandS/li_phpDocumentor.html

/**
 * Method for creating a slider.
 *
 * @static
 * @param string $arg1  The first argument description.
 * @param int leftPadding  The size of the padding field on the left
 * @param int rightPadding  Optional field for setting the size of the padding
 * field on the right.
 * @return Slider  A horizontal slider control
 */

Notes:
* multiple types can be separated by a "|", i.e. int|string|array
* field comments can span multiple lines.
"""

# PHPDoc tags and the help (calltip) for the tag.
# Note: Not all of these have a meaning for the php ciler.
phpdoc_tags = {
    "abstract":     "Mark an abstract class, class variable or method.\n"
                    "@abstract",

    "access":       "Access control for an element. Should be one of\n"
                    "public, protected or private.\n"
                    "@access public|protected|private",

    "author":       "Author of the current element.\n"
                    "@author John Smith <jsmith@pod1.mars>",

    "category":     "Specify a category to organize the documented\n"
                    "element's package into.\n"
                    "@category Testing",

    "copyright":    "Document Copyright information.\n"
                    "@copyright Copyright (c) 2007, John Smith",

    "deprecated":   "Document elements that have been deprecated and should\n"
                    "not be used as they may be removed at any time from a\n"
                    "future version.\n"
                    "@deprecated since versionstring",

    "example":      "Include an external example file with syntax highlighting.\n"
                    "@example reference The description",

    "exception":    "Documents an exception that can be thrown by the method.\n"
                    "@exception Exception when something bad occurs",

    "final":        "Document a class method that should never be overridden\n"
                    "in a child class.\n"
                    "@final",

    "filesource":   "Will create a syntax-highlighted cross-referenced file\n"
                    "containing source code of the current file and link to it.\n"
                    "@filesource",

    "global":       "Document a global variable, or its use in a function.\n"
                    "@global array $GLOBALS['baz']",

    "ignore":       "Prevent documentation of an element.\n"
                    "@ignore",

    "internal":     "Mark documentation as private, internal to the\n"
                    "software project.\n"
                    "@internal Notes for internal use.",

    "license":      "Display a hyperlink to a URL for a license.\n"
                    "@license http://lic.org/lic.php MyLicense",

    "link":         "Display a hyperlink to a URL in the documentation.\n"
                    "@link http://pod.mars/ Mars Pod",

    "method":       "Document a 'Magic' Method of a class.\n"
                    "@method returntype someMethod() description of method",

    "name":         "Specify an alias to use for a procedural page or global\n"
                    "variable in displayed documentation and linking.\n"
                    "Note: Used in conjunction with the @global tag.\n"
                    "@name $baz",

    "package":      "Name to group classes or functions and defines into.\n"
                    "@package packagename",

    "param":        "Provide information about a function parameter.\n"
                    "@param datatype $paramname The description",

    "property":     "Document a 'Magic' Property of a class.\n"
                    "@property datatype $property_name The description",

    "return":       "Specify the return type of a function or method.\n"
                    "@return datatype The description",

    "see":          "Display a link to the documentation for an element.\n"
                    "@see reference",

    "since":        "Document when (at which version) an element was first\n"
                    "added to a package.\n"
                    "@since versionstring",

    "static":       "Document a static property or method.\n"
                    "@static",

    "staticvar":    "Document a static variable's use in a function/method.\n"
                    "@staticvar datatype The description.",

    "subpackage":   "Specify sub-package to group classes or functions and\n"
                    "defines into. Must only be used with the @package tag.\n"
                    "@subpackage subpackagename",

    "throws":       "Documents an exception that can be thrown by the method.\n"
                    "@throws Exception when something bad occurs",

    "todo":         "Document changes that will be made in the future.\n"
                    "@todo The description",

    "tutorial":     "Display a link to the documentation for a tutorial.\n"
                    "@tutorial reference",

    "uses":         "Display a link to the documentation for an element,\n"
                    "and create a backlink in the other element's\n"
                    "documentation to this.\n"
                    "@uses reference The description",

    "var":          "Document the data type of a class variable.\n"
                    "@var datatype The description.",

    "version":      "Version of current element.\n"
                    "@version versionstring",

}
