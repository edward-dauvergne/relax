###############################################################################
#                                                                             #
# Copyright (C) 2004-2012 Edward d'Auvergne                                   #
# Copyright (C) 2007-2009 Sebastien Morin                                     #
#                                                                             #
# This file is part of the program relax.                                     #
#                                                                             #
# relax is free software; you can redistribute it and/or modify               #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation; either version 2 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# relax is distributed in the hope that it will be useful,                    #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with relax; if not, write to the Free Software                        #
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA   #
#                                                                             #
###############################################################################

# Python module imports.
from re import search
from warnings import warn

# relax module imports.
from api_base import API_base
from api_common import API_common
from generic_fns.mol_res_spin import exists_mol_res_spin_data, return_spin, spin_loop
from generic_fns import pipes
from maths_fns.consistency_tests import Consistency
from physical_constants import N15_CSA, NH_BOND_LENGTH, h_bar, mu0, return_gyromagnetic_ratio
from relax_errors import RelaxError, RelaxFuncSetupError, RelaxNoSequenceError, RelaxNoValueError, RelaxProtonTypeError, RelaxSpinTypeError
from relax_warnings import RelaxDeselectWarning
import specific_fns
from user_functions.data import Uf_tables; uf_tables = Uf_tables()
from user_functions.objects import Desc_container


