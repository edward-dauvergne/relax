###############################################################################
#                                                                             #
# Copyright (C) 2004-2012 Edward d'Auvergne                                   #
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
"""The relaxation curve fitting specific code."""

# Python module imports.
from minfx.generic import generic_minimise
from minfx.grid import grid
from numpy import array, average, dot, float64, identity, zeros
from numpy.linalg import inv
from re import match, search
from warnings import warn

# relax module imports.
from dep_check import C_module_exp_fn
from generic_fns import pipes
from generic_fns.mol_res_spin import exists_mol_res_spin_data, generate_spin_id, return_spin, spin_loop
from relax_errors import RelaxError, RelaxFuncSetupError, RelaxLenError, RelaxNoModelError, RelaxNoSequenceError
from relax_warnings import RelaxDeselectWarning
from specific_fns.api_base import API_base
from specific_fns.api_common import API_common
from user_functions.data import Uf_tables; uf_tables = Uf_tables()
from user_functions.objects import Desc_container

# C modules.
if C_module_exp_fn:
    from maths_fns.relax_fit import setup, func, dfunc, d2func, back_calc_I


class Relax_fit(API_base, API_common):
    """Class containing functions for relaxation curve fitting."""

    def __init__(self):
        """Initialise the class by placing API_common methods into the API."""

        # Execute the base class __init__ method.
        super(Relax_fit, self).__init__()

        # Place methods into the API.
        self.base_data_loop = self._base_data_loop_spin
        self.model_loop = self._model_loop_spin
        self.return_conversion_factor = self._return_no_conversion_factor
        self.return_value = self._return_value_general
        self.set_error = self._set_error_spin
        self.set_param_values = self._set_param_values_spin
        self.set_selected_sim = self._set_selected_sim_spin
        self.sim_init_values = self._sim_init_values_spin
        self.sim_return_param = self._sim_return_param_spin
        self.sim_return_selected = self._sim_return_selected_spin

        # Set up the spin parameters.
        self.PARAMS.add('intensities', scope='spin', py_type=list, grace_string='\\qPeak intensities\\Q')
        self.PARAMS.add('relax_times', scope='spin', py_type=list, grace_string='\\qRelaxation time period (s)\\Q')
        self.PARAMS.add('rx', scope='spin', default=8.0, desc='Either the R1 or R2 relaxation rate', set='params', py_type=float, grace_string='\\qR\\sx\\Q', err=True, sim=True)
        self.PARAMS.add('i0', scope='spin', default=10000.0, desc='The initial intensity', py_type=float, set='params', grace_string='\\qI\\s0\\Q', err=True, sim=True)
        self.PARAMS.add('iinf', scope='spin', default=0.0, desc='The intensity at infinity', py_type=float, set='params', grace_string='\\qI\\sinf\\Q', err=True, sim=True)
        self.PARAMS.add('params', scope='spin', desc='The model parameters', py_type=list)

        # Add the minimisation data.
        self.PARAMS.add_min_data(min_stats_global=False, min_stats_spin=True)


    def _assemble_param_vector(self, spin=None, sim_index=None):
        """Assemble the exponential curve parameter vector (as a numpy array).

        @keyword spin:          The spin data container.
        @type spin:             SpinContainer instance
        @keyword sim_index:     The optional MC simulation index.
        @type sim_index:        int
        @return:                An array of the parameter values of the exponential model.
        @rtype:                 numpy array
        """

        # Initialise.
        param_vector = []

        # Loop over the model parameters.
        for i in range(len(spin.params)):
            # Relaxation rate.
            if spin.params[i] == 'Rx':
                if sim_index != None:
                    param_vector.append(spin.rx_sim[sim_index])
                elif spin.rx == None:
                    param_vector.append(0.0)
                else:
                    param_vector.append(spin.rx)

            # Initial intensity.
            elif spin.params[i] == 'I0':
                if sim_index != None:
                    param_vector.append(spin.i0_sim[sim_index])
                elif spin.i0 == None:
                    param_vector.append(0.0)
                else:
                    param_vector.append(spin.i0)

            # Intensity at infinity.
            elif spin.params[i] == 'Iinf':
                if sim_index != None:
                    param_vector.append(spin.iinf_sim[sim_index])
                elif spin.iinf == None:
                    param_vector.append(0.0)
                else:
                    param_vector.append(spin.iinf)

        # Return a numpy array.
        return array(param_vector, float64)


    def _assemble_scaling_matrix(self, spin=None, scaling=True):
        """Create and return the scaling matrix.

        @keyword spin:          The spin data container.
        @type spin:             SpinContainer instance
        @keyword scaling:       A flag which if false will cause the identity matrix to be returned.
        @type scaling:          bool
        @return:                The diagonal and square scaling matrix.
        @rtype:                 numpy diagonal matrix
        """

        # Initialise.
        scaling_matrix = identity(len(spin.params), float64)
        i = 0

        # No diagonal scaling.
        if not scaling:
            return scaling_matrix

        # Loop over the parameters.
        for i in range(len(spin.params)):
            # Relaxation rate.
            if spin.params[i] == 'Rx':
                pass

            # Intensity scaling.
            elif search('^i', spin.params[i]):
                # Find the position of the first time point.
                pos = cdp.relax_times.index(min(cdp.relax_times))

                # Scaling.
                scaling_matrix[i, i] = 1.0 / average(spin.intensities[pos])

            # Increment i.
            i = i + 1

        # Return the scaling matrix.
        return scaling_matrix


    def _back_calc(self, spin=None, relax_time_id=None):
        """Back-calculation of peak intensity for the given relaxation time.

        @keyword spin:              The spin container.
        @type spin:                 SpinContainer instance
        @keyword relax_time_id:     The ID string for the desired relaxation time.
        @type relax_time_id:        str
        @return:                    The peak intensity for the desired relaxation time.
        @rtype:                     float
        """

        # Create the initial parameter vector.
        param_vector = self._assemble_param_vector(spin=spin)

        # Create a scaling matrix.
        scaling_matrix = self._assemble_scaling_matrix(spin=spin, scaling=False)

        # The keys.
        keys = list(spin.intensities.keys())

        # The peak intensities and times.
        values = []
        errors = []
        times = []
        for key in keys:
            values.append(spin.intensities[key])
            errors.append(spin.intensity_err[key])
            times.append(cdp.relax_times[key])

        # Initialise the relaxation fit functions.
        setup(num_params=len(spin.params), num_times=len(cdp.relax_times), values=values, sd=errors, relax_times=times, scaling_matrix=scaling_matrix)

        # Make a single function call.  This will cause back calculation and the data will be stored in the C module.
        self._func(param_vector)

        # Get the data back.
        results = back_calc_I()

        # Return the correct peak height.
        return results[keys.index(relax_time_id)]


    def _disassemble_param_vector(self, param_vector=None, spin=None, sim_index=None):
        """Disassemble the parameter vector.

        @keyword param_vector:  The parameter vector.
        @type param_vector:     numpy array
        @keyword spin:          The spin data container.
        @type spin:             SpinContainer instance
        @keyword sim_index:     The optional MC simulation index.
        @type sim_index:        int
        """

        # Monte Carlo simulations.
        if sim_index != None:
            # The relaxation rate.
            spin.rx_sim[sim_index] = param_vector[0]

            # Initial intensity.
            spin.i0_sim[sim_index] = param_vector[1]

            # Intensity at infinity.
            if cdp.curve_type == 'inv':
                spin.iinf_sim[sim_index] = param_vector[2]

        # Parameter values.
        else:
            # The relaxation rate.
            spin.rx = param_vector[0]

            # Initial intensity.
            spin.i0 = param_vector[1]

            # Intensity at infinity.
            if cdp.curve_type == 'inv':
                spin.iinf = param_vector[2]


    def _func(self, params):
        """Wrapper function for the C module, for converting numpy arrays.

        @param params:  The parameter array from the minimisation code.
        @type params:   numpy array
        @return:        The function value generated by the C module.
        @rtype:         float
        """

        # Call the C code.
        chi2 = func(params.tolist())

        # Return the chi2 value.
        return chi2


    def _dfunc(self, params):
        """Wrapper function for the C module, for converting numpy arrays.

        The currently does nothing.
        """


    def _d2func(self, params):
        """Wrapper function for the C module, for converting numpy arrays.

        The currently does nothing.
        """


    def _grid_search_setup(self, spin=None, param_vector=None, lower=None, upper=None, inc=None, scaling_matrix=None):
        """The grid search setup function.

        @keyword spin:              The spin data container.
        @type spin:                 SpinContainer instance
        @keyword param_vector:      The parameter vector.
        @type param_vector:         numpy array
        @keyword lower:             The lower bounds of the grid search which must be equal to the
                                    number of parameters in the model.  This optional argument is
                                    only used when doing a grid search.
        @type lower:                array of numbers
        @keyword upper:             The upper bounds of the grid search which must be equal to the
                                    number of parameters in the model.  This optional argument is
                                    only used when doing a grid search.
        @type upper:                array of numbers
        @keyword inc:               The increments for each dimension of the space for the grid
                                    search.  The number of elements in the array must equal to the
                                    number of parameters in the model.  This argument is only used
                                    when doing a grid search.
        @type inc:                  array of int
        @keyword scaling_matrix:    The scaling matrix.
        @type scaling_matrix:       numpy diagonal matrix
        @return:                    A tuple of the grid size and the minimisation options.  For the
                                    minimisation options, the first dimension corresponds to the
                                    model parameter.  The second dimension is a list of the number
                                    of increments, the lower bound, and upper bound.
        @rtype:                     (int, list of lists [int, float, float])
        """

        # The length of the parameter array.
        n = len(param_vector)

        # Make sure that the length of the parameter array is > 0.
        if n == 0:
            raise RelaxError("Cannot run a grid search on a model with zero parameters.")

        # Lower bounds.
        if lower != None and len(lower) != n:
            raise RelaxLenError('lower bounds', n)

        # Upper bounds.
        if upper != None and len(upper) != n:
            raise RelaxLenError('upper bounds', n)

        # Increments.
        if isinstance(inc, list) and len(inc) != n:
            raise RelaxLenError('increment', n)
        elif isinstance(inc, int):
            inc = [inc]*n

        # Set up the default bounds.
        if not lower:
            # Init.
            lower = []
            upper = []

            # Loop over the parameters.
            for i in range(n):
                # Relaxation rate (from 0 to 20 s^-1).
                if spin.params[i] == 'Rx':
                    lower.append(0.0)
                    upper.append(20.0)

                # Intensity
                elif search('^I', spin.params[i]):
                    # Find the ID of the first time point.
                    min_time = min(cdp.relax_times.values())
                    for key in list(cdp.relax_times.keys()):
                        if cdp.relax_times[key] == min_time:
                            id = key
                            break

                    # Defaults.
                    lower.append(0.0)
                    upper.append(average(spin.intensities[id]))

        # Parameter scaling.
        for i in range(n):
            lower[i] = lower[i] / scaling_matrix[i, i]
            upper[i] = upper[i] / scaling_matrix[i, i]

        return inc, lower, upper


    def _linear_constraints(self, spin=None, scaling_matrix=None):
        """Set up the relaxation curve fitting linear constraint matrices A and b.

        Standard notation
        =================

        The relaxation rate constraints are::

            Rx >= 0

        The intensity constraints are::

            I0 >= 0
            Iinf >= 0


        Matrix notation
        ===============

        In the notation A.x >= b, where A is an matrix of coefficients, x is an array of parameter
        values, and b is a vector of scalars, these inequality constraints are::

            | 1  0  0 |     |  Rx  |      |    0    |
            |         |     |      |      |         |
            | 1  0  0 |  .  |  I0  |  >=  |    0    |
            |         |     |      |      |         |
            | 1  0  0 |     | Iinf |      |    0    |


        @keyword spin:              The spin data container.
        @type spin:                 SpinContainer instance
        @keyword scaling_matrix:    The diagonal, square scaling matrix.
        @type scaling_matrix:       numpy diagonal matrix
        """

        # Initialisation (0..j..m).
        A = []
        b = []
        n = len(spin.params)
        zero_array = zeros(n, float64)
        i = 0
        j = 0

        # Loop over the parameters.
        for k in range(len(spin.params)):
            # Relaxation rate.
            if spin.params[k] == 'Rx':
                # Rx >= 0.
                A.append(zero_array * 0.0)
                A[j][i] = 1.0
                b.append(0.0)
                j = j + 1

            # Intensity parameter.
            elif search('^I', spin.params[k]):
                # I0, Iinf >= 0.
                A.append(zero_array * 0.0)
                A[j][i] = 1.0
                b.append(0.0)
                j = j + 1

            # Increment i.
            i = i + 1

        # Convert to numpy data structures.
        A = array(A, float64)
        b = array(b, float64)

        return A, b


    def _model_setup(self, model, params):
        """Update various model specific data structures.

        @param model:   The exponential curve type.
        @type model:    str
        @param params:  A list consisting of the model parameters.
        @type params:   list of str
        """

        # Set the model.
        cdp.curve_type = model

        # Loop over the sequence.
        for spin in spin_loop():
            # Skip deselected spins.
            if not spin.select:
                continue

            # Initialise the data structures (if needed).
            self.data_init(spin)

            # The model and parameter names.
            spin.model = model
            spin.params = params


    def _relax_time(self, time=0.0, spectrum_id=None):
        """Set the relaxation time period associated with a given spectrum.

        @keyword time:          The time, in seconds, of the relaxation period.
        @type time:             float
        @keyword spectrum_id:   The spectrum identification string.
        @type spectrum_id:      str
        """

        # Test if the spectrum id exists.
        if spectrum_id not in cdp.spectrum_ids:
            raise RelaxError("The peak heights corresponding to spectrum id '%s' have not been loaded." % spectrum_id)

        # Initialise the global relaxation time data structure if needed.
        if not hasattr(cdp, 'relax_times'):
            cdp.relax_times = {}

        # Add the time at the correct position.
        cdp.relax_times[spectrum_id] = time


    def _select_model(self, model='exp'):
        """Function for selecting the model of the exponential curve.

        @keyword model: The exponential curve type.  Can be one of 'exp' or 'inv'.
        @type model:    str
        """

        # Test if the current pipe exists.
        pipes.test()

        # Test if the pipe type is set to 'relax_fit'.
        function_type = cdp.pipe_type
        if function_type != 'relax_fit':
            raise RelaxFuncSetupError(specific_setup.get_string(function_type))

        # Test if sequence data is loaded.
        if not exists_mol_res_spin_data():
            raise RelaxNoSequenceError

        # Two parameter exponential fit.
        if model == 'exp':
            print("Two parameter exponential fit.")
            params = ['Rx', 'I0']

        # Three parameter inversion recovery fit.
        elif model == 'inv':
            print("Three parameter inversion recovery fit.")
            params = ['Rx', 'I0', 'Iinf']

        # Invalid model.
        else:
            raise RelaxError("The model '" + model + "' is invalid.")

        # Set up the model.
        self._model_setup(model, params)


    def create_mc_data(self, data_id=None):
        """Create the Monte Carlo peak intensity data.

        @keyword data_id:   The spin identification string, as yielded by the base_data_loop() generator method.
        @type data_id:      str
        @return:            The Monte Carlo simulation data.
        @rtype:             list of floats
        """

        # Initialise the MC data data structure.
        mc_data = {}

        # Get the spin container.
        spin = return_spin(data_id)

        # Skip deselected spins.
        if not spin.select:
            return

        # Skip spins which have no data.
        if not hasattr(spin, 'intensities'):
            return

        # Test if the model is set.
        if not hasattr(spin, 'model') or not spin.model:
            raise RelaxNoModelError

        # Loop over the spectral time points.
        for id in list(cdp.relax_times.keys()):
            # Back calculate the value.
            value = self._back_calc(spin=spin, relax_time_id=id)

            # Append the value.
            mc_data[id] = value

        # Return the MC data.
        return mc_data


    def data_init(self, data_cont, sim=False):
        """Initialise the spin specific data structures.

        @param data_cont:   The spin container.
        @type data_cont:    SpinContainer instance
        @keyword sim:       The Monte Carlo simulation flag, which if true will initialise the simulation data structure.
        @type sim:          bool
        """

        # Loop over the data structure names.
        for name in self.data_names(set='params'):
            # Data structures which are initially empty arrays.
            list_data = [ 'params' ]
            if name in list_data:
                init_data = []

            # Otherwise initialise the data structure to None.
            else:
                init_data = None

            # If the name is not in 'data_cont', add it.
            if not hasattr(data_cont, name):
                setattr(data_cont, name, init_data)


    default_value_doc = Desc_container("Relaxation curve fitting default values")
    default_value_doc.add_paragraph("These values are completely arbitrary as peak heights (or volumes) are extremely variable and the Rx value is a compensation for both the R1 and R2 values.")
    _table = uf_tables.add_table(label="table: curve-fit default values", caption="Relaxation curve fitting default values.")
    _table.add_headings(["Data type", "Object name", "Value"])
    _table.add_row(["Relaxation rate", "'rx'", "8.0"])
    _table.add_row(["Initial intensity", "'i0'", "10000.0"])
    _table.add_row(["Intensity at infinity", "'iinf'", "0.0"])
    default_value_doc.add_table(_table.label)


    def grid_search(self, lower=None, upper=None, inc=None, constraints=True, verbosity=1, sim_index=None):
        """The exponential curve fitting grid search method.

        @keyword lower:         The lower bounds of the grid search which must be equal to the number of parameters in the model.
        @type lower:            array of numbers
        @keyword upper:         The upper bounds of the grid search which must be equal to the number of parameters in the model.
        @type upper:            array of numbers
        @keyword inc:           The increments for each dimension of the space for the grid search.  The number of elements in the array must equal to the number of parameters in the model.
        @type inc:              array of int
        @keyword constraints:   If True, constraints are applied during the grid search (eliminating parts of the grid).  If False, no constraints are used.
        @type constraints:      bool
        @keyword verbosity:     A flag specifying the amount of information to print.  The higher the value, the greater the verbosity.
        @type verbosity:        int
        @keyword sim_index:     The index of the simulation to apply the grid search to.  If None, the normal model is optimised.
        @type sim_index:        int
        """

        # Minimisation.
        self.minimise(min_algor='grid', lower=lower, upper=upper, inc=inc, constraints=constraints, verbosity=verbosity, sim_index=sim_index)


    def minimise(self, min_algor=None, min_options=None, func_tol=None, grad_tol=None, max_iterations=None, constraints=False, scaling=True, verbosity=0, sim_index=None, lower=None, upper=None, inc=None):
        """Relaxation curve fitting minimisation method.

        @keyword min_algor:         The minimisation algorithm to use.
        @type min_algor:            str
        @keyword min_options:       An array of options to be used by the minimisation algorithm.
        @type min_options:          array of str
        @keyword func_tol:          The function tolerance which, when reached, terminates optimisation.  Setting this to None turns of the check.
        @type func_tol:             None or float
        @keyword grad_tol:          The gradient tolerance which, when reached, terminates optimisation.  Setting this to None turns of the check.
        @type grad_tol:             None or float
        @keyword max_iterations:    The maximum number of iterations for the algorithm.
        @type max_iterations:       int
        @keyword constraints:       If True, constraints are used during optimisation.
        @type constraints:          bool
        @keyword scaling:           If True, diagonal scaling is enabled during optimisation to allow the problem to be better conditioned.
        @type scaling:              bool
        @keyword verbosity:         The amount of information to print.  The higher the value, the greater the verbosity.
        @type verbosity:            int
        @keyword sim_index:         The index of the simulation to optimise.  This should be None if normal optimisation is desired.
        @type sim_index:            None or int
        @keyword lower:             The lower bounds of the grid search which must be equal to the number of parameters in the model.  This optional argument is only used when doing a grid search.
        @type lower:                array of numbers
        @keyword upper:             The upper bounds of the grid search which must be equal to the number of parameters in the model.  This optional argument is only used when doing a grid search.
        @type upper:                array of numbers
        @keyword inc:               The increments for each dimension of the space for the grid search.  The number of elements in the array must equal to the number of parameters in the model.  This argument is only used when doing a grid search.
        @type inc:                  array of int
        """

        # Test if sequence data is loaded.
        if not exists_mol_res_spin_data():
            raise RelaxNoSequenceError

        # Loop over the sequence.
        for spin, mol_name, res_num, res_name in spin_loop(full_info=True):
            # Skip deselected spins.
            if not spin.select:
                continue

            # Skip spins which have no data.
            if not hasattr(spin, 'intensities'):
                continue

            # Create the initial parameter vector.
            param_vector = self._assemble_param_vector(spin=spin)

            # Diagonal scaling.
            scaling_matrix = self._assemble_scaling_matrix(spin=spin, scaling=scaling)
            if len(scaling_matrix):
                param_vector = dot(inv(scaling_matrix), param_vector)

            # Get the grid search minimisation options.
            if match('^[Gg]rid', min_algor):
                inc, lower, upper = self._grid_search_setup(spin=spin, param_vector=param_vector, lower=lower, upper=upper, inc=inc, scaling_matrix=scaling_matrix)

            # Linear constraints.
            if constraints:
                A, b = self._linear_constraints(spin=spin, scaling_matrix=scaling_matrix)
            else:
                A, b = None, None

            # Print out.
            if verbosity >= 1:
                # Get the spin id string.
                spin_id = generate_spin_id(mol_name, res_num, res_name, spin.num, spin.name)

                # Individual spin printout.
                if verbosity >= 2:
                    print("\n\n")

                string = "Fitting to spin " + repr(spin_id)
                print("\n\n" + string)
                print(len(string) * '~')


            # Initialise the function to minimise.
            ######################################

            # The keys.
            keys = list(spin.intensities.keys())

            # The peak intensities and times.
            values = []
            errors = []
            times = []
            for key in keys:
                # The values.
                if sim_index == None:
                    values.append(spin.intensities[key])
                else:
                    values.append(spin.sim_intensities[sim_index][key])

                # The errors.
                errors.append(spin.intensity_err[key])

                # The relaxation times.
                times.append(cdp.relax_times[key])

            setup(num_params=len(spin.params), num_times=len(values), values=values, sd=errors, relax_times=times, scaling_matrix=scaling_matrix.tolist())


            # Setup the minimisation algorithm when constraints are present.
            ################################################################

            if constraints and not match('^[Gg]rid', min_algor):
                algor = min_options[0]
            else:
                algor = min_algor


            # Levenberg-Marquardt minimisation.
            ###################################

            if match('[Ll][Mm]$', algor) or match('[Ll]evenburg-[Mm]arquardt$', algor):
                # Reconstruct the error data structure.
                lm_error = zeros(len(spin.relax_times), float64)
                index = 0
                for k in range(len(spin.relax_times)):
                    lm_error[index:index+len(relax_error[k])] = relax_error[k]
                    index = index + len(relax_error[k])

                min_options = min_options + (self.relax_fit.lm_dri, lm_error)


            # Minimisation.
            ###############

            # Grid search.
            if search('^[Gg]rid', min_algor):
                results = grid(func=self._func, args=(), num_incs=inc, lower=lower, upper=upper, A=A, b=b, verbosity=verbosity)

                # Unpack the results.
                param_vector, chi2, iter_count, warning = results
                f_count = iter_count
                g_count = 0.0
                h_count = 0.0

            # Minimisation.
            else:
                results = generic_minimise(func=self._func, dfunc=self._dfunc, d2func=self._d2func, args=(), x0=param_vector, min_algor=min_algor, min_options=min_options, func_tol=func_tol, grad_tol=grad_tol, maxiter=max_iterations, A=A, b=b, full_output=True, print_flag=verbosity)

                # Unpack the results.
                if results == None:
                    return
                param_vector, chi2, iter_count, f_count, g_count, h_count, warning = results

            # Scaling.
            if scaling:
                param_vector = dot(scaling_matrix, param_vector)

            # Disassemble the parameter vector.
            self._disassemble_param_vector(param_vector=param_vector, spin=spin, sim_index=sim_index)

            # Monte Carlo minimisation statistics.
            if sim_index != None:
                # Chi-squared statistic.
                spin.chi2_sim[sim_index] = chi2

                # Iterations.
                spin.iter_sim[sim_index] = iter_count

                # Function evaluations.
                spin.f_count_sim[sim_index] = f_count

                # Gradient evaluations.
                spin.g_count_sim[sim_index] = g_count

                # Hessian evaluations.
                spin.h_count_sim[sim_index] = h_count

                # Warning.
                spin.warning_sim[sim_index] = warning


            # Normal statistics.
            else:
                # Chi-squared statistic.
                spin.chi2 = chi2

                # Iterations.
                spin.iter = iter_count

                # Function evaluations.
                spin.f_count = f_count

                # Gradient evaluations.
                spin.g_count = g_count

                # Hessian evaluations.
                spin.h_count = h_count

                # Warning.
                spin.warning = warning


    def overfit_deselect(self, data_check=True, verbose=True):
        """Deselect spins which have insufficient data to support minimisation.

        @keyword data_check:    A flag to signal if the presence of base data is to be checked for.
        @type data_check:       bool
        @keyword verbose:       A flag which if True will allow printouts.
        @type verbose:          bool
        """

        # Print out.
        if verbose:
            print("\nOver-fit spin deselection:")

        # Test the sequence data exists.
        if not exists_mol_res_spin_data():
            raise RelaxNoSequenceError

        # Loop over spin data.
        deselect_flag = False
        for spin, spin_id in spin_loop(return_id=True):
            # Skip deselected spins.
            if not spin.select:
                continue

            # Check if data exists.
            if not hasattr(spin, 'intensities'):
                warn(RelaxDeselectWarning(spin_id, 'missing intensity data'))
                spin.select = False
                deselect_flag = True
                continue

            # Require 3 or more data points.
            elif len(spin.intensities) < 3:
                warn(RelaxDeselectWarning(spin_id, 'insufficient data, 3 or more data points are required'))
                spin.select = False
                deselect_flag = True
                continue

            # Check that the number of relaxation times is complete.
            if len(spin.intensities) != len(cdp.relax_times):
                raise RelaxError("The %s peak intensity points of the spin '%s' does not match the expected number of %s (the IDs %s do not match %s)." % (len(spin.intensities), spin_id, len(cdp.relax_times), list(spin.intensities.keys()), list(cdp.relax_times.keys())))

        # Final printout.
        if verbose and not deselect_flag:
            print("No spins have been deselected.")


    def return_data(self, spin):
        """Function for returning the peak intensity data structure.

        @param spin:    The spin container.
        @type spin:     SpinContainer instance
        @return:        The peak intensity data structure.
        @rtype:         list of float
        """

        return spin.intensities


    return_data_name_doc = Desc_container("Relaxation curve fitting data type string matching patterns")
    _table = uf_tables.add_table(label="table: curve-fit data type patterns", caption="Relaxation curve fitting data type string matching patterns.")
    _table.add_headings(["Data type", "Object name"])
    _table.add_row(["Relaxation rate", "'rx'"])
    _table.add_row(["Peak intensities (series)", "'intensities'"])
    _table.add_row(["Initial intensity", "'i0'"])
    _table.add_row(["Intensity at infinity", "'iinf'"])
    _table.add_row(["Relaxation period times (series)", "'relax_times'"])
    return_data_name_doc.add_table(_table.label)


    def return_error(self, data_id):
        """Return the standard deviation data structure.

        @param data_id: The spin identification string, as yielded by the base_data_loop() generator
                        method.
        @type data_id:  str
        @return:        The standard deviation data structure.
        @rtype:         list of float
        """

        # Get the spin container.
        spin = return_spin(data_id)

        # Return the error list.
        return spin.intensity_err


    def return_units(self, param):
        """Dummy method which returns None as the stats have no units.

        @param param:   The name of the parameter to return the units string for.
        @type param:    str
        @return:        Nothing.
        @rtype:         None
        """

        # Unitless.
        return None


    set_doc = Desc_container("Relaxation curve fitting set details")
    set_doc.add_paragraph("Only three parameters can be set, the relaxation rate (Rx), the initial intensity (I0), and the intensity at infinity (Iinf).  Setting the parameter Iinf has no effect if the chosen model is that of the exponential curve which decays to zero.")


    def sim_pack_data(self, data_id, sim_data):
        """Pack the Monte Carlo simulation data.

        @param data_id:     The spin identification string, as yielded by the base_data_loop() generator method.
        @type data_id:      str
        @param sim_data:    The Monte Carlo simulation data.
        @type sim_data:     list of float
        """

        # Get the spin container.
        spin = return_spin(data_id)

        # Create the data structure.
        spin.sim_intensities = sim_data
