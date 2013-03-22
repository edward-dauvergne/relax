###############################################################################
#                                                                             #
# Copyright (C) 2003-2013 Edward d'Auvergne                                   #
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
"""The Pymol macro methods of the specific API for model-free analysis."""

# relax module imports.
from specific_analyses.model_free.macro_base import Macro


class Pymol(Macro):
    """Class containing the Pymol specific functions for model-free analysis."""

    def classic_colour(self, res_num=None, width=None, rgb_array=None):
        """Colour the given peptide bond."""

        # Blank line (to make the macro file easier to read for the user).
        self.commands.append("")

        # Define the colour.
        colour_name = 'pept_colour_%i' % res_num
        self.commands.append("set_color %s, [%s, %s, %s]" % (colour_name, rgb_array[0], rgb_array[1], rgb_array[2]))

        # The peptide bond.
        self.commands.append("select pept_bond, (name ca,n and resi %i) or (name ca,c and resi %i)" % (res_num, res_num-1))
        self.commands.append("as sticks, pept_bond")
        self.commands.append("set_bond stick_radius, %s, pept_bond" % width)
        self.commands.append("set_bond stick_color, %s, pept_bond" % colour_name)

        # Delete the selection.
        self.commands.append("delete pept_bond")


    def classic_header(self):
        """Create the header for the pymol macro."""

        # Hide all bonds.
        self.commands.append("hide")

        # Show the backbone bonds as lines.
        self.commands.append("select bb, (name ca,n,c)")
        self.commands.append("show lines, bb")

        # Colour the backbone black.
        self.commands.append("color black, bb")

        # Delete the selection.
        self.commands.append("delete bb")

        # Set the background colour to white.
        self.commands.append("bg_color white")


    def pymol_macro(self, data_type, style=None, colour_start=None, colour_end=None, colour_list=None, spin_id=None):
        """Wrapper method for the create_macro method.

        @param data_type:       The parameter name or data type.
        @type data_type:        str
        @keyword style:         The Molmol style.
        @type style:            None or str
        @keyword colour_start:  The starting colour (must be a MOLMOL or X11 name).
        @type colour_start:     str
        @keyword colour_end:    The ending colour (must be a MOLMOL or X11 name).
        @type colour_end:       str
        @keyword colour_list:   The colour list used, either 'molmol' or 'x11'.
        @type colour_list:      str
        @keyword spin_id:       The spin identification string.
        @type spin_id:          str
        """

        self.create_macro(data_type, style=style, colour_start=colour_start, colour_end=colour_end, colour_list=colour_list, spin_id=spin_id)
