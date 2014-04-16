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
"""Module for the manipulation of relaxation data."""

# Python module imports.
from numpy import int32, ones, zeros
import string
import sys
from warnings import warn

# relax module imports.
from data_store import Relax_data_store; ds = Relax_data_store()
from data_store.exp_info import ExpInfo
from lib.errors import RelaxError, RelaxMultiSpinIDError, RelaxNoRiError, RelaxNoSequenceError, RelaxNoSpinError, RelaxRiError
from lib.io import write_data
from lib.physical_constants import element_from_isotope, number_from_isotope
from lib.sequence import read_spin_data
from lib.warnings import RelaxWarning
from pipe_control import bmrb, pipes, value
from pipe_control.interatomic import define, return_interatom, return_interatom_list
from pipe_control.mol_res_spin import Selection, exists_mol_res_spin_data, find_index, generate_spin_id_unique, get_molecule_names, return_spin, return_spin_from_selection, spin_index_loop, spin_loop
from pipe_control.spectrometer import copy_frequencies, delete_frequencies, frequency_checks, loop_frequencies, set_frequency
from specific_analyses.api import return_api


# The relaxation data types supported.
VALID_TYPES = ['R1', 'R2', 'NOE', 'R2eff']



def back_calc(ri_id=None, ri_type=None, frq=None):
    """Back calculate the relaxation data.

    If no relaxation data currently exists, then the ri_id, ri_type, and frq args are required.


    @keyword ri_id:     The relaxation data ID string.  If not given, all relaxation data will be back calculated.
    @type ri_id:        None or str
    @keyword ri_type:   The relaxation data type.  This should be one of 'R1', 'R2', or 'NOE'.
    @type ri_type:      None or str
    @keyword frq:       The spectrometer proton frequency in Hz.
    @type frq:          None or float
    """

    # Test if the current pipe exists.
    pipes.test()

    # Test if sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Check that ri_type and frq are supplied if no relaxation data exists.
    if ri_id and (not hasattr(cdp, 'ri_ids') or ri_id not in cdp.ri_ids) and (ri_type == None or frq == None):
        raise RelaxError("The 'ri_type' and 'frq' arguments must be supplied as no relaxation data corresponding to '%s' exists." % ri_id)

    # Check if the type is valid.
    if ri_type and ri_type not in VALID_TYPES:
        raise RelaxError("The relaxation data type '%s' must be one of %s." % (ri_type, VALID_TYPES))

    # Frequency checks.
    frequency_checks(frq)

    # Initialise the global data for the current pipe if necessary.
    if not hasattr(cdp, 'ri_type'):
        cdp.ri_type = {}
    if not hasattr(cdp, 'ri_ids'):
        cdp.ri_ids = []

    # Update the global data if needed.
    if ri_id and ri_id not in cdp.ri_ids:
        cdp.ri_ids.append(ri_id)
        cdp.ri_type[ri_id] = ri_type
        set_frequency(id=ri_id, frq=frq)

    # The specific analysis API object.
    api = return_api()

    # The IDs to loop over.
    if ri_id == None:
        ri_ids = cdp.ri_ids
    else:
        ri_ids = [ri_id]

    # The data types.
    if ri_type == None:
        ri_types = cdp.ri_type
    else:
        ri_types = {ri_id: ri_type}

    # The frequencies.
    if frq == None:
        frqs = cdp.spectrometer_frq
    else:
        frqs = {ri_id: frq}

    # Loop over the spins.
    for spin, spin_id in spin_loop(return_id=True):
        # Skip deselected spins.
        if not spin.select:
            continue

        # The global index.
        spin_index = find_index(spin_id)

        # Initialise the spin data if necessary.
        if not hasattr(spin, 'ri_data_bc'):
            spin.ri_data_bc = {}

        # Back-calculate the relaxation value.
        for ri_id in ri_ids:
            spin.ri_data_bc[ri_id] = api.back_calc_ri(spin_index=spin_index, ri_id=ri_id, ri_type=ri_types[ri_id], frq=frqs[ri_id])


