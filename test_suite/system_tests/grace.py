###############################################################################
#                                                                             #
# Copyright (C) 2008-2012 Edward d'Auvergne                                   #
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
from os import sep
from re import search
from tempfile import mktemp

# relax module imports.
from status import Status; status = Status()
from test_suite.system_tests.base_classes import SystemTestCase


class Grace(SystemTestCase):
    """Class for testing the creation of grace plots."""

    def setUp(self):
        """Common set up for these system tests."""

        # Create a temporary grace file name.
        self.tmpfile = mktemp()


    def test_cam_kkalpha_plot1(self):
        """Test the plotting of the 15N data from the CaM-KKalpha save state."""

        # Load the state.
        self.interpreter.state.load('state_cam_kkalpha', dir=status.install_path + sep+'test_suite'+sep+'shared_data'+sep+'saved_states')

        # Create the plot.
        self.interpreter.grace.write('res_num', 's2', file=self.tmpfile, spin_id='@N', dir=None)

        # Read the file data.
        file = open(self.tmpfile)
        lines = file.readlines()
        file.close()

        # Init the data.
        spin = []
        value = []
        error = []

        # Check the data.
        in_data = False
        for i in range(len(lines)):
            # Start of the first plot.
            if search('G0.S0', lines[i]):
                in_data=True
                continue

            # No in the data range.
            if not in_data:
                continue

            # Skip the first @ line.
            if search('^@', lines[i]):
                continue

            # The end.
            if search('^&', lines[i]):
                break

            # Split up the data.
            row = lines[i].split()

            # Store the data.
            spin.append(float(row[0]))
            value.append(float(row[1]))
            error.append(float(row[2]))

        # The real data.
        real_data = [
            [2,  0.693, 0.005],
            [3,  0.400, 0.000],
            [4,  0.882, 0.008],
            [5,  0.901, 0.001],
            [6,  0.953, 0.014],
            [7,  0.905, 0.000],
            [8,  0.939, 0.007],
            [9,  0.948, 0.003],
            [10, 0.957, 0.004]
        ]

        # Check the data length.
        self.assertEqual(len(real_data), len(spin))

        # Check the data.
        for i in range(len(real_data)):
            self.assertEqual(float(real_data[i][0]), spin[i])
            self.assertAlmostEqual(real_data[i][1], value[i])
            self.assertAlmostEqual(real_data[i][2], error[i])
