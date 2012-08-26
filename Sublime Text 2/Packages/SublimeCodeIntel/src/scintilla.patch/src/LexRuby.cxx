// Scintilla source code edit control
/** @file LexRuby.cxx
 ** Lexer for Ruby.
 **/
// Copyright 2001- by Clemens Wyss <wys@helbling.ch>
// The License.txt file describes the conditions under which this software may be distributed.

#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdio.h>
#include <stdarg.h>

#include "Platform.h"

#include "PropSet.h"
#include "Accessor.h"
#include "KeyWords.h"
#include "Scintilla.h"
#include "SciLexer.h"

#ifdef SCI_NAMESPACE
using namespace Scintilla;
#endif

//XXX Identical to Perl, put in common area
static inline bool isEOLChar(char ch) {
    return (ch == '\r') || (ch == '\n');
}

#define isSafeASCII(ch) ((unsigned int)(ch) <= 127)
// This one's redundant, but makes for more readable code
#define isHighBitChar(ch) ((unsigned int)(ch) > 127)

static inline bool isSafeAlpha(char ch) {
    return (isSafeASCII(ch) && isalpha(ch)) || ch == '_';
}

static inline bool isSafeAlnum(char ch) {
    return (isSafeASCII(ch) && isalnum(ch)) || ch == '_';
}

static inline bool isSafeAlnumOrHigh(char ch) {
    return isHighBitChar(ch) || isalnum(ch) || ch == '_';
}

static inline bool isSafeDigit(char ch) {
    return isSafeASCII(ch) && isdigit(ch);
}

static inline bool isSafeWordcharOrHigh(char ch) {
    // Error: scintilla's KeyWords.h includes '.' as a word-char
    // we want to separate things that can take methods from the
    // methods.
    return isHighBitChar(ch) || isalnum(ch) || ch == '_';
}

static bool inline iswhitespace(char ch) {
    return ch == ' ' || ch == '\t';
}

#define MAX_KEYWORD_LENGTH 200

#define STYLE_MASK 63
#define actual_style(style) (style & STYLE_MASK)

static bool followsDot(unsigned int pos, Accessor &styler) {
    styler.Flush();
    for (; pos >= 1; --pos) {
        int style = actual_style(styler.StyleAt(pos));
        char ch;
        switch (style) {
            case SCE_RB_DEFAULT:
                ch = styler[pos];
                if (ch == ' ' || ch == '\t') {
                    //continue
                } else {
                    return false;
                }
                break;
                
            case SCE_RB_OPERATOR:
                return styler[pos] == '.';

            default:
                return false;
        }
    }
    return false;
}

// Forward declarations
static bool keywordIsAmbiguous(const char *prevWord);
static bool keywordDoStartsLoop(int pos,
                                Accessor &styler);
static bool keywordIsModifier(const char *word,
                              int pos,
                              Accessor &styler);

static char* getCurrentWord(unsigned int start, unsigned int end, Accessor &styler) {
    static char s[MAX_KEYWORD_LENGTH];
    unsigned int lim = end - start + 1; // num chars to copy
    if (lim >= MAX_KEYWORD_LENGTH) {
        s[0] = 0;
        return s;
    }
    unsigned int i, j;
    for (i = start, j = 0; j < lim; i++, j++) {
        s[j] = styler[i];
    }
    s[j] = '\0';
    return s;
}

static int ClassifyWordRb(unsigned int start, unsigned int end, WordList &keywords, Accessor &styler, char *currWord, char *prevWord) {
    int chAttr;
    if (!currWord) {
        return SCE_RB_IDENTIFIER;
    }
    if (0 == strcmp(prevWord, "class"))
        chAttr = SCE_RB_CLASSNAME;
    else if (0 == strcmp(prevWord, "module"))
        chAttr = SCE_RB_MODULE_NAME;
    else if (0 == strcmp(prevWord, "def"))
        chAttr = SCE_RB_DEFNAME;
    else if (keywords.InList(currWord) && !followsDot(start - 1, styler)) {
        if (keywordIsAmbiguous(currWord)
            && keywordIsModifier(currWord, start, styler)) {
            
            // Demoted keywords are colored as keywords,
            // but do not affect changes in indentation.
            //
            // Consider the word 'if':
            // 1. <<if test ...>> : normal
            // 2. <<stmt if test>> : demoted
            // 3. <<lhs = if ...>> : normal: start a new indent level
            // 4. <<obj.if = 10>> : color as identifer, since it follows '.'
            
            chAttr = SCE_RB_WORD_DEMOTED;
        } else {
            chAttr = SCE_RB_WORD;
        }
    } else
    chAttr = SCE_RB_IDENTIFIER;
    styler.ColourTo(end, chAttr);
    if (chAttr == SCE_RB_WORD) {
        strcpy(prevWord, currWord);
    } else {
        prevWord[0] = 0;
    }
    return chAttr;
}


//XXX Identical to Perl, put in common area
static bool isMatch(Accessor &styler, int lengthDoc, int pos, const char *val) {
    if ((pos + static_cast<int>(strlen(val))) >= lengthDoc) {
        return false;
    }
    while (*val) {
        if (*val != styler[pos++]) {
            return false;
        }
        val++;
    }
    return true;
}

// Do Ruby better -- find the end of the line, work back,
// and then check for leading white space

// Precondition: the here-doc target can be indented
static bool lookingAtHereDocDelim(Accessor     &styler,
                                  int           pos,
                                  int           lengthDoc,
                                  const char   *HereDocDelim)
{
    if (!isMatch(styler, lengthDoc, pos, HereDocDelim)) {
        return false;
    }
    while (--pos > 0) {
        char ch = styler[pos];
        if (isEOLChar(ch)) {
            return true;
        } else if (ch != ' ' && ch != '\t') {
            return false;
        }
    }
    return false;
}

//XXX Identical to Perl, put in common area
static char opposite(char ch) {
    if (ch == '(')
        return ')';
    if (ch == '[')
        return ']';
    if (ch == '{')
        return '}';
    if (ch == '<')
        return '>';
    return ch;
}

// Null transitions when we see we've reached the end
// and need to relex the curr char.

static void redo_char(int &i, char &ch, char &chNext, char &chNext2,
                      int &state) {
    i--;
    chNext2 = chNext;
    chNext = ch;
    state = SCE_RB_DEFAULT;
}

static void advance_char(int &i, char &ch, char &chNext, char &chNext2) {
    i++;
    ch = chNext;
    chNext = chNext2;
}

// precondition: startPos points to one after the EOL char
static bool currLineContainsHereDelims(int& startPos,
                                       Accessor &styler) {
    if (startPos <= 1)
        return false;

    int pos;
    for (pos = startPos - 1; pos > 0; pos--) {
        char ch = styler.SafeGetCharAt(pos);
        if (isEOLChar(ch)) {
            // Leave the pointers where they are -- there are no
            // here doc delims on the current line, even if
            // the EOL isn't default style
            
            return false;
        } else {
            styler.Flush();
            if (actual_style(styler.StyleAt(pos)) == SCE_RB_HERE_DELIM) {
                break;
            }
        }
    }
    if (pos == 0) {
        return false;
    }
    // Update the pointers so we don't have to re-analyze the string
    startPos = pos;
    return true;
}

// This class is used by the enter and exit methods, so it needs
// to be hoisted out of the function.

class QuoteCls {
    public:
    int  Count;
    char Up;
    char Down;
    QuoteCls() {
        this->New();
    }
    void New() {
        Count = 0;
        Up    = '\0';
        Down  = '\0';
    }
    void Open(char u) {
        Count++;
        Up    = u;
        Down  = opposite(Up);
    }
    QuoteCls(const QuoteCls& q) {
        // copy constructor -- use this for copying in
        Count = q.Count;
        Up    = q.Up;
        Down  = q.Down;
    }
    QuoteCls& operator=(const QuoteCls& q) { // assignment constructor
        if (this != &q) {
            Count = q.Count;
            Up    = q.Up;
            Down  = q.Down;
        }
        return *this;
    }
            
};


