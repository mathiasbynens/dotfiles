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

inline bool IsWhitespace (const unsigned char ch)
{
  return (ch == 0 || (ch < 128 && isspace(ch)));
}

#define isNameChar(ch) (((unsigned char)(ch) >= 128) \
			|| (isalnum(ch) || (ch) == '_' || (ch) == '-' \
                           || (ch) == '-' || (ch) == ':'))
			

// Don't make these STL maps in case we want to submit this to scintilla.

static char* XSLT_TagNamesWithXPathAttribute[] = {
  (char *) "xsl:apply-templates",
  (char *) "xsl:copy-of",
  (char *) "xsl:for-each",
  (char *) "xsl:if",
  (char *) "xsl:key",
  (char *) "xsl:number",
  (char *) "xsl:param",
  (char *) "xsl:sort",
  (char *) "xsl:template",
  (char *) "xsl:value-of",
  (char *) "xsl:variable",
  (char *) "xsl:when",
  (char *) "xsl:with-param",
  0
};
  
static char* XSLT_XPath_Attributes[] = {
  (char *) "count",
  (char *) "from",
  (char *) "match",
  (char *) "select",
  (char *) "test",
  (char *) "use",
  (char *) "value",
  0
};
  

//Precondition: terms in LookupList[] are in ascending order.

static bool FindMatch(char *LookupList[], char *term) {
  int i = 0;
  int res;
  while (LookupList[i]) {
    res = strcmp(term, LookupList[i]);
    if (!res)
      return true;
    else if (res < 0)
      return false;
    i++;
  }
  return false;
}

#define HoldUp() i -= 1

#define IncFoldCheck() if (fold && styler.SafeGetCharAt(i - 1) != '/') levelCurrent++

#define DecFoldCheck() if (fold) levelCurrent--


//Precondition:
// currPos points to the last char of the attribute

static bool InsideXPathElementWithXPathAttr(unsigned int currPos,
					    Accessor &styler)
{
  unsigned int attrStart = styler.GetStartSegment();
  unsigned int elementEnd;

  // First what kind of element we're in
  for (elementEnd = attrStart - 2;
       elementEnd > 0;
       elementEnd--) {
    switch (styler.StyleAt(elementEnd)) {
    case SCE_XPATH_TAG_NAME:
      {
	 char nameBuf[10];
	 char *s = nameBuf;
	 if (currPos >= attrStart
	     && currPos - attrStart < (unsigned int)(sizeof(nameBuf) / sizeof(nameBuf[0]))) {
	    unsigned int j;
	    for (j = attrStart; j <= currPos; j++) {
	       *s++ = styler[j];
	    }
	    *s = 0;
	    return FindMatch (XSLT_XPath_Attributes, nameBuf);
	 } else {
	    return false;
	 }
      }
      /*NOTREACHED*/
      break;

      case SCE_XML_START_TAG_NAME:
	// We're in a standard element, so bail out.
	return false;
      }
  }
  return false;
}


static bool CheckIfNameIsXPathElement(int i,
				      Accessor &styler)
{
  //todo: if this name is an XSLT name, color it so.
  // i points to one past the end of the name

  char nameBuf[30];
  char *s = nameBuf;
	 
  int startingPoint = (int) styler.GetStartSegment();
	 
  if (startingPoint < i // sanity check
      && i - startingPoint < (int)(sizeof(nameBuf) / sizeof(nameBuf[0]))) {
    int j;
    for (j = startingPoint; j < i; j++) {
      *s++ = styler[j];
    }
    *s = 0;
    if (FindMatch (XSLT_TagNamesWithXPathAttribute, nameBuf)) {
      return true;
    }
  }
  return false;
}
				      

inline bool LookingAtNewline(const char ch,
                             int i,
                             Accessor &styler)
{
    return (ch == '\n' || (ch == '\r' && styler.SafeGetCharAt(i + 1) != '\n'));
}


inline bool LookingAtNewline(const char ch,
                             const char chNext)
{
    return (ch == '\n' || (ch == '\r' && chNext != '\n'));
}


