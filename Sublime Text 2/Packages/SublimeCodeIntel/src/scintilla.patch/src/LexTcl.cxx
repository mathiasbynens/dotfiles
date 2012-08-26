/*  -*- tab-width: 8; indent-tabs-mode: t -*-
 * Scintilla source code edit control
 * @file LexTcl.cxx
 * Lexer for Tcl.
 */
// Copyright (c) 2001-2006 ActiveState Software Inc.
// The License.txt file describes the conditions under which this software may
// be distributed.

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

#if 1	// No Debug
#define colourString(end, state, styler) styler.ColourTo(end, state)
#else	// Debug color printfs
#define colourString(end, state, styler) \
	describeString(end, state, styler), styler.ColourTo(end, state)

static char *stateToString(int state) {
    switch (state) {
    case SCE_TCL_DEFAULT:	return "default";
    case SCE_TCL_NUMBER:	return "number";
    case SCE_TCL_WORD:		return "word";
    case SCE_TCL_COMMENT:	return "comment";
    case SCE_TCL_STRING:	return "string";
    case SCE_TCL_CHARACTER:	return "character";
    case SCE_TCL_LITERAL:	return "literal";
    case SCE_TCL_OPERATOR:	return "operator";
    case SCE_TCL_IDENTIFIER:	return "identifier";
    case SCE_TCL_EOL:		return "eol";
    case SCE_TCL_VARIABLE:	return "variable";
    case SCE_TCL_ARRAY:		return "array";
    default:			return "unknown";
    }
}

static void describeString(unsigned int end, int state, Accessor &styler) {
    char s[1024];
    unsigned int start = styler.GetStartSegment();
    unsigned int len = end - start + 1;

    if (!len) { return; }

    for (unsigned int i = 0; i < len && i < 100; i++) {
	s[i] = styler[start + i];
	s[i + 1] = '\0';
    }

    int start_line = styler.GetLine(start);
    int start_pos = start - styler.LineStart(start_line);
    int end_line = styler.GetLine(end);
    int end_pos = end - styler.LineStart(end_line);

    fprintf(stderr, "%s [%d] [(%d:%d)=>(%d:%d)]:\t'%s'\n",
	    stateToString(state), len,
	    start_line, start_pos,
	    end_line, end_pos,
	    s); fflush(stderr);
}
#endif

static inline bool isTclOperator(char ch) {
    return strchr("(){}[];!%^&*-=+|<>?/", ch) != NULL;
}

static void classifyWordTcl(unsigned int start,
			    unsigned int end,
			    WordList &keywords,
			    Accessor &styler) {
    char s[100];
    char chAttr;
    bool wordIsNumber = isdigit(styler[start]) || (styler[start] == '.');

    for (unsigned int i = 0; i < end - start + 1 && i < 40; i++) {
	s[i] = styler[start + i];
	s[i + 1] = '\0';
    }

    if (wordIsNumber) {
	chAttr = SCE_TCL_NUMBER;
    } else if (keywords.InList(s)) {
	chAttr = SCE_TCL_WORD;
    } else {
	// was default, but that should be reserved for white-space,
	// and we had to see an alpha-char to get here
	chAttr = SCE_TCL_IDENTIFIER;
    }

    colourString(end, chAttr, styler);
}

// KOMODO  see if a style is one of our IO styles
static inline bool IsIOStyle(int style) {
	return style == SCE_TCL_STDIN ||
		style == SCE_TCL_STDOUT ||
		style == SCE_TCL_STDERR;
}

// By default there are 5 style bits, plenty for Tcl
#define STYLE_MASK 31
#define actual_style(style) (style & STYLE_MASK)

// Null transitions when we see we've reached the end
// and need to relex the curr char.

static void redo_char(unsigned int &i, char &ch, char &chNext, int &state) {
    i--;
    chNext = ch;
    state = SCE_TCL_DEFAULT;
}

// Because of the quote-in-brace problem, sync at the first
// line that starts with a keyword

