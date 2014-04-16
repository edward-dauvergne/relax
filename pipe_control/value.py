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
"""Module for the manipulation of parameter and constant values."""

# Python module imports.
from numpy import ndarray
import sys

# relax module imports.
from lib.check_types import is_num
from lib.errors import RelaxError, RelaxNoSequenceError, RelaxParamSetError, RelaxValueError
from lib.io import get_file_path, open_write_file
from lib.sequence import read_spin_data, write_spin_data
from pipe_control import minimise, pipes
from pipe_control.mol_res_spin import exists_mol_res_spin_data, generate_spin_id_unique, spin_loop
from pipe_control.result_files import add_result_file
from specific_analyses.api import return_api
from status import Status; status = Status()


def copy(pipe_from=None, pipe_to=None, param=None):
    """Copy spin specific data values from pipe_from to pipe_to.

    @param pipe_from:   The data pipe to copy the value from.  This defaults to the current data
                        pipe.
    @type pipe_from:    str
    @param pipe_to:     The data pipe to copy the value to.  This defaults to the current data pipe.
    @type pipe_to:      str
    @param param:       The name of the parameter to copy the values of.
    @type param:        str
    """

    # The current data pipe.
    if pipe_from == None:
        pipe_from = pipes.cdp_name()
    if pipe_to == None:
        pipe_to = pipes.cdp_name()
    pipe_orig = pipes.cdp_name()

    # The second pipe does not exist.
    pipes.test(pipe_to)

    # Test if the sequence data for pipe_from is loaded.
    if not exists_mol_res_spin_data(pipe_from):
        raise RelaxNoSequenceError(pipe_from)

    # Test if the sequence data for pipe_to is loaded.
    if not exists_mol_res_spin_data(pipe_to):
        raise RelaxNoSequenceError(pipe_to)

    # The specific analysis API object.
    api = return_api(pipe_name=pipe_from)

    # Test if the data exists for pipe_to.
    for spin in spin_loop(pipe=pipe_to):
        # Get the value and error for pipe_to.
        value, error = api.return_value(spin, param)

        # Data exists.
        if value != None or error != None:
            raise RelaxValueError(param, pipe_to)

    # Switch to the data pipe to copy values to.
    pipes.switch(pipe_to)

    # Copy the values.
    for spin, spin_id in spin_loop(pipe=pipe_from, return_id=True):
        # Get the value and error from pipe_from.
        value, error = api.return_value(spin, param)

        # Set the values of pipe_to.
        if value != None:
            set(spin_id=spin_id, val=value, param=param, pipe=pipe_to)
        if error != None:
            set(spin_id=spin_id, val=error, param=param, pipe=pipe_to, error=True)

    # Reset all minimisation statistics.
    minimise.reset_min_stats(pipe_to)

    # Switch back to the original current data pipe.
    pipes.switch(pipe_orig)


def display(param=None, scaling=1.0):
    """Display spin specific data values.

    @keyword param:     The name of the parameter to display.
    @type param:        str
    @keyword scaling:   The value to scale the parameter by.
    @type scaling:      float
    """

    # Test if the current pipe exists.
    pipes.test()

    # Test if the sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Print the data.
    write_data(param=param, file=sys.stdout, scaling=scaling)


def get_parameters():
    """Return a list of the parameters associated with the current data pipe.

    @return:    The list of parameters.
    @rtype:     list of str
    """

    # No data pipes.
    if cdp == None:
        return []

    # The specific analysis API object.
    api = return_api()

    # Return an empty list if the required functions are absent.
    if not hasattr(api, 'data_names') or not hasattr(api, 'return_data_desc'):
        return []

    # Loop over the parameters.
    params = []
    for name in (api.data_names(set='params') + api.data_names(set='generic') + api.data_names(set='min')):
        # Get the description.
        desc = api.return_data_desc(name)

        # No description.
        if not desc:
            text = name

        # The text.
        else:
            text = "'%s':  %s" % (name, desc)

        # Append the data as a list.
        params.append((text, name))

    # Return the data.
    return params