def bmrb_read(star, sample_conditions=None):
    """Read the relaxation data from the NMR-STAR dictionary object.

    @param star:                The NMR-STAR dictionary object.
    @type star:                 NMR_STAR instance
    @keyword sample_conditions: The sample condition label to read.  Only one sample condition can be read per data pipe.
    @type sample_conditions:    None or str
    """

    # Get the relaxation data.
    for data in star.relaxation.loop():
        # Store the keys.
        keys = list(data.keys())

        # Sample conditions do not match (remove the $ sign).
        if 'sample_cond_list_label' in keys and sample_conditions and data['sample_cond_list_label'].replace('$', '') != sample_conditions:
            continue

        # Create the labels.
        ri_type = data['data_type']
        frq = float(data['frq']) * 1e6

        # Round the label to the nearest factor of 10.
        frq_label = create_frq_label(float(data['frq']) * 1e6)

        # The ID string.
        ri_id = "%s_%s" % (ri_type, frq_label)

        # The number of spins.
        N = bmrb.num_spins(data)

        # No data in the saveframe.
        if N == 0:
            continue

        # The molecule names.
        mol_names = bmrb.molecule_names(data, N)

        # Generate the sequence if needed.
        bmrb.generate_sequence(N, spin_names=data['atom_names'], res_nums=data['res_nums'], res_names=data['res_names'], mol_names=mol_names, isotopes=data['isotope'], elements=data['atom_types'])

        # The attached protons.
        if 'atom_names_2' in data:
            # Generate the proton spins.
            bmrb.generate_sequence(N, spin_names=data['atom_names_2'], res_nums=data['res_nums'], res_names=data['res_names'], mol_names=mol_names, isotopes=data['isotope_2'], elements=data['atom_types_2'])

            # Define the dipolar interaction.
            for i in range(len(data['atom_names'])):
                # The spin IDs.
                spin_id1 = generate_spin_id_unique(spin_name=data['atom_names'][i], res_num=data['res_nums'][i], res_name=data['res_names'][i], mol_name=mol_names[i])
                spin_id2 = generate_spin_id_unique(spin_name=data['atom_names_2'][i], res_num=data['res_nums'][i], res_name=data['res_names'][i], mol_name=mol_names[i])

                # Check if the container exists.
                if return_interatom(spin_id1=spin_id1, spin_id2=spin_id2):
                    continue

                # Define.
                define(spin_id1=spin_id1, spin_id2=spin_id2, verbose=False)

        # The data and error.
        vals = data['data']
        errors = data['errors']
        if vals == None:
            vals = [None] * N
        if errors == None:
            errors = [None] * N

        # Data transformation.
        if vals != None and 'units' in keys:
            # Scaling.
            if data['units'] == 'ms':
                # Loop over the data.
                for i in range(N):
                    # The value.
                    if vals[i] != None:
                        vals[i] = vals[i] / 1000

                    # The error.
                    if errors[i] != None:
                        errors[i] = errors[i] / 1000

            # Invert.
            if data['units'] in ['s', 'ms']:
                # Loop over the data.
                for i in range(len(vals)):
                    # The value.
                    if vals[i] != None:
                        vals[i] = 1.0 / vals[i]

                    # The error.
                    if vals[i] != None and errors[i] != None:
                        errors[i] = errors[i] * vals[i]**2

        # Pack the data.
        pack_data(ri_id, ri_type, frq, vals, errors, mol_names=mol_names, res_nums=data['res_nums'], res_names=data['res_names'], spin_nums=None, spin_names=data['atom_names'], gen_seq=True, verbose=False)

        # Store the temperature calibration and control.
        if data['temp_calibration']:
            temp_calibration(ri_id=ri_id, method=data['temp_calibration'])
        if data['temp_control']:
            temp_control(ri_id=ri_id, method=data['temp_control'])

        # Peak intensity type.
        if data['peak_intensity_type']:
            peak_intensity_type(ri_id=ri_id, type=data['peak_intensity_type'])