static void enterInnerExpression(int  *p_inner_string_types,
                                 int  *p_inner_expn_brace_counts,
                                 QuoteCls *p_inner_quotes,
                                 int&  inner_string_count,
                                 int&  state,
                                 int&  brace_counts,
                                 QuoteCls curr_quote
                                 ) {
    p_inner_string_types[inner_string_count] = state;
    state = SCE_RB_DEFAULT;
    p_inner_expn_brace_counts[inner_string_count] = brace_counts;
    brace_counts = 0;
    p_inner_quotes[inner_string_count] = curr_quote;
    ++inner_string_count;
}

static void exitInnerExpression(int *p_inner_string_types,
                                 int *p_inner_expn_brace_counts,
                                 QuoteCls *p_inner_quotes,
                                 int& inner_string_count,
                                 int& state,
                                 int&  brace_counts,
                                 QuoteCls& curr_quote
                                ) {
    --inner_string_count;
    state = p_inner_string_types[inner_string_count];
    brace_counts = p_inner_expn_brace_counts[inner_string_count];
    curr_quote = p_inner_quotes[inner_string_count];
}

static bool isEmptyLine(int pos,
                        Accessor &styler) {
    int spaceFlags = 0;
    int lineCurrent = styler.GetLine(pos);
    int indentCurrent = styler.IndentAmount(lineCurrent, &spaceFlags, NULL);
    return (indentCurrent & SC_FOLDLEVELWHITEFLAG) != 0;
}

static bool RE_CanFollowIdentifier(const char *keyword) {
// Members of Kernel that can precede strings or REs:
    if (!strcmp(keyword, "eval")
        || !strcmp(keyword, "exec")
        || !strcmp(keyword, "open")
        || !strcmp(keyword, "p")
        || !strcmp(keyword, "print")
        || !strcmp(keyword, "printf")
        || !strcmp(keyword, "puts")
        || !strcmp(keyword, "require")
        || !strcmp(keyword, "split")
        || !strcmp(keyword, "sprintf")
        || !strcmp(keyword, "system")) {
        return true;
    }
    return false;
}

static bool RE_CanFollowKeyword(const char *keyword) {
    if (!strcmp(keyword, "and")
        || !strcmp(keyword, "begin")
        || !strcmp(keyword, "break")
        || !strcmp(keyword, "case")
        || !strcmp(keyword, "do")
        || !strcmp(keyword, "else")
        || !strcmp(keyword, "elsif")
        || !strcmp(keyword, "if")
        || !strcmp(keyword, "next")
        || !strcmp(keyword, "return")
        || !strcmp(keyword, "when")
        || !strcmp(keyword, "unless")
        || !strcmp(keyword, "until")
        || !strcmp(keyword, "not")
        || !strcmp(keyword, "or")) {
        return true;
    }
    return false;
}

// Look at chars up to but not including endPos
// Don't look at styles in case we're looking forward

static int skipWhitespace(int startPos,
                           int endPos,
                           Accessor &styler) {
    for (int i = startPos; i < endPos; i++) {
        if (!iswhitespace(styler[i])) {
            return i;
        }
    }
    return endPos;
}
    
// This routine looks for false positives like
// undef foo, <<
// There aren't too many.
//
// iPrev points to the start of <<

static bool sureThisIsHeredoc(int iPrev,
                              Accessor &styler,
                              char *prevWord) {
                    
    // Not so fast, since Ruby's so dynamic.  Check the context
    // to make sure we're OK.
    int prevStyle;
    int lineStart = styler.GetLine(iPrev);
    int lineStartPosn = styler.LineStart(lineStart);
    styler.Flush();

    // Find the first word after some whitespace
    int firstWordPosn = skipWhitespace(lineStartPosn, iPrev, styler);
    if (firstWordPosn >= iPrev) {
        // Have something like {^     <<}
        //XXX Look at the first previous non-comment non-white line
        // to establish the context.  Not too likely though.
        return true;
    } else {
        switch (prevStyle = styler.StyleAt(firstWordPosn)) {
        case SCE_RB_WORD:
        case SCE_RB_WORD_DEMOTED:
        case SCE_RB_IDENTIFIER:
            break;
        default:
            return true;
        }
    }
    int firstWordEndPosn = firstWordPosn;
    char *dst = prevWord;
    for (;;) {
        if (firstWordEndPosn >= iPrev ||
            styler.StyleAt(firstWordEndPosn) != prevStyle) {
            *dst = 0;
            break;
        }
        *dst++ = styler[firstWordEndPosn];
        firstWordEndPosn += 1;
    }
    //XXX Write a style-aware thing to regex scintilla buffer objects
    if (!strcmp(prevWord, "undef")
        || !strcmp(prevWord, "def")
        || !strcmp(prevWord, "alias")) {
        // These keywords are what we were looking for
        return false;
    }
    return true;
}

// Routine that saves us from allocating a buffer for the here-doc target
// targetEndPos points one past the end of the current target
static bool haveTargetMatch(int currPos,
                            int lengthDoc,
                            int targetStartPos,
                            int targetEndPos,
                            Accessor &styler) {
    if (lengthDoc - currPos < targetEndPos - targetStartPos) {
        return false;
    }
    int i, j;
    for (i = targetStartPos, j = currPos;
         i < targetEndPos && j < lengthDoc;
         i++, j++) {
        if (styler[i] != styler[j]) {
            return false;
        }
    }
    return true;
}

// We need a check because the form
// [identifier] <<[target]
// is ambiguous.  The Ruby lexer/parser resolves it by
// looking to see if [identifier] names a variable or a
// function.  If it's the first, it's the start of a here-doc.
// If it's a var, it's an operator.  This lexer doesn't
// maintain a symbol table, so it looks ahead to see what's
// going on, in cases where we have
// ^[white-space]*[identifier([.|::]identifier)*][white-space]*<<[target]
//
// If there's no occurrence of [target] on a line, assume we don't.

// return true == yes, we have no heredocs

