###############################################################################
#                                                                             #
# Copyright (C) 2007-2014 Edward d'Auvergne                                   #
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
from lib.errors import RelaxBoolError, RelaxNoneIntListIntError, RelaxNoneStrError, RelaxNoneStrListStrError, RelaxNumError, RelaxStrError
from test_suite.unit_tests.structure_testing_base import Structure_base_class

# Unit test imports.
from test_suite.unit_tests._prompt.data_types import DATA_TYPES


class Test_structure(Structure_base_class, TestCase):
    """Unit tests for the functions of the 'prompt.structure' module."""

    def __init__(self, methodName=None):
        """Set up the test case class for the system tests."""

        # Execute the base __init__ methods.
        super(Test_structure, self).__init__(methodName)

        # Load the interpreter.
        self.interpreter = Interpreter(show_script=False, raise_relax_error=True)
        self.interpreter.populate_self()
        self.interpreter.on(verbose=False)

        # Alias the user function class.
        self.structure_fns = self.interpreter.structure


    def test_create_diff_tensor_pdb_argfail_scale(self):
        """The scale arg test of the structure.create_diff_tensor_pdb() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the float, bin, and int arguments, and skip them.
            if data[0] == 'float' or data[0] == 'bin' or data[0] == 'int':
                continue

            # The argument test.
            self.assertRaises(RelaxNumError, self.structure_fns.create_diff_tensor_pdb, scale=data[1])


    def test_create_diff_tensor_pdb_argfail_file(self):
        """The file arg test of the structure.create_diff_tensor_pdb() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the str arguments, and skip them.
            if data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxStrError, self.structure_fns.create_diff_tensor_pdb, file=data[1])


    def test_create_diff_tensor_pdb_argfail_dir(self):
        """The dir arg test of the structure.create_diff_tensor_pdb() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and str arguments, and skip them.
            if data[0] == 'None' or data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneStrError, self.structure_fns.create_diff_tensor_pdb, dir=data[1])


    def test_create_diff_tensor_pdb_argfail_force(self):
        """The force arg test of the structure.create_diff_tensor_pdb() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the bool arguments, and skip them.
            if data[0] == 'bool':
                continue

            # The argument test.
            self.assertRaises(RelaxBoolError, self.structure_fns.create_diff_tensor_pdb, force=data[1])


    def test_create_vector_dist_argfail_length(self):
        """The length arg test of the structure.create_vector_dist() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the number arguments, and skip them.
            if data[0] == 'bin' or data[0] == 'int' or data[0] == 'float':
                continue

            # The argument test.
            self.assertRaises(RelaxNumError, self.structure_fns.create_vector_dist, length=data[1])


    def test_create_vector_dist_argfail_file(self):
        """The file arg test of the structure.create_vector_dist() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the str arguments, and skip them.
            if data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxStrError, self.structure_fns.create_vector_dist, file=data[1])


    def test_create_vector_dist_argfail_dir(self):
        """The dir arg test of the structure.create_vector_dist() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and str arguments, and skip them.
            if data[0] == 'None' or data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneStrError, self.structure_fns.create_vector_dist, dir=data[1])


    def test_create_vector_dist_argfail_symmetry(self):
        """The symmetry arg test of the structure.create_vector_dist() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the bool arguments, and skip them.
            if data[0] == 'bool':
                continue

            # The argument test.
            self.assertRaises(RelaxBoolError, self.structure_fns.create_vector_dist, symmetry=data[1])


    def test_create_vector_dist_argfail_force(self):
        """The force arg test of the structure.create_vector_dist() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the bool arguments, and skip them.
            if data[0] == 'bool':
                continue

            # The argument test.
            self.assertRaises(RelaxBoolError, self.structure_fns.create_vector_dist, force=data[1])


    def test_load_spins_argfail_spin_id(self):
        """The spin_id arg test of the structure.load_spins() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and str arguments, and skip them.
            if data[0] == 'None' or data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneStrError, self.structure_fns.load_spins, spin_id=data[1])


    def test_read_pdb_argfail_file(self):
        """The file arg test of the structure.read_pdb() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the str arguments, and skip them.
            if data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxStrError, self.structure_fns.read_pdb, file=data[1])


    def test_read_pdb_argfail_dir(self):
        """The dir arg test of the structure.read_pdb() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None and str arguments, and skip them.
            if data[0] == 'None' or data[0] == 'str':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneStrError, self.structure_fns.read_pdb, file='test.pdb', dir=data[1])


    def test_read_pdb_argfail_read_mol(self):
        """The read_mol arg test of the structure.read_pdb() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None, bin, int, and int list arguments, and skip them.
            if data[0] == 'None' or data[0] == 'bin' or data[0] == 'int' or data[0] == 'int list':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneIntListIntError, self.structure_fns.read_pdb, file='test.pdb', read_mol=data[1])


    def test_read_pdb_argfail_set_mol_name(self):
        """The set_mol_name arg test of the structure.read_pdb() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None, str, and str list arguments, and skip them.
            if data[0] == 'None' or data[0] == 'str' or data[0] == 'str list':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneStrListStrError, self.structure_fns.read_pdb, file='test.pdb', set_mol_name=data[1])


    def test_read_pdb_argfail_read_model(self):
        """The read_model arg test of the structure.read_pdb() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None, bin, int, and int list arguments, and skip them.
            if data[0] == 'None' or data[0] == 'bin' or data[0] == 'int' or data[0] == 'int list':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneIntListIntError, self.structure_fns.read_pdb, file='test.pdb', read_model=data[1])


    def test_read_pdb_argfail_set_model_num(self):
        """The set_model_num arg test of the structure.read_pdb() user function."""

        # Loop over the data types.
        for data in DATA_TYPES:
            # Catch the None, bin, int, and int list arguments, and skip them.
            if data[0] == 'None' or data[0] == 'bin' or data[0] == 'int' or data[0] == 'int list':
                continue

            # The argument test.
            self.assertRaises(RelaxNoneIntListIntError, self.structure_fns.read_pdb, file='test.pdb', set_model_num=data[1])
