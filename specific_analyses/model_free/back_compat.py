###############################################################################
#                                                                             #
# Copyright (C) 2003-2014 Edward d'Auvergne                                   #
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
"""The model-free analysis relax 1.2 result creation and processing functions.

This module is provided only for backwards compatibility with ancient relax results files.
"""

# Python module imports.
from math import pi
from numpy import float64, array, transpose
from re import search

# relax module imports.
from lib.errors import RelaxError, RelaxInvalidDataError
import pipe_control
from pipe_control.interatomic import define, return_interatom, return_interatom_list
from pipe_control.mol_res_spin import create_spin, generate_spin_id_unique, return_spin, spin_loop
from pipe_control.spectrometer import set_frequency
from specific_analyses.model_free.api import Model_free
from specific_analyses.model_free.uf import model_setup

# The API object.
api_model_free = Model_free()



def determine_version(file_data, verbosity=1):
    """Determine which relax version the results file belongs to.

    @param file_data:   The processed results file data.
    @type file_data:    list of lists of str
    @keyword verbosity: A variable specifying the amount of information to print.  The higher
                        the value, the greater the verbosity.
    @type verbosity:    int
    @return:            The relax version number.
    @rtype:             str
    @raises RelaxError: If the relax version the model-free results file belongs to cannot be
                        determined.
    """

    # relax 1.2 results file (test for the 1.2 header line).
    if len(file_data[0]) > 9 and file_data[0][0:8] == ['Num', 'Name', 'Selected', 'Data_set', 'Nucleus', 'Model', 'Equation', 'Params']:
        version = '1.2'

    # Can't determine the file version.
    else:
        raise RelaxError("Cannot determine the relax version the model-free results file belongs to.")

    # Print out.
    if verbosity:
        print("relax " + version + " model-free results file.")

    # Return the version.
    return version


def fix_params(spin_line, col, verbosity=1):
    """Fix certain parameters depending on the model type.

    @param spin_line:   The line of data for a single spin.
    @type spin_line:    list of str
    @param col:         The column indices.
    @type col:          dict of int
    @keyword verbosity: A variable specifying the amount of information to print.  The higher
                        the value, the greater the verbosity.
    @type verbosity:    int
    """

    # Extract the model type if it exists, otherwise return.
    if spin_line[col['param_set']] != 'None':
        model_type = spin_line[col['param_set']]
    else:
        return

    # Local tm and model-free only model types.
    if model_type == 'local_tm' or model_type == 'mf':
        diff_fixed = True
        mf_fixed = False

    # Diffusion tensor model type.
    elif model_type == 'diff':
        diff_fixed = False
        mf_fixed = True

    # 'all' model type.
    elif model_type == 'all':
        diff_fixed = False
        mf_fixed = False

    # No model type.
    elif model_type == 'None':
        model_type = None
        diff_fixed = None
        mf_fixed = None

    # Print out.
    if verbosity >= 2:
        print("\nFixing parameters based on the model type.")
        print("Model type: " + model_type)
        print("Diffusion tensor fixed: " + repr(diff_fixed))
        print("Model-free parameters fixed: " + repr(mf_fixed))

    # Set the diffusion tensor fixed flag.
    if model_type != 'local_tm' and diff_fixed != None:
        cdp.diff_tensor.set_fixed(diff_fixed)

    # Set the spin specific fixed flags.
    for spin, id in spin_loop(return_id=True):
        if not spin.select:
            continue

        if mf_fixed != None:
            spin.fixed = mf_fixed


def generate_sequence(spin_line, col, verbosity=1):
    """Generate the sequence.

    @param spin_line:   The line of data for a single spin.
    @type spin_line:    list of str
    @param col:         The column indices.
    @type col:          dict of int
    @keyword verbosity: A variable specifying the amount of information to print.  The higher
                        the value, the greater the verbosity.
    @type verbosity:    int
    """

    # The spin info (for relax 1.2).
    if 'num' in col:
        mol_name = None
        res_num = int(spin_line[col['num']])
        res_name = spin_line[col['name']]
        spin_num = None
        spin_name = None
        if col['nucleus'] < len(spin_line) and search('N', spin_line[col['nucleus']]):
            spin_name = 'N'
        if col['nucleus'] < len(spin_line) and search('C', spin_line[col['nucleus']]):
            spin_name = 'C'

    # The spin info.
    else:
        mol_name = spin_line[col['mol_name']]
        res_num = int(spin_line[col['res_num']])
        res_name = spin_line[col['res_name']]
        spin_num = int(spin_line[col['spin_num']])
        spin_name = spin_line[col['spin_name']]

    # Generate the sequence.
    pipe_control.sequence.generate(mol_name, res_num, res_name, spin_num, spin_name, verbose=False)

    # Get the spin identification string.
    spin_id = generate_spin_id_unique(mol_name=mol_name, res_num=res_num, res_name=res_name, spin_num=spin_num, spin_name=spin_name)

    # Set the selection status.
    select = bool(int(spin_line[col['select']]))
    if select:
        pipe_control.selection.sel_spin(spin_id)
    else:
        pipe_control.selection.desel_spin(spin_id)


