###############################################################################
#                                                                             #
# Copyright (C) 2003-2012 Edward d'Auvergne                                   #
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
"""Module for the manipulation of pseudocontact shift data."""

# Python module imports.
from copy import deepcopy
from math import pi, sqrt
from numpy import array, float64, ones, zeros
from numpy.linalg import norm
import sys
from warnings import warn

# relax module imports.
from generic_fns import grace, pipes
from generic_fns.align_tensor import get_tensor_index
from generic_fns.mol_res_spin import exists_mol_res_spin_data, generate_spin_id, return_spin, spin_loop
from maths_fns.pcs import ave_pcs_tensor
from physical_constants import g1H, pcs_constant
from relax_errors import RelaxError, RelaxNoPdbError, RelaxNoSequenceError
from relax_io import open_write_file, read_spin_data, write_spin_data
from relax_warnings import RelaxWarning, RelaxNoSpinWarning


def back_calc(align_id=None):
    """Back calculate the PCS from the alignment tensor.

    @keyword align_id:      The alignment tensor ID string.
    @type align_id:         str
    """

    # Arg check.
    if align_id and align_id not in cdp.align_ids:
        raise RelaxError("The alignment ID '%s' is not in the alignment ID list %s." % (align_id, cdp.align_ids))

    # Convert the align IDs to an array, or take all IDs.
    if align_id:
        align_ids = [align_id]
    else:
        align_ids = cdp.align_ids

    # Add the ID to the PCS IDs, if needed.
    for align_id in align_ids:
        # Init.
        if not hasattr(cdp, 'pcs_ids'):
            cdp.pcs_ids = []

        # Add the ID.
        if align_id not in cdp.pcs_ids:
            cdp.pcs_ids.append(align_id)

    # The weights.
    weights = ones(cdp.N, float64) / cdp.N

    # Unit vector data structure init.
    unit_vect = zeros((cdp.N, 3), float64)

    # Loop over the spins.
    for spin in spin_loop():
        # Skip spins with no position.
        if not hasattr(spin, 'pos'):
            continue

        # Atom positions.
        pos = spin.pos
        if type(pos[0]) in [float, float64]:
            pos = [pos] * cdp.N

        # Loop over the alignments.
        for id in align_ids:
            # Vectors.
            vect = zeros((cdp.N, 3), float64)
            r = zeros(cdp.N, float64)
            dj = zeros(cdp.N, float64)
            for c in range(cdp.N):
                # The vector.
                vect[c] = pos[c] - cdp.paramagnetic_centre

                # The length.
                r[c] = norm(vect[c])

                # Normalise (only if the vector has length).
                if r[c]:
                    vect[c] = vect[c] / r[c]

                # Calculate the PCS constant.
                dj[c] = pcs_constant(cdp.temperature[id], cdp.frq[id] * 2.0 * pi / g1H, r[c]/1e10)

            # Initialise if necessary.
            if not hasattr(spin, 'pcs_bc'):
                spin.pcs_bc = {}

            # Calculate the PCSs (in ppm).
            spin.pcs_bc[id] = ave_pcs_tensor(dj, vect, cdp.N, cdp.align_tensors[get_tensor_index(id)].A, weights=weights) * 1e6