static bool sureThisIsNotHeredoc(int lt2StartPos,
                                 Accessor &styler) {
    int prevStyle;
     // Use full document, not just part we're styling
    int lengthDoc = styler.Length();
    int lineStart = styler.GetLine(lt2StartPos);
    int lineStartPosn = styler.LineStart(lineStart);
    styler.Flush();
    const bool definitely_not_a_here_doc = true;
    const bool looks_like_a_here_doc = false;
    
    // Find the first word after some whitespace
    int firstWordPosn = skipWhitespace(lineStartPosn, lt2StartPos, styler);
    if (firstWordPosn >= lt2StartPos) {
        return definitely_not_a_here_doc;
    }
    prevStyle = styler.StyleAt(firstWordPosn);
    // If we have '<<' following a keyword, it's not a heredoc
    if (prevStyle != SCE_RB_IDENTIFIER) {
        return definitely_not_a_here_doc;
    }
    int newStyle = prevStyle;
    // Some compilers incorrectly warn about uninit newStyle
    for (firstWordPosn += 1; firstWordPosn <= lt2StartPos; firstWordPosn += 1) {
        // Inner loop looks at the name
        for (; firstWordPosn <= lt2StartPos; firstWordPosn += 1) {
            newStyle = styler.StyleAt(firstWordPosn);
            if (newStyle != prevStyle) {
                break;
            }
        }
        // Do we have '::' or '.'?
        if (firstWordPosn < lt2StartPos && newStyle == SCE_RB_OPERATOR) {
            char ch = styler[firstWordPosn];
            if (ch == '.') {
                // yes
            } else if (ch == ':') {
                if (styler.StyleAt(++firstWordPosn) != SCE_RB_OPERATOR) {
                    return definitely_not_a_here_doc;
                } else if (styler[firstWordPosn] != ':') {
                    return definitely_not_a_here_doc;
                }
            } else {
                break;
            }
        } else {
            break;
        }
    }
    // Skip next batch of white-space
    firstWordPosn = skipWhitespace(firstWordPosn, lt2StartPos, styler);
    if (firstWordPosn != lt2StartPos) {
        // Have [[^ws[identifier]ws[*something_else*]ws<<
        return definitely_not_a_here_doc;
    }
    // OK, now 'j' will point to the current spot moving ahead
    int j = firstWordPosn + 1;
    if (styler.StyleAt(j) != SCE_RB_OPERATOR || styler[j] != '<') {
        // This shouldn't happen
        return definitely_not_a_here_doc;
    }
    int nextLineStartPosn = styler.LineStart(lineStart + 1);
    if (nextLineStartPosn >= lengthDoc) {
        return definitely_not_a_here_doc;
    }
    j = skipWhitespace(j + 1, nextLineStartPosn, styler);
    if (j >= lengthDoc) {
        return definitely_not_a_here_doc;
    }
    bool allow_indent;
    int target_start, target_end;
    // From this point on no more styling, since we're looking ahead
    if (styler[j] == '-') {
        allow_indent = true;
        j++;
    } else {
        allow_indent = false;
    }

    // Allow for quoted targets.
    char target_quote = 0;
    switch (styler[j]) {
    case '\'':
    case '"':
    case '`':
        target_quote = styler[j];
        j += 1;
    }
    
    if (isSafeAlnum(styler[j])) {
        // Init target_end because some compilers think it won't
        // be initialized by the time it's used
        target_start = target_end = j;
        j++;
    } else {
        return definitely_not_a_here_doc;
    }
    for (; j < lengthDoc; j++) {
        if (!isSafeAlnum(styler[j])) {
            if (target_quote && styler[j] != target_quote) {
                // unquoted end
                return definitely_not_a_here_doc;
            }

            // And for now make sure that it's a newline
            // don't handle arbitrary expressions yet
            
            target_end = j;
            if (target_quote) {
                // Now we can move to the character after the string delimiter.
                j += 1;
            }
            j = skipWhitespace(j, lengthDoc, styler);
            if (j >= lengthDoc) {
                return definitely_not_a_here_doc;
            } else {
                char ch = styler[j];
                if (ch == '#' || isEOLChar(ch)) {
                    // This is OK, so break and continue;
                    break;
                } else {
                    return definitely_not_a_here_doc;
                }
            }
        }
    }

    // Just look at the start of each line
    int last_line = styler.GetLine(lengthDoc - 1);
    // But don't go too far
    if (last_line > lineStart + 50) {
        last_line = lineStart + 50;
    }
    for (int line_num = lineStart + 1; line_num <= last_line; line_num++) {
        if (allow_indent) {
            j = skipWhitespace(styler.LineStart(line_num), lengthDoc, styler);
        } else {
            j = styler.LineStart(line_num);
        }
        // target_end is one past the end
        if (haveTargetMatch(j, lengthDoc, target_start, target_end, styler)) {
            // We got it
            return looks_like_a_here_doc;
        }
    }
    return definitely_not_a_here_doc;
}

//todo: if we aren't looking at a stdio character,
// move to the start of the first line that is not in a 
// multi-line construct

// KOMODO -- interactive shell colorizing
static bool isStdioChar(int style) {
    switch (style) {
    case SCE_RB_STDIN:
    case SCE_RB_STDOUT:
    case SCE_RB_STDERR:
        return true;
    }
    return false;
}
    

// KOMODO -- interactive shell colorizing
static int prevNonNewlinePos(int line,
                             Accessor &styler) {
    if (line <= 0) return -1;
    int lineStart = styler.LineStart(line);
    if (lineStart == 0) return -1;
    // Move to the previous line
    int pos = lineStart - 1;
    char ch = styler.SafeGetCharAt(pos);
    while (pos > 0 && (ch == '\n' || ch == '\r')) {
        ch = styler.SafeGetCharAt(--pos);
    }
    return pos;
}

static void synchronizeDocStart(unsigned int& startPos,
                                int &length,
                                int &initStyle,
                                Accessor &styler) {

    styler.Flush();
    int style;
    int pos = startPos;
    // Quick way to characterize each line
    int currLine = styler.GetLine(pos);
    while (currLine > 0) {
        // Now look at the style before the previous line's EOL
        // KOMODO -- interactive shell colorizing
        pos = prevNonNewlinePos(currLine, styler);
        if (pos == -1) {
            currLine = 0;
            break;
        }
        style = actual_style(styler.StyleAt(pos));
        if (isStdioChar(style)) {
            break;
        } else if (styler.SafeGetCharAt(pos) == '\\') {
            // Continuation line -- keep going
        } else if (actual_style(styler.StyleAt(pos + 1)) != SCE_RB_DEFAULT) {
            // Part of multi-line construct -- keep going
        } else if (currLineContainsHereDelims(pos, styler)) {
            // Keep going, with pos and length now pointing
            // at the end of the here-doc delimiter
        } else {
            break;
        }
        currLine = styler.GetLine(pos);
    }
    pos = styler.LineStart(currLine);
    length += (startPos - pos);
    startPos = pos;
    initStyle = SCE_RB_DEFAULT;
}

