###############################################################################
#                                                                             #
# Copyright (C) 2009-2012 Edward d'Auvergne                                   #
#                                                                             #
# This file is part of the program relax (http://www.nmr-relax.com).          #
#                                                                             #
# relax is free software; you can redistribute it and/or modify               #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation; either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# relax is distributed in the hope that it will be useful,                    #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with relax.  If not, see <http://www.gnu.org/licenses/>.              #
#                                                                             #
###############################################################################

# Python module imports.
from unittest import TestCase

# relax module imports.
from prompt.interpreter import Interpreter
from relax_errors import RelaxNoneStrError, RelaxNoneListNumError, RelaxNoneStrListNumError, RelaxStrError

# Unit test imports.
from data_types import DATA_TYPES


class Test_pymol(TestCase):
    """Unit tests for the functions of the 'prompt.pymol' module."""

    def __init__(self, methodName=None):
        """Set up the test case class for the system tests."""

        # Execute the base __init__ methods.
        super(Test_pymol, self).__init__(methodName)

        # Load the interpreter.
        self.interpreter = Interpreter(show_script=False, quit=False, raise_relax_error=True)
        self.interpreter.populate_self()
        self.interpreter.on(verbose=False)

        # Alias the user function class.
        self.pymol_fns = self.interpreter.pymol


    def test_macro_apply_argfail_data_type(self):
        """The data_type arg test of the pymol.macro_apply() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the str arguments, and skip them.
            if data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxStrError, self.pymol_fns.macro_apply, data_type=data[1])


    def test_macro_apply_argfail_style(self):
        """The style arg test of the pymol.macro_apply() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the str arguments, and skip them.
            if data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxStrError, self.pymol_fns.macro_apply, data_type='a', style=data[1])


    def test_macro_apply_argfail_colour_start_name(self):
        """The colour_start_name arg test of the pymol.macro_apply() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and str arguments, and skip them.
            if data[0] == 'None' or data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneStrError, self.pymol_fns.macro_apply, data_type='a', style='x', colour_start_name=data[1])


    def test_macro_apply_argfail_colour_start_rgb(self):
        """The colour_start_rgb arg test of the pymol.macro_apply() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and num list arguments, and skip them.
            if data[0] == 'None' or ((data[0] == 'int list' or data[0] == 'float list' or data[0] == 'number list') and len(data[1]) == 3):
                continue

            # The argument test.
            self.assertRaises(RelaxNoneListNumError, self.pymol_fns.macro_apply, data_type='a', style='x', colour_start_rgb=data[1])


    def test_macro_apply_argfail_colour_end_name(self):
        """The colour_end_name arg test of the pymol.macro_apply() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and str arguments, and skip them.
            if data[0] == 'None' or data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneStrError, self.pymol_fns.macro_apply, data_type='a', style='x', colour_end_name=data[1])


    def test_macro_apply_argfail_colour_end_rgb(self):
        """The colour_end_rgb arg test of the pymol.macro_apply() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and num list arguments, and skip them.
            if data[0] == 'None' or ((data[0] == 'int list' or data[0] == 'float list' or data[0] == 'number list') and len(data[1]) == 3):
                continue

            # The argument test.
            self.assertRaises(RelaxNoneListNumError, self.pymol_fns.macro_apply, data_type='a', style='x', colour_end_rgb=data[1])


    def test_macro_apply_argfail_colour_list(self):
        """The colour_list arg test of the pymol.macro_apply() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and str arguments, and skip them.
            if data[0] == 'None' or data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneStrError, self.pymol_fns.macro_apply, data_type='a', style='x', colour_list=data[1])