def centre(pos=None, atom_id=None, pipe=None, verbosity=1, ave_pos=False, force=False):
    """Specify the atom in the loaded structure corresponding to the paramagnetic centre.

    @keyword pos:       The atomic position.  If set, the atom_id string will be ignored.
    @type pos:          list of float
    @keyword atom_id:   The atom identification string.
    @type atom_id:      str
    @keyword pipe:      An alternative data pipe to extract the paramagnetic centre from.
    @type pipe:         None or str
    @keyword verbosity: The amount of information to print out.  The bigger the number, the more information.
    @type verbosity:    int
    @keyword ave_pos:   A flag which if True causes the atomic positions from multiple models to be averaged.
    @type ave_pos:      bool
    @keyword force:     A flag which if True will cause the current PCS centre to be overwritten.
    """

    # The data pipe.
    if pipe == None:
        pipe = pipes.cdp_name()

    # Test the data pipe.
    pipes.test(pipe)

    # Get the data pipes.
    source_dp = pipes.get_pipe(pipe)

    # Test if the structure has been loaded.
    if not hasattr(source_dp, 'structure'):
        raise RelaxNoPdbError

    # Test the centre has already been set.
    if not force and hasattr(cdp, 'paramagnetic_centre'):
        raise RelaxError("The paramagnetic centre has already been set to the coordinates " + repr(cdp.paramagnetic_centre) + ".")

    # Position is supplied.
    if pos != None:
        centre = array(pos)
        num_pos = 1
        full_pos_list = []

    # Position from a loaded structure.
    else:
        # Get the positions.
        centre = zeros(3, float64)
        full_pos_list = []
        num_pos = 0
        for spin, spin_id in spin_loop(atom_id, pipe=pipe, return_id=True):
            # No atomic positions.
            if not hasattr(spin, 'pos'):
                continue
    
            # Spin position list.
            if isinstance(spin.pos[0], float) or isinstance(spin.pos[0], float64):
                pos_list = [spin.pos]
            else:
                pos_list = spin.pos
    
            # Loop over the model positions.
            for pos in pos_list:
                full_pos_list.append(pos)
                centre = centre + array(pos)
                num_pos = num_pos + 1
    
        # No positional information!
        if not num_pos:
            raise RelaxError("No positional information could be found for the spin '%s'." % atom_id)

    # Averaging.
    centre = centre / float(num_pos)

    # Print out.
    if verbosity:
        print("Paramagnetic centres located at:")
        for pos in full_pos_list:
            print(("    [%8.3f, %8.3f, %8.3f]" % (pos[0], pos[1], pos[2])))
        print("\nAverage paramagnetic centre located at:")
        print(("    [%8.3f, %8.3f, %8.3f]" % (centre[0], centre[1], centre[2])))

    # Set the centre (place it into the current data pipe).
    if ave_pos:
        if verbosity:
            print("\nUsing the average paramagnetic position.")
        cdp.paramagnetic_centre = centre
    else:
        if verbosity:
            print("\nUsing all paramagnetic positions.")
        cdp.paramagnetic_centre = full_pos_list


def corr_plot(format=None, file=None, dir=None, force=False):
    """Generate a correlation plot of the measured vs. back-calculated PCSs.

    @keyword format:    The format for the plot file.  The following values are accepted: 'grace', a Grace plot; None, a plain text file.
    @type format:       str or None
    @keyword file:      The file name or object to write to.
    @type file:         str or file object
    @keyword dir:       The name of the directory to place the file into (defaults to the current directory).
    @type dir:          str
    @keyword force:     A flag which if True will cause any pre-existing file to be overwritten.
    @type force:        bool
    """

    # Test if the current pipe exists.
    pipes.test()

    # Test if the sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Does PCS data exist?
    if not hasattr(cdp, 'pcs_ids') or not cdp.pcs_ids:
        warn(RelaxWarning("No PCS data exists, skipping file creation."))
        return

    # Open the file for writing.
    file = open_write_file(file, dir, force)

    # Init.
    data = []

    # The diagonal.
    data.append([[-100, -100, 0], [100, 100, 0]])

    # The spin types.
    types = []
    for spin in spin_loop():
        if spin.element not in types:
            types.append(spin.element)

    # Loop over the PCS data.
    for align_id in cdp.pcs_ids:
        # Loop over the spin types.
        for i in range(len(types)):
            # Append a new list for this alignment.
            data.append([])

            # Errors present?
            err_flag = False
            for spin in spin_loop():
                # Skip deselected spins.
                if not spin.select:
                    continue

                # Error present.
                if hasattr(spin, 'pcs_err') and align_id in spin.pcs_err.keys():
                    err_flag = True
                    break

            # Loop over the spins.
            for spin, spin_id in spin_loop(return_id=True):
                # Skip deselected spins.
                if not spin.select:
                    continue

                # Incorrect spin type.
                if spin.element != types[i]:
                    continue

                # Skip if data is missing.
                if not hasattr(spin, 'pcs') or not hasattr(spin, 'pcs_bc') or not align_id in spin.pcs.keys() or not align_id in spin.pcs_bc.keys():
                    continue

                # Append the data.
                data[-1].append([spin.pcs_bc[align_id], spin.pcs[align_id]])

                # Errors.
                if err_flag:
                    if hasattr(spin, 'pcs_err') and align_id in spin.pcs_err.keys():
                        data[-1][-1].append(spin.pcs_err[align_id])
                    else:
                        data[-1][-1].append(None)

                # Label.
                data[-1][-1].append(spin_id)

    # The data size.
    size = len(data)

    # Only one data set.
    data = [data]

    # Graph type.
    if err_flag:
        graph_type = 'xydy'
    else:
        graph_type = 'xy'

    # Grace file.
    if format == 'grace':
        # The set names.
        set_names = [None]
        for i in range(len(cdp.pcs_ids)):
            for j in range(len(types)):
                set_names.append("%s (%s)" % (cdp.pcs_ids[i], types[j]))

        # The header.
        grace.write_xy_header(file=file, title="PCS correlation plot", sets=size, set_names=set_names, linestyle=[2]+[0]*size, data_type=['pcs_bc', 'pcs'], axis_min=[-0.5, -0.5], axis_max=[0.5, 0.5], legend_pos=[1, 0.5])

        # The main data.
        grace.write_xy_data(data=data, file=file, graph_type=graph_type)


