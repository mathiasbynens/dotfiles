cpp_keywords = \
    "asm auto bool break case catch char class const const_cast continue "\
    "default delete do double dynamic_cast else enum explicit export extern false float for "\
    "friend goto if inline int long mutable namespace new operator private protected public "\
    "register reinterpret_cast return short signed sizeof static static_cast struct switch "\
    "template this throw true try typedef typeid typename union unsigned using "\
    "virtual void volatile wchar_t while"

doxygen_keywords = \
    "a addindex addtogroup anchor arg attention "\
    "author b brief bug c class code date def defgroup deprecated dontinclude "\
    "e em endcode endhtmlonly endif endlatexonly endlink endverbatim enum example exception "\
    "f$ f[ f] file fn hideinitializer htmlinclude htmlonly "\
    "if image include ingroup internal invariant interface latexonly li line link "\
    "mainpage name namespace nosubgrouping note overload "\
    "p page par param post pre ref relates remarks return retval "\
    "sa section see showinitializer since skip skipline struct subsection "\
    "test throw todo typedef union until "\
    "var verbatim verbinclude version warning weakgroup $ @ \ & < > # { }"


java_keywords = \
    "abstract assert boolean break byte case catch char class "\
    "const continue default do double else extends final finally float for future "\
    "generic goto if implements import inner instanceof int interface long "\
    "native new null outer package private protected public rest "\
    "return short static super switch synchronized this throw throws "\
    "transient try var void volatile while"

javadoc_keywords = \
    "author code docRoot deprecated exception inheritDoc link linkplain "\
    "literal param return see serial serialData serialField since throws "\
    "value version"

perl_keywords = \
    "__FILE__ __LINE__ __PACKAGE__ __DATA__ __END__ AUTOLOAD "\
    "BEGIN CHECK CORE DESTROY END INIT CHECK UNITCHECK abs accept "\
    "alarm and atan2 bind binmode bless break caller chdir chmod chomp chop "\
    "chown chr chroot close closedir cmp connect continue cos crypt "\
    "dbmclose dbmopen default defined delete die do dump each else elsif endgrent "\
    "endhostent endnetent endprotoent endpwent endservent eof eq eval "\
    "exec exists exit exp fcntl fileno flock for foreach fork format "\
    "formline ge getc getgrent getgrgid getgrnam gethostbyaddr gethostbyname "\
    "gethostent getlogin getnetbyaddr getnetbyname getnetent getpeername "\
    "getpgrp getppid getpriority getprotobyname getprotobynumber getprotoent "\
    "getpwent getpwnam getpwuid getservbyname getservbyport getservent "\
    "getsockname getsockopt given glob gmtime goto grep gt hex if import "\
    "include index "\
    "int ioctl join keys kill last lc lcfirst le length link listen "\
    "local localtime lock log lstat lt m map mkdir msgctl msgget msgrcv "\
    "msgsnd my ne new next no not oct open opendir or ord our pack package "\
    "pipe pop pos print printf prototype push q qq qr quotemeta "\
    "qw qx rand read readdir readline readlink readpipe recv redo "\
    "ref rename require reset return reverse rewinddir rindex rmdir "\
    "s say scalar seek seekdir select semctl semget semop send setgrent "\
    "sethostent setnetent setpgrp setpriority setprotoent setpwent "\
    "setservent setsockopt shift shmctl shmget shmread shmwrite shutdown "\
    "sin sleep socket socketpair sort splice split sprintf sqrt srand "\
    "stat state study sub substr symlink syscall sysopen sysread sysseek "\
    "system syswrite tell telldir tie tied time times tr truncate "\
    "uc ucfirst umask undef unless unlink unpack unshift untie until "\
    "use utime values vec wait waitpid wantarray warn when while write "\
    "x xor y"

python_keywords = \
    "and assert break class continue def del elif else except " \
    "exec finally for from global if import in is lambda None not or pass print " \
    "raise return try while yield"