static void synchronizeDocStart(unsigned int& startPos,
				int &length,
				int &initStyle,
				Accessor &styler
				// Left for compatibility with other lexers
				// ,bool skipWhiteSpace=false
				) {

    styler.Flush();
    int style = actual_style(styler.StyleAt(startPos));
    switch (style) {
	case SCE_TCL_STDIN:
	case SCE_TCL_STDOUT:
	case SCE_TCL_STDERR:
	    // Don't do anything else with these.
	    return;
    }
    int start_line, start_line_pos, start_style;
    char ch;
    int minLinesUp = 3;
    for (start_line = styler.GetLine(startPos) - minLinesUp; start_line > 0; start_line--) {
	start_line_pos = styler.LineStart(start_line);
	start_style = actual_style(styler.StyleAt(start_line_pos));
	// We like lines that start with a keyword or comment
	if (start_style == SCE_TCL_WORD
	    || start_style == SCE_TCL_COMMENT) {
	    length += startPos - start_line_pos;
	    startPos = start_line_pos;
	    initStyle = start_style;
	    return;
	} else if (start_style == SCE_TCL_DEFAULT) {
	    // Look for ^\s+<keyword>
	    int i = start_line_pos;
	    int lim = styler.LineStart(start_line + 1); // has to exist
	    for (i = start_line_pos; i < lim; i++) {
		ch = styler[i];
		if (ch != ' ' && ch != '\t') {
		    break;
		} else {
		    int next_style = actual_style(styler.StyleAt(i + 1));
		    if (next_style == SCE_TCL_WORD) {
			length += startPos - start_line_pos;
			startPos = start_line_pos;
			initStyle = start_style;
			return;
		    } else if (next_style != SCE_TCL_DEFAULT) {
			break;
		    }
		}
	    }
	} else {
	    break;
	}
    }
    // Go back to the beginning.
    length += startPos;
    startPos = 0;
    initStyle = SCE_TCL_DEFAULT;
}

static inline bool isSafeAlnum(char ch) {
    return ((unsigned int) ch >= 128) || isalnum(ch) || ch == '_';
}

static inline void advanceOneChar(unsigned int& i, char&ch, char& chNext, char chNext2) {
    i++;
    ch = chNext;
    chNext = chNext2;
}

