###############################################################################
#                                                                             #
# Copyright (C) 2003-2013 Edward d'Auvergne                                   #
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
"""Module for model minimisation/optimisation."""

# Python module imports.
from re import search

# relax module imports.
from lib.errors import RelaxError
from multi import Processor_box
from pipe_control.mol_res_spin import return_spin, spin_loop
from pipe_control import pipes
import specific_analyses
from status import Status; status = Status()
from user_functions.data import Uf_tables; uf_tables = Uf_tables()
from user_functions.objects import Desc_container


def calc(verbosity=1):
    """Function for calculating the function value.

    @param verbosity:   The amount of information to print.  The higher the value, the greater
                        the verbosity.
    @type verbosity:    int
    """

    # Test if the current data pipe exists.
    pipes.test()

    # Specific calculate function setup.
    calculate = specific_analyses.setup.get_specific_fn('calculate', cdp.pipe_type)
    overfit_deselect = specific_analyses.setup.get_specific_fn('overfit_deselect', cdp.pipe_type)

    # Deselect spins lacking data:
    overfit_deselect()

    # Get the Processor box singleton (it contains the Processor instance) and alias the Processor.
    processor_box = Processor_box() 
    processor = processor_box.processor

    # Monte Carlo simulation calculation.
    if hasattr(cdp, 'sim_state') and cdp.sim_state == 1:
        # Loop over the simulations.
        for i in range(cdp.sim_number):
            # Status.
            if status.current_analysis:
                status.auto_analysis[status.current_analysis].mc_number = i
            else:
                status.mc_number = i

            # Calculation.
            calculate(verbosity=verbosity-1, sim_index=i)

            # Print out.
            if verbosity and not processor.is_queued():
                print("Simulation " + repr(i+1))

        # Unset the status.
        if status.current_analysis:
            status.auto_analysis[status.current_analysis].mc_number = None
        else:
            status.mc_number = None

    # Minimisation.
    else:
        calculate(verbosity=verbosity)

    # Execute any queued commands.
    processor.run_queue()


def grid_search(lower=None, upper=None, inc=None, constraints=True, verbosity=1):
    """The grid search function.

    @param lower:       The lower bounds of the grid search which must be equal to the number of
                        parameters in the model.
    @type lower:        array of numbers
    @param upper:       The upper bounds of the grid search which must be equal to the number of
                        parameters in the model.
    @type upper:        array of numbers
    @param inc:         The increments for each dimension of the space for the grid search.  The
                        number of elements in the array must equal to the number of parameters in
                        the model.
    @type inc:          array of int
    @param constraints: If True, constraints are applied during the grid search (elinating parts of
                        the grid).  If False, no constraints are used.
    @type constraints:  bool
    @param verbosity:   The amount of information to print.  The higher the value, the greater
                        the verbosity.
    @type verbosity:    int
    """

    # Test if the current data pipe exists.
    pipes.test()

    # Specific grid search function.
    grid_search = specific_analyses.setup.get_specific_fn('grid_search', cdp.pipe_type)
    overfit_deselect = specific_analyses.setup.get_specific_fn('overfit_deselect', cdp.pipe_type)

    # Deselect spins lacking data:
    overfit_deselect()

    # Get the Processor box singleton (it contains the Processor instance) and alias the Processor.
    processor_box = Processor_box() 
    processor = processor_box.processor

    # Monte Carlo simulation grid search.
    if hasattr(cdp, 'sim_state') and cdp.sim_state == 1:
        # Loop over the simulations.
        for i in range(cdp.sim_number):
            # Status.
            if status.current_analysis:
                status.auto_analysis[status.current_analysis].mc_number = i
            else:
                status.mc_number = i

            # Optimisation.
            grid_search(lower=lower, upper=upper, inc=inc, constraints=constraints, verbosity=verbosity-1, sim_index=i)

            # Print out.
            if verbosity and not processor.is_queued():
                print("Simulation " + repr(i+1))

        # Unset the status.
        if status.current_analysis:
            status.auto_analysis[status.current_analysis].mc_number = None
        else:
            status.mc_number = None

    # Grid search.
    else:
        grid_search(lower=lower, upper=upper, inc=inc, constraints=constraints, verbosity=verbosity)

    # Execute any queued commands.
    processor.run_queue()


