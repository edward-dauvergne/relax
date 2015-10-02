# Script for optimising the free rotor frame order test model of CaM.

# Python module imports.
from numpy import array, cross, float64, zeros
from numpy.linalg import norm

# relax module imports.
from lib.frame_order.rotor_axis import create_rotor_axis_alpha
from lib.geometry.lines import closest_point_ax
from lib.geometry.coord_transform import spherical_to_cartesian
from lib.geometry.rotations import reverse_euler_zyz
from lib.geometry.vectors import vector_angle
from pipe_control.structure.mass import pipe_centre_of_mass


def alpha_angle(pivot=None, com=None, axis=None):
    """Calculate and return the rotor alpha angle."""

    # The CoM-pivot axis.
    com_piv = com - pivot
    com_piv /= norm(com_piv)

    # The mu_xy vector.
    z_axis = array([0, 0, 1], float64)
    mu_xy = cross(z_axis, com_piv)
    mu_xy /= norm(mu_xy)

    # The alpha angle.
    return vector_angle(mu_xy, axis, com_piv)


def shift_pivot(pivot_orig=None, com=None, axis=None):
    """Shift the pivot to the closest point on the rotor axis to the CoM.)"""

    # The closest point.
    pivot_new = closest_point_ax(line_pt=pivot_orig, axis=axis, point=com)

    # Printout.
    print("\n%-20s%s" % ("Original pivot:", pivot_orig))
    print("%-20s%s" % ("New pivot:", pivot_new))

    # Return the shifted pivot.
    return pivot_new


# The real parameter values.
AVE_POS_X, AVE_POS_Y, AVE_POS_Z = [ -20.859750185691549,   -2.450606987447843,   -2.191854570352916]
AVE_POS_BETA = 0.19740471457956135
AVE_POS_GAMMA = 4.6622313104265416
AXIS_THETA = 0.9600799785953431
AXIS_PHI = 4.0322755062196229

# Reconstruct the rotation axis.
AXIS = zeros(3, float64)
spherical_to_cartesian([1, AXIS_THETA, AXIS_PHI], AXIS)
print("Rotation axis: %s" % AXIS)

# Create the data pipe.
pipe.create(pipe_name='frame order', pipe_type='frame order')

# Read the structures.
structure.read_pdb('1J7O_1st_NH.pdb', dir='..', set_mol_name='N-dom')
structure.read_pdb('1J7P_1st_NH_rot.pdb', dir='..', set_mol_name='C-dom')

# Set up the 15N and 1H spins.
structure.load_spins(spin_id='@N', ave_pos=False)
structure.load_spins(spin_id='@H', ave_pos=False)
spin.isotope(isotope='15N', spin_id='@N')
spin.isotope(isotope='1H', spin_id='@H')

# Define the magnetic dipole-dipole relaxation interaction.
interatom.define(spin_id1='@N', spin_id2='@H', direct_bond=True)
interatom.set_dist(spin_id1='@N', spin_id2='@H', ave_dist=1.041 * 1e-10)
interatom.unit_vectors()

# Loop over the alignments.
ln = ['dy', 'tb', 'tm', 'er']
for i in range(len(ln)):
    # Load the RDCs.
    rdc.read(align_id=ln[i], file='rdc_%s.txt'%ln[i], spin_id1_col=1, spin_id2_col=2, data_col=3, error_col=4)

    # The PCS.
    pcs.read(align_id=ln[i], file='pcs_%s.txt'%ln[i], mol_name_col=1, res_num_col=2, spin_name_col=5, data_col=6, error_col=7)

    # The temperature and field strength.
    spectrometer.temperature(id=ln[i], temp=303)
    spectrometer.frequency(id=ln[i], frq=900e6)

# Load the N-domain tensors (the full tensors).
script('../tensors.py')

# Define the domains.
domain(id='N', spin_id=":1-78")
domain(id='C', spin_id=":80-148")

# The tensor domains and reductions.
full = ['Dy N-dom', 'Tb N-dom', 'Tm N-dom', 'Er N-dom']
red =  ['Dy C-dom', 'Tb C-dom', 'Tm C-dom', 'Er C-dom']
ids = ['dy', 'tb', 'tm', 'er']
for i in range(len(full)):
    # Initialise the reduced tensor.
    align_tensor.init(tensor=red[i], align_id=ids[i], params=(0, 0, 0, 0, 0))

    # Set the domain info.
    align_tensor.set_domain(tensor=full[i], domain='N')
    align_tensor.set_domain(tensor=red[i], domain='C')

    # Specify which tensor is reduced.
    align_tensor.reduction(full_tensor=full[i], red_tensor=red[i])