static void ColouriseXSLTDoc(unsigned int startPos,
                             int length,
                             int initStyle,
                             WordList *[],
                             Accessor &styler)
{
    int state = initStyle;
    unsigned int lengthDoc = startPos + length;
  
    // Variables to allow folding.
    bool fold = styler.GetPropertyInt("fold") != 0;
    int lineCurrent = styler.GetLine(startPos);
    int levelPrev = styler.LevelAt(lineCurrent) & SC_FOLDLEVELNUMBERMASK;
    int levelCurrent = levelPrev;
    bool hasVisibleChars = false;

    styler.StartAt(startPos,63);
    styler.StartSegment(startPos);

    char ch;
    // Prime this.
    ch = styler.SafeGetCharAt(startPos);
  
    for (unsigned int i = startPos; i < lengthDoc; i++) {
        // Update the char registers on each iteration in case i was
        // messed with.
     
        ch = styler[i];

        // Rule out common cases first
        if (ch == '<') {
            switch (state) {
             case SCE_XML_START_TAG_OPEN:
             case SCE_XML_START_TAG_NAME:
             case SCE_XML_START_TAG_CLOSE:
             case SCE_XML_START_TAG_EMPTY_CLOSE:
             case SCE_XML_START_TAG_WHITE_SPACE:
             case SCE_XML_START_TAG_ATTR_NAME:
             case SCE_XML_START_TAG_ATTR_EQUALS:
             case SCE_XML_START_TAG_ATTR_QUOT_CONTENT:
             case SCE_XML_START_TAG_ATTR_APOS_CONTENT:
             case SCE_XML_START_TAG_ATTR_QUOT_CLOSE:
             case SCE_XML_START_TAG_ATTR_UNQUOTED:
             case SCE_XML_END_TAG_NAME:
             case SCE_XML_END_TAG_WHITE_SPACE:
             case SCE_XML_ENTITY_REF:
             case SCE_XML_CHAR_REF:
             case SCE_XML_DATA_CHARS:
             case SCE_XML_DATA_NEWLINE:
             case SCE_XML_DECLARATION_TYPE:
             case SCE_XML_DECLN_NAME:
             case SCE_XML_DECLN_WHITE_SPACE:
             case SCE_XML_DECLN_CLOSE:
             case SCE_XML_DECLN_DATA_CHARS:
	  
                 styler.ColourTo(i - 1, state);
                 state = SCE_XML_START_TAG_OPEN;
                 continue;
            }
        } else if (ch == '&') {
            switch (state) {
             case SCE_XML_START_TAG_OPEN:
             case SCE_XML_START_TAG_NAME:
             case SCE_XML_START_TAG_CLOSE:
             case SCE_XML_START_TAG_EMPTY_CLOSE:
             case SCE_XML_START_TAG_WHITE_SPACE:
             case SCE_XML_START_TAG_ATTR_NAME:
             case SCE_XML_START_TAG_ATTR_EQUALS:
             case SCE_XML_START_TAG_ATTR_QUOT_CLOSE:
             case SCE_XML_END_TAG_NAME:
             case SCE_XML_END_TAG_WHITE_SPACE:
             case SCE_XML_ENTITY_REF:
             case SCE_XML_CHAR_REF:
             case SCE_XML_DATA_CHARS:
             case SCE_XML_DATA_NEWLINE:
                 styler.ColourTo(i - 1, state);
                 if (styler.SafeGetCharAt(i + 1) == '#') {
                     state = SCE_XML_CHAR_REF;
                     i += 1;
                 } else {
                     state = SCE_XML_ENTITY_REF;
                 }
                 continue;
            }
        }

        if (fold) {
            if (LookingAtNewline(ch, i, styler)) {
                // Apply folding at the end of the line (if required).
                int lev = levelPrev;
                if (!hasVisibleChars) {
                    lev |= SC_FOLDLEVELWHITEFLAG;
                }
                if (levelCurrent > levelPrev) {
                    lev |= SC_FOLDLEVELHEADERFLAG;
                }
                styler.SetLevel(lineCurrent++, lev);
                levelPrev = (levelCurrent > 0) ? levelCurrent : 0; 
                hasVisibleChars = false;
            } else if (!hasVisibleChars) {
                if (!IsWhitespace(ch)) {
                    hasVisibleChars = true;
                }
            }
        }

        // How to speed this up:

        // 1. Remove as many instances of HoldUp() as possible.
     
        // These routines should color both the previous and current
        // state, and switch to the appropriate state.

        // 

        switch (state) {
         case SCE_XML_DEFAULT:
             // epsilon transition
             if (LookingAtNewline(ch, i, styler))
                 state = SCE_XML_DATA_NEWLINE;
             else {
                 HoldUp();
                 state = SCE_XML_DATA_CHARS;
             }
             break;

         case SCE_XML_START_TAG_OPEN:
             if (isNameChar (ch)) {
                 styler.ColourTo(i - 1, state);
                 state = SCE_XML_START_TAG_NAME;
             } else if (ch == '/') {
                 state = SCE_XML_END_TAG_OPEN;
             } else {
                 char chNext = styler.SafeGetCharAt(i + 1);
                 char chNext2 = styler.SafeGetCharAt(i + 2);
                 if (ch == '!') {
                     if (chNext == '-') {
                         if (chNext2 == '-') {
                             styler.ColourTo(i + 2, SCE_XML_COMMENT_OPEN);
                             i += 2;
                             state = SCE_XML_COMMENT_CONTENT;
                         } else {
                             styler.ColourTo(i + 1, SCE_XML_DATA_CHARS);
                             i += 1;
                             state = SCE_XML_DATA_CHARS;
                         }
                     } else if (chNext == '[') {
                         if (chNext2 == 'C'
                             && styler.SafeGetCharAt(i + 3) == 'D'
                             && styler.SafeGetCharAt(i + 4) == 'A'
                             && styler.SafeGetCharAt(i + 5) == 'T'
                             && styler.SafeGetCharAt(i + 6) == 'A'
                             && styler.SafeGetCharAt(i + 7) == '[') {
                             styler.ColourTo(i + 7, SCE_XML_CDATA_SECT_OPEN);
                             i += 7;
                             state = SCE_XML_CDATA_SECT_CONTENT;
                         } else {
                             styler.ColourTo(i, SCE_XML_DATA_CHARS);
                             i += 1;
                             state = SCE_XML_DATA_CHARS;
                         }
                     } else if (isNameChar (chNext)) {
                         styler.ColourTo(i, SCE_XML_DECLARATION_OPEN);
                         state = SCE_XML_DECLARATION_TYPE;
                     } else {
                         state = SCE_XML_DATA_CHARS;
                     }
                 } else if (ch == '?') {
                     if (chNext == 'x'
                         && chNext2 == 'm'
                         && styler.SafeGetCharAt(i + 3) == 'l'
                         && IsWhitespace(styler.SafeGetCharAt(i + 4))) {
                         styler.ColourTo(i + 3, SCE_XML_XML_DECL_OPEN);
                         i += 3;
                         state = SCE_XML_XML_DECL_CONTENT;
                     } else {
                         styler.ColourTo(i, SCE_XML_PI_OPEN);
                         state = SCE_XML_PI_CONTENT;
                     }
                 } else if (LookingAtNewline(ch, chNext)) {
                     state = SCE_XML_DATA_NEWLINE;
                 } else {
                     state = SCE_XML_DATA_CHARS;
                     HoldUp();
                 }
             }
             break;

         case SCE_XML_START_TAG_NAME:
             if (isNameChar (ch)) {
                 // do nothing
             } else {
	  
	 
                 if (CheckIfNameIsXPathElement(i, styler)) {
                     styler.ColourTo(i - 1, SCE_XPATH_TAG_NAME);
                 } else {
                     styler.ColourTo(i - 1, state);
                 }
	  
                 if (IsWhitespace(ch)) {
                     state = SCE_XML_START_TAG_WHITE_SPACE;
                 } else if (ch == '/') {
                     state = SCE_XML_START_TAG_EMPTY_CLOSE;
                 } else if (ch == '>') {
                     IncFoldCheck();
                     state = SCE_XML_START_TAG_CLOSE;
                 } else if (ch == '\'') {
                     styler.ColourTo(i, SCE_XML_START_TAG_ATTR_APOS_OPEN);
                     state = SCE_XML_START_TAG_ATTR_APOS_CONTENT;
                 } else if (ch == '"') {
                     styler.ColourTo(i, SCE_XML_START_TAG_ATTR_QUOT_OPEN);
                     state = SCE_XML_START_TAG_ATTR_QUOT_CONTENT;
                 } else {
                     state = SCE_XML_DATA_CHARS;
                 }
             }
             break;

         case SCE_XML_START_TAG_CLOSE:
             styler.ColourTo(i - 1, state);
             if (LookingAtNewline(ch, i, styler))
                 state = SCE_XML_DATA_NEWLINE;
             else {
                 state = SCE_XML_DATA_CHARS;
                 HoldUp();
             }
             break;

         case SCE_XML_START_TAG_EMPTY_CLOSE:
             if (ch == '>') {
                 styler.ColourTo(i, state);
             } else {
                 styler.ColourTo(i - 1, state);
                 if (LookingAtNewline(ch, i, styler)) {
                     state = SCE_XML_DATA_NEWLINE;
                 } else {
                     HoldUp();
                     state = SCE_XML_DATA_CHARS;
                 }
             }
             break;

         case SCE_XML_START_TAG_WHITE_SPACE:
             if (IsWhitespace(ch)) {
                 // stay
             } else {
                 styler.ColourTo(i - 1, state);
                 if (isNameChar (ch)) {
                     state = SCE_XML_START_TAG_ATTR_NAME;
                 } else if (ch == '/') {
                     state = SCE_XML_START_TAG_EMPTY_CLOSE;
                 } else if (ch == '>') {
                     IncFoldCheck();
                     state = SCE_XML_START_TAG_CLOSE;
                 } else if (ch == '\'') {
                     styler.ColourTo(i, SCE_XML_START_TAG_ATTR_APOS_OPEN);
                     state = SCE_XML_START_TAG_ATTR_APOS_CONTENT;
                 } else if (ch == '"') {
                     styler.ColourTo(i, SCE_XML_START_TAG_ATTR_QUOT_OPEN);
                     state = SCE_XML_START_TAG_ATTR_QUOT_CONTENT;
                 } else {
                     state = SCE_XML_DATA_CHARS;
                 }
             }
             break;

         case SCE_XML_START_TAG_ATTR_NAME:
             if (isNameChar (ch)) {
                 // stay
             } else {
                 bool IsXPathAttr = InsideXPathElementWithXPathAttr(i - 1, styler);
                 state = IsXPathAttr ? SCE_XPATH_ATTR_NAME: SCE_XML_START_TAG_ATTR_NAME;
                 styler.ColourTo(i - 1, state);
                 if (IsWhitespace(ch) || ch == '=') {
                     state = SCE_XML_START_TAG_ATTR_EQUALS;
                 } else if (ch == '/') {
                     state = SCE_XML_START_TAG_EMPTY_CLOSE;
                 } else if (ch == '>') {
                     IncFoldCheck();
                     state = SCE_XML_START_TAG_CLOSE;
                 } else if (ch == '\'') {
                     styler.ColourTo(i, SCE_XML_START_TAG_ATTR_APOS_OPEN);
                     state = SCE_XML_START_TAG_ATTR_APOS_CONTENT;
                 } else if (ch == '"') {
                     styler.ColourTo(i, SCE_XML_START_TAG_ATTR_QUOT_OPEN);
                     state = SCE_XML_START_TAG_ATTR_QUOT_CONTENT;
                 } else {
                     state = SCE_XML_DATA_CHARS;
                 }
             }
             break;

         case SCE_XML_START_TAG_ATTR_EQUALS:
             if (IsWhitespace(ch) || ch == '=') {
                 // stay
             } else {
                 styler.ColourTo(i - 1, state);
                 if (ch == '\'' || ch == '"') {
                     int j;
                     bool useXPathAttr = false;
                     for (j = i - 2; j > 0; j--) {
                         switch (styler.StyleAt(j)) {
                          case SCE_XPATH_ATTR_NAME:
                              useXPathAttr = true;
                              j = 0;
                              break;
		 
                          case SCE_XML_START_TAG_ATTR_NAME:
                              useXPathAttr = false;
                              j = 0;
                              break;
                         }
                     }
                     if (useXPathAttr) {
                         styler.ColourTo(i, SCE_XPATH_OPEN);
                         if (ch == '\'') {
                             state = SCE_XPATH_CONTENT_APOS;
                         } else {
                             state = SCE_XPATH_CONTENT_QUOT;
                         }
                     } else {
                         if (ch == '\'') {
                             styler.ColourTo(i, SCE_XML_START_TAG_ATTR_APOS_OPEN);
                             state = SCE_XML_START_TAG_ATTR_APOS_CONTENT;
                         } else {
                             styler.ColourTo(i, SCE_XML_START_TAG_ATTR_QUOT_OPEN);
                             state = SCE_XML_START_TAG_ATTR_QUOT_CONTENT;
                         }
                     }
                 } else if (ch == '/') {
                     state = SCE_XML_START_TAG_EMPTY_CLOSE;
                 } else if (ch == '>') {
                     IncFoldCheck();
                     state = SCE_XML_START_TAG_CLOSE;
                 } else {
                     // Allow old-style unquoted attr values
                     state = SCE_XML_START_TAG_ATTR_UNQUOTED;
                 }
             }
             break;

         case SCE_XML_START_TAG_ATTR_QUOT_OPEN:
             styler.ColourTo(i, state);
             state = SCE_XML_START_TAG_ATTR_QUOT_CONTENT;
             break;

         case SCE_XML_START_TAG_ATTR_QUOT_CONTENT:
             if (ch == '"') {
                 styler.ColourTo(i - 1, state);
                 state = SCE_XML_START_TAG_ATTR_QUOT_CLOSE;
             }
             break;

         case SCE_XML_START_TAG_ATTR_QUOT_CLOSE:
         case SCE_XML_START_TAG_ATTR_APOS_CLOSE:
             styler.ColourTo(i - 1, state);
             if (IsWhitespace(ch)) {
                 state = SCE_XML_START_TAG_WHITE_SPACE;
             } else if (ch == '/') {
                 state = SCE_XML_START_TAG_EMPTY_CLOSE;
             } else if (ch == '>') {
                 IncFoldCheck();
                 state = SCE_XML_START_TAG_CLOSE;
             } else {
                 state = SCE_XML_START_TAG_WHITE_SPACE;
                 if (!LookingAtNewline(ch, i, styler))
                     HoldUp();
             }
             break;

         case SCE_XML_START_TAG_ATTR_APOS_OPEN:
             styler.ColourTo(i - 1, state);
             state = SCE_XML_START_TAG_ATTR_APOS_CONTENT;
             break;

         case SCE_XML_START_TAG_ATTR_APOS_CONTENT:
             if (ch == '\'') {
                 styler.ColourTo(i - 1, state);
                 state = SCE_XML_START_TAG_ATTR_APOS_CLOSE;
             }
             break;

         case SCE_XML_START_TAG_ATTR_UNQUOTED:
             if (ch == '>') {
                 styler.ColourTo(i - 1, state);
                 IncFoldCheck();
                 state = SCE_XML_START_TAG_CLOSE;
             } else if (IsWhitespace(ch)) {
                 styler.ColourTo(i - 1, state);
                 state = SCE_XML_START_TAG_WHITE_SPACE;
             } else {
                 // stay
             }
             break;

         case SCE_XML_END_TAG_OPEN:
             styler.ColourTo(i - 1, state);
             state = SCE_XML_END_TAG_NAME;
             break;

         case SCE_XML_END_TAG_NAME:
             if (isNameChar (ch)) {
                 // stay
             } else {
                 if (CheckIfNameIsXPathElement(i, styler)) {
                     styler.ColourTo(i - 1, SCE_XPATH_TAG_NAME);
                 } else {
                     styler.ColourTo(i - 1, state);
                 }
                 if (IsWhitespace(ch)) {
                     state = SCE_XML_END_TAG_WHITE_SPACE;
                 } else {
                     state = SCE_XML_END_TAG_CLOSE;
                     DecFoldCheck();
                 }
             }
             break;

         case SCE_XML_END_TAG_WHITE_SPACE:
             if (IsWhitespace(ch)) {
                 // stay
             } else {
                 styler.ColourTo(i - 1, state);
                 if (ch == '>') {
                     state = SCE_XML_END_TAG_CLOSE;
                     DecFoldCheck();
                 } else {
                     state = SCE_XML_DATA_CHARS;
                 }
             }
             break;
	
         case SCE_XML_END_TAG_CLOSE:
             styler.ColourTo(i - 1, state);
             if (LookingAtNewline(ch, i, styler))
                 state = SCE_XML_DATA_NEWLINE;
             else {
                 HoldUp();
                 state = SCE_XML_DATA_CHARS;
             }
             break;

         case SCE_XML_START_TAG_ATTR_NUMBER:
             // Not used
             if (LookingAtNewline(ch, i, styler))
                 state = SCE_XML_DATA_NEWLINE;
             else {
                 HoldUp();
                 state = SCE_XML_DATA_CHARS;
             }
             break;

         case SCE_XML_ENTITY_REF:
             if (isNameChar (ch)) {
                 // stay
             } else {
                 if (ch == ';') {
                     styler.ColourTo(i, state);
                 } else {
                     styler.ColourTo(i - 1, state);
                     if (LookingAtNewline(ch, i, styler))
                         state = SCE_XML_DATA_NEWLINE;
                     else {
                         HoldUp();
                         state = SCE_XML_DATA_CHARS;
                     }
                 }
                 state = SCE_XML_DATA_CHARS;
             }
             break;

         case SCE_XML_CHAR_REF:
             if ((unsigned int) ch < 128 && isalnum (ch)) {
                 // stay
             } else {
                 if (ch == ';') {
                     styler.ColourTo(i, state);
                 } else {
                     styler.ColourTo(i - 1, state);
                     if (LookingAtNewline(ch, i, styler))
                         state = SCE_XML_DATA_NEWLINE;
                     else {
                         HoldUp();
                         state = SCE_XML_DATA_CHARS;
                     }
                 }
                 state = SCE_XML_DATA_CHARS;
             }
             break;

         case SCE_XML_DATA_NEWLINE:
             if (ch == '\r' || ch == '\n') {
                 // stay
             } else {
                 // We don't have a < or &, so don't hold up.
                 styler.ColourTo(i - 1, state);
                 state = SCE_XML_DATA_CHARS;
             }
             break;

         case SCE_XML_DATA_CHARS:
             if (ch == '\r' || ch == '\n') {
                 styler.ColourTo(i - 1, state);
                 state = SCE_XML_DATA_NEWLINE;
             }
             // otherwise stay.
             break;

         case SCE_XML_CDATA_SECT_OPEN:
             styler.ColourTo(i - 1, state);
             if (ch == ']') {
                 HoldUp();
             }
             state = SCE_XML_CDATA_SECT_CONTENT;
             break;

         case SCE_XML_CDATA_SECT_CONTENT:
             if (ch == ']'
                 && styler.SafeGetCharAt(i + 1) == ']'
                 && styler.SafeGetCharAt(i + 2) == '>') {
                 styler.ColourTo(i - 1, state);
                 i += 2;
                 styler.ColourTo(i, SCE_XML_CDATA_SECT_CLOSE);
                 state = SCE_XML_DATA_CHARS;
             }
             break;

         case SCE_XML_CDATA_SECT_CLOSE:
             // Shouldn't happen
             styler.ColourTo(i - 1, state);
             state = SCE_XML_DATA_CHARS;
             break;

         case SCE_XML_COMMENT_OPEN:
             // Shouldn't happen
             state = SCE_XML_DATA_CHARS;
             break;

         case SCE_XML_COMMENT_CONTENT:
             if (ch == '-'
                 && styler.SafeGetCharAt(i + 1) == '-'
                 && styler.SafeGetCharAt(i + 2) == '>') {
                 styler.ColourTo(i - 1, state);
                 i += 2;
                 styler.ColourTo(i, SCE_XML_COMMENT_CLOSE);
                 state = SCE_XML_DATA_CHARS;
             } 
             break;

         case SCE_XML_COMMENT_CLOSE:
             // Shouldn't happen
             state = SCE_XML_DATA_CHARS;
             break;

         case SCE_XML_PI_OPEN:
             // Shouldn't happen
             state = SCE_XML_DATA_CHARS;
             break;

         case SCE_XML_PI_CONTENT:
             if (ch == '?' && styler.SafeGetCharAt(i + 1) == '>') {
                 styler.ColourTo(i - 1, state);
                 i += 1;
                 styler.ColourTo(i, SCE_XML_PI_CLOSE);
                 state = SCE_XML_DATA_CHARS;
             }
             break;

         case SCE_XML_PI_CLOSE:
             // Shouldn't happen
             break;

         case SCE_XML_XML_DECL_OPEN:
             // Shouldn't happen
             break;

         case SCE_XML_XML_DECL_CONTENT:
             if (ch == '?' && styler.SafeGetCharAt(i + 1) == '>') {
                 styler.ColourTo(i - 1, state);
                 i += 1;
                 styler.ColourTo(i, SCE_XML_XML_DECL_CLOSE);
                 state = SCE_XML_DATA_CHARS;
             }
             break;

         case SCE_XML_XML_DECL_CLOSE:
             // Shouldn't happen
             state = SCE_XML_DATA_CHARS;
             break;

         case SCE_XML_BOM:
             // Shouldn't happen
             state = SCE_XML_DATA_CHARS;
             break;

         case SCE_XPATH_TAG_NAME:
             // Shouldn't happen
             state = SCE_XML_DATA_CHARS;
             break;

         case SCE_XPATH_ATTR_NAME:
             // Shouldn't happen
             state = SCE_XML_DATA_CHARS;
             break;

         case SCE_XPATH_OPEN:
             // Shouldn't happen
             state = SCE_XML_DATA_CHARS;
             break;

         case SCE_XPATH_CONTENT_QUOT:
             if (ch == '"') {
                 styler.ColourTo(i - 1, state);
                 state = SCE_XPATH_CLOSE;
             }
             break;

         case SCE_XPATH_CONTENT_APOS:
             if (ch == '\'') {
                 styler.ColourTo(i - 1, state);
                 state = SCE_XPATH_CLOSE;
             }
             break;

         case SCE_XPATH_CLOSE:
             styler.ColourTo(i - 1, state);
             if (!LookingAtNewline(ch, i, styler))
                 HoldUp();
             state = SCE_XML_START_TAG_WHITE_SPACE;
             break;

         case SCE_XML_DECLARATION_TYPE:
         case SCE_XML_DECLN_NAME:
             if (isNameChar (ch)) {
                 // stay
             } else {
                 styler.ColourTo(i - 1, state);
                 if (IsWhitespace(ch) || ch == '%') {
                     state = SCE_XML_DECLN_WHITE_SPACE;
                 } else if (ch == '>') {
                     state = SCE_XML_DECLN_CLOSE;
                 } else if (ch == '"') {
                     state = SCE_XML_DECLN_QUOT_CONTENT;
                 } else if (ch == '\'') {
                     state = SCE_XML_DECLN_APOS_CONTENT;
                 } else if (ch == ']') {
                     if (styler.SafeGetCharAt(i + 1) == '>') {
                         i++;
                         styler.ColourTo(i, SCE_XML_DECLN_DATA_CHARS);
                         state = SCE_XML_DATA_CHARS;
                     }
                 } else {
                     if (!LookingAtNewline(ch, i, styler))
                         HoldUp();
                     state = SCE_XML_DECLN_DATA_CHARS;
                 }
             }
             break;

         case SCE_XML_DECLN_WHITE_SPACE:
             if (IsWhitespace(ch) || ch == '%') {
                 // stay
             } else {
                 styler.ColourTo(i - 1, state);
                 if (isNameChar (ch)) {
                     state = SCE_XML_DECLN_NAME;
                 } else if (ch == '>') {
                     state = SCE_XML_DECLN_CLOSE;
                 } else if (ch == '"') {
                     state = SCE_XML_DECLN_QUOT_CONTENT;
                 } else if (ch == '\'') {
                     state = SCE_XML_DECLN_APOS_CONTENT;
                 } else if (ch == ']') {
                     if (styler.SafeGetCharAt(i + 1) == '>') {
                         i++;
                         styler.ColourTo(i, SCE_XML_DECLN_DATA_CHARS);
                         state = SCE_XML_DATA_CHARS;
                     }
                 } else {
                     if (!LookingAtNewline(ch, i, styler))
                         HoldUp();
                     state = SCE_XML_DECLN_DATA_CHARS;
                 }
             }
             break;

         case SCE_XML_DECLN_QUOT_CONTENT:
             if (ch == '"') {
                 styler.ColourTo(i, state);
                 state = SCE_XML_DECLN_WHITE_SPACE;
             }
             break;

         case SCE_XML_DECLN_APOS_CONTENT:
             if (ch == '\'') {
                 styler.ColourTo(i, state);
                 state = SCE_XML_DECLN_WHITE_SPACE;
             }
             break;

         case SCE_XML_DECLN_CLOSE:
             styler.ColourTo(i - 1, state);
             if (!LookingAtNewline(ch, i, styler))
                 HoldUp();
             state = SCE_XML_DECLN_DATA_CHARS;
             break;

         case SCE_XML_DECLN_DATA_CHARS:
             if (isNameChar (ch)) {
                 styler.ColourTo(i - 1, state);
                 state = SCE_XML_DECLN_NAME;
             } else if (ch == '>') {
                 styler.ColourTo(i - 1, state);
                 state = SCE_XML_DECLN_CLOSE;
             } else if (ch == '"') {
                 styler.ColourTo(i - 1, state);
                 state = SCE_XML_DECLN_QUOT_CONTENT;
             } else if (ch == '\'') {
                 styler.ColourTo(i - 1, state);
                 state = SCE_XML_DECLN_APOS_CONTENT;
             } else if (IsWhitespace(ch) || ch == '%') {
                 styler.ColourTo(i - 1, state);
                 state = SCE_XML_DECLN_WHITE_SPACE;
             } else if (ch == ']') {
                 if (styler.SafeGetCharAt(i + 1) == '>') {
                     i++;
                     styler.ColourTo(i, state);
                     state = SCE_XML_DATA_CHARS;
                 }
             }
             break;

         default:
             // Shouldn't see this.
             HoldUp();
             state = SCE_XML_DATA_CHARS;
        }
    }
    styler.ColourTo(lengthDoc - 1, state);
    if (fold) {
        int flagsNext = styler.LevelAt(lineCurrent) & ~SC_FOLDLEVELNUMBERMASK;
        styler.SetLevel(lineCurrent, levelPrev | flagsNext);
    }
}

  //LexerModule lmXSLT(SCLEX_XSLT, ColouriseXSLTDoc, "XSLT", (LexerFunction) 0);
LexerModule lmXSLT(SCLEX_XSLT, ColouriseXSLTDoc, "xslt");
