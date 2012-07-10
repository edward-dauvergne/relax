###############################################################################
#                                                                             #
# Copyright (C) 2003-2012 Edward d'Auvergne                                   #
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
"""The module containing the base class for the model-free macros."""

# Python module imports.
from math import pi
from re import search

# relax module imports.
from colour import linear_gradient
from generic_fns.mol_res_spin import spin_loop
from relax_errors import RelaxError, RelaxFault, RelaxStyleError, RelaxUnknownDataTypeError
from user_functions.data import Uf_tables; uf_tables = Uf_tables()
from user_functions.objects import Desc_container



class Macro:
    """The base class for the model-free analysis Molmol and PyMOL macro creation."""

    classic_style_doc = Desc_container("Model-free classic style")
    classic_style_doc.add_paragraph("Creator:  Edward d'Auvergne")
    classic_style_doc.add_paragraph("Argument string:  \"classic\"")
    classic_style_doc.add_paragraph("Description:  The classic style draws the backbone of a protein in a cylindrical bond style.  Rather than colouring the amino acids to which the NH bond belongs, the three covalent bonds of the peptide bond from Ca to Ca in which the NH bond is located are coloured.  Deselected residues are shown as black lines.")
    classic_style_doc.add_paragraph("Supported data types:")
    table = uf_tables.add_table(label="table: model-free macro classic style", caption="The model-free classic style for mapping model spin specific data onto 3D molecular structures using either PyMOL or Molmol.", caption_short="The model-free classic style for PyMOL and Molmol data mapping.")
    table.add_headings(["Data type", "String", "Description"])
    table.add_row(["S2.", "'s2'", "The standard model-free order parameter, equal to S2f.S2s for the two timescale models.  The default colour gradient starts at 'yellow' and ends at 'red'."])
    table.add_row(["S2f.", "'s2f'", "The order parameter of the faster of two internal motions.  Residues which are described by model-free models m1 to m4, the single timescale models, are illustrated as white neon bonds.  The default colour gradient is the same as that for the S2 data type."])
    table.add_row(["S2s.", "'s2s'", "The order parameter of the slower of two internal motions.  This functions exactly as S2f except that S2s is plotted instead."])
    table.add_row(["Amplitude of fast motions.", "'amp_fast'", "Model independent display of the amplite of fast motions.  For residues described by model-free models m5 to m8, the value plotted is that of S2f.  However, for residues described by models m1 to m4, what is shown is dependent on the timescale of the motions.  This is because these single timescale models can, at times, be perfect approximations to the more complex two timescale models.  Hence if te is less than 200 ps, S2 is plotted.  Otherwise the peptide bond is coloured white.  The default colour gradient  is the same as that for S2."])
    table.add_row(["Amplitude of slow motions.", "'amp_slow'", "Model independent display of the amplite of slow motions, arbitrarily defined as motions slower than 200 ps.  For residues described by model-free models m5 to m8, the order parameter S2 is plotted if ts > 200 ps.  For models m1 to m4, S2 is plotted if te > 200 ps.  The default colour gradient is the same as that for S2."])
    table.add_row(["te.", "'te'", "The correlation time, te.  The default colour gradient starts at 'turquoise' and ends at 'blue'."])
    table.add_row(["tf.", "'tf'", "The correlation time, tf.  The default colour gradient is the same as that of te."])
    table.add_row(["ts.", "'ts'", "The correlation time, ts.  The default colour gradient starts at 'blue' and ends at 'black'."])
    table.add_row(["Timescale of fast motions", "'time_fast'", "Model independent display of the timescale of fast motions.  For models m5 to m8, only the parameter tf is plotted.  For models m2 and m4, the parameter te is plotted only if it is less than 200 ps.  All other residues are assumed to have a correlation time of zero.  The default colour gradient is the same as that of te."])
    table.add_row(["Timescale of slow motions", "'time_slow'", "Model independent display of the timescale of slow motions.  For models m5 to m8, only the parameter ts is plotted.  For models m2 and m4, the parameter te is plotted only if it is greater than 200 ps.  All other residues are coloured white.  The default colour gradient is the same as that of ts."])
    table.add_row(["Chemical exchange", "'rex'", "The chemical exchange, Rex.  Residues which experience no chemical exchange are coloured white.  The default colour gradient starts at 'yellow' and finishes at 'red'."])
    classic_style_doc.add_table(table.label)

    def classic_style(self, data_type=None, colour_start=None, colour_end=None, colour_list=None, spin_id=None):
        """The classic macro style.

        @keyword data_type:     The parameter name or data type.
        @type data_type:        str
        @keyword colour_start:  The starting colour (must be a MOLMOL or X11 name).
        @type colour_start:     str
        @keyword colour_end:    The ending colour (must be a MOLMOL or X11 name).
        @type colour_end:       str
        @keyword colour_list:   The colour list used, either 'molmol' or 'x11'.
        @type colour_list:      str
        @keyword spin_id:       The spin identification string.
        @type spin_id:          str
        """

        # Test the validity of the data (only a single spin per residue).
        #################################################################

        # Init some variables.
        prev_res_num = None
        num = 0

        # Loop over the spins.
        for spin, mol_name, res_num, res_name in spin_loop(spin_id, full_info=True):
            # No relaxation data, so skip.
            if not hasattr(spin, 'ri_data'):
                continue

            # More than one spin.
            if prev_res_num == res_num:
                raise RelaxError("Only a single spin per residue is allowed for the classic macro style.")

            # Update the previous residue number.
            prev_res_num = res_num


        # Generate the macro header.
        ############################

        self.classic_header()


        # S2.
        #####

        if data_type == 's2':
            # Loop over the spins.
            for spin, mol_name, res_num, res_name in spin_loop(spin_id, full_info=True):
                # Skip deselected spins.
                if not spin.select:
                    continue

                # Skip spins which don't have an S2 value.
                if not hasattr(spin, 's2') or spin.s2 == None:
                    continue

                # S2 width and colour.
                self.classic_order_param(res_num, spin.s2, colour_start, colour_end, colour_list)


        # S2f.
        ######

        elif data_type == 's2f':
            # Loop over the spins.
            for spin, mol_name, res_num, res_name in spin_loop(spin_id, full_info=True):
                # Skip deselected spins.
                if not spin.select:
                    continue

                # Colour residues which don't have an S2f value white.
                if not hasattr(spin, 's2f') or spin.s2f == None:
                    self.classic_colour(res_num=res_num, width=0.3, rgb_array=[1, 1, 1])

                # S2f width and colour.
                else:
                    self.classic_order_param(res_num, spin.s2f, colour_start, colour_end, colour_list)


        # S2s.
        ######

        elif data_type == 's2s':
            # Loop over the spins.
            for spin, mol_name, res_num, res_name in spin_loop(spin_id, full_info=True):
                # Skip deselected spins.
                if not spin.select:
                    continue

                # Colour residues which don't have an S2s value white.
                if not hasattr(spin, 's2s') or spin.s2s == None:
                    self.classic_colour(res_num=res_num, width=0.3, rgb_array=[1, 1, 1])

                # S2s width and colour.
                else:
                    self.classic_order_param(res_num, spin.s2s, colour_start, colour_end, colour_list)


        # Amplitude of fast motions.
        ############################

        elif data_type == 'amp_fast':
            # Loop over the spins.
            for spin, mol_name, res_num, res_name in spin_loop(spin_id, full_info=True):
                # Skip deselected spins.
                if not spin.select:
                    continue

                # The model.
                if search('tm[0-9]', spin.model):
                    model = spin.model[1:]
                else:
                    model = spin.model

                # S2f width and colour (for models m5 to m8).
                if hasattr(spin, 's2f') and spin.s2f != None:
                    self.classic_order_param(res_num, spin.s2f, colour_start, colour_end, colour_list)

                # S2 width and colour (for models m1 and m3).
                elif model == 'm1' or model == 'm3':
                    self.classic_order_param(res_num, spin.s2, colour_start, colour_end, colour_list)

                # S2 width and colour (for models m2 and m4 when te <= 200 ps).
                elif (model == 'm2' or model == 'm4') and spin.te <= 200e-12:
                    self.classic_order_param(res_num, spin.s2, colour_start, colour_end, colour_list)

                # White bonds (for models m2 and m4 when te > 200 ps).
                elif (model == 'm2' or model == 'm4') and spin.te > 200e-12:
                    self.classic_colour(res_num=res_num, width=0.3, rgb_array=[1, 1, 1])

                # Catch errors.
                else:
                    raise RelaxFault


        # Amplitude of slow motions.
        ############################

        elif data_type == 'amp_slow':
            # Loop over the spins.
            for spin, mol_name, res_num, res_name in spin_loop(spin_id, full_info=True):
                # Skip deselected spins.
                if not spin.select:
                    continue

                # The model.
                if search('tm[0-9]', spin.model):
                    model = spin.model[1:]
                else:
                    model = spin.model

                # S2 width and colour (for models m5 to m8).
                if hasattr(spin, 'ts') and spin.ts != None:
                    self.classic_order_param(res_num, spin.s2, colour_start, colour_end, colour_list)

                # S2 width and colour (for models m2 and m4 when te > 200 ps).
                elif (model == 'm2' or model == 'm4') and spin.te > 200 * 1e-12:
                    self.classic_order_param(res_num, spin.s2, colour_start, colour_end, colour_list)

                # White bonds for fast motions.
                else:
                    self.classic_colour(res_num=res_num, width=0.3, rgb_array=[1, 1, 1])

        # te.
        #####

        elif data_type == 'te':
            # Loop over the spins.
            for spin, mol_name, res_num, res_name in spin_loop(spin_id, full_info=True):
                # Skip deselected spins.
                if not spin.select:
                    continue

                # Skip spins which don't have a te value.
                if not hasattr(spin, 'te') or spin.te == None:
                    continue

                # te width and colour.
                self.classic_correlation_time(res_num, spin.te, colour_start, colour_end, colour_list)


        # tf.
        #####

        elif data_type == 'tf':
            # Loop over the spins.
            for spin, mol_name, res_num, res_name in spin_loop(spin_id, full_info=True):
                # Skip deselected spins.
                if not spin.select:
                    continue

                # Skip spins which don't have a tf value.
                if not hasattr(spin, 'tf') or spin.tf == None:
                    continue

                # tf width and colour.
                self.classic_correlation_time(res_num, spin.tf, colour_start, colour_end, colour_list)


        # ts.
        #####

        elif data_type == 'ts':
            # Loop over the spins.
            for spin, mol_name, res_num, res_name in spin_loop(spin_id, full_info=True):
                # Skip deselected spins.
                if not spin.select:
                    continue

                # Skip spins which don't have a ts value.
                if not hasattr(spin, 'ts') or spin.ts == None:
                    continue

                # The default start and end colours.
                if colour_start == None:
                    colour_start = 'blue'
                if colour_end == None:
                    colour_end = 'black'

                # ts width and colour.
                self.classic_correlation_time(res_num, spin.ts / 10.0, colour_start, colour_end, colour_list)


        # Timescale of fast motions.
        ############################

        elif data_type == 'time_fast':
            # Loop over the spins.
            for spin, mol_name, res_num, res_name in spin_loop(spin_id, full_info=True):
                # Skip deselected spins.
                if not spin.select:
                    continue

                # The model.
                if search('tm[0-9]', spin.model):
                    model = spin.model[1:]
                else:
                    model = spin.model

                # tf width and colour (for models m5 to m8).
                if hasattr(spin, 'tf') and spin.tf != None:
                    self.classic_correlation_time(res_num, spin.tf, colour_start, colour_end, colour_list)

                # te width and colour (for models m2 and m4 when te <= 200 ps).
                elif (model == 'm2' or model == 'm4') and spin.te <= 200e-12:
                    self.classic_correlation_time(res_num, spin.te, colour_start, colour_end, colour_list)

                # All other residues are assumed to have a fast correlation time of zero (statistically zero, not real zero!).
                # Colour these bonds white.
                else:
                    self.classic_colour(res_num=res_num, width=0.3, rgb_array=[1, 1, 1])


        # Timescale of slow motions.
        ############################

        elif data_type == 'time_slow':
            # Loop over the spins.
            for spin, mol_name, res_num, res_name in spin_loop(spin_id, full_info=True):
                # Skip deselected spins.
                if not spin.select:
                    continue

                # The model.
                if search('tm[0-9]', spin.model):
                    model = spin.model[1:]
                else:
                    model = spin.model

                # The default start and end colours.
                if colour_start == None:
                    colour_start = 'blue'
                if colour_end == None:
                    colour_end = 'black'

                # ts width and colour (for models m5 to m8).
                if hasattr(spin, 'ts') and spin.ts != None:
                    self.classic_correlation_time(res_num, spin.ts / 10.0, colour_start, colour_end, colour_list)

                # te width and colour (for models m2 and m4 when te > 200 ps).
                elif (model == 'm2' or model == 'm4') and spin.te > 200e-12:
                    self.classic_correlation_time(res_num, spin.te / 10.0, colour_start, colour_end, colour_list)

                # White bonds for the rest.
                else:
                    self.classic_colour(res_num=res_num, width=0.3, rgb_array=[1, 1, 1])


        # Rex.
        ######

        elif data_type == 'rex':
            # Loop over the spins.
            for spin, mol_name, res_num, res_name in spin_loop(spin_id, full_info=True):
                # Skip deselected spins.
                if not spin.select:
                    continue

                # Residues which chemical exchange.
                if hasattr(spin, 'rex') and spin.rex != None:
                    self.classic_rex(res_num, spin.rex, colour_start, colour_end, colour_list)

                # White bonds for the rest.
                else:
                    self.classic_colour(res_num=res_num, width=0.3, rgb_array=[1, 1, 1])


        # Unknown data type.
        ####################

        else:
            raise RelaxUnknownDataTypeError(data_type)


    def classic_correlation_time(self, res_num, te, colour_start, colour_end, colour_list):
        """Function for generating the bond width and colours for correlation times."""

        # The te value in picoseconds.
        te = te * 1e12

        # The bond width (aiming for a width range of 2 to 0 for te values of 0 to 10 ns).
        width = 2.0 - 200.0 / (te + 100.0)

        # Catch invalid widths.
        if width <= 0.0:
            width = 0.001

        # Colour value (hyperbolic).
        colour_value = 1.0 / (te / 100.0 + 1.0)

        # Catch invalid colours.
        if colour_value < 0.0:
            colour_value = 0.0
        elif colour_value > 1.0:
            colour_value = 1.0

        # Default colours.
        if colour_start == None:
            colour_start = 'turquoise'
        if colour_end == None:
            colour_end = 'blue'

        # Get the RGB colour array (swap the colours because of the inverted hyperbolic colour value).
        rgb_array = linear_gradient(colour_value, colour_end, colour_start, colour_list)

        # Colour the peptide bond.
        self.classic_colour(res_num, width, rgb_array)


    def classic_order_param(self, res_num, s2, colour_start, colour_end, colour_list):
        """Function for generating the bond width and colours for order parameters."""

        # The bond width (aiming for a width range of 2 to 0 for S2 values of 0.0 to 1.0).
        if s2 <= 0.0:
            width = 2.0
        else:
            width = 2.0 * (1.0 - s2**2)

        # Catch invalid widths.
        if width <= 0.0:
            width = 0.001

        # Colour value (quartic).
        colour_value = s2 ** 4

        # Catch invalid colours.
        if colour_value < 0.0:
            colour_value = 0.0
        elif colour_value > 1.0:
            colour_value = 1.0

        # Default colours.
        if colour_start == None:
            colour_start = 'red'
        if colour_end == None:
            colour_end = 'yellow'

        # Get the RGB colour array.
        rgb_array = linear_gradient(colour_value, colour_start, colour_end, colour_list)

        # Colour the peptide bond.
        self.classic_colour(res_num, width, rgb_array)


    def classic_rex(self, res_num, rex, colour_start, colour_end, colour_list):
        """Function for generating the bond width and colours for correlation times."""

        # The Rex value at the first field strength.
        rex = rex * (2.0 * pi * cdp.frq[cdp.ri_ids[0]])**2

        # The bond width (aiming for a width range of 2 to 0 for Rex values of 0 to 25 s^-1).
        width = 2.0 - 2.0 / (rex/5.0 + 1.0)

        # Catch invalid widths.
        if width <= 0.0:
            width = 0.001

        # Colour value (hyperbolic).
        colour_value = 1.0 / (rex + 1.0)

        # Catch invalid colours.
        if colour_value < 0.0:
            colour_value = 0.0
        elif colour_value > 1.0:
            colour_value = 1.0

        # Default colours.
        if colour_start == None:
            colour_start = 'yellow'
        if colour_end == None:
            colour_end = 'red'

        # Get the RGB colour array (swap the colours because of the inverted hyperbolic colour value).
        rgb_array = linear_gradient(colour_value, colour_end, colour_start, colour_list)

        # Colour the peptide bond.
        self.classic_colour(res_num, width, rgb_array)


    def create_macro(self, data_type, style=None, colour_start=None, colour_end=None, colour_list=None, spin_id=None):
        """Create and return an array of macros of the model-free parameters.

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

        # Initialise.
        self.commands = []

        # The classic style.
        if style == 'classic':
            self.classic_style(data_type, colour_start, colour_end, colour_list, spin_id)

        # Unknown style.
        else:
            raise RelaxStyleError(style)

        # Return the command array.
        return self.commands
