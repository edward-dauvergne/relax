###############################################################################
#                                                                             #
# Copyright (C) 2010-2011 Edward d'Auvergne                                   #
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
"""Module for functions relating to the paramagnetic centre."""

# Python imports.
from numpy.linalg import norm


def vectors_centre_per_state(atomic_pos, paramag_centre, unit_vector, r):
    """Calculate the electron spin to nuclear spin unit vectors and distances.

    This assumes that there is one paramagnetic centre per state of the system.


    @param atomic_pos:      The atomic positions in Angstrom.  The first index is the spins, the second is the structures, and the third is the atomic coordinates.
    @type atomic_pos:       numpy rank-3 array
    @param paramag_centre:  The paramagnetic centre position in Angstrom.
    @type paramag_centre:   numpy rank-2, Nx3 array
    @param unit_vector:     The structure to fill with the electron spin to nuclear spin unit vectors.
    @type unit_vector:      numpy rank-3 array
    @param r:               The structure to fill with the electron spin to nuclear spin distances.
    @type r:                numpy rank-2 array
    """

    # Loop over the spins.
    for i in range(len(atomic_pos)):
        # Loop over the states.
        for c in range(len(atomic_pos[i])):
            # The vector.
            vect = atomic_pos[i, c] - paramag_centre[c]

            # The length.
            r[i, c] = norm(vect)

            # The unit vector.
            unit_vector[i, c] = vect / r[i, c]

            # Convert the distances from Angstrom to meters.
            r[i, c] = r[i, c] * 1e-10


def vectors_single_centre(atomic_pos, paramag_centre, unit_vector, r):
    """Calculate the electron spin to nuclear spin unit vectors and distances.

    This assumes that there is only one paramagnetic centre for all states of the system.


    @param atomic_pos:      The atomic positions in Angstrom.  The first index is the spins, the second is the structures, and the third is the atomic coordinates.
    @type atomic_pos:       numpy rank-3 array
    @param paramag_centre:  The paramagnetic centre position in Angstrom.
    @type paramag_centre:   numpy rank-1, 3D array
    @param unit_vector:     The structure to fill with the electron spin to nuclear spin unit vectors.
    @type unit_vector:      numpy rank-3 array
    @param r:               The structure to fill with the electron spin to nuclear spin distances.
    @type r:                numpy rank-2 array
    """

    # Loop over the spins.
    for i in range(len(atomic_pos)):
        # Loop over the states.
        for c in range(len(atomic_pos[i])):
            # The vector.
            vect = atomic_pos[i, c] - paramag_centre

            # The length.
            r[i, c] = norm(vect)

            # The unit vector.
            unit_vector[i, c] = vect / r[i, c]

            # Convert the distances from Angstrom to meters.
            r[i, c] = r[i, c] * 1e-10
