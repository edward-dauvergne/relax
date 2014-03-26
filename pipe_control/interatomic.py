###############################################################################
#                                                                             #
# Copyright (C) 2012-2014 Edward d'Auvergne                                   #
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
"""Module for the manipulation of the interatomic data structures in the relax data store."""

# Python module imports.
from copy import deepcopy
from numpy import float64, zeros
from numpy.linalg import norm
from re import search
import sys
from warnings import warn

# relax module imports.
from lib.arg_check import is_float
from lib.errors import RelaxError, RelaxInteratomInconsistentError, RelaxNoInteratomError, RelaxNoSpinError
from lib.io import extract_data, strip, write_data
from lib.warnings import RelaxWarning, RelaxZeroVectorWarning
from pipe_control import pipes
from pipe_control.mol_res_spin import Selection, count_spins, exists_mol_res_spin_data, generate_spin_id_unique, return_spin, spin_loop


def copy(pipe_from=None, pipe_to=None, spin_id1=None, spin_id2=None, verbose=True):
    """Copy the interatomic data from one data pipe to another.

    @keyword pipe_from:         The data pipe to copy the interatomic data from.  This defaults to the current data pipe.
    @type pipe_from:            str
    @keyword pipe_to:           The data pipe to copy the interatomic data to.  This defaults to the current data pipe.
    @type pipe_to:              str
    @keyword spin_id1:          The spin ID string of the first atom.
    @type spin_id1:             str
    @keyword spin_id2:          The spin ID string of the second atom.
    @type spin_id2:             str
    @keyword verbose:           A flag which if True will cause info about each spin pair to be printed out.
    @type verbose:              bool
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

    # Check that the spin IDs exist.
    if spin_id1:
        if count_spins(selection=spin_id1, pipe=pipe_from, skip_desel=False) == 0:
            raise RelaxNoSpinError(spin_id1, pipe_from)
        if count_spins(selection=spin_id1, pipe=pipe_to, skip_desel=False) == 0:
            raise RelaxNoSpinError(spin_id1, pipe_to)
    if spin_id2:
        if count_spins(selection=spin_id2, pipe=pipe_from, skip_desel=False) == 0:
            raise RelaxNoSpinError(spin_id2, pipe_from)
        if count_spins(selection=spin_id2, pipe=pipe_to, skip_desel=False) == 0:
            raise RelaxNoSpinError(spin_id2, pipe_to)

    # Check for the sequence data in the target pipe if no spin IDs are given.
    if not spin_id1 and not spin_id2:
        for spin, spin_id in spin_loop(pipe=pipe_from, return_id=True):
            if not return_spin(spin_id, pipe=pipe_to):
                raise RelaxNoSpinError(spin_id, pipe_to)

    # Test if pipe_from contains interatomic data (skipping the rest of the function if it is missing).
    if not exists_data(pipe_from):
        return

    # Loop over the interatomic data of the pipe_from data pipe.
    ids = []
    for interatom in interatomic_loop(selection1=spin_id1, selection2=spin_id2, pipe=pipe_from):
        # Create a new container.
        new_interatom = create_interatom(spin_id1=interatom.spin_id1, spin_id2=interatom.spin_id2, pipe=pipe_to)

        # Duplicate all the objects of the container.
        for name in dir(interatom):
            # Skip special objects.
            if search('^_', name):
                continue

            # Skip the spin IDs.
            if name in ['spin_id1', 'spin_id2']:
                continue

            # Skip class methods.
            if name in list(interatom.__class__.__dict__.keys()):
                continue

            # Duplicate all other objects.
            obj = deepcopy(getattr(interatom, name))
            setattr(new_interatom, name, obj)

        # Store the IDs for the printout.
        ids.append([repr(interatom.spin_id1), repr(interatom.spin_id2)])

    # Print out.
    if verbose:
        write_data(out=sys.stdout, headings=["Spin_ID_1", "Spin_ID_2"], data=ids)


def consistent_interatomic_data(pipe1=None, pipe2=None):
    """Check that the interatomic data is consistent between two data pipes.

    @keyword pipe1:     The name of the first data pipe to compare.
    @type pipe1:        str
    @keyword pipe2:     The name of the second data pipe to compare.
    @type pipe2:        str
    @raises RelaxError: If the data is inconsistent.
    """

    # Get the data pipes.
    dp1 = pipes.get_pipe(pipe1)
    dp2 = pipes.get_pipe(pipe2)

    # Check the data lengths.
    if len(dp1.interatomic) != len(dp2.interatomic):
        raise RelaxInteratomInconsistentError(pipe1, pipe2)

    # Loop over the interatomic data.
    for i in range(len(dp1.interatomic)):
        # Alias the containers.
        interatom1 = dp1.interatomic[i]
        interatom2 = dp2.interatomic[i]

        # Check the spin IDs.
        if interatom1.spin_id1 != interatom2.spin_id1:
            raise RelaxInteratomInconsistentError(pipe1, pipe2)
        if interatom1.spin_id2 != interatom2.spin_id2:
            raise RelaxInteratomInconsistentError(pipe1, pipe2)


def create_interatom(spin_id1=None, spin_id2=None, pipe=None, verbose=False):
    """Create and return the interatomic data container for the two spins.

    @keyword spin_id1:  The spin ID string of the first atom.
    @type spin_id1:     str
    @keyword spin_id2:  The spin ID string of the second atom.
    @type spin_id2:     str
    @keyword pipe:      The data pipe to create the interatomic data container for.  This defaults to the current data pipe if not supplied.
    @type pipe:         str or None
    @keyword verbose:   A flag which if True will result printouts.
    @type verbose:      bool
    @return:            The newly created interatomic data container.
    @rtype:             data.interatomic.InteratomContainer instance
    """

    # Printout.
    if verbose:
        print("Creating an interatomic data container between the spins '%s' and '%s'." % (spin_id1, spin_id2))

    # The data pipe.
    if pipe == None:
        pipe = pipes.cdp_name()

    # Get the data pipe.
    dp = pipes.get_pipe(pipe)

    # Check that the spin IDs exist.
    spin = return_spin(spin_id1, pipe)
    if spin == None:
        raise RelaxNoSpinError(spin_id1)
    spin = return_spin(spin_id2, pipe)
    if spin == None:
        raise RelaxNoSpinError(spin_id2)

    # Check if the two spin IDs have already been added.
    for i in range(len(dp.interatomic)):
        if id_match(spin_id=spin_id1, interatom=dp.interatomic[i], pipe=pipe) and id_match(spin_id=spin_id2, interatom=dp.interatomic[i], pipe=pipe):
            raise RelaxError("The spin pair %s and %s have already been added." % (spin_id1, spin_id2))

    # Add and return the data.
    return dp.interatomic.add_item(spin_id1=spin_id1, spin_id2=spin_id2)


def define(spin_id1=None, spin_id2=None, pipe=None, direct_bond=False, verbose=True):
    """Set up the magnetic dipole-dipole interaction.

    @keyword spin_id1:      The spin identifier string of the first spin of the pair.
    @type spin_id1:         str
    @keyword spin_id2:      The spin identifier string of the second spin of the pair.
    @type spin_id2:         str
    @param pipe:        The data pipe to operate on.  Defaults to the current data pipe.
    @type pipe:         str
    @keyword direct_bond:   A flag specifying if the two spins are directly bonded.
    @type direct_bond:      bool
    @keyword verbose:       A flag which if True will result in printouts of the created interatomoic data containers.
    @type verbose:          bool
    """

    # The data pipe.
    if pipe == None:
        pipe = pipes.cdp_name()

    # Get the data pipe.
    dp = pipes.get_pipe(pipe)

    # Initialise the spin ID pairs list.
    ids = []

    # Use the structural data to find connected atoms.
    if hasattr(dp, 'structure'):
        # Loop over the atoms of the first spin selection.
        for mol_name1, res_num1, res_name1, atom_num1, atom_name1, mol_index1, atom_index1 in dp.structure.atom_loop(atom_id=spin_id1, model_num=1, mol_name_flag=True, res_num_flag=True, res_name_flag=True, atom_num_flag=True, atom_name_flag=True, mol_index_flag=True, index_flag=True):
            # Generate the first spin ID.
            id1 = generate_spin_id_unique(pipe_cont=dp, mol_name=mol_name1, res_num=res_num1, res_name=res_name1, spin_num=atom_num1, spin_name=atom_name1)

            # Do the spin exist?
            if not return_spin(id1):
                continue

            # Loop over the atoms of the second spin selection.
            for mol_name2, res_num2, res_name2, atom_num2, atom_name2, mol_index2, atom_index2 in dp.structure.atom_loop(atom_id=spin_id2, model_num=1, mol_name_flag=True, res_num_flag=True, res_name_flag=True, atom_num_flag=True, atom_name_flag=True, mol_index_flag=True, index_flag=True):
                # Directly bonded atoms.
                if direct_bond:
                    # Different molecules.
                    if mol_name1 != mol_name2:
                        continue

                    # Skip non-bonded atom pairs.
                    if not dp.structure.are_bonded_index(mol_index1=mol_index1, atom_index1=atom_index1, mol_index2=mol_index2, atom_index2=atom_index2):
                        continue

                # Generate the second spin ID.
                id2 = generate_spin_id_unique(pipe_cont=dp, mol_name=mol_name2, res_num=res_num2, res_name=res_name2, spin_num=atom_num2, spin_name=atom_name2)

                # Do the spin exist?
                if not return_spin(id2):
                    continue

                # Store the IDs for the printout.
                ids.append([id1, id2])

    # No structural data present or the spin IDs are not in the structural data, so use spin loops and some basic rules.
    if ids == []:
        for spin1, mol_name1, res_num1, res_name1, id1 in spin_loop(spin_id1, pipe=pipe, full_info=True, return_id=True):
            for spin2, mol_name2, res_num2, res_name2, id2 in spin_loop(spin_id2, pipe=pipe, full_info=True, return_id=True):
                # Directly bonded atoms.
                if direct_bond:
                    # Different molecules.
                    if mol_name1 != mol_name2:
                        continue

                    # No element info.
                    if not hasattr(spin1, 'element'):
                        raise RelaxError("The spin '%s' does not have the element type set." % id1)
                    if not hasattr(spin2, 'element'):
                        raise RelaxError("The spin '%s' does not have the element type set." % id2)

                    # Backbone NH and CH pairs.
                    pair = False
                    if (spin1.element == 'N' and spin2.element == 'H') or (spin2.element == 'N' and spin1.element == 'H'):
                        pair = True
                    elif (spin1.element == 'C' and spin2.element == 'H') or (spin2.element == 'C' and spin1.element == 'H'):
                        pair = True

                    # Same residue, so skip.
                    if pair and res_num1 != None and res_num1 != res_num2:
                        continue
                    elif pair and res_num1 == None and res_name1 != res_name2:
                        continue

                # Store the IDs for the printout.
                ids.append([id1, id2])

    # No matches, so fail!
    if not len(ids):
        # Find the problem.
        count1 = 0
        count2 = 0
        for spin in spin_loop(spin_id1):
            count1 += 1
        for spin in spin_loop(spin_id2):
            count2 += 1

        # Report the problem.
        if count1 == 0 and count2 == 0:
            raise RelaxError("Neither spin IDs '%s' and '%s' match any spins." % (spin_id1, spin_id2))
        elif count1 == 0:
            raise RelaxError("The spin ID '%s' matches no spins." % spin_id1)
        elif count2 == 0:
            raise RelaxError("The spin ID '%s' matches no spins." % spin_id2)
        else:
            raise RelaxError("Unknown error.")

    # Define the interaction.
    for id1, id2 in ids:
        # Get the interatomic data object, if it exists.
        interatom = return_interatom(id1, id2, pipe=pipe)

        # Create the container if needed.
        if interatom == None:
            interatom = create_interatom(spin_id1=id1, spin_id2=id2, pipe=pipe)

        # Check that this has not already been set up.
        if interatom.dipole_pair:
            raise RelaxError("The magnetic dipole-dipole interaction already exists between the spins '%s' and '%s'." % (id1, id2))

        # Set a flag indicating that a dipole-dipole interaction is present.
        interatom.dipole_pair = True

    # Printout.
    if verbose:
        # Conversion.
        for i in range(len(ids)):
            ids[i][0] = repr(ids[i][0])
            ids[i][1] = repr(ids[i][1])

        # The printout.
        print("Interatomic interactions are now defined for the following spins:\n")
        write_data(out=sys.stdout, headings=["Spin_ID_1", "Spin_ID_2"], data=ids)


def exists_data(pipe=None):
    """Determine if any interatomic data exists.

    @keyword pipe:      The data pipe in which the interatomic data will be checked for.
    @type pipe:         str
    @return:            The answer to the question about the existence of data.
    @rtype:             bool
    """

    # The current data pipe.
    if pipe == None:
        pipe = pipes.cdp_name()

    # Test the data pipe.
    pipes.test(pipe)

    # Get the data pipe.
    dp = pipes.get_pipe(pipe)

    # The interatomic data structure is empty.
    if dp.interatomic.is_empty():
        return False

    # Otherwise.
    return True


def id_match(spin_id=None, interatom=None, pipe=None):
    """Test if the spin ID matches one of the two spins of the given container.

    @keyword spin_id:   The spin ID string of the first atom.
    @type spin_id:      str
    @keyword interatom: The interatomic data container.
    @type interatom:    InteratomContainer instance
    @keyword pipe:      The data pipe containing the interatomic data container.  Defaults to the current data pipe.
    @type pipe:         str or None
    @return:            True if the spin ID matches one of the two spins, False otherwise.
    @rtype:             bool
    """

    # Get the spin containers.
    spin1 = return_spin(interatom.spin_id1, pipe=pipe)
    spin2 = return_spin(interatom.spin_id2, pipe=pipe)

    # No spins.
    if spin1 == None or spin2 == None:
        return False

    # Check if the ID is in the private metadata list.
    if spin_id in spin1._spin_ids or spin_id in spin2._spin_ids:
        return True

    # Nothing found.
    return False


def interatomic_loop(selection1=None, selection2=None, pipe=None, skip_desel=True):
    """Generator function for looping over all the interatomic data containers.

    @keyword selection1:    The optional spin ID selection of the first atom.
    @type selection1:       str
    @keyword selection2:    The optional spin ID selection of the second atom.
    @type selection2:       str
    @keyword pipe:          The data pipe containing the spin.  Defaults to the current data pipe.
    @type pipe:             str
    @keyword skip_desel:    A flag which if True will cause only selected interatomic data containers to be returned.
    @type skip_desel:       bool
    """

    # The data pipe.
    if pipe == None:
        pipe = pipes.cdp_name()

    # Get the data pipe.
    dp = pipes.get_pipe(pipe)

    # Parse the spin ID selection strings.
    select_obj = None
    select_obj1 = None
    select_obj2 = None
    if selection1 and selection2:
        select_obj1 = Selection(selection1)
        select_obj2 = Selection(selection2)
    elif selection1:
        select_obj = Selection(selection1)
    elif selection2:
        select_obj = Selection(selection2)

    # Loop over the containers, yielding them.
    for i in range(len(dp.interatomic)):
        # Skip deselected containers.
        if skip_desel and not dp.interatomic[i].select:
            continue

        # Aliases.
        interatom = dp.interatomic[i]
        mol_index1, res_index1, spin_index1 = cdp.mol._spin_id_lookup[interatom.spin_id1]
        mol_index2, res_index2, spin_index2 = cdp.mol._spin_id_lookup[interatom.spin_id2]
        mol1 =  cdp.mol[mol_index1]
        res1 =  cdp.mol[mol_index1].res[res_index1]
        spin1 = cdp.mol[mol_index1].res[res_index1].spin[spin_index1]
        mol2 = cdp.mol[mol_index2]
        res2 =  cdp.mol[mol_index2].res[res_index2]
        spin2 = cdp.mol[mol_index2].res[res_index2].spin[spin_index2]

        # The different selection combinations.
        if select_obj:
            sel1 = select_obj.contains_spin(spin_name=spin1.name, spin_num=spin1.num, res_name=res1.name, res_num=res1.num, mol=mol1.name)
            sel2 = select_obj.contains_spin(spin_name=spin2.name, spin_num=spin2.num, res_name=res2.name, res_num=res2.num, mol=mol2.name)
        if select_obj1:
            sel11 = select_obj1.contains_spin(spin_name=spin1.name, spin_num=spin1.num, res_name=res1.name, res_num=res1.num, mol=mol1.name)
            sel12 = select_obj1.contains_spin(spin_name=spin2.name, spin_num=spin2.num, res_name=res2.name, res_num=res2.num, mol=mol2.name)
        if select_obj2:
            sel21 = select_obj2.contains_spin(spin_name=spin1.name, spin_num=spin1.num, res_name=res1.name, res_num=res1.num, mol=mol1.name)
            sel22 = select_obj2.contains_spin(spin_name=spin2.name, spin_num=spin2.num, res_name=res2.name, res_num=res2.num, mol=mol2.name)

        # Check that the selections are met.
        if select_obj:
            if not sel1 and not sel2:
                continue
        if select_obj1:
            if not (sel11 or sel12):
                continue
        if select_obj2:
            if not (sel21 or sel22):
                continue

        # Return the container.
        yield interatom


def read_dist(file=None, dir=None, unit='meter', spin_id1_col=None, spin_id2_col=None, data_col=None, sep=None):
    """Set up the magnetic dipole-dipole interaction.

    @keyword file:          The name of the file to open.
    @type file:             str
    @keyword dir:           The directory containing the file (defaults to the current directory if None).
    @type dir:              str or None
    @keyword unit:          The measurement unit.  This can be either 'meter' or 'Angstrom'.
    @type unit:             str
    @keyword spin_id1_col:  The column containing the spin ID strings of the first spin.
    @type spin_id1_col:     int
    @keyword spin_id2_col:  The column containing the spin ID strings of the second spin.
    @type spin_id2_col:     int
    @keyword data_col:      The column containing the averaged distances in meters.
    @type data_col:         int or None
    @keyword sep:           The column separator which, if None, defaults to whitespace.
    @type sep:              str or None
    """

    # Check the units.
    if unit not in ['meter', 'Angstrom']:
        raise RelaxError("The measurement unit of '%s' must be one of 'meter' or 'Angstrom'." % unit)

    # Test if the current data pipe exists.
    pipes.test()

    # Test if sequence data exists.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Extract the data from the file, and clean it up.
    file_data = extract_data(file, dir, sep=sep)
    file_data = strip(file_data, comments=True)

    # Loop over the RDC data.
    data = []
    for line in file_data:
        # Invalid columns.
        if spin_id1_col > len(line):
            warn(RelaxWarning("The data %s is invalid, no first spin ID column can be found." % line))
            continue
        if spin_id2_col > len(line):
            warn(RelaxWarning("The data %s is invalid, no second spin ID column can be found." % line))
            continue
        if data_col and data_col > len(line):
            warn(RelaxWarning("The data %s is invalid, no data column can be found." % line))
            continue

        # Unpack.
        spin_id1 = line[spin_id1_col-1]
        spin_id2 = line[spin_id2_col-1]
        ave_dist = None
        if data_col:
            ave_dist = line[data_col-1]

        # Convert and check the value.
        if ave_dist != None:
            try:
                ave_dist = float(ave_dist)
            except ValueError:
                warn(RelaxWarning("The averaged distance of '%s' from the line %s is invalid." % (ave_dist, line)))
                continue

        # Unit conversion.
        if unit == 'Angstrom':
            ave_dist = ave_dist * 1e-10

        # Get the interatomic data container.
        interatom = return_interatom(spin_id1, spin_id2)

        # No container found, so create it.
        if interatom == None:
            interatom = create_interatom(spin_id1=spin_id1, spin_id2=spin_id2, verbose=True)

        # Store the averaged distance.
        interatom.r = ave_dist

        # Store the data for the printout.
        data.append([repr(interatom.spin_id1), repr(interatom.spin_id2), repr(ave_dist)])

    # No data, so fail!
    if not len(data):
        raise RelaxError("No data could be extracted from the file.")

    # Print out.
    print("The following averaged distances have been read:\n")
    write_data(out=sys.stdout, headings=["Spin_ID_1", "Spin_ID_2", "Ave_distance(meters)"], data=data)


def return_interatom(spin_id1=None, spin_id2=None, pipe=None):
    """Return the list of interatomic data containers for the two spins.

    @keyword spin_id1:  The spin ID string of the first atom.
    @type spin_id1:     str
    @keyword spin_id2:  The spin ID string of the second atom.
    @type spin_id2:     str
    @keyword pipe:      The data pipe holding the container.  Defaults to the current data pipe.
    @type pipe:         str or None
    @return:            The matching interatomic data container, if it exists.
    @rtype:             data.interatomic.InteratomContainer instance or None
    """

    # Checks.
    if spin_id1 == None:
        raise RelaxError("The first spin ID must be supplied.")
    if spin_id2 == None:
        raise RelaxError("The second spin ID must be supplied.")

    # The data pipe.
    if pipe == None:
        pipe = pipes.cdp_name()

    # Get the data pipe.
    dp = pipes.get_pipe(pipe)

    # Return the matching container.
    for i in range(len(dp.interatomic)):
        if id_match(spin_id=spin_id1, interatom=dp.interatomic[i], pipe=pipe) and id_match(spin_id=spin_id2, interatom=dp.interatomic[i], pipe=pipe):
            return dp.interatomic[i]

    # No matchs.
    return None


def return_interatom_list(spin_id=None, pipe=None):
    """Return the list of interatomic data containers for the given spin.

    @keyword spin_id:   The spin ID string.
    @type spin_id:      str
    @keyword pipe:      The data pipe holding the container.  This defaults to the current data pipe.
    @type pipe:         str or None
    @return:            The list of matching interatomic data containers, if any exist.
    @rtype:             list of data.interatomic.InteratomContainer instances
    """

    # Check.
    if spin_id == None:
        raise RelaxError("The spin ID must be supplied.")

    # The data pipe.
    if pipe == None:
        pipe = pipes.cdp_name()

    # Get the data pipe.
    dp = pipes.get_pipe(pipe)

    # Initialise.
    interatoms = []

    # Find and append all containers.
    for i in range(len(dp.interatomic)):
        if id_match(spin_id=spin_id, interatom=dp.interatomic[i], pipe=pipe) or id_match(spin_id=spin_id, interatom=dp.interatomic[i], pipe=pipe):
            interatoms.append(dp.interatomic[i])

    # Return the list of containers.
    return interatoms


def set_dist(spin_id1=None, spin_id2=None, ave_dist=None, unit='meter'):
    """Set up the magnetic dipole-dipole interaction.

    @keyword spin_id1:      The spin identifier string of the first spin of the pair.
    @type spin_id1:         str
    @keyword spin_id2:      The spin identifier string of the second spin of the pair.
    @type spin_id2:         str
    @keyword ave_dist:      The r^-3 averaged interatomic distance.
    @type ave_dist:         float
    @keyword unit:          The measurement unit.  This can be either 'meter' or 'Angstrom'.
    @type unit:             str
    """

    # Check the units.
    if unit not in ['meter', 'Angstrom']:
        raise RelaxError("The measurement unit of '%s' must be one of 'meter' or 'Angstrom'." % unit)

    # Unit conversion.
    if unit == 'Angstrom':
        ave_dist = ave_dist * 1e-10

    # Generate the selection objects.
    sel_obj1 = Selection(spin_id1)
    sel_obj2 = Selection(spin_id2)

    # Loop over the interatomic containers.
    data = []
    for interatom in interatomic_loop():
        # Get the spin info.
        mol_name1, res_num1, res_name1, spin1 = return_spin(interatom.spin_id1, full_info=True)
        mol_name2, res_num2, res_name2, spin2 = return_spin(interatom.spin_id2, full_info=True)

        # No match, either way.
        if not (sel_obj1.contains_spin(spin_num=spin1.num, spin_name=spin1.name, res_num=res_num1, res_name=res_name1, mol=mol_name1) and sel_obj2.contains_spin(spin_num=spin2.num, spin_name=spin2.name, res_num=res_num2, res_name=res_name2, mol=mol_name2)) and not (sel_obj2.contains_spin(spin_num=spin1.num, spin_name=spin1.name, res_num=res_num1, res_name=res_name1, mol=mol_name1) and sel_obj1.contains_spin(spin_num=spin2.num, spin_name=spin2.name, res_num=res_num2, res_name=res_name2, mol=mol_name2)):
            continue

        # Store the averaged distance.
        interatom.r = ave_dist

        # Store the data for the printout.
        data.append([repr(interatom.spin_id1), repr(interatom.spin_id2), repr(ave_dist)])

    # No data, so fail!
    if not len(data):
        raise RelaxError("No data could be set.")

    # Print out.
    print("The following averaged distances have been set:\n")
    write_data(out=sys.stdout, headings=["Spin_ID_1", "Spin_ID_2", "Ave_distance(meters)"], data=data)


def unit_vectors(ave=True):
    """Extract the bond vectors from the loaded structures and store them in the spin container.

    @keyword ave:           A flag which if True will cause the average of all vectors to be calculated.
    @type ave:              bool
    """

    # Test if the current data pipe exists.
    pipes.test()

    # Test if interatomic data exists.
    if not exists_data():
        raise RelaxNoInteratomError

    # Print out.
    if ave:
        print("Averaging all vectors.")
    else:
        print("No averaging of the vectors.")

    # Loop over the interatomic data containers.
    no_vectors = True
    pos_info = False
    for interatom in interatomic_loop(skip_desel=False):
        # Get the spin info.
        spin1 = return_spin(interatom.spin_id1)
        spin2 = return_spin(interatom.spin_id2)

        # No positional information.
        if not hasattr(spin1, 'pos'):
            continue
        if not hasattr(spin2, 'pos'):
            continue

        # Positional information flag.
        pos_info = True

        # Both single positions.
        if is_float(spin1.pos[0], raise_error=False) and is_float(spin2.pos[0], raise_error=False):
            # The vector.
            vector_list = [spin2.pos - spin1.pos]

        # A single and multiple position pair.
        elif is_float(spin1.pos[0], raise_error=False) or is_float(spin2.pos[0], raise_error=False):
            # The first spin has multiple positions.
            if is_float(spin2.pos[0], raise_error=False):
                vector_list = []
                for i in range(len(spin1.pos)):
                    vector_list.append(spin2.pos - spin1.pos[i])

            # The second spin has multiple positions.
            else:
                vector_list = []
                for i in range(len(spin2.pos)):
                    vector_list.append(spin2.pos[i] - spin1.pos)

        # Both spins have multiple positions.
        else:
            # Non-matching number of positions.
            if len(spin1.pos) != len(spin2.pos):
                raise RelaxError("The spin '%s' consists of %s positions whereas the spin '%s' consists of %s - these numbers must match." % (interatom.spin_id1, len(spin1.pos), interatom.spin_id1, len(spin1.pos)))

            # Calculate all vectors.
            vector_list = []
            for i in range(len(spin1.pos)):
                vector_list.append(spin2.pos[i] - spin1.pos[i])

        # Unit vectors.
        for i in range(len(vector_list)):
            # Normalisation factor.
            norm_factor = norm(vector_list[i])

            # Test for zero length.
            if norm_factor == 0.0:
                warn(RelaxZeroVectorWarning(spin_id1=interatom.spin_id1, spin_id2=interatom.spin_id2))

            # Calculate the normalised vector.
            else:
                vector_list[i] = vector_list[i] / norm_factor

        # Average.
        if ave:
            ave_vector = zeros(3, float64)
            for i in range(len(vector_list)):
                ave_vector = ave_vector + vector_list[i]
            vector_list = [ave_vector / len(vector_list)]

        # Convert to a single vector if needed.
        if len(vector_list) == 1:
            vector_list = vector_list[0]

        # Store the unit vector(s).
        setattr(interatom, 'vector', vector_list)

        # We have a vector!
        no_vectors = False

        # Print out.
        num = 1
        if not is_float(vector_list[0], raise_error=False):
            num = len(vector_list)
        plural = 's'
        if num == 1:
            plural = ''
        if spin1.name:
            spin1_str = spin1.name
        else:
            spin1_str = spin1.num
        if spin2.name:
            spin2_str = spin2.name
        else:
            spin2_str = spin2.num
        print("Calculated %s %s-%s unit vector%s between the spins '%s' and '%s'." % (num, spin1_str, spin2_str, plural, interatom.spin_id1, interatom.spin_id2))

    # Catch the problem of no positional information being present.
    if not pos_info:
        raise RelaxError("Positional information could not be found for any spins.")

    # Right, catch the problem of missing vectors to prevent massive user confusion!
    if no_vectors:
        raise RelaxError("No vectors could be extracted.")