ruby_keywords = \
    "__FILE__ and def end in or self unless __LINE__ begin "\
    "defined? ensure module redo super until BEGIN break do false next rescue "\
    "then when END case else for nil retry true while alias class elsif if "\
    "not return undef yield"

sql_keywords = \
    "ABSOLUTE ACTION ADD ADMIN AFTER AGGREGATE " \
    "ALIAS ALL ALLOCATE ALTER AND ANY ARE ARRAY AS ASC " \
    "ASSERTION AT AUTHORIZATION "\
    "BEFORE BEGIN BINARY BIT BLOB BOOLEAN BOTH BREADTH BY "\
    "CALL CASCADE CASCADED CASE CAST CATALOG CHAR CHARACTER "\
    "CHECK CLASS CLOB CLOSE COLLATE COLLATION COLUMN COMMIT "\
    "COMPLETION CONNECT CONNECTION CONSTRAINT CONSTRAINTS "\
    "CONSTRUCTOR CONTINUE CORRESPONDING CREATE CROSS CUBE CURRENT "\
    "CURRENT_DATE CURRENT_PATH CURRENT_ROLE CURRENT_TIME CURRENT_TIMESTAMP "\
    "CURRENT_USER CURSOR CYCLE "\
    "DATA DATE DAY DEALLOCATE DEC DECIMAL DECLARE DEFAULT "\
    "DEFERRABLE DEFERRED DELETE DEPTH DEREF DESC DESCRIBE DESCRIPTOR "\
    "DESTROY DESTRUCTOR DETERMINISTIC DICTIONARY DIAGNOSTICS DISCONNECT "\
    "DISTINCT DOMAIN DOUBLE DROP DYNAMIC "\
    "EACH ELSE END END-EXEC EQUALS ESCAPE EVERY EXCEPT "\
    "EXCEPTION EXEC EXECUTE EXTERNAL "\
    "FALSE FETCH FIRST FLOAT FOR FOREIGN FOUND FROM FREE FULL "\
    "FUNCTION "\
    "GENERAL GET GLOBAL GO GOTO GRANT GROUP GROUPING "\
    "HAVING HOST HOUR "\
    "IDENTITY IGNORE IMMEDIATE IN INDICATOR INITIALIZE INITIALLY "\
    "INNER INOUT INPUT INSERT INT INTEGER INTERSECT INTERVAL "\
    "INTO IS ISOLATION ITERATE "\
    "JOIN "\
    "KEY "\
    "LANGUAGE LARGE LAST LATERAL LEADING LEFT LESS LEVEL LIKE "\
    "LIMIT LOCAL LOCALTIME LOCALTIMESTAMP LOCATOR "\
    "MAP MATCH MINUTE MODIFIES MODIFY MODULE MONTH "\
    "NAMES NATIONAL NATURAL NCHAR NCLOB NEW NEXT NO NONE "\
    "NOT NULL NUMERIC "\
    "OBJECT OF OFF OLD ON ONLY OPEN OPERATION OPTION "\
    "OR ORDER ORDINALITY OUT OUTER OUTPUT "\
    "PAD PARAMETER PARAMETERS PARTIAL PATH POSTFIX PRECISION PREFIX "\
    "PREORDER PREPARE PRESERVE PRIMARY "\
    "PRIOR PRIVILEGES PROCEDURE PUBLIC "\
    "READ READS REAL RECURSIVE REF REFERENCES REFERENCING RELATIVE "\
    "RESTRICT RESULT RETURN RETURNS REVOKE RIGHT "\
    "ROLE ROLLBACK ROLLUP ROUTINE ROW ROWS "\
    "SAVEPOINT SCHEMA SCROLL SCOPE SEARCH SECOND SECTION SELECT "\
    "SEQUENCE SESSION SESSION_USER SET SETS SIZE SMALLINT SOME| SPACE "\
    "SPECIFIC SPECIFICTYPE SQL SQLEXCEPTION SQLSTATE SQLWARNING START "\
    "STATE STATEMENT STATIC STRUCTURE SYSTEM_USER "\
    "TABLE TEMPORARY TERMINATE THAN THEN TIME TIMESTAMP "\
    "TIMEZONE_HOUR TIMEZONE_MINUTE TO TRAILING TRANSACTION TRANSLATION "\
    "TREAT TRIGGER TRUE "\
    "UNDER UNION UNIQUE UNKNOWN "\
    "UNNEST UPDATE USAGE USER USING "\
    "VALUE VALUES VARCHAR VARIABLE VARYING VIEW "\
    "WHEN WHENEVER WHERE WITH WITHOUT WORK WRITE "\
    "YEAR "\
    "ZONE"

