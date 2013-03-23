# Script for checking the parametric restriction of the pseudo-ellipse to the free rotor isotropic cone frame order model.

# Python module imports.
from numpy import array, cross, float64, zeros
from numpy.linalg import norm
from os import sep

# relax module imports.
from data_store import Relax_data_store; ds = Relax_data_store()
from lib.geometry.rotations import R_to_euler_zyz
from status import Status; status = Status()


def get_angle(index, incs=None, deg=False):
    """Return the angle corresponding to the incrementation index."""

    # The angle of one increment.
    inc_angle = pi / incs

    # The angle of the increment.
    angle = inc_angle * (index+1)

    # Return.
    if deg:
        return angle / (2*pi) * 360
    else:
        return angle


# Init.
INC = 18

# Generate 3 orthogonal vectors.
vect_z = array([2, 1, 3], float64)
vect_x = cross(vect_z, array([1, 1, 1], float64))
vect_y = cross(vect_z, vect_x)

# Normalise.
vect_x = vect_x / norm(vect_x)
vect_y = vect_y / norm(vect_y)
vect_z = vect_z / norm(vect_z)

# Build the frame.
EIG_FRAME = zeros((3, 3), float64)
EIG_FRAME[:, 0] = vect_x
EIG_FRAME[:, 1] = vect_y
EIG_FRAME[:, 2] = vect_z
a, b, g = R_to_euler_zyz(EIG_FRAME)

# Load the tensors.
self._execute_uf(uf_name='script', file=status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'tensors'+sep+'iso_cone_free_rotor_axis2_1_3_tensors_beta78_75.py')

# Data stores.
ds.chi2 = []
ds.angles = []

# Loop over the cones.
for i in range(INC):
    # Switch data pipes.
    ds.angles.append(get_angle(i, incs=INC, deg=True))
    self._execute_uf(uf_name='pipe.switch', pipe_name='cone_%.1f_deg' % ds.angles[-1])

    # Data init.
    cdp.ave_pos_alpha  = cdp.ave_pos_alpha2  = 0.0
    cdp.ave_pos_beta   = cdp.ave_pos_beta2   = 78.75 / 360.0 * 2.0 * pi
    cdp.ave_pos_gamma  = cdp.ave_pos_gamma2  = 0.0
    cdp.eigen_alpha    = cdp.eigen_alpha2    = a
    cdp.eigen_beta     = cdp.eigen_beta2     = b
    cdp.eigen_gamma    = cdp.eigen_gamma2    = g
    cdp.cone_theta_x   = cdp.cone_theta_x2   = get_angle(i, incs=INC, deg=False)
    cdp.cone_theta_y   = cdp.cone_theta_y2   = get_angle(i, incs=INC, deg=False)
    cdp.cone_sigma_max = cdp.cone_sigma_max2 = pi

    # Select the Frame Order model.
    self._execute_uf(uf_name='frame_order.select_model', model='pseudo-ellipse')

    # Set the reference domain.
    self._execute_uf(uf_name='frame_order.ref_domain', ref='full')

    # Calculate the chi2.
    self._execute_uf(uf_name='calc')
    #cdp.chi2b = cdp.chi2
    #self._execute_uf(uf_name='minimise', min_algor='simplex')
    ds.chi2.append(cdp.chi2)

# Save the program state.
#self._execute_uf(uf_name='state.save', state="pseudo_ellipse_to_iso_cone_free_rotor", force=True)

print("\n\n")
for i in range(INC):
    print("Cone %3i deg, chi2: %s" % (ds.angles[i], ds.chi2[i]))