static void ColouriseRbDoc(unsigned int startPos, int length, int initStyle,
                           WordList *keywordlists[], Accessor &styler) {

    // Lexer for Ruby often has to backtrack to start of current style to determine
    // which characters are being used as quotes, how deeply nested is the
    // start position and what the termination string is for here documents
    
    WordList &keywords = *keywordlists[0];

    class HereDocCls {
    public:
        int State;
        // States
        // 0: '<<' encountered
        // 1: collect the delimiter
        // 1b: text between the end of the delimiter and the EOL
        // 2: here doc text (lines after the delimiter)
        char Quote;     // the char after '<<'
        bool Quoted;        // true if Quote in ('\'','"','`')
        int DelimiterLength;    // strlen(Delimiter)
        char Delimiter[256];    // the Delimiter, limit of 256: from Perl
        bool CanBeIndented;
        HereDocCls() {
            State = 0;
            DelimiterLength = 0;
            Delimiter[0] = '\0';
            CanBeIndented = false;
        }
    };
    HereDocCls HereDoc; 

    QuoteCls Quote;

    int numDots = 0;  // For numbers --
                      // Don't start lexing in the middle of a num
    int num_e_s = 0;  // Also for floating-point numbers

    synchronizeDocStart(startPos, length, initStyle, styler // ref args
                        );

    bool preferRE = true;
    int state = initStyle;
    int lengthDoc = startPos + length;

    char prevWord[MAX_KEYWORD_LENGTH + 1]; // 1 byte for zero
    prevWord[0] = '\0';
    if (length == 0)
        return;

    char chPrev = styler.SafeGetCharAt(startPos - 1);
    char chNext = styler.SafeGetCharAt(startPos);
    bool is_real_number = true;   // Differentiate between constants and ?-sequences.
    // Ruby uses a different mask because bad indentation is marked by oring with 32
    styler.StartAt(startPos, 127);
    styler.StartSegment(startPos);

    static int q_states[] = {SCE_RB_STRING_Q,
                             SCE_RB_STRING_QQ,
                             SCE_RB_STRING_QR,
                             SCE_RB_STRING_QW,
                             SCE_RB_STRING_QW,
                             SCE_RB_STRING_QX};
    static const char* q_chars = "qQrwWx";

    // In most cases a value of 2 should be ample for the code in the
    // Ruby library, and the code the user is likely to enter.
    // For example,
    // fu_output_message "mkdir #{options[:mode] ? ('-m %03o ' % options[:mode]) : ''}#{list.join ' '}"
    //     if options[:verbose]
    // from fileutils.rb nests to a level of 2
    // If the user actually hits a 6th occurrence of '#{' in a double-quoted
    // string (including regex'es, %Q, %<sym>, %w, and other strings
    // that interpolate), it will stay as a string.  The problem with this
    // is that quotes might flip, a 7th '#{' will look like a comment,
    // and code-folding might be wrong.

    // If anyone runs into this problem, I recommend raising this
    // value slightly higher to replacing the fixed array with a linked
    // list.  Keep in mind this code will be called everytime the lexer
    // is invoked.

#define INNER_STRINGS_MAX_COUNT 5
    // These vars track our instances of "...#{,,,%Q<..#{,,,}...>,,,}..."
    int inner_string_types[INNER_STRINGS_MAX_COUNT];
    // Track # braces when we push a new #{ thing
    int inner_expn_brace_counts[INNER_STRINGS_MAX_COUNT];
    QuoteCls inner_quotes[INNER_STRINGS_MAX_COUNT];
    int inner_string_count = 0;
    int brace_counts = 0;   // Number of #{ ... } things within an expression

    int i;
    for (i = 0; i < INNER_STRINGS_MAX_COUNT; i++) {
        inner_string_types[i] = 0;
        inner_expn_brace_counts[i] = 0;
    }
    for (i = startPos; i < lengthDoc; i++) {
        char ch = chNext;
        chNext = styler.SafeGetCharAt(i + 1);
        char chNext2 = styler.SafeGetCharAt(i + 2);

        if (styler.IsLeadByte(ch)) {
            chNext = chNext2;
            chPrev = ' ';
            i += 1;
            continue;
        }
        
        // skip on DOS/Windows
        //No, don't, because some things will get tagged on,
        // so we won't recognize keywords, for example
#if 0
        if (ch == '\r' && chNext == '\n') {
            continue;
        }
#endif
            
        if (HereDoc.State == 1 && isEOLChar(ch)) {
            // Begin of here-doc (the line after the here-doc delimiter):
            HereDoc.State = 2;
            styler.ColourTo(i-1, state);
            // Don't check for a missing quote, just jump into
            // the here-doc state
            state = SCE_RB_HERE_Q;
        }

        // Regular transitions
        if (state == SCE_RB_DEFAULT) {
            if (isSafeDigit(ch)) {
                styler.ColourTo(i - 1, state);
                state = SCE_RB_NUMBER;
                is_real_number = true;
                numDots = 0;
                num_e_s = 0; // For the exponent part in a float constant
            } else if (isHighBitChar(ch) || iswordstart(ch)) {
                styler.ColourTo(i - 1, state);
                state = SCE_RB_WORD;
            } else if (ch == '#') {
                styler.ColourTo(i - 1, state);
                state = SCE_RB_COMMENTLINE;
            } else if (ch == '=') {
                // =begin indicates the start of a comment (doc) block
                if (i == 0 || (isEOLChar(chPrev)
                    && chNext == 'b'
                    && styler.SafeGetCharAt(i + 2) == 'e'
                    && styler.SafeGetCharAt(i + 3) == 'g'
                    && styler.SafeGetCharAt(i + 4) == 'i'
                    && styler.SafeGetCharAt(i + 5) == 'n'
                    && !isSafeWordcharOrHigh(styler.SafeGetCharAt(i + 6)))) {
                    styler.ColourTo(i - 1, state);
                    state = SCE_RB_POD;
                } else {
                    styler.ColourTo(i - 1, state);
                    styler.ColourTo(i, SCE_RB_OPERATOR);
                    preferRE = true;
                }
            } else if (ch == '"') {
                styler.ColourTo(i - 1, state);
                state = SCE_RB_STRING;
                Quote.New();
                Quote.Open(ch);
            } else if (ch == '\'') {
                styler.ColourTo(i - 1, state);
                state = SCE_RB_CHARACTER;
                Quote.New();
                Quote.Open(ch);
            } else if (ch == '`') {
                styler.ColourTo(i - 1, state);
                state = SCE_RB_BACKTICKS;
                Quote.New();
                Quote.Open(ch);
            } else if (ch == '@') {
                // Instance or class var
                styler.ColourTo(i - 1, state);
                if (chNext == '@') {
                    state = SCE_RB_CLASS_VAR;
                    advance_char(i, ch, chNext, chNext2); // pass by ref
                } else {
                    state = SCE_RB_INSTANCE_VAR;
                }
            } else if (ch == '$') {
                // Check for a builtin global
                styler.ColourTo(i - 1, state);
                // Recognize it bit by bit
                state = SCE_RB_GLOBAL;
            } else if (ch == '/' && preferRE) {
                // Ambigous operator
                styler.ColourTo(i - 1, state);
                state = SCE_RB_REGEX;
                Quote.New();
                Quote.Open(ch);
            } else if (ch == '<' && chNext == '<' && chNext2 != '=') {

                // Recognise the '<<' symbol - either a here document or a binary op
                styler.ColourTo(i - 1, state);
                i++;
                chNext = chNext2;
                styler.ColourTo(i, SCE_RB_OPERATOR);

                if (! (strchr("\"\'`_-", chNext2) || isSafeAlpha(chNext2))) {
                    // It's definitely not a here-doc,
                    // based on Ruby's lexer/parser in the
                    // heredoc_identifier routine.
                    // Nothing else to do.
                } else if (preferRE) {
                    if (sureThisIsHeredoc(i - 1, styler, prevWord)) {
                        state = SCE_RB_HERE_DELIM;
                        HereDoc.State = 0;
                    }
                    // else leave it in default state
                } else {
                    if (sureThisIsNotHeredoc(i - 1, styler)) {
                        // leave state as default
                        // We don't have all the heuristics Perl has for indications
                        // of a here-doc, because '<<' is overloadable and used
                        // for so many other classes.
                    } else {
                        state = SCE_RB_HERE_DELIM;
                        HereDoc.State = 0;
                    }
                }
                preferRE = (state != SCE_RB_HERE_DELIM);
            } else if (ch == ':') {
                styler.ColourTo(i - 1, state);
                if (chNext == ':') {
                    // Mark "::" as an operator, not symbol start
                    styler.ColourTo(i + 1, SCE_RB_OPERATOR);
                    advance_char(i, ch, chNext, chNext2); // pass by ref
                    state = SCE_RB_DEFAULT;
                    preferRE = false;
                } else if (isSafeWordcharOrHigh(chNext)) {
                    state = SCE_RB_SYMBOL;
                } else if (strchr("[*!~+-*/%=<>&^|", chNext)) {
                    // Do the operator analysis in-line, looking ahead
                    // Based on the table in pickaxe 2nd ed., page 339
                    bool doColoring = true;
                    switch (chNext) {
                    case '[':
                        if (chNext2 == ']' ) {
                            char ch_tmp = styler.SafeGetCharAt(i + 3);
                            if (ch_tmp == '=') {
                                i += 3;
                                ch = ch_tmp;
                                chNext = styler.SafeGetCharAt(i + 1);
                            } else {
                                i += 2;
                                ch = chNext2;
                                chNext = ch_tmp;
                            }
                        } else {
                            doColoring = false;
                        }
                        break;

                    case '*':
                        if (chNext2 == '*') {
                            i += 2;
                            ch = chNext2;
                            chNext = styler.SafeGetCharAt(i + 1);
                        } else {
                            advance_char(i, ch, chNext, chNext2);
                        }
                        break;

                    case '!':
                        if (chNext2 == '=' || chNext2 == '~') {
                            i += 2;
                            ch = chNext2;
                            chNext = styler.SafeGetCharAt(i + 1);
                        } else {
                            advance_char(i, ch, chNext, chNext2);
                        }
                        break;

                    case '<':
                        if (chNext2 == '<') {
                            i += 2;
                            ch = chNext2;
                            chNext = styler.SafeGetCharAt(i + 1);
                        } else if (chNext2 == '=') {
                            char ch_tmp = styler.SafeGetCharAt(i + 3);
                            if (ch_tmp == '>') {  // <=> operator
                                i += 3;
                                ch = ch_tmp;
                                chNext = styler.SafeGetCharAt(i + 1);
                            } else {
                                i += 2;
                                ch = chNext2;
                                chNext = ch_tmp;
                            }
                        } else {
                            advance_char(i, ch, chNext, chNext2);
                        }
                        break;

                    default:
                        // Simple one-character operators
                        advance_char(i, ch, chNext, chNext2);
                        break;
                    }
                    if (doColoring) {
                        styler.ColourTo(i, SCE_RB_SYMBOL);
                        state = SCE_RB_DEFAULT;
                    }
                } else if (strchr(" \t\r\n", chNext)) {
                    styler.ColourTo(i, SCE_RB_OPERATOR);
                    state = SCE_RB_DEFAULT;
                    preferRE = true;
                } else if (!preferRE) {
                    // Don't color symbol strings (yet)
                    // Just color the ":" and color rest as string
                    styler.ColourTo(i, SCE_RB_SYMBOL);
                    state = SCE_RB_DEFAULT;
                } else {
                    styler.ColourTo(i, SCE_RB_OPERATOR);
                    state = SCE_RB_DEFAULT;
                    preferRE = true;
                }
            } else if (ch == '%') {
                styler.ColourTo(i - 1, state);
                bool have_string = false;
                if (strchr(q_chars, chNext) && !isSafeWordcharOrHigh(chNext2)) {
                    Quote.New();
                    const char *hit = strchr(q_chars, chNext);
                    if (hit != NULL) {
                        state = q_states[hit - q_chars];
                        Quote.Open(chNext2);
                        i += 2;
                        ch = chNext2;
            chNext = styler.SafeGetCharAt(i + 1);
                        have_string = true;
                    }
                } else if (preferRE && !isSafeWordcharOrHigh(chNext)) {
                    // Ruby doesn't allow high bit chars here,
                    // but the editor host might
                    state = SCE_RB_STRING_QQ;
                    Quote.Open(chNext);
                    advance_char(i, ch, chNext, chNext2); // pass by ref
                    have_string = true;
                }
                if (!have_string) {
                    styler.ColourTo(i, SCE_RB_OPERATOR);
                    // stay in default
                    preferRE = true;
                }
            } else if (ch == '?') {
                styler.ColourTo(i - 1, state);
                if (iswhitespace(chNext) || chNext == '\n' || chNext == '\r') {
                    styler.ColourTo(i, SCE_RB_OPERATOR);
                } else {
                    // It's the start of a character code escape sequence
                    // Color it as a number.
                    state = SCE_RB_NUMBER;
                    is_real_number = false;
                }
            } else if (isoperator(ch) || ch == '.') {
                styler.ColourTo(i - 1, state);
                styler.ColourTo(i, SCE_RB_OPERATOR);
                // If we're ending an expression or block,
                // assume it ends an object, and the ambivalent
                // constructs are binary operators
                //
                // So if we don't have one of these chars,
                // we aren't ending an object exp'n, and ops
                // like : << / are unary operators.
                
                if (ch == '{') {
                    ++brace_counts;
                    preferRE = true;
                } else if (ch == '}' && --brace_counts < 0
                           && inner_string_count > 0) {
                    styler.ColourTo(i, SCE_RB_OPERATOR);
                    exitInnerExpression(inner_string_types,
                                        inner_expn_brace_counts,
                                        inner_quotes,
                                        inner_string_count,
                                        state, brace_counts, Quote);
                } else {
                    preferRE = (strchr(")}].", ch) == NULL);
                }
                // Stay in default state
            } else if (isEOLChar(ch)) {
                // Make sure it's a true line-end, with no backslash
                if ((ch == '\r' || (ch == '\n' && chPrev != '\r'))
                    && chPrev != '\\') {
                    // Assume we've hit the end of the statement.
                    preferRE = true;
                }
            }
        } else if (state == SCE_RB_WORD) {
            if (ch == '.' || !isSafeWordcharOrHigh(ch)) {
                // Words include x? in all contexts,
                // and <letters>= after either 'def' or a dot
                // Move along until a complete word is on our left

                // Default accessor treats '.' as word-chars,
                // but we don't for now.
                
                if (ch == '='
                    && isSafeWordcharOrHigh(chPrev)
                    && (chNext == '('
                        || strchr(" \t\n\r", chNext) != NULL)
                    && (!strcmp(prevWord, "def")
                        || followsDot(styler.GetStartSegment(), styler))) {
                    // <name>= is a name only when being def'd -- Get it the next time
                    // This means that <name>=<name> is always lexed as
                    // <name>, (op, =), <name>
                } else if ((ch == '?' || ch == '!')
                           && isSafeWordcharOrHigh(chPrev)
                           && !isSafeWordcharOrHigh(chNext)) {
                    // <name>? is a name -- Get it the next time
                    // But <name>?<name> is always lexed as
                    // <name>, (op, ?), <name>
                    // Same with <name>! to indicate a method that
                    // modifies its target
                } else if (isEOLChar(ch)
                           && isMatch(styler, lengthDoc, i - 7, "__END__")) {
                    styler.ColourTo(i, SCE_RB_DATASECTION);
                    state = SCE_RB_DATASECTION;
                    // No need to handle this state -- we'll just move to the end
                    preferRE = false;
                } else {
                    int wordStartPos = styler.GetStartSegment();
                    char *currWord = getCurrentWord(wordStartPos, i - 1, styler);
                    int word_style = ClassifyWordRb(wordStartPos, i - 1, keywords, styler, currWord, prevWord);
                    switch (word_style) {
                        case SCE_RB_WORD:
                            preferRE = RE_CanFollowKeyword(currWord);
                            break;
                            
                        case SCE_RB_WORD_DEMOTED:
                            preferRE = true;
                            break;
                            
                        case SCE_RB_IDENTIFIER:
                            preferRE = RE_CanFollowIdentifier(currWord);
                            if (!preferRE && isEOLChar(ch)) {
                                preferRE = true;
                            }
                            break;
                        default:
                            preferRE = false;
                    }
                    if (ch == '.') {
                        // We might be redefining an operator-method
                        preferRE = false;
                    }
                    // And if it's the first 
                    redo_char(i, ch, chNext, chNext2, state); // pass by ref
                }
            }
        } else if (state == SCE_RB_NUMBER) {
            if (!is_real_number) {
                if (ch != '\\') {
                    styler.ColourTo(i, state);
                    state = SCE_RB_DEFAULT;
                    preferRE = false;
                } else if (strchr("\\ntrfvaebs", chNext)) {
                    // Terminal escape sequence -- handle it next time
                    // Nothing more to do this time through the loop
                } else if (chNext == 'C' || chNext == 'M') {
                    if (chNext2 != '-') {
                        // \C or \M ends the sequence -- handle it next time
                    } else {
                        // Move from abc?\C-x
                        //               ^
                        // to
                        //                 ^
                        i += 2;
                        ch = chNext2;
                        chNext = styler.SafeGetCharAt(i + 1);
                    }
                } else if (chNext == 'c') {
                    // Stay here, \c is a combining sequence
                    advance_char(i, ch, chNext, chNext2); // pass by ref
                } else {
                    // ?\x, including ?\\ is final.
                    styler.ColourTo(i + 1, state);
                    state = SCE_RB_DEFAULT;
                    preferRE = false;
                    advance_char(i, ch, chNext, chNext2);
                }
            } else if (((ch == 'e' || ch == 'E') && ++num_e_s == 1)
                       && (chNext == '+' || chNext == '-'
                           || isSafeDigit(chNext))) {
                advance_char(i, ch, chNext, chNext2); // pass by ref
                // Can't end a number with a bare 'E', so do more checking.
            } else if (isSafeAlnumOrHigh(ch) || ch == '_') {
                // Keep going
            } else if (ch == '.' && ++numDots == 1) {
                // Keep going
            } else {
                styler.ColourTo(i - 1, state);
                redo_char(i, ch, chNext, chNext2, state); // pass by ref
                preferRE = false;
            }
        } else if (state == SCE_RB_COMMENTLINE) {
            if (isEOLChar(ch)) {
                styler.ColourTo(i - 1, state);
                state = SCE_RB_DEFAULT;
                // Use whatever setting we had going into the comment
            }
        } else if (state == SCE_RB_HERE_DELIM) {
            // See the comment for SCE_RB_HERE_DELIM in LexPerl.cxx
            // Slightly different: if we find an immediate '-',
            // the target can appear indented.
            
            if (HereDoc.State == 0) { // '<<' encountered
                HereDoc.State = 1;
                HereDoc.DelimiterLength = 0;
                if (ch == '-') {
                    HereDoc.CanBeIndented = true;
                    advance_char(i, ch, chNext, chNext2); // pass by ref
                } else {
                    HereDoc.CanBeIndented = false;
                }
                if (isEOLChar(ch)) {
                    // Bail out of doing a here doc if there's no target
                    state = SCE_RB_DEFAULT;
                    preferRE = false;
                } else {
                    HereDoc.Quote = ch;
                
                    if (ch == '\'' || ch == '"' || ch == '`') {
                        HereDoc.Quoted = true;
                        HereDoc.Delimiter[0] = '\0';
                    } else {
                        HereDoc.Quoted = false;
                        HereDoc.Delimiter[0] = ch;
                        HereDoc.Delimiter[1] = '\0';
                        HereDoc.DelimiterLength = 1;
                    }
                }
            } else if (HereDoc.State == 1) { // collect the delimiter
                if (isEOLChar(ch)) {
                    // End the quote now, and go back for more
                    styler.ColourTo(i - 1, state);
                    state = SCE_RB_DEFAULT;
                    i--;
                    chNext = ch;
                    chNext2 = chNext;
                    preferRE = false;
                } else if (HereDoc.Quoted) {
                    if (ch == HereDoc.Quote) { // closing quote => end of delimiter
                        styler.ColourTo(i, state);
                        state = SCE_RB_DEFAULT;
                        preferRE = false;
                    } else {
                        if (ch == '\\' && !isEOLChar(chNext)) {
                            advance_char(i, ch, chNext, chNext2);
                        }
                        HereDoc.Delimiter[HereDoc.DelimiterLength++] = ch;
                        HereDoc.Delimiter[HereDoc.DelimiterLength] = '\0';
                    }
                } else { // an unquoted here-doc delimiter
                    if (isSafeAlnumOrHigh(ch) || ch == '_') {
                        HereDoc.Delimiter[HereDoc.DelimiterLength++] = ch;
                        HereDoc.Delimiter[HereDoc.DelimiterLength] = '\0';
                    } else {
                        styler.ColourTo(i - 1, state);
                        redo_char(i, ch, chNext, chNext2, state);
                        preferRE = false;
                    }
                }
                if (HereDoc.DelimiterLength >= static_cast<int>(sizeof(HereDoc.Delimiter)) - 1) {
                    styler.ColourTo(i - 1, state);
                    state = SCE_RB_ERROR;
                    preferRE = false;
                }
            }
        } else if (state == SCE_RB_HERE_Q) {
            // Not needed: HereDoc.State == 2
            // Indentable here docs: look backwards
            // Non-indentable: look forwards, like in Perl
            //
            // Why: so we can quickly resolve things like <<-" abc"

            if (!HereDoc.CanBeIndented) {
                if (isEOLChar(chPrev)
                    && isMatch(styler, lengthDoc, i, HereDoc.Delimiter)) {
                    styler.ColourTo(i - 1, state);
                    i += HereDoc.DelimiterLength - 1;
                    chNext = styler.SafeGetCharAt(i + 1);
                    if (isEOLChar(chNext)) {
                        styler.ColourTo(i, SCE_RB_HERE_DELIM);
                        state = SCE_RB_DEFAULT;
                        HereDoc.State = 0;
                        preferRE = false;
                    }
                    // Otherwise we skipped through the here doc faster.
                }
            } else if (isEOLChar(chNext)
                       && lookingAtHereDocDelim(styler,
                                                i - HereDoc.DelimiterLength + 1,
                                                lengthDoc,
                                                HereDoc.Delimiter)) {
                styler.ColourTo(i - 1 - HereDoc.DelimiterLength, state);
                styler.ColourTo(i, SCE_RB_HERE_DELIM);
                state = SCE_RB_DEFAULT;
                preferRE = false;
                HereDoc.State = 0;
            }
        } else if (state == SCE_RB_CLASS_VAR
                   || state == SCE_RB_INSTANCE_VAR) {
            if (!isSafeWordcharOrHigh(ch)) {
                styler.ColourTo(i - 1, state);
                redo_char(i, ch, chNext, chNext2, state); // pass by ref
                preferRE = false;
            }
        } else if (state == SCE_RB_SYMBOL) {
            if (!isSafeWordcharOrHigh(ch)) {
                if (ch == '!' || ch == '?' || ch == '=') {
                    styler.ColourTo(i, state);
                    state = SCE_RB_DEFAULT;
                } else {
                    styler.ColourTo(i - 1, state);
                    redo_char(i, ch, chNext, chNext2, state); // pass by ref
                }
                preferRE = false;
            }
        } else if (state == SCE_RB_GLOBAL) {
            if (!isSafeWordcharOrHigh(ch)) {
                // handle special globals here as well
                if (chPrev == '$') {
                    if (ch == '-') {
                        // Include the next char, like $-a
                        advance_char(i, ch, chNext, chNext2);
                    }
                    styler.ColourTo(i, state);
                    state = SCE_RB_DEFAULT;
                } else {
                    styler.ColourTo(i - 1, state);
                    redo_char(i, ch, chNext, chNext2, state); // pass by ref
                }
                preferRE = false;
            }
        } else if (state == SCE_RB_POD) {
            // PODs end with ^=end\s, -- any whitespace can follow =end
            if (strchr(" \t\n\r", ch) != NULL
                && i > 5
                && isEOLChar(styler[i - 5])
                && isMatch(styler, lengthDoc, i - 4, "=end")) {
                styler.ColourTo(i - 1, state);
                state = SCE_RB_DEFAULT;
                preferRE = false;
            }
        } else if (state == SCE_RB_REGEX || state == SCE_RB_STRING_QR) {
            if (ch == '\\' && Quote.Up != '\\') {
                // Skip one
                advance_char(i, ch, chNext, chNext2);
            } else if (ch == Quote.Down) {
                Quote.Count--;
                if (Quote.Count == 0) {
                    // Include the options
                    while (isSafeAlpha(chNext)) {
                        i++;
                        ch = chNext;
                        chNext = styler.SafeGetCharAt(i + 1);
                    }
                    styler.ColourTo(i, state);
                    state = SCE_RB_DEFAULT;
                    preferRE = false;
                }
            } else if (ch == Quote.Up) {
                // Only if close quoter != open quoter
                Quote.Count++;
                
            } else if (ch == '#' ) {
                if (chNext == '{'
                    && inner_string_count < INNER_STRINGS_MAX_COUNT) {
                    // process #{ ... }
                    styler.ColourTo(i - 1, state);
                    styler.ColourTo(i + 1, SCE_RB_OPERATOR);
                    enterInnerExpression(inner_string_types,
                                         inner_expn_brace_counts,
                                         inner_quotes,
                                         inner_string_count,
                                         state,
                                         brace_counts,
                                         Quote);
                    preferRE = true;
                    // Skip one
                    advance_char(i, ch, chNext, chNext2);
                } else {
                    //todo: distinguish comments from pound chars
                    // for now, handle as comment
                    styler.ColourTo(i - 1, state);
                    bool inEscape = false;
                    while (++i < lengthDoc) {
                        ch = styler.SafeGetCharAt(i);
                        if (ch == '\\') {
                            inEscape = true;
                        } else if (isEOLChar(ch)) {
                            // Comment inside a regex
                            styler.ColourTo(i - 1, SCE_RB_COMMENTLINE);
                            break;
                        } else if (inEscape) {
                            inEscape = false;  // don't look at char
                        } else if (ch == Quote.Down) {
                            // Have the regular handler deal with this
                            // to get trailing modifiers.
                            i--;
                            ch = styler[i];
                            break;
                        }
                    }
                    chNext = styler.SafeGetCharAt(i + 1);
                    chNext2 = styler.SafeGetCharAt(i + 2);
                }
            }
        // Quotes of all kinds...
        } else if (state == SCE_RB_STRING_Q || state == SCE_RB_STRING_QQ || 
                   state == SCE_RB_STRING_QX || state == SCE_RB_STRING_QW ||
                   state == SCE_RB_STRING || state == SCE_RB_CHARACTER ||
                   state == SCE_RB_BACKTICKS) {
            if (!Quote.Down && !isspacechar(ch)) {
                Quote.Open(ch);
            } else if (ch == '\\' && Quote.Up != '\\') {
                //Riddle me this: Is it safe to skip *every* escaped char?
                advance_char(i, ch, chNext, chNext2);
            } else if (ch == Quote.Down) {
                Quote.Count--;
                if (Quote.Count == 0) {
                    styler.ColourTo(i, state);
                    state = SCE_RB_DEFAULT;
                    preferRE = false;
                }
            } else if (ch == Quote.Up) {
                Quote.Count++;
            } else if (ch == '#' && chNext == '{'
                       && inner_string_count < INNER_STRINGS_MAX_COUNT
                       && state != SCE_RB_CHARACTER
                       && state != SCE_RB_STRING_Q) {
                // process #{ ... }
                styler.ColourTo(i - 1, state);
                styler.ColourTo(i + 1, SCE_RB_OPERATOR);
                enterInnerExpression(inner_string_types,
                                     inner_expn_brace_counts,
                                     inner_quotes,
                                     inner_string_count,
                                     state,
                                     brace_counts,
                                     Quote);
                preferRE = true;
                // Skip one
                advance_char(i, ch, chNext, chNext2);
            }
        }
            
        if (state == SCE_RB_ERROR) {
            break;
        }
        chPrev = ch;
    }
    if (state == SCE_RB_WORD) {
        // We've ended on a word, possibly at EOF, and need to
        // classify it.
        int wordStartPos = styler.GetStartSegment();
        char *currWord = getCurrentWord(wordStartPos, lengthDoc - 1, styler);
        (void) ClassifyWordRb(wordStartPos, lengthDoc - 1, keywords, styler, currWord, prevWord);
    } else {
        styler.ColourTo(lengthDoc - 1, state);
    }
}