def load_model_free_data(spin_line, col, data_set, spin, spin_id, verbosity=1):
    """Read the model-free data for the spin.

    @param spin_line:   The line of data for a single spin.
    @type spin_line:    list of str
    @param col:         The column indices.
    @type col:          dict of int
    @param data_set:    The data set type, one of 'value', 'error', or 'sim_xxx' (where xxx is
                        a number).
    @type data_set:     str
    @param spin:        The spin container.
    @type spin:         SpinContainer instance
    @param spin_id:     The spin identification string.
    @type spin_id:      str
    @keyword verbosity: A variable specifying the amount of information to print.  The higher
                        the value, the greater the verbosity.
    @type verbosity:    int
    """

    # Set up the model-free models.
    if data_set == 'value':
        # Get the model-free model.
        model = spin_line[col['model']]
        if model == 'None':
            model = None

        # Get the model-free equation.
        equation = spin_line[col['eqi']]
        if equation == 'None':
            equation = None

        # Get the model-free parameters.
        params = eval(spin_line[col['params']])

        # Loop over and convert the parameters.
        if params:
            for i in range(len(params)):
                # Fix for the 1.2 relax versions whereby the parameter 'tm' was renamed to 'local_tm' (which occurred in version 1.2.5).
                if params[i] == 'tm':
                    params[i] = 'local_tm'

                # Lower case conversion.
                params[i] = params[i].lower()

        # Set up the model-free model.
        model_setup(model=model, equation=equation, params=params, spin_id=spin_id)

    # The model type.
    model_type = spin_line[col['param_set']]

    # Get the interatomic data container.
    interatom = return_interatom_list(spin_id)[0]

    # Values.
    if data_set == 'value':
        # S2.
        try:
            spin.s2 = float(spin_line[col['s2']]) * api_model_free.return_conversion_factor('s2')
        except ValueError:
            spin.s2 = None

        # S2f.
        try:
            spin.s2f = float(spin_line[col['s2f']]) * api_model_free.return_conversion_factor('s2f')
        except ValueError:
            spin.s2f = None

        # S2s.
        try:
            spin.s2s = float(spin_line[col['s2s']]) * api_model_free.return_conversion_factor('s2s')
        except ValueError:
            spin.s2s = None

        # Local tm.
        try:
            spin.local_tm = float(spin_line[col['local_tm']]) * api_model_free.return_conversion_factor('local_tm')
        except ValueError:
            spin.local_tm = None

        # te.
        try:
            spin.te = float(spin_line[col['te']]) * api_model_free.return_conversion_factor('te')
        except ValueError:
            spin.te = None

        # tf.
        try:
            spin.tf = float(spin_line[col['tf']]) * api_model_free.return_conversion_factor('tf')
        except ValueError:
            spin.tf = None

        # ts.
        try:
            spin.ts = float(spin_line[col['ts']]) * api_model_free.return_conversion_factor('ts')
        except ValueError:
            spin.ts = None

        # Rex.
        try:
            spin.rex = float(spin_line[col['rex']]) * api_model_free.return_conversion_factor('rex')
        except ValueError:
            spin.rex = None

        # CSA.
        try:
            spin.csa = float(spin_line[col['csa']]) * api_model_free.return_conversion_factor('csa')
        except ValueError:
            spin.csa = None

        # Minimisation details (global minimisation results).
        if model_type == 'diff' or model_type == 'all':
            cdp.chi2 = eval(spin_line[col['chi2']])
            cdp.iter = eval(spin_line[col['iter']])
            cdp.f_count = eval(spin_line[col['f_count']])
            cdp.g_count = eval(spin_line[col['g_count']])
            cdp.h_count = eval(spin_line[col['h_count']])
            if spin_line[col['warn']] == 'None':
                cdp.warning = None
            else:
                cdp.warning = spin_line[col['warn']].replace('_', ' ')

        # Minimisation details (individual residue results).
        else:
            spin.chi2 = eval(spin_line[col['chi2']])
            spin.iter = eval(spin_line[col['iter']])
            spin.f_count = eval(spin_line[col['f_count']])
            spin.g_count = eval(spin_line[col['g_count']])
            spin.h_count = eval(spin_line[col['h_count']])
            if spin_line[col['warn']] == 'None':
                spin.warning = None
            else:
                spin.warning = spin_line[col['warn']].replace('_', ' ')

        # Interatomic distances.
        try:
            interatom.r = float(spin_line[col['r']]) * 1e-10
        except ValueError:
            interatom.r = None

    # Errors.
    if data_set == 'error':
        # S2.
        try:
            spin.s2_err = float(spin_line[col['s2']]) * api_model_free.return_conversion_factor('s2')
        except ValueError:
            spin.s2_err = None

        # S2f.
        try:
            spin.s2f_err = float(spin_line[col['s2f']]) * api_model_free.return_conversion_factor('s2f')
        except ValueError:
            spin.s2f_err = None

        # S2s.
        try:
            spin.s2s_err = float(spin_line[col['s2s']]) * api_model_free.return_conversion_factor('s2s')
        except ValueError:
            spin.s2s_err = None

        # Local tm.
        try:
            spin.local_tm_err = float(spin_line[col['local_tm']]) * api_model_free.return_conversion_factor('local_tm')
        except ValueError:
            spin.local_tm_err = None

        # te.
        try:
            spin.te_err = float(spin_line[col['te']]) * api_model_free.return_conversion_factor('te')
        except ValueError:
            spin.te_err = None

        # tf.
        try:
            spin.tf_err = float(spin_line[col['tf']]) * api_model_free.return_conversion_factor('tf')
        except ValueError:
            spin.tf_err = None

        # ts.
        try:
            spin.ts_err = float(spin_line[col['ts']]) * api_model_free.return_conversion_factor('ts')
        except ValueError:
            spin.ts_err = None

        # Rex.
        try:
            spin.rex_err = float(spin_line[col['rex']]) * api_model_free.return_conversion_factor('rex')
        except ValueError:
            spin.rex_err = None

        # CSA.
        try:
            spin.csa_err = float(spin_line[col['csa']]) * api_model_free.return_conversion_factor('csa')
        except ValueError:
            spin.csa_err = None

    # Construct the simulation data structures.
    if data_set == 'sim_0':
        # Get the parameter object names.
        param_names = api_model_free.data_names(set='params', scope='spin')

        # Get the minimisation statistic object names.
        min_names = api_model_free.data_names(set='min', scope='spin')

        # Loop over all the parameter names.
        for object_name in param_names:
            # Name for the simulation object.
            sim_object_name = object_name + '_sim'

            # Create the simulation object.
            setattr(spin, sim_object_name, [])

        # Loop over all the minimisation object names.
        for object_name in min_names:
            # Name for the simulation object.
            sim_object_name = object_name + '_sim'

            # Create the simulation object.
            if model_type == 'diff' or model_type == 'all':
                setattr(cdp, sim_object_name, [])
                object = getattr(cdp, sim_object_name)
                object = []
            else:
                setattr(spin, sim_object_name, [])

    # Simulations.
    if data_set != 'value' and data_set != 'error':
        # S2.
        try:
            spin.s2_sim.append(float(spin_line[col['s2']]) * api_model_free.return_conversion_factor('s2'))
        except ValueError:
            spin.s2_sim.append(None)

        # S2f.
        try:
            spin.s2f_sim.append(float(spin_line[col['s2f']]) * api_model_free.return_conversion_factor('s2f'))
        except ValueError:
            spin.s2f_sim.append(None)

        # S2s.
        try:
            spin.s2s_sim.append(float(spin_line[col['s2s']]) * api_model_free.return_conversion_factor('s2s'))
        except ValueError:
            spin.s2s_sim.append(None)

        # Local tm.
        try:
            spin.local_tm_sim.append(float(spin_line[col['local_tm']]) * api_model_free.return_conversion_factor('local_tm'))
        except ValueError:
            spin.local_tm_sim.append(None)

        # te.
        try:
            spin.te_sim.append(float(spin_line[col['te']]) * api_model_free.return_conversion_factor('te'))
        except ValueError:
            spin.te_sim.append(None)

        # tf.
        try:
            spin.tf_sim.append(float(spin_line[col['tf']]) * api_model_free.return_conversion_factor('tf'))
        except ValueError:
            spin.tf_sim.append(None)

        # ts.
        try:
            spin.ts_sim.append(float(spin_line[col['ts']]) * api_model_free.return_conversion_factor('ts'))
        except ValueError:
            spin.ts_sim.append(None)

        # Rex.
        try:
            spin.rex_sim.append(float(spin_line[col['rex']]) * api_model_free.return_conversion_factor('rex'))
        except ValueError:
            spin.rex_sim.append(None)

        # CSA.
        try:
            spin.csa_sim.append(float(spin_line[col['csa']]) * api_model_free.return_conversion_factor('csa'))
        except ValueError:
            spin.csa_sim.append(None)

        # Minimisation details (global minimisation results).
        if model_type == 'diff' or model_type == 'all':
            # The simulation index.
            index = int(data_set.split('_')[1])

            # Already loaded.
            if len(cdp.chi2_sim) == index + 1:
                return

            # Set the values.
            cdp.chi2_sim.append(eval(spin_line[col['chi2']]))
            cdp.iter_sim.append(eval(spin_line[col['iter']]))
            cdp.f_count_sim.append(eval(spin_line[col['f_count']]))
            cdp.g_count_sim.append(eval(spin_line[col['g_count']]))
            cdp.h_count_sim.append(eval(spin_line[col['h_count']]))
            if spin_line[col['warn']] == 'None':
                cdp.warning_sim.append(None)
            else:
                cdp.warning_sim.append(spin_line[col['warn']].replace('_', ' '))

        # Minimisation details (individual residue results).
        else:
            spin.chi2_sim.append(eval(spin_line[col['chi2']]))
            spin.iter_sim.append(eval(spin_line[col['iter']]))
            spin.f_count_sim.append(eval(spin_line[col['f_count']]))
            spin.g_count_sim.append(eval(spin_line[col['g_count']]))
            spin.h_count_sim.append(eval(spin_line[col['h_count']]))
            if spin_line[col['warn']] == 'None':
                spin.warning_sim.append(None)
            else:
                spin.warning_sim.append(spin_line[col['warn']].replace('_', ' '))


