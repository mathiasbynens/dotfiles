// Scintilla source code edit control
/** @file LexPerl.cxx
 ** Lexer for subset of Perl.
 **/
// Copyright 1998-2001 by Neil Hodgson <neilh@scintilla.org>
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

static inline void advanceOneChar(unsigned int& i, char&ch, char& chNext, char chNext2) {
    i++;
    ch = chNext;
    chNext = chNext2;
}

static inline void retreatOneChar(unsigned int& i, char& chPrev, char& ch, char& chNext) {
    i--;
    chNext = ch;
    ch = chPrev;
}

// This is ASCII specific but is safe with chars >= 0x80

static inline bool isEOLChar(char ch) {
    return (ch == '\r') || (ch == '\n');
}

static inline bool isSingleCharOp(char ch) {
    return strchr("rwxoRWXOezsfdlpSbctugkTBMAC", ch) != NULL;
}

static inline bool isPerlOperator(char ch) {
    return strchr("%^&*\\()-+=|{}[]:;<>,/?!.~",ch) != NULL;
}

static inline bool isHereDocStyle(int style) {
    return style == SCE_PL_HERE_Q || style == SCE_PL_HERE_DELIM;
}

// Assume high-bit chars are part of a utf-8 name, not part of
// something like a non-breaking space or fancy hyphen

static inline bool isSafeAlpha(char ch) {
    return ((unsigned int) ch >= 128) || isalpha(ch);
}

static inline bool isSafeAlnum(char ch) {
    return ((unsigned int) ch >= 128) || isalnum(ch) || ch == '_';
}

// Digits on the other hand don't have utf-8 representations.
static inline bool isSafeDigit(char ch) {
    return ((unsigned int) ch <= 127) && isdigit(ch);
}

static inline bool isSimpleWS(char ch) {
    return (ch == ' ') || (ch == '\t');
}

static inline char safeStyleAt(int pos, Accessor &styler) {
    return ((char) (((unsigned int)styler.StyleAt(pos)) & 0x3f)); // 6 bits
}

static inline int columnStartPos(int pos, Accessor &styler) {
    return pos - styler.LineStart(styler.GetLine(pos));
}

static bool isFatCommaNext(Accessor &styler, unsigned int startIndex, unsigned int length) {
    bool inComment = false;
    unsigned int i;
    for (i = startIndex;i < length;i++) {
        char ch = styler.SafeGetCharAt(i);
        if (inComment) {
            if (isEOLChar(ch)) {
                inComment = false;
            }
        } else if (ch == '=') {
            if (styler.SafeGetCharAt(i+1) == '>') {
                return true;
            }
        } else if (ch == '#') {
            inComment = true;
        } else if (!isspacechar(ch)) {
            break;
        }
    }

    return false;
}

static int classifyWordPerl(unsigned int start, unsigned int end, unsigned int length,
                            WordList &keywords, Accessor &styler,
                            bool *p_BraceStartsBlock)
{
    char ch, s[51];
    ch = styler[start];
    bool wordIsNumber = (((unsigned int) ch) < 128
                         && (isdigit(ch) || (ch == '.')));
    bool isSimpleWord = true;
    
    // Copy the word into a local buffer.
    unsigned int i;
    for (i = 0; i < end - start + 1 && i < 50; i++) {
        ch = styler[start+i];
        if (isSimpleWord && !isSafeAlnum(ch) && !(i == 0 && ch == '-')) {
            isSimpleWord = false;
        }
        s[i] = ch;
    }
    s[i] = '\0';
    
    // Choose and apply a colour style for the word.
    if (p_BraceStartsBlock) {
        *p_BraceStartsBlock = true;
    }
    char chAttr = SCE_PL_IDENTIFIER;
    if (wordIsNumber) {
        chAttr = SCE_PL_NUMBER;
    } else if (isSimpleWord && isFatCommaNext(styler,end+1,length)) {
        chAttr = SCE_PL_STRING_Q;
    } else if (keywords.InList(s)) {
        chAttr = SCE_PL_WORD;
        if (p_BraceStartsBlock
            && (!strcmp(s, "bless")
                || !strcmp(s, "return")
                || !strcmp(s, "ref"))) {
            *p_BraceStartsBlock = false;
        }
    }
    styler.ColourTo(end, chAttr);
    return chAttr;
}

//precondition: styler[start..end] is a keyword

static bool RE_CanFollowKeyword(unsigned int start, unsigned int end,
                                Accessor &styler)
{
    char ch, s[53];
    ch = styler[start];
    unsigned int i;
    // Copy the word into a local buffer.
    s[0] = '|';
    for (i = 0; i < end - start + 1 && i < 51; i++) {
        s[i + 1] = styler[start+i];
    }
    s[i + 1] = '|';
    s[i + 2] = '\0';
    const char *no_RE_KwdList = 
        "|while|if|unless|until|and|or|not|xor|split|grep|map|print|";
    return strstr(no_RE_KwdList, s) != NULL;
}

// Let's look back: if we see /(^|;(10))\s*\w+(5|11)\s(0)*<here>/, return true
// Precondition: i points to the end of the text we're trying to match

static bool afterLabel(int pos, Accessor &styler)
{
    char ch;
    int style;
    styler.Flush();
    for (; pos >= 0; pos--) {
        ch = styler.SafeGetCharAt(pos);
        if (isSimpleWS(ch)) {
            style = safeStyleAt(pos, styler);
            if (style != SCE_PL_DEFAULT) {
                return false;
            }
        } else {
            break;
        }
    }
    // at the start of the line ... report failure anyway
    if (pos < 0) {
        return false;
    }
    int curr_pos = pos;
    for (; pos >= 0; pos--) {
        style = safeStyleAt(pos, styler);
        if (style != SCE_PL_WORD && style != SCE_PL_IDENTIFIER) {
            break;
        }
    }
    if (pos == curr_pos) {
        // we didn't retreat, so we're aren't looking at a word
        return false;
    }
    for (; pos >= 0; pos--) {
        ch = styler.SafeGetCharAt(pos);
        if (!isSimpleWS(ch)) {
            break;
        }
    }
    if (pos < 0) {
        return true;
    }
    ch = styler.SafeGetCharAt(pos);
    return strchr("\n:{}", ch) != NULL;
}

static inline bool isEndVar(char ch) {
    return !isSafeAlnum(ch) && !strchr("#$_\'[{",ch);
}

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


// It's harder to look forward than backward, but it's more correct:
// Makes fewer assumptions about what scintilla innards are doing.

static bool atStartOfFormatStmt(unsigned int &pos,
                                int lengthDoc,
                                Accessor &styler) 
{
    // <format:word> to left, match ws+, <word|ident>, ws*, '='
    // First just match the chars.  If the chars match,
    // paint them correctly, and return true.

    int positions[5];
    // {start, end of ws-1, end-of-ident, end of ws-2, '='

    char ch;
    positions[0] = pos;
    ch = styler.SafeGetCharAt(pos);

    if (pos + 3 >= (unsigned int)lengthDoc) {
        return false;
    }
    
    int testPos = pos + 1;

    ch = styler.SafeGetCharAt(testPos);
    if (!isSimpleWS(ch)) {
        return false;
    }

    // Match <ws>
    for (; testPos < lengthDoc; testPos++) {
        ch = styler.SafeGetCharAt(testPos);
        if (!isSimpleWS(ch)) {
            break;
        }
    }
    positions[1] = testPos - 1;

    // Match <ident>
    ch = styler.SafeGetCharAt(testPos);
    if (!(isSafeAlpha(ch) || ch == '_')) {
        return false;
    }
    for (testPos++; testPos < lengthDoc; testPos++) {
        ch = styler.SafeGetCharAt(testPos);
        if (!isSafeAlnum(ch)) {
            break;
        }
    }
    positions[2] = testPos - 1;
    
    // Match <ws?>
    for (; testPos < lengthDoc; testPos++) {
        ch = styler.SafeGetCharAt(testPos);
        if (!isSimpleWS(ch)) {
            break;
        }
    }
    positions[3] = testPos - 1;

    if (testPos >= lengthDoc) {
        return false;
    }
    ch = styler.SafeGetCharAt(testPos);
    if (ch == '=') {
        positions[4] = testPos;
    } else {
        return false;
    }

    // Now color the line we matched based on the positions,
    // and update the final state.
    //
    // Don't match the newline in this routine -- let the standard
    // newline-handling code deal with it.

    int styles[4] = {SCE_PL_DEFAULT,
                     SCE_PL_IDENTIFIER,
                     SCE_PL_DEFAULT,
                     SCE_PL_OPERATOR
    };
    int idx;
    styler.ColourTo(pos, SCE_PL_WORD);
    for (idx = 0; idx < 4; idx++) {
        if (positions[idx + 1] > positions[idx]) {
            styler.ColourTo(positions[idx + 1], styles[idx]);
        }
    }
    // Leave it pointing at the '='
    pos = testPos;
    styler.Flush();
    return true;
}


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

// Calculates the current fold level (for the relevant line) when the lexer has 
// parsed up to the given index.
int getFoldLevelModifier(Accessor& styler, int startIndex, int endIndex) {
    int modifier = 0;
    int index;
    styler.Flush();
    for (index = startIndex;index < endIndex;index++) {
        int style = safeStyleAt(index, styler);
        if (style == SCE_PL_OPERATOR || style == SCE_PL_VARIABLE_INDEXER) {
            char ch = styler.SafeGetCharAt(index);
            if (ch == '{' || ch == '(' || ch == '[') {
                modifier++;
            } else if (ch == '}' || ch == ')' || ch == ']') {
                modifier--;
            }
        }
    }
    return modifier;
}    

/* Leading dashes are allowed only in some places before fat-commas,
 * such as inside hash definitions.
 * This code doesn't know which context it's called in, so will always
 * report a string with a leading dash as a bareword.  If it isn't,
 * the code is invalid.  Editor users will see an error indicator.
 * Other clients of this code are unlikely to call this incorrectly,
 * as they're most likely using it to analyze correct code.
 */