# Select the model.
frame_order.select_model('free rotor')

# Set the reference domain.
frame_order.ref_domain('N')

# Set the initial pivot point.
pivot = shift_pivot(pivot_orig=array([ 37.254, 0.5, 16.7465]), com=pipe_centre_of_mass(verbosity=0), axis=AXIS)
frame_order.pivot(pivot, fix=True)

# Set the paramagnetic centre.
paramag.centre(pos=[35.934, 12.194, -4.206])

# Check the minimum (at a very high quality to check that the chi-squared value is zero).
frame_order.num_int_pts(num=100000)
value.set(param='ave_pos_x', val=AVE_POS_X)
value.set(param='ave_pos_y', val=AVE_POS_Y)
value.set(param='ave_pos_z', val=AVE_POS_Z)
value.set(param='ave_pos_beta', val=AVE_POS_BETA)
value.set(param='ave_pos_gamma', val=AVE_POS_GAMMA)
value.set(param='axis_alpha', val=alpha_angle(pivot=pivot, com=pipe_centre_of_mass(verbosity=0), axis=AXIS))
minimise.calculate()

# Create the PDB representation of the true state.
frame_order.pdb_model(ave_pos='ave_pos_true', rep='frame_order_true', dist=None, compress_type=2, force=True)

# Grid search (low quality for speed).
frame_order.num_int_pts(num=100)
grid_search(inc=[None, None, None, None, None, 21])

# Iterative optimisation with increasing precision.
num_int_pts = [100, 1000, 10000, 50000]
func_tol = [1e-2, 1e-3, 5e-3, 1e-4]
for i in range(len(num_int_pts)):
    frame_order.num_int_pts(num=num_int_pts[i])
    minimise('simplex', func_tol=func_tol[i])

# Store the result.
frame_order.pdb_model(ave_pos='ave_pos_fixed_piv', rep='frame_order_fixed_piv', dist=None, compress_type=2, force=True)

# Optimise the pivot and model, again iterating with increasing precision.
frame_order.pivot(pivot, fix=False)
num_int_pts = [100, 1000, 10000, 50000]
func_tol = [1e-2, 1e-3, 5e-3, 1e-4]
for i in range(len(num_int_pts)):
    frame_order.num_int_pts(num=num_int_pts[i])
    minimise('simplex', func_tol=func_tol[i])

# The distance from the optimised pivot and the rotation axis.
opt_piv = array([cdp.pivot_x, cdp.pivot_y, cdp.pivot_z])
print("\n\nOptimised pivot displacement: %s" % norm(pivot - opt_piv))
pt = closest_point_ax(line_pt=pivot, axis=AXIS, point=opt_piv)
print("Distance from axis: %s\n" % norm(pt - opt_piv))

# Recreate the axis and compare to the original.
opt_axis = create_rotor_axis_alpha(alpha=cdp.axis_alpha, pivot=opt_piv, point=pipe_centre_of_mass(verbosity=0))
print("Original axis:   %s" % AXIS)
print("Optimised axis:  %s" % opt_axis)

# Test Monte Carlo simulations (at low quality for speed).
frame_order.num_int_pts(num=100)
monte_carlo.setup(number=5)
monte_carlo.create_data()
monte_carlo.initial_values()
minimise('simplex', func_tol=1e-2)
eliminate()
monte_carlo.error_analysis()

# Create the PDB representation.
frame_order.pdb_model(ave_pos='ave_pos', rep='frame_order', dist=None, compress_type=2, force=True)

# PyMOL.
pymol.view()
pymol.command('show spheres')
pymol.frame_order(ave_pos='ave_pos_true', rep='frame_order_true', dist=None)
pymol.frame_order(ave_pos='ave_pos_fixed_piv', rep='frame_order_fixed_piv', dist=None)
pymol.frame_order(ave_pos='ave_pos', rep='frame_order', dist=None)

# Save the state.
state.save('frame_order', force=True)