verilog_keywords =\
                 "always end endcase begin endfunction module "\
                 "case endmodule casex function or default if "\
                 "else initial and table rcmos task "\
                 "ifnone casez join release assign "\
                 "cmos large repeat deassign macromodule rnmos "\
                 "medium rpmos disable nand rtran edge nmos "\
                 "rtranif0 vectored endprimitive nor rtranif1 wait endspecify not scalared wand "\
                 "endtable endtask specify event pmos "\
                 "while for primitive wor force pull0 strong1 "\
                 "xnor forever xor fork "

verilog_keywords2 =\
                 "inout posedge input reg "\
                 "tri case negedge tri0 tri1 output "\
                 "wire  parameter highz0 pullup buf highz1 "\
                 "bufif0  real time bufif1 integer realtime tran tranif0 "\
                 "tranif1  triand defparam "\
                 "trior trireg "\
                 "notif0 small weak0 notif1  weak1  "\
                 "specparam  strong0 pull0 strong1 "\
                 "pull1 supply0 pulldown supply "

vxml_elements =\
    "assign audio block break catch choice clear disconnect else elseif "\
    "emphasis enumerate error exit field filled form goto grammar help "\
    "if initial link log menu meta noinput nomatch object option p paragraph "\
    "param phoneme prompt property prosody record reprompt return s say-as "\
    "script sentence subdialog submit throw transfer value var voice vxml"

vxml_attributes=\
    "accept age alphabet anchor application base beep bridge category charset "\
    "classid cond connecttimeout content contour count dest destexpr dtmf dtmfterm "\
    "duration enctype event eventexpr expr expritem fetchtimeout finalsilence "\
    "gender http-equiv id level maxage maxstale maxtime message messageexpr "\
    "method mime modal mode name namelist next nextitem ph pitch range rate "\
    "scope size sizeexpr skiplist slot src srcexpr sub time timeexpr timeout "\
    "transferaudio type value variant version volume xml:lang"

vxml_keywords = vxml_elements + " " + vxml_attributes + " " + "public !doctype"

html4_elements=\
    "a abbr acronym address applet area b base basefont " \
    "bdo big blockquote body br button caption center " \
    "cite code col colgroup dd del dfn dir div dl dt em " \
    "fieldset font form frame frameset h1 h2 h3 h4 h5 h6 " \
    "head hr html i iframe img input ins isindex kbd label " \
    "legend li link map menu meta noframes noscript " \
    "object ol optgroup option p param pre q s samp " \
    "script select small span strike strong style sub sup " \
    "table tbody td textarea tfoot th thead title tr tt u ul " \
    "var xml xmlns"

html5_elements=\
    "article aside audio canvas command datalist details dialog " \
    "embed figcaption figure footer header hgroup keygen mark menu " \
    "meter nav output progress rp rt ruby section source summary " \
    "time video"

# Note: There hypertext_elements are not sorted!
hypertext_elements = html4_elements + " " + html5_elements