static bool isWordBeforeFatComma(Accessor &styler, unsigned int startIndex, 
                                 unsigned int length) {
    unsigned int i = startIndex;
    // Allow a '-' at the start
    if (i < length && styler.SafeGetCharAt(i) == '-') {
        ++i;
    }
    for (; i < length; i++) {
        char ch = styler.SafeGetCharAt(i);
        if (!isSafeAlnum(ch)) {
            break;
        }
    }
    return isFatCommaNext(styler,i,length);
}

static bool isInterpolatingString(int style, char ch) {
    switch(style) {
    case SCE_PL_STRING_QQ:
    case SCE_PL_STRING:
    case SCE_PL_STRING_QX:
    case SCE_PL_BACKTICKS:
        return isSafeAlnum(ch) || ch == '_';
    }
    return false;
}

static void doInterpolateVariable(unsigned int&         i,
                                  unsigned int          lengthDoc,
                                  int                   state,
                                  char&                 ch,
                                  Accessor&             styler) {
    // bug 34374: color interpolated variables
    styler.ColourTo(i - 1, state);
    int variableType = ch == '$' ? SCE_PL_SCALAR : SCE_PL_ARRAY;
    // Enter a mini-mode to color scalars and arrays inside strings
    while (++i < lengthDoc) {
        ch = styler.SafeGetCharAt(i);
        if (!isSafeAlnum(ch) && ch != '_') {
            break;
        }
    }
    styler.ColourTo(i - 1, variableType);
}

// support checking backwards for

// You can't always look for styles, because the entire sequence hasn't been
// restyled yet.  YOu need to do a lex analysis:

// {[indexer], \s*, [-]?[a-zA-Z0-9_]+, \s*

static bool followsStartIndexer(Accessor &styler, unsigned int index)
{
    char ch;
    int style;
    if (index > 0x0fffffff) return false;
    long i = 0x0fffffff & index;
    // First check for trailing default <anything> (since we haven't colorized it yet
    for (; i >= 0; i--) {        
        ch = styler[i];
        if (!isspacechar(ch)) {
            break;
        }
    }

    // Now check for word-chars
    // The '< 1' test is intended to select out
    // negative values where char's range from 0 .. 255,
    // and the 'ch >= 127' for where char's range over -128 .. 127
    for (; i >= 0; i--) {        
        ch = styler[i];
        if (!isSafeAlnum(ch)) {
            break;
        }
    }
    // Optional leading '-'
    if (i >= 0 && styler[i] == '-')
        --i;

    // Leading space
    for (; i >= 0; i--) {        
        ch = styler[i];
        if (!isspacechar(ch)) {
            break;
        }
    }

    if (i < 0) {
        return false;
    }
    style = safeStyleAt(i, styler);
    if (style != SCE_PL_VARIABLE_INDEXER) {
        return false;
    }
    ch = styler[i];
    return (ch == '{');
}

/* Match <space>*, -? [\w\d_]+, <space>*, } */
static bool lookingAtBareword(Accessor &styler, unsigned int index,
                              unsigned int actualLengthDoc) 
{
    if (index > 0x0fffffff) return false;
    char ch = ' ';
    unsigned int i = (index & 0x0fffffff); // signed index
    for (; i < actualLengthDoc; i++) {
        ch = styler[i];
        if (!isspacechar(ch)) {
            break;
        }
    }
    if (i < actualLengthDoc - 1 && ch == '-') {
        ch = styler[++i];
    }
    // Make sure we have a character
    if (i >= actualLengthDoc || !isSafeAlnum(ch)) {
        return false;
    }
    for (i++; i < actualLengthDoc; i++) {
        ch = styler[i];
        if (!isSafeAlnum(ch)) {
            break;
        }
    }
    // Use the char set in the char-skipping loop
    for(;;) {
        if (!isspacechar(ch)) {
            break;
        }
        if (i >= actualLengthDoc - 1) {
            break;
        }
        ch = styler[++i];
    }
    return (i < actualLengthDoc && ch == '}');
}

static char colouriseBareword(Accessor &styler, unsigned int &i, int &state,
                              unsigned int actualLengthDoc)
{
    // We're going to colorize everything here to avoid
    // further complicating the state machine.

    char ch = ' ';
    for (i++; i < actualLengthDoc; i++) {
        ch = styler[i];
        if (!isspacechar(ch)) {
            break;
        }
    }
    // fprintf(stderr, "Color as default to posn %d\n", i - 1);
    styler.ColourTo(i - 1, SCE_PL_DEFAULT);
    if (ch == '-') {
        ch = styler[++i];
    }
    for (; i < actualLengthDoc; i++) {
        ch = styler[i];
        if (!isSafeAlnum(ch)) {
            break;
        }
    }
    styler.ColourTo(i - 1, SCE_PL_STRING);
    // fprintf(stderr, "Color as string to posn %d\n", i - 1);
    for (; i < actualLengthDoc; i++) {
        ch = styler[i];
        if (!isspacechar(ch)) {
            break;
        }
    }
    styler.ColourTo(i - 1, SCE_PL_DEFAULT);
    // fprintf(stderr, "Color as space to posn %d\n", i - 1);
    i -= 1;
    state = SCE_PL_DEFAULT;
    return styler[i]; // The last char we found
}

static bool precedesIndexer(Accessor &styler, unsigned int index,
                            unsigned int endPoint)
{
    if (index > 0x0fffffff) return false;
    unsigned int i = 0x0fffffff & index;
    if (i >= endPoint) {
        return false;
    }
    char ch;
    // Look for \s*\}, return false on anything else.
    for (; i < endPoint; i++) {
        ch = styler[i];
        if (!isspacechar(ch)) {
            return (ch == '}');
            break;
        }
    }
    return false;
}


static bool wordEndsHere(char chNext, char chNext2, bool no_namespace_op)
{
    // ".." is always an operator if preceded by a SCE_PL_WORD.
    // "." is an operator unless we're inside a number thing
    // Archaic Perl has quotes inside names
    
    if (chNext == '.') {
        return true;
    } else if (chNext == ':' && chNext2 == ':' && no_namespace_op) {
        return false;
    } else if (iswordchar(chNext)) {
        return false;
    } else if (chNext != '\'') {
        return true;
    } else {
        return !iswordstart(chNext2);  // ada-like $pkg'member
    }
}

// KOMODO -- interactive shell colorizing
static bool isStdioChar(int style) {
    switch (style) {
        case SCE_PL_STDIN:
        case SCE_PL_STDOUT:
        case SCE_PL_STDERR:
            return true;
    }
    return false;
}

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

/*
 * This implementation just walks back up the
 * buffer, since looking at line levels is way too error-prone.
 * In Perl you can have long runs of blocks that are all at the
 * same level given non-standard code formatting, like
 *
 * if (1 ...
 *    ) { my %abc = { abc => map { if (2
 *                                     ...) {
 * ...
 *
 * This seems fast enough -- on cgi.pm it goes from line 40 to 3808
 * without any noticeable dela.
 */

static int GetMatchingPos(int currPos, Accessor &styler)
{
    char currChar = styler.SafeGetCharAt(currPos);
    if (currChar != '}') {
        return -1;
    }
    int num_extra_closers = 1;
    int direction = 0;
    for (int i = currPos - 1; i >= 0; i--) {
        char ch = styler.SafeGetCharAt(i);
        if (ch == '{') {
            direction = -1;
        } else if (ch == '}') {
            direction = +1;
        } else {
            direction = 0;
        }
        if (direction) {
            switch ((int) safeStyleAt(i, styler)) {
            case SCE_PL_OPERATOR:
            case SCE_PL_VARIABLE_INDEXER:
                num_extra_closers += direction;
                if (num_extra_closers == 0) {
                    return i;
                }
                break;
            }
        }
    }
    return -1;
}

static
int GetMatchingStyle(int currPos, Accessor &styler)
{
    // We need to flush in case things above us changed, as this code uses styles.
    styler.Flush();
    int startPos = GetMatchingPos(currPos, styler);
    if (startPos >= 0) {
        int startStyle = safeStyleAt(startPos, styler);
        return startStyle;
    }
    return SCE_PL_OPERATOR;
}

typedef int BracePoint;

class BracePositionInfo {
    public:
    BracePositionInfo(int cap_=16) {
        capacity = cap_;
        p_BI = (BracePoint *) malloc(capacity * sizeof(BracePoint));
        if (!p_BI) {
            capacity = 0;
        }
        index = 0;
    };
    ~BracePositionInfo() {
        if (p_BI) free ((void *) p_BI);
    };
    bool add(int style) {
        if (capacity <= 0 || index < 0) {
            return false;
        } else if (capacity <= index) {
            int new_cap = capacity;
            while (new_cap <= index) {
                new_cap = new_cap * 2;
            }
            // fprintf(stderr, "BracePositionInfo::add: about to realloc 0x%x from %d to %d bytes\n", p_BI, capacity, new_cap);
            BracePoint *tmp =
                (BracePoint *) realloc((void *) p_BI,
                                      new_cap * sizeof(BracePoint));
            if (!tmp) {
                // Throw it *all* away
                // fprintf(stderr, "BracePositionInfo::add: failed\n");
                free ((void *) p_BI);
                p_BI = 0;
                index = capacity = 0;
                return false;
            } else {
                p_BI = tmp;
                capacity = new_cap;
                // fprintf(stderr, "BracePositionInfo::add: worked, mem=0x%x, cap = %d\n", p_BI, capacity);
            }
        }
        p_BI[index++] = style;
        return true;
    };
    int getStyle(bool pop=true) {
        if (!p_BI || index <= 0) {
            return -1;
        }
        int style = p_BI[index - 1];
        if (pop) {
            index--;
        }
        return style;
    };
    
    private:
    BracePoint *p_BI;
    int index;
    int capacity;
};

// Move back to the start of the last statement. This may require passing 
// through a here document body and/or a line declaring a here doc follows.