// Helper functions for folding, disambiguation keywords
// Assert that there are no high-bit chars 

static void getPrevWord(int pos,
                        char *prevWord,
                        Accessor &styler,
                        int word_state)
{
    int i;
    styler.Flush();
    for (i = pos - 1; i > 0; i--) {
        if (actual_style(styler.StyleAt(i)) != word_state) {
            i++;
            break;
        }
    }
    if (i < pos - MAX_KEYWORD_LENGTH) // overflow
        i = pos - MAX_KEYWORD_LENGTH;
    char *dst = prevWord;
    for (; i <= pos; i++) {
        *dst++ = styler[i];
    }
    *dst = 0;
}

static bool keywordIsAmbiguous(const char *prevWord)
{
    // Order from most likely used to least likely
    // Lots of ways to do a loop in Ruby besides 'while/until'
    if (!strcmp(prevWord, "if")
        || !strcmp(prevWord, "do")
        || !strcmp(prevWord, "while")
        || !strcmp(prevWord, "unless")
        || !strcmp(prevWord, "until")) {
        return true;
    } else {
        return false;
    }
}

// Demote keywords in the following conditions:
// if, while, unless, until modify a statement
// do after a while or until, as a noise word (like then after if) 

static bool keywordIsModifier(const char *word,
                              int pos,
                              Accessor &styler)
{
    if (word[0] == 'd' && word[1] == 'o' && !word[2]) {
        return keywordDoStartsLoop(pos, styler);
    }
    char ch;
    int style = SCE_RB_DEFAULT;
    int lineStart = styler.GetLine(pos);
    int lineStartPosn = styler.LineStart(lineStart);
    styler.Flush();
    while (--pos >= lineStartPosn) {
        style = actual_style(styler.StyleAt(pos));
        if (style == SCE_RB_DEFAULT) {
            if (iswhitespace(ch = styler[pos])) {
                //continue
            } else if (ch == '\r' || ch == '\n') {
                // Scintilla's LineStart() and GetLine() routines aren't
                // platform-independent, so if we have text prepared with
                // a different system we can't rely on it.
                return false;
            }
        } else {
            break;
        }
    }
    if (pos < lineStartPosn) {
        return false; //XXX not quite right if the prev line is a continuation
    }
    // First things where the action is unambiguous
    switch (style) {
        case SCE_RB_DEFAULT:
        case SCE_RB_COMMENTLINE:
        case SCE_RB_POD:
        case SCE_RB_CLASSNAME:
        case SCE_RB_DEFNAME:
        case SCE_RB_MODULE_NAME:
            return false;
        case SCE_RB_OPERATOR:
            break;
        case SCE_RB_WORD:
            // Watch out for uses of 'else if'
            //XXX: Make a list of other keywords where 'if' isn't a modifier
            //     and can appear legitimately
            // Formulate this to avoid warnings from most compilers
            if (strcmp(word, "if") == 0) {
                char prevWord[MAX_KEYWORD_LENGTH + 1];
                getPrevWord(pos, prevWord, styler, SCE_RB_WORD);
                return strcmp(prevWord, "else") != 0;
            }
            return true;
        default:
            return true;
    }
    // Assume that if the keyword follows an operator,
    // usually it's a block assignment, like
    // a << if x then y else z
    
    ch = styler[pos];
    switch (ch) {
        case ')':
        case ']':
        case '}':
            return true;
        default:
            return false;
    }
}