def bmrb_write(star):
    """Generate the relaxation data saveframes for the NMR-STAR dictionary object.

    @param star:    The NMR-STAR dictionary object.
    @type star:     NMR_STAR instance
    """

    # Get the current data pipe.
    cdp = pipes.get_pipe()

    # Initialise the spin specific data lists.
    mol_name_list = []
    res_num_list = []
    res_name_list = []
    atom_name_list = []
    isotope_list = []
    element_list = []
    attached_atom_name_list = []
    attached_isotope_list = []
    attached_element_list = []
    ri_data_list = []
    ri_data_err_list = []
    for i in range(len(cdp.ri_ids)):
        ri_data_list.append([])
        ri_data_err_list.append([])

    # Relax data labels.
    labels = cdp.ri_ids
    exp_label = []
    spectro_ids = []
    spectro_labels = []

    # Store the spin specific data in lists for later use.
    for spin, mol_name, res_num, res_name, spin_id in spin_loop(full_info=True, return_id=True):
        # Skip spins with no relaxation data.
        if not hasattr(spin, 'ri_data'):
            continue

        # Check the data for None (not allowed in BMRB!).
        if res_num == None:
            raise RelaxError("For the BMRB, the residue of spin '%s' must be numbered." % spin_id)
        if res_name == None:
            raise RelaxError("For the BMRB, the residue of spin '%s' must be named." % spin_id)
        if spin.name == None:
            raise RelaxError("For the BMRB, the spin '%s' must be named." % spin_id)
        if spin.isotope == None:
            raise RelaxError("For the BMRB, the spin isotope type of '%s' must be specified." % spin_id)

        # The molecule/residue/spin info.
        mol_name_list.append(mol_name)
        res_num_list.append(str(res_num))
        res_name_list.append(str(res_name))
        atom_name_list.append(str(spin.name))

        # Interatomic info.
        interatoms = return_interatom_list(spin_id)
        if len(interatoms) == 0:
            raise RelaxError("No interatomic interactions are defined for the spin '%s'." % spin_id)
        if len(interatoms) > 1:
            raise RelaxError("The BMRB only handles a signal interatomic interaction for the spin '%s'." % spin_id)

        # Get the attached spin.
        spin_attached = return_spin(interatoms[0].spin_id1)
        if id(spin_attached) == id(spin):
            spin_attached = return_spin(interatoms[0].spin_id2)

        # The attached atom info.
        if hasattr(spin_attached, 'name'):
            attached_atom_name_list.append(str(spin_attached.name))
        else:
            attached_atom_name_list.append(None)
        if hasattr(spin_attached, 'isotope'):
            attached_element_list.append(element_from_isotope(spin_attached.isotope))
            attached_isotope_list.append(str(number_from_isotope(spin_attached.isotope)))
        else:
            attached_element_list.append(None)
            attached_isotope_list.append(None)

        # The relaxation data.
        used_index = -ones(len(cdp.ri_ids))
        for i in range(len(cdp.ri_ids)):
            # Data exists.
            if cdp.ri_ids[i] in list(spin.ri_data.keys()):
                ri_data_list[i].append(str(spin.ri_data[cdp.ri_ids[i]]))
                ri_data_err_list[i].append(str(spin.ri_data_err[cdp.ri_ids[i]]))
            else:
                ri_data_list[i].append(None)
                ri_data_err_list[i].append(None)

        # Other info.
        isotope_list.append(int(spin.isotope.strip(string.ascii_letters)))
        element_list.append(spin.element)

    # Convert the molecule names into the entity IDs.
    entity_ids = zeros(len(mol_name_list), int32)
    mol_names = get_molecule_names()
    for i in range(len(mol_name_list)):
        for j in range(len(mol_names)):
            if mol_name_list[i] == mol_names[j]:
                entity_ids[i] = j+1

    # Check the temperature control methods.
    if not hasattr(cdp, 'exp_info') or not hasattr(cdp.exp_info, 'temp_calibration'):
        raise RelaxError("The temperature calibration methods have not been specified.")
    if not hasattr(cdp, 'exp_info') or not hasattr(cdp.exp_info, 'temp_control'):
        raise RelaxError("The temperature control methods have not been specified.")

    # Check the peak intensity type.
    if not hasattr(cdp, 'exp_info') or not hasattr(cdp.exp_info, 'peak_intensity_type'):
        raise RelaxError("The peak intensity types measured for the relaxation data have not been specified.")

    # Loop over the relaxation data.
    for i in range(len(cdp.ri_ids)):
        # Alias.
        ri_id = cdp.ri_ids[i]
        ri_type = cdp.ri_type[ri_id]

        # Convert to MHz.
        frq = cdp.spectrometer_frq[ri_id] * 1e-6

        # Get the temperature control methods.
        temp_calib = cdp.exp_info.temp_calibration[ri_id]
        temp_control = cdp.exp_info.temp_control[ri_id]

        # Get the peak intensity type.
        peak_intensity_type = cdp.exp_info.peak_intensity_type[ri_id]

        # Check.
        if not temp_calib:
            raise RelaxError("The temperature calibration method for the '%s' relaxation data ID string has not been specified." % ri_id)
        if not temp_control:
            raise RelaxError("The temperature control method for the '%s' relaxation data ID string has not been specified." % ri_id)

        # Add the relaxation data.
        star.relaxation.add(data_type=ri_type, frq=frq, entity_ids=entity_ids, res_nums=res_num_list, res_names=res_name_list, atom_names=atom_name_list, atom_types=element_list, isotope=isotope_list, entity_ids_2=entity_ids, res_nums_2=res_num_list, res_names_2=res_name_list, atom_names_2=attached_atom_name_list, atom_types_2=attached_element_list, isotope_2=attached_isotope_list, data=ri_data_list[i], errors=ri_data_err_list[i], temp_calibration=temp_calib, temp_control=temp_control, peak_intensity_type=peak_intensity_type)

        # The experimental label.
        if ri_type == 'NOE':
            exp_name = 'steady-state NOE'
        else:
            exp_name = ri_type
        exp_label.append("%s MHz %s" % (frq, exp_name))

        # Spectrometer info.
        frq_num = 1
        for frq in loop_frequencies():
            if frq == cdp.spectrometer_frq[ri_id]:
                break
            frq_num += 1
        spectro_ids.append(frq_num)
        spectro_labels.append("$spectrometer_%s" % spectro_ids[-1])

    # Add the spectrometer info.
    num = 1
    for frq in loop_frequencies():
        star.nmr_spectrometer.add(name="$spectrometer_%s" % num, manufacturer=None, model=None, frq=int(frq/1e6))
        num += 1

    # Add the experiment saveframe.
    star.experiment.add(name=exp_label, spectrometer_ids=spectro_ids, spectrometer_labels=spectro_labels)