static void synchronizeDocStart(unsigned int& startPos,
                                unsigned int endPos,
                                int& state,
                                Accessor& styler)
{
    styler.Flush();
    int style;
    int pos = startPos;
    int currLine = styler.GetLine(pos);
    int lastLine = styler.GetLine(endPos);
    int lineEndPos = (lastLine == currLine) ? styler.Length() : styler.LineStart(currLine + 1) - 1;
    
    while (currLine > 0) {
        // Now look at the style before the previous line's EOL
        int prevLine_PosBeforeEOL = prevNonNewlinePos(currLine, styler);
        if (prevLine_PosBeforeEOL == -1) {
            break;
        }
        style = safeStyleAt(prevLine_PosBeforeEOL, styler);
        int lineStartPos = styler.LineStart(currLine);
        // KOMODO -- interactive shell colorizing
        if (isStdioChar(style)) {
            // stop at start of line currLine
            startPos = lineStartPos;
            state = SCE_PL_DEFAULT;
            return;
        }
        // If the previous newline style isn't default, keep moving back
        int prevLineEndPos = lineStartPos - 1;

        // Look at the style at the end of the previous line
        style = safeStyleAt(prevLineEndPos, styler);
        if (style != SCE_PL_DEFAULT) {
            switch (style) {
            case SCE_PL_POD:
            case SCE_PL_DATASECTION:
                // These always end the same, so we can stop in one.
                // Otherwise we risk walking back through very long
                // documents for no reason.
                startPos = lineStartPos;
                state = style;
                return;
            }
            currLine -= 1;
            lineEndPos = prevLineEndPos;
            continue;
        }            

        // Now look at the first non-white token on this line
        // and decide what to do.

        int first_sig_pos;
        for (first_sig_pos = lineStartPos; // first significant position
             first_sig_pos < lineEndPos;
             first_sig_pos++) {
            int style = safeStyleAt(first_sig_pos, styler);
            if (style != SCE_PL_DEFAULT) {
                break;
            }
        }

        int firstStyle = safeStyleAt(first_sig_pos, styler);
        switch (firstStyle) {
        case SCE_PL_COMMENTLINE:
        case SCE_PL_NUMBER:
        case SCE_PL_WORD:
        case SCE_PL_OPERATOR:
        case SCE_PL_IDENTIFIER:
        case SCE_PL_SCALAR:
        case SCE_PL_ARRAY:
        case SCE_PL_HASH:
        case SCE_PL_SYMBOLTABLE:
        case SCE_PL_VARIABLE_INDEXER:
            // Verify the char before this one is default EOL,
            // then we know it's safe to break here,
            // as the lexer will proceed in the default state.
            startPos = lineStartPos;
            state = SCE_PL_DEFAULT;
            return;
        }
        currLine -= 1;
        lineEndPos = prevLineEndPos;
    }
    startPos = 0;
    state = SCE_PL_DEFAULT;
}