hypertext_attributes=\
    "abbr accept-charset accept accesskey action align alink " \
    "alt archive axis background bgcolor border " \
    "cellpadding cellspacing char charoff charset checked cite " \
    "class classid clear codebase codetype color cols colspan " \
    "compact content coords " \
    "data datafld dataformatas datapagesize datasrc datetime " \
    "declare defer dir disabled enctype event " \
    "face for frame frameborder " \
    "headers height href hreflang hspace http-equiv " \
    "id ismap label lang language leftmargin link longdesc " \
    "marginwidth marginheight maxlength media method multiple " \
    "name nohref noresize noshade nowrap " \
    "object onblur onchange onclick ondblclick onfocus " \
    "onkeydown onkeypress onkeyup onload onmousedown " \
    "onmousemove onmouseover onmouseout onmouseup " \
    "onreset onselect onsubmit onunload " \
    "profile prompt readonly rel rev rows rowspan rules " \
    "scheme scope selected shape size span src standby start style " \
    "summary tabindex target text title topmargin type usemap " \
    "valign value valuetype version vlink vspace width " \
    "text password checkbox radio submit reset " \
    "file hidden image"

hypertext_keywords = hypertext_elements + " " + hypertext_attributes + " " + "public !doctype"

php_keywords =\
    "and argv as argc break case cfunction class continue declare default do "\
    "die echo else elseif empty enddeclare endfor endforeach endif endswitch "\
    "endwhile E_ALL E_PARSE E_ERROR E_WARNING eval exit extends FALSE for "\
    "foreach function global HTTP_COOKIE_VARS HTTP_GET_VARS HTTP_POST_VARS "\
    "HTTP_POST_FILES HTTP_ENV_VARS HTTP_SERVER_VARS if include include_once "\
    "list new not NULL old_function or parent PHP_OS PHP_SELF PHP_VERSION "\
    "print require require_once return static switch stdClass this TRUE var "\
    "xor virtual while __FILE__ __LINE__ __sleep __wakeup"

sgml_keywords = "ELEMENT DOCTYPE ATTLIST ENTITY NOTATION"

yaml_keywords = "true false yes no"

xslt_elements = \
    "apply-templates call-template apply-imports for-each value-of copy-of "\
    "number choose if text copy variable message fallback "\
    "processing-instruction comment element attribute import include "\
    "strip-space preserve-space output key decimal-format attribute-set "\
    "variable param template namespace-alias stylesheet transform when "\
    "otherwise"

xslt_attributes = \
    "extension-element-prefixes exclude-result-prefixes id version "\
    "xmlns:xsl href elements method encoding omit-xml-declaration "\
    "standalone doctype-public doctype-system cdata-section-elements "\
    "indent media-type name match use name decimal-separator "\
    "grouping-separator infinity minus-sign NaN percent per-mille "\
    "zero-digit digit pattern-separator stylesheet-prefix "\
    "result-prefix match name priority mode select "\
    "disable-output-escaping level count from value format lang "\
    "letter-value grouping-separator grouping-size lang data-type "\
    "order case-order test use-attribute-sets " \
    "disable-output-escaping namespace terminate"\


xslt_keywords = xslt_elements + " " + xslt_attributes + " " + ' '.join(
        ['xsl:' + word for word in (xslt_elements + " " + xslt_attributes).split(' ')]
    )  

js_keywords = (
    "abstract boolean break byte case catch "
    "char class const continue debugger default "
    "delete do double else enum export "
    "extends false final finally float for function "
    "goto if implements import in instanceof "
    "int interface long native new null package "
    "private protected public return short "
    "static super switch synchronized this throw "
    "throws transient true try typeof var void "
    "while with")

# http://msdn.microsoft.com/library/default.asp?url=/library/en-us/vblr7/html/vaorivblangkeywordsall.asp
vb_keywords = (
    "addhandler addressof alias and andalso  ansi as assembly "
    "auto boolean byref byte byval call case catch "
    "cbool cbyte cchar cdate cdec cdbl char cint "
    "class clng cobj const cshort csng cstr ctype "
    "date decimal declare default delegate dim directcast do "
    "double each else elseif end enum erase error "
    "event exit false finally for friend function get "
    "gettype gosub goto handles if implements imports in "
    "inherits integer interface is let lib like long "
    "loop me mod module mustinherit mustoverride mybase myclass "
    "namespace new next not nothing notinheritable notoverridable object "
    "on option optional or orelse overloads overridable overrides "
    "paramarray preserve private property protected public raiseevent "
    "readonly redim rem removehandler resume "
    "return select set shadows step stop string structure "
    "sub synclock then throw to true try typeof " 
    "unicode until variant when while with withevents writeonly xor")

