"""
Safari/Webkit CSS extensions.
"""

import textwrap

### START: Auto generated

CSS_WEBKIT_DATA = {

    '-webkit-animation':
{       'description': u'Combines common animation properties into a single property.',
        'syntax': u'-webkit-animation: name duration timing_function delay iteration_count direction [, ... ];',
        'values': {       u'delay': u'Defines when an animation starts.',
                          u'direction': u'Determines whether the animation should play in reverse on alternate iterations.',
                          u'duration': u'Specifies the length of time that an animation takes to complete one iteration.',
                          u'iteration_count': u'Specifies the number of times an animation iterates.',
                          u'name': u'The name of the animation.',
                          u'timing_function': u'Defines how an animation progresses between keyframes.'},
        'versions': [u'Safari 4.0', u'iPhone OS 2.0']},

    '-webkit-animation-delay':
{       'description': u'Defines when an animation starts.',
        'syntax': u'-webkit-animation-delay: time [, ...];',
        'values': {       u'0': u'(by default) ',
                          u'now': u'The animation begins immediately. Available in iPhone OS 2.0 and later.'},
        'versions': [u'Safari 4.0', u'iPhone OS 2.0']},

    '-webkit-animation-direction':
{       'description': u'Determines whether the animation should play in reverse on alternate iterations.',
        'syntax': u'-webkit-animation-direction: direction [, ...]',
        'values': {       u'alternate': u'Play even-numbered iterations of the animation in the forward direction and odd-numbered iterations in the reverse direction. \n When an animation is played in reverse, the timing functions are also reversed. For example, when played in reverse, an ease-in animation appears as an ease-out animation.',
                          u'normal': u'(by default) Play each iteration of the animation in the forward direction.'},
        'versions': [u'Safari 4.0', u'iPhone OS 2.0']},

    '-webkit-animation-duration':
{       'description': u'Specifies the length of time that an animation takes to complete one iteration.',
        'syntax': u'-webkit-animation-duration: time [, ...]',
        'values': {       u'0': u'(by default) ', u'<time>': ''},
        'versions': [u'Safari 4.0', u'iPhone OS 2.0']},

    '-webkit-animation-iteration-count':
{       'description': u'Specifies the number of times an animation iterates.',
        'syntax': u'-webkit-animation-iteration-count: number [, ...]',
        'values': {       u'1': u'(by default) ',
                          u'infinite': u'Repeats the animation forever.'},
        'versions': [u'Safari 4.0', u'iPhone OS 2.0']},

    '-webkit-animation-name':
{       'description': u'Specifies the name of an animation.',
        'syntax': u'-webkit-animation-name: name [, ...]',
        'values': {       u'name': u'The name of the animation.'},
        'versions': [u'Safari 4.0', u'iPhone OS 2.0']},

    '-webkit-animation-play-state':
{       'description': u'Determines whether the animation is running or paused.',
        'syntax': u'-webkit-animation-play-state: play_state [, ...];',
        'values': {       u'paused': u'Pauses the animation.',
                          u'running': u'(by default) Plays the animation.'},
        'versions': [u'Safari 4.0', u'iPhone OS 2.0']},

    '-webkit-animation-timing-function':
{       'description': u'Defines how an animation progresses between keyframes.',
        'syntax': u'-webkit-animation-timing-function: function [, ...]',
        'values': {       u'<function>': '',
                          u'ease': u'(by default) Equivalent to  cubic-bezier(0.25, 0.1, 0.25, 1.0) .',
                          u'ease-in': u'Equivalent to  cubic-bezier(0.42, 0, 1.0, 1.0) .',
                          u'ease-in-out': u'Equivalent to  cubic-bezier(0.42, 0, 0.58, 1.0) .',
                          u'ease-out': u'Equivalent to  cubic-bezier(0, 0, 0.58, 1.0) .',
                          u'linear': u'Equivalent to  cubic-bezier(0.0, 0.0, 1.0, 1.0) .'},
        'versions': [u'Safari 4.0', u'iPhone OS 2.0']},

    '-webkit-appearance':
{       'description': u'Changes the appearance of buttons and other controls to resemble native controls.',
        'syntax': u'-webkit-appearance: appearance;',
        'values': {       u'button': '',
                          u'button-bevel': '',
                          u'caps-lock-indicator': u'The indicator that appears in a password field when Caps Lock is active. Available in Safari 4.0 and later. Available in iPhone OS 2.0 and later.',
                          u'caret': '',
                          u'checkbox': '',
                          u'default-button': '',
                          u'listbox': '',
                          u'listitem': '',
                          u'media-fullscreen-button': '',
                          u'media-mute-button': '',
                          u'media-play-button': '',
                          u'media-seek-back-button': '',
                          u'media-seek-forward-button': '',
                          u'media-slider': '',
                          u'media-sliderthumb': '',
                          u'menulist': '',
                          u'menulist-button': '',
                          u'menulist-text': '',
                          u'menulist-textfield': '',
                          u'none': '',
                          u'push-button': '',
                          u'radio': '',
                          u'scrollbarbutton-down': u'Unsupported in Safari 4.0',
                          u'scrollbarbutton-left': u'Unsupported in Safari 4.0',
                          u'scrollbarbutton-right': u'Unsupported in Safari 4.0',
                          u'scrollbarbutton-up': u'Unsupported in Safari 4.0',
                          u'scrollbargripper-horizontal': u'Unsupported in Safari 4.0',
                          u'scrollbargripper-vertical': u'Unsupported in Safari 4.0',
                          u'scrollbarthumb-horizontal': u'Unsupported in Safari 4.0',
                          u'scrollbarthumb-vertical': u'Unsupported in Safari 4.0',
                          u'scrollbartrack-horizontal': u'Unsupported in Safari 4.0',
                          u'scrollbartrack-vertical': u'Unsupported in Safari 4.0',
                          u'searchfield': '',
                          u'searchfield-cancel-button': '',
                          u'searchfield-decoration': '',
                          u'searchfield-results-button': '',
                          u'searchfield-results-decoration': '',
                          u'slider-horizontal': '',
                          u'slider-vertical': '',
                          u'sliderthumb-horizontal': '',
                          u'sliderthumb-vertical': '',
                          u'square-button': '',
                          u'textarea': '',
                          u'textfield': ''},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-backface-visibility':
{       'description': u'Determines whether or not a transformed element is visible when it is not facing the screen.',
        'syntax': u'-webkit-backface-visibility: visibility;',
        'values': {       u'hidden': u'The element is invisible if it is not facing the screen.',
                          u'visible': u'(by default) The element is always visible even when it is not facing the screen.'},
        'versions': [u'iPhone OS 2.0']},

    '-webkit-background-clip':
{       'description': u'Specifies the clipping behavior of the background of a box.',
        'syntax': u'-webkit-background-clip: behavior;',
        'values': {       u'border': u'The background clips to the border of the box.',
                          u'content': u'The background clips to the content of the box.',
                          u'padding': u'The background clips to the padding of the box.',
                          u'text': u'The background clips to the text of the box. Available in Safari 4.0 and later.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-background-composite':
{       'description': u'Sets a compositing style for background images and colors.',
        'syntax': u'-webkit-background-composite: compositing_style;',
        'values': {       u'border': u'(by default) The background extends into the border area',
                          u'padding': u'The background extends only into the padding area enclosed by the border'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-background-origin':
{       'description': u'Determines where the  background-position  property is anchored.',
        'syntax': u'-webkit-background-origin: origin;',
        'values': {       u'origin': u'The origin of the background position.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-background-size':
{       'description': u'Overrides the size of a background image.',
        'syntax': u'-webkit-background-size: length;',
        'values': {       u'length': u'The width and height of the background image.',
                          u'length_x': u'The width of the background image.',
                          u'length_y': u'The height of the background image.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-border-bottom-left-radius':
{       'description': u'Specifies that the bottom-left corner of a box be rounded with the specified radius.',
        'syntax': u'-webkit-border-bottom-left-radius: radius;',
        'values': {       u'horizontal_radius': u'The horizontal radius of the rounded corner.',
                          u'radius': u'The radius of the rounded corner.',
                          u'vertical_radius': u'The vertical radius of the rounded corner.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-border-bottom-right-radius':
{       'description': u'Specifies that the bottom-right corner of a box be rounded with the specified radius.',
        'syntax': u'-webkit-border-bottom-right-radius: radius;',
        'values': {       u'horizontal_radius': u'The horizontal radius of the rounded corner.',
                          u'radius': u'The radius of the rounded corner.',
                          u'vertical_radius': u'The vertical radius of the rounded corner.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-border-horizontal-spacing':
{       'description': u'Defines the spacing between the horizontal portion of an element\u2019s border and the content within.',
        'syntax': u'-webkit-border-horizontal-spacing: value;',
        'values': {       u'value': u'The amount of horizontal spacing.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-border-image':
{       'description': u'Specifies an image as the border for a box.',
        'syntax': u'-webkit-border-image: uri top right bottom left x_repeat y_repeat',
        'values': {       u'repeat': u'The image is tiled.',
                          u'round': u'The image is stretched before it is tiled to prevent partial tiles.',
                          u'stretch': u'The image is stretched to the size of the border.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-border-radius':
{       'description': u'Specifies that the corners of a box be rounded with the specified radius.',
        'syntax': u'-webkit-border-radius: radius;',
        'values': {       u'horizontal_radius': u'The horizontal radius of the rounded corners.',
                          u'radius': u'The radius of the rounded corners.',
                          u'vertical_radius': u'The vertical radius of the rounded corners.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-border-top-left-radius':
{       'description': u'Specifies that the top-left corner of a box be rounded with the specified radius.',
        'syntax': u'-webkit-border-top-left-radius: radius;',
        'values': {       u'horizontal_radius': u'The horizontal radius of the rounded corner.',
                          u'radius': u'The radius of the rounded corner.',
                          u'vertical_radius': u'The vertical radius of the rounded corner.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-border-top-right-radius':
{       'description': u'Specifies that the top-right corner of a box be rounded with the specified radius.',
        'syntax': u'-webkit-border-top-right-radius: radius;',
        'values': {       u'horizontal_radius': u'The horizontal radius of the rounded corner.',
                          u'radius': u'The radius of the rounded corner.',
                          u'vertical_radius': u'The vertical radius of the rounded corner.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-border-vertical-spacing':
{       'description': u'Defines the spacing between the vertical portion of an element\u2019s border and the content within.',
        'syntax': u'-webkit-border-vertical-spacing: value;',
        'values': {       u'value': u'The amount of vertical spacing.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-box-align':
{       'description': u'Specifies the alignment of nested elements within an outer flexible box element.',
        'syntax': u'-webkit-box-align: alignment;',
        'values': {       u'baseline': u'Elements are aligned with the baseline of the box.',
                          u'center': u'Elements are aligned with the center of the box.',
                          u'end': u'Elements are aligned with the end of the box.',
                          u'start': u'Elements are aligned with the start of the box.',
                          u'stretch': u'Elements are stretched to fill the box.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-box-direction':
{       'description': u'Specifies the direction in which child elements of a flexible box element are laid out.',
        'syntax': u'-webkit-box-direction: layout_direction;',
        'values': {       u'normal': u'(by default) Elements are laid out in the default direction.',
                          u'reverse': u'Elements are laid out in the reverse direction.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-box-flex':
{       'description': u'Specifies an element\u2019s flexibility.',
        'syntax': u'-webkit-box-flex: flex_value;',
        'values': {       u'<flexvalue>': u'Floating-point number'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-box-flex-group':
{       'description': u'Specifies groups of dynamically resizing elements that are adjusted to be the same size.',
        'syntax': u'-webkit-box-flex-group: group_number;',
        'values': {       u'<group_number>': u'Integer, nonnegative value'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-box-lines':
{       'description': u'Specifies whether a flexible box should contain multiple lines of content.',
        'syntax': u'-webkit-box-lines: behavior;',
        'values': {       u'multiple': u'The box can contain multiple lines of content.',
                          u'single': u'The box can contain only one line of content.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-box-ordinal-group':
{       'description': u'Specifies a rough ordering of elements in a flexible box.',
        'syntax': u'-webkit-box-ordinal-group: group_number;',
        'values': {       u'<group_number>': u'Integer, nonnegative value'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-box-orient':
{       'description': u'Specifies the layout of elements nested within a flexible box element.',
        'syntax': u'-webkit-box-orient: orientation;',
        'values': {       u'block-axis': u"Elements are oriented along the box's axis.",
                          u'horizontal': u'Elements are oriented horizontally.',
                          u'inline-axis': u'Elements are oriented along the inline axis.',
                          u'vertical': u'Elements are oriented vertically.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-box-pack':
{       'description': u'Specifies alignment of child elements within the current element in the direction of orientation.',
        'syntax': u'-webkit-box-pack: alignment;',
        'values': {       u'center': u'Child elements are aligned to the center of the element.',
                          u'end': u'Child elements are aligned to the end of the element.',
                          u'justify': u'Child elements are justified with both the start and end of the element.',
                          u'start': u'Child elements are aligned to the start of the element.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-box-reflect':
{       'description': u'Defines a reflection of a border box.',
        'syntax': u'-webkit-box-reflect: direction offset mask-box-image;',
        'values': {       u'above': u'The reflection appears above the border box.',
                          u'below': u'The reflection appears below the border box.',
                          u'left': u'The reflection appears to the left of the border box.',
                          u'right': u'The reflection appears to the right of the border box.'},
        'versions': [u'iPhone OS 2.0']},

    '-webkit-box-shadow':
{       'description': u'Applies a drop shadow effect to the border box of an object.',
        'syntax': u'-webkit-box-shadow: hoff voff blur color;',
        'values': {       u'none': u'(by default) The box has no shadow.'},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-box-sizing':
{       'description': u'Specifies that the size of a box be measured according to either its content (default) or its total size including borders.',
        'syntax': u'-webkit-box-sizing: sizing_model;',
        'values': {       u'border-box': u'The box size includes borders in addition to content.',
                          u'content-box': u'(by default) The box size only includes content.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-column-break-after':
{       'description': u'Determines whether a column break can and should occur after an element in a multicolumn flow layout.',
        'syntax': u'-webkit-column-break-after: policy;',
        'values': {       u'always': u'A column break is always inserted after the element.',
                          u'auto': u'(by default) A right column break is inserted after the element where appropriate.',
                          u'avoid': u'Column breaks are avoided after the element.',
                          u'left': u'A left column break is inserted after the element.',
                          u'right': u'A right column break is inserted after the element.'},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-column-break-before':
{       'description': u'Determines whether a column break can and should occur before an element in a multicolumn flow layout.',
        'syntax': u'-webkit-column-break-before: policy;',
        'values': {       u'always': u'A column break is always inserted before the element.',
                          u'auto': u'(by default) A right column break is inserted before the element where appropriate.',
                          u'avoid': u'Column breaks are avoided before the element.',
                          u'left': u'A left column break is inserted before the element.',
                          u'right': u'A right column break is inserted before the element.'},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-column-break-inside':
{       'description': u'Determines whether a column break should be avoided within the bounds of an element in a multicolumn flow layout.',
        'syntax': u'-webkit-column-break-inside: policy;',
        'values': {       u'auto': u'(by default) A right column break is inserted within the element where appropriate.',
                          u'avoid': u'Column breaks are avoided within the element.'},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-column-count':
{       'description': u'Specifies the number of columns desired in a multicolumn flow.',
        'syntax': u'-webkit-column-count: number_of_columns;',
        'values': {       u'<number_of_columns>': u'Integer, nonnegative value',
                          u'auto': u'(by default) The element has one column.'},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-column-gap':
{       'description': u'Specifies the space between columns in a multicolumn flow.',
        'syntax': u'-webkit-column-gap: width;',
        'values': {       u'<width>': u'Length unit',
                          u'normal': u'(by default) Columns in the element have the normal gap width between them.'},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-column-rule':
{       'description': u'Specifies the color, style, and width of the column rule.',
        'syntax': u'-webkit-column-rule: width style color;',
        'values': {       u'color': u'The color of the column rule.',
                          u'style': u'The style of the column rule.',
                          u'width': u'The width of the column rule.'},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-column-rule-color':
{       'description': u'Specifies the color of the column rule.',
        'syntax': u'-webkit-column-rule-color: color;',
        'values': {       u'-webkit-activelink': u'The default color of a hyperlink that is being clicked.',
                          u'-webkit-focus-ring-color': u'The color that surrounds a UI element, such as a text field, that has focus.',
                          u'-webkit-link': u'The default color of a hyperlink that has been visited.',
                          u'-webkit-text': u'The default text color.',
                          u'activeborder': '',
                          u'activecaption': '',
                          u'appworkspace': '',
                          u'aqua': '',
                          u'background': '',
                          u'black': '',
                          u'blue': '',
                          u'buttonface': '',
                          u'buttonhighlight': '',
                          u'buttonshadow': '',
                          u'buttontext': '',
                          u'captiontext': '',
                          u'currentcolor': u"(by default) The value of the element's color property.",
                          u'fuchsia': '',
                          u'gray': '',
                          u'graytext': '',
                          u'green': '',
                          u'grey': '',
                          u'highlight': '',
                          u'highlighttext': '',
                          u'inactiveborder': '',
                          u'inactivecaption': '',
                          u'inactivecaptiontext': '',
                          u'infobackground': '',
                          u'infotext': '',
                          u'lime': '',
                          u'maroon': '',
                          u'match': '',
                          u'menu': '',
                          u'menutext': '',
                          u'navy': '',
                          u'olive': '',
                          u'orange': '',
                          u'purple': '',
                          u'red': '',
                          u'scrollbar': '',
                          u'silver': '',
                          u'teal': '',
                          u'threeddarkshadow': '',
                          u'threedface': '',
                          u'threedhighlight': '',
                          u'threedlightshadow': '',
                          u'threedshadow': '',
                          u'transparent': '',
                          u'white': '',
                          u'window': '',
                          u'windowframe': '',
                          u'windowtext': '',
                          u'yellow': ''},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-column-rule-style':
{       'description': u'Specifies the style of the column rule.',
        'syntax': u'-webkit-column-rule-style: style;',
        'values': {       u'dashed': u'The column rule has a dashed line style.',
                          u'dotted': u'The column rule has a dotted line style.',
                          u'double': u'The column rule has a double solid line style.',
                          u'groove': u'The column rule has a grooved style.',
                          u'hidden': u'The column rule is hidden.',
                          u'inset': u'The column rule has an inset style.',
                          u'none': u'The column rule has no style.',
                          u'outset': u'The column rule has an outset style.',
                          u'ridge': u'The column rule has a ridged style.',
                          u'solid': u'The column rule has a solid line style.'},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-column-rule-width':
{       'description': u'Specifies the width of the column rule.',
        'syntax': u'-webkit-column-rule-width: width;',
        'values': {       u'<width>': u'Length unit',
                          u'medium': u'The column rule has a medium width.',
                          u'thick': u'The column rule has a thick width.',
                          u'thin': u'The column rule has a thin width.'},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-column-width':
{       'description': u'Specifies the width of the column in a multicolumn flow.',
        'syntax': u'-webkit-column-width: width;',
        'values': {       u'<width>': u'Length unit',
                          u'auto': u'(by default) Columns in the element are of normal width.'},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-columns':
{       'description': u'A composite property that specifies the width and number of columns in a multicolumn flow layout.',
        'syntax': u'-webkit-columns: width count;',
        'values': {       u'count': u'The number of columns.',
                          u'width': u'The width of each column.'},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-dashboard-region':
{       'description': u'Specifies the behavior of regions in a Dashboard widget.',
        'syntax': u'-webkit-dashboard-region: dashboard-region(...) [...];',
        'values': {       u'none': u'No behavior is specified.'},
        'versions': [u'Safari 3.0']},

    '-webkit-line-break':
{       'description': u'Specifies line-breaking rules for CJK (Chinese, Japanese, and Korean) text.',
        'syntax': u'-webkit-line-break: setting;',
        'values': {       u'after-white-space': u'The line breaks after white space.',
                          u'normal': u'(by default) A standard line-breaking rule.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-margin-bottom-collapse':
{       'description': u"Specifies the behavior of an element's bottom margin if it is adjacent to an element with a margin. Elements can maintain their respective margins or share a single margin between them.",
        'syntax': u'-webkit-margin-bottom-collapse: collapse_behavior;',
        'values': {       u'collapse': u'Two adjacent margins are collapsed into a single margin.',
                          u'discard': u'The element\u2019s margin is discarded if it is adjacent to another element with a margin.',
                          u'separate': u'Two adjacent margins remain separate.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-margin-collapse':
{       'description': u'Specifies the behavior of an element\u2019s vertical margins if it is adjacent to an element with a margin. Elements can maintain their respective margins or share a single margin between them.',
        'syntax': u'-webkit-margin-collapse: collapse_behavior;',
        'values': {       u'collapse_behavior': u'The behavior of the vertical margins.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-margin-start':
{       'description': u'Provides the width of the starting margin.',
        'syntax': u'-webkit-margin-start: width;',
        'values': {       u'<width>': u'Number as a percentage, length unit',
                          u'auto': u'(by default) The margin is automatically determined.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-margin-top-collapse':
{       'description': u'Specifies the behavior of an element\u2019s top margin if it is adjacent to an element with a margin. Elements can maintain their respective margins or share a single margin between them.',
        'syntax': u'-webkit-margin-top-collapse: collapse_behavior;',
        'values': {       u'collapse': u'Two adjacent margins are collapsed into a single margin.',
                          u'discard': u'The element\u2019s margin is discarded if it is adjacent to another element with a margin.',
                          u'separate': u'Two adjacent margins remain separate.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-marquee':
{       'description': u'Defines properties for showing content as though displayed on an electronic marquee sign.',
        'syntax': u'-webkit-marquee: direction increment repetition style speed;',
        'values': {       u'direction': u'The direction of the marquee.',
                          u'increment': u'The distance the marquee moves in each increment',
                          u'repetition': u'The number of times the marquee repeats.',
                          u'speed': u'The scroll or slide speed of the marquee.',
                          u'style': u'The style of the marquee\u2019s motion.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-marquee-direction':
{       'description': u'Specifies the direction of motion for a marquee box.',
        'syntax': u'-webkit-marquee-direction: direction;',
        'values': {       u'ahead': u'The marquee moves from bottom to top.',
                          u'auto': u'(by default) The marquee moves in the default direction.',
                          u'backwards': u'The marquee moves from right to left.',
                          u'down': u'The marquee moves from bottom to top.',
                          u'forwards': u'The marquee moves from left to right.',
                          u'left': u'The marquee moves from right to left.',
                          u'reverse': u'The marquee moves from top to bottom.',
                          u'right': u'The marquee moves from left to right.',
                          u'up': u'The marquee moves from bottom to top.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-marquee-increment':
{       'description': u'Defines the distance the marquee moves in each increment.',
        'syntax': u'-webkit-marquee-increment: distance;',
        'values': {       u'<distance>': u'Number as a percentage, length unit',
                          u'large': u'The marquee moves a large amount in each increment.',
                          u'medium': u'The marquee moves a medium amount in each increment.',
                          u'small': u'The marquee moves a small amount in each increment.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-marquee-repetition':
{       'description': u'Specifies the number of times a marquee box repeats (or  infinite ).',
        'syntax': u'-webkit-marquee-repetition: iterations;',
        'values': {       u'<iterations>': u'Integer, nonnegative value',
                          u'infinite': u'(by default) The marquee repeats infinitely.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-marquee-speed':
{       'description': u'Defines the scroll or slide speed of a marquee box.',
        'syntax': u'-webkit-marquee-speed: speed;',
        'values': {       u'<distance>': u'Integer, nonnegative value',
                          u'<time>': u'Time unit, nonnegative value',
                          u'fast': u'The marquee moves at a fast speed.',
                          u'normal': u'The marquee moves at a normal speed.',
                          u'slow': u'The marquee moves at a slow speed.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-marquee-style':
{       'description': u'Specifies the style of marquee motion.',
        'syntax': u'-webkit-marquee-style: style;',
        'values': {       u'alternate': u'The marquee shifts back and forth.',
                          u'none': u'The marquee does not move.',
                          u'scroll': u'The marquee loops in its specified direction.',
                          u'slide': u'The marquee moves in its specified direction, but stops either when the entirety of its content has been displayed or the content reaches the opposite border of its box, whichever comes second.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-mask':
{       'description': u'Defines a variety of mask properties within one declaration.',
        'syntax': u'-webkit-mask: attachment, clip, origin, image, repeat, composite, box-image;',
        'values': {       u'attachment': u'Defines the scrolling or fixed nature of the image mask. See  -webkit-mask-attachment .',
                          u'clip': u'Specifies whether the mask should extend into the border of a box. See  -webkit-mask-clip .',
                          u'composite': u'Sets a compositing style for a mask. See  -webkit-mask-composite .',
                          u'image': u'Defines an image to be used as a mask for an element. See  -webkit-mask-image .',
                          u'origin': u'Determines where the  -webkit-mask-position  property is anchored. See  -webkit-mask-origin .',
                          u'repeat': u'Defines the repeating qualities of a mask. See  -webkit-mask-repeat .'},
        'versions': [u'Safari 4.0']},

    '-webkit-mask-attachment':
{       'description': u'Defines the scrolling or fixed nature of the image mask.',
        'syntax': u'-webkit-mask-attachment: mask_attachment;',
        'values': {       u'fixed': u'The mask does not move when the page scrolls.',
                          u'scroll': u'The image moves when the page scrolls.'},
        'versions': [u'Safari 4.0']},

    '-webkit-mask-box-image':
{       'description': u'Defines an image to be used as a mask for a border box.',
        'syntax': u'-webkit-mask-box-image: uri top right bottom left x_repeat y_repeat;',
        'values': {       u'bottom': u'The distance from the bottom edge of the image.',
                          u'left': u'The distance from the left edge of the image.',
                          u'right': u'The distance from the right edge of the image.',
                          u'top': u'The distance from the top edge of the image.',
                          u'uri': u'The file path of the image.',
                          u'x_repeat': u'The horizontal repeat style.',
                          u'y_repeat': u'The vertical repeat style.'},
        'versions': [u'Safari 4.0']},

    '-webkit-mask-clip':
{       'description': u'Specifies whether the mask should extend into the border of a box.',
        'syntax': u'-webkit-mask-clip: behavior;',
        'values': {       u'behavior': u'The clipping behavior of the mask.'},
        'versions': [u'Safari 4.0']},

    '-webkit-mask-composite':
{       'description': u'Sets a compositing style for a mask.',
        'syntax': u'-webkit-mask-composite: compositing_style;',
        'values': {       u'border': u'(by default) ', u'padding': ''},
        'versions': [u'Safari 4.0']},

    '-webkit-mask-image':
{       'description': u'Defines an image to be used as a mask for an element.',
        'syntax': u'-webkit-mask-image: value;',
        'values': {       u'value': u'The file path of the image.'},
        'versions': [u'Safari 4.0']},

    '-webkit-mask-origin':
{       'description': u'Determines where the -webkit-mask-position property is anchored.',
        'syntax': u'-webkit-mask-origin: origin;',
        'values': {       u'border': u"The mask's position is anchored at the upper-left corner of the element's border.",
                          u'content': u"The mask's position is anchored at the upper-left corner of the element's content.",
                          u'padding': u"The mask's position is anchored at the upper-left corner of the element's padding."},
        'versions': [u'Safari 4.0']},

    '-webkit-mask-position':
{       'description': u'Defines the position of a mask.',
        'syntax': u'-webkit-mask-position: xpos;',
        'values': {       u'<position>': '',
                          u'bottom': '',
                          u'center': '',
                          u'left': '',
                          u'right': '',
                          u'top': ''},
        'versions': [u'Safari 4.0']},

    '-webkit-mask-position-x':
{       'description': u'Defines the x-coordinate of the position of a mask.',
        'syntax': u'-webkit-mask-position-x: value;',
        'values': {       u'value': u'The x-coordinate of the position of the mask.'},
        'versions': [u'Safari 4.0']},

    '-webkit-mask-position-y':
{       'description': u'Defines the y-coordinate of the position of a mask.',
        'syntax': u'-webkit-mask-position-y: value;',
        'values': {       u'value': u'The y-coordinate of the position of the mask.'},
        'versions': [u'Safari 4.0']},

    '-webkit-mask-repeat':
{       'description': u'Defines the repeating qualities of a mask.',
        'syntax': u'-webkit-mask-repeat: value;',
        'values': {       u'value': u'The repeating behavior of the mask.'},
        'versions': [u'Safari 4.0']},

    '-webkit-mask-size':
{       'description': u'Overrides the size of a mask.',
        'syntax': u'-webkit-mask-size: length;',
        'values': {       u'length': u'The width and height of the mask.',
                          u'length_x': u'The width of the mask.',
                          u'length_y': u'The height of the mask.'},
        'versions': [u'Safari 4.0']},

    '-webkit-nbsp-mode':
{       'description': u'Defines the behavior of nonbreaking spaces within text.',
        'syntax': u'-webkit-nbsp-mode: behavior;',
        'values': {       u'normal': u'Nonbreaking spaces are treated as usual.',
                          u'space': u'Nonbreaking spaces are treated like standard spaces.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-padding-start':
{       'description': u'Provides the width of the starting padding.',
        'syntax': u'-webkit-padding-start: width;',
        'values': {       u'<length>': '', u'<percentage>': ''},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-perspective':
{       'description': u'Gives depth to a scene, causing elements farther away from the viewer to appear smaller.',
        'syntax': u'-webkit-perspective: value;',
        'values': {       u'<distance>': u'Length in pixel',
                          u'none': u'(by default) No perspective transform is applied.'},
        'versions': [u'iPhone OS 2.0']},

    '-webkit-perspective-origin':
{       'description': u'Sets the origin of the  -webkit-perspective  property described in  "-webkit-perspective."',
        'syntax': u'-webkit-perspective-origin: posx posy;',
        'values': {       u'50%': u'50% (by default) ',
                          u'<percentage>': '',
                          u'bottom': u'Sets the y-origin to the bottom of the element\u2019s border box.',
                          u'center': u'Sets the x or y origin to the center of the element\u2019s border box. If this constant appears before  left  or  right , specifies the y-origin. If it appears after  top  or  bottom , specifies the x-origin. If appears alone, centers both the x and y origin.',
                          u'left': u'Sets the x-origin to the left side of the border box.',
                          u'right': u'Sets the x-origin to the right side of the border box.',
                          u'top': u'Sets the y-origin to the top of the element\u2019s border box.'},
        'versions': [u'iPhone OS 2.0']},

    '-webkit-rtl-ordering':
{       'description': u'Overrides ordering defaults for right-to-left content.',
        'syntax': u'-webkit-rtl-ordering: order;',
        'values': {       u'logical': u'Raw content is in mixed order (requiring a bidirectional renderer).',
                          u'visual': u'Right-to-left content is encoded in reverse order so an entire line of text can be rendered from left to right in a unidirectional fashion.'},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-tap-highlight-color':
{       'description': u'Overrides the highlight color shown when the user taps a link or a JavaScript clickable element in Safari on iPhone.',
        'syntax': u'-webkit-tap-highlight-color: color;',
        'values': {       u'color': u'The tapped link color.'},
        'versions': [u'iPhone OS 1.1.1']},

    '-webkit-text-fill-color':
{       'description': u'Specifies a fill color for text.',
        'syntax': u'-webkit-text-fill-color: color;',
        'values': {       u'-webkit-activelink': u'The default color of a hyperlink that is being clicked.',
                          u'-webkit-focus-ring-color': u'The color that surrounds a UI element, such as a text field, that has focus.',
                          u'-webkit-link': u'The default color of a hyperlink that has been visited.',
                          u'-webkit-text': u'The default text color.',
                          u'activeborder': '',
                          u'activecaption': '',
                          u'appworkspace': '',
                          u'aqua': '',
                          u'background': '',
                          u'black': '',
                          u'blue': '',
                          u'buttonface': '',
                          u'buttonhighlight': '',
                          u'buttonshadow': '',
                          u'buttontext': '',
                          u'captiontext': '',
                          u'currentcolor': u'(by default) The value of the element\u2019s color property.',
                          u'fuchsia': '',
                          u'gray': '',
                          u'graytext': '',
                          u'green': '',
                          u'grey': '',
                          u'highlight': '',
                          u'highlighttext': '',
                          u'inactiveborder': '',
                          u'inactivecaption': '',
                          u'inactivecaptiontext': '',
                          u'infobackground': '',
                          u'infotext': '',
                          u'lime': '',
                          u'maroon': '',
                          u'match': '',
                          u'menu': '',
                          u'menutext': '',
                          u'navy': '',
                          u'olive': '',
                          u'orange': '',
                          u'purple': '',
                          u'red': '',
                          u'scrollbar': '',
                          u'silver': '',
                          u'teal': '',
                          u'threeddarkshadow': '',
                          u'threedface': '',
                          u'threedhighlight': '',
                          u'threedlightshadow': '',
                          u'threedshadow': '',
                          u'transparent': '',
                          u'white': '',
                          u'window': '',
                          u'windowframe': '',
                          u'windowtext': '',
                          u'yellow': ''},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-text-security':
{       'description': u'Specifies the shape to use in place of letters in a password input field.',
        'syntax': u'-webkit-text-security: shape;',
        'values': {       u'circle': u'A circle shape.',
                          u'disc': u'A disc shape.',
                          u'none': u'No shape is used.',
                          u'square': u'A square shape.'},
        'versions': [u'Safari 3.0', u'iPhone OS 1.0']},

    '-webkit-text-size-adjust':
{       'description': u'Specifies a size adjustment for displaying text content in Safari on iPhone.',
        'syntax': u'-webkit-text-size-adjust: percentage;',
        'values': {       u'<percentage>': u'The size in percentage at which to display text in Safari on iPhone.',
                          u'auto': u'The text size is automatically adjusted for Safari on iPhone.',
                          u'none': u'(by default) The text size is not adjusted.'},
        'versions': [u'iPhone OS 1.0']},

    '-webkit-text-stroke':
{       'description': u'Specifies the width and color of the outline (stroke) of text.',
        'syntax': u'-webkit-text-stroke: width color;',
        'values': {       u'color': u'The color of the stroke.',
                          u'width': u'The width of the stroke.'},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-text-stroke-color':
{       'description': u'Specifies the color of the outline (stroke) of text.',
        'syntax': u'-webkit-text-stroke-color: color;',
        'values': {       u'-webkit-activelink': u'The default color of a hyperlink that is being clicked.',
                          u'-webkit-focus-ring-color': u'The color that surrounds a UI element, such as a text field, that has focus.',
                          u'-webkit-link': u'The default color of a hyperlink that has been visited.',
                          u'-webkit-text': u'The default text color.',
                          u'activeborder': '',
                          u'activecaption': '',
                          u'appworkspace': '',
                          u'aqua': '',
                          u'background': '',
                          u'black': '',
                          u'blue': '',
                          u'buttonface': '',
                          u'buttonhighlight': '',
                          u'buttonshadow': '',
                          u'buttontext': '',
                          u'captiontext': '',
                          u'currentcolor': u"(by default) The value of the element's color property.",
                          u'fuchsia': '',
                          u'gray': '',
                          u'graytext': '',
                          u'green': '',
                          u'grey': '',
                          u'highlight': '',
                          u'highlighttext': '',
                          u'inactiveborder': '',
                          u'inactivecaption': '',
                          u'inactivecaptiontext': '',
                          u'infobackground': '',
                          u'infotext': '',
                          u'lime': '',
                          u'maroon': '',
                          u'match': '',
                          u'menu': '',
                          u'menutext': '',
                          u'navy': '',
                          u'olive': '',
                          u'orange': '',
                          u'purple': '',
                          u'red': '',
                          u'scrollbar': '',
                          u'silver': '',
                          u'teal': '',
                          u'threeddarkshadow': '',
                          u'threedface': '',
                          u'threedhighlight': '',
                          u'threedlightshadow': '',
                          u'threedshadow': '',
                          u'transparent': '',
                          u'white': '',
                          u'window': '',
                          u'windowframe': '',
                          u'windowtext': '',
                          u'yellow': ''},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-text-stroke-width':
{       'description': u'Specifies the width for the text outline.',
        'syntax': u'-webkit-text-stroke-width: width;',
        'values': {       u'<width>': u'Length unit',
                          u'medium': u'A medium stroke.',
                          u'thick': u'A thick stroke.',
                          u'thin': u'A thin stroke.'},
        'versions': [u'Safari 3.0', u'iPhone OS 2.0']},

    '-webkit-touch-callout':
{       'description': u'Disables the default callout shown when you touch and hold a touch target.',
        'syntax': u'-webkit-touch-callout: behavior;',
        'values': {       u'inherit': '', u'none': ''},
        'versions': [u'iPhone OS 2.0']},

    '-webkit-transform':
{       'description': u'Specifies transformations to be applied to an element.',
        'syntax': u'-webkit-transform: function ... ;',
        'values': {       u'<function>': '',
                          u'none': u'(by default) No transforms are applied.'},
        'versions': [u'Safari 3.1', u'iPhone OS 2.0']},

    '-webkit-transform-origin':
{       'description': u'Sets the origin for the  -webkit-transform  property.',
        'syntax': u'-webkit-transform-origin: posx;',
        'values': {       u'50%': u'50% (by default) ',
                          u'bottom': '',
                          u'center': '',
                          u'left': '',
                          u'right': '',
                          u'top': ''},
        'versions': [u'Safari 3.1', u'iPhone OS 2.0']},

    '-webkit-transform-origin-x':
{       'description': u'The x coordinate of the origin for transforms applied to an element with respect to its border box.',
        'syntax': u'-webkit-transform-origin-x: posx;',
        'values': {       u'posx': u'The x origin as a percentage or value.'},
        'versions': [u'Safari 3.1', u'iPhone OS 2.0']},

    '-webkit-transform-origin-y':
{       'description': u'The y coordinate of the origin for transforms applied to an element with respect to its border box.',
        'syntax': u'-webkit-transform-origin-y: posy;',
        'values': {       u'posy': u'The y origin as a percentage or value.'},
        'versions': [u'Safari 3.1', u'iPhone OS 2.0']},

    '-webkit-transform-origin-z':
{       'description': u'The z coordinate of the origin for transforms applied to an element with respect to its border box.',
        'syntax': u'-webkit-transform-origin-z: posz;',
        'values': {       u'posz': u'The z origin as a percentage or value.'},
        'versions': [u'iPhone OS 2.0']},

    '-webkit-transform-style':
{       'description': u'Defines how nested, transformed elements are rendered in 3D space.',
        'syntax': u'-webkit-transform-style: style;',
        'values': {       u'flat': u'(by default) Flatten all children of this element into the 2D plane.',
                          u'preserve-3d': u'Preserve the 3D perspective.'},
        'versions': [u'iPhone OS 2.0']},

    '-webkit-transition':
{       'description': u'Combines  -webkit-transition-delay ,  -webkit-transition-duration ,  -webkit-transition-property , and  -webkit-transition-timing-function  into a single property.',
        'syntax': u'-webkit-transition: property duration timing_function delay [, ...];',
        'values': {       u'delay': u'Defines when the transition starts. See  -webkit-transition-delay .',
                          u'duration': u'Defines how long the transition from the old value to the new value should take. See  -webkit-transition-duration .',
                          u'property': u'Specifies the name of the CSS property to which the transition is applied. See  -webkit-transition-property .',
                          u'timing_function': u'Specifies how the intermediate values used during a transition are calculated. See  -webkit-transition-timing-function .'},
        'versions': [u'Safari 3.1', u'iPhone OS 2.0']},

    '-webkit-transition-delay':
{       'description': u'Defines when the transition starts.',
        'syntax': u'-webkit-transition-delay: time [, ...];',
        'values': {       u'0': u'(by default) ',
                          u'now': u'The transition begins immediately. Available in iPhone OS 2.0 and later.'},
        'versions': [u'Safari 4.0', u'iPhone OS 2.0']},

    '-webkit-transition-duration':
{       'description': u'Defines how long the transition from the old value to the new value should take.',
        'syntax': u'-webkit-transition-duration: time [, ...];',
        'values': {       u'0': u'(by default) '},
        'versions': [u'Safari 3.1', u'iPhone OS 2.0']},

    '-webkit-transition-property':
{       'description': u'Specifies the name of the CSS property to which the transition is applied.',
        'syntax': u'-webkit-transition-property: name;',
        'values': {       u'<name>': u'CSS property name',
                          u'all': u'(by default) The default transition name.',
                          u'none': u'No transition specified.'},
        'versions': [u'Safari 3.1', u'iPhone OS 2.0']},

    '-webkit-transition-timing-function':
{       'description': u'Specifies how the intermediate values used during a transition are calculated.',
        'syntax': u'-webkit-transition-timing-function: timing_function [, ...];',
        'values': {       u'<timing_function>': '',
                          u'ease': u'(by default) Equivalent to  cubic-bezier(0.25, 0.1, 0.25, 1.0)',
                          u'ease-in': u'Equivalent to  cubic-bezier(0.42, 0, 1.0, 1.0)',
                          u'ease-in-out': u'Equivalent to  cubic-bezier(0.42, 0, 0.58, 1.0)',
                          u'ease-out': u'Equivalent to  cubic-bezier(0, 0, 0.58, 1.0)',
                          u'linear': u'Equivalent to  cubic-bezier(0.0, 0.0, 1.0, 1.0)'},
        'versions': [u'Safari 3.1', u'iPhone OS 2.0']},

    '-webkit-user-drag':
{       'description': u'Specifies that an entire element should be draggable instead of its contents.',
        'syntax': u'-webkit-user-drag: behavior;',
        'values': {       u'auto': u'(by default) The default dragging behavior is used.',
                          u'element': u'The entire element is draggable instead of its contents.',
                          u'none': u'The element cannot be dragged at all.'},
        'versions': [u'Safari 3.0']},

    '-webkit-user-modify':
{       'description': u'Determines whether a user can edit the content of an element.',
        'syntax': u'-webkit-user-modify: policy;',
        'values': {       u'read-only': u'The content is read-only.',
                          u'read-write': u'The content can be read and written.',
                          u'read-write-plaintext-only': u'The content can be read and written, but any rich formatting of pasted text is lost.'},
        'versions': [u'Safari 3.0']},

    '-webkit-user-select':
{       'description': u'Determines whether a user can select the content of an element.',
        'syntax': u'-webkit-user-select: policy;',
        'values': {       u'auto': u'(by default) The user can select content in the element.',
                          u'none': u'The user cannot select any content.',
                          u'text': u'The user can select text in the element.'},
        'versions': [u'Safari 3.0', u'iPhone OS 3.0']},
}


### END: Auto generated




CSS_WEBKIT_SPECIFIC_ATTRS_DICT = {}
CSS_WEBKIT_SPECIFIC_CALLTIP_DICT = {}
for attr, details in CSS_WEBKIT_DATA.items():
    values = details.get("values", {})
    versions = details.get("versions", [])
    attr_completions = sorted(values.keys())
    if attr_completions:
        CSS_WEBKIT_SPECIFIC_ATTRS_DICT[attr] = attr_completions
    else:
        CSS_WEBKIT_SPECIFIC_ATTRS_DICT[attr] = None
    description = details.get("description", '')
    if versions:
        description += "\nVersions: %s\n" % (", ".join(versions))
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
        CSS_WEBKIT_SPECIFIC_CALLTIP_DICT[attr] = "\n".join(desc_lines).encode("ascii", 'replace')