def load_relax_data(spin_line, col, data_set, spin, verbosity=1):
    """Load the relaxation data.

    @param spin_line:   The line of data for a single spin.
    @type spin_line:    list of str
    @param col:         The column indices.
    @type col:          dict of int
    @param data_set:    The data set type, one of 'value', 'error', or 'sim_xxx' (where xxx is
                        a number).
    @type data_set:     str
    @param spin:        The spin container.
    @type spin:         SpinContainer instance
    @keyword verbosity: A variable specifying the amount of information to print.  The higher
                        the value, the greater the verbosity.
    @type verbosity:    int
    """

    # Skip the error 'data_set'.
    if data_set == 'error':
        return

    # Relaxation data structures.
    ri_labels = eval(spin_line[col['ri_labels']])
    remap_table = eval(spin_line[col['remap_table']])
    frq_labels = eval(spin_line[col['frq_labels']])
    frq = eval(spin_line[col['frq']])

    # No relaxation data.
    if not ri_labels:
        return

    # Initialise the value and error arrays.
    values = []
    errors = []

    # Loop over the relaxation data of the residue.
    for i in range(len(ri_labels)):
        # Determine the data and error columns for this relaxation data set.
        data_col = col['frq'] + i + 1
        error_col = col['frq'] + len(ri_labels) + i + 1

        # Append the value and error.
        values.append(eval(spin_line[data_col]))
        errors.append(eval(spin_line[error_col]))

    # Simulations.
    sim = True
    if data_set == 'value' or data_set == 'error':
        sim = False

    # Loop over the relaxation data sets.
    for i in range(len(ri_labels)):
        # The ID string.
        ri_id = "%s_%s" % (ri_labels[i], frq_labels[remap_table[i]])

        # Initialise the global structures if necessary.
        if not hasattr(cdp, 'ri_ids'):
            cdp.ri_ids = []
        if not hasattr(cdp, 'ri_type'):
            cdp.ri_type = {}

        # Update the global structures if necessary.
        if ri_id not in cdp.ri_ids:
            cdp.ri_ids.append(ri_id)
            cdp.ri_type[ri_id] = ri_labels[i]
            set_frequency(id=ri_id, frq=frq[remap_table[i]])

        # Simulation data.
        if sim:
            # Initialise.
            if not hasattr(spin, 'ri_data_sim'):
                spin.ri_data_sim = {}

            # Set the value.
            spin.ri_data_sim[ri_id] = values[i]

        # Normal data.
        else:
            # Initialise.
            if not hasattr(spin, 'ri_data'):
                spin.ri_data = {}
            if not hasattr(spin, 'ri_data_err'):
                spin.ri_data_err = {}

            # Set the value.
            if values[i] != None:
                spin.ri_data[ri_id] = values[i]
            if errors[i] != None:
                spin.ri_data_err[ri_id] = errors[i]