def delete(align_id=None):
    """Delete the PCS data corresponding to the alignment ID.

    @keyword align_id:  The alignment tensor ID string.  If not specified, all data will be deleted.
    @type align_id:     str or None
    """

    # Test if the current data pipe exists.
    pipes.test()

    # Test if sequence data exists.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Check that the ID exists.
    if align_id and not align_id in cdp.pcs_ids:
        raise RelaxError("The PCS alignment id '%s' does not exist" % align_id)

    # The IDs.
    if not align_id:
        ids = deepcopy(cdp.pcs_ids)
    else:
        ids = [align_id]

    # Loop over the alignments, removing all the corresponding data.
    for id in ids:
        # The PCS ID.
        cdp.pcs_ids.pop(cdp.pcs_ids.index(id))

        # The data type.
        if hasattr(cdp, 'pcs_data_types') and cdp.pcs_data_types.has_key(id):
            cdp.pcs_data_types.pop(id)

        # The spin data.
        for spin in spin_loop():
            # The data.
            if hasattr(spin, 'pcs') and spin.pcs.has_key(id):
                spin.pcs.pop(id)

            # The error.
            if hasattr(spin, 'pcs_err') and spin.pcs_err.has_key(id):
                spin.pcs_err.pop(id)

        # Clean the global data.
        if not hasattr(cdp, 'rdc_ids') or id not in cdp.rdc_ids:
            cdp.align_ids.pop(id)


def display(align_id=None, bc=False):
    """Display the PCS data corresponding to the alignment ID.

    @keyword align_id:  The alignment tensor ID string.
    @type align_id:     str
    @keyword bc:        The back-calculation flag which if True will cause the back-calculated rather than measured data to be displayed.
    @type bc:           bool
    """

    # Call the write method with sys.stdout as the file.
    write(align_id=align_id, file=sys.stdout, bc=bc)