void ColourisePerlDoc(unsigned int startPos, int length, int , // initStyle
                      WordList *keywordlists[], Accessor &styler)
{

    // Lexer for perl often has to backtrack to start of current style to determine
    // which characters are being used as quotes, how deeply nested is the
    // start position and what the termination string is for here documents

    WordList &keywords = *keywordlists[0];
    
    class HereDocCls {
    public:
        int State;      // 0: '<<' encountered
        // 1: collect the delimiter
        // 2: here doc text (lines after the delimiter)
        char Quote;     // the char after '<<'
        bool Quoted;        // true if Quote in ('\'','"','`')
        int DelimiterLength;    // strlen(Delimiter)
        char Delimiter[256];    // the Delimiter, 256: sizeof PL_tokenbuf
        bool HasSemiColon;
        HereDocCls() {
            State = 0;
            DelimiterLength = 0;
            Delimiter[0] = '\0';
        }
    };
    HereDocCls HereDoc;

    class QuoteCls {
        public:
        int  Rep;
        int  Count;
        char Up;
        char Down;
        QuoteCls() {
            this->New(1);
        }
        void New(int r) {
            Rep   = r;
            Count = 0;
            Up    = '\0';
            Down  = '\0';
        }
        void Open(char u) {
            Count++;
            Up    = u;
            Down  = opposite(Up);
        }
    };
    QuoteCls Quote;
    // Info on parsing numbers
    int numDots = 0;
    int numBase = 10;
    int numExponents = 0;

    bool preferRE = true;
    unsigned int lengthDoc = startPos + length;
    bool binaryOperatorExpected = false; // If true, a binary operator can follow.
    bool braceStartsBlock = true; // Whether a brace starts a block or an indexed expression
    int variableNestingCount = 0; // The number of unclosed '(' and '{' in the current variable name.

#if 0
    int origStartPos = startPos;
#endif

    bool hasVisibleChars = false;

    int state;
    synchronizeDocStart(startPos, lengthDoc, state, styler);
    
    int previousState = SCE_PL_DEFAULT; // Used to restore the original state after a comment.

    if (startPos < 0) {
        startPos = 0;
        state = SCE_PL_DEFAULT;
    }
#if 0
    {
        int origLine = styler.GetLine(origStartPos);
        int newLine = styler.GetLine(startPos);
        fprintf(stderr, "Synch: moved from [%d:%d:%d]=>(%d) to [%d:%d:%d], state %d\n",
                origStartPos, origLine,
                origStartPos - styler.LineStart(origLine),
                lengthDoc,
                startPos, newLine,
                startPos - styler.LineStart(newLine),
                state);
        int targetPos = lengthDoc - 1;
        int targetLine = styler.GetLine(targetPos);
        fprintf(stderr, "Color chars upto [%d:%d:%d] (%d chars)\n",
                targetPos, targetLine, targetPos - styler.LineStart(targetLine),
                lengthDoc - startPos);
    }
#endif

    // Work on this in case we hit an unmatched close-brace.
    BracePositionInfo *p_BraceInfo = new BracePositionInfo();

    // fprintf(stderr, "Starting lexing at pos %d (line %d)\n", startPos, styler.GetLine(startPos));

    // Variables to allow folding.
    bool fold = styler.GetPropertyInt("fold") != 0;
    int lineCurrent = styler.GetLine(startPos);
    int levelPrev = 0, levelCurrent = 0;

    // Properties
    bool no_namespace_op = styler.GetPropertyInt("double_colons_are_names") != 0;
    // bool be_verbose = strchr(styler.GetProperties(), 'v') != NULL;
    {
        // We need to modify the starting levels. Curly braces on the current or 
        // previous lines affect their respective level because the level of a line 
        // is calculated from its starting level.
        int startOfCurrent = styler.LineStart(lineCurrent);
        if (lineCurrent > 0) { 
            int startOfPrev = styler.LineStart(lineCurrent-1);
            levelPrev = ((styler.LevelAt(lineCurrent-1)
                          & SC_FOLDLEVELNUMBERMASK
                          & ~SC_FOLDLEVELBASE)
                         + getFoldLevelModifier(styler,startOfPrev,startOfCurrent));
            if (levelPrev < 0) {
                levelPrev = 0;
            }
        }
        levelCurrent = levelPrev + getFoldLevelModifier(styler,startOfCurrent,startPos);
        if (levelCurrent < 0) {
            levelCurrent =  0;
        }
    }
    
    // Get the styler and the character variables ready to go.
    char lexerMask = 0x3f; // 6 bits
    styler.StartAt(startPos, lexerMask);
    char chPrev = styler.SafeGetCharAt(startPos - 1);
    char chNext = styler.SafeGetCharAt(startPos);
    styler.StartSegment(startPos);
    static int q_states[] = {SCE_PL_STRING_QQ,
                             SCE_PL_STRING_QR,
                             SCE_PL_STRING_QW,
                             SCE_PL_STRING_QX};
    static const char* q_chars = "qrwx";

    unsigned int i;
    unsigned int actualLengthDoc = styler.Length();
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
        // This has been here since day 1 but it's a bad idea as
        // it can result in lexing of the previous item to bleed
        // over the \r
        //
        // Obsolete code left in for documentation purposes:
        // if (ch == '\r' && chNext == '\n') {
        // continue;
        // }

        if (fold) {
    
            // Apply folding at the end of the line (if required).
            if (ch == '\n' || (ch == '\r' && chNext != '\n')) {
                int lev = levelPrev;
                if (lev < 0 || lev > 0x3ff)
                    lev = 0;
                if (!hasVisibleChars) {
                    lev |= SC_FOLDLEVELWHITEFLAG;
                }
                if (levelCurrent > levelPrev && i < lengthDoc - 1) {
                    lev |= SC_FOLDLEVELHEADERFLAG;
                }
                styler.SetLevel(lineCurrent, lev | SC_FOLDLEVELBASE);
                lineCurrent++;
                levelPrev = (levelCurrent > 0) ? levelCurrent : 0;
                hasVisibleChars = false;
            } else if (!hasVisibleChars && !isspacechar(ch)) {
                hasVisibleChars = true;
            }
        }
        
        if (HereDoc.State == 1 && isEOLChar(ch)) {
            // Begin of here-doc (the line after the here-doc delimiter):
            // Move back skipping whitespace, looking for semi-colon or start
            char hch;
            HereDoc.HasSemiColon = false;
            int j = i - 1;
            if (styler.SafeGetCharAt(j) == 10) j--;
            if (styler.SafeGetCharAt(j) == 13) j--;
            for (; j > 0 && (unsigned int) j > startPos; j--) {
              hch = styler.SafeGetCharAt(j);
              if (isEOLChar(hch)) {
                break;
              } else if (hch == ';') {
                HereDoc.HasSemiColon = true;
                break;
              } else if (hch == ' ' || hch == '\t') {
                 // continue;
              } else {
                break;
              }
            }
            HereDoc.State = 2;
            styler.ColourTo(i-1, state);
            if (HereDoc.Quoted && state == SCE_PL_HERE_DELIM) {
                // Missing quote at end of string! We are stricter than perl.
                state = SCE_PL_ERROR;
            } else {
                state = SCE_PL_HERE_Q;
            }
        }
        
        // Skip over styles that have been set as stdio
        {
            // KOMODO -- interactive shell colorizing
            int origStyle = safeStyleAt(i, styler);
            if (isStdioChar(origStyle)) {
                styler.ColourTo(i - 1, state);
                while (++i < lengthDoc) {
                    int style = safeStyleAt(i, styler);
                    if (!isStdioChar(style)) {
                        break;
                    }
                }
                if (i < lengthDoc) {
                    chPrev = styler.SafeGetCharAt(i - 1);
                    chNext = styler[i];
                    i--;
                }
                styler.StartSegment(i);
                state = SCE_PL_DEFAULT;
                continue;
            }
        }

        if (state == SCE_PL_DEFAULT) {
            if (isSafeDigit(ch)) {
                styler.ColourTo(i - 1, state);
                state = SCE_PL_NUMBER;
                if (ch == '0') {
                    if (chNext == 'x' || chNext == 'X') {
                        // Perl 5.14: 0X and 0B are now supported.
                        numBase = 16;
                        // Move to the next char, 'x' isn't allowed inside a number
                        advanceOneChar(i, ch, chNext, chNext2);
                    } else if (chNext == 'b' || chNext == 'B') {
                        numBase = 2;
                        // 'b' isn't allowed either
                        advanceOneChar(i, ch, chNext, chNext2);
                    } else {
                        numBase = 8;
                    }
                } else {
                    numDots = 0;
                    numExponents = 0;
                    numBase = 10;
                }
            } else if (iswordstart(ch)) {
                binaryOperatorExpected = false;
                styler.ColourTo(i - 1, state);
                styler.Flush();
                if (i > 0 && followsStartIndexer(styler, i - 1)) {
                    preferRE = false;
                    
                    // Watch out for single-char barewords
                    // And also watch out for q-strings in this context
                    if (ch == 'q') {
                        if (!iswordchar(chNext)) {
                            if (precedesIndexer(styler, i + 1, lengthDoc)) {
                                // color preceding string,
                                // go to default
                                styler.ColourTo(i, SCE_PL_STRING);
                                // stay in state = SCE_PL_DEFAULT;
                            } else {
                                state = SCE_PL_STRING_Q;
                                Quote.New(1);
                            }
                        } else if (strchr(q_chars, chNext) && !iswordchar(chNext2)) {
                             if (precedesIndexer(styler, i + 2, lengthDoc)) {
                                 // color preceding string,
                                 // go to default
                                 styler.ColourTo(i + 1, SCE_PL_STRING);
                                 // stay in state = SCE_PL_DEFAULT;
                             } else {
                                 const char *hit = strchr(q_chars, chNext);
                                 if (hit != NULL) {
                                     state = q_states[hit - q_chars];
                                 } else {
                                     state = SCE_PL_STRING_QQ;
                                 }
                                 Quote.New(1);
                             }
                             advanceOneChar(i, ch, chNext, chNext2);
                        } else {
                            state = SCE_PL_WORD;
                        }
                    } else if (!iswordchar(chNext)) {
                        styler.ColourTo(i, SCE_PL_STRING);
                        braceStartsBlock = true;
                    } else {
                        state = SCE_PL_WORD;
                    }
                    // Look for keyword-like things that are followed
                    // by fat commas.  You might think this doesn't always
                    // work, but Perl doesn't allow
                    // q=>...=
                    // qq=>...=
                    // s=>...=...=
                    // tr=>...=...=
                    // y=>...=...=

                } else if (ch == 's' && !isSafeAlnum(chNext) && !isEOLChar(chNext)) {
                    if (isFatCommaNext(styler, i + 1, lengthDoc)) {
                        styler.ColourTo(i, SCE_PL_STRING_Q);
                        state = SCE_PL_DEFAULT;
                    } else {
                        state = SCE_PL_REGSUBST;
                        Quote.New(2);
                    }
                } else if (ch == 'x' && !isSafeAlnum(chNext)) {
                    if (isFatCommaNext(styler, i + 1, lengthDoc)) {
                        styler.ColourTo(i, SCE_PL_STRING_Q);
                        state = SCE_PL_DEFAULT;
                    } else {
                        styler.ColourTo(i, SCE_PL_OPERATOR);
                    }
                } else if (ch == 'm' && !isSafeAlnum(chNext)) {
                    if (isFatCommaNext(styler, i + 1, lengthDoc)) {
                        styler.ColourTo(i, SCE_PL_STRING_Q);
                        state = SCE_PL_DEFAULT;
                    } else {
                        state = SCE_PL_REGEX;
                        Quote.New(1);
                    }
                } else if (ch == 'q' && !isSafeAlnum(chNext)) {
                    if (isFatCommaNext(styler, i + 1, lengthDoc)) {
                        styler.ColourTo(i, SCE_PL_STRING_Q);
                        state = SCE_PL_DEFAULT;
                    } else {
                        state = SCE_PL_STRING_Q;
                        Quote.New(1);
                    }
                } else if (ch == 'y' && !isSafeAlnum(chNext)) {
                    if (isFatCommaNext(styler, i + 1, lengthDoc)) {
                        styler.ColourTo(i, SCE_PL_STRING_Q);
                        state = SCE_PL_DEFAULT;
                    } else {
                        state = SCE_PL_REGSUBST;
                        Quote.New(2);
                    }
                } else if (ch == 't' && chNext == 'r' && !isSafeAlnum(chNext2)) {
                    if (isFatCommaNext(styler, i + 2, lengthDoc)) {
                        styler.ColourTo(i + 1, SCE_PL_STRING_Q);
                        state = SCE_PL_DEFAULT;
                    } else {
                        state = SCE_PL_REGSUBST;
                        Quote.New(2);
                    }
                    advanceOneChar(i, ch, chNext, chNext2);
                } else if (ch == 'q' && (chNext == 'q' || chNext == 'r' || chNext == 'w' || chNext == 'x') && !isSafeAlnum(chNext2)) {
                    if (isFatCommaNext(styler, i + 2, lengthDoc)) {
                        styler.ColourTo(i + 1, SCE_PL_STRING_Q);
                        state = SCE_PL_DEFAULT;
                    } else {
                        const char *hit = strchr(q_chars, chNext);
                        if (hit != NULL) {
                            state = q_states[hit - q_chars];
                        }
                        Quote.New(1);
                    }
                    advanceOneChar(i, ch, chNext, chNext2);

                } else {
                    preferRE = false;
                    if (wordEndsHere(chNext, chNext2, no_namespace_op)) {
                        // We need that if length of word == 1!
                        // This test is copied from the SCE_PL_WORD handler.
                        int wordStart = styler.GetStartSegment();
                        if (classifyWordPerl(wordStart, i, lengthDoc,
                                             keywords, styler, &braceStartsBlock) == SCE_PL_WORD)
                        {               
                            preferRE = RE_CanFollowKeyword(wordStart,i,styler);
                        } else {
                            binaryOperatorExpected = true;
                        }
                        state = SCE_PL_DEFAULT;
                    } else {
                        state = SCE_PL_WORD;
                    }
                }
            } else if (ch == '#') {
                styler.ColourTo(i - 1, state);
                previousState = state;
                state = SCE_PL_COMMENTLINE;
            
            } else if (ch == '\"') {
                styler.ColourTo(i - 1, state);
                state = SCE_PL_STRING;
                Quote.New(1);
                Quote.Open(ch);
            } else if (ch == '\'') {
                // Don't handle archaic calls.
                if (chPrev != '&') {
                    styler.ColourTo(i - 1, state);
                    state = SCE_PL_CHARACTER;
                    Quote.New(1);
                    Quote.Open(ch);
                }
            } else if (ch == '`') {
                styler.ColourTo(i - 1, state);
                state = SCE_PL_BACKTICKS;
                Quote.New(1);
                Quote.Open(ch);

            // Handle all the variable indicators.
            } else if (ch == '$' || ch == '%' || ch == '@') {
                preferRE = false;
                binaryOperatorExpected = true;
                styler.ColourTo(i - 1, state);
                int variableType = 
                    (ch == '$') ? SCE_PL_SCALAR : (ch == '%') ? SCE_PL_HASH : SCE_PL_ARRAY;
                if (i == lengthDoc - 1) {
                    // Prevent a crash.
                    preferRE = true;
                    binaryOperatorExpected = false;
                    braceStartsBlock = true;
                    state = SCE_PL_OPERATOR;
                } else if (chNext == '{' && chNext2 == '^') {
                    // New builtins are coming in as ${^DESCRIPTION}
                    // To simplify brace-matching color the ${ as op,
                    // the inners as scalar, and the close-} will be
                    // colored as an op.
                    levelCurrent++;
                    i += 2;
                    styler.ColourTo(i, SCE_PL_OPERATOR);
                    chNext = styler.SafeGetCharAt(i+1);
                    state = variableType;
                    p_BraceInfo->add(SCE_PL_OPERATOR);
                } else if (isSafeAlnum(chNext) || chNext == '_' || chNext == '{') {
                    state = variableType;
                } else if (chNext == ':' && chNext2 == ':') {
                    advanceOneChar(i, ch, chNext, chNext2);
                    state = variableType;
                } else if (chNext == '^' && isSafeAlnum(chNext2)) {
                    i += 2;
                    chNext = styler.SafeGetCharAt(i+1);
                    styler.ColourTo(i, variableType);
                } else if (ch == '$' && chNext == '#') {
                    advanceOneChar(i, ch, chNext, chNext2);
                    state = SCE_PL_SCALAR;
                } else if (ch == '$' && chNext == '$') {
                    // $$ is a scalar if it isn't followed by '$' or varstart
                    // otherwise it's the start of a longer scalar thing,
                    // involving 2+ dereferences.
                    // Helpful thing -- the 'x' operator requires white-space
                    //
                    // $$ x ... != $$x ...
                    // So if $$ is followed by neither '$' nor var name,
                    // it's atomic.  Otherwise we have a sequence of '$'
                    // which must eventually be followed by a brace or varname
                    //
                    // And we let ${...} be colored separately.
                    
                    if (chNext2 == '$') {
                        i += 2;
                        while ((chNext = styler.SafeGetCharAt(i + 1)) == '$') {
                            i++;
                        }
                        state = SCE_PL_SCALAR;
                    } else if (isSafeAlpha(chNext2) || chNext2 == '_') {
                        advanceOneChar(i, ch, chNext, chNext2);
                        state = SCE_PL_SCALAR;
                    } else {
                        advanceOneChar(i, ch, chNext, chNext2);
                        styler.ColourTo(i, variableType);
                        state = SCE_PL_DEFAULT;
                        braceStartsBlock = true;
                    }
                } else if (ch == '@' && chNext == '$') {
                    advanceOneChar(i, ch, chNext, chNext2);
                    state = SCE_PL_ARRAY;
                } else if (ch == '%' && chNext == '$') {
                    advanceOneChar(i, ch, chNext, chNext2);
                    state = SCE_PL_HASH;
                } else if (ispunct(chNext)) {
                    if (chNext == '{') {
                        p_BraceInfo->add(SCE_PL_VARIABLE_INDEXER);
                        levelCurrent++;
                    }
                    advanceOneChar(i, ch, chNext, chNext2);
                    styler.ColourTo(i, variableType);
                    braceStartsBlock = false;
                } else {
                    advanceOneChar(i, ch, chNext, chNext2);
                    styler.ColourTo(i, SCE_PL_OPERATOR);
                    preferRE = true;
                    binaryOperatorExpected = false;
                    braceStartsBlock = true;
                }

            } else if (ch == '*') {
                styler.ColourTo(i - 1, state);
                if (chNext == '*') {
                    advanceOneChar(i, ch, chNext, chNext2);
                    styler.ColourTo(i, SCE_PL_OPERATOR);
                    braceStartsBlock = true;
                } else if (isSafeAlpha(chNext) || chNext == '_' || chNext == '{') {
                    preferRE = false;
                    state = SCE_PL_SYMBOLTABLE;
                } else if (chNext == ':' && chNext2 == ':') {
                    preferRE = false;
                    i++;
                    state = SCE_PL_SYMBOLTABLE;
                } else {
                    binaryOperatorExpected = false;
                    styler.ColourTo(i,SCE_PL_OPERATOR);
                    braceStartsBlock = true;
                }
                
            } else if ((ch == '/' || ch == '?') && preferRE) {
                styler.ColourTo(i - 1, state);
                state = SCE_PL_REGEX;
                Quote.New(1);
                Quote.Open(ch);

            } else if (ch == '<') {
                // Recognise the '<<' symbol - either a here document or a left bit-shift operator.
                if (chNext == '<') {
                    styler.ColourTo(i - 1, state);
                    advanceOneChar(i, ch, chNext, chNext2);
                    styler.ColourTo(i, SCE_PL_OPERATOR);

                    // It sucks, but we need to look both backwards and
                    // forwards to disambiguate here docs.
                    //
                    // Requirements for '<<' to be a here doc op
                    // After:
                    // space | quote | apos | letter _ '_'
                    //
                    // Before:
                    // skip spaces, get one of:
                    // op style
                    // ident

                    // Don't look at binaryOperatorExpected, etc.
                    // They don't give enough info

                    bool couldBeHereDoc = false;

                    if (chNext2 == '\''
                        || chNext2 == '"'
                        || chNext2 == '_'
                        || chNext2 == '`'
                        || isSafeAlpha(chNext2)) {
                        couldBeHereDoc = true;
                    } else if (chNext2 == ' ') {
                        // Look ahead -- if we hit a newline, it's not
                        // If we hit a digit or scalar, it isn't
                        // If we hit a string, it isn't
                        // If we hit an operator, it's hard to say...
                        int inext;
                        char inextChar;
                        // Watch out for those border situations.
                        for (inext = i + 2; inext < (int) actualLengthDoc; inext++) {
                            inextChar = styler.SafeGetCharAt(inext);
                            if (inextChar == ' ' || inextChar == '\t') {
                                continue;
                            } else {
                                if (isEOLChar(inextChar)) {
                                // nothing left to do
                                } else if (isSafeAlnum(inextChar) || inextChar == '_') {
                                // nothing left to do
                                } else {
                                    switch(inextChar) {
                                        case '@':
                                        case '$':
                                        case '(':
                                            // nothing left to do
                                            break;
                                            // These two are ambiguous, so turn it on
                                            // Use parens to turn off here-doc
                                        case '-':
                                        case '+':
                                            couldBeHereDoc = true;
                                            break;
                                            
                                        case '"':
                                        case '\'':
                                            // This gets more complicated
                                            // If the first char after the quote
                                            // is EOL, not a here-doc
                                            // If it's a digit, not a here-doc
                                            // Otherwise assume it is, and
                                            // ignore space between
                                            // << and the quoted target.
                                            // Whatever happens, we're breaking
                                            // at this point.
                                            if (inext < (int) actualLengthDoc - 1) {
                                                char inext2Char = styler.SafeGetCharAt(inext + 1);
                                                if (inext2Char == '\r'
                                                    || inext2Char == '\n') {
                                                    // not a here doc
                                                } else if (isSafeDigit(inext2Char)) {
                                                    // not a here doc
                                                } else {
                                                    couldBeHereDoc = true;
                                                }
                                            }
                                            break;
                                            
                                        default:
                                            // Most other chars indicate something
                                            // like <<[string] op...
                                            couldBeHereDoc = true;
                                    }
                                }
                                break;
                            }
                        }
                    }
                
                    if (couldBeHereDoc) {
                        // Look back to see what else we have
                        int prevStyle;
                        int iprev;
                        char iprevChar;
                        styler.Flush();
                        for (iprev = i - 2; iprev >= 0; iprev--) {
                            prevStyle = safeStyleAt(iprev, styler);
                            if (prevStyle == SCE_PL_DEFAULT) {
                                iprevChar = styler.SafeGetCharAt(iprev);
                                if ((unsigned int) iprevChar < 128 && isspace(iprevChar)) {
                                    continue;
                                } else {
                                    couldBeHereDoc = false;
                                    break;
                                }
                            } else {
                                switch (prevStyle) {
                                    case SCE_PL_OPERATOR:
                                    case SCE_PL_VARIABLE_INDEXER:
                                        // Make sure it isn't a space colored as op
                                        // due to context.
                                        iprevChar = styler.SafeGetCharAt(iprev);
                                        if ((unsigned int) iprevChar < 128 && isspace(iprevChar)) {
                                            continue;
                                        } else {
                                            couldBeHereDoc = true;
                                        }
                                        break;
                                    case SCE_PL_WORD:
                                    case SCE_PL_IDENTIFIER:
                                        // Assume word|ident << string starts a here-doc
                                    case SCE_PL_HERE_DELIM:
                                        // Two here-docs in a row that aren't stacked
                                        // (see bug 76004).
                                        couldBeHereDoc = true;
                                        break;
                                    
                                    case SCE_PL_SCALAR:
                                        iprev -= 1;
                                        styler.Flush();
                                        while (iprev > 0 &&
                                               safeStyleAt(iprev, styler) == SCE_PL_SCALAR){
                                            iprev -= 1;
                                        }
                                        while (styler.SafeGetCharAt(iprev) == ' ') {
                                            iprev -= 1;
                                        }
                                        prevStyle = safeStyleAt(iprev, styler);
                                        if (prevStyle == SCE_PL_WORD
                                            || prevStyle == SCE_PL_IDENTIFIER) {
                                            couldBeHereDoc = true;
                                        } else {
                                            couldBeHereDoc = false;
                                        }
                                        break;
                                    
                                    default:
                                        couldBeHereDoc = false;
                                }
                                break;
                            }
                        }
                    }

                    if (couldBeHereDoc) {
                        state = SCE_PL_HERE_DELIM;
                        HereDoc.State = 0;
                    }

                } else {
                    styler.ColourTo(i-1, state);
                    preferRE = false;
                    binaryOperatorExpected = false;
                    braceStartsBlock = true;
                    if (chNext == '=') {
                        if (chNext2 == '>') {
                            i += 2;
                            chNext = styler.SafeGetCharAt(i + 1);
                        } else {
                            advanceOneChar(i, ch, chNext, chNext2);
                        }
                    }
                    // Leave state at default for all three operators
                    styler.ColourTo(i,SCE_PL_OPERATOR);
                }
            } else if (ch == '=' && isSafeAlpha(chNext) && (i == 0 || isEOLChar(chPrev))) {
                styler.ColourTo(i - 1, state);
                state = SCE_PL_POD;
                levelCurrent++;
            } else if (ch == '-' && chPrev != '-' && !binaryOperatorExpected && 
                       isWordBeforeFatComma(styler,i+1,lengthDoc)) {
                styler.ColourTo(i-1, state);
                state = SCE_PL_WORD;
                braceStartsBlock = true;
            } else if (ch == '-' && chNext == '>') {
                styler.ColourTo(i-1,state);
                styler.ColourTo(i+1,SCE_PL_OPERATOR);
                advanceOneChar(i, ch, chNext, chNext2);
                state = SCE_PL_UNKNOWN_FIELD;
                braceStartsBlock = false;
            } else if (ch == '-' && isSingleCharOp(chNext) && !isSafeAlnum(chNext2)) {
                styler.ColourTo(i - 1, state);
                styler.ColourTo(i + 1, SCE_PL_WORD);
                state = SCE_PL_DEFAULT;
                preferRE = false;
                binaryOperatorExpected = false;
                braceStartsBlock = true;
                advanceOneChar(i, ch, chNext, chNext2);
            } else if (ch == '=' && chNext == '>') {
                styler.ColourTo(i - 1, state);
                styler.ColourTo(i + 1, SCE_PL_OPERATOR);
                preferRE = false;
                binaryOperatorExpected = false;
                braceStartsBlock = false;
                advanceOneChar(i, ch, chNext, chNext2);
            } else if (ch == ':' && chNext == ':' && no_namespace_op) {
                preferRE = true;
                binaryOperatorExpected = true;
                braceStartsBlock = true;
                styler.ColourTo(i - 1, state);
                if (iswordstart(chNext2)) {
                    state = SCE_PL_WORD;
                } else {
                    styler.ColourTo(i + 1, SCE_PL_IDENTIFIER);
                }
                advanceOneChar(i, ch, chNext, chNext2);
            } else if (ch == '.') {
                styler.ColourTo(i - 1, state);
                // Now what we do next depends on what follows
                if (isSafeDigit(chNext)) {
                    state = SCE_PL_NUMBER;
                    numDots = 1;
                    numExponents = 0;
                    numBase = 10;
                } else {
                    if (chNext == '.') {
                        if (chNext2 == '.') {
                            ch = chNext2;
                            chNext = styler.SafeGetCharAt(i + 3);
                            i += 2;
                        } else {
                            advanceOneChar(i, ch, chNext, chNext2);
                        }
                    }
                    // Either it's a concat op or a flip op
                    preferRE = true;
                    braceStartsBlock = false;
                    binaryOperatorExpected = false;
                    styler.ColourTo(i, SCE_PL_OPERATOR);
                    // And stay in default state
                }
            } else if (isPerlOperator(ch)) {
                if (ch == ')' || ch == ']' || (ch == '}' && variableNestingCount)) {
                    preferRE = false;
                } else {
                    preferRE = true;
                }
                
                styler.ColourTo(i - 1, state);
                int operatorType = SCE_PL_OPERATOR;

                // If this is an open bracket operator, start a fold.
                if (ch == '[') {
                    operatorType = SCE_PL_VARIABLE_INDEXER;
                    variableNestingCount++;
                    braceStartsBlock = false;
                    binaryOperatorExpected = false;
                    levelCurrent++;
                } else if (ch == '{') {
                    bool look_for_bareword = false;
                    if (!braceStartsBlock) {
                        operatorType = SCE_PL_VARIABLE_INDEXER;
                        variableNestingCount++;
                        look_for_bareword = (variableNestingCount == 1);
                    }
                    p_BraceInfo->add(operatorType);
                    levelCurrent++;
                    binaryOperatorExpected = false;
                    if (look_for_bareword && lookingAtBareword(styler, i + 1, actualLengthDoc)) {
                        // fprintf(stderr, "Looking at a bareword after a brace at posn %d\n", i);
                        styler.ColourTo(i, SCE_PL_VARIABLE_INDEXER);
                        ch = colouriseBareword(styler, i, state, actualLengthDoc);
                        chNext = styler.SafeGetCharAt(i + 1);
                    }
                } else if (ch == '(') {
                    binaryOperatorExpected = false;
                    levelCurrent++;
                    braceStartsBlock = false;
                // If this is a close bracket operator, end the previous fold.
                } else if (ch == ']') {
                    if (variableNestingCount) {
                        operatorType = SCE_PL_VARIABLE_INDEXER;
                        variableNestingCount--;
                        binaryOperatorExpected = true;
                        preferRE = false;
                        braceStartsBlock = false;
                    
                        if (chNext == '-' && chNext2 == '>') {
                            state = SCE_PL_UNKNOWN_FIELD;
                        }

                    } else {
                        binaryOperatorExpected = false;
                    }
                    if (levelCurrent > 0) {
                        levelCurrent--;
                    }
                } else if (ch == '}') {
                    operatorType = p_BraceInfo->getStyle();
                    if (operatorType == -1) {
                        // fprintf(stderr, " op type: %d\n", operatorType);
                        operatorType = GetMatchingStyle(i, styler);
                        // fprintf(stderr, "GetMatchingStyle(%d) => %d\n", i, operatorType);
                    }
                    // Keep this updated
                    if (operatorType == SCE_PL_VARIABLE_INDEXER) {
                        if (variableNestingCount > 0) {
                            variableNestingCount--;
                        }
                        binaryOperatorExpected = true;
                        preferRE = false;
                        if (chNext == '-' && chNext2 == '>') {
                            state = SCE_PL_UNKNOWN_FIELD;
                        }
                    } else {
                        binaryOperatorExpected = false;
                    }
                    if (levelCurrent > 0) {
                        levelCurrent--;
                    }
                    braceStartsBlock = false;
                } else if (ch == ')') {
                    binaryOperatorExpected = false;
                    braceStartsBlock = true;
                    if (levelCurrent > 0) {
                        levelCurrent--;
                    }
                } else {
                    // Analyze the other operators
                    binaryOperatorExpected = false;
                    switch (ch) {
                        case '=':
                        case ',':
                        case '\\':
                        case '?':
                            braceStartsBlock = false;
                            break;
                            
                        case '&':
                        case '|':
                            braceStartsBlock = (chPrev != ch);
                            break;

                        case ':':
                            // If we're in a ternary operator, bSB is false
                            // If we're after a label, it doesn't.
                            // Let's look back: if we see /(^|;(10))\s*\w+(5|11)<here>/,
                            // assume it's a label.  Otherwise it's ternary
                            braceStartsBlock = afterLabel(i - 1, styler);
                            break;

                        case '+':
                        case '-':
                            // If we're followed by the same char,
                            // handle preferRE etc differently
                            if (chNext == ch) {
                                binaryOperatorExpected = true;
                                preferRE = false;
                                braceStartsBlock = true;
                                advanceOneChar(i, ch, chNext, chNext2);
                            }
                            break;
                        
                        case '/':
                            if (chNext == '/') {
                                // Perl 5.10 definedness or-operator
                                advanceOneChar(i, ch, chNext, chNext2);
                            }
                            braceStartsBlock = true;
                            break;

                        default:
                            braceStartsBlock = true;
                            break;
                    }
                }
                styler.ColourTo(i, operatorType);
            }
        } else if (state == SCE_PL_WORD) {
            if (ch == ':' && chNext == ':' && no_namespace_op) {
                // Skip over the namespace separator
                if (!iswordstart(chNext2)) {
                    // The word ends here
                    preferRE = true;
                    binaryOperatorExpected = true;
                    braceStartsBlock = true;
                    styler.ColourTo(i, SCE_PL_IDENTIFIER);
                    state = SCE_PL_DEFAULT;
                }
                ch = chNext2;
                chNext = styler.SafeGetCharAt(i + 3);
                i += 2;
            } else if (wordEndsHere(chNext, chNext2, no_namespace_op)) {
                styler.Flush();
                // Be strict in what we'll color bare
                if ((i == lengthDoc - 1 || chNext == '}')
                    && followsStartIndexer(styler, i - 1)) {
                    styler.ColourTo(i, SCE_PL_STRING);
                    state = SCE_PL_DEFAULT;
                } else {
                    bool doDefault = false;
                    unsigned int kwdStartPos = styler.GetStartSegment();
                    char sequenceStartChar = styler[kwdStartPos];
                    if (sequenceStartChar == '_') {
                        if (isMatch(styler, lengthDoc, kwdStartPos, "__DATA__")) {
                            styler.ColourTo(i, SCE_PL_DATASECTION);
                            state = SCE_PL_DATASECTION;
                        } else if (isMatch(styler, lengthDoc, kwdStartPos, "__END__")) {
                            styler.ColourTo(i, SCE_PL_DATASECTION);
                            state = SCE_PL_DATASECTION;
                        } else {
                            doDefault = true;
                        }
                    } else if (kwdStartPos + 5 == i
                               && sequenceStartChar == 'f'
                               && isMatch(styler, lengthDoc, kwdStartPos, "format")
                               && atStartOfFormatStmt(i, lengthDoc, styler)) {
                        state = SCE_PL_FORMAT;
                        // Don't need to set chNext2
                        ch = styler.SafeGetCharAt(i);
                        chNext = styler.SafeGetCharAt(i + 1);
                    } else {
                        doDefault = true;
                    }
                    if (doDefault) {
                        state = SCE_PL_DEFAULT;
                        ch = ' ';
                    
                        // Recognise the beginning of a subroutine - enter the SUB state.
                        if (kwdStartPos+2 == i && isMatch(styler, lengthDoc, kwdStartPos, "sub")) { 
                            for (unsigned int j = i+1;j < lengthDoc;j++) {
                                char c = styler.SafeGetCharAt(j);
                                if (!isspacechar(c)) {
                                    if (isSafeAlpha(c) || c == '_' || c == '{' || c == ';' || c == '(') {
                                        styler.ColourTo(i,SCE_PL_WORD);
                                        state = SCE_PL_SUB;
                                    } else {
                                        styler.ColourTo(i,SCE_PL_IDENTIFIER);
                                    }
                                    break;
                                }
                            }
                            styler.ColourTo(i,SCE_PL_WORD);
                            braceStartsBlock = true;
                         
                            // Colour the word as a number, identifier or keyword.
                        } else if (classifyWordPerl(kwdStartPos,i,lengthDoc,keywords,styler, &braceStartsBlock) == SCE_PL_WORD) {             
                            preferRE = RE_CanFollowKeyword(kwdStartPos,i,styler);

                        } else {
                            binaryOperatorExpected = true;
                            braceStartsBlock = true;
                        }
                    }
                }
            }
        } else if (state == SCE_PL_NUMBER) {
            bool restyle = false;
            if (isSafeDigit(ch) || ch == '_') {
                // Keep going
            } else if (numBase == 10) {
                if (ch == '.') {
                    restyle = !(++numDots == 1 && numExponents == 0 && chNext != '.');
                } else if (ch == 'e' || ch == 'E') {
                    restyle = !(++numExponents == 1);
                } else if (ch == '-' && (chPrev == 'e' || chPrev == 'E')) {
                    // Keep going
                } else {
                    restyle = true;
                }
            } else if (numBase == 16 && strchr("abcdefABCDEF", ch)) {
                // Keep going
            } else {
                restyle = true;
            }
            if (restyle) {
                styler.ColourTo(i - 1, state);
                // Retry with this character.
                // Special-case handling of newlines due to how folding works
                if (ch == '\n' || ch == '\r') {
                    // Default is fine, no need to do anything else.
                } else if (ch == '.' && chNext != '.') {
                    // Special case this, otherwise something like
                    // 0x3.4 will be colorized as two contiguous numbers
                    styler.ColourTo(i, SCE_PL_OPERATOR);
                } else {
                    retreatOneChar(i, chPrev, ch, chNext);
                }
                state = SCE_PL_DEFAULT;
                preferRE = false;
                binaryOperatorExpected = true;
                braceStartsBlock = true;
            }
        } else if (state == SCE_PL_COMMENTLINE) {
            if (isEOLChar(ch)) {
                styler.ColourTo(i - 1, state);
                state = previousState;
            }
        } else if (state == SCE_PL_HERE_DELIM) {
            //
            // From perldata.pod:
            // ------------------
            // A line-oriented form of quoting is based on the shell ``here-doc''
            // syntax.
            // Following a << you specify a string to terminate the quoted material,
            // and all lines following the current line down to the terminating
            // string are the value of the item.
            // The terminating string may be either an identifier (a word),
            // or some quoted text.
            // If quoted, the type of quotes you use determines the treatment of
            // the text, just as in regular quoting.
            // An unquoted identifier works like double quotes.
            // There must be no space between the << and the identifier.
            // (If you put a space it will be treated as a null identifier,
            // which is valid, and matches the first empty line.)
            // The terminating string must appear by itself (unquoted and with no
            // surrounding whitespace) on the terminating line.
            //
            if (HereDoc.State == 0) { // '<<' encountered
                HereDoc.State = 1;
                HereDoc.Quote = ch;
                HereDoc.Quoted = false;
                HereDoc.DelimiterLength = 0;
                HereDoc.Delimiter[HereDoc.DelimiterLength] = '\0';
                
                // A quoted here-doc delimiter.
                if (ch == '\'' || ch == '"' || ch == '`') { 
                    HereDoc.Quoted = true;
                
                   // TODO: does this need to be handled differently? as a ref?
                } else if (chNext == '\\') {
            
                   // An unquoted here-doc delimiter.
                } else if (isSafeAlnum(ch)) {
                    HereDoc.Delimiter[HereDoc.DelimiterLength++] = ch;
                    HereDoc.Delimiter[HereDoc.DelimiterLength] = '\0';
                
                // deprecated here-doc delimiter
                } else if (isspacechar(ch)) {
                    styler.ColourTo(i, state);
                    state = SCE_PL_DEFAULT;
                    braceStartsBlock = true;
                }

            } else if (HereDoc.State == 1) { // collect the delimiter
                if (HereDoc.Quoted) { // a quoted here-doc delimiter
                    if (ch == HereDoc.Quote) { // closing quote => end of delimiter
                        styler.ColourTo(i, state);
                        state = SCE_PL_DEFAULT;
                        binaryOperatorExpected = true;
                        braceStartsBlock = true;
                    } else {
                        if (ch == '\\' && chNext == HereDoc.Quote) { // escaped quote
                            advanceOneChar(i, ch, chNext, chNext2);
                        }
                        HereDoc.Delimiter[HereDoc.DelimiterLength++] = ch;
                        HereDoc.Delimiter[HereDoc.DelimiterLength] = '\0';
                    }
                } else { // an unquoted here-doc delimiter
                    if (isSafeAlnum(ch)) {
                        HereDoc.Delimiter[HereDoc.DelimiterLength++] = ch;
                        HereDoc.Delimiter[HereDoc.DelimiterLength] = '\0';
                    } else {
                        styler.ColourTo(i - 1, state);
                        state = SCE_PL_DEFAULT;
                        braceStartsBlock = true;
                        // Retry with this character.
                        retreatOneChar(i, chPrev, ch, chNext);
                    }
                }
                if (HereDoc.DelimiterLength >= static_cast<int>(sizeof(HereDoc.Delimiter)) - 1) {
                    styler.ColourTo(i - 1, state);
                    state = SCE_PL_ERROR;
                    braceStartsBlock = true;
                }
            }

        } else if (HereDoc.State == 2 && isEOLChar(chPrev)) {

            // Look for a blank line to end a space delimited here document.
            if (isspacechar(HereDoc.Quote) && isEOLChar(ch)) {
                styler.ColourTo(i - 1, state);
                styler.ColourTo(i, SCE_PL_HERE_DELIM);
                state = SCE_PL_DEFAULT;
                HereDoc.State = 0;
                preferRE = HereDoc.HasSemiColon;
                HereDoc.HasSemiColon = false;
                braceStartsBlock = true;
            
            // Look for the here document's delimiter.
            } else if (isMatch(styler, lengthDoc, i, HereDoc.Delimiter)) {
                styler.ColourTo(i - 1, state);
                i += HereDoc.DelimiterLength - 1;
                chNext = styler.SafeGetCharAt(i + 1);
                if (isEOLChar(chNext)) {
                    styler.ColourTo(i, SCE_PL_HERE_DELIM);
                    state = SCE_PL_DEFAULT;
                    HereDoc.State = 0;
                    preferRE = HereDoc.HasSemiColon;
                    HereDoc.HasSemiColon = false;
                    braceStartsBlock = true;
                }
            }
            
        } else if (state == SCE_PL_SCALAR || state == SCE_PL_ARRAY || state == SCE_PL_HASH || 
                   state == SCE_PL_SYMBOLTABLE) { 
            
            // Recognise if the variable is indexed.
            if (ch == '{' || ch == '[') {
                styler.ColourTo(i-1, state);
                styler.ColourTo(i, SCE_PL_VARIABLE_INDEXER);
                variableNestingCount++;
                binaryOperatorExpected = false;
                levelCurrent++;
                if (ch == '{') {
                    p_BraceInfo->add(SCE_PL_VARIABLE_INDEXER);
                }
                state = SCE_PL_DEFAULT;
                braceStartsBlock = false;
                if (lookingAtBareword(styler, i + 1, actualLengthDoc)) {
                    // fprintf(stderr, "Looking at a bareword after a brace indexer at posn %d\n", i);
                    ch = colouriseBareword(styler, i, state, actualLengthDoc);
                    chNext = styler.SafeGetCharAt(i + 1);
                }
            
            // Skip over the namespace symbol.
            } else if (chNext == ':' && chNext2 == ':') {
                if (no_namespace_op) {
                    ch = chNext2;
                    chNext = styler.SafeGetCharAt(i + 3);
                    i += 2;
                } else {
                    advanceOneChar(i, ch, chNext, chNext2);
                }
            } else if (ch == '-' && chNext == '>') {
                styler.ColourTo(i-1,state);
                styler.ColourTo(i+1,SCE_PL_OPERATOR);
                advanceOneChar(i, ch, chNext, chNext2);
                state = SCE_PL_UNKNOWN_FIELD;
                braceStartsBlock = false;
                
            // If the next character is not a legal variable character, colour 
            // the preceding variable name and return to the default state.
            } else if (isspacechar(chNext) || 
                       (isEndVar(chNext) && (chNext != '-' || chNext2 != '>'))) {
                styler.ColourTo(i, state);
                state = SCE_PL_DEFAULT;
                binaryOperatorExpected = true;
                braceStartsBlock = !isspacechar(chNext);
                if (ch == '(') {
                    levelCurrent++;
                } else if (strchr(")]}", ch) && levelCurrent > 0) {
                    levelCurrent--;
                }
            }

        } else if (state == SCE_PL_UNKNOWN_FIELD) {
            // after --> 
            if (ch == '{' || ch == '[') {
                styler.ColourTo(i, SCE_PL_VARIABLE_INDEXER);
                variableNestingCount++;
                binaryOperatorExpected = false;
                levelCurrent++;
                if (ch == '{') {
                    p_BraceInfo->add(SCE_PL_VARIABLE_INDEXER);
                }
                state = SCE_PL_DEFAULT;
                braceStartsBlock = false;
            } else if (ch == '(') {
                // It's a function name, using indirect accessor
                // notation:
                // $obj->[selector]->(args) ===
                // &{$obj->[selector]}(args)
                styler.ColourTo(i, SCE_PL_OPERATOR);
                binaryOperatorExpected = false;
                state = SCE_PL_DEFAULT;
                braceStartsBlock = false;
                levelCurrent++;
            } else if (iswordstart(ch)) {
                // It's a function name
                styler.ColourTo(i - 1, state);
                binaryOperatorExpected = true;
                if (!iswordchar(chNext)) {
                    state = SCE_PL_DEFAULT;
                } else {
                    state = SCE_PL_WORD;
                }
                braceStartsBlock = false;
            } else if (ch == '-' && chNext == '>') {
                // Another arrow?  Color it as an operator, and stay here.
                styler.ColourTo(i+1,SCE_PL_OPERATOR);
                advanceOneChar(i, ch, chNext, chNext2);
                braceStartsBlock = false;
            } else if (isspacechar(ch)) {
                // Color it blank, stay for another round.
                styler.ColourTo(i, SCE_PL_DEFAULT);
                braceStartsBlock = false;
            } else if (ch == '$' || ch == '%' || ch == '@') {
                // Move to default state and retry
                styler.ColourTo(i - 1, SCE_PL_DEFAULT);
                state = SCE_PL_DEFAULT;
                retreatOneChar(i, chPrev, ch, chNext);
            } else {
                // Give up: go to default state.
                state = SCE_PL_DEFAULT;
                braceStartsBlock = true;
                if (strchr(")]}", ch) && levelCurrent > 0) {
                    levelCurrent--;
                }
            }
        } else if (state == SCE_PL_POD) {
            if (ch == '=' && isEOLChar(chPrev) && isMatch(styler, lengthDoc, i, "=cut")) {
                i += 3;
                styler.ColourTo(i, state);
                state = SCE_PL_COMMENTLINE;
                braceStartsBlock = true;
                if (levelCurrent > 0) {
                    levelCurrent--;
                }
                ch = styler.SafeGetCharAt(i);
                chNext = styler.SafeGetCharAt(i + 1);
            }

        
        // Continue parsing a reg exp ...
        } else if (state == SCE_PL_REGEX || state == SCE_PL_STRING_QR) {
            if (!Quote.Up && !isspacechar(ch)) {
                Quote.Open(ch);
            } else if (ch == '\\' && Quote.Up != '\\') {
                // TODO: Is it safe to skip *every* escaped char?
                i++;
                ch = chNext;
                chNext = styler.SafeGetCharAt(i + 1);
            } else {
                if (ch == Quote.Down /*&& chPrev != '\\'*/) {
                    Quote.Count--;
                    if (Quote.Count == 0) {
                        Quote.Rep--;
                        if (Quote.Up == Quote.Down) {
                            Quote.Count++;
                        }
                    }
                    if (!isSafeAlpha(chNext)) {
                        if (Quote.Rep <= 0) {
                            styler.ColourTo(i, state);
                            state = SCE_PL_DEFAULT;
                            preferRE = false;
                            braceStartsBlock = true;
                        }
                    }
                } else if (ch == Quote.Up /*&& chPrev != '\\'*/) {
                    Quote.Count++;
                } else if (!isSafeAlpha(chNext)) {
                    if (Quote.Rep <= 0) {
                        styler.ColourTo(i, state);
                        state = SCE_PL_DEFAULT;
                        preferRE = false;
                        braceStartsBlock = true;
                    }
                } else if ((ch == '$' || ch == '@')
                           && isInterpolatingString(SCE_PL_STRING, chNext)) {
                    doInterpolateVariable(i, lengthDoc, state, ch, styler);
                    retreatOneChar(i, chPrev, ch, chNext);
                }
            }
        } else if (state == SCE_PL_REGSUBST) {
            if (!Quote.Up && !isspacechar(ch)) {
                Quote.Open(ch);
            } else if (ch == '\\' && Quote.Up != '\\') {
                // TODO: Is it safe to skip *every* escaped char?
                i++;
                ch = chNext;
                chNext = styler.SafeGetCharAt(i + 1);
            } else {
                if (Quote.Count == 0 && Quote.Rep == 1) {
                    /* We matched something like s(...) or tr{...}
                    * and are looking for the next matcher characters,
                    * which could be either bracketed ({...}) or non-bracketed
                    * (/.../).
                    *
                    * Number-signs are problematic.  If they occur after
                    * the close of the first part, treat them like
                    * a Quote.Up char, even if they actually start comments.
                    *
                    * If we find an alnum, we end the regsubst, and punt.
                    *
                    * Eric Promislow   ericp@activestate.com  Aug 9,2000
                    */
                    if (isspacechar(ch)) {
                        // Keep going
                    }
                    else if (ch != '_' && isSafeAlnum(ch)) {
                        // Don't allow an underscore here
                        styler.ColourTo(i, state);
                        state = SCE_PL_DEFAULT;
                        preferRE = false;
                        braceStartsBlock = true;
                        ch = ' ';
                    } else {
                        Quote.Open(ch);
                    }
                } else if (ch == Quote.Down /*&& chPrev != '\\'*/) {
                    Quote.Count--;
                    if (Quote.Count == 0) {
                        Quote.Rep--;
                    }
                    if (!isSafeAlpha(chNext)) {
                        if (Quote.Rep <= 0) {
                            styler.ColourTo(i, state);
                            state = SCE_PL_DEFAULT;
                            preferRE = false;
                            braceStartsBlock = true;
                            ch = ' ';
                        }
                    }
                    if (Quote.Up == Quote.Down) {
                        Quote.Count++;
                    }
                } else if (ch == Quote.Up /*&& chPrev != '\\'*/) {
                    Quote.Count++;
                } else if (!isSafeAlpha(chNext)) {
                    if (Quote.Rep <= 0) {
                        styler.ColourTo(i, state);
                        state = SCE_PL_DEFAULT;
                        braceStartsBlock = true;
                        preferRE = false;
                        ch = ' ';
                    }
                } else if ((ch == '$' || ch == '@')
                           && Quote.Rep == 2
                           && isInterpolatingString(SCE_PL_STRING, chNext)) {
                    doInterpolateVariable(i, lengthDoc, state, ch, styler);
                    retreatOneChar(i, chPrev, ch, chNext);
                }
            }

        // Quotes of all kinds...
        } else if (state == SCE_PL_STRING_Q || state == SCE_PL_STRING_QQ || 
                   state == SCE_PL_STRING_QX || state == SCE_PL_STRING_QW ||
                   state == SCE_PL_STRING || state == SCE_PL_CHARACTER ||
                   state == SCE_PL_BACKTICKS) {
            if (!Quote.Down && !isspacechar(ch)) {
                Quote.Open(ch);
            } else if (ch == '\\' && Quote.Up != '\\') {
                // TODO: Is it save to skip *every* escaped char?
                i++;
                ch = chNext;
                chNext = styler.SafeGetCharAt(i + 1);
            } else if (ch == Quote.Down) {
                Quote.Count--;
                if (Quote.Count == 0) {
                    Quote.Rep--;
                    if (Quote.Rep <= 0) {
                        styler.ColourTo(i, state);
                        state = SCE_PL_DEFAULT;
                        braceStartsBlock = true;
                    }
                    if (Quote.Up == Quote.Down) {
                        Quote.Count++;
                    }
                    preferRE = false;
                }
            } else if (ch == Quote.Up) {
                Quote.Count++;
            } else if ((ch == '$' || ch == '@')
                       && isInterpolatingString(state, chNext)) {
                doInterpolateVariable(i, lengthDoc, state, ch, styler);
                retreatOneChar(i, chPrev, ch, chNext);
            }

        // Handle the beginning of a subroutine.
        } else if (state == SCE_PL_SUB) {
            
            // The end of subroutine state. Switch either back to normal mode or 
            // subroutine argument mode.
            if (ch == '(' || ch == '{' || ch == ';') {
                styler.ColourTo(i - 1, SCE_PL_IDENTIFIER);
                styler.ColourTo(i, SCE_PL_OPERATOR);
                if (ch == '(') {
                    state = SCE_PL_SUB_ARGS;
                    braceStartsBlock = true;
                    levelCurrent++;
                } else {
                    if (ch =='{') {
                        levelCurrent++;
                        braceStartsBlock = false;
                        p_BraceInfo->add(SCE_PL_OPERATOR);
                    } else {
                        braceStartsBlock = true;
                    }
                    state = SCE_PL_DEFAULT;
                }

            // Switch temporarily to COMMENTLINE state if a # is encountered.
            } else if (ch == '#') {
                styler.ColourTo(i - 1, SCE_PL_IDENTIFIER);
                previousState = state;
                state = SCE_PL_COMMENTLINE;
                braceStartsBlock = true;
            }
            
        // Handle the arguments of a subroutine.
        } else if (state == SCE_PL_SUB_ARGS) {
            if (ch == ')') {
                styler.ColourTo(i - 1, SCE_PL_DEFAULT);
                styler.ColourTo(i, SCE_PL_OPERATOR);
                state = SCE_PL_DEFAULT;
                if (levelCurrent > 0) {
                    levelCurrent--;
                }
                braceStartsBlock = true;
            }
        } else if (state == SCE_PL_FORMAT) {
            if (ch == '.' && isEOLChar(chPrev) && isEOLChar(chNext)) {
                styler.ColourTo(i, state);
                state = SCE_PL_DEFAULT;
            }
        }

        if (state == SCE_PL_ERROR) {
            break;
        }
        chPrev = ch;
    }
    if (state == SCE_PL_SUB) {
        state = SCE_PL_IDENTIFIER;
        braceStartsBlock = true;
    } else if (state == SCE_PL_SUB_ARGS) {
        state = SCE_PL_DEFAULT;
        braceStartsBlock = true;
    }
    styler.ColourTo(lengthDoc - 1, state);

    //Fill in the real level of the next line, keeping the current flags as they will be filled in later
    if (fold) {
        int flagsNext = styler.LevelAt(lineCurrent) & ~SC_FOLDLEVELNUMBERMASK;
        if (levelPrev < 0 || levelPrev >= 0x3ff) {
            levelPrev = 0;
        }
        styler.SetLevel(lineCurrent, levelPrev | flagsNext | SC_FOLDLEVELBASE);
    }
    styler.Flush();
    delete p_BraceInfo;
}