def load_structure(spin_line, col, verbosity=1):
    """Load the structure back into the current data pipe.

    @param spin_line:   The line of data for a single spin.
    @type spin_line:    list of str
    @param col:         The column indices.
    @type col:          dict of int
    @keyword verbosity: A variable specifying the amount of information to print.  The higher
                        the value, the greater the verbosity.
    @type verbosity:    int
    @return:            True if the structure was loaded, False otherwise.
    @rtype:             bool
    """

    # File name.
    pdb = spin_line[col['pdb']]

    # PDB model.
    pdb_model = eval(spin_line[col['pdb_model']])

    # Read the PDB file (if it exists).
    if not pdb == 'None':
        pipe_control.structure.main.read_pdb(file=pdb, set_model_num=pdb_model, fail=False, verbosity=verbosity)
        return True
    else:
        return False


def read_1_2_col_numbers(header):
    """Determine the column indices from the header line.

    @param header:      The header line.
    @type header:       list of str
    @return:            The column indices.
    @rtype:             dictionary of int
    """

    # Initialise the dictionary of column indices.
    col = {}

    # Loop over the columns.
    for i in range(len(header)):
        # Residue info (for relax 1.2).
        if header[i] == 'Num':
            col['num'] = i
        elif header[i] == 'Name':
            col['name'] = i

        # Spin information.
        elif header[i] == 'Spin_id':
            col['spin_id'] = i
        elif header[i] == 'Selected':
            col['select'] = i
        elif header[i] == 'Data_set':
            col['data_set'] = i
        elif header[i] == 'Nucleus':
            col['nucleus'] = i
        elif header[i] == 'Model':
            col['model'] = i
        elif header[i] == 'Equation':
            col['eqi'] = i
        elif header[i] == 'Params':
            col['params'] = i
        elif header[i] == 'Param_set':
            col['param_set'] = i

        # Parameters.
        elif header[i] == 'S2':
            col['s2'] = i
        elif header[i] == 'S2f':
            col['s2f'] = i
        elif header[i] == 'S2s':
            col['s2s'] = i
        elif search('^Local_tm', header[i]):
            col['local_tm'] = i
        elif search('^te', header[i]):
            col['te'] = i
        elif search('^tf', header[i]):
            col['tf'] = i
        elif search('^ts', header[i]):
            col['ts'] = i
        elif search('^Rex', header[i]):
            col['rex'] = i
        elif search('^Bond_length', header[i]):
            col['r'] = i
        elif search('^CSA', header[i]):
            col['csa'] = i

        # Minimisation info.
        elif header[i] == 'Chi-squared':
            col['chi2'] = i
        elif header[i] == 'Iter':
            col['iter'] = i
        elif header[i] == 'f_count':
            col['f_count'] = i
        elif header[i] == 'g_count':
            col['g_count'] = i
        elif header[i] == 'h_count':
            col['h_count'] = i
        elif header[i] == 'Warning':
            col['warn'] = i

        # Diffusion tensor (for relax 1.2).
        elif header[i] == 'Diff_type':
            col['diff_type'] = i
        elif header[i] == 'tm_(s)':
            col['tm'] = i
        elif header[i] == 'Da_(1/s)':
            col['da'] = i
        elif header[i] == 'theta_(deg)':
            col['theta'] = i
        elif header[i] == 'phi_(deg)':
            col['phi'] = i
        elif header[i] == 'Da_(1/s)':
            col['da'] = i
        elif header[i] == 'Dr_(1/s)':
            col['dr'] = i
        elif header[i] == 'alpha_(deg)':
            col['alpha'] = i
        elif header[i] == 'beta_(deg)':
            col['beta'] = i
        elif header[i] == 'gamma_(deg)':
            col['gamma'] = i

        # PDB and XH vector (for relax 1.2).
        elif header[i] == 'PDB':
            col['pdb'] = i
        elif header[i] == 'PDB_model':
            col['pdb_model'] = i
        elif header[i] == 'PDB_heteronuc':
            col['pdb_heteronuc'] = i
        elif header[i] == 'PDB_proton':
            col['pdb_proton'] = i
        elif header[i] == 'XH_vector':
            col['xh_vect'] = i

        # Relaxation data (for relax 1.2).
        elif header[i] == 'Ri_labels':
            col['ri_labels'] = i
        elif header[i] == 'Remap_table':
            col['remap_table'] = i
        elif header[i] == 'Frq_labels':
            col['frq_labels'] = i
        elif header[i] == 'Frequencies':
            col['frq'] = i

    # Return the column indices.
    return col