css_keywords = \
    """
    background background-attachment background-color background-image
    background-position background-repeat border border-bottom
    border-bottom-width border-color border-left border-left-width
    border-right border-right-width border-style border-top
    border-top-width border-width clear color display float font
    font-family font-size font-style font-variant font-weight height
    letter-spacing line-height list-style list-style-image
    list-style-position list-style-type margin margin-bottom margin-left
    margin-right margin-top padding padding-bottom padding-left
    padding-right padding-top text-align text-decoration text-indent
    text-transform vertical-align white-space width word-spacing
    """
css_pseudo_classes = \
    """
    active after before first first-child first-letter first-line
    focus hover lang left link right visited
    """

css_keywords_2 = \
    """
    ascent azimuth baseline bbox border-bottom-color
    border-bottom-style border-collapse border-color border-left-color
    border-left-style border-right-color border-right-style
    border-spacing border-style border-top-color border-top-style
    bottom cap-height caption-side centerline clip content
    counter-increment counter-reset cue cue-after cue-before cursor
    definition-src descent direction elevation empty-cells
    font-size-adjust font-stretch left marker-offset marks mathline
    max-height max-width min-height min-width orphans outline
    outline-color outline-style outline-width overflow page
    page-break-after page-break-before page-break-inside panose-1
    pause pause-after pause-before pitch pitch-range play-during
    position quotes richness right size slope speak speak-header
    speak-numeral speak-punctuation speech-rate src stemh stemv stress
    table-layout text-shadow top topline unicode-bidi unicode-range
    units-per-em visibility voice-family volume widows widths x-height
    z-index
    """

css_properties_3 = \
    ""

css_pseudo_elements = \
    ""
css_browser_specific_properties = \
    ""
css_browser_specific_pseudo_classes = \
    ""
css_browser_specific_pseudo_elements = \
    ""

postscript_level1_keywords = \
    "$error = == FontDirectory StandardEncoding UserObjects abs add aload " \
    "anchorsearch and arc arcn arcto array ashow astore atan awidthshow begin bind " \
    "bitshift bytesavailable cachestatus ceiling charpath clear cleardictstack " \
    "cleartomark clip clippath closefile closepath concat concatmatrix copy copypage " \
    "cos count countdictstack countexecstack counttomark currentcmykcolor " \
    "currentcolorspace currentdash currentdict currentfile currentflat currentfont " \
    "currentgray currenthsbcolor currentlinecap currentlinejoin currentlinewidth " \
    "currentmatrix currentmiterlimit currentpagedevice currentpoint currentrgbcolor " \
    "currentscreen currenttransfer cvi cvlit cvn cvr cvrs cvs cvx def defaultmatrix " \
    "definefont dict dictstack div dtransform dup echo end eoclip eofill eq " \
    "erasepage errordict exch exec execstack executeonly executive exit exp false " \
    "file fill findfont flattenpath floor flush flushfile for forall ge get " \
    "getinterval grestore grestoreall gsave gt idetmatrix idiv idtransform if ifelse " \
    "image imagemask index initclip initgraphics initmatrix inustroke invertmatrix " \
    "itransform known kshow le length lineto ln load log loop lt makefont mark " \
    "matrix maxlength mod moveto mul ne neg newpath noaccess nor not null nulldevice " \
    "or pathbbox pathforall pop print prompt pstack put putinterval quit rand rcheck " \
    "rcurveto read readhexstring readline readonly readstring rectstroke repeat " \
    "resetfile restore reversepath rlineto rmoveto roll rotate round rrand run save " \
    "scale scalefont search setblackgeneration setcachedevice setcachelimit " \
    "setcharwidth setcolorscreen setcolortransfer setdash setflat setfont setgray " \
    "sethsbcolor setlinecap setlinejoin setlinewidth setmatrix setmiterlimit " \
    "setpagedevice setrgbcolor setscreen settransfer setvmthreshold show showpage " \
    "sin sqrt srand stack start status statusdict stop stopped store string " \
    "stringwidth stroke strokepath sub systemdict token token transform translate " \
    "true truncate type ueofill undefineresource userdict usertime version vmstatus " \
    "wcheck where widthshow write writehexstring writestring xcheck xor " \