def copy(pipe_from=None, pipe_to=None, ri_id=None):
    """Copy the relaxation data from one data pipe to another.

    @keyword pipe_from: The data pipe to copy the relaxation data from.  This defaults to the current data pipe.
    @type pipe_from:    str
    @keyword pipe_to:   The data pipe to copy the relaxation data to.  This defaults to the current data pipe.
    @type pipe_to:      str
    @param ri_id:       The relaxation data ID string.
    @type ri_id:        str
    """

    # Defaults.
    if pipe_from == None and pipe_to == None:
        raise RelaxError("The pipe_from and pipe_to arguments cannot both be set to None.")
    elif pipe_from == None:
        pipe_from = pipes.cdp_name()
    elif pipe_to == None:
        pipe_to = pipes.cdp_name()

    # Test if the pipe_from and pipe_to data pipes exist.
    pipes.test(pipe_from)
    pipes.test(pipe_to)

    # Get the data pipes.
    dp_from = pipes.get_pipe(pipe_from)
    dp_to = pipes.get_pipe(pipe_to)

    # Test if pipe_from contains sequence data.
    if not exists_mol_res_spin_data(pipe_from):
        raise RelaxNoSequenceError

    # Test if pipe_to contains sequence data.
    if not exists_mol_res_spin_data(pipe_to):
        raise RelaxNoSequenceError

    # Test if relaxation data ID string exists for pipe_from.
    if ri_id and (not hasattr(dp_from, 'ri_ids') or ri_id not in dp_from.ri_ids):
        raise RelaxNoRiError(ri_id)

    # The IDs.
    if ri_id == None:
        ri_ids = dp_from.ri_ids
    else:
        ri_ids = [ri_id]

    # Init target pipe global structures.
    if not hasattr(dp_to, 'ri_ids'):
        dp_to.ri_ids = []
    if not hasattr(dp_to, 'ri_type'):
        dp_to.ri_type = {}

    # Loop over the Rx IDs.
    for ri_id in ri_ids:
        # Test if relaxation data ID string exists for pipe_to.
        if ri_id in dp_to.ri_ids:
            raise RelaxRiError(ri_id)

        # Copy the global data.
        dp_to.ri_ids.append(ri_id)
        dp_to.ri_type[ri_id] = dp_from.ri_type[ri_id]

        # Copy the frequency information.
        copy_frequencies(pipe_from=pipe_from, pipe_to=pipe_to, id=ri_id)

        # Spin loop.
        for mol_index, res_index, spin_index in spin_index_loop():
            # Alias the spin containers.
            spin_from = dp_from.mol[mol_index].res[res_index].spin[spin_index]
            spin_to = dp_to.mol[mol_index].res[res_index].spin[spin_index]

            # No data or errors.
            if not hasattr(spin_from, 'ri_data') and not hasattr(spin_from, 'ri_data_err'):
                continue

            # Initialise the spin data if necessary.
            if not hasattr(spin_to, 'ri_data'):
                spin_to.ri_data = {}
            if not hasattr(spin_to, 'ri_data_err'):
                spin_to.ri_data_err = {}

            # Copy the value and error from pipe_from.
            spin_to.ri_data[ri_id] = spin_from.ri_data[ri_id]
            spin_to.ri_data_err[ri_id] = spin_from.ri_data_err[ri_id]


def create_frq_label(frq):
    """Generate a frequency label in MHz, rounded to the nearest factor of 10.

    @param frq:     The frequency in Hz.
    @type frq:      float
    @return:        The MHz frequency label.
    @rtype:         str
    """

    # Convert to MHz.
    label = frq / 1e6

    # Rounding to the nearest factor of 10.
    label = int(round(label/10)*10)

    # Convert to str and return.
    return str(label)