static void ColouriseTclDoc(unsigned int startPos,
			    int length,
			    int initStyle,
			    WordList *keywordlists[],
			    Accessor &styler) {
    WordList &keywords = *keywordlists[0];

    int inEscape	= 0;
    int inStrBraceCnt	= 0;
    int inCmtBraceCnt    = 0; 
    int lastQuoteSpot   = -1;
    // We're not always sure of the command start, but make an attempt
    bool cmdStart	= true;
    // Keep track of whether a variable is using braces or it is an array
    bool varBraced	= 0;
    bool isMultiLineString = false;

    //fprintf(stderr, "Start lexing at pos %d, len %d, style %d\n", startPos, length, initStyle);
    
    int state;
    unsigned int lengthDoc = startPos + length;
    if (IsIOStyle(initStyle)) {
	// KOMODO
	// Skip initial IO Style?
	while (startPos < lengthDoc
	       && IsIOStyle(actual_style(styler.StyleAt(startPos)))) {
	    startPos++;
	}
	state = SCE_P_DEFAULT;
    } else {
	synchronizeDocStart(startPos, length, initStyle, styler);
	lengthDoc = startPos + length;
	state = initStyle;
    }
    //fprintf(stderr, "After sync, start at pos %d, len %d, style %d\n", startPos, length, initStyle);
    char chPrev		= ' ';
    char chNext		= styler[startPos];

    // Folding info
    int visibleChars = 0;
    int lineCurrent = styler.GetLine(startPos);
    int levelPrev   = styler.LevelAt(lineCurrent) & SC_FOLDLEVELNUMBERMASK;
    int levelCurrent = levelPrev;
    bool foldCompact = styler.GetPropertyInt("fold.compact", 1) != 0;

    struct tag_lineInfo {
	int lineCurrent, levelCurrent, levelPrev, visibleChars;
    } heldLineInfo = {0, 0, 0, 0};

    styler.StartAt(startPos);
    styler.StartSegment(startPos);
    for (unsigned int i = startPos; i < lengthDoc; i++) {
	char ch = chNext;
	chNext = styler.SafeGetCharAt(i + 1);

	if (styler.IsLeadByte(ch)) {
	    chNext = styler.SafeGetCharAt(i + 2);
	    chPrev = ' ';
	    i += 1;
	    visibleChars++;
	    continue;
	}

	if (chPrev == '\\') {
	    // If the prev char was the escape char, flip the inEscape bit.
	    // This works because colorization always starts at the
	    // beginning of the line.
	    inEscape = !inEscape;
	} else if (inEscape) {
	    if (chPrev == '\r' && ch == '\n') {
		// Keep inEscape for one more round
	    } else {
		// Otherwise we aren't in an escape sequence
		inEscape = 0;
	    }
	}

	if ((ch == '\r' && chNext != '\n') || (ch == '\n')) {
	    // Trigger on CR only (Mac style) or either on LF from CR+LF
	    // (Dos/Win) or on LF alone (Unix) Avoid triggering two times on
	    // Dos/Win End of line
	    if (state == SCE_TCL_EOL) {
		colourString(i, state, styler);
		state = SCE_TCL_DEFAULT;
	    }
#if 0
	    fprintf(stderr, "end of line %d, levelPrev=0x%0x, levelCurrent=0x%0x\n",
		    lineCurrent, levelPrev, levelCurrent);
#endif
	    int lev = levelPrev;
	    if (lev < SC_FOLDLEVELBASE) {
		lev = SC_FOLDLEVELBASE;
	    }
	    if (visibleChars == 0 && foldCompact) {
		lev |= SC_FOLDLEVELWHITEFLAG;
	    }
	    if ((levelCurrent > levelPrev) && (visibleChars > 0)) {
		lev |= SC_FOLDLEVELHEADERFLAG;
	    }
	    if (lev != styler.LevelAt(lineCurrent)) {
		styler.SetLevel(lineCurrent, lev);
	    }
	    lineCurrent++;
	    levelPrev = levelCurrent;
	    visibleChars = 0;
	} else if (!isspacechar(ch)) {
	    visibleChars++;
	}

	if (state == SCE_TCL_DEFAULT) {
	    if ((ch == '#') && cmdStart) {
		colourString(i-1, state, styler);
		state = SCE_TCL_COMMENT;
		inCmtBraceCnt = 0; 
	    } else if ((ch == '\"') && !inEscape) {
		colourString(i-1, state, styler);
		isMultiLineString = false;
		state = SCE_TCL_STRING;
		inStrBraceCnt = 0;
		lastQuoteSpot = i;
		heldLineInfo.lineCurrent = lineCurrent;
		heldLineInfo.levelCurrent = levelCurrent;
		heldLineInfo.levelPrev = levelPrev;
		heldLineInfo.visibleChars = visibleChars;
	    } else if (ch == '$') {
		colourString(i-1, state, styler);
		if (chNext == '{') {
		    varBraced = true;
		    advanceOneChar(i, ch, chNext, styler.SafeGetCharAt(i + 1));
		    state = SCE_TCL_VARIABLE;
		} else if (iswordchar(chNext)) {
		    varBraced = false;
		    state = SCE_TCL_VARIABLE;
		} else {
		    colourString(i, SCE_TCL_OPERATOR, styler);
		    // Stay in default mode.
		}
	    } else if (isTclOperator(ch) || ch == ':') {
		if (ch == '-' && isascii(chNext) && isalpha(chNext)) {
		    colourString(i-1, state, styler);
		    // We could call it an identifier, but then we'd need another
		    // state.  classifyWordTcl will do the right thing.
		    state = SCE_TCL_WORD;
		} else {
		    // color up this one character as our operator
		    // multi-character operators will have their second
		    // character colored on the next pass
		    colourString(i-1, state, styler);
		    colourString(i, SCE_TCL_OPERATOR, styler);
		    if (!inEscape) {
			if (ch == '{' || ch == '[') {
			    ++levelCurrent;
			    cmdStart = true;
			} else if  (ch == ']' || ch == '}') {
			    if ((levelCurrent & SC_FOLDLEVELNUMBERMASK) > SC_FOLDLEVELBASE) {
				--levelCurrent;
			    }
			}
		    }
		}
	    } else if (iswordstart(ch)) {
		colourString(i-1, state, styler);
		if (iswordchar(chNext)) {
		    state = SCE_TCL_WORD;
		} else {
		    classifyWordTcl(styler.GetStartSegment(), i,
				    keywords, styler);
		    // Stay in the default state
		}
	    }
	} else if (state == SCE_TCL_WORD) {
	    if (!iswordchar(chNext)) {
		classifyWordTcl(styler.GetStartSegment(), i,
				keywords, styler);
		state = SCE_TCL_DEFAULT;
	    }
	} else {
	    if (state == SCE_TCL_VARIABLE) {
		/*
		 * A variable is ${?\w*}? and may be directly followed by
		 * another variable.  This should handle weird cases like:
		 * $a$b           ;# multiple vars
		 * ${a(def)(def)} ;# all one var
		 * ${abc}(def)    ;# (def) is not part of the var name now
		 * Previous to Komodo 4.2.1:
		 * $a(def)(ghi)   ;# (def) is array key, (ghi) is just chars
		 * ${a...}(def)(ghi)   ;# ( and ) are operators, def and ghi are chars
		 */
		if (!iswordchar(chNext)) {
		    bool varEndsHere = false;
		    if (varBraced) {
			if (chNext == '}') {
			    varBraced = false;
			    colourString(i + 1, state, styler);
			    state = SCE_TCL_DEFAULT;
			    advanceOneChar(i, ch, chNext, styler.SafeGetCharAt(i + 2));
			}
			// else continue building a var-braced string
		    } else if (chNext == ':' && styler.SafeGetCharAt(i + 2) == ':') {
			// continue, it's part of a simple name, but advance
			// so we don't stumble on the second colon
			advanceOneChar(i, ch, chNext, ':');
		    } else {
			varEndsHere = true;
		    }
		    if (varEndsHere) {
			colourString(i, state, styler);
			state = SCE_TCL_DEFAULT;
		    }
		}
	    } else if (state == SCE_TCL_OPERATOR) {
		/* not reached */
		if (ch == '}') {
		    colourString(i-1, state, styler);
		    state = SCE_TCL_DEFAULT;
		}
	    } else if (state == SCE_TCL_COMMENT) {
		/*
		 * The line continuation character also works for comments.
		 */
		if ((ch == '\r' || ch == '\n') && !inEscape) {
		    colourString(i-1, state, styler);
		    state = SCE_TCL_DEFAULT;
		} else if ((ch == '{') && !inEscape) {
		    inCmtBraceCnt++;
		} else if ((ch == '}') && !inEscape) {
		    inCmtBraceCnt--;
		    if (inCmtBraceCnt < 0) {
			if (levelCurrent > levelPrev) {
			    colourString(i - 1, state, styler);
			    redo_char(i, ch, chNext, state); // pass by ref
			}
		    }
		}
	    } else if (state == SCE_TCL_STRING) {
		if ((ch == '\r' || ch == '\n') && !inEscape) {
		    /*
		     * In the case of EOL in a string where the line
		     * continuations character isn't used, leave us in the
		     * SCE_TCL_STRING state, but color the newline.
		     */
		    // No I think this is wrong -- EP
		    // The lexer will color it as a string if it hits
		    // a quote or EOF, otherwise it'll hit the brace
		    // and whip back.
		    
		    //!! colourString(i-1, state, styler);
		    isMultiLineString = true;
		    //colourString(i, SCE_TCL_EOL, styler);
		    /*
		     * We are in a string, but in Tcl you can never really
		     * say when a command starts or not until eval.
		     */
		    cmdStart = true;
		} else if ((ch == '\"') && !inEscape) {
		    colourString(i, state, styler);
		    state = SCE_TCL_DEFAULT;
		} else if ((ch == '{') && !inEscape) {
		    inStrBraceCnt++;
		} else if ((ch == '}') && !inEscape) {
		    inStrBraceCnt--;
		    if (inStrBraceCnt < 0) {
			bool inside_brace;
			if (levelCurrent > levelPrev) {
			    inside_brace = true;
			} else {
			    int lev = styler.LevelAt(lineCurrent > 0 ? lineCurrent - 1 : 0);
			    //fprintf(stderr, "pos %d, line %d, raw level=0x%0x\n", i, lineCurrent, lev);
			    inside_brace = (((lev
					      & (SC_FOLDLEVELNUMBERMASK
						 & ~SC_FOLDLEVELBASE))) > 0);
			}
			if (inside_brace) {
			    /*
			     * We have hit a situation where brace counting
			     * inside the string is < 0, so this was likely
			     * a lone unescaped " character is a {}ed string.
			     * Color it as a literal, and then relex from
			     * the point after it.
			     */
			    state = SCE_TCL_DEFAULT;
			    if (lastQuoteSpot >= 0) {
				if (isMultiLineString) {
				    // recolor
				    styler.StartSegment(lastQuoteSpot);
				    isMultiLineString = false;
				}
				colourString(lastQuoteSpot, SCE_TCL_LITERAL, styler);
				chPrev = styler[i = lastQuoteSpot];
				chNext = styler[lastQuoteSpot + 1];
				lastQuoteSpot = -1;
				lineCurrent = heldLineInfo.lineCurrent;
				levelCurrent = heldLineInfo.levelCurrent;
				levelPrev = heldLineInfo.levelPrev;
				visibleChars = heldLineInfo.visibleChars;
				continue;
			    
			    } else {
				colourString(i-1, SCE_TCL_LITERAL, styler);
				colourString(i, SCE_TCL_OPERATOR, styler);
			    }
			}
		    }
		}
	    }
	}

	cmdStart = ((!inEscape && strchr("\r\n;[", ch)) // XXX '[' not needed?
		    || (cmdStart && strchr(" \t[{", ch)));

	chPrev = ch;
    }
    // Make sure to colorize last part of document
    // If it was SCE_TCL_WORD (the default if we were in a word), then
    // check to see whether it's a legitamite word.
    if (state == SCE_TCL_WORD) {
	classifyWordTcl(styler.GetStartSegment(), lengthDoc - 1,
			keywords, styler);
    } else {
	colourString(lengthDoc - 1, state, styler);
    }
    int flagsNext = styler.LevelAt(lineCurrent) & ~SC_FOLDLEVELNUMBERMASK;
    styler.SetLevel(lineCurrent, levelPrev | flagsNext);
    styler.Flush();
}

static const char * const tclWordListDesc[] = {
    "Tcl keywords",
    0
};

LexerModule lmTcl(SCLEX_TCL, ColouriseTclDoc, "tcl", NULL,
		  tclWordListDesc);