def partition_params(val, param):
    """Function for sorting and partitioning the parameters and their values.

    The two major partitions are the tensor parameters and the spin specific parameters.

    @param val:     The parameter values.
    @type val:      None, number, or list of numbers
    @param param:   The parameter names.
    @type param:    None, str, or list of str
    @return:        A tuple, of length 4, of lists.  The first and second elements are the lists of
                    spin specific parameters and values respectively.  The third and forth elements
                    are the lists of all other parameters and their values.
    @rtype:         tuple of 4 lists
    """

    # The specific analysis API object.
    api = return_api()

    # Initialise.
    spin_params = []
    spin_values = []
    other_params = []
    other_values = []

    # Single parameter.
    if isinstance(param, str):
        # Spin specific parameter.
        if api.is_spin_param(param):
            params = spin_params
            values = spin_values

        # Other parameters.
        else:
            params = other_params
            values = other_values

        # List of values.
        if isinstance(val, list) or isinstance(val, ndarray):
            # Parameter name.
            for i in range(len(val)):
                params.append(param)

            # Parameter value.
            values = val

        # Single value.
        else:
            # Parameter name.
            params.append(param)

            # Parameter value.
            values.append(val)

    # Multiple parameters.
    elif isinstance(param, list):
        # Loop over all parameters.
        for i in range(len(param)):
            # Spin specific parameter.
            if api.is_spin_param(param[i]):
                params = spin_params
                values = spin_values

            # Other parameters.
            else:
                params = other_params
                values = other_values

            # Parameter name.
            params.append(param[i])

            # Parameter value.
            if isinstance(val, list) or isinstance(val, ndarray):
                values.append(val[i])
            else:
                values.append(val)


    # Return the partitioned parameters and values.
    return spin_params, spin_values, other_params, other_values