def read_1_2_results(file_data, verbosity=1):
    """Read the relax 1.2 model-free results file.

    @param file_data:   The processed results file data.
    @type file_data:    list of lists of str
    @keyword verbosity: A variable specifying the amount of information to print.  The higher
                        the value, the greater the verbosity.
    @type verbosity:    int
    """

    # Extract and remove the header.
    header = file_data[0]
    file_data = file_data[1:]

    # Sort the column numbers.
    col = read_1_2_col_numbers(header)

    # Test the file.
    if len(col) < 2:
        raise RelaxInvalidDataError

    # Initialise some data structures and flags.
    sim_num = None
    sims = []
    all_select_sim = []
    diff_data_set = False
    diff_error_set = False
    diff_sim_set = None
    model_type = None
    pdb = False
    pdb_model = None
    pdb_heteronuc = None
    pdb_proton = None
    ri_labels = None

    # Generate the sequence.
    if verbosity:
        print("\nGenerating the sequence.")
    for file_line in file_data:
        # The data set.
        data_set = file_line[col['data_set']]

        # Stop creating the sequence once the data_set is no longer 'value'.
        if data_set != 'value':
            break

        # Sequence.
        generate_sequence(file_line, col, verbosity)

    # Count the number of simulations.
    for file_line in file_data:
        # The data set.
        data_set = file_line[col['data_set']]

        # Simulation number.
        if data_set != 'value' and data_set != 'error':
            # Extract the number from the data_set string.
            sim_num = data_set.split('_')
            try:
                sim_num = int(sim_num[1])
            except:
                raise RelaxError("The simulation number '%s' is invalid." % sim_num)
    if sim_num != None:
        cdp.sim_number = sim_num + 1

    # Loop over the lines of the file data.
    for file_line in file_data:
        # The data set.
        data_set = file_line[col['data_set']]

        # The spin info (for relax 1.2).
        if 'num' in col:
            mol_name = None
            res_num = int(file_line[col['num']])
            res_name = file_line[col['name']]
            spin_num = None
            spin_name = None
            if col['nucleus'] < len(file_line) and search('N', file_line[col['nucleus']]):
                spin_name = 'N'
            if col['nucleus'] < len(file_line) and search('C', file_line[col['nucleus']]):
                spin_name = 'C'

        # The spin info.
        else:
            mol_name = file_line[col['mol_name']]
            res_num = int(file_line[col['res_num']])
            res_name = file_line[col['res_name']]
            spin_num = int(file_line[col['spin_num']])
            spin_name = file_line[col['spin_name']]

        # Create the spin ID.
        spin_id = generate_spin_id_unique(mol_name=mol_name, res_num=res_num, res_name=res_name, spin_num=spin_num, spin_name=spin_name)

        # Get the spin container.
        spin = return_spin(spin_id)

        # Create a new spin container for the proton, then set up a dipole interaction between the two spins.
        if data_set == 'value' and spin_name:
            h_spin = create_spin(mol_name=mol_name, res_num=res_num, res_name=res_name, spin_name='H')
            h_spin.select = False
            h_spin.element = 'H'
            h_spin.isotope = '1H'
            spin_id2 = generate_spin_id_unique(mol_name=mol_name, res_num=res_num, res_name=res_name, spin_name='H')
            define(spin_id, spin_id2, verbose=False)

        # Backwards compatibility for the reading of the results file from versions 1.2.0 to 1.2.9.
        if len(file_line) == 4:
            continue

        # Set the nuclear isotope types and spin names (absent from the 1.2 results file).
        if data_set == 'value':
            if file_line[col['nucleus']] != 'None':
                if search('N', file_line[col['nucleus']]):
                    spin.isotope = '15N'
                    if spin.name == None:
                        spin.name = 'N'
                elif search('C', file_line[col['nucleus']]):
                    spin.isotope = '13C'
                    if spin.name == None:
                        spin.name = 'C'

        # Simulation number.
        if data_set != 'value' and data_set != 'error':
            # Extract the number from the data_set string.
            sim_num = data_set.split('_')
            try:
                sim_num = int(sim_num[1])
            except:
                raise RelaxError("The simulation number '%s' is invalid." % sim_num)

            # A new simulation number.
            if sim_num not in sims:
                # Update the sims array and append an empty array to the selected sims array.
                sims.append(sim_num)
                all_select_sim.append([])

            # Selected simulations.
            all_select_sim[-1].append(bool(file_line[col['select']]))

            # Initial printout for the simulation.
            if verbosity:
                if diff_sim_set == None:
                    print("\nLoading simulations.")
                if sim_num != diff_sim_set:
                    print(data_set)

        # Diffusion tensor data.
        if data_set == 'value' and not diff_data_set:
            read_1_2_set_diff_tensor(file_line, col, data_set, verbosity, sim_num=sim_num)
            diff_data_set = True

        # Diffusion tensor errors.
        elif data_set == 'error' and not diff_error_set:
            read_1_2_set_diff_tensor(file_line, col, data_set, verbosity, sim_num=sim_num)
            diff_error_set = True

        # Diffusion tensor simulation data.
        elif data_set != 'value' and data_set != 'error' and sim_num != diff_sim_set:
            # Set up the diffusion tensor.
            if not hasattr(cdp.diff_tensor, '_sim_num') or cdp.diff_tensor._sim_num == None:
                cdp.diff_tensor.set_sim_num(cdp.sim_number)

            read_1_2_set_diff_tensor(file_line, col, data_set, verbosity, sim_num=sim_num)
            diff_sim_set = sim_num

        # Model type.
        if model_type == None:
            fix_params(file_line, col, verbosity)

        # PDB.
        if not pdb:
            if load_structure(file_line, col, verbosity):
                pdb = True

        # XH vector, heteronucleus, and proton.
        if data_set == 'value':
            set_xh_vect(file_line, col, spin, spin_id1=spin_id, spin_id2=spin_id2, verbosity=verbosity)

        # Relaxation data.
        load_relax_data(file_line, col, data_set, spin, verbosity)

        # Model-free data.
        load_model_free_data(file_line, col, data_set, spin, spin_id, verbosity)

    # Set up the simulations.
    if len(sims):
        # Convert the selected simulation array of arrays into a Numeric matrix, transpose it, then convert back to a Python list.
        all_select_sim = transpose(array(all_select_sim))
        all_select_sim = all_select_sim.tolist()

        # Set up the Monte Carlo simulations.
        pipe_control.monte_carlo.setup(number=len(sims), all_select_sim=all_select_sim)

        # Turn the simulation state to off!
        cdp.sim_state = False


