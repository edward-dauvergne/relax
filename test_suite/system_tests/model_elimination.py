###############################################################################
#                                                                             #
# Copyright (C) 2006-2012 Edward d'Auvergne                                   #
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
from os import sep

# relax module imports.
from base_classes import SystemTestCase
from data import Relax_data_store; ds = Relax_data_store()
from generic_fns.mol_res_spin import return_spin
from status import Status; status = Status()


class Modelim(SystemTestCase):
    """Class for testing model selection."""

    def setUp(self):
        """Set up for these system tests."""

        # Create a model-free data pipe.
        self.interpreter.pipe.create('elim', 'mf')


    def test_te_200ns(self):
        """Test the elimination of a model-free model with te = 200 ns."""

        # Read a results file.
        self.interpreter.results.read(file='final_results_trunc_1.3_v2', dir=status.install_path + sep+'test_suite'+sep+'shared_data'+sep+'model_free'+sep+'OMP')

        # Set the te value for residue 11 Leu to 200 ns.
        self.interpreter.value.set(200*1e-9, 'te', spin_id=":11")

        # Model elimination.
        self.interpreter.eliminate()

        # Checks.
        self.assert_(return_spin(':9@N').select)
        self.assert_(return_spin(':10@N').select)
        self.assert_(not return_spin(':11@N').select)
        self.assert_(return_spin(':12@N').select)


    def test_tm_51ns(self):
        """Test the elimination of a model-free model with the local tm = 51 ns."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'local_tm_model_elimination.py')

        # Checks.
        self.assert_(return_spin(':13').select)
        self.assert_(return_spin(':14').select)
        self.assert_(not return_spin(':15').select)
        self.assert_(return_spin(':16').select)