def delete(ri_id=None):
    """Delete relaxation data corresponding to the relaxation data ID.

    @keyword ri_id: The relaxation data ID string.
    @type ri_id:    str
    """

    # Test if the current pipe exists.
    pipes.test()

    # Test if the sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Check the ID.
    if ri_id == None:
        raise RelaxError("The relaxation data ID string must be supplied.")

    # Test if data exists.
    if not hasattr(cdp, 'ri_ids') or ri_id not in cdp.ri_ids:
        raise RelaxNoRiError(ri_id)

    # Pop the ID, and remove it from the frequency and type lists.
    cdp.ri_ids.pop(cdp.ri_ids.index(ri_id))
    del cdp.ri_type[ri_id]

    # Prune empty structures.
    if len(cdp.ri_ids) == 0:
        del cdp.ri_ids
    if len(cdp.ri_type) == 0:
        del cdp.ri_type

    # Loop over the spins, deleting the relaxation data and errors when present.
    for spin in spin_loop():
        # Data deletion.
        if hasattr(spin, 'ri_data') and ri_id in spin.ri_data:
            del spin.ri_data[ri_id]
        if hasattr(spin, 'ri_data_err') and ri_id in spin.ri_data_err:
            del spin.ri_data_err[ri_id]

        # Prune empty structures.
        if hasattr(spin, 'ri_data') and len(spin.ri_data) == 0:
            del spin.ri_data
        if hasattr(spin, 'ri_data_err') and len(spin.ri_data_err) == 0:
            del spin.ri_data_err

    # Delete the metadata.
    if hasattr(cdp, 'exp_info') and hasattr(cdp.exp_info, 'temp_calibration') and ri_id in cdp.exp_info.temp_calibration:
        del cdp.exp_info.temp_calibration[ri_id]
        if len(cdp.exp_info.temp_calibration) == 0:
            del cdp.exp_info.temp_calibration
    if hasattr(cdp, 'exp_info') and hasattr(cdp.exp_info, 'temp_control') and ri_id in cdp.exp_info.temp_control:
        del cdp.exp_info.temp_control[ri_id]
        if len(cdp.exp_info.temp_control) == 0:
            del cdp.exp_info.temp_control
    if hasattr(cdp, 'exp_info') and hasattr(cdp.exp_info, 'peak_intensity_type') and ri_id in cdp.exp_info.peak_intensity_type:
        del cdp.exp_info.peak_intensity_type[ri_id]
        if len(cdp.exp_info.peak_intensity_type) == 0:
            del cdp.exp_info.peak_intensity_type

    # Delete the frequency information.
    delete_frequencies(id=ri_id)


def display(ri_id=None):
    """Display relaxation data corresponding to the ID.

    @keyword ri_id: The relaxation data ID string.
    @type ri_id:    str
    """

    # Test if the current pipe exists.
    pipes.test()

    # Test if the sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Test if data exists.
    if not hasattr(cdp, 'ri_ids') or ri_id not in cdp.ri_ids:
        raise RelaxNoRiError(ri_id)

    # Print the data.
    value.write_data(param=ri_id, file=sys.stdout, return_value=return_value, return_data_desc=return_data_desc)


def get_data_names(global_flag=False, sim_names=False):
    """Return a list of names of data structures associated with relaxation data.

    Description
    ===========

    The names are as follows:

    ri_data:  Relaxation data.

    ri_data_err:  Relaxation data error.

    ri_data_bc:  The back calculated relaxation data.

    ri_type:  The relaxation data type, i.e. one of ['NOE', 'R1', 'R2']

    frq:  NMR frequencies in Hz, eg [600.0 * 1e6, 500.0 * 1e6]


    @keyword global_flag:   A flag which if True corresponds to the pipe specific data structures and if False corresponds to the spin specific data structures.
    @type global_flag:      bool
    @keyword sim_names:     A flag which if True will add the Monte Carlo simulation object names as well.
    @type sim_names:        bool
    @return:                The list of object names.
    @rtype:                 list of str
    """

    # Initialise.
    names = []

    # Global data names.
    if not sim_names and global_flag:
        names.append('ri_id')
        names.append('ri_type')
        names.append('frq')

    # Spin specific data names.
    if not sim_names and not global_flag:
        names.append('ri_data')
        names.append('ri_data_err')
        names.append('ri_data_bc')

    # Simulation object names.
    if sim_names and not global_flag:
        names.append('ri_data_sim')

    # Return the list of names.
    return names


def get_ids():
    """Return the list of all relaxation data IDs.

    @return:        The list of all relaxation data IDs.
    @rtype:         list of str
    """

    # No pipe.
    if cdp == None:
        return []

    # No relaxation data.
    if not hasattr(cdp, 'ri_ids'):
        return []

    # The relaxation data IDs.
    return cdp.ri_ids


