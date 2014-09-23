###############################################################################
#                                                                             #
# Copyright (C) 2008-2013 Edward d'Auvergne                                   #
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
from os import path, sep

# relax module imports.
from data_store import Relax_data_store; ds = Relax_data_store()
from pipe_control.reset import reset
from lib.io import file_root
from lib.structure.internal.molecules import MolContainer
from lib.structure.internal.object import Internal
from status import Status; status = Status()
from test_suite.unit_tests.base_classes import UnitTestCase


class Test_internal(UnitTestCase):
    """Unit tests for the functions of the 'pipe_control.structure.internal' module."""

    def setUp(self):
        """Set up for all the internal relax structural object unit tests."""

        # The path to a PDB file.
        self.test_pdb_path = status.install_path+sep+'test_suite'+sep+'shared_data'+sep+'structures'+sep+'Ap4Aase_res1-12.pdb'
        expanded = path.split(self.test_pdb_path)
        self.test_pdb_dir = expanded[0]
        self.test_pdb_file_name = expanded[1]
        self.test_pdb_root = file_root(self.test_pdb_path)

        # Instantiate the structural data object.
        self.data = Internal()

        # Instantiate a MolContainer object.
        self.mol_cont = MolContainer()


    def tearDown(self):
        """Reset the relax data storage object."""

        # Delete the structural data object.
        del self.data

        # Reset relax.
        reset()


    def test__trim_helix1(self):
        """1st test of the Internal._trim_helix() method."""

        # The helix metadata of the internal structural object.
        helix = ['H1', 'A', 'ILE', 23, 'A', 'GLU', 34, 1, 12]

        # Residues deleted before the helix.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_helix = self.data._trim_helix(helix=helix, trim_res_list=[1, 2, 3, 22], res_data=res_data)

        # Test that nothing has happened.
        self.assertEqual(helix, new_helix)


    def test__trim_helix2(self):
        """2nd test of the Internal._trim_helix() method."""

        # The helix metadata of the internal structural object.
        helix = ['H1', 'A', 'ILE', 23, 'A', 'GLU', 34, 1, 12]

        # Residues deleted after the helix.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_helix = self.data._trim_helix(helix=helix, trim_res_list=[51, 52, 53], res_data=res_data)

        # Test that nothing has happened.
        self.assertEqual(helix, new_helix)


    def test__trim_helix3(self):
        """3rd test of the Internal._trim_helix() method."""

        # The helix metadata of the internal structural object.
        helix = ['H1', 'A', 'ILE', 23, 'A', 'GLU', 34, 1, 12]
        trimmed_helix = ['H1', 'A', 'GLU', 24, 'A', 'GLU', 34, 1, 11]

        # Trim the start of the helix.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_helix = self.data._trim_helix(helix=helix, trim_res_list=[21, 22, 23], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_helix, new_helix)


    def test__trim_helix4(self):
        """4th test of the Internal._trim_helix() method."""

        # The helix metadata of the internal structural object.
        helix = ['H1', 'A', 'ILE', 23, 'A', 'GLU', 34, 1, 12]
        trimmed_helix = ['H1', 'A', 'VAL', 26, 'A', 'GLU', 34, 1, 9]

        # Trim the start of the helix.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_helix = self.data._trim_helix(helix=helix, trim_res_list=[21, 22, 23, 24, 25], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_helix, new_helix)


    def test__trim_helix5(self):
        """5th test of the Internal._trim_helix() method."""

        # The helix metadata of the internal structural object.
        helix = ['H1', 'A', 'ILE', 23, 'A', 'GLU', 34, 1, 12]
        trimmed_helix = ['H1', 'A', 'VAL', 26, 'A', 'GLU', 34, 1, 9]

        # Trim the start of the helix.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_helix = self.data._trim_helix(helix=helix, trim_res_list=[21, 22, 23, 24, 25, 30], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_helix, new_helix)


    def test__trim_helix6(self):
        """6th test of the Internal._trim_helix() method."""

        # The helix metadata of the internal structural object.
        helix = ['H1', 'A', 'ILE', 23, 'A', 'GLU', 34, 1, 12]
        trimmed_helix = ['H1', 'A', 'VAL', 26, 'A', 'GLU', 34, 1, 9]

        # Trim the start of the helix.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_helix = self.data._trim_helix(helix=helix, trim_res_list=[21, 22, 23, 24, 25, 40], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_helix, new_helix)


    def test__trim_helix7(self):
        """7th test of the Internal._trim_helix() method."""

        # The helix metadata of the internal structural object.
        helix = ['H1', 'A', 'ILE', 23, 'A', 'GLU', 34, 1, 12]
        trimmed_helix = ['H1', 'A', 'ILE', 23, 'A', 'LYS', 33, 1, 11]

        # Trim the end of the helix.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_helix = self.data._trim_helix(helix=helix, trim_res_list=[34, 35, 36], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_helix, new_helix)


    def test__trim_helix8(self):
        """8th test of the Internal._trim_helix() method."""

        # The helix metadata of the internal structural object.
        helix = ['H1', 'A', 'ILE', 23, 'A', 'GLU', 34, 1, 12]

        # Trim nothing.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_helix = self.data._trim_helix(helix=helix, trim_res_list=[35, 36], res_data=res_data)

        # Test the trimming.
        self.assertEqual(helix, new_helix)


    def test__trim_helix9(self):
        """9th test of the Internal._trim_helix() method."""

        # The helix metadata of the internal structural object.
        helix = ['H1', 'A', 'ILE', 23, 'A', 'GLU', 34, 1, 12]
        trimmed_helix = ['H1', 'A', 'ILE', 23, 'A', 'ILE', 30, 1, 8]

        # Trim the end of the helix.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_helix = self.data._trim_helix(helix=helix, trim_res_list=[31, 32, 33, 34, 35], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_helix, new_helix)


    def test__trim_helix10(self):
        """10th test of the Internal._trim_helix() method."""

        # The helix metadata of the internal structural object.
        helix = ['H1', 'A', 'ILE', 23, 'A', 'GLU', 34, 1, 12]
        trimmed_helix = ['H1', 'A', 'ILE', 23, 'A', 'GLN', 31, 1, 9]

        # Trim the end of the helix.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_helix = self.data._trim_helix(helix=helix, trim_res_list=[24, 32, 33, 34, 35], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_helix, new_helix)


    def test__trim_helix11(self):
        """11th test of the Internal._trim_helix() method."""

        # The helix metadata of the internal structural object.
        helix = ['H1', 'A', 'ILE', 23, 'A', 'GLU', 34, 1, 12]
        trimmed_helix = ['H1', 'A', 'ASN', 25, 'A', 'GLN', 31, 1, 7]

        # Trim the both ends of the helix.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_helix = self.data._trim_helix(helix=helix, trim_res_list=[22, 23, 24, 32, 33, 34, 35], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_helix, new_helix)


    def test__trim_helix12(self):
        """12th test of the Internal._trim_helix() method."""

        # The helix metadata of the internal structural object.
        helix = ['H1', 'A', 'ILE', 23, 'A', 'GLU', 34, 1, 12]
        trimmed_helix = ['H1', 'A', 'ASN', 25, 'A', 'GLN', 31, 1, 7]

        # Trim the both ends of the helix.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_helix = self.data._trim_helix(helix=helix, trim_res_list=[22, 23, 24, 27, 32, 33, 34, 35], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_helix, new_helix)


    def test__trim_helix13(self):
        """13th test of the Internal._trim_helix() method."""

        # The helix metadata of the internal structural object.
        helix = ['H1', 'A', 'ILE', 23, 'A', 'GLU', 34, 1, 12]

        # Trim everything.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_helix = self.data._trim_helix(helix=helix, trim_res_list=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35], res_data=res_data)

        # Test the trimming.
        self.assertEqual(None, new_helix)


    def test__trim_sheet1(self):
        """1st test of the Internal._trim_sheet() method."""

        # The sheet metadata of the internal structural object.
        sheet = [1, 'BET', 5, 'GLY', 'A', 10, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]

        # Residues deleted before the sheet.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_sheet = self.data._trim_sheet(sheet=sheet, trim_res_list=[1, 2, 3, 22], res_data=res_data)

        # Test that nothing has happened.
        self.assertEqual(sheet, new_sheet)


    def test__trim_sheet2(self):
        """2nd test of the Internal._trim_sheet() method."""

        # The sheet metadata of the internal structural object.
        sheet = [1, 'BET', 5, 'GLY', 'A', 10, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]

        # Residues deleted after the sheet.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_sheet = self.data._trim_sheet(sheet=sheet, trim_res_list=[51, 52, 53], res_data=res_data)

        # Test that nothing has happened.
        self.assertEqual(sheet, new_sheet)


    def test__trim_sheet3(self):
        """3rd test of the Internal._trim_sheet() method."""

        # The sheet metadata of the internal structural object.
        sheet = [1, 'BET', 5, 'GLY', 'A', 10, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]
        trimmed_sheet = [1, 'BET', 5, 'LYS', 'A', 11, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]

        # Trim the start of the sheet.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_sheet = self.data._trim_sheet(sheet=sheet, trim_res_list=[8, 9, 10], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_sheet, new_sheet)


    def test__trim_sheet4(self):
        """4th test of the Internal._trim_sheet() method."""

        # The sheet metadata of the internal structural object.
        sheet = [1, 'BET', 5, 'GLY', 'A', 10, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]
        trimmed_sheet = [1, 'BET', 5, 'ILE', 'A', 13, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]

        # Trim the start of the sheet.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_sheet = self.data._trim_sheet(sheet=sheet, trim_res_list=[8, 9, 10, 11, 12], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_sheet, new_sheet)


    def test__trim_sheet5(self):
        """5th test of the Internal._trim_sheet() method."""

        # The sheet metadata of the internal structural object.
        sheet = [1, 'BET', 5, 'GLY', 'A', 10, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]
        trimmed_sheet = [1, 'BET', 5, 'ILE', 'A', 13, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]

        # Trim the start of the sheet.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_sheet = self.data._trim_sheet(sheet=sheet, trim_res_list=[8, 9, 10, 11, 12, 15], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_sheet, new_sheet)


    def test__trim_sheet6(self):
        """6th test of the Internal._trim_sheet() method."""

        # The sheet metadata of the internal structural object.
        sheet = [1, 'BET', 5, 'GLY', 'A', 10, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]
        trimmed_sheet = [1, 'BET', 5, 'ILE', 'A', 13, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]

        # Trim the start of the sheet.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_sheet = self.data._trim_sheet(sheet=sheet, trim_res_list=[8, 9, 10, 11, 12, 30], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_sheet, new_sheet)


    def test__trim_sheet7(self):
        """7th test of the Internal._trim_sheet() method."""

        # The sheet metadata of the internal structural object.
        sheet = [1, 'BET', 5, 'GLY', 'A', 10, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]
        trimmed_sheet = [1, 'BET', 5, 'GLY', 'A', 10, None, 'GLU', 'A', 16, None, 0, None, None, None, None, None, None, None, None, None, None]

        # Trim the end of the sheet.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_sheet = self.data._trim_sheet(sheet=sheet, trim_res_list=[17, 18, 19], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_sheet, new_sheet)


    def test__trim_sheet8(self):
        """8th test of the Internal._trim_sheet() method."""

        # The sheet metadata of the internal structural object.
        sheet = [1, 'BET', 5, 'GLY', 'A', 10, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]

        # Trim nothing.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_sheet = self.data._trim_sheet(sheet=sheet, trim_res_list=[18, 19], res_data=res_data)

        # Test the trimming.
        self.assertEqual(sheet, new_sheet)


    def test__trim_sheet9(self):
        """9th test of the Internal._trim_sheet() method."""

        # The sheet metadata of the internal structural object.
        sheet = [1, 'BET', 5, 'GLY', 'A', 10, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]
        trimmed_sheet = [1, 'BET', 5, 'GLY', 'A', 10, None, 'THR', 'A', 14, None, 0, None, None, None, None, None, None, None, None, None, None]

        # Trim the end of the sheet.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_sheet = self.data._trim_sheet(sheet=sheet, trim_res_list=[15, 16, 17, 18, 19], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_sheet, new_sheet)


    def test__trim_sheet10(self):
        """10th test of the Internal._trim_sheet() method."""

        # The sheet metadata of the internal structural object.
        sheet = [1, 'BET', 5, 'GLY', 'A', 10, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]
        trimmed_sheet = [1, 'BET', 5, 'GLY', 'A', 10, None, 'THR', 'A', 14, None, 0, None, None, None, None, None, None, None, None, None, None]

        # Trim the end of the sheet.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_sheet = self.data._trim_sheet(sheet=sheet, trim_res_list=[11, 15, 16, 17, 18, 19], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_sheet, new_sheet)


    def test__trim_sheet11(self):
        """11th test of the Internal._trim_sheet() method."""

        # The sheet metadata of the internal structural object.
        sheet = [1, 'BET', 5, 'GLY', 'A', 10, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]
        trimmed_sheet = [1, 'BET', 5, 'LYS', 'A', 11, None, 'LEU', 'A', 15, None, 0, None, None, None, None, None, None, None, None, None, None]

        # Trim the both ends of the sheet.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_sheet = self.data._trim_sheet(sheet=sheet, trim_res_list=[9, 10, 16, 17, 18, 19], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_sheet, new_sheet)


    def test__trim_sheet12(self):
        """12th test of the Internal._trim_sheet() method."""

        # The sheet metadata of the internal structural object.
        sheet = [1, 'BET', 5, 'GLY', 'A', 10, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]
        trimmed_sheet = [1, 'BET', 5, 'LYS', 'A', 11, None, 'LEU', 'A', 15, None, 0, None, None, None, None, None, None, None, None, None, None]

        # Trim the both ends of the sheet.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_sheet = self.data._trim_sheet(sheet=sheet, trim_res_list=[9, 10, 13, 16, 17, 18, 19], res_data=res_data)

        # Test the trimming.
        self.assertEqual(trimmed_sheet, new_sheet)


    def test__trim_sheet13(self):
        """13th test of the Internal._trim_sheet() method."""

        # The sheet metadata of the internal structural object.
        sheet = [1, 'BET', 5, 'GLY', 'A', 10, None, 'VAL', 'A', 17, None, 0, None, None, None, None, None, None, None, None, None, None]

        # Trim everything.
        res_data = {1: 'MET', 2: 'GLN', 3: 'ILE', 4: 'PHE', 5: 'VAL', 6: 'LYS', 7: 'THR', 8: 'LEU', 9: 'THR', 10: 'GLY', 11: 'LYS', 12: 'THR', 13: 'ILE', 14: 'THR', 15: 'LEU', 16: 'GLU', 17: 'VAL', 18: 'GLU', 19: 'PRO', 20: 'SER', 21: 'ASP', 22: 'THR', 23: 'ILE', 24: 'GLU', 25: 'ASN', 26: 'VAL', 27: 'LYS', 28: 'ALA', 29: 'LYS', 30: 'ILE', 31: 'GLN', 32: 'ASP', 33: 'LYS', 34: 'GLU'}
        new_sheet = self.data._trim_sheet(sheet=sheet, trim_res_list=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35], res_data=res_data)

        # Test the trimming.
        self.assertEqual(None, new_sheet)


    def test_atom_loop(self):
        """Test the Internal.atom_loop() method."""

        # Load the PDB file.
        self.data.load_pdb(self.test_pdb_path)

        # Loop over the atoms.
        atom_count = 0
        selection = self.data.selection(atom_id=None)
        for atom in self.data.atom_loop(selection=selection):
            atom_count = atom_count + 1

        # Test the number of atoms looped over.
        self.assertEqual(atom_count, 150)


    def test_atom_loop_mol_selection(self):
        """Test the Internal.atom_loop() method with the '#XXX' mol selection."""

        # Load the PDB file.
        self.data.load_pdb(self.test_pdb_path)

        # Loop over the atoms.
        atom_count = 0
        selection = self.data.selection(atom_id='#XXX')
        for atom in self.data.atom_loop(selection=selection):
            atom_count = atom_count + 1

        # Test the number of atoms looped over.
        self.assertEqual(atom_count, 0)


    def test_atom_loop_res_selection1(self):
        """Test the Internal.atom_loop() method with the ':8' res selection."""

        # Load the PDB file.
        self.data.load_pdb(self.test_pdb_path)

        # Loop over the atoms.
        atom_count = 0
        selection = self.data.selection(atom_id=':8')
        for res_num, res_name in self.data.atom_loop(selection=selection, res_num_flag=True, res_name_flag=True):
            # Test the residue name and number.
            self.assertEqual(res_num, 8)
            self.assertEqual(res_name, 'SER')

            # Increment the atom count.
            atom_count = atom_count + 1

        # Test the number of atoms looped over.
        self.assertEqual(atom_count, 11)


    def test_atom_loop_res_selection2(self):
        """Test the Internal.atom_loop() method with the ':PRO' res selection."""

        # Load the PDB file.
        self.data.load_pdb(self.test_pdb_path)

        # Loop over the atoms.
        atom_count = 0
        selection = self.data.selection(atom_id=':PRO')
        for atom in self.data.atom_loop(selection=selection, res_name_flag=True):
            # Test the residue name.
            self.assertEqual(atom, 'PRO')

            # Increment the atom count.
            atom_count = atom_count + 1

        # Test the number of atoms looped over.
        self.assertEqual(atom_count, 42)


    def test_atom_loop_spin_selection1(self):
        """Test the Internal.atom_loop() method with the '@CA' spin selection."""

        # Load the PDB file.
        self.data.load_pdb(self.test_pdb_path)

        # Loop over the atoms.
        atom_count = 0
        selection = self.data.selection(atom_id='@CA')
        for spin_name in self.data.atom_loop(selection=selection, atom_name_flag=True):
            # Test the spin name.
            self.assertEqual(spin_name, 'CA')

            # Increment the atom count.
            atom_count = atom_count + 1

        # Test the number of atoms looped over.
        self.assertEqual(atom_count, 12)


    def test_atom_loop_spin_selection2(self):
        """Test the Internal.atom_loop() method with the '@163' spin selection."""

        # Load the PDB file.
        self.data.load_pdb(self.test_pdb_path)

        # Loop over the atoms.
        atom_count = 0
        selection = self.data.selection(atom_id='@140')
        for mol_name, res_num, res_name, spin_num, spin_name, element, pos in self.data.atom_loop(selection=selection, mol_name_flag=True, res_num_flag=True, res_name_flag=True, atom_num_flag=True, atom_name_flag=True, element_flag=True, pos_flag=True):
            # Test the spin info.
            self.assertEqual(mol_name, self.test_pdb_root+'_mol1')
            self.assertEqual(res_num, 11)
            self.assertEqual(res_name, 'GLU')
            self.assertEqual(spin_num, 140)
            self.assertEqual(spin_name, 'OE1')
            self.assertEqual(element, 'O')
            self.assertEqual(pos.shape, (1, 3))
            self.assertEqual(pos[0, 0], float('10.055'))
            self.assertEqual(pos[0, 1], float('-2.74'))
            self.assertEqual(pos[0, 2], float('-13.193'))

            # Increment the atom count.
            atom_count = atom_count + 1

        # Test the number of atoms looped over.
        self.assertEqual(atom_count, 1)


    def test_load_pdb(self):
        """Load a PDB file using Internal.load_pdb()."""

        # Load the PDB file.
        self.data.load_pdb(self.test_pdb_path)

        # The ModelContainer and MolContainer.
        model = self.data.structural_data[0]
        mol = model.mol[0]

        # Test the structural data.
        self.assertEqual(len(self.data.structural_data), 1)
        self.assertEqual(len(model.mol), 1)
        self.assertEqual(model.num, 1)
        self.assertEqual(mol.mol_name, self.test_pdb_root+'_mol1')
        self.assertEqual(mol.file_name, self.test_pdb_file_name)
        self.assertEqual(mol.file_path, self.test_pdb_dir)
        self.assertEqual(mol.file_model, 1)
        self.assertEqual(mol.file_mol_num, 1)

        # The real atomic data.
        atom_name = ['N', 'CA', '1HA', '2HA', 'C', 'O', '1HT', '2HT', '3HT', 'N', 'CD', 'CA', 'HA', 'CB', '1HB', '2HB', 'CG', '1HG', '2HG', '1HD', '2HD', 'C', 'O', 'N', 'H', 'CA', 'HA', 'CB', '1HB', '2HB', 'CG', 'HG', 'CD1', '1HD1', '2HD1', '3HD1', 'CD2', '1HD2', '2HD2', '3HD2', 'C', 'O', 'N', 'H', 'CA', '1HA', '2HA', 'C', 'O', 'N', 'H', 'CA', 'HA', 'CB', '1HB', '2HB', 'OG', 'HG', 'C', 'O', 'N', 'H', 'CA', 'HA', 'CB', '1HB', '2HB', 'CG', '1HG', '2HG', 'SD', 'CE', '1HE', '2HE', '3HE', 'C', 'O', 'N', 'H', 'CA', 'HA', 'CB', '1HB', '2HB', 'CG', 'OD1', 'OD2', 'C', 'O', 'N', 'H', 'CA', 'HA', 'CB', '1HB', '2HB', 'OG', 'HG', 'C', 'O', 'N', 'CD', 'CA', 'HA', 'CB', '1HB', '2HB', 'CG', '1HG', '2HG', '1HD', '2HD', 'C', 'O', 'N', 'CD', 'CA', 'HA', 'CB', '1HB', '2HB', 'CG', '1HG', '2HG', '1HD', '2HD', 'C', 'O', 'N', 'H', 'CA', 'HA', 'CB', '1HB', '2HB', 'CG', '1HG', '2HG', 'CD', 'OE1', 'OE2', 'C', 'O', 'N', 'H', 'CA', '1HA', '2HA', 'C', 'O']
        bonded = [[]]*174
        chain_id = [None]*174
        element = ['N', 'C', 'H', 'H', 'C', 'O', 'H', 'H', 'H', 'N', 'C', 'C', 'H', 'C', 'H', 'H', 'C', 'H', 'H', 'H', 'H', 'C', 'O', 'N', 'H', 'C', 'H', 'C', 'H', 'H', 'C', 'H', 'C', 'H', 'H', 'H', 'C', 'H', 'H', 'H', 'C', 'O', 'N', 'H', 'C', 'H', 'H', 'C', 'O', 'N', 'H', 'C', 'H', 'C', 'H', 'H', 'O', 'H', 'C', 'O', 'N', 'H', 'C', 'H', 'C', 'H', 'H', 'C', 'H', 'H', 'S', 'C', 'H', 'H', 'H', 'C', 'O', 'N', 'H', 'C', 'H', 'C', 'H', 'H', 'C', 'O', 'O', 'C', 'O', 'N', 'H', 'C', 'H', 'C', 'H', 'H', 'O', 'H', 'C', 'O', 'N', 'C', 'C', 'H', 'C', 'H', 'H', 'C', 'H', 'H', 'H', 'H', 'C', 'O', 'N', 'C', 'C', 'H', 'C', 'H', 'H', 'C', 'H', 'H', 'H', 'H', 'C', 'O', 'N', 'H', 'C', 'H', 'C', 'H', 'H', 'C', 'H', 'H', 'C', 'O', 'O', 'C', 'O', 'N', 'H', 'C', 'H', 'H', 'C', 'O']
        pdb_record = ['ATOM']*174
        res_name = ['GLY', 'GLY', 'GLY', 'GLY', 'GLY', 'GLY', 'GLY', 'GLY', 'GLY', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'LEU', 'LEU', 'LEU', 'LEU', 'LEU', 'LEU', 'LEU', 'LEU', 'LEU', 'LEU', 'LEU', 'LEU', 'LEU', 'LEU', 'LEU', 'LEU', 'LEU', 'LEU', 'LEU', 'GLY', 'GLY', 'GLY', 'GLY', 'GLY', 'GLY', 'GLY', 'SER', 'SER', 'SER', 'SER', 'SER', 'SER', 'SER', 'SER', 'SER', 'SER', 'SER', 'MET', 'MET', 'MET', 'MET', 'MET', 'MET', 'MET', 'MET', 'MET', 'MET', 'MET', 'MET', 'MET', 'MET', 'MET', 'MET', 'MET', 'ASP', 'ASP', 'ASP', 'ASP', 'ASP', 'ASP', 'ASP', 'ASP', 'ASP', 'ASP', 'ASP', 'ASP', 'SER', 'SER', 'SER', 'SER', 'SER', 'SER', 'SER', 'SER', 'SER', 'SER', 'SER', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'PRO', 'GLU', 'GLU', 'GLU', 'GLU', 'GLU', 'GLU', 'GLU', 'GLU', 'GLU', 'GLU', 'GLU', 'GLU', 'GLU', 'GLU', 'GLU', 'GLY', 'GLY', 'GLY', 'GLY', 'GLY', 'GLY', 'GLY']
        res_num = [1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 11, 12, 12, 12, 12, 12, 12, 12]
        seg_id = [None]*174
        x = [8.442, 7.469, 8.013, 6.825, 6.610, 6.827, 9.398, 8.180, 8.448, 5.613, 5.281, 4.714, 5.222, 3.646, 3.332, 2.800, 4.319, 4.853, 3.587, 6.162, 4.805, 4.075, 3.593, 4.074, 4.475, 3.498, 3.572, 2.025, 1.965, 1.609, 1.176, 1.823, 0.176, 0.096, 0.509, -0.789, 0.474, 0.809, -0.595, 0.707, 4.264, 4.364, 4.809, 4.697, 5.561, 6.220, 6.156, 4.659, 4.746, 3.786, 3.770, 2.851, 2.368, 1.785, 1.177, 1.165, 2.360, 1.690, 3.546, 3.804, 3.814, 3.563, 4.442, 4.984, 5.411, 6.192, 4.872, 6.068, 6.868, 5.332, 6.747, 6.155, 5.409, 6.977, 5.721, 3.369, 2.255, 3.703, 4.604, 2.753, 1.851, 3.329, 4.182, 3.644, 2.319, 1.992, 1.854, 2.419, 1.251, 3.451, 4.359, 3.267, 2.246, 4.223, 4.054, 4.040, 5.573, 6.142, 3.488, 4.276, 2.795, 1.828, 2.929, 2.810, 1.772, 0.912, 2.067, 1.505, 0.464, 2.138, 0.938, 2.273, 4.268, 4.585, 5.076, 4.776, 6.392, 6.925, 7.120, 7.968, 7.464, 6.130, 6.384, 6.135, 4.210, 4.246, 6.325, 5.263, 7.477, 8.281, 7.587, 7.039, 9.047, 9.133, 9.654, 9.590, 10.670, 9.215, 9.190, 10.055, 8.012, 7.007, 7.361, 6.144, 5.925, 5.555, 6.329, 4.814, 4.894, 4.761]
        y = [10.188, 9.889, 9.712, 10.745, 8.674, 7.991, 10.291, 11.073, 9.416, 8.385, 9.152, 7.243, 6.302, 7.443, 6.483, 7.963, 8.253, 7.605, 8.842, 9.327, 10.088, 7.251, 8.285, 6.099, 5.309, 5.986, 4.953, 6.396, 7.471, 6.106, 5.775, 5.225, 4.796, 4.954, 3.787, 4.949, 6.853, 7.828, 6.775, 6.720, 6.853, 8.068, 6.222, 5.251, 6.956, 6.273, 7.706, 7.634, 8.841, 6.847, 5.889, 7.360, 6.511, 8.230, 7.620, 8.669, 9.269, 9.652, 8.174, 9.362, 7.546, 6.604, 8.253, 9.095, 7.354, 7.976, 6.886, 6.258, 5.824, 5.499, 6.846, 5.570, 5.985, 5.190, 4.766, 8.771, 8.245, 9.789, 10.161, 10.351, 10.605, 11.610, 11.341, 12.287, 12.322, 11.787, 13.410, 9.322, 9.015, 8.776, 9.052, 7.758, 7.826, 7.990, 8.977, 7.248, 7.894, 8.285, 6.370, 6.214, 5.342, 5.431, 3.973, 3.943, 3.230, 3.234, 2.212, 3.991, 3.892, 3.624, 5.960, 5.908, 3.339, 3.179, 2.980, 3.150, 2.375, 2.876, 2.616, 3.262, 1.675, 3.264, 4.305, 2.758, 4.055, 2.299, 0.876, 0.258, 0.312, 0.871, -1.106, -1.253, -1.489, -2.564, -1.049, -1.041, -1.011, -0.052, -1.970, -2.740, -1.931, -2.037, -1.962, -2.949, -2.983, -3.917, -4.588, -4.488, -3.289, -3.932]
        z = [6.302, 7.391, 8.306, 7.526, 7.089, 6.087, 6.697, 5.822, 5.604, 7.943, 9.155, 7.752, 7.908, 8.829, 9.212, 8.407, 9.880, 10.560, 10.415, 9.754, 8.900, 6.374, 5.909, 5.719, 6.139, 4.391, 4.081, 4.415, 4.326, 5.367, 3.307, 2.640, 3.889, 4.956, 3.700, 3.430, 2.493, 2.814, 2.633, 1.449, 3.403, 3.572, 2.369, 2.281, 1.371, 0.855, 1.868, 0.359, 0.149, -0.269, -0.055, -1.268, -1.726, -0.608, 0.037, -1.377, 0.162, 0.731, -2.354, -2.175, -3.496, -3.603, -4.606, -4.199, -5.387, -5.803, -6.196, -4.563, -5.146, -4.350, -3.001, -1.895, -1.241, -1.307, -2.472, -5.551, -5.582, -6.328, -6.269, -7.274, -6.735, -7.913, -8.518, -7.133, -8.791, -9.871, -8.395, -8.346, -8.584, -8.977, -8.732, -10.002, -10.355, -11.174, -11.584, -11.936, -10.759, -11.425, -9.403, -8.469, -9.921, -11.030, -9.410, -8.336, -10.080, -9.428, -10.291, -11.333, -11.606, -12.128, -10.723, -11.893, -9.781, -10.959, -8.768, -7.344, -8.971, -9.765, -7.642, -7.816, -7.251, -6.715, -6.584, -5.765, -7.175, -6.955, -9.288, -9.222, -9.654, -9.696, -10.009, -10.928, -10.249, -10.194, -9.475, -11.596, -11.540, -11.813, -12.724, -13.193, -13.137, -8.947, -7.774, -9.383, -10.338, -8.477, -8.138, -9.017, -7.265, -6.226]

        # Test the atomic data.
        for i in range(len(mol.atom_name)):
            self.assertEqual(mol.atom_name[i], atom_name[i])
            self.assertEqual(mol.bonded[i], bonded[i])
            self.assertEqual(mol.chain_id[i], chain_id[i])
            self.assertEqual(mol.element[i], element[i])
            self.assertEqual(mol.pdb_record[i], pdb_record[i])
            self.assertEqual(mol.res_name[i], res_name[i])
            self.assertEqual(mol.res_num[i], res_num[i])
            self.assertEqual(mol.seg_id[i], seg_id[i])
            self.assertEqual(mol.x[i], x[i])
            self.assertEqual(mol.y[i], y[i])
            self.assertEqual(mol.z[i], z[i])