def read(param=None, scaling=1.0, file=None, dir=None, file_data=None, spin_id_col=None, mol_name_col=None, res_num_col=None, res_name_col=None, spin_num_col=None, spin_name_col=None, data_col=None, error_col=None, sep=None, spin_id=None):
    """Read spin specific data values from a file.

    @keyword param:         The name of the parameter to read.
    @type param:            str
    @keyword scaling:       A scaling factor by which all read values are multiplied by.
    @type scaling:          float
    @keyword file:          The name of the file to open.
    @type file:             str
    @keyword dir:           The directory containing the file (defaults to the current directory if None).
    @type dir:              str or None
    @keyword file_data:     An alternative to opening a file, if the data already exists in the correct format.  The format is a list of lists where the first index corresponds to the row and the second the column.
    @type file_data:        list of lists
    @keyword spin_id_col:   The column containing the spin ID strings.  If supplied, the mol_name_col, res_name_col, res_num_col, spin_name_col, and spin_num_col arguments must be none.
    @type spin_id_col:      int or None
    @keyword mol_name_col:  The column containing the molecule name information.  If supplied, spin_id_col must be None.
    @type mol_name_col:     int or None
    @keyword res_name_col:  The column containing the residue name information.  If supplied, spin_id_col must be None.
    @type res_name_col:     int or None
    @keyword res_num_col:   The column containing the residue number information.  If supplied, spin_id_col must be None.
    @type res_num_col:      int or None
    @keyword spin_name_col: The column containing the spin name information.  If supplied, spin_id_col must be None.
    @type spin_name_col:    int or None
    @keyword spin_num_col:  The column containing the spin number information.  If supplied, spin_id_col must be None.
    @type spin_num_col:     int or None
    @keyword data_col:      The column containing the RDC data in Hz.
    @type data_col:         int or None
    @keyword error_col:     The column containing the RDC errors.
    @type error_col:        int or None
    @keyword sep:           The column separator which, if None, defaults to whitespace.
    @type sep:              str or None
    @keyword spin_id:       The spin ID string.
    @type spin_id:          None or str
    """

    # Test if the current pipe exists.
    pipes.test()

    # Test if sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

        # Minimisation statistic flag.
        min_stat = False

        # Alias specific analysis API object method.
        api = return_api()
        return_value = api.return_value

        # Specific set function.                                                           
        set_fn = set

    # Test data corresponding to param already exists.
    for spin in spin_loop():
        # Skip deselected spins.
        if not spin.select:
            continue

        # Get the value and error.
        value, error = return_value(spin, param)

        # Data exists.
        if value != None or error != None:
            raise RelaxValueError(param)

    # Loop over the data.
    mol_names = []
    res_nums = []
    res_names = []
    spin_nums = []
    spin_names = []
    values = []
    errors = []
    for data in read_spin_data(file=file, dir=dir, file_data=file_data, spin_id_col=spin_id_col, mol_name_col=mol_name_col, res_num_col=res_num_col, res_name_col=res_name_col, spin_num_col=spin_num_col, spin_name_col=spin_name_col, data_col=data_col, error_col=error_col, sep=sep, spin_id=spin_id):
        # Unpack.
        if data_col and error_col:
            mol_name, res_num, res_name, spin_num, spin_name, value, error = data
        elif data_col:
            mol_name, res_num, res_name, spin_num, spin_name, value = data
            error = None
        else:
            mol_name, res_num, res_name, spin_num, spin_name, error = data
            value = None

        # Set the value.
        id = generate_spin_id_unique(mol_name=mol_name, res_num=res_num, res_name=res_name, spin_num=spin_num, spin_name=spin_name)
        set_fn(val=value, error=error, param=param, spin_id=id)

        # Append the data for printout.
        mol_names.append(mol_name)
        res_nums.append(res_num)
        res_names.append(res_name)
        spin_nums.append(spin_num)
        spin_names.append(spin_name)
        values.append(value)
        errors.append(error)

    # Print out.
    write_spin_data(file=sys.stdout, mol_names=mol_names, res_nums=res_nums, res_names=res_names, spin_nums=spin_nums, spin_names=spin_names, data=values, data_name=param, error=errors, error_name='%s_error'%param)

    # Reset the minimisation statistics.
    if api.set(param) == 'min':
        minimise.reset_min_stats()


def set(val=None, param=None, index=None, pipe=None, spin_id=None, error=False, force=True, reset=True):
    """Set global or spin specific data values.

    @keyword val:       The parameter values.
    @type val:          None or list
    @keyword param:     The parameter names.
    @type param:        None, str, or list of str
    @keyword index:     The index for parameters which are of the list-type.  This is ignored for all other types.
    @type index:        None or int
    @keyword pipe:      The data pipe the values should be placed in.
    @type pipe:         None or str
    @keyword spin_id:   The spin identification string.
    @type spin_id:      str
    @keyword error:     A flag which if True will allow the parameter errors to be set instead of the values.
    @type error:        bool
    @keyword force:     A flag forcing the overwriting of current values.
    @type force:        bool
    @keyword reset:     A flag which if True will cause all minimisation statistics to be reset.
    @type reset:        bool
    """

    # Switch to the data pipe, storing the original.
    if pipe:
        orig_pipe = pipes.cdp_name()
        pipes.switch(pipe)

    # Test if the current data pipe exists.
    pipes.test()

    # The specific analysis API object.
    api = return_api()

    # Convert numpy arrays to lists, if necessary.
    if isinstance(val, ndarray):
        val = val.tolist()

    # Invalid combinations.
    if (isinstance(val, float) or isinstance(val, int)) and param == None:
        raise RelaxError("The combination of a single value '%s' without specifying the parameter name is invalid." % val)
    if isinstance(val, list) and isinstance(param, str):
        raise RelaxError("Invalid combination:  When multiple values '%s' are specified, either no parameters or a list of parameters must by supplied rather than the single parameter '%s'." % (val, param))

    # Value array and parameter array of equal length.
    if isinstance(val, list) and isinstance(param, list) and len(val) != len(param):
        raise RelaxError("Both the value array and parameter array must be of equal length.")

    # Get the parameter list if needed.
    if param == None:
        param = api.get_param_names()

    # Convert the param to a list if needed.
    if not isinstance(param, list):
        param = [param]

    # Convert the value to a list if needed.
    if val != None and not isinstance(val, list):
        val = [val] * len(param)

    # Default values.
    if val == None:
        # Loop over the parameters, getting the default values.
        val = []
        for i in range(len(param)):
            val.append(api.default_value(param[i]))

            # Check that there is a default.
            if val[-1] == None:
                raise RelaxParamSetError(param[i])

    # Set the parameter values.
    api.set_param_values(param=param, value=val, index=index, spin_id=spin_id, error=error, force=force)

    # Reset all minimisation statistics.
    if reset:
        minimise.reset_min_stats()

    # Switch back.
    if pipe:
        pipes.switch(orig_pipe)


