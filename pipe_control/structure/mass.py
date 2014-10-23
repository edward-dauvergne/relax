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

# Python module imports.
from warnings import warn

# relax module imports.
from lib.errors import RelaxNoPdbError
from lib.structure.mass import centre_of_mass
from lib.warnings import RelaxWarning


def pipe_centre_of_mass(atom_id=None, model=None, return_mass=False, verbosity=1):
    """Calculate and return the centre of mass of the structures in the current data pipe.

    @keyword atom_id:       The molecule, residue, and atom identifier string.  Only atoms matching this selection will be used.
    @type atom_id:          str or None
    @keyword model:         Only use a specific model.
    @type model:            int or None
    @keyword return_mass:   A flag which if False will cause only the centre of mass to be returned, but if True will cause the centre of mass and the mass itself to be returned as a tuple.
    @type return_mass:      bool
    @keyword verbosity:     The amount of text to print out.  0 results in no printouts, 1 the full amount.
    @type verbosity:        int
    @return:                The centre of mass vector, and additionally the mass.
    @rtype:                 list of 3 floats (or tuple of a list of 3 floats and one float)
    """

    # Test if a structure has been loaded.
    if not hasattr(cdp, 'structure') or cdp.structure.num_models() == 0:
        raise RelaxNoPdbError

    # The selection object.
    selection = cdp.structure.selection(atom_id=atom_id)

    # Loop over all atoms.
    coord = []
    element_list = []
    for mol_name, res_num, res_name, atom_num, atom_name, element, pos in cdp.structure.atom_loop(selection=selection, model_num=model, mol_name_flag=True, res_num_flag=True, res_name_flag=True, atom_num_flag=True, atom_name_flag=True, element_flag=True, pos_flag=True, ave=True):
        # Initialise the spin 
        id = ''

        # Get the corresponding molecule container.
        if mol_name != None:
            id = id + '#' + mol_name

        # Get the corresponding residue container.
        if res_num != None:
            id = id + ':' + repr(res_num)

        # Get the corresponding spin container.
        if atom_num != None:
            id = id + '@' + repr(atom_num)

        # No element?
        if element == None:
            warn(RelaxWarning("Skipping the atom '%s' as the element type cannot be determined." % id))
            continue

        # Store the position and element.
        coord.append(pos)
        element_list.append(element)

    # Calculate the CoM.
    com, mass = centre_of_mass(pos=coord, elements=element_list, verbosity=verbosity)

    # Return the centre of mass.
    if return_mass:
        return com, mass
    else:
        return com