def pack_data(ri_id, ri_type, frq, values, errors, spin_ids=None, mol_names=None, res_nums=None, res_names=None, spin_nums=None, spin_names=None, spin_id=None, gen_seq=False, verbose=True):
    """Pack the relaxation data into the data pipe and spin containers.

    The values, errors, and spin_ids arguments must be lists of equal length or None.  Each element i corresponds to a unique spin.

    @param ri_id:           The relaxation data ID string.
    @type ri_id:            str
    @param ri_type:         The relaxation data type, ie 'R1', 'R2', or 'NOE'.
    @type ri_type:          str
    @param frq:             The spectrometer proton frequency in Hz.
    @type frq:              float
    @keyword values:        The relaxation data for each spin.
    @type values:           None or list of float or float array
    @keyword errors:        The relaxation data errors for each spin.
    @type errors:           None or list of float or float array
    @keyword spin_ids:      The list of spin ID strings.  If the other spin identifiers are given, i.e. mol_names, res_nums, res_names, spin_nums, and/or spin_names, then this argument is not necessary.
    @type spin_ids:         None or list of str
    @keyword mol_names:     The list of molecule names used for creating the spin IDs (if not given) or for generating the sequence data.
    @type mol_names:        None or list of str
    @keyword res_nums:      The list of residue numbers used for creating the spin IDs (if not given) or for generating the sequence data.
    @type res_nums:         None or list of str
    @keyword res_names:     The list of residue names used for creating the spin IDs (if not given) or for generating the sequence data.
    @type res_names:        None or list of str
    @keyword spin_nums:     The list of spin numbers used for creating the spin IDs (if not given) or for generating the sequence data.
    @type spin_nums:        None or list of str
    @keyword spin_names:    The list of spin names used for creating the spin IDs (if not given) or for generating the sequence data.
    @type spin_names:       None or list of str
    @keyword gen_seq:       A flag which if True will cause the molecule, residue, and spin sequence data to be generated.
    @type gen_seq:          bool
    @keyword verbose:       A flag which if True will cause all relaxation data loaded to be printed out.
    @type verbose:          bool
    """

    # The number of spins.
    N = len(values)

    # Test the data.
    if errors != None and len(errors) != N:
        raise RelaxError("The length of the errors arg (%s) does not match that of the value arg (%s)." % (len(errors), N))
    if spin_ids and len(spin_ids) != N:
        raise RelaxError("The length of the spin ID strings arg (%s) does not match that of the value arg (%s)." % (len(mol_names), N))
    if mol_names and len(mol_names) != N:
        raise RelaxError("The length of the molecule names arg (%s) does not match that of the value arg (%s)." % (len(mol_names), N))
    if res_nums and len(res_nums) != N:
        raise RelaxError("The length of the residue numbers arg (%s) does not match that of the value arg (%s)." % (len(res_nums), N))
    if res_names and len(res_names) != N:
        raise RelaxError("The length of the residue names arg (%s) does not match that of the value arg (%s)." % (len(res_names), N))
    if spin_nums and len(spin_nums) != N:
        raise RelaxError("The length of the spin numbers arg (%s) does not match that of the value arg (%s)." % (len(spin_nums), N))
    if spin_names and len(spin_names) != N:
        raise RelaxError("The length of the spin names arg (%s) does not match that of the value arg (%s)." % (len(spin_names), N))

    # Generate some empty lists.
    if not mol_names:
        mol_names = [None] * N
    if not res_nums:
        res_nums = [None] * N
    if not res_names:
        res_names = [None] * N
    if not spin_nums:
        spin_nums = [None] * N
    if not spin_names:
        spin_names = [None] * N
    if errors == None:
        errors = [None] * N

    # Generate the spin IDs.
    if not spin_ids:
        spin_ids = []
        for i in range(N):
            spin_ids.append(generate_spin_id_unique(spin_num=spin_nums[i], spin_name=spin_names[i], res_num=res_nums[i], res_name=res_names[i], mol_name=mol_names[i]))

    # Initialise the global data for the current pipe if necessary.
    if not hasattr(cdp, 'ri_type'):
        cdp.ri_type = {}
    if not hasattr(cdp, 'ri_ids'):
        cdp.ri_ids = []

    # Set the spectrometer frequency.
    set_frequency(id=ri_id, frq=frq)

    # Update the global data.
    cdp.ri_ids.append(ri_id)
    cdp.ri_type[ri_id] = ri_type

    # The selection object.
    select_obj = None
    if spin_id:
        select_obj = Selection(spin_id)

    # Loop over the spin data.
    data = []
    for i in range(N):
        # Get the corresponding spin container.
        match_mol_names, match_res_nums, match_res_names, spins = return_spin_from_selection(spin_ids[i], full_info=True, multi=True)
        if spins in [None, []]:
            raise RelaxNoSpinError(spin_ids[i])

        # Remove non-matching spins.
        if select_obj:
            new_spins = []
            new_mol_names = []
            new_res_nums = []
            new_res_names = []
            new_ids = []
            for j in range(len(spins)):
                if select_obj.contains_spin(spin_num=spins[j].num, spin_name=spins[j].name, res_num=match_res_nums[j], res_name=match_res_names[j], mol=match_mol_names[j]):
                    new_spins.append(spins[j])
                    new_mol_names.append(match_mol_names[j])
                    new_res_nums.append(match_res_nums[j])
                    new_res_names.append(match_res_names[j])
                    new_ids.append(generate_spin_id_unique(mol_name=mol_names[i], res_num=res_nums[i], res_name=res_names[i], spin_num=spins[j].num, spin_name=spins[j].name))
            new_id = new_ids[0]

        # Aliases for normal operation.
        else:
            new_spins = spins
            new_mol_names = match_mol_names
            new_res_nums = match_res_nums
            new_res_names = match_res_names
            new_id = spin_ids[i]
            new_ids = None

        # Check that only a singe spin is present.
        if len(new_spins) > 1:
            if new_ids:
                raise RelaxMultiSpinIDError(spin_ids[i], new_ids)
            else:
                raise RelaxMultiSpinIDError(spin_ids[i], new_ids)
        if len(new_spins) == 0:
            raise RelaxNoSpinError(spin_ids[i])

        # Loop over the spins.
        for j in range(len(new_spins)):
            # No match to the selection.
            if select_obj and not select_obj.contains_spin(spin_num=new_spins[j].num, spin_name=new_spins[j].name, res_num=new_res_nums[j], res_name=new_res_names[j], mol=new_mol_names[j]):
                continue

            # Initialise the spin data if necessary.
            if not hasattr(new_spins[j], 'ri_data') or new_spins[j].ri_data == None:
                new_spins[j].ri_data = {}
            if not hasattr(new_spins[j], 'ri_data_err') or new_spins[j].ri_data_err == None:
                new_spins[j].ri_data_err = {}

            # Update all data structures.
            new_spins[j].ri_data[ri_id] = values[i]
            new_spins[j].ri_data_err[ri_id] = errors[i]

            # Append the data for printing out.
            data.append([new_id, repr(values[i]), repr(errors[i])])

    # Print out.
    if verbose:
        print("\nThe following %s MHz %s relaxation data with the ID '%s' has been loaded into the relax data store:\n" % (frq/1e6, ri_type, ri_id))
        write_data(out=sys.stdout, headings=["Spin_ID", "Value", "Error"], data=data)