static void FoldPerlDoc(unsigned int startPos, int length, int, WordList *[],
                        Accessor &styler) {
    bool foldComment = styler.GetPropertyInt("fold.comment") != 0;
    bool foldCompact = styler.GetPropertyInt("fold.compact", 1) != 0;
    unsigned int endPos = startPos + length;
    int state;
    synchronizeDocStart(startPos, endPos, state, styler);
    
    int visibleChars = 0;
    int lineCurrent = styler.GetLine(startPos);

#if 0
    // Synchronize: if the previous line is a POD or here doc, move up one
    if (lineCurrent > 0) {
        int prevLineStartPos = styler.LineStart(lineCurrent - 1);
        if (safeStyleAt(prevLineStartPos, styler) == SCE_PL_POD) {
            startPos = prevLineStartPos;
            lineCurrent -= 1;
        }
    }
#endif
            
    int levelPrev = styler.LevelAt(lineCurrent) & SC_FOLDLEVELNUMBERMASK;
    int levelCurrent = levelPrev;
    int lengthDoc = styler.Length();
    char chNext = styler[startPos];
    int styleNext = safeStyleAt(startPos, styler);
    for (unsigned int i = startPos; i < endPos; i++) {
        char ch = chNext;
        chNext = styler.SafeGetCharAt(i + 1);
        int style = styleNext;
        styleNext = safeStyleAt(i + 1, styler);
        bool atEOL = (ch == '\r' && chNext != '\n') || (ch == '\n');
        if (foldComment && (style == SCE_PL_COMMENTLINE)) {
            if ((ch == '/') && (chNext == '/')) {
                char chNext2 = styler.SafeGetCharAt(i + 2);
                if (chNext2 == '{') {
                    levelCurrent++;
                } else if (levelCurrent > 0 && chNext2 == '}') {
                    levelCurrent--;
                }
            }
        } else if (style == SCE_PL_OPERATOR || style == SCE_PL_VARIABLE_INDEXER) {
            if (strchr("{[(", ch)) {
                levelCurrent++;
            } else if (levelCurrent > 0 && strchr(")]}", ch)) {
                levelCurrent--;
            }
        } else if (style == SCE_PL_POD && ch == '=') {
            // Check the previous line
            if (lineCurrent == 0
                || safeStyleAt(styler.LineStart(lineCurrent - 1), styler) != SCE_PL_POD) {
                levelCurrent++;
            } else if (levelCurrent > 0) {
                int nextLinePos = styler.LineStart(lineCurrent + 1);
                if (nextLinePos < lengthDoc
                    && safeStyleAt(nextLinePos, styler) != SCE_PL_POD) {
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
            if (lev != styler.LevelAt(lineCurrent)) {
                styler.SetLevel(lineCurrent, lev);
            }
            lineCurrent++;
            levelPrev = levelCurrent;
            visibleChars = 0;
        }
        if (!isspacechar(ch))
            visibleChars++;
    }
    // Fill in the real level of the next line, keeping the current flags as they will be filled in later
    int flagsNext = styler.LevelAt(lineCurrent) & ~SC_FOLDLEVELNUMBERMASK;
    styler.SetLevel(lineCurrent, levelPrev | flagsNext);
    styler.Flush();
}

static const char * const perlWordListDesc[] = {
    "Keywords",
    0
};

LexerModule lmPerl(SCLEX_PERL, ColourisePerlDoc, "perl", FoldPerlDoc, perlWordListDesc);
