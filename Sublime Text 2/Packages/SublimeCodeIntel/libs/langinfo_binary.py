# ***** BEGIN LICENSE BLOCK *****
# Version: MPL 1.1/GPL 2.0/LGPL 2.1
# 
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
# 
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
# License for the specific language governing rights and limitations
# under the License.
# 
# The Original Code is Komodo code.
# 
# The Initial Developer of the Original Code is ActiveState Software Inc.
# Portions created by ActiveState Software Inc are Copyright (C) 2000-2007
# ActiveState Software Inc. All Rights Reserved.
# 
# Contributor(s):
#   ActiveState Software Inc
# 
# Alternatively, the contents of this file may be used under the terms of
# either the GNU General Public License Version 2 or later (the "GPL"), or
# the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
# in which case the provisions of the GPL or the LGPL are applicable instead
# of those above. If you wish to allow use of your version of this file only
# under the terms of either the GPL or the LGPL, and not to allow others to
# use your version of this file under the terms of the MPL, indicate your
# decision by deleting the provisions above and replace them with the notice
# and other provisions required by the GPL or the LGPL. If you do not delete
# the provisions above, a recipient may use your version of this file under
# the terms of any one of the MPL, the GPL or the LGPL.
# 
# ***** END LICENSE BLOCK *****

"""LangInfo definitions for some binary file types."""

from langinfo import LangInfo



class ELFLangInfo(LangInfo):
    """ELF-format binary (e.g. a standard executable on Linux)"""
    name = "ELF"

    # From '/usr/share/file/magic':
    #   0	string		\177ELF		ELF
    magic_numbers = [(0, 'string', '\177ELF')]

class ArchiveLibLangInfo(LangInfo):
    """Archive library (ar)"""
    name = "ar"
    exts = [".a"]
    magic_numbers = [(0, 'string', '!<arch>')]

class MachOUniversalLangInfo(LangInfo):
    name = "Mach-O universal"

    # See '/usr/share/file/magic' for the full details on collision
    # between compiled Java class data and Mach-O universal binaries and
    # the hack to distinguish them.
    #   0	belong		0xcafebabe
    #TODO: check with a 64-bit Mach-O universal
    magic_numbers = [(0, '>L', int('0xcafebabe', 16))]

class MachOLangInfo(LangInfo):
    name = "Mach-O"

    # From '/usr/share/file/magic':
    #   0	lelong&0xfffffffe	0xfeedface	Mach-O
    #   0	belong&0xfffffffe	0xfeedface	Mach-O
    # Note: We are not current handling the '&0xfffffffe'.
    #
    #TODO: check with a 64-bit Mach-O
    magic_numbers = [(0, '<L', int('0xfeedface', 16)),
                     (0, '>L', int('0xfeedface', 16))]

class WindowsExeLangInfo(LangInfo):
    name = "Windows executable"
    exts = [".exe", ".dll"]

    # From '/usr/share/file/magic':
    #   0	string	MZ		MS-DOS executable (EXE)
    magic_numbers = [(0, "string", "MZ")]

class CompiledJavaClassLangInfo(LangInfo):
    name = "compiled Java class"
    exts = [".class"]
    # See MachOUniversalLangInfo above. There is a collision in the
    # magic number of Mach-O universal binaries and Java .class files.
    # For now we rely on the '.class' extension to properly identify
    # before magic number checking is done.
    magic_numbers = None

class ZipLangInfo(LangInfo):
    name = "Zip archive"
    exts = [".zip"]
    magic_numbers = [(0, "string", "PK\003\004")]

class GZipLangInfo(LangInfo):
    name = "gzip archive"
    exts = [".gz", ".tgz"]
    magic_numbers = [(0, "string", "\037\213")]

class BZip2LangInfo(LangInfo):
    name = "bzip2 compressed data"
    exts = [".bz2"]
    magic_numbers = [(0, "string", "BZh")]

class MSILangInfo(LangInfo):
    """Microsoft Installer Package"""
    name = "MSI"
    exts = [".msi"]

class JarLangInfo(ZipLangInfo):
    name = "Jar archive"
    exts = [".jar"]

class IcoLangInfo(LangInfo):
    name = "Windows icon"
    exts = [".ico"]

class IcnsLangInfo(LangInfo):
    name = "Mac icon"
    exts = [".icns"]

class XPMLangInfo(LangInfo):
    name = "XPM"
    exts = [".xpm"]
    magic_numbers = [(0, "string", "/* XPM */")]

class PSDLangInfo(LangInfo):
    name = "Adobe Photoshop Document"
    exts = [".psd"]
    magic_numbers = [(0, "string", "8BPS")]

class PNGLangInfo(LangInfo):
    name = "PNG"
    exts = [".png"]
    magic_numbers = [(0, "string", "\x89PNG")]

class GIFLangInfo(LangInfo):
    name = "GIF"
    exts = [".gif"]
    magic_numbers = [(0, "string", "GIF8")]

class JPEGLangInfo(LangInfo):
    name = "JPEG"
    exts = [".jpg", ".jpeg"]
    # From '/usr/share/file/magic':
    #   0	beshort		0xffd8		JPEG image data
    magic_numbers = [(0, ">H", int("0xffd8", 16))]

class BMPLangInfo(LangInfo):
    name = "Bitmap image"
    exts = [".bmp"]
    magic_numbers = [(0, "string", "BM")]