def minimise(min_algor=None, line_search=None, hessian_mod=None, hessian_type=None, func_tol=None, grad_tol=None, max_iter=None, constraints=True, scaling=True, verbosity=1, sim_index=None):
    """Minimisation function.

    @keyword min_algor:         The minimisation algorithm to use.
    @type min_algor:            str
    @keyword line_search:       The line search algorithm which will only be used in combination with the line search and conjugate gradient methods.  This will default to the More and Thuente line search.
    @type line_search:          str or None
    @keyword hessian_mod:       The Hessian modification.  This will only be used in the algorithms which use the Hessian, and defaults to Gill, Murray, and Wright modified Cholesky algorithm.
    @type hessian_mod:          str or None
    @keyword hessian_type:      The Hessian type.  This will only be used in a few trust region algorithms, and defaults to BFGS.
    @type hessian_type:         str or None
    @keyword func_tol:          The function tolerance which, when reached, terminates optimisation.  Setting this to None turns of the check.
    @type func_tol:             None or float
    @keyword grad_tol:          The gradient tolerance which, when reached, terminates optimisation.  Setting this to None turns of the check.
    @type grad_tol:             None or float
    @keyword max_iter:          The maximum number of iterations for the algorithm.
    @type max_iter:             int
    @keyword constraints:       If True, constraints are used during optimisation.
    @type constraints:          bool
    @keyword scaling:           If True, diagonal scaling is enabled during optimisation to allow the problem to be better conditioned.
    @type scaling:              bool
    @keyword verbosity:         The amount of information to print.  The higher the value, the greater the verbosity.
    @type verbosity:            int
    @keyword sim_index:         The index of the simulation to optimise.  This should be None if normal optimisation is desired.
    @type sim_index:            None or int
    """

    # Test if the current data pipe exists.
    pipes.test()

    # Re-package the minimisation algorithm, options, and constraints for the generic_minimise() calls within the specific code.
    if constraints:
        min_options = [min_algor]

        # Determine the constraint algorithm to use.
        fn = specific_analyses.setup.get_specific_fn('constraint_algorithm', cdp.pipe_type)
        min_algor = fn()
    else:
        min_options = []
    if line_search != None:
        min_options.append(line_search)
    if hessian_mod != None:
        min_options.append(hessian_mod)
    if hessian_type != None:
        min_options.append(hessian_type)
    min_options = tuple(min_options)

    # Specific minimisation function.
    minimise = specific_analyses.setup.get_specific_fn('minimise', cdp.pipe_type)
    overfit_deselect = specific_analyses.setup.get_specific_fn('overfit_deselect', cdp.pipe_type)

    # Deselect spins lacking data:
    overfit_deselect()

    # Get the Processor box singleton (it contains the Processor instance) and alias the Processor.
    processor_box = Processor_box() 
    processor = processor_box.processor

    # Single Monte Carlo simulation.
    if sim_index != None:
        minimise(min_algor=min_algor, min_options=min_options, func_tol=func_tol, grad_tol=grad_tol, max_iterations=max_iter, constraints=constraints, scaling=scaling, verbosity=verbosity, sim_index=sim_index)

    # Monte Carlo simulation minimisation.
    elif hasattr(cdp, 'sim_state') and cdp.sim_state == 1:
        for i in range(cdp.sim_number):
            # Status.
            if status.current_analysis:
                status.auto_analysis[status.current_analysis].mc_number = i
            else:
                status.mc_number = i

            # Optimisation.
            minimise(min_algor=min_algor, min_options=min_options, func_tol=func_tol, grad_tol=grad_tol, max_iterations=max_iter, constraints=constraints, scaling=scaling, verbosity=verbosity-1, sim_index=i)

            # Print out.
            if verbosity and not processor.is_queued():
                print("Simulation " + repr(i+1))

        # Unset the status.
        if status.current_analysis:
            status.auto_analysis[status.current_analysis].mc_number = None
        else:
            status.mc_number = None

    # Standard minimisation.
    else:
        minimise(min_algor=min_algor, min_options=min_options, func_tol=func_tol, grad_tol=grad_tol, max_iterations=max_iter, constraints=constraints, scaling=scaling, verbosity=verbosity)

    # Execute any queued commands.
    processor.run_queue()