#define WHILE_BACKWARDS "elihw"
#define UNTIL_BACKWARDS "litnu"
#define FOR_BACKWARDS "rof"

// Nothing fancy -- look to see if we follow a while/until somewhere
// on the current line

static bool keywordDoStartsLoop(int pos,
                                Accessor &styler)
{
    char ch;
    int style;
    int lineStart = styler.GetLine(pos);
    int lineStartPosn = styler.LineStart(lineStart);
    styler.Flush();
    while (--pos >= lineStartPosn) {
        style = actual_style(styler.StyleAt(pos));
        if (style == SCE_RB_DEFAULT) {
            if ((ch = styler[pos]) == '\r' || ch == '\n') {
                // Scintilla's LineStart() and GetLine() routines aren't
                // platform-independent, so if we have text prepared with
                // a different system we can't rely on it.
                return false;
            }
        } else if (style == SCE_RB_WORD) {
            // Check for while or until, but write the word in backwards
            char prevWord[MAX_KEYWORD_LENGTH + 1]; // 1 byte for zero
            char *dst = prevWord;
            int wordLen = 0;
            int start_word;
            for (start_word = pos;
                 start_word >= lineStartPosn && actual_style(styler.StyleAt(start_word)) == SCE_RB_WORD;
                 start_word--) {
                if (++wordLen < MAX_KEYWORD_LENGTH) {
                    *dst++ = styler[start_word];
                }
            }
            *dst = 0;
            // Did we see our keyword?
            if (!strcmp(prevWord, WHILE_BACKWARDS)
                || !strcmp(prevWord, UNTIL_BACKWARDS)
                || !strcmp(prevWord, FOR_BACKWARDS)) {
                return true;
            }
            // We can move pos to the beginning of the keyword, and then
            // accept another decrement, as we can never have two contiguous
            // keywords:
            // word1 word2
            //           ^
            //        <-  move to start_word
            //      ^
            //      <- loop decrement
            //     ^  # pointing to end of word1 is fine
            pos = start_word;
        } else if (style == SCE_RB_OPERATOR && styler[pos] == ';') {
            return false;
        }
    }
    return false;
}

