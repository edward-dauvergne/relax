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
"""Module for the manipulation of paramagnetic data."""

# Python module imports.
from numpy import array, float64, zeros

# relax module imports.
from lib.errors import RelaxError
from pipe_control import pipes
from pipe_control.pipes import check_pipe
from pipe_control.mol_res_spin import spin_loop


def centre(pos=None, atom_id=None, pipe=None, verbosity=1, fix=True, ave_pos=False, force=False):
    """Specify the atom in the loaded structure corresponding to the paramagnetic centre.

    @keyword pos:       The atomic position.  If set, the atom_id string will be ignored.
    @type pos:          list of float
    @keyword atom_id:   The atom identification string.
    @type atom_id:      str
    @keyword pipe:      An alternative data pipe to extract the paramagnetic centre from.
    @type pipe:         None or str
    @keyword verbosity: The amount of information to print out.  The bigger the number, the more information.
    @type verbosity:    int
    @keyword fix:       A flag which if False causes the paramagnetic centre to be optimised during minimisation.
    @type fix:          bool
    @keyword ave_pos:   A flag which if True causes the atomic positions from multiple models to be averaged.
    @type ave_pos:      bool
    @keyword force:     A flag which if True will cause the current paramagnetic centre to be overwritten.
    @type force:        bool
    """

    # The data pipe.
    if pipe == None:
        pipe = pipes.cdp_name()

    # Test the data pipe.
    check_pipe(pipe)

    # Get the data pipes.
    source_dp = pipes.get_pipe(pipe)

    # Test the centre has already been set.
    if pos != None and not force and hasattr(cdp, 'paramagnetic_centre'):
        raise RelaxError("The paramagnetic centre has already been set to the coordinates " + repr(cdp.paramagnetic_centre) + ".")

    # The fixed flag.
    if fix:
        print("The paramagnetic centre position will be fixed during optimisation.")
    else:
        print("The paramagnetic centre position will be optimised.")
    cdp.paramag_centre_fixed = fix

    # Position is supplied.
    if pos != None:
        centre = array(pos)
        num_pos = 1
        full_pos_list = []

    # Position from a loaded structure.
    elif atom_id:
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

    # No position - so simply exit the function.
    else:
        return

    # Averaging.
    centre = centre / float(num_pos)

    # Print out.
    if verbosity:
        print("Paramagnetic centres located at:")
        for pos in full_pos_list:
            print("    [%8.3f, %8.3f, %8.3f]" % (pos[0], pos[1], pos[2]))
        print("\nAverage paramagnetic centre located at:")
        print("    [%8.3f, %8.3f, %8.3f]" % (centre[0], centre[1], centre[2]))

    # Set the centre (place it into the current data pipe).
    if ave_pos:
        if verbosity:
            print("\nUsing the average paramagnetic position.")
        cdp.paramagnetic_centre = centre
    else:
        if verbosity:
            print("\nUsing all paramagnetic positions.")
        cdp.paramagnetic_centre = full_pos_list