def reset_min_stats(data_pipe=None, spin=None):
    """Function for resetting the minimisation statistics.

    @param data_pipe:   The name of the data pipe to reset the minimisation statisics of.  This
                        defaults to the current data pipe.
    @type data_pipe:    str
    @param spin:        The spin data container if spin specific data is to be reset.
    @type spin:         SpinContainer
    """

    # The data pipe.
    if data_pipe == None:
        data_pipe = pipes.cdp_name()

    # Get the data pipe.
    dp = pipes.get_pipe(data_pipe)


    # Global minimisation statistics.
    #################################

    # Chi-squared.
    if hasattr(dp, 'chi2'):
        dp.chi2 = None

    # Iteration count.
    if hasattr(dp, 'iter'):
        dp.iter = None

    # Function count.
    if hasattr(dp, 'f_count'):
        dp.f_count = None

    # Gradient count.
    if hasattr(dp, 'g_count'):
        dp.g_count = None

    # Hessian count.
    if hasattr(dp, 'h_count'):
        dp.h_count = None

    # Warning.
    if hasattr(dp, 'warning'):
        dp.warning = None


    # Sequence specific minimisation statistics.
    ############################################

    # Loop over all spins.
    for spin in spin_loop():
        # Chi-squared.
        if hasattr(spin, 'chi2'):
            spin.chi2 = None

        # Iteration count.
        if hasattr(spin, 'iter'):
            spin.iter = None

        # Function count.
        if hasattr(spin, 'f_count'):
            spin.f_count = None

        # Gradient count.
        if hasattr(spin, 'g_count'):
            spin.g_count = None

        # Hessian count.
        if hasattr(spin, 'h_count'):
            spin.h_count = None

        # Warning.
        if hasattr(spin, 'warning'):
            spin.warning = None


def return_conversion_factor(stat_type):
    """Dummy function for returning 1.0.

    @param stat_type:   The name of the statistic.  This is unused!
    @type stat_type:    str
    @return:            A conversion factor of 1.0.
    @rtype:             float
    """

    return 1.0


return_data_name_doc = Desc_container("Minimisation statistic data type string matching patterns")
table = uf_tables.add_table(label="table: min data type patterns", caption="Minimisation statistic data type string matching patterns.")
table.add_headings(["Data type", "Object name", "Patterns"])
table.add_row(["Chi-squared statistic", "'chi2'", "'^[Cc]hi2$' or '^[Cc]hi[-_ ][Ss]quare'"])
table.add_row(["Iteration count", "'iter'", "'^[Ii]ter'"])
table.add_row(["Function call count", "'f_count'", "'^[Ff].*[ -_][Cc]ount'"])
table.add_row(["Gradient call count", "'g_count'", "'^[Gg].*[ -_][Cc]ount'"])
table.add_row(["Hessian call count", "'h_count'", "'^[Hh].*[ -_][Cc]ount'"])
return_data_name_doc.add_table(table.label)

def return_data_name(name):
    """Return a unique identifying string for the minimisation parameter.

    @param name:    The minimisation parameter.
    @type name:     str
    @return:        The unique parameter identifying string.
    @rtype:         str
    """

    # Chi-squared.
    if search('^[Cc]hi2$', name) or search('^[Cc]hi[-_ ][Ss]quare', name):
        return 'chi2'

    # Iteration count.
    if search('^[Ii]ter', name):
        return 'iter'

    # Function call count.
    if search('^[Ff].*[ -_][Cc]ount', name):
        return 'f_count'

    # Gradient call count.
    if search('^[Gg].*[ -_][Cc]ount', name):
        return 'g_count'

    # Hessian call count.
    if search('^[Hh].*[ -_][Cc]ount', name):
        return 'h_count'