def q_factors(spin_id=None):
    """Calculate the Q-factors for the PCS data.

    @keyword spin_id:   The spin ID string used to restrict the Q-factor calculation to a subset of all spins.
    @type spin_id:      None or str
    """

    # No PCSs, so no Q factors can be calculated.
    if not hasattr(cdp, 'pcs_ids') or not len(cdp.pcs_ids):
        warn(RelaxWarning("No PCS data exists, Q factors cannot be calculated."))
        return

    # Q-factor dictionary.
    cdp.q_factors_pcs = {}

    # Loop over the alignments.
    for align_id in cdp.pcs_ids:
        # Init.
        pcs2_sum = 0.0
        sse = 0.0

        # Spin loop.
        spin_count = 0
        pcs_data = False
        pcs_bc_data = False
        for spin in spin_loop(spin_id):
            # Skip deselected spins.
            if not spin.select:
                continue

            # Increment the spin counter.
            spin_count += 1

            # Data checks.
            if hasattr(spin, 'pcs') and spin.pcs.has_key(align_id):
                pcs_data = True
            if hasattr(spin, 'pcs_bc') and spin.pcs_bc.has_key(align_id):
                pcs_bc_data = True

            # Skip spins without PCS data.
            if not hasattr(spin, 'pcs') or not hasattr(spin, 'pcs_bc') or not spin.pcs.has_key(align_id) or spin.pcs[align_id] == None or not spin.pcs_bc.has_key(align_id) or spin.pcs_bc[align_id] == None:
                continue

            # Sum of squares.
            sse = sse + (spin.pcs[align_id] - spin.pcs_bc[align_id])**2

            # Sum the PCSs squared (for normalisation).
            pcs2_sum = pcs2_sum + spin.pcs[align_id]**2

        # The Q-factor for the alignment.
        if pcs2_sum:
            Q = sqrt(sse / pcs2_sum)
            cdp.q_factors_pcs[align_id] = Q

        # Warnings (and then exit).
        if not spin_count:
            warn(RelaxWarning("No spins have been used in the calculation."))
            return
        if not pcs_data:
            warn(RelaxWarning("No PCS data can be found."))
            return
        if not pcs_bc_data:
            warn(RelaxWarning("No back-calculated PCS data can be found."))
            return

    # The total Q-factor.
    cdp.q_pcs = 0.0
    for id in cdp.q_factors_pcs:
        cdp.q_pcs = cdp.q_pcs + cdp.q_factors_pcs[id]**2
    cdp.q_pcs = cdp.q_pcs / len(cdp.q_factors_pcs)
    cdp.q_pcs = sqrt(cdp.q_pcs)


def read(align_id=None, file=None, dir=None, file_data=None, spin_id_col=None, mol_name_col=None, res_num_col=None, res_name_col=None, spin_num_col=None, spin_name_col=None, data_col=None, error_col=None, sep=None, spin_id=None):
    """Read the PCS data from file.

    @param align_id:        The alignment tensor ID string.
    @type align_id:         str
    @param file:            The name of the file to open.
    @type file:             str
    @param dir:             The directory containing the file (defaults to the current directory if None).
    @type dir:              str or None
    @param file_data:       An alternative opening a file, if the data already exists in the correct format.  The format is a list of lists where the first index corresponds to the row and the second the column.
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
    @keyword data_col:      The column containing the PCS data in Hz.
    @type data_col:         int or None
    @keyword error_col:     The column containing the PCS errors.
    @type error_col:        int or None
    @keyword sep:           The column separator which, if None, defaults to whitespace.
    @type sep:              str or None
    @keyword spin_id:       The spin ID string used to restrict data loading to a subset of all spins.
    @type spin_id:          None or str
    """

    # Test if the current data pipe exists.
    pipes.test()

    # Test if sequence data exists.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Either the data or error column must be supplied.
    if data_col == None and error_col == None:
        raise RelaxError("One of either the data or error column must be supplied.")


    # Spin specific data.
    #####################

    # Loop over the PCS data.
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

        # Test the error value (cannot be 0.0).
        if error == 0.0:
            raise RelaxError("An invalid error value of zero has been encountered.")

        # Get the corresponding spin container.
        id = generate_spin_id(mol_name=mol_name, res_num=res_num, res_name=res_name, spin_num=spin_num, spin_name=spin_name)
        spin = return_spin(id)
        if spin == None:
            warn(RelaxNoSpinWarning(id))
            continue

        # Add the data.
        if data_col:
            # Initialise.
            if not hasattr(spin, 'pcs'):
                spin.pcs = {}

            # Append the value.
            spin.pcs[align_id] = value

        # Add the error.
        if error_col:
            # Initialise.
            if not hasattr(spin, 'pcs_err'):
                spin.pcs_err = {}

            # Append the error.
            spin.pcs_err[align_id] = error

        # Append the data for printout.
        mol_names.append(mol_name)
        res_nums.append(res_num)
        res_names.append(res_name)
        spin_nums.append(spin_num)
        spin_names.append(spin_name)
        values.append(value)
        errors.append(error)

    # Print out.
    write_spin_data(file=sys.stdout, mol_names=mol_names, res_nums=res_nums, res_names=res_names, spin_nums=spin_nums, spin_names=spin_names, data=values, data_name='PCSs', error=errors, error_name='PCS_error')


    # Global (non-spin specific) data.
    ##################################

    # No data, so return.
    if not len(values):
        return

    # Initialise.
    if not hasattr(cdp, 'align_ids'):
        cdp.align_ids = []
    if not hasattr(cdp, 'pcs_ids'):
        cdp.pcs_ids = []

    # Add the PCS id string.
    if align_id not in cdp.align_ids:
        cdp.align_ids.append(align_id)
    if align_id not in cdp.pcs_ids:
        cdp.pcs_ids.append(align_id)


