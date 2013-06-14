###############################################################################
#                                                                             #
# Copyright (C) 2011-2013 Edward d'Auvergne                                   #
#                                                                             #
# This file is part of the program relax (http://www.nmr-relax.com).          #
#                                                                             #
# This program is free software: you can redistribute it and/or modify        #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation, either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# This program is distributed in the hope that it will be useful,             #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.       #
#                                                                             #
###############################################################################

# Module docstring.
"""A standard set of font definitions for consistency throughout the GUI."""

# Python module imports.
import wx

# relax module imports.
from status import Status; status = Status()


class Font:
    """A storage container for the fonts."""

    def setup(self):
        """To be called by the main wx app, so that the fonts can be initialised correctly."""

        # Operating system dependent font scaling.
        scale = 0
        if status.wx_info["os"] == 'darwin':
            scale = 2

        # The fonts.
        self.smaller =              wx.Font(6+scale,  wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, "Sans")
        self.small =                wx.Font(8+scale,  wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, "Sans")
        self.button =               wx.Font(8+scale,  wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, "Sans")
        self.normal =               wx.Font(10+scale, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, "Sans")
        self.normal_bold =          wx.Font(10+scale, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD,   0, "Sans")
        self.normal_italic =        wx.Font(10+scale, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL, 0, "Sans")
        self.subtitle =             wx.Font(12+scale, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD,   0, "Sans")
        self.font_14 =              wx.Font(14+scale, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, "Sans")
        self.title =                wx.Font(16+scale, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0, "Sans")

        # Modern fixed-width fonts.
        self.modern_small =         wx.Font(8+scale,  wx.FONTFAMILY_MODERN,  wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0)
        self.modern_small_bold =    wx.Font(8+scale,  wx.FONTFAMILY_MODERN,  wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD,   0)
        self.modern_normal =        wx.Font(10+scale, wx.FONTFAMILY_MODERN,  wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0)
        self.modern_normal_bold =   wx.Font(10+scale, wx.FONTFAMILY_MODERN,  wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD,   0)

        # Roman fonts.
        self.roman_smaller =        wx.Font(6+scale,  wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0)
        self.roman_small =          wx.Font(8+scale,  wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0)
        self.roman_button =         wx.Font(8+scale,  wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0)
        self.roman_normal =         wx.Font(10+scale, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0)
        self.roman_normal_bold =    wx.Font(10+scale, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD,   0)
        self.roman_normal_italic =  wx.Font(10+scale, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL, 0)
        self.roman_subtitle =       wx.Font(12+scale, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD,   0)
        self.roman_font_12 =        wx.Font(12+scale, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0)
        self.roman_font_14 =        wx.Font(14+scale, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0)
        self.roman_title =          wx.Font(16+scale, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0)
        self.roman_title_italic =   wx.Font(16+scale, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_NORMAL, 0)
        self.roman_font_18 =        wx.Font(18+scale, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL, 0)


# Initialise the class for importing.
font = Font()