def read_1_2_set_diff_tensor(spin_line, col, data_set, verbosity=1, sim_num=None):
    """Set up the diffusion tensor.

    @param spin_line:   The line of data for a single spin.
    @type spin_line:    list of str
    @param col:         The column indices.
    @type col:          dict of int
    @param data_set:    The data set type, one of 'value', 'error', or 'sim_xxx' (where xxx is a number).
    @type data_set:     str
    @keyword verbosity: A variable specifying the amount of information to print.  The higher the value, the greater the verbosity.
    @type verbosity:    int
    @keyword sim_num:   The Monte Carlo simulation index.
    @type sim_num:      int or None
    """

    # The diffusion tensor type.
    diff_type = spin_line[col['diff_type']]
    if diff_type == 'None':
        diff_type = None

    # Print out.
    if diff_type and data_set == 'value' and verbosity:
        print("\nSetting the diffusion tensor.")
        print("Diffusion type: " + diff_type)

    # Sphere.
    if diff_type == 'sphere':
        # Convert the parameters to floating point numbers.
        try:
            tm = float(spin_line[col['tm']])
        except ValueError:
            # Errors or simulation values set to None.
            if data_set != 'value' and spin_line[col['tm']] == 'None':
                return

            # Genuine error.
            raise RelaxError("The diffusion tensor parameters are not numbers.")

        # Values.
        if data_set == 'value':
            diff_params = tm

        # Errors.
        elif data_set == 'error':
            cdp.diff_tensor.set(param='tm', value=tm, category='err')

        # Simulation values.
        else:
            # Set the value.
            cdp.diff_tensor.set(param='tm', value=tm, category='sim', sim_index=sim_num)


    # Spheroid.
    elif diff_type == 'spheroid' or diff_type == 'oblate' or diff_type == 'prolate':
        # Convert the parameters to floating point numbers.
        try:
            tm = float(spin_line[col['tm']])
            Da = float(spin_line[col['da']])
            theta = float(spin_line[col['theta']]) / 360.0 * 2.0 * pi
            phi = float(spin_line[col['phi']]) / 360.0 * 2.0 * pi
        except ValueError:
            # Errors or simulation values set to None.
            if data_set != 'value' and spin_line[col['tm']] == 'None':
                return

            # Genuine error.
            raise RelaxError("The diffusion tensor parameters are not numbers.")

        # Values.
        if data_set == 'value':
            diff_params = [tm, Da, theta, phi]

        # Errors.
        elif data_set == 'error':
            cdp.diff_tensor.set(param='tm', value=tm, category='err')
            cdp.diff_tensor.set(param='Da', value=Da, category='err')
            cdp.diff_tensor.set(param='theta', value=theta, category='err')
            cdp.diff_tensor.set(param='phi', value=phi, category='err')

        # Simulation values.
        else:
            # Set the values.
            cdp.diff_tensor.set(param='tm', value=tm, category='sim', sim_index=sim_num)
            cdp.diff_tensor.set(param='Da', value=Da, category='sim', sim_index=sim_num)
            cdp.diff_tensor.set(param='theta', value=theta, category='sim', sim_index=sim_num)
            cdp.diff_tensor.set(param='phi', value=phi, category='sim', sim_index=sim_num)


    # Ellipsoid.
    elif diff_type == 'ellipsoid':
        # Convert the parameters to floating point numbers.
        try:
            tm = float(spin_line[col['tm']])
            Da = float(spin_line[col['da']])
            Dr = float(spin_line[col['dr']])
            alpha = float(spin_line[col['alpha']]) / 360.0 * 2.0 * pi
            beta = float(spin_line[col['beta']]) / 360.0 * 2.0 * pi
            gamma = float(spin_line[col['gamma']]) / 360.0 * 2.0 * pi
        except ValueError:
            # Errors or simulation values set to None.
            if data_set != 'value' and spin_line[col['tm']] == 'None':
                return

            # Genuine error.
            raise RelaxError("The diffusion tensor parameters are not numbers.")

        # Values.
        if data_set == 'value':
            diff_params = [tm, Da, Dr, alpha, beta, gamma]

        # Errors.
        elif data_set == 'error':
            cdp.diff_tensor.set(param='tm', value=tm, category='err')
            cdp.diff_tensor.set(param='Da', value=Da, category='err')
            cdp.diff_tensor.set(param='Dr', value=Dr, category='err')
            cdp.diff_tensor.set(param='alpha', value=alpha, category='err')
            cdp.diff_tensor.set(param='beta', value=beta, category='err')
            cdp.diff_tensor.set(param='gamma', value=gamma, category='err')

        # Simulation values.
        else:
            # Set the values.
            cdp.diff_tensor.set(param='tm', value=tm, category='sim', sim_index=sim_num)
            cdp.diff_tensor.set(param='Da', value=Da, category='sim', sim_index=sim_num)
            cdp.diff_tensor.set(param='Dr', value=Dr, category='sim', sim_index=sim_num)
            cdp.diff_tensor.set(param='alpha', value=alpha, category='sim', sim_index=sim_num)
            cdp.diff_tensor.set(param='beta', value=beta, category='sim', sim_index=sim_num)
            cdp.diff_tensor.set(param='gamma', value=gamma, category='sim', sim_index=sim_num)

    # Set the diffusion tensor.
    if data_set == 'value' and diff_type:
        # Sort out the spheroid type.
        spheroid_type = None
        if diff_type == 'oblate' or diff_type == 'prolate':
            spheroid_type = diff_type

        # Set the diffusion tensor.
        pipe_control.diffusion_tensor.init(params=diff_params, angle_units='rad', spheroid_type=spheroid_type)