postscript_level2_keywords = \
    "GlobalFontDirectory ISOLatin1Encoding SharedFontDirectory UserObject arct " \
    "colorimage cshow currentblackgeneration currentcacheparams currentcmykcolor " \
    "currentcolor currentcolorrendering currentcolorscreen currentcolorspace " \
    "currentcolortransfer currentdevparams currentglobal currentgstate " \
    "currenthalftone currentobjectformat currentoverprint currentpacking " \
    "currentpagedevice currentshared currentstrokeadjust currentsystemparams " \
    "currentundercolorremoval currentuserparams defineresource defineuserobject " \
    "deletefile execform execuserobject filenameforall fileposition filter " \
    "findencoding findresource gcheck globaldict glyphshow gstate ineofill infill " \
    "instroke inueofill inufill inustroke languagelevel makepattern packedarray " \
    "printobject product realtime rectclip rectfill rectstroke renamefile " \
    "resourceforall resourcestatus revision rootfont scheck selectfont serialnumber " \
    "setbbox setblackgeneration setcachedevice2 setcacheparams setcmykcolor setcolor " \
    "setcolorrendering setcolorscreen setcolorspace setcolortranfer setdevparams " \
    "setfileposition setglobal setgstate sethalftone setobjectformat setoverprint " \
    "setpacking setpagedevice setpattern setshared setstrokeadjust setsystemparams " \
    "setucacheparams setundercolorremoval setuserparams setvmthreshold shareddict " \
    "startjob uappend ucache ucachestatus ueofill ufill undef undefinefont " \
    "undefineresource undefineuserobject upath ustroke ustrokepath vmreclaim " \
    "writeobject xshow xyshow yshow"
    
postscript_level3_keywords = \
    "cliprestore clipsave composefont currentsmoothness findcolorrendering " \
    "setsmoothness shfill"

postscript_ripspecific_keywords = \
    ".begintransparencygroup .begintransparencymask .bytestring .charboxpath " \
    ".currentaccuratecurves .currentblendmode .currentcurvejoin .currentdashadapt " \
    ".currentdotlength .currentfilladjust2 .currentlimitclamp .currentopacityalpha " \
    ".currentoverprintmode .currentrasterop .currentshapealpha " \
    ".currentsourcetransparent .currenttextknockout .currenttexturetransparent " \
    ".dashpath .dicttomark .discardtransparencygroup .discardtransparencymask " \
    ".endtransparencygroup .endtransparencymask .execn .filename .filename " \
    ".fileposition .forceput .forceundef .forgetsave .getbitsrect .getdevice " \
    ".inittransparencymask .knownget .locksafe .makeoperator .namestring .oserrno " \
    ".oserrorstring .peekstring .rectappend .runandhide .setaccuratecurves " \
    ".setblendmode .setcurvejoin .setdashadapt .setdebug .setdefaultmatrix " \
    ".setdotlength .setfilladjust2 .setlimitclamp .setmaxlength .setopacityalpha " \
    ".setoverprintmode .setrasterop .setsafe .setshapealpha .setsourcetransparent " \
    ".settextknockout .settexturetransparent .stringbreak .stringmatch .tempfile " \
    ".type1decrypt .type1encrypt .type1execchar .unread arccos arcsin copydevice " \
    "copyscanlines currentdevice finddevice findlibfile findprotodevice flushpage " \
    "getdeviceprops getenv makeimagedevice makewordimagedevice max min " \
    "putdeviceprops setdevice"