def write(param=None, file=None, dir=None, scaling=1.0, return_value=None, return_data_desc=None, comment=None, bc=False, force=False):
    """Write data to a file.

    @keyword param:             The name of the parameter to write to file.
    @type param:                str
    @keyword file:              The file to write the data to.
    @type file:                 str
    @keyword dir:               The name of the directory to place the file into (defaults to the current directory).
    @type dir:                  str
    @keyword scaling:           The value to scale the parameter by.
    @type scaling:              float
    @keyword return_value:      An optional function which if supplied will override the default value returning function.
    @type return_value:         None or func
    @keyword return_data_desc:  An optional function which if supplied will override the default parameter description returning function.
    @type return_data_desc:     None or func
    @keyword comment:           Text which will be added to the start of the file as comments.  All lines will be prefixed by '# '.
    @type comment:              str
    @keyword bc:                A flag which if True will cause the back calculated values to be written.
    @type bc:                   bool
    @keyword force:             A flag which if True will cause any pre-existing file to be overwritten.
    @type force:                bool
    """

    # Test if the current pipe exists.
    pipes.test()

    # Test if the sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Open the file for writing.
    file_path = get_file_path(file, dir)
    file = open_write_file(file, dir, force)

    # Write the data.
    write_data(param=param, file=file, scaling=scaling, return_value=return_value, return_data_desc=return_data_desc, comment=comment, bc=bc)

    # Close the file.
    file.close()

    # Add the file to the results file list.
    add_result_file(type='text', label='Text', file=file_path)