/*
 *  Folding Ruby
 * 
 *  The language is quite complex to analyze without a full parse.
 *  For example, this line shouldn't affect fold level:
 * 
 *   print "hello" if feeling_friendly?
 * 
 *  Neither should this:
 * 
 *   print "hello" \
 *      if feeling_friendly?
 * 
 * 
 *  But this should:
 * 
 *   if feeling_friendly?  #++
 *     print "hello" \
 *     print "goodbye"
 *   end                   #--
 * 
 *  So we cheat, by actually looking at the existing indentation
 *  levels for each line, and just echoing it back.  Like Python.
 *  Then if we get better at it, we'll take braces into consideration,
 *  which always affect folding levels.

 *  How the keywords should work:
 *  No effect:
 *  __FILE__ __LINE__ BEGIN END alias and 
 *  defined? false in nil not or self super then
 *  true undef

 *  Always increment:
 *  begin  class def do for module when {
 * 
 *  Always decrement:
 *  end }
 * 
 *  Increment if these start a statement
 *  if unless until while -- do nothing if they're modifiers

 *  These end a block if there's no modifier, but don't bother
 *  break next redo retry return yield
 * 
 *  These temporarily de-indent, but re-indent
 *  case else elsif ensure rescue
 * 
 *  This means that the folder reflects indentation rather
 *  than setting it.  The language-service updates indentation
 *  when users type return and finishes entering de-denters.
 * 
 *  Later offer to fold POD, here-docs, strings, and blocks of comments
 */

