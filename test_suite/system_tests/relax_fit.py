###############################################################################
#                                                                             #
# Copyright (C) 2006-2014 Edward d'Auvergne                                   #
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
from tempfile import mkdtemp

# relax module imports.
from data_store import Relax_data_store; ds = Relax_data_store()
import dep_check
from pipe_control.mol_res_spin import spin_index_loop, spin_loop
from pipe_control import pipes
from lib.errors import RelaxError
from status import Status; status = Status()
from test_suite.system_tests.base_classes import SystemTestCase


class Relax_fit(SystemTestCase):
    """Class for testing various aspects specific to relaxation curve-fitting."""

    def __init__(self, methodName='runTest'):
        """Skip the tests if the C modules are non-functional.

        @keyword methodName:    The name of the test.
        @type methodName:       str
        """

        # Execute the base class method.
        super(Relax_fit, self).__init__(methodName)

        # Missing module.
        if not dep_check.C_module_exp_fn:
            # Store in the status object. 
            status.skipped_tests.append([methodName, 'Relax curve-fitting C module', self._skip_type])


    def setUp(self):
        """Set up for all the functional tests."""

        # Create the data pipe.
        self.interpreter.pipe.create('mf', 'mf')

        # Create a temporary directory for dumping files.
        ds.tmpdir = mkdtemp()


    def check_curve_fitting(self):
        """Check the results of the curve-fitting."""

        # Data.
        relax_times = [0.0176, 0.0176, 0.0352, 0.0704, 0.0704, 0.1056, 0.1584, 0.1584, 0.1936, 0.1936]
        chi2 = [None, None, None, 2.916952651567855, 5.4916923952919632, 16.21182245065274, 4.3591263759462926, 9.8925377583244316, None, None, None, 6.0238341559877782]
        rx = [None, None, None, 8.0814894819820662, 8.6478971039559642, 9.5710638183013845, 10.716551838066295, 11.143793935455122, None, None, None, 12.82875370075309]
        i0 = [None, None, None, 1996050.9679875025, 2068490.9458927638, 1611556.5194095275, 1362887.2331948928, 1877670.5623875158, None, None, None, 897044.17382064369]

        # Some checks.
        self.assertEqual(cdp.curve_type, 'exp')
        self.assertEqual(cdp.int_method, ds.int_type)
        self.assertEqual(len(cdp.relax_times), 10)
        cdp_relax_times = sorted(cdp.relax_times.values())
        for i in range(10):
            self.assertEqual(cdp_relax_times[i], relax_times[i])

        # Check the errors.
        for key in cdp.sigma_I:
            self.assertAlmostEqual(cdp.sigma_I[key], 10578.039482421433, 6)
            self.assertAlmostEqual(cdp.var_I[key], 111894919.29166669)

        # Spin data check.
        i = 0
        for spin in spin_loop():
            # No data present.
            if chi2[i] == None:
                self.assert_(not hasattr(spin, 'chi2'))

            # Data present.
            else:
                self.assertAlmostEqual(spin.chi2, chi2[i])
                self.assertAlmostEqual(spin.rx, rx[i])
                self.assertAlmostEqual(spin.i0/1e6, i0[i]/1e6)

            # Increment the spin index.
            i = i + 1
            if i >= 12:
                break


    def test_bug_12670_12679(self):
        """Test the relaxation curve fitting, replicating U{bug #12670<https://gna.org/bugs/?12670>} and U{bug #12679<https://gna.org/bugs/?12679>}."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'1UBQ_relax_fit.py')

        # Open the intensities.agr file.
        file = open(ds.tmpdir + sep + 'intensities.agr')
        lines = file.readlines()
        file.close()

        # Loop over all lines.
        for i in range(len(lines)):
            # Find the "@target G0.S0" line.
            if search('@target', lines[i]):
                index = i + 2

            # Split up the lines.
            lines[i] = lines[i].split()

        # Check some of the Grace data.
        self.assertEqual(len(lines[index]), 3)
        self.assertEqual(lines[index][0], '0.004')
        self.assertEqual(lines[index][1], '487178.000000000000000')
        self.assertEqual(lines[index][2], '20570.000000000000000')


    def test_bug_18789(self):
        """Test for zero errors in Grace plots, replicating U{bug #18789<https://gna.org/bugs/?18789>}."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'curve_fitting'+sep+'bug_18789_no_grace_errors.py')

        # Open the Grace file.
        file = open(ds.tmpdir + sep + 'rx.agr')
        lines = file.readlines()
        file.close()

        # Loop over all lines.
        for i in range(len(lines)):
            # Find the "@target G0.S0" line.
            if search('@target', lines[i]):
                index = i + 2

            # Split up the lines.
            lines[i] = lines[i].split()

        # Check for zero errors.
        self.assertEqual(len(lines[index]), 3)
        self.assertNotEqual(float(lines[index][2]), 0.0)
        self.assertNotEqual(float(lines[index+1][2]), 0.0)


    def test_bug_19887_curvefit_fail(self):
        """Test for the failure of relaxation curve-fitting, replicating U{bug #19887<https://gna.org/bugs/?19887>}."""

        # Execute the script.
        try:
            self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'curve_fitting'+sep+'bug_19887_curvefit_fail.py')

        # A RelaxError is expected (but assertRaises() does not work with the script_exec method).
        except RelaxError:
            pass


    def test_curve_fitting_height(self):
        """Test the relaxation curve fitting C modules."""

        # The intensity type.
        ds.int_type = 'height'

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'relax_fit.py')

        # Check the curve-fitting results.
        self.check_curve_fitting()


    def test_curve_fitting_volume(self):
        """Test the relaxation curve fitting C modules."""

        # The intensity type.
        ds.int_type = 'point sum'

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'relax_fit.py')

        # Check the curve-fitting results.
        self.check_curve_fitting()


    def test_read_sparky(self):
        """The Sparky peak height loading test."""

        # Load the original state.
        self.interpreter.state.load(state='basic_heights_T2_ncyc1', dir=status.install_path + sep+'test_suite'+sep+'shared_data'+sep+'saved_states', force=True)

        # Create a new data pipe for the new data.
        self.interpreter.pipe.create('new', 'relax_fit')

        # Load the Lupin Ap4Aase sequence.
        self.interpreter.sequence.read(file="Ap4Aase.seq", dir=status.install_path + sep+'test_suite'+sep+'shared_data', res_num_col=1, res_name_col=2)

        # Name the spins so they can be matched to the assignments.
        self.interpreter.spin.name(name='N')

        # Read the peak heights.
        self.interpreter.spectrum.read_intensities(file="T2_ncyc1_ave.list", dir=status.install_path + sep+'test_suite'+sep+'shared_data'+sep+'curve_fitting', spectrum_id='0.0176')


        # Test the integrity of the data.
        #################################

        # Get the data pipes.
        dp_new = pipes.get_pipe('new')
        dp_rx = pipes.get_pipe('rx')

        # Loop over the spins of the original data.
        for mol_index, res_index, spin_index in spin_index_loop():
            # Alias the spin containers.
            new_spin = dp_new.mol[mol_index].res[res_index].spin[spin_index]
            orig_spin = dp_rx.mol[mol_index].res[res_index].spin[spin_index]

            # Check the sequence info.
            self.assertEqual(dp_new.mol[mol_index].name, dp_rx.mol[mol_index].name)
            self.assertEqual(dp_new.mol[mol_index].res[res_index].num, dp_rx.mol[mol_index].res[res_index].num)
            self.assertEqual(dp_new.mol[mol_index].res[res_index].name, dp_rx.mol[mol_index].res[res_index].name)
            self.assertEqual(new_spin.num, orig_spin.num)
            self.assertEqual(new_spin.name, orig_spin.name)

            # Skip deselected spins.
            if not orig_spin.select:
                continue

            # Check intensities (if they exist).
            if hasattr(orig_spin, 'peak_intensity'):
                for id in dp_new.spectrum_ids:
                    self.assertEqual(orig_spin.peak_intensity[id], new_spin.peak_intensity[id])
