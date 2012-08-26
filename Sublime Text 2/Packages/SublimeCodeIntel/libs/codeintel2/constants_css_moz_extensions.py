"""
Mozilla CSS extensions.
"""

import textwrap

# Auto generated from:
#  'src/codeintel/support/gencix/css/gen_moz_css_properties.py'

### START: Auto generated

CSS_MOZ_DATA = {

    '-moz-appearance':
{       'description': "The -moz-appearance CSS property is used in Gecko (Firefox) to display an element using a platform-native styling based on the operating system's theme.",
        'values': {       '-moz-mac-unified-toolbar': 'New in Firefox 3.5. Mac OS X only. This causes the toolbar and title bar to render using the unified toolbar style common to Mac OS X 10.4 and later applications.',
                          '-moz-win-browsertabbar-toolbox': 'New in Firefox 3. Windows Vista and later. This toolbox style is meant to be used for the tab bar in a browser.',
                          '-moz-win-communications-toolbox': 'New in Firefox 3. Windows Vista and later. This toolbox style is meant to be used in communications and productivity applications. Corresponding foreground color is -moz-win-communicationstext .',
                          '-moz-win-glass': 'New in Firefox 3.5. Windows Vista and later. This style applies the Aero Glass effect to the element.',
                          '-moz-win-media-toolbox': 'New in Firefox 3. Windows Vista and later. This toolbox style is meant to be used in applications that manage media objects. Corresponding foreground color is -moz-win-mediatext .',
                          'button': 'The element is drawn like a button.',
                          'checkbox': 'The element is drawn like a checkbox, including only the actual "checkbox" portion.',
                          'checkbox-container': 'The element is drawn like a container for a checkbox, which may include a prelighting background effect under certain platforms. Normally a would contain a label and a checkbox.',
                          'checkbox-small': '',
                          'dialog': 'The element is styled like a dialog box, which includes background color and other properties.',
                          'listbox': '',
                          'menuitem': 'The element is styled as menu item, item is highlighted when hovered.',
                          'menulist': '',
                          'menulist-button': 'The element is styled as a button that would indicate a menulist can be opened.',
                          'menulist-textfield': 'The element is styled as the text field for a menulist.',
                          'menupopup': '',
                          'none': 'No special styling is applied. (Default)',
                          'progressbar': 'The element is styled like a progress bar.',
                          'radio': 'The element is drawn like a radio button, including only the actual "radio button" portion.',
                          'radio-container': 'The element is drawn like a container for a radio button, which may include a prelighting background effect under certain platforms. Normally would contain a label and a radio button.',
                          'radio-small': '',
                          'resizer': '',
                          'scrollbar': '',
                          'scrollbarbutton-down': '',
                          'scrollbarbutton-left': '',
                          'scrollbarbutton-right': '',
                          'scrollbarbutton-up': '',
                          'scrollbartrack-horizontal': '',
                          'scrollbartrack-vertical': '',
                          'separator': '',
                          'statusbar': '',
                          'tab': '',
                          'tab-left-edge': 'Obsolete. ',
                          'tabpanels': '',
                          'textfield': '',
                          'toolbar': '',
                          'toolbarbutton': '',
                          'toolbox': '',
                          'tooltip': '',
                          'treeheadercell': '',
                          'treeheadersortarrow': '',
                          'treeitem': '',
                          'treetwisty': '',
                          'treetwistyopen': '',
                          'treeview': '',
                          'window': ''},
        'version': 'Firefox 1.0 (1.0)'},

    '-moz-background-clip':
{       'description': "The background-clip CSS property specifies whether an element's background, either the color or image, extends underneath its border. -moz-background-clip is supported up to Gecko version 1.9.2 (Firefox 3.6). Warning: To support both, older and newer versions of Gecko (Firefox), you have to add both properties in the stylesheet. See examples.",
        'values': {       'border': '(Firefox 1.0-3.6). The background extends to the outside edge of the border (but underneath the border in z-ordering). Default value, but see Browser compatibility section below for special case Internet Explorer 7.',
                          'border-box': '(Requires Gecko 1.9.3). The background extends to the outside edge of the border (but underneath the border in z-ordering). Default value, but see Browser compatibility section below for special case Internet Explorer 7.',
                          'content-box': 'Requires Gecko 1.9.3. The background is painted within (clipped to) the content box.',
                          'padding': '(Firefox 1.0-3.6). No background is drawn below the border (background extends to the outside edge of the padding).',
                          'padding-box': '(Requires Gecko 1.9.3). No background is drawn below the border (background extends to the outside edge of the padding).'},
        'version': 'Firefox (Gecko) 1.0-3.6 (1.2-1.9.2)'},

    '-moz-background-inline-policy':
{       'description': 'In Gecko -based applications like Firefox, the -moz-background-inline-policy CSS property specifies how the background image of an inline element is determined when the content of the inline element wraps onto multiple lines. The choice of position has significant effects on repetition.',
        'values': {       'bounding-box': 'The background image is positioned (and repeated) in the smallest rectangle that contains all of the inline boxes for the element. It is then clipped to be visible only within those boxes, according to the -moz-background-clip property.',
                          'continuous': 'The background image is positioned (and repeated) as if the inline box were not broken across lines, and then this long rectangle is sliced into pieces for each line.',
                          'each-box': 'The background image is positioned (and repeated) separately for each box of the inline element. This means that an image with background-repeat : no-repeat may be repeated multiple times.'}},

    '-moz-background-origin':
{       'description': 'The background-origin CSS property determines the background positioning area (the origin of a background-image). background-origin does not apply when background-attachment is fixed . -moz-background-origin is supported up to Gecko version 1.9.2 (Firefox 3.6). Warning: To support both, older and newer versions of Gecko (Firefox), you have to add both properties in the stylesheet. See examples.',
        'values': {       'border': '(Firefox 1.0-3.6). The background position is relative to the border, so the image can go behind the border.',
                          'border-box': '(New in Firefox 4). The background position is relative to the border, so the image can go behind the border.',
                          'content': '(Firefox 1.0-3.6). The background position is relative to the content.',
                          'content-box': '(New in Firefox 4). The background position is relative to the content.',
                          'padding': '(Firefox 1.0-3.6). Default value. The background position is relative to the padding. (For single boxes " 0 0 " is the upper left corner of the padding edge, " 100% 100% " is the lower right corner.)',
                          'padding-box': '(New in Firefox 4). Default value. The background position is relative to the padding. (For single boxes " 0 0 " is the upper left corner of the padding edge, " 100% 100% " is the lower right corner.)'},
        'version': 'Firefox (Gecko) 1.0-3.6 (1.2-1.9.2)'},

    '-moz-background-size':
{       'description': 'The background-size CSS property specifies the size of the background images. -moz-background-size is supported by Gecko version 1.9.2 (Firefox 3.6). Warning: To support both, Firefox 3.6 and newer versions, you have to include both properties in the stylesheet. See examples.',
        'values': {       '<length>': 'Scales the background image to the specified length in the desired dimension.',
                          '<percentage>': "Scales the background image in the desired dimension to the specified percentage of the background positioning area, which is determined by the value of -moz-background-origin . The background positioning area is, by default, the area containing the content of the box and its padding; the area may also be changed to just the content or to the area containing borders, padding, and content. If the background's attachment is fixed , the background positioning area is instead the entire area of the browser window, not including the area covered by scrollbars if they are present.",
                          'auto': 'Scales the background image in the relevant direction such that its intrinsic proportions are maintained.',
                          'contain': 'Specifies that the background image should be scaled to be as large as possible while ensuring both its dimensions are less than or equal to the corresponding dimensions of the background positioning area.',
                          'cover': 'Specifies that the background image should be scaled to be as small as possible while ensuring both its dimensions are greater than or equal to the corresponding dimensions of the background positioning area.'},
        'version': 'Firefox (Gecko) 3.6 (1.9.2)'},

    '-moz-binding':
{       'description': 'The -moz-binding CSS property is used by Mozilla-based applications to attach an XBL binding to a DOM element.',
        'values': {       '<uri>': 'The URI for the XBL binding (including the fragment identifier).',
                          'none': 'no XBL binding is applied to the element.'}},

    '-moz-border-bottom-colors':
{       'description': 'In Mozilla applications like Firefox, -moz-border-bottom-colors sets a list of colors for the bottom border.'},

    '-moz-border-end':
{       },

    '-moz-border-end-color':
{       },

    '-moz-border-end-style':
{       },

    '-moz-border-end-width':
{       },

    '-moz-border-image':
{       'description': 'The border-image CSS property allows drawing an image on the borders of elements. This makes drawing complex looking widgets much simpler than it has been and removes the need for nine boxes in some cases.',
        'values': {       '<border-width>': '(optional). If the slash / is present in the property value, the one, two, three or four values after it are used for the width of the border instead of the border-width properties. The order of the values is the same as for border-width .',
                          '<image>': '(required). The image value is a <uri> , e.g. url(http://example.org/image.png)',
                          '<number>': '| <percentage> (required). One, two, three or four values represent inward offsets from the top, right, bottom, and left edges of the image (respectively), dividing it into nine regions: four corners, four edges and a middle. One value belongs to all four sides of the image. Two values belong 1. to top and bottom and 2. to right and left side. Three values belong 1. to top, 2. to the right and left side and 3. to bottom. Four values belong to the top, right, bottom and left edge of the image in that order. In Gecko 1.9.1 (Firefox 3.5) the middle part of the image is drawn like a background-image of the element. This may change in future versions. Percentages are relative to the width/height of the image. Numbers represent pixels in the image (if the image is a raster image) or vector coordinates (if the image is an SVG image).',
                          'none': 'No image displayed, other border styles are used.',
                          'stretch': '| round | repeat (optional). One or two keywords, that specify how the images for the sides and the middle part are scaled and tiled. stretch (default value) will cause images to be scaled to fit their box. round will tile the images, but also scale them so that a whole number fit in the box. repeat simply tiles the images inside the box. The first keyword describes how to draw the top, middle, and bottom images, while the second describes the left and right borders. If the second is absent, it is assumed to be the same as the first. If both are absent, the default value stretch is used.'},
        'version': 'Firefox (Gecko) 3.5 (1.9.1)'},

    '-moz-border-left-colors':
{       'description': 'In Mozilla applications like Firefox, the -moz-border-left-colors sets a list of colors for the left border.'},

    '-moz-border-radius':
{       'description': 'In Mozilla applications like Firefox, the -moz-border-radius CSS property can be used to give borders rounded corners. The radius applies also to the background even if the element has no border.',
        'values': {       '<length>': 'See <length> for possible units.',
                          '<percentage>': 'In Gecko (Firefox) Non-standard : A percentage, relative to the width of the box (the percentage is relative to the width even when specifying the radius for a height). In CSS 3: Percentages for the horizontal radius refer to the width of the box, whereas percentages for the vertical radius refer to the height of the box.'},
        'version': 'Firefox (Gecko) 1.0 (1.0)'},

    '-moz-border-radius-bottomleft':
{       'description': 'In Mozilla applications, -moz-border-radius-bottomleft sets the rounding of the bottom-left corner of the border.'},

    '-moz-border-radius-bottomright':
{       'description': 'In Mozilla applications, -moz-border-radius-bottomright sets the rounding of the bottom-right corner of the border.'},

    '-moz-border-radius-topleft':
{       'description': 'In Mozilla applications like Firefox, the -moz-border-radius-topleft CSS property sets the rounding of the top-left corner of the element.',
        'values': {       '<length>': 'See <length> for possible units.',
                          '<percentage>': 'In Gecko (Firefox) Non-standard : Relative to the width of the box (the percentage is relative to the width even when specifying the radius for a height). In CSS 3: Percentages for the horizontal radius refer to the width of the box, whereas percentages for the vertical radius refer to the height of the box.'},
        'version': 'Firefox 1.0 (Gecko 1.0)'},

    '-moz-border-radius-topright':
{       'description': 'In Mozilla applications like Firefox, the -moz-border-radius-topright CSS property sets the rounding of the top-right corner of the border.'},

    '-moz-border-right-colors':
{       'description': 'In Mozilla applications like Firefox, -moz-border-right-colors sets a list of colors for the right border.'},

    '-moz-border-start':
{       },

    '-moz-border-start-color':
{       },

    '-moz-border-start-style':
{       },

    '-moz-border-start-width':
{       },

    '-moz-border-top-colors':
{       'description': 'In Mozilla applications like Firefox, the -moz-border-top-colors CSS property sets a list of colors for the top border.',
        'values': {       '<color>': 'Specifies the color of a line of pixels in the bottom border. transparent is valid. See <color> values for possible units.',
                          'none': 'Default, no colors are drawn or border-color is used, if specified.'}},

    '-moz-box-align':
{       'description': 'In Mozilla applications, -moz-box-align specifies how a XUL box\naligns its contents across (perpendicular to) the direction of its layout. The effect of this is only\nvisible if there is extra space in the box.',
        'values': {       'baseline': "The box aligns the baselines of the contents (lining up the text). This only applies if the box'sorientation is horizontal.",
                          'center': 'The box aligns contents in the center, dividing any extra space equally between the start and the end.',
                          'end': 'The box aligns contents at the end, leaving any extra space at the start.',
                          'start': 'The box aligns contents at the start, leaving any extra space at the end.',
                          'stretch': 'The box stretches the contents so that there is no extra space in the box.'}},

    '-moz-box-direction':
{       'description': 'In Mozilla applications, -moz-box-direction specifies whether a box lays out its contents normally (from the top or left edge), or in reverse (from the bottom or right edge).',
        'values': {       'normal': 'The box lays out its contents from the start (the left or top edge).',
                          'reverse': 'The box lays out its contents from the end (the right or bottom edge).'}},

    '-moz-box-flex':
{       'description': "In Mozilla applications, -moz-box-flex specifies how a box grows\nto fill the box that contains it, in the direction of the containing box's layout.",
        'values': {       '0': 'The box does not grow.'}},

    '-moz-box-flexgroup':
{       },

    '-moz-box-ordinal-group':
{       'description': 'Indicates the ordinal group the element belongs to. Elements with a lower ordinal group are displayed before those with a higher ordinal group.',
        'values': {       }},

    '-moz-box-orient':
{       'description': 'In Mozilla applications, -moz-box-orient specifies whether a box\nlays out its contents horizontally or vertically.',
        'values': {       'horizontal': 'The box lays out its contents horizontally.',
                          'vertical': 'The box lays out its contents vertically.'}},

    '-moz-box-pack':
{       'description': 'In Mozilla applications, -moz-box-pack specifies how a box\npacks its contents in the direction of its layout. The effect of this is only\nvisible if there is extra space in the box.',
        'values': {       'center': 'The box packs contents in the center, dividing any extra space equally between the start and the end.',
                          'end': 'The box packs contents at the end, leaving any extra space at the start.',
                          'justify': '?',
                          'start': 'The box packs contents at the start, leaving any extra space at the end.'}},

    '-moz-box-shadow':
{       'description': 'The box-shadow CSS property accepts one or more shadow effects as a comma-separated list. It allows to cast a drop shadow from the frame of almost any arbitrary element. If a border-radius is specified on the element with a box shadow, the box shadow will take on the same rounded corners. The z-ordering of multiple box shadows is the same as multiple text-shadows (the first specified shadow is on top).',
        'values': {       '<blur-radius>': "(optional). This is a third <length> value. The larger this value, the bigger the blur, so the shadow becomes bigger and lighter. Negative values are not allowed. If not specified, it will be 0 (the shadow's edge is sharp).",
                          '<color>': "(optional). See <color> values for possible keywords and notations. If not specified, the color depends on the browser. In Gecko (Firefox), the value of the color property is used. WebKit's shadow is transparent and therefore useless if <color> is omitted.",
                          '<offset-x>': '<offset-y> (required). This are two <length> values to set the shadow offset. <offset-x> specifies the horizontal distance. Negative values place the shadow to the left of the element. <offset-y> specifies the vertical distance. Negative values place the shadow above the element. See <length> for possible units. If both values are 0 , the shadow is placed behind the element (and may generate a blur effect if <blur-radius> and/or <spread-radius> is set).',
                          '<spread-radius>': '(optional). This is a fourth <length> value. Positive values will cause the shadow to expand and grow bigger, negative values will cause the shadow to shrink. If not specified, it will be 0 (the shadow will be the same size as the element).',
                          'inset': '(optional). If not specified (default), the shadow is assumed to be a drop shadow (as if the box were raised above the content). The presence of the inset keyword changes the shadow to one inside the frame (as if the content was depressed inside the box). Inset shadows are drawn above background, but below border and content.'},
        'version': 'Firefox (Gecko) 3.5 (1.9.1)'},

    '-moz-box-sizing':
{       'description': '< CSS < CSS Reference < CSS Reference:Mozilla Extensions',
        'values': {       }},

    '-moz-column-count':
{       'description': 'In Mozilla applications like Firefox, the -moz-column-count CSS property can be used to set the ideal number of columns into which the content of the element will be flowed.',
        'values': {       '<integer>': 'Describes the ideal number of columns into which the content of the element will be flowed.'},
        'version': 'Firefox (Gecko) 1.5 (1.8)'},

    '-moz-column-gap':
{       'description': 'In Mozilla applications like Firefox, the -moz-column-gap CSS property sets the gap between columns for block elements which are specified to display as a multi-column element.',
        'values': {       '<length>': 'A non-negative value in any of the CSS <length> units to specify the gap between columns.',
                          'normal': 'Default value, depends on the user agent. In desktop browsers like Firefox this is 1em. In Gecko 1.8.1 (Firefox 2.0) and before the default value was 0 .'},
        'version': 'Firefox (Gecko) 1.5 (1.8)'},

    '-moz-column-rule':
{       'description': 'In multi-column layouts, the -moz-column-rule CSS property specifies a straight line, or "rule", to be drawn between each column. -moz-column-rule is a convenient shorthand to avoid setting each of the individual -moz-column-rule-* properties separately: -moz-column-rule-width , -moz-column-rule-style and -moz-column-rule-color .',
        'values': {       '<border-style>': 'Required , default value none is used if absent. See border-style for possible values and details.',
                          '<border-width>': 'Optional, is one value or keyword of: <length> | thin | medium | thick Default value medium is used if absent. See border-width for details.',
                          '<color>': "Optional , see <color> value. Default value if absent: currentColor , the value of the element's color property (foreground color)."},
        'version': 'Firefox (Gecko) 3.5 (1.9.1)'},

    '-moz-column-rule-color':
{       'description': 'The -moz-column-rule-color CSS property lets you set the color of the rule drawn between columns in multi-column layouts.',
        'values': {       '<color>': 'See <color> values.'},
        'version': 'Firefox (Gecko) 3.0 (1.9.1)'},

    '-moz-column-rule-style':
{       'description': 'The -moz-column-rule-style CSS property lets you set the style of the rule drawn between columns in multi-column layouts.',
        'values': {       '<border-style>': 'See border-style'},
        'version': 'Firefox (Gecko) 3.0 (1.9.1)'},

    '-moz-column-rule-width':
{       'description': 'The -moz-column-rule-width CSS property lets you set the width of the rule drawn between columns in multi-column layouts.',
        'values': {       '<border-width>': 'See border-width .'},
        'version': 'Firefox (Gecko) 3.0 (1.9.1)'},

    '-moz-column-width':
{       'description': 'In Mozilla applications like Firefox, the -moz-column-width CSS property suggests an optimal column width. The actual column width may be wider (to fill the available space), or narrower (only if the available space is smaller than the specified column width).',
        'values': {       '<length>': 'See <length> value for possible units.'},
        'version': 'Firefox (Gecko) 1.5 (1.8)'},

    '-moz-float-edge':
{       'description': 'bug 432891', 'values': {       }},

    '-moz-force-broken-image-icon':
{       'description': '-moz-force-broken-image-icon is an extended CSS property, for more info see bug 58646 . The value 1 forces a broken image icon even if the image has alt text',
        'values': {       '<integer>': ''}},

    '-moz-image-region':
{       'description': 'For certain XUL elements and pseudo-elements that use an image from the list-style-image property, this property specifies a region of the image that is used in place of the whole image. This allows elements to use different pieces of the same image to improve performance.'},

    '-moz-margin-end':
{       'description': 'In left to right (LTR) situations, the -moz-margin-end CSS property specifies the right margin and is synonymous with margin-right . In RTL cases it sets the left margin (same as margin-left ).',
        'values': {       '<length>': 'Specifies a fixed width.',
                          '<percentage>': 'A percentage with respect to the width of the containing block.'},
        'version': 'Firefox (Gecko) 1.0 (1.7)'},

    '-moz-margin-start':
{       'description': 'In left to right (LTR) situations the -moz-margin-start CSS property specifies the left margin and is synonymous with margin-left . In RTL cases it sets the right margin (same as margin-right ).',
        'values': {       '<length>': 'Specifies a fixed width.',
                          '<percentage>': 'a percentage with respect to the width of the containing block.'},
        'version': 'Firefox (Gecko) 1.0 (1.7)'},

    '-moz-opacity':
{       'description': 'The opacity CSS property specifies the transparency of an element, i.e. the degree to which the background behind the element is overlaid.',
        'values': {       '0': '< number < 1. The element is translucent (background can be seen).',
                          '1': 'The element is fully opaque (solid).'},
        'version': 'Firefox (Gecko) 0.9 (1.7) opacity'},

    '-moz-outline':
{       'description': '(OBSOLETE) Starting with Gecko 1.8 (Firefox 1.5), the standard CSS 2.1 outline property is supported as well. Use of outline is preferred to -moz-outline .',
        'values': {       }},

    '-moz-outline-color':
{       'description': '(OBSOLETE) Starting with Gecko 1.8 / Firefox 1.5, the standard CSS 2.1 outline-color property is supported as well. Use of outline-color is preferred to -moz-outline-color .',
        'values': {       }},

    '-moz-outline-offset':
{       'description': '(OBSOLETE) Support since Gecko 1.8 (Firefox 1.5) contemporary with the standard CSS 3 outline-offset property. Use only outline-offset .',
        'values': {       }},

    '-moz-outline-radius':
{       'description': 'In Mozilla applications like Firefox, the -moz-outline-radius CSS property can be used to give outlines rounded corners. An outline is a line that is drawn around elements, outside the border edge, to make the element stand out.',
        'values': {       '<length>': 'See <length> for possible values',
                          '<percentage>': 'A <percentage> , relative to the width of the box'}},

    '-moz-outline-radius-bottomleft':
{       'description': 'In Mozilla applications, -moz-outline-radius-bottomleft sets the rounding of the bottom-left corner of the outline.'},

    '-moz-outline-radius-bottomright':
{       'description': 'In Mozilla applications, -moz-outline-radius-bottomright sets the rounding of the bottom-right corner of the outline.'},

    '-moz-outline-radius-topleft':
{       'description': 'In Mozilla applications, -moz-outline-radius-topleft sets the rounding of the top-left corner of the outline.'},

    '-moz-outline-radius-topright':
{       'description': 'In Mozilla applications, -moz-outline-radius-topright sets the rounding of the top-right corner of the outline.'},

    '-moz-outline-style':
{       'description': '(OBSOLETE) Starting with Gecko 1.8 / Firefox 1.5, the standard CSS 2.1 outline-style property is supported as well. Use of outline-style is preferred to -moz-outline-style .',
        'values': {       }},

    '-moz-outline-width':
{       'description': '(OBSOLETE) Starting with Gecko 1.8 / Firefox 1.5, the standard CSS 2.1 outline-width property is supported as well. Use of outline-width is preferred to -moz-outline-width .',
        'values': {       }},

    '-moz-padding-end':
{       'description': "When rendering right-to-left text, -moz-padding-end flips the element's padding without having to specify absolute left or right. In a left-to-right text display -moz-padding-end is treated as a right sided padding, while in a right-to-left display it is padded on the left.",
        'values': {       '<length>': 'Specifies a fixed width.',
                          '<percentage>': 'a percentage with respect to the width of the containing block.'}},

    '-moz-padding-start':
{       'description': 'In Right to Left situations -moz-padding-start flips the elements padding without having to specify absolute left or right. In a Left to Right display -moz-padding-start would be treated as a left sided padding, and alternately in a Right to Left display it would become the right.',
        'values': {       '<length>': 'Specifies a fixed width.',
                          '<percentage>': 'a percentage with respect to the width of the containing block.'}},

    '-moz-stack-sizing':
{       'description': '-moz-stack-sizing is an extended CSS property. Normally, a stack will change its size so that all of its child elements are completely visible. For example, moving a child of the stack far to the right will widen the stack so the child remains visible.',
        'values': {       'ignore': "The stack won't consider this child when calculating the its size.",
                          'stretch-to-fit': "The child will influence the stack's size."}},

    '-moz-transform':
{       'description': '< CSS < CSS Reference < CSS Reference:Mozilla Extensions Introduced in Gecko 1.9.1 (Firefox 3.5 / Thunderbird 3 / SeaMonkey 2)',
        'values': {       'none': 'Specifies that no transform should be applied.',
                          'transform-function': 'One or more of the CSS transform functions to be applied, see below.'}},

    '-moz-transform-origin':
{       'description': "The -moz-transform-origin CSS property lets you modify the origin for transformations of an element. For example, the transform-origin of the rotate() function is the centre of rotation. (This property is applied by first translating the element by the negated value of the property, then applying the element's transform, then translating by the property value.)",
        'values': {       '<length>': 'With a value pair of e.g. 2cm 1cm , the transform-origin is placed 2cm to the right and 1cm below the upper left corner of the element.',
                          '<percentage>': 'With a value pair of 0% 0% , (or just 0 0 ) the transform-origin is the upper left corner of the box. A value pair of 100% 100% places the transform-origin to the lower right corner. With a value pair of 14% 84% , the point 14% across and 84% down the box is the transform-origin.',
                          'bottom': 'right | right bottom. Same as 100% 100%',
                          'center': '| center center. Same as 50% 50% (default value)',
                          'left': '| left center | center left. Same as 0 50%',
                          'right': '| right center | center right. Same as 100% 50%',
                          'top': '| top center | center top. Same as 50% 0'},
        'version': 'Firefox (Gecko) 3.5 (1.9.1)'},

    '-moz-transition':
{       'description': 'The -moz-transition CSS property is a shorthand property for -moz-transition-property , -moz-transition-duration , -moz-transition-timing-function , and -moz-transition-delay .',
        'version': 'Firefox (Gecko) 3.7? (Gecko 1.9.3)'},

    '-moz-transition-delay':
{       'description': 'The -moz-transition-delay CSS property specifies the number of seconds to wait between a change being requested to a property that is to be transitioned and the start of the transition effect .',
        'values': {       'time': "The number of seconds to wait between a property's value changing and the start of the animation effect."},
        'version': 'Firefox (Gecko) 3.7? (Gecko 1.9.3)'},

    '-moz-transition-duration':
{       'description': 'The -moz-transition-duration CSS property specifies the number of seconds a transition animation should take to complete. By default, the value is 0, meaning that no animation will occur.',
        'values': {       'time': 'The number of seconds the transition from the old value of a property to the new value should take.'},
        'version': 'Firefox (Gecko) 3.7? (Gecko 1.9.3)'},

    '-moz-transition-property':
{       'description': 'The -moz-transition-property CSS property is used to specify the names of CSS properties to which a transition effect should be applied.',
        'values': {       'all': 'All properties that can have an animated transition will do so.',
                          'none': 'No properties will transition.',
                          'property-name': 'A property to which a transition effect should be applied when its value changes.'},
        'version': 'Firefox (Gecko) 3.7? (Gecko 1.9.3)'},

    '-moz-transition-timing-function':
{       'description': 'The -moz-transition-timing-function CSS property is used to describe how the intermediate values of the CSS properties being affected by a transition effect are calculated. This in essence lets you establish an acceleration curve, so that the speed of the transition can vary over its duration.',
        'values': {       'cubic-bezier': 'Specifies a cubic bezier curve to use as the easing function. The four number values specify the P 1 and P 2 points of the curve as (x 1 , y 1 , x 2 , y 2 ). All values must be in the range [0.0, 1.0] inclusive.',
                          'ease': 'This keyword sets the easing function to cubic-bezier(0.25, 0.1, 0.25, 1.0) .',
                          'ease-in': 'This keyword sets the easing function to cubic-bezier(0.42, 0.0, 1.0, 1.0) .',
                          'ease-in-out': 'This keyword sets the easing function to cubic-bezier(0.42, 0.0, 0.58, 1.0) .',
                          'ease-out': 'This keyword sets the easing function to cubic-bezier(0.0, 0.0, 0.58, 1.0) .',
                          'linear': 'This keyword sets the easing function to cubic-bezier(0.0, 0.0, 1.0, 1.0) .'},
        'version': 'Firefox (Gecko) 3.7? (Gecko 1.9.3)'},

    '-moz-user-focus':
{       'description': "Used to indicate whether the element can have the focus. By setting this to 'ignore', you can disable focusing the element, which means that the user will not be able to activate the element. The element will be skipped in the tab sequence. A similar property 'user-focus' has been proposed for CSS3.",
        'values': {       'ignore': 'The element does not accept the keyboard focus and will be skipped in the tab order.',
                          'normal': 'The element can accept the keyboard focus.'}},

    '-moz-user-input':
{       'description': 'In Mozilla applications, -moz-user-input determines if an element will accept user input.',
        'values': {       'disabled': 'The element does not accept user input. However, this is not the same as setting disabled to true, in that the element is drawn normally.',
                          'enabled': 'The element accepts user input. For textboxes, this is the default behavior.',
                          'none': 'The element does not respond to user input, and it does not become :active .'}},

    '-moz-user-modify':
{       },

    '-moz-user-select':
{       'description': "Controls the appearance (only) of selection. This does not have any affect on actual selection operation. This doesn't have any effect on content loaded as chrome, except in textboxes.",
        'values': {       '-moz-none': 'The text of the element and sub-elements cannot be selected, but selection can be enabled on sub-elements using -moz-user-select:text .',
                          'all': 'In HTML editor, if double-click or context-click occurred in sub-elements, the highest ancestor with this value will be selected.',
                          'none': 'The text of the element and sub-elements will appear as if they cannot be selected. Any use of Selection however will contain these elements.',
                          'text': 'The text can be selected by the user.'}},

    '-moz-window-shadow':
{       'description': '-moz-window-shadow specifies whether a window will have a shadow. Currently it only works on Mac OS X.',
        'values': {       'default': 'The window will have a shadow with the default window shadow style.',
                          'none': "The window won't have a shadow."}},
}


### END: Auto generated




CSS_MOZ_SPECIFIC_ATTRS_DICT = {}
CSS_MOZ_SPECIFIC_CALLTIP_DICT = {}
for attr, details in CSS_MOZ_DATA.items():
    values = details.get("values", {})
    attr_completions = sorted(values.keys())
    if attr_completions:
        CSS_MOZ_SPECIFIC_ATTRS_DICT[attr] = attr_completions
    else:
        CSS_MOZ_SPECIFIC_ATTRS_DICT[attr] = None
    description = details.get("description")
    if description:
        desc_lines = textwrap.wrap(description, width=60)
        if values:
            desc_lines.append("")
            for value, attr_desc in values.items():
                attr_desc = "  %r: %s" % (value, attr_desc)
                attr_desc_lines = textwrap.wrap(attr_desc, width=50)
                for i in range(len(attr_desc_lines)):
                    attr_line = attr_desc_lines[i]
                    if i > 0:
                        attr_line = "        " + attr_line
                    desc_lines.append(attr_line)
        CSS_MOZ_SPECIFIC_CALLTIP_DICT[attr] = "\n".join(desc_lines).encode("ascii", 'replace')