def weight(align_id=None, spin_id=None, weight=1.0):
    """Set optimisation weights on the PCS data.

    @keyword align_id:  The alignment tensor ID string.
    @type align_id:     str
    @keyword spin_id:   The spin ID string.
    @type spin_id:      None or str
    @keyword weight:    The optimisation weight.  The higher the value, the more importance the PCS will have.
    @type weight:       float or int.
    """

    # Test if sequence data exists.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Test if data corresponding to 'align_id' exists.
    if not hasattr(cdp, 'pcs_ids') or align_id not in cdp.pcs_ids:
        raise RelaxNoPCSError(align_id)

    # Loop over the spins.
    for spin in spin_loop(spin_id):
        # No data structure.
        if not hasattr(spin, 'pcs_weight'):
            spin.pcs_weight = {}

        # Set the weight.
        spin.pcs_weight[align_id] = weight


def write(align_id=None, file=None, dir=None, bc=False, force=False):
    """Display the PCS data corresponding to the alignment ID.

    @keyword align_id:  The alignment tensor ID string.
    @type align_id:     str
    @keyword file:      The file name or object to write to.
    @type file:         str or file object
    @keyword dir:       The name of the directory to place the file into (defaults to the current directory).
    @type dir:          str
    @keyword bc:        The back-calculation flag which if True will cause the back-calculated rather than measured data to be written.
    @type bc:           bool
    @keyword force:     A flag which if True will cause any pre-existing file to be overwritten.
    @type force:        bool
    """

    # Test if the current pipe exists.
    pipes.test()

    # Test if the sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Test if data corresponding to 'align_id' exists.
    if not hasattr(cdp, 'pcs_ids') or align_id not in cdp.pcs_ids:
        raise RelaxNoPCSError(align_id)

    # Open the file for writing.
    file = open_write_file(file, dir, force)

    # Loop over the spins and collect the data.
    mol_names = []
    res_nums = []
    res_names = []
    spin_nums = []
    spin_names = []
    values = []
    errors = []
    for spin, mol_name, res_num, res_name in spin_loop(full_info=True):
        # Skip spins with no PCSs.
        if not bc and (not hasattr(spin, 'pcs') or not align_id in spin.pcs.keys()):
            continue
        elif bc and (not hasattr(spin, 'pcs_bc') or align_id not in spin.pcs_bc.keys()):
            continue

        # Append the spin data.
        mol_names.append(mol_name)
        res_nums.append(res_num)
        res_names.append(res_name)
        spin_nums.append(spin.num)
        spin_names.append(spin.name)

        # The value.
        if bc:
            values.append(spin.pcs_bc[align_id])
        else:
            values.append(spin.pcs[align_id])

        # The error.
        if hasattr(spin, 'pcs_err') and align_id in spin.pcs_err.keys():
            errors.append(spin.pcs_err[align_id])
        else:
            errors.append(None)

    # Write out.
    write_spin_data(file=file, mol_names=mol_names, res_nums=res_nums, res_names=res_names, spin_nums=spin_nums, spin_names=spin_names, data=values, data_name='PCSs', error=errors, error_name='PCS_error')