class TIFFLangInfo(LangInfo):
    """TIFF image format"""
    name = "TIFF"
    exts = [".tiff", ".tif"]
    magic_numbers = [
        (0, "string", "MM\x00\x2a"), # TIFF image data, big-endian
        (0, "string", "II\x2a\x00"), # TIFF image data, little-endian
    ]

class DSStoreLangInfo(LangInfo):
    """Mac OS X filesystem directory metadata files."""
    name = "DSStore"
    filename_patterns = [".DS_Store"]

class BOMLangInfo(LangInfo):
    """Mac OS X/BSD 'Bill of Materials' file."""
    name = "BOM"
    exts = [".bom"]
    magic_numbers = [(0, "string", "BOMStore")]

class PDFLangInfo(LangInfo):
    name = "PDF"
    exts = [".pdf"]

class RIFFLangInfo(LangInfo):
    """Resource Interchange File Format -- a generic meta-format for
    storing data in tagged chunks.

    http://en.wikipedia.org/wiki/RIFF_(File_format)
    """
    name = "RIFF"
    magic_numbers = [
        (0, "string", "RIFX"),  # RIFF (big-endian) data
        (0, "string", "RIFF"),  # RIFF (little-endian) data
    ]

class WAVLangInfo(LangInfo):
    """Waveform (WAVE) Audio format"""
    name = "WAV"
    conforms_to_bases = ["RIFF"]
    exts = [".wav"]

class AVILangInfo(LangInfo):
    """Audio Video Interleave"""
    name = "AVI"
    conforms_to_bases = ["RIFF"]
    exts = [".avi"]


class MacHelpIndexLangInfo(LangInfo):
    """Mac OS X Help Index"""
    name = "Mac Help Index"
    exts = [".helpindex"]

class AppleBinaryPListLangInfo(LangInfo):
    name = "Apple Binary Property List"
    magic_numbers = [(0, "string", "bplist00")]

class MacOSXDiskImageLangInfo(LangInfo):
    name = "Mac OS X Disk Image"
    exts = [".dmg"]

class OggLangInfo(LangInfo):
    name = "Ogg data"
    exts = [".ogg"]
    magic_numbers = [(0, "string", "OggS")]

class FlashVideoLangInfo(LangInfo):
    """Macromedia Flash FLV Video File Format
   
    http://www.digitalpreservation.gov/formats/fdd/fdd000131.shtml
    """
    name = "Flash Video"
    exts = [".flv"]
    magic_numbers = [(0, "string", "FLV")]

class FlashSWFLangInfo(LangInfo):
    """Macromedia Flash SWF File Format
    
    http://www.digitalpreservation.gov/formats/fdd/fdd000248.shtml
    """
    name = "Flash SWF"
    exts = [".swf"]
    magic_numbers = [
        (0, "string", "FWS"),   # uncompressed
        (0, "string", "CWS"),   # compressed
    ]

class MP3LangInfo(LangInfo):
    """MPEG 1.0 Layer 3 audio encoding"""
    name = "MP3"
    exts = [".mp3"]
    magic_numbers = [
        (0, "string", "ID3"),  # MP3 file with ID3 version 2.
    ]

class MPEGLangInfo(LangInfo):
    """MPEG video"""
    name = "MPEG"
    exts = [".mpg", ".mpeg"]
    magic_numbers = [
        (0, '>L', int('0x000001b3', 16)),   # belong; MPEG video stream data
        (0, '>L', int('0x000001ba', 16)),   # belong; MPEG system stream data
    ]

class AACLangInfo(LangInfo):
    """MPEG-4 Advanced Audio Coding file"""
    name = "AAC"
    exts = [".m4a"]
    magic_numbers = [
        (16, "string", "M4A"),
    ]

class QuickTimeMovieLangInfo(LangInfo):
    """Apple QuickTime movie"""
    name = "QuickTime Movie"
    exts = [".mov"]
    # Note: Excluding these checks as an optimization and to avoid possible
    # false positives.
    #magic_numbers = [
    #    (4, "string", "moov"),
    #    (4, "string", "mdat"),
    #    (4, "string", "ftyp"),
    #    (4, "string", "free"),
    #    (4, "string", "junk"),
    #    (4, "string", "pnot"),
    #    (4, "string", "skip"),
    #    (4, "string", "wide"),
    #    (4, "string", "pict"),
    #]

class WindowsThumbnailCacheLangInfo(LangInfo):
    """Microsoft Windows directory thumbnail cache."""
    name = "Windows thumbnail cache"
    filename_patterns = ["Thumbs.db"]


class GettextMOLangInfo(LangInfo):
    """GNU Gettext message catalog

    http://www.gnu.org/software/gettext/manual/gettext.html#MO-Files
    """
    name = "GNU message catalog"
    exts = [".mo"]
    magic_numbers = [
        (0, "string", "\336\22\4\225"), # GNU message catalog (little endian)
        (0, "string", "\225\4\22\336"), # GNU message catalog (big endian),
    ]


class MSOfficeDocumentLangInfo(LangInfo):
    name = "MS Office Document"
    magic_numbers = [
        (0, "string", "\376\067\0\043"),
        (0, "string", "\320\317\021\340\241\261\032\341"),
        (0, "string", "\333\245-\0\0\0"),
    ]

class ExcelDocumentLangInfo(MSOfficeDocumentLangInfo):
    name = "MS Excel Document"
    exts = [".xls"]

class MSWordDocumentLangInfo(MSOfficeDocumentLangInfo):
    name = "MS Word Document"
    #TODO: consider extended 'specialization' facility to look at ext as well.
    # Can cause false positives for, e.g., a text document that uses '.doc'.
    #exts = [".doc"]