static void FoldRbDoc(unsigned int startPos, int length, int initStyle,
                      WordList *[], Accessor &styler) {
    const bool foldCompact = styler.GetPropertyInt("fold.compact", 1) != 0;
    bool foldComment = styler.GetPropertyInt("fold.comment") != 0;
    
    synchronizeDocStart(startPos, length, initStyle, styler // ref args
                        );
    unsigned int endPos = startPos + length;
    int visibleChars = 0;
    int lineCurrent = styler.GetLine(startPos);
    int levelPrev = startPos == 0 ? 0 : (styler.LevelAt(lineCurrent)
                                         & SC_FOLDLEVELNUMBERMASK
                                         & ~SC_FOLDLEVELBASE);
    int levelCurrent = levelPrev;
    char chNext = styler[startPos];
    int styleNext = styler.StyleAt(startPos);
    int stylePrev = startPos <= 1 ? SCE_RB_DEFAULT : styler.StyleAt(startPos - 1);
    bool buffer_ends_with_eol = false;
    for (unsigned int i = startPos; i < endPos; i++) {
        char ch = chNext;
        chNext = styler.SafeGetCharAt(i + 1);
        int style = styleNext;
        styleNext = styler.StyleAt(i + 1);
        bool atEOL = (ch == '\r' && chNext != '\n') || (ch == '\n');
        if (style == SCE_RB_COMMENTLINE) {
            if (foldComment && stylePrev != SCE_RB_COMMENTLINE) {
                if (chNext == '{') {
                    levelCurrent++;
                } else if (chNext == '}' && levelCurrent > 0) {
                    levelCurrent--;
                }
            }
        } else if (style == SCE_RB_OPERATOR) {
            if (strchr("[{(", ch)) {
                levelCurrent++;
            } else if (strchr(")}]", ch)) {
                // Don't decrement below 0
                if (levelCurrent > 0)
                    levelCurrent--;
            }
        } else if (style == SCE_RB_WORD && styleNext != SCE_RB_WORD) {
            // Look at the keyword on the left and decide what to do
            char prevWord[MAX_KEYWORD_LENGTH + 1]; // 1 byte for zero
            prevWord[0] = 0;
            getPrevWord(i, prevWord, styler, SCE_RB_WORD);
            if (!strcmp(prevWord, "end")) {
                // Don't decrement below 0
                if (levelCurrent > 0)
                    levelCurrent--;
            } else if (   !strcmp(prevWord, "if")
                       || !strcmp(prevWord, "def")
                       || !strcmp(prevWord, "class")
                       || !strcmp(prevWord, "module")
                       || !strcmp(prevWord, "begin")
                       || !strcmp(prevWord, "case")
                       || (!strcmp(prevWord, "do")
                           && !keywordDoStartsLoop(i, styler))
                       || !strcmp(prevWord, "while")
                       || !strcmp(prevWord, "unless")
                       || !strcmp(prevWord, "until")
                       || !strcmp(prevWord, "for")
                          ) {
                levelCurrent++;
            }
        } else if (atEOL) {
            if (style == SCE_RB_POD) {
                int lineStartPosn = styler.LineStart(lineCurrent);
                if (lineStartPosn == 0
                    || styler.StyleAt(lineStartPosn - 1) != SCE_RB_POD) {
                    levelCurrent++;
                }
            } else if (style == SCE_RB_DEFAULT) {
                if (styler.StyleAt(styler.LineStart(lineCurrent)) == SCE_RB_POD) {
                    levelCurrent--;
                }
            }
        }
        if (atEOL) {
            int lev = levelPrev;
            if (visibleChars == 0 && foldCompact)
                lev |= SC_FOLDLEVELWHITEFLAG;
            if ((levelCurrent > levelPrev) && (visibleChars > 0))
                lev |= SC_FOLDLEVELHEADERFLAG;
            styler.SetLevel(lineCurrent, lev|SC_FOLDLEVELBASE);
            lineCurrent++;
            levelPrev = levelCurrent;
            visibleChars = 0;
            buffer_ends_with_eol = true;
        } else if (!isspacechar(ch)) {
            visibleChars++;
            buffer_ends_with_eol = false;
        }
        stylePrev = style;
    }
    // Fill in the real level of the next line, keeping the current flags as they will be filled in later
    if (!buffer_ends_with_eol) {
        lineCurrent++;
        int new_lev = levelCurrent;
        if (visibleChars == 0 && foldCompact)
            new_lev |= SC_FOLDLEVELWHITEFLAG;
            if ((levelCurrent > levelPrev) && (visibleChars > 0))
                new_lev |= SC_FOLDLEVELHEADERFLAG;
            levelCurrent = new_lev;
    }
    styler.SetLevel(lineCurrent, levelCurrent|SC_FOLDLEVELBASE);
}

static const char * const rubyWordListDesc[] = {
    "Keywords",
    0
};

LexerModule lmRuby(SCLEX_RUBY, ColouriseRbDoc, "ruby", FoldRbDoc, rubyWordListDesc);