class Consistency_tests(API_base, API_common):
    """Class containing functions specific to consistency testing."""

    def __init__(self):
        """Initialise the class by placing API_common methods into the API."""

        # Execute the base class __init__ method.
        super(Consistency_tests, self).__init__()

        # Place methods into the API.
        self.base_data_loop = self._base_data_loop_spin
        self.create_mc_data = self._create_mc_relax_data
        self.model_loop = self._model_loop_spin
        self.return_conversion_factor = self._return_no_conversion_factor
        self.return_error = self._return_error_relax_data
        self.return_value = self._return_value_general
        self.set_param_values = self._set_param_values_spin
        self.set_selected_sim = self._set_selected_sim_spin
        self.sim_pack_data = self._sim_pack_relax_data

        # Set up the spin parameters.
        self.PARAMS.add('j0', scope='spin', desc='Spectral density value at 0 MHz (from Farrow et al. (1995) JBNMR, 6: 153-162)', py_type=float, grace_string='\\qJ(0)\\Q', err=True, sim=True)
        self.PARAMS.add('f_eta', scope='spin', desc='Eta-test (from Fushman et al. (1998) JACS, 120: 10947-10952)', py_type=float, grace_string='\\qF\\s\\xh\\Q', err=True, sim=True)
        self.PARAMS.add('f_r2', scope='spin', desc='R2-test (from Fushman et al. (1998) JACS, 120: 10947-10952)', py_type=float, grace_string='\\qF\\sR2\\Q', err=True, sim=True)
        self.PARAMS.add('r', scope='spin', default=NH_BOND_LENGTH, units='Angstrom', desc='Bond length', py_type=float, grace_string='Bond length')
        self.PARAMS.add('csa', scope='spin', default=N15_CSA, units='ppm', desc='CSA value', py_type=float, grace_string='\\qCSA\\Q')
        self.PARAMS.add('heteronuc_type', scope='spin', default='15N', desc='The heteronucleus type', py_type=str)
        self.PARAMS.add('proton_type', scope='spin', default='1H', desc='The proton type', py_type=str)
        self.PARAMS.add('orientation', scope='spin', default=15.7, units='degrees', desc="Angle between the 15N-1H vector and the principal axis of the 15N chemical shift tensor", py_type=float, grace_string='\\q\\xq\\Q')
        self.PARAMS.add('tc', scope='spin', default=13 * 1e-9, units='ns', desc="Correlation time", py_type=float, grace_string='\\q\\xt\\f{}c\\Q')


    def _set_frq(self, frq=None):
        """Function for selecting which relaxation data to use in the consistency tests."""

        # Test if the current pipe exists.
        pipes.test()

        # Test if the pipe type is set to 'ct'.
        function_type = cdp.pipe_type
        if function_type != 'ct':
            raise RelaxFuncSetupError(specific_fns.setup.get_string(function_type))

        # Test if the frequency has been set.
        if hasattr(cdp, 'ct_frq'):
            raise RelaxError("The frequency for the run has already been set.")

        # Create the data structure if it doesn't exist.
        if not hasattr(cdp, 'ct_frq'):
            cdp.ct_frq = {}

        # Set the frequency.
        cdp.ct_frq = frq


    def calculate(self, spin_id=None, verbosity=1, sim_index=None):
        """Calculation of the consistency functions.

        @keyword spin_id:   The spin identification string.
        @type spin_id:      None or str
        @keyword verbosity: The amount of information to print.  The higher the value, the greater the verbosity.
        @type verbosity:    int
        @keyword sim_index: The optional MC simulation index.
        @type sim_index:    None or int
        """

        # Test if the frequency has been set.
        if not hasattr(cdp, 'ct_frq') or not isinstance(cdp.ct_frq, float):
            raise RelaxError("The frequency has not been set up.")

        # Test if the sequence data is loaded.
        if not exists_mol_res_spin_data():
            raise RelaxNoSequenceError

        # Test if the CSA, bond length, angle Theta and correlation time values have been set.
        for spin in spin_loop(spin_id):
            # Skip deselected spins.
            if not spin.select:
                continue

            # Test if the CSA value has been set.
            if not hasattr(spin, 'csa') or spin.csa == None:
                raise RelaxNoValueError("CSA")

            # Test if the bond length has been set.
            if not hasattr(spin, 'r') or spin.r == None:
                raise RelaxNoValueError("bond length")

            # Test if the angle Theta has been set.
            if not hasattr(spin, 'orientation') or spin.orientation == None:
                raise RelaxNoValueError("angle Theta")

            # Test if the correlation time has been set.
            if not hasattr(spin, 'tc') or spin.tc == None:
                raise RelaxNoValueError("correlation time")

            # Test if the spin type has been set.
            if not hasattr(spin, 'heteronuc_type'):
                raise RelaxSpinTypeError

            # Test if the type attached proton has been set.
            if not hasattr(spin, 'proton_type'):
                raise RelaxProtonTypeError

        # Frequency index.
        if cdp.ct_frq not in cdp.frq.values():
            raise RelaxError("No relaxation data corresponding to the frequency %s has been loaded." % cdp.ct_frq)

        # Consistency testing.
        for spin in spin_loop(spin_id):
            # Skip deselected spins.
            if not spin.select:
                continue

            # Set the r1, r2, and NOE to None.
            r1 = None
            r2 = None
            noe = None

            # Get the R1, R2, and NOE values corresponding to the set frequency.
            for ri_id in cdp.ri_ids:
                # The frequency does not match.
                if cdp.frq[ri_id] != cdp.ct_frq:
                    continue

                # R1.
                if cdp.ri_type[ri_id] == 'R1':
                    if sim_index == None:
                        r1 = spin.ri_data[ri_id]
                    else:
                        r1 = spin.ri_data_sim[ri_id][sim_index]

                # R2.
                if cdp.ri_type[ri_id] == 'R2':
                    if sim_index == None:
                        r2 = spin.ri_data[ri_id]
                    else:
                        r2 = spin.ri_data_sim[ri_id][sim_index]

                # NOE.
                if cdp.ri_type[ri_id] == 'NOE':
                    if sim_index == None:
                        noe = spin.ri_data[ri_id]
                    else:
                        noe = spin.ri_data_sim[ri_id][sim_index]

            # Skip the spin if not all of the three value exist.
            if r1 == None or r2 == None or noe == None:
                continue

            # Initialise the function to calculate.
            self.ct = Consistency(frq=cdp.ct_frq, gx=return_gyromagnetic_ratio(spin.heteronuc_type), gh=return_gyromagnetic_ratio(spin.proton_type), mu0=mu0, h_bar=h_bar)

            # Calculate the consistency tests values.
            j0, f_eta, f_r2 = self.ct.func(orientation=spin.orientation, tc=spin.tc, r=spin.r, csa=spin.csa, r1=r1, r2=r2, noe=noe)

            # Consistency tests values.
            if sim_index == None:
                spin.j0 = j0
                spin.f_eta = f_eta
                spin.f_r2 = f_r2

            # Monte Carlo simulated consistency tests values.
            else:
                # Initialise the simulation data structures.
                self.data_init(spin, sim=1)
                if spin.j0_sim == None:
                    spin.j0_sim = []
                    spin.f_eta_sim = []
                    spin.f_r2_sim = []

                # Consistency tests values.
                spin.j0_sim.append(j0)
                spin.f_eta_sim.append(f_eta)
                spin.f_r2_sim.append(f_r2)


    def data_init(self, data_cont, sim=False):
        """Initialise the data structures.

        @param data_cont:   The data container.
        @type data_cont:    instance
        @keyword sim:       The Monte Carlo simulation flag, which if true will initialise the simulation data structure.
        @type sim:          bool
        """

        # Get the data names.
        data_names = self.data_names()

        # Loop over the data structure names.
        for name in data_names:
            # Simulation data structures.
            if sim:
                # Add '_sim' to the names.
                name = name + '_sim'

            # If the name is not in 'data_cont', add it.
            if not hasattr(data_cont, name):
                # Set the attribute.
                setattr(data_cont, name, None)


    default_value_doc = Desc_container("Consistency testing default values")
    default_value_doc.add_paragraph("These default values are found in the file 'physical_constants.py'.")
    _table = uf_tables.add_table(label="table: consistency testing default values", caption="Consistency testing default values.")
    _table.add_headings(["Data type", "Object name", "Value"])
    _table.add_row(["Bond length", "'r'", "1.02 * 1e-10"])
    _table.add_row(["CSA", "'csa'", "-172 * 1e-6"])
    _table.add_row(["Heteronucleus type", "'heteronuc_type'", "'15N'"])
    _table.add_row(["Angle theta", "'proton_type'", "'1H'"])
    _table.add_row(["Proton type", "'orientation'", "15.7"])
    _table.add_row(["Correlation time", "'tc'", "13 * 1e-9"])
    default_value_doc.add_table(_table.label)


    def overfit_deselect(self):
        """Deselect spins which have insufficient data to support calculation."""

        # Print out.
        print("\n\nOver-fit spin deselection.\n")

        # Test the sequence data exists.
        if not exists_mol_res_spin_data():
            raise RelaxNoSequenceError

        # Loop over spin data.
        for spin, spin_id in spin_loop(return_id=True):
            # Skip deselected spins.
            if not spin.select:
                continue

            # Check if data exists.
            if not hasattr(spin, 'ri_data'):
                warn(RelaxDeselectWarning(spin_id, 'missing relaxation data'))
                spin.select = False

            # Require 3 or more data points.
            else:
                # Count the points.
                data_points = 0
                for id in cdp.ri_ids:
                    if spin.ri_data.has_key(id) and spin.ri_data[id] != None:
                        data_points += 1

                # Not enough.
                if data_points < 3:
                    warn(RelaxDeselectWarning(spin_id, 'insufficient relaxation data, 3 or more data points are required'))
                    spin.select = False


    return_data_name_doc = Desc_container("Consistency testing data type string matching patterns")
    _table = uf_tables.add_table(label="table: Consistency testing data types", caption="Consistency testing data type string matching patterns.")
    _table.add_headings(["Data type", "Object name"])
    _table.add_row(["J(0)", "'j0'"])
    _table.add_row(["F_eta", "'f_eta'"])
    _table.add_row(["F_R2", "'f_r2'"])
    _table.add_row(["Bond length", "'r'"])
    _table.add_row(["CSA", "'csa'"])
    _table.add_row(["Heteronucleus type", "'heteronuc_type'"])
    _table.add_row(["Proton type", "'proton_type'"])
    _table.add_row(["Angle theta", "'orientation'"])
    _table.add_row(["Correlation time", "'tc'"])
    return_data_name_doc.add_table(_table.label)


    set_doc = Desc_container("Consistency testing set details")
    set_doc.add_paragraph("In consistency testing, only four values can be set, the bond length, CSA, angle Theta ('orientation') and correlation time values. These must be set prior to the calculation of consistency functions.")


    def set_error(self, model_info, index, error):
        """Set the parameter errors.

        @param model_info:  The spin container originating from model_loop().
        @type model_info:   SpinContainer instance
        @param index:       The index of the parameter to set the errors for.
        @type index:        int
        @param error:       The error value.
        @type error:        float
        """

        # Alias.
        spin = model_info

        # Return J(0) sim data.
        if index == 0:
            spin.j0_err = error

        # Return F_eta sim data.
        if index == 1:
            spin.f_eta_err = error

        # Return F_R2 sim data.
        if index == 2:
            spin.f_r2_err = error


    def sim_return_param(self, model_info, index):
        """Return the array of simulation parameter values.

        @param model_info:  The spin container originating from model_loop().
        @type model_info:   SpinContainer instance
        @param index:       The index of the parameter to return the array of values for.
        @type index:        int
        @return:            The array of simulation parameter values.
        @rtype:             list of float
        """

        # Alias.
        spin = model_info

        # Skip deselected spins.
        if not spin.select:
                return

        # Return J(0) sim data.
        if index == 0:
            return spin.j0_sim

        # Return F_eta sim data.
        if index == 1:
            return spin.f_eta_sim

        # Return F_R2 sim data.
        if index == 2:
            return spin.f_r2_sim


    def sim_return_selected(self, model_info):
        """Return the array of selected simulation flags.

        @param model_info:  The spin container originating from model_loop().
        @type model_info:   SpinContainer instance
        @return:            The array of selected simulation flags.
        @rtype:             list of int
        """

        # Alias.
        spin = model_info

        # Multiple spins.
        return spin.select_sim
