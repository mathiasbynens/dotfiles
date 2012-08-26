"""
Microsoft CSS extensions.
"""

import textwrap

### START: Auto generated

CSS_MICROSOFT_DATA = {
    '-ms-accelerator': {
        'description': "Extension",
    },
    '-ms-background-position-x': {
        'description': "CSS3 - Working Draft",
    },
    '-ms-background-position-y': {
        'description': "CSS3 - Working Draft",
    },
    '-ms-behavior': {
        'description': "Extension",
    },
    '-ms-block-progression': {
        'description': "CSS3 - Editor's Draft",
    },
    '-ms-filter': {
        'description': "Extension - Sets or retrieves the filter or collection of filters applied to the object.",
        'values': {
            'progid:DXImageTransform.Microsoft.Alpha': "Adjusts the opacity of the content of the object.",
            'progid:DXImageTransform.Microsoft.BasicImage': "Adjusts the color processing, image rotation, or opacity of the content of the object.",
            'progid:DXImageTransform.Microsoft.Blur': "Blurs the content of the object so that it appears out of focus.",
            'progid:DXImageTransform.Microsoft.Chroma': "Displays a specific color of the content of the object as transparent.",
            'progid:DXImageTransform.Microsoft.Compositor': "Displays new content of the object as a logical color combination of the new and original content. The color and alpha values of each version of the content are evaluated to determine the final color on the output image.",
            'progid:DXImageTransform.Microsoft.DropShadow': "Creates a solid silhouette of the content of the object, offset in the specified direction. This creates the illusion that the content is floating and casting a shadow.",
            'progid:DXImageTransform.Microsoft.Emboss': "Displays the content of the object as an embossed texture using grayscale values.",
            'progid:DXImageTransform.Microsoft.Engrave': "Displays the content of the object as an engraved texture using grayscale values.",
            'progid:DXImageTransform.Microsoft.Glow': "Adds radiance around the outside edges of the content of the object so that it appears to glow.",
            'progid:DXImageTransform.Microsoft.ICMFilter': "Converts the color content of the object based on an Image Color Management (ICM) profile. This enables improved display of specific content, or simulated display for hardware devices, such as printers or monitors.",
            'progid:DXImageTransform.Microsoft.Light': "Creates the effect of a light shining on the content of the object.",
            'progid:DXImageTransform.Microsoft.MaskFilter': "Displays transparent pixels of the object content as a color mask, and makes the nontransparent pixels transparent.",
            'progid:DXImageTransform.Microsoft.Matrix': "Resizes, rotates, or reverses the content of the object using matrix transformation.",
            'progid:DXImageTransform.Microsoft.MotionBlur': "Causes the content of the object to appear to be in motion.",
            'progid:DXImageTransform.Microsoft.Shadow': "Creates a solid silhouette of the content of the object, offset in the specified direction. This creates the illusion of a shadow.",
            'progid:DXImageTransform.Microsoft.Wave': "Performs a sine wave distortion of the content of the object  along the vertical axis.",
        }
    },
    '-ms-ime-mode': {
        'description': "Extension",
    },
    '-ms-layout-grid': {
        'description': "CSS3 - Editor's Draft",
    },
    '-ms-layout-grid-char': {
        'description': "CSS3 - Editor's Draft",
    },
    '-ms-layout-grid-line': {
        'description': "CSS3 - Editor's Draft",
    },
    '-ms-layout-grid-mode': {
        'description': "CSS3 - Editor's Draft",
    },
    '-ms-layout-grid-type': {
        'description': "CSS3 - Editor's Draft",
    },
    '-ms-line-break': {
        'description': "CSS3 - Working Draft",
    },
    '-ms-line-grid-mode': {
        'description': "CSS3 - Editor's Draft",
    },
    '-ms-interpolation-mode': {
        'description': "Extension",
    },
    '-ms-overflow-x': {
        'description': "CSS3 - Working Draft",
    },
    '-ms-overflow-y': {
        'description': "CSS3 - Working Draft",
    },
    '-ms-scrollbar-3dlight-color': {
        'description': "Extension",
    },
    '-ms-scrollbar-arrow-color': {
        'description': "Extension",
    },
    '-ms-scrollbar-base-color': {
        'description': "Extension",
    },
    '-ms-scrollbar-darkshadow-color': {
        'description': "Extension",
    },
    '-ms-scrollbar-face-color': {
        'description': "Extension",
    },
    '-ms-scrollbar-highlight-color': {
        'description': "Extension",
    },
    '-ms-scrollbar-shadow-color': {
        'description': "Extension",
    },
    '-ms-scrollbar-track-color': {
        'description': "Extension",
    },
    '-ms-text-align-last': {
        'description': "CSS3 - Working Draft",
    },
    '-ms-text-autospace': {
        'description': "CSS3 - Working Draft",
    },
    '-ms-text-justify': {
        'description': "CSS3 - Working Draft",
    },
    '-ms-text-kashida-space': {
        'description': "CSS3 - Working Draft",
    },
    '-ms-text-overflow': {
        'description': "CSS3 - Working Draft",
    },
    '-ms-text-underline-position': {
        'description': "Extension",
    },
    '-ms-word-break': {
        'description': "CSS3 - Working Draft",
    },
    '-ms-word-wrap': {
        'description': "CSS3 - Working Draft",
    },
    '-ms-writing-mode': {
        'description': "CSS3 - Editor's Draft",
    },
    '-ms-zoom': {
        'description': "Extension",
    },
}

### END: Auto generated




CSS_MICROSOFT_SPECIFIC_ATTRS_DICT = {}
CSS_MICROSOFT_SPECIFIC_CALLTIP_DICT = {}
for attr, details in CSS_MICROSOFT_DATA.items():
    values = details.get("values", {})
    versions = details.get("versions", [])
    attr_completions = sorted(values.keys())
    if attr_completions:
        CSS_MICROSOFT_SPECIFIC_ATTRS_DICT[attr] = attr_completions
    else:
        CSS_MICROSOFT_SPECIFIC_ATTRS_DICT[attr] = None
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
        CSS_MICROSOFT_SPECIFIC_CALLTIP_DICT[attr] = "\n".join(desc_lines).encode("ascii", 'replace')
