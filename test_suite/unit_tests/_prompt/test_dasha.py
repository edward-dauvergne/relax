###############################################################################
#                                                                             #
# Copyright (C) 2008-2014 Edward d'Auvergne                                   #
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

# Python module imports.
from unittest import TestCase

# relax module imports.
from prompt.interpreter import Interpreter
from lib.errors import RelaxBoolError, RelaxNoneStrError, RelaxStrError

# Unit test imports.
from test_suite.unit_tests._prompt.data_types import DATA_TYPES


class Test_dasha(TestCase):
    """Unit tests for the functions of the 'prompt.dasha' module."""

    def __init__(self, methodName=None):
        """Set up the test case class for the system tests."""

        # Execute the base __init__ methods.
        super(Test_dasha, self).__init__(methodName)

        # Load the interpreter.
        self.interpreter = Interpreter(show_script=False, raise_relax_error=True)
        self.interpreter.populate_self()
        self.interpreter.on(verbose=False)

        # Alias the user function class.
        self.dasha_fns = self.interpreter.dasha


    def test_create_argfail_algor(self):
        """Failure of the algor arg of the dasha.create() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the str argument, and skip it.
            if data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxStrError, self.dasha_fns.create, algor=data[1])


    def test_create_argfail_dir(self):
        """Failure of the dir arg of the dasha.create() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and str arguments, and skip them.
            if data[0] == 'None' or data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneStrError, self.dasha_fns.create, dir=data[1])


    def test_create_argfail_force(self):
        """The force arg test of the dasha.create() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the bool arguments, and skip them.
            if data[0] == 'bool':
                continue

            # The argument test.
            self.assertRaises(RelaxBoolError, self.dasha_fns.create, force=data[1])


    def test_execute_argfail_dir(self):
        """Failure of the dir arg of the dasha.execute() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and str arguments, and skip them.
            if data[0] == 'None' or data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneStrError, self.dasha_fns.execute, dir=data[1])


    def test_execute_argfail_force(self):
        """The force arg test of the dasha.execute() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the bool arguments, and skip them.
            if data[0] == 'bool':
                continue

            # The argument test.
            self.assertRaises(RelaxBoolError, self.dasha_fns.execute, force=data[1])


    def test_execute_argfail_binary(self):
        """Failure of the binary arg of the dasha.execute() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the str argument, and skip it.
            if data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxStrError, self.dasha_fns.execute, binary=data[1])


    def test_extract_argfail_dir(self):
        """Failure of the dir arg of the dasha.extract() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and str arguments, and skip them.
            if data[0] == 'None' or data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneStrError, self.dasha_fns.extract, dir=data[1])