def peak_intensity_type(ri_id=None, type=None):
    """Set the type of intensity measured for the peaks.

    @keyword ri_id: The relaxation data ID string.
    @type ri_id:    str
    @keyword type:  The peak intensity type, one of 'height' or 'volume'.
    @type type:     str
    """

    # Test if the current pipe exists.
    pipes.test()

    # Test if sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Test if data exists.
    if not hasattr(cdp, 'ri_ids') or ri_id not in cdp.ri_ids:
        raise RelaxNoRiError(ri_id)

    # Check the values, and warn if not in the list.
    valid = ['height', 'volume']
    if type not in valid:
        raise RelaxError("The '%s' peak intensity type is unknown.  Please select one of %s." % (type, valid))

    # Set up the experimental info data container, if needed.
    if not hasattr(cdp, 'exp_info'):
        cdp.exp_info = ExpInfo()

    # Store the type.
    cdp.exp_info.setup_peak_intensity_type(ri_id, type)


def read(ri_id=None, ri_type=None, frq=None, file=None, dir=None, file_data=None, spin_id_col=None, mol_name_col=None, res_num_col=None, res_name_col=None, spin_num_col=None, spin_name_col=None, data_col=None, error_col=None, sep=None, spin_id=None):
    """Read R1, R2, or NOE, or R2eff relaxation data from a file.

    @param ri_id:           The relaxation data ID string.
    @type ri_id:            str
    @param ri_type:         The relaxation data type, ie 'R1', 'R2', 'NOE', or 'R2eff'.
    @type ri_type:          str
    @param frq:             The spectrometer proton frequency in Hz.
    @type frq:              float
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
    @keyword data_col:      The column containing the relaxation data.
    @type data_col:         int or None
    @keyword error_col:     The column containing the relaxation data errors.
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

    # Test if the ri_id already exists.
    if hasattr(cdp, 'ri_ids') and ri_id in cdp.ri_ids:
        raise RelaxError("The relaxation ID string '%s' already exists." % ri_id)

    # Check if the type is valid.
    if ri_type not in VALID_TYPES:
        raise RelaxError("The relaxation data type '%s' must be one of %s." % (ri_type, VALID_TYPES))

    # Frequency checks.
    frequency_checks(frq)

    # Loop over the file data to create the data structures for packing.
    values = []
    errors = []
    mol_names = []
    res_nums = []
    res_names = []
    spin_nums = []
    spin_names = []
    for data in read_spin_data(file=file, dir=dir, file_data=file_data, spin_id_col=spin_id_col, mol_name_col=mol_name_col, res_num_col=res_num_col, res_name_col=res_name_col, spin_num_col=spin_num_col, spin_name_col=spin_name_col, data_col=data_col, error_col=error_col, sep=sep):
        # Unpack.
        if data_col and error_col:
            mol_name, res_num, res_name, spin_num, spin_name, value, error = data
        elif data_col:
            mol_name, res_num, res_name, spin_num, spin_name, value = data
            error = None
        else:
            mol_name, res_num, res_name, spin_num, spin_name, error = data
            value = None

        # No data.
        if value == None and error == None:
            continue

        # Store all the info.
        mol_names.append(mol_name)
        res_nums.append(res_num)
        res_names.append(res_name)
        spin_nums.append(spin_num)
        spin_names.append(spin_name)
        values.append(value)
        errors.append(error)

    # Pack the data.
    pack_data(ri_id, ri_type, frq, values, errors, mol_names=mol_names, res_nums=res_nums, res_names=res_names, spin_nums=spin_nums, spin_names=spin_names, spin_id=spin_id)


def return_data_desc(name):
    """Return a description of the spin specific object.

    @param name:    The name of the spin specific object.
    @type name:     str
    """

    if name == 'ri_data':
        return 'The relaxation data'
    if name == 'ri_data_err':
        return 'The relaxation data errors'


def return_value(spin, data_type, bc=False):
    """Return the value and error corresponding to 'data_type'.

    @param spin:        The spin container.
    @type spin:         SpinContainer instance
    @param data_type:   The relaxation data ID string.
    @type data_type:    str
    @keyword bc:        A flag which if True will cause the back calculated relaxation data to be written.
    @type bc:           bool
    """

    # Relaxation data.
    data = None
    if not bc and hasattr(spin, 'ri_data') and spin.ri_data != None and data_type in list(spin.ri_data.keys()):
        data = spin.ri_data[data_type]

    # Back calculated relaxation data
    if bc and hasattr(spin, 'ri_data_bc') and spin.ri_data_bc != None and data_type in list(spin.ri_data_bc.keys()):
        data = spin.ri_data_bc[data_type]

    # Relaxation errors.
    error = None
    if hasattr(spin, 'ri_data_err') and spin.ri_data_err != None and data_type in list(spin.ri_data_err.keys()):
        error = spin.ri_data_err[data_type]

    # Return the data.
    return data, error


def temp_calibration(ri_id=None, method=None):
    """Set the temperature calibration method.

    @keyword ri_id:     The relaxation data type, ie 'R1', 'R2', or 'NOE'.
    @type ri_id:        str
    @keyword method:    The temperature calibration method.
    @type method:       str
    """

    # Test if the current pipe exists.
    pipes.test()

    # Test if sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Test if data exists.
    if not hasattr(cdp, 'ri_ids') or ri_id not in cdp.ri_ids:
        raise RelaxNoRiError(ri_id)

    # Check the values, and warn if not in the list.
    valid = ['methanol', 'monoethylene glycol', 'no calibration applied']
    if method not in valid:
        warn(RelaxWarning("The '%s' method is unknown.  Please try to use one of %s." % (method, valid)))

    # Set up the experimental info data container, if needed.
    if not hasattr(cdp, 'exp_info'):
        cdp.exp_info = ExpInfo()

    # Store the method.
    cdp.exp_info.temp_calibration_setup(ri_id, method)


def temp_control(ri_id=None, method=None):
    """Set the temperature control method.

    @keyword ri_id:     The relaxation data ID string.
    @type ri_id:        str
    @keyword method:    The temperature control method.
    @type method:       str
    """

    # Test if the current pipe exists.
    pipes.test()

    # Test if sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Test if data exists.
    if not hasattr(cdp, 'ri_ids') or ri_id not in cdp.ri_ids:
        raise RelaxNoRiError(ri_id)

    # Check the values, and warn if not in the list.
    valid = ['single scan interleaving', 'temperature compensation block', 'single scan interleaving and temperature compensation block', 'single fid interleaving', 'single experiment interleaving', 'no temperature control applied']
    if method not in valid:
        raise RelaxError("The '%s' method is unknown.  Please select one of %s." % (method, valid))

    # Set up the experimental info data container, if needed.
    if not hasattr(cdp, 'exp_info'):
        cdp.exp_info = ExpInfo()

    # Store the method.
    cdp.exp_info.temp_control_setup(ri_id, method)


def type(ri_id=None, ri_type=None):
    """Set or reset the frequency associated with the ID.

    @param ri_id:   The relaxation data ID string.
    @type ri_id:    str
    @param ri_type: The relaxation data type, ie 'R1', 'R2', or 'NOE'.
    @type ri_type:  str
    """

    # Test if the current data pipe exists.
    pipes.test()

    # Test if sequence data exists.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Test if data exists.
    if not hasattr(cdp, 'ri_ids') or ri_id not in cdp.ri_ids:
        raise RelaxNoRiError(ri_id)

    # Check if the type is valid.
    if ri_type not in VALID_TYPES:
        raise RelaxError("The relaxation data type '%s' must be one of %s." % (ri_type, VALID_TYPES))

    # Initialise if needed.
    if not hasattr(cdp, 'ri_type'):
        cdp.ri_type = {}

    # Set the type.
    cdp.ri_type[ri_id] = ri_type


def write(ri_id=None, file=None, dir=None, bc=False, force=False):
    """Write relaxation data to a file.

    @keyword ri_id: The relaxation data ID string.
    @type ri_id:    str
    @keyword file:  The name of the file to create.
    @type file:     str
    @keyword dir:   The directory to write to.
    @type dir:      str or None
    @keyword bc:    A flag which if True will cause the back calculated relaxation data to be written.
    @type bc:       bool
    @keyword force: A flag which if True will cause any pre-existing file to be overwritten.
    @type force:    bool
    """

    # Test if the current pipe exists.
    pipes.test()

    # Test if the sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Test if data exists.
    if not hasattr(cdp, 'ri_ids') or ri_id not in cdp.ri_ids:
        raise RelaxNoRiError(ri_id)

    # Create the file name if none is given.
    if file == None:
        file = ri_id + ".out"

    # Write the data.
    value.write(param=ri_id, file=file, dir=dir, bc=bc, force=force, return_value=return_value, return_data_desc=return_data_desc)