def read_columnar_results(file_data, verbosity=1):
    """Read the columnar formatted model-free results file.

    @param file_data:   The processed results file data.
    @type file_data:    list of lists of str
    @keyword verbosity: A variable specifying the amount of information to print.  The higher
                        the value, the greater the verbosity.
    @type verbosity:    int
    """

    # Determine the results file version.
    version = determine_version(file_data, verbosity)

    # Execute the version specific methods.
    if version == '1.2':
        read_1_2_results(file_data, verbosity)


def set_xh_vect(spin_line, col, spin, spin_id1=None, spin_id2=None, verbosity=1):
    """Set the unit vectors.

    @param spin_line:   The line of data for a single spin.
    @type spin_line:    list of str
    @param col:         The column indices.
    @type col:          dict of int
    @param spin:        The spin container.
    @type spin:         SpinContainer instance
    @keyword spin_id1:  The ID string of the first spin.
    @type spin_id1:     str
    @keyword spin_id2:  The ID string of the second spin.
    @type spin_id2:     str
    @keyword verbosity: A variable specifying the amount of information to print.  The higher the value, the greater the verbosity.
    @type verbosity:    int
    """

    # Get the interatomic data container.
    interatom = return_interatom(spin_id1=spin_id1, spin_id2=spin_id2)
    if interatom == None:
        raise RelaxError("No interatomic interaction between spins '%s' and '%s' could be found." (spin_id1, spin_id2))

    # The vector.
    vector = eval(spin_line[col['xh_vect']])
    if vector:
        # numpy array format.
        try:
            vector = array(vector, float64)
        except:
            raise RelaxError("The XH unit vector " + spin_line[col['xh_vect']] + " is invalid.")

        # Set the vector.
        interatom.vector = vector