def return_grace_string(stat_type):
    """Function for returning the Grace string representing the data type for axis labelling.

    @param stat_type:   The name of the statistic to return the Grace string for.
    @type stat_type:    str
    @return:            The Grace string.
    @rtype:             str
    """

    # Get the object name.
    object_name = return_data_name(stat_type)

    # Chi-squared.
    if object_name == 'chi2':
        grace_string = '\\xc\\S2'

    # Iteration count.
    elif object_name == 'iter':
        grace_string = 'Iteration count'

    # Function call count.
    elif object_name == 'f_count':
        grace_string = 'Function call count'

    # Gradient call count.
    elif object_name == 'g_count':
        grace_string = 'Gradient call count'

    # Hessian call count.
    elif object_name == 'h_count':
        grace_string = 'Hessian call count'

    # Return the Grace string.
    return grace_string


def return_units(stat_type):
    """Dummy function which returns None as the stats have no units.

    @param stat_type:   The name of the statistic.  This is unused!
    @type stat_type:    str
    @return:            Nothing.
    @rtype:             None
    """

    return None


def return_value(spin=None, stat_type=None, sim=None):
    """Function for returning the minimisation statistic corresponding to 'stat_type'.

    @param spin:        The spin data container if spin specific data is to be reset.
    @type spin:         SpinContainer
    @param stat_type:   The name of the statistic to return the value for.
    @type stat_type:    str
    @param sim:         The index of the simulation to return the value for.  If None, then the
                        normal value is returned.
    @type sim:          None or int
    """

    # Get the object name.
    object_name = return_data_name(stat_type)

    # The statistic type does not exist.
    if not object_name:
        raise RelaxError("The statistic type " + repr(stat_type) + " does not exist.")

    # The simulation object name.
    object_sim = object_name + '_sim'

    # Get the global statistic.
    if spin == None:
        # Get the statistic.
        if sim == None:
            if hasattr(cdp, object_name):
                stat = getattr(cdp, object_name)
            else:
                stat = None

        # Get the simulation statistic.
        else:
            if hasattr(cdp, object_sim):
                stat = getattr(cdp, object_sim)[sim]
            else:
                stat = None

    # Residue specific statistic.
    else:
        # Get the statistic.
        if sim == None:
            if hasattr(spin, object_name):
                stat = getattr(spin, object_name)
            else:
                stat = None

        # Get the simulation statistic.
        else:
            if hasattr(spin, object_sim):
                stat = getattr(spin, object_sim)[sim]
            else:
                stat = None

    # Return the statistic (together with None to indicate that there are no errors associated with the statistic).
    return stat, None


set_doc = """
        Minimisation statistic set details
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        This shouldn't really be executed by a user.
"""

def set(val=None, error=None, param=None, scaling=None, spin_id=None):
    """Set global or spin specific minimisation parameters.

    @keyword val:       The parameter values.
    @type val:          number
    @keyword param:     The parameter names.
    @type param:        str
    @keyword scaling:   Unused.
    @type scaling:      float
    @keyword spin_id:   The spin identification string.
    @type spin_id:      str
    """

    # Get the parameter name.
    param_name = return_data_name(param)

    # Global minimisation stats.
    if spin_id == None:
        # Chi-squared.
        if param_name == 'chi2':
            cdp.chi2 = val

        # Iteration count.
        elif param_name == 'iter':
            cdp.iter = val

        # Function call count.
        elif param_name == 'f_count':
            cdp.f_count = val

        # Gradient call count.
        elif param_name == 'g_count':
            cdp.g_count = val

        # Hessian call count.
        elif param_name == 'h_count':
            cdp.h_count = val

    # Residue specific minimisation.
    else:
        # Get the spin.
        spin = return_spin(spin_id)

        # Chi-squared.
        if param_name == 'chi2':
            spin.chi2 = val

        # Iteration count.
        elif param_name == 'iter':
            spin.iter = val

        # Function call count.
        elif param_name == 'f_count':
            spin.f_count = val

        # Gradient call count.
        elif param_name == 'g_count':
            spin.g_count = val

        # Hessian call count.
        elif param_name == 'h_count':
            spin.h_count = val
