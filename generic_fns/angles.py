###############################################################################
#                                                                             #
# Copyright (C) 2003-2012 Edward d'Auvergne                                   #
#                                                                             #
# This file is part of the program relax (http://www.nmr-relax.com).          #
#                                                                             #
# relax is free software; you can redistribute it and/or modify               #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation; either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# relax is distributed in the hope that it will be useful,                    #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with relax.  If not, see <http://www.gnu.org/licenses/>.              #
#                                                                             #
###############################################################################

# Module docstring.
"""Module for the manipulation of angular information."""

# Python module imports.
from math import acos, pi, sin
from numpy import dot
from warnings import warn

# relax module imports.
from generic_fns import pipes
from generic_fns.interatomic import interatomic_loop
from generic_fns.mol_res_spin import exists_mol_res_spin_data, generate_spin_id, spin_loop
from relax_errors import RelaxError, RelaxNoPdbError, RelaxNoSequenceError, RelaxNoTensorError
from relax_warnings import RelaxWarning


def angle_diff_frame():
    """Function for calculating the angle defining the XH vector in the diffusion frame."""

    # Test if the current data pipe exists.
    pipes.test()

    # Test if the PDB file has been loaded.
    if not hasattr(cdp, 'structure'):
        raise RelaxNoPdbError

    # Test if sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Test if the diffusion tensor data is loaded.
    if not hasattr(cdp, 'diff_tensor'):
        raise RelaxNoTensorError('diffusion')

    # Sphere.
    if cdp.diff_tensor.type == 'sphere':
        return

    # Spheroid.
    elif cdp.diff_tensor.type == 'spheroid':
        spheroid_frame()

    # Ellipsoid.
    elif cdp.diff_tensor.type == 'ellipsoid':
        raise RelaxError("No coded yet.")


def ellipsoid_frame():
    """Calculate the spherical angles of the bond vector in the ellipsoid frame."""

    # Get the unit vectors Dx, Dy, and Dz of the diffusion tensor axes.
    Dx, Dy, Dz = diffusion_tensor.unit_axes()

    # Spin loop.
    for spin, mol_name, res_num, res_name in spin_loop(full_info=True):
        # Test if the vector exists.
        if not hasattr(spin, 'xh_vect'):
            # Get the spin id string.
            spin_id = generate_spin_id(mol_name, res_num, res_name, spin.num, spin.name)

            # Throw a warning.
            warn(RelaxWarning("No angles could be calculated for the spin " + repr(spin_id) + "."))

            # Skip the spin.
            continue

        # dz and dx direction cosines.
        dz = dot(Dz, spin.xh_vect)
        dx = dot(Dx, spin.xh_vect)

        # Calculate the polar angle theta.
        spin.theta = acos(dz)

        # Calculate the azimuthal angle phi.
        spin.phi = acos(dx / sin(spin.theta))


def fold_spherical_angles(theta, phi, theta_lower=0, theta_upper=2*pi, theta_window=2*pi, phi_lower=0, phi_upper=2*pi, phi_window=2*pi):
    """Fold the spherical angles taking symmetry into account.

    The angles will be folded between::

        0 <= theta <= pi,
        0 <= phi <= 2*pi,

    @param theta:           The azimuthal angle.
    @type theta:            float
    @param phi:             The polar angle.
    @type phi:              float
    @param theta_lower:     The theta angle lower bound (defaults to 0).
    @type theta_lower:      float
    @param theta_upper:     The theta angle upper bound (defaults to 2*pi).
    @type theta_upper:      float
    @param theta_window:    The size of the theta angle window where symmetry exists (defaults to 2*pi).
    @type theta_window:     float
    @param phi_lower:       The phi angle lower bound (defaults to 0).
    @type phi_lower:        float
    @param phi_upper:       The phi angle upper bound (defaults to 2*pi).
    @type phi_upper:        float
    @param phi_window:      The size of the phi angle window where symmetry exists (defaults to 2*pi).
    @type phi_window:       float
    @return:                The folded angles, theta and phi.
    @rtype:                 float
    """

    # Check the bounds and window.
    if theta_window - (theta_upper - theta_lower) > 1e-7:
        raise RelaxError, "The theta angle lower and upper bounds [%s, %s] do not match the window size of %s." % (theta_lower, theta_upper, theta_window)
    if phi_window - (phi_upper - phi_lower) > 1e-7:
        raise RelaxError, "The phi angle lower and upper bounds [%s, %s] do not match the window size of %s." % (phi_lower, phi_upper, phi_window)

    # First wrap the angles.
    theta = wrap_angles(theta, theta_lower, theta_upper, theta_window)
    phi = wrap_angles(phi, phi_lower, phi_upper, phi_window)

    # Then remove the symmetry to the lower half of phi.
    if phi >= phi_upper - phi_window/2.0:
        theta = pi - theta
        phi = phi - pi

    # Wrap again if necessary.
    theta = wrap_angles(theta, theta_lower, theta_upper, theta_window)
    phi = wrap_angles(phi, phi_lower, phi_upper, phi_window)

    # Return the folded angles.
    return theta, phi


def spheroid_frame():
    """Function for calculating the angle alpha of the XH vector within the spheroid frame."""

    # Loop over the interatomic info.
    for interatom in interatomic_loop():
        # Test if the vector exists.
        if not hasattr(interatom, 'vector'):
            # Throw a warning.
            warn(RelaxWarning("No angles could be calculated for the spin pair '%s' and '%s'." % (interatom.spin_id1, interatom.spin_id2)))

            # Skip the container.
            continue

        # Calculate alpha.
        interatom.alpha = acos(dot(cdp.diff_tensor.Dpar_unit, interatom.vector))


def wrap_angles(angle, lower, upper, window=2*pi):
    """Convert the given angle to be between the lower and upper values.

    @param angle:   The starting angle.
    @type angle:    float
    @param lower:   The lower bound.
    @type lower:    float
    @param upper:   The upper bound.
    @type upper:    float
    @param window:  The size of the window where symmetry exists (defaults to 2pi).
    @type window:   float
    @return:        The wrapped angle.
    @rtype:         float
    """

    # Check the bounds and window.
    if window - (upper - lower) > 1e-7:
        raise RelaxError, "The lower and upper bounds [%s, %s] do not match the window size of %s." % (lower, upper, window)

    # Keep wrapping until the angle is within the limits.
    while True:
        # The angle is too big.
        if angle > upper:
            angle = angle - window

        # The angle is too small.
        elif angle < lower:
            angle = angle + window

        # Inside the window, so stop wrapping.
        else:
            break

    # Return the wrapped angle.
    return angle