def write_data(param=None, file=None, scaling=1.0, bc=False, return_value=None, return_data_desc=None, comment=None):
    """The function which actually writes the data.

    @keyword param:             The parameter to write.
    @type param:                str
    @keyword file:              The file to write the data to.
    @type file:                 str
    @keyword scaling:           The value to scale the parameter by.
    @type scaling:              float
    @keyword bc:                A flag which if True will cause the back calculated values to be written.
    @type bc:                   bool
    @keyword return_value:      An optional function which if supplied will override the default value returning function.
    @type return_value:         None or func
    @keyword return_data_desc:  An optional function which if supplied will override the default parameter description returning function.
    @type return_data_desc:     None or func
    @keyword comment:           Text which will be added to the start of the file as comments.  All lines will be prefixed by '# '.
    @type comment:              str
    """

    # The specific analysis API object.
    api = return_api()

    # Get the value and error returning function parameter description function if required.
    if not return_value:
        return_value = api.return_value
    if not return_data_desc:
        return_data_desc = api.return_data_desc

    # Format string.
    format = "%-30s%-30s"

    # Init the data.
    mol_names = []
    res_nums = []
    res_names = []
    spin_nums = []
    spin_names = []
    values = []
    errors = []

    # Get the parameter description and add it to the file.
    desc = return_data_desc(param)
    if desc:
        file.write("# Parameter description:  %s.\n" % desc)
        file.write("#\n")

    # The comments.
    if comment:
        # Split up the lines.
        lines = comment.splitlines()

        # Write out.
        for line in lines:
            file.write("# %s\n" % line)
        file.write("#\n")

    # Determine the data type, check the data, and set up the dictionary type data keys.
    data_names = 'value'
    error_names = 'error'
    data_type = None
    for spin, mol_name, res_num, res_name in spin_loop(full_info=True):
        # Get the value and error.
        value, error = return_value(spin, param, bc=bc)

        # Dictionary type data.
        if isinstance(value, dict):
            # Sanity check.
            if not data_type in [None, 'dict']:
                raise RelaxError("Mixed data types.")
            data_type = 'dict'

            # Initialise the structures.
            if not isinstance(data_names, list):
                data_names = []
                error_names = []

            # Sort the keys.
            keys = sorted(value.keys())

            # Loop over the keys.
            for key in keys:
                # Add the data and error names if new.
                if key not in data_names:
                    data_names.append(key)
                    error_names.append('sd(%s)' % key)

        # List type data.
        elif isinstance(value, list):
            # Sanity check.
            if not data_type in [None, 'list']:
                raise RelaxError("Mixed data types.")
            data_type = 'list'

            # Initialise the structures.
            if not isinstance(data_names, list):
                data_names = []
                error_names = []

            # Check the length.
            elif len(data_names) != len(value):
                raise RelaxError("The list type data has an inconsistent number of elements between different spin systems.")

            # Loop over the data.
            for i in range(len(value)):
                # The data and error names.
                data_names.append('value_%s' % i)
                error_names.append('error_%s' % i)

        # None.
        elif value == None:
            pass

        # Simple values.
        else:
            # Sanity check.
            if not data_type in [None, 'value']:
                raise RelaxError("Mixed data types.")
            data_type = 'value'

    # Pack the data.
    for spin, mol_name, res_num, res_name in spin_loop(full_info=True):
        # Get the value and error.
        value, error = return_value(spin, param, bc=bc)

        # Append the spin data (scaled).
        mol_names.append(mol_name)
        res_nums.append(res_num)
        res_names.append(res_name)
        spin_nums.append(spin.num)
        spin_names.append(spin.name)

        # Dictionary type data.
        if data_type == 'dict':
            # Initialise the lists.
            values.append([])
            errors.append([])

            # Loop over the keys.
            for key in data_names:
                # Append the scaled values and errors.
                if value == None or key not in value:
                    values[-1].append(None)
                else:
                    values[-1].append(scale(value[key], scaling))
                if error == None or key not in error:
                    errors[-1].append(None)
                else:
                    errors[-1].append(scale(error[key], scaling))

        # List type data.
        elif data_type == 'list':
            # Initialise the lists.
            values.append([])
            errors.append([])

            # Loop over the data.
            for i in range(len(data_names)):
                # Append the scaled values and errors.
                if value == None:
                    values[-1].append(None)
                else:
                    values[-1].append(scale(value[i], scaling))
                if error == None:
                    errors[-1].append(None)
                else:
                    errors[-1].append(scale(error[i], scaling))

        # Simple values.
        else:
            # Append the scaled values and errors.
            values.append(scale(value, scaling))
            errors.append(scale(error, scaling))

    # Write the data.
    write_spin_data(file, mol_names=mol_names, res_nums=res_nums, res_names=res_names, spin_nums=spin_nums, spin_names=spin_names, data=values, data_name=data_names, error=errors, error_name=error_names)


def scale(value, scaling):
    """Scale the given value by the scaling factor, handling all input value types.

    @param value:   The value to scale.
    @type value:    anything
    @param scaling: The scaling factor.
    @type scaling:  float
    """

    # No a number, so return the value unmodified.
    if not is_num(value):
        return value

    # Scale.
    return value * scaling
