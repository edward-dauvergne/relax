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
from lib.errors import RelaxError, RelaxBoolError, RelaxIntError, RelaxIntListIntError, RelaxNoneListNumError, RelaxNoneNumError, RelaxNoneStrError, RelaxNumError, RelaxStrError
from test_suite.unit_tests.minimisation_testing_base import Minimisation_base_class

# Unit test imports.
from test_suite.unit_tests._prompt.data_types import DATA_TYPES


class Test_minimisation(Minimisation_base_class, TestCase):
    """Unit tests for the functions of the 'prompt.minimisation' module."""

    def __init__(self, methodName=None):
        """Set up the test case class for the system tests."""

        # Execute the base __init__ methods.
        super(Test_minimisation, self).__init__(methodName)

        # Load the interpreter.
        self.interpreter = Interpreter(show_script=False, raise_relax_error=True)
        self.interpreter.populate_self()
        self.interpreter.on(verbose=False)

        # Alias the user function class.
        self.minimisation_fns = self.interpreter.minimise


    def test_calc_argfail_verbosity(self):
        """The verbosity arg test of the minimise.calculate() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the int and bin arguments, and skip them.
            if data[0] == 'int' or data[0] == 'bin':
                continue

            # The argument test.
            self.assertRaises(RelaxIntError, self.minimisation_fns.calculate, verbosity=data[1])


    def test_grid_search_argfail_lower(self):
        """The lower arg test of the minimise.grid_search() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and int, float, and number list arguments arguments, and skip them.
            if data[0] == 'None' or data[0] == 'int list' or data[0] == 'float list' or data[0] == 'number list':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneListNumError, self.minimisation_fns.grid_search, lower=data[1])


    def test_grid_search_argfail_upper(self):
        """The upper arg test of the minimise.grid_search() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and int, float, and number list arguments arguments, and skip them.
            if data[0] == 'None' or data[0] == 'int list' or data[0] == 'float list' or data[0] == 'number list':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneListNumError, self.minimisation_fns.grid_search, upper=data[1])


    def test_grid_search_argfail_inc(self):
        """The inc arg test of the minimise.grid_search() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the bin, int, and interger list arguments, and skip them.
            if data[0] == 'bin' or data[0] == 'int' or data[0] == 'int list' or data[0] == 'none list':
                continue

            # The argument test.
            self.assertRaises(RelaxIntListIntError, self.minimisation_fns.grid_search, inc=data[1])


    def test_grid_search_argfail_constraints(self):
        """The constraints arg test of the minimise.grid_search() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the bool arguments, and skip them.
            if data[0] == 'bool':
                continue

            # The argument test.
            self.assertRaises(RelaxBoolError, self.minimisation_fns.grid_search, constraints=data[1])


    def test_grid_search_argfail_verbosity(self):
        """The verbosity arg test of the minimise.grid_search() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the int and bin arguments, and skip them.
            if data[0] == 'int' or data[0] == 'bin':
                continue

            # The argument test.
            self.assertRaises(RelaxIntError, self.minimisation_fns.grid_search, verbosity=data[1])


    def test_minimise_argfail_bad_keyword(self):
        """The test of a bad keyword argument in the minimise.execute() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # The argument test.
            self.assertRaises(RelaxError, self.minimisation_fns.execute, 'Newton', step_tol=data[1])


    def test_minimise_argfail_min_algor(self):
        """The min_algor arg test of the minimise.execute() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the str argument, and skip it.
            if data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxStrError, self.minimisation_fns.execute, data[1])


    def test_minimise_argfail_line_search(self):
        """The line_search arg test of the minimise.execute() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and str arguments, and skip them.
            if data[0] == 'None' or data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneStrError, self.minimisation_fns.execute, 'Newton', line_search=data[1])


    def test_minimise_argfail_hessian_mod(self):
        """The hessian_mod arg test of the minimise.execute() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and str arguments, and skip them.
            if data[0] == 'None' or data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneStrError, self.minimisation_fns.execute, 'Newton', hessian_mod=data[1])


    def test_minimise_argfail_hessian_type(self):
        """The hessian_type arg test of the minimise.execute() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and str arguments, and skip them.
            if data[0] == 'None' or data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneStrError, self.minimisation_fns.execute, 'Newton', hessian_type=data[1])


    def test_minimise_argfail_func_tol(self):
        """The func_tol arg test of the minimise.execute() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the float, bin, and int arguments, and skip them.
            if data[0] == 'float' or data[0] == 'bin' or data[0] == 'int':
                continue

            # The argument test.
            self.assertRaises(RelaxNumError, self.minimisation_fns.execute, 'Newton', func_tol=data[1])


    def test_minimise_argfail_grad_tol(self):
        """The grad_tol arg test of the minimise.execute() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None, float, bin, and int arguments, and skip them.
            if data[0] == 'None' or data[0] == 'float' or data[0] == 'bin' or data[0] == 'int':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneNumError, self.minimisation_fns.execute, 'Newton', grad_tol=data[1])


    def test_minimise_argfail_max_iter(self):
        """The max_iter arg test of the minimise.execute() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the bin and int arguments, and skip them.
            if data[0] == 'bin' or data[0] == 'int':
                continue

            # The argument test.
            self.assertRaises(RelaxIntError, self.minimisation_fns.execute, 'Newton', max_iter=data[1])


    def test_minimise_argfail_constraints(self):
        """The constraints arg test of the minimise.execute() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the bool arguments, and skip them.
            if data[0] == 'bool':
                continue

            # The argument test.
            self.assertRaises(RelaxBoolError, self.minimisation_fns.execute, 'Newton', constraints=data[1])


    def test_minimise_argfail_scaling(self):
        """The scaling arg test of the minimise.execute() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the bool arguments, and skip them.
            if data[0] == 'bool':
                continue

            # The argument test.
            self.assertRaises(RelaxBoolError, self.minimisation_fns.execute, 'Newton', scaling=data[1])


    def test_minimise_argfail_verbosity(self):
        """The verbosity arg test of the minimise.execute() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the bin and int arguments, and skip them.
            if data[0] == 'bin' or data[0] == 'int':
                continue

            # The argument test.
            self.assertRaises(RelaxIntError, self.minimisation_fns.execute, 'Newton', verbosity=data[1])


