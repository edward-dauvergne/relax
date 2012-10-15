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
"""Module for the support of diffusion tensors."""

# Python module imports.
from copy import deepcopy
from math import cos, pi, sin
from numpy import cross, float64, int32, ones, transpose, zeros
from numpy.linalg import norm, svd
from re import search
import string

# relax module imports.
from data.diff_tensor import DiffTensorData
from generic_fns import pipes
from generic_fns.angles import fold_spherical_angles, wrap_angles
from generic_fns.interatomic import return_interatom_list
from generic_fns.mol_res_spin import get_molecule_names, return_spin, spin_loop
from maths_fns.coord_transform import cartesian_to_spherical
from maths_fns.rotation_matrix import R_to_euler_zyz
from physical_constants import element_from_isotope, number_from_isotope
from relax_errors import RelaxError, RelaxNoTensorError, RelaxStrError, RelaxTensorError, RelaxUnknownParamCombError, RelaxUnknownParamError
from user_functions.data import Uf_tables; uf_tables = Uf_tables()
from user_functions.objects import Desc_container


def bmrb_read(star):
    """Read the relaxation data from the NMR-STAR dictionary object.

    @param star:    The NMR-STAR dictionary object.
    @type star:     NMR_STAR instance
    """

    # Get the diffusion tensor data.
    found = 0
    for data in star.tensor.loop():
        # No data.
        if data == None:
            continue

        # Not a diffusion tensor.
        if data['tensor_type'] != 'diffusion':
            continue

        # Found.
        found = found + 1

    # No diffusion tensor data.
    if not found:
        return

    # Check.
    if found != 1:
        raise RelaxError("More than one diffusion tensor found.")

    # Rebuild the tensor.
    tensor = zeros((3, 3), float64)
    tensor[0, 0] = data['tensor_11'][0]
    tensor[0, 1] = data['tensor_12'][0]
    tensor[0, 2] = data['tensor_13'][0]
    tensor[1, 0] = data['tensor_21'][0]
    tensor[1, 1] = data['tensor_22'][0]
    tensor[1, 2] = data['tensor_23'][0]
    tensor[2, 0] = data['tensor_31'][0]
    tensor[2, 1] = data['tensor_32'][0]
    tensor[2, 2] = data['tensor_33'][0]

    # Eigenvalues.
    Di, R, alpha, beta, gamma = tensor_eigen_system(tensor)

    # X-Y eigenvalue comparison.
    xy_match = False
    epsilon = 1e-1
    if abs(Di[0] - Di[1]) < epsilon:
        xy_match = True

    # Y-Z eigenvalue comparison.
    yz_match = False
    if abs(Di[1] - Di[2]) < epsilon:
        yz_match = True

    # Determine the tensor type.
    if xy_match and yz_match:
        shape = ['sphere']
    elif xy_match:
        shape = ['spheroid', 'prolate spheroid']
        type = 'prolate'
        Dpar = Di[2]
        Dper = Di[0]
    elif yz_match:
        shape = ['spheroid', 'oblate spheroid']
        type = 'oblate'
        Dpar = Di[0]
        Dper = Di[2]
    else:
        shape = ['ellipsoid']

    # Check the shape.
    if data['geometric_shape'] not in shape:
        raise RelaxError("The tensor with eigenvalues %s does not match the %s geometric shape." % (Di, shape[0]))

    # Add the diff_tensor object to the data pipe.
    cdp.diff_tensor = DiffTensorData()

    # Set the fixed flag.
    cdp.diff_tensor.set_fixed(True)

    # Sphere.
    if data['geometric_shape'] == 'sphere':
        sphere(params=Di[0], d_scale=1.0, param_types=1)

    # Spheroid.
    elif data['geometric_shape'] in ['spheroid', 'oblate spheroid', 'prolate spheroid']:
        # The spherical angles.
        theta = data['axial_sym_axis_polar_angle'][0]
        phi = data['axial_sym_axis_azimuthal_angle'][0]

        # Set up the tensor.
        spheroid(params=(Dpar, Dper, theta, phi), d_scale=1.0, param_types=3, spheroid_type=type)

    # Ellipsoid.
    elif data['geometric_shape'] == 'ellipsoid':
        ellipsoid(params=(Di[0], Di[1], Di[2], alpha, beta, gamma), d_scale=1.0, param_types=3)


def bmrb_write(star):
    """Generate the diffusion tensor saveframes for the NMR-STAR dictionary object.

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

    # Store the spin specific data in lists for later use.
    for spin, mol_name, res_num, res_name, spin_id in spin_loop(full_info=True, return_id=True):
        # Check the data for None (not allowed in BMRB!).
        if res_num == None:
            raise RelaxError("For the BMRB, the residue of spin '%s' must be numbered." % spin_id)
        if res_name == None:
            raise RelaxError("For the BMRB, the residue of spin '%s' must be named." % spin_id)
        if spin.name == None:
            raise RelaxError("For the BMRB, the spin '%s' must be named." % spin_id)
        if not hasattr(spin, 'isotope') or spin.isotope == None:
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

    # The tensor geometric shape.
    geometric_shape = cdp.diff_tensor.type
    if geometric_shape == 'spheroid':
        geometric_shape = "%s %s" % (cdp.diff_tensor.spheroid_type, geometric_shape)

    # The tensor symmetry.
    shapes = ['sphere', 'oblate spheroid', 'prolate spheroid', 'ellipsoid']
    sym = ['isotropic', 'axial symmetry', 'axial symmetry', 'rhombic']
    for i in range(len(shapes)):
        if geometric_shape == shapes[i]:
            tensor_symmetry = sym[i]

    # Axial symmetry axis.
    theta = None
    phi = None
    if tensor_symmetry == 'axial symmetry':
        theta = cdp.diff_tensor.theta
        phi = cdp.diff_tensor.phi

    # Euler angles.
    alpha, beta, gamma = None, None, None
    if tensor_symmetry == 'rhombic':
        alpha = cdp.diff_tensor.alpha
        beta =  cdp.diff_tensor.beta
        gamma = cdp.diff_tensor.gamma

    # The tensor eigenvalues.
    Diso = cdp.diff_tensor.Diso
    Da = None
    Dr = None
    if tensor_symmetry == 'axial symmetry':
        Da = cdp.diff_tensor.Da
    elif tensor_symmetry == 'rhombic':
        Dr = cdp.diff_tensor.Dr

    # The full tensor.
    tensor_11 = cdp.diff_tensor.tensor[0, 0]
    tensor_12 = cdp.diff_tensor.tensor[0, 1]
    tensor_13 = cdp.diff_tensor.tensor[0, 2]
    tensor_21 = cdp.diff_tensor.tensor[1, 0]
    tensor_22 = cdp.diff_tensor.tensor[1, 1]
    tensor_23 = cdp.diff_tensor.tensor[1, 2]
    tensor_31 = cdp.diff_tensor.tensor[2, 0]
    tensor_32 = cdp.diff_tensor.tensor[2, 1]
    tensor_33 = cdp.diff_tensor.tensor[2, 2]


    # Add the diffusion tensor.
    star.tensor.add(tensor_type='diffusion', euler_type='zyz', geometric_shape=geometric_shape, tensor_symmetry=tensor_symmetry, matrix_val_units='s-1', angle_units='rad', iso_val_formula='Diso = 1/(6.tm)', aniso_val_formula='Da = Dpar - Dper', rhomb_val_formula='Dr = (Dy - Dx)/2Da', entity_ids=entity_ids, res_nums=res_num_list, res_names=res_name_list, atom_names=atom_name_list, atom_types=element_list, isotope=isotope_list, axial_sym_axis_polar_angle=theta, axial_sym_axis_azimuthal_angle=phi, iso_val=Diso, aniso_val=Da, rhombic_val=Dr, euler_alpha=alpha, euler_beta=beta, euler_gamma=gamma, tensor_11=tensor_11, tensor_12=tensor_12, tensor_13=tensor_13, tensor_21=tensor_21, tensor_22=tensor_22, tensor_23=tensor_23, tensor_31=tensor_31, tensor_32=tensor_32, tensor_33=tensor_33)



def copy(pipe_from=None, pipe_to=None):
    """Function for copying diffusion tensor data from one data pipe to another.

    @param pipe_from:   The data pipe to copy the diffusion tensor data from.  This defaults to the
                        current data pipe.
    @type pipe_from:    str
    @param pipe_to:     The data pipe to copy the diffusion tensor data to.  This defaults to the
                        current data pipe.
    @type pipe_to:      str
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

    # Test if pipe_from contains diffusion tensor data.
    if not diff_data_exists(pipe_from):
        raise RelaxNoTensorError('diffusion')

    # Test if pipe_to contains diffusion tensor data.
    if diff_data_exists(pipe_to):
        raise RelaxTensorError('diffusion')

    # Copy the data.
    dp_to.diff_tensor = deepcopy(dp_from.diff_tensor)


def data_names():
    """Function for returning a list of names of data structures associated with the sequence."""

    names = [ 'diff_type',
              'diff_params' ]

    return names


def default_value(param):
    """Return the default values for the diffusion tensor parameters.

    @param param:   The name of the parameter.
    @type param:    str
    @return:        The default value.
    @rtype:         float
    """

    # tm.
    if param == 'tm':
        return 10.0 * 1e-9

    # Diso, Dx, Dy, Dz, Dpar, Dper.
    elif param == 'Diso' or param == 'Dx' or param == 'Dy' or param == 'Dz' or param == 'Dpar' or param == 'Dper':
        return 1.666 * 1e7

    # Da, Dr.
    elif param == 'Da' or param == 'Dr':
        return 0.0

    # Dratio.
    elif param == 'Dratio':
        return 1.0

    # All angles.
    elif param == 'alpha' or param == 'beta' or param == 'gamma' or param == 'theta' or param == 'phi':
        return 0.0

# User function documentation.
__default_value_doc__ = Desc_container("Diffusion tensor parameter default values")
table = uf_tables.add_table(label="table: diff default values", caption="Diffusion tensor parameter default values.")
table.add_headings(["Data type", "Object name", "Value"])
table.add_row(["tm", "'tm'", "10 * 1e-9"])
table.add_row(["Diso", "'Diso'", "1.666 * 1e7"])
table.add_row(["Da", "'Da'", "0.0"])
table.add_row(["Dr", "'Dr'", "0.0"])
table.add_row(["Dx", "'Dx'", "1.666 * 1e7"])
table.add_row(["Dy", "'Dy'", "1.666 * 1e7"])
table.add_row(["Dz", "'Dz'", "1.666 * 1e7"])
table.add_row(["Dpar", "'Dpar'", "1.666 * 1e7"])
table.add_row(["Dper", "'Dper'", "1.666 * 1e7"])
table.add_row(["Dratio", "'Dratio'", "1.0"])
table.add_row(["alpha", "'alpha'", "0.0"])
table.add_row(["beta", "'beta'", "0.0"])
table.add_row(["gamma", "'gamma'", "0.0"])
table.add_row(["theta", "'theta'", "0.0"])
table.add_row(["phi", "'phi'", "0.0"])
__default_value_doc__.add_table(table.label)


def delete():
    """Function for deleting diffusion tensor data."""

    # Test if the current data pipe exists.
    pipes.test()

    # Test if diffusion tensor data exists.
    if not diff_data_exists():
        raise RelaxNoTensorError('diffusion')

    # Delete the diffusion data.
    del(cdp.diff_tensor)


def diff_data_exists(pipe=None):
    """Function for determining if diffusion data exists in the current data pipe.

    @param pipe:    The data pipe to search for data in.
    @type pipe:     str
    @return:        The answer to the question.
    @rtype:         bool
    """

    # The data pipe to check.
    if pipe == None:
        pipe = pipes.cdp_name()

    # Get the data pipe.
    dp = pipes.get_pipe(pipe)

    # Test if the data structure exists.
    if hasattr(dp, 'diff_tensor'):
        return True
    else:
        return False


def display():
    """Function for displaying the diffusion tensor."""

    # Test if the current data pipe exists.
    pipes.test()

    # Test if diffusion tensor data exists.
    if not diff_data_exists():
        raise RelaxNoTensorError('diffusion')

    # Spherical diffusion.
    if cdp.diff_tensor.type == 'sphere':
        # Tensor type.
        print("Type:  Spherical diffusion")

        # Parameters.
        print("\nParameters {tm}.")
        print(("tm (s):  " + repr(cdp.diff_tensor.tm)))

        # Alternate parameters.
        print("\nAlternate parameters {Diso}.")
        print(("Diso (1/s):  " + repr(cdp.diff_tensor.Diso)))

        # Fixed flag.
        print(("\nFixed:  " + repr(cdp.diff_tensor.fixed)))

    # Spheroidal diffusion.
    elif cdp.diff_tensor.type == 'spheroid':
        # Tensor type.
        print("Type:  Spheroidal diffusion")

        # Parameters.
        print("\nParameters {tm, Da, theta, phi}.")
        print(("tm (s):  " + repr(cdp.diff_tensor.tm)))
        print(("Da (1/s):  " + repr(cdp.diff_tensor.Da)))
        print(("theta (rad):  " + repr(cdp.diff_tensor.theta)))
        print(("phi (rad):  " + repr(cdp.diff_tensor.phi)))

        # Alternate parameters.
        print("\nAlternate parameters {Diso, Da, theta, phi}.")
        print(("Diso (1/s):  " + repr(cdp.diff_tensor.Diso)))
        print(("Da (1/s):  " + repr(cdp.diff_tensor.Da)))
        print(("theta (rad):  " + repr(cdp.diff_tensor.theta)))
        print(("phi (rad):  " + repr(cdp.diff_tensor.phi)))

        # Alternate parameters.
        print("\nAlternate parameters {Dpar, Dper, theta, phi}.")
        print(("Dpar (1/s):  " + repr(cdp.diff_tensor.Dpar)))
        print(("Dper (1/s):  " + repr(cdp.diff_tensor.Dper)))
        print(("theta (rad):  " + repr(cdp.diff_tensor.theta)))
        print(("phi (rad):  " + repr(cdp.diff_tensor.phi)))

        # Alternate parameters.
        print("\nAlternate parameters {tm, Dratio, theta, phi}.")
        print(("tm (s):  " + repr(cdp.diff_tensor.tm)))
        print(("Dratio:  " + repr(cdp.diff_tensor.Dratio)))
        print(("theta (rad):  " + repr(cdp.diff_tensor.theta)))
        print(("phi (rad):  " + repr(cdp.diff_tensor.phi)))

        # Fixed flag.
        print(("\nFixed:  " + repr(cdp.diff_tensor.fixed)))

    # Ellipsoidal diffusion.
    elif cdp.diff_tensor.type == 'ellipsoid':
        # Tensor type.
        print("Type:  Ellipsoidal diffusion")

        # Parameters.
        print("\nParameters {tm, Da, Dr, alpha, beta, gamma}.")
        print(("tm (s):  " + repr(cdp.diff_tensor.tm)))
        print(("Da (1/s):  " + repr(cdp.diff_tensor.Da)))
        print(("Dr:  " + repr(cdp.diff_tensor.Dr)))
        print(("alpha (rad):  " + repr(cdp.diff_tensor.alpha)))
        print(("beta (rad):  " + repr(cdp.diff_tensor.beta)))
        print(("gamma (rad):  " + repr(cdp.diff_tensor.gamma)))

        # Alternate parameters.
        print("\nAlternate parameters {Diso, Da, Dr, alpha, beta, gamma}.")
        print(("Diso (1/s):  " + repr(cdp.diff_tensor.Diso)))
        print(("Da (1/s):  " + repr(cdp.diff_tensor.Da)))
        print(("Dr:  " + repr(cdp.diff_tensor.Dr)))
        print(("alpha (rad):  " + repr(cdp.diff_tensor.alpha)))
        print(("beta (rad):  " + repr(cdp.diff_tensor.beta)))
        print(("gamma (rad):  " + repr(cdp.diff_tensor.gamma)))

        # Alternate parameters.
        print("\nAlternate parameters {Dx, Dy, Dz, alpha, beta, gamma}.")
        print(("Dx (1/s):  " + repr(cdp.diff_tensor.Dx)))
        print(("Dy (1/s):  " + repr(cdp.diff_tensor.Dy)))
        print(("Dz (1/s):  " + repr(cdp.diff_tensor.Dz)))
        print(("alpha (rad):  " + repr(cdp.diff_tensor.alpha)))
        print(("beta (rad):  " + repr(cdp.diff_tensor.beta)))
        print(("gamma (rad):  " + repr(cdp.diff_tensor.gamma)))

        # Fixed flag.
        print(("\nFixed:  " + repr(cdp.diff_tensor.fixed)))


def ellipsoid(params=None, time_scale=None, d_scale=None, angle_units=None, param_types=None):
    """Function for setting up a ellipsoidal diffusion tensor.
    
    @param params:          The diffusion tensor parameter.
    @type params:           float
    @param time_scale:      The correlation time scaling value.
    @type time_scale:       float
    @param d_scale:         The diffusion tensor eigenvalue scaling value.
    @type d_scale:          float
    @param angle_units:     The units for the angle parameters which can be either 'deg' or 'rad'.
    @type angle_units:      str
    @param param_types:     The type of parameters supplied.  These correspond to 0: {tm, Da, theta,
                            phi}, 1: {Diso, Da, theta, phi}, 2: {tm, Dratio, theta, phi}, 3:  {Dpar,
                            Dper, theta, phi}, 4: {Diso, Dratio, theta, phi}.
    @type param_types:      int
    """

    # The diffusion type.
    cdp.diff_tensor.set_type('ellipsoid')

    # (tm, Da, Dr, alpha, beta, gamma).
    if param_types == 0:
        # Unpack the tuple.
        tm, Da, Dr, alpha, beta, gamma = params

        # Scaling.
        tm = tm * time_scale
        Da = Da * d_scale

        # Set the parameters.
        set(value=[tm, Da, Dr], param=['tm', 'Da', 'Dr'])

    # (Diso, Da, Dr, alpha, beta, gamma).
    elif param_types == 1:
        # Unpack the tuple.
        Diso, Da, Dr, alpha, beta, gamma = params

        # Scaling.
        Diso = Diso * d_scale
        Da = Da * d_scale

        # Set the parameters.
        set(value=[Diso, Da, Dr], param=['Diso', 'Da', 'Dr'])

    # (Dx, Dy, Dz, alpha, beta, gamma).
    elif param_types == 2:
        # Unpack the tuple.
        Dx, Dy, Dz, alpha, beta, gamma = params

        # Scaling.
        Dx = Dx * d_scale
        Dy = Dy * d_scale
        Dz = Dz * d_scale

        # Set the parameters.
        set(value=[Dx, Dy, Dz], param=['Dx', 'Dy', 'Dz'])

    # (Dxx, Dyy, Dzz, Dxy, Dxz, Dyz).
    elif param_types == 3:
        # Unpack the tuple.
        Dxx, Dyy, Dzz, Dxy, Dxz, Dyz = params

        # Build the tensor.
        tensor = zeros((3, 3), float64)
        tensor[0, 0] = Dxx
        tensor[1, 1] = Dyy
        tensor[2, 2] = Dzz
        tensor[0, 1] = tensor[1, 0] = Dxy
        tensor[0, 2] = tensor[2, 0] = Dxz
        tensor[1, 2] = tensor[2, 1] = Dyz

        # Scaling.
        tensor = tensor * d_scale

        # Eigenvalues.
        Di, R, alpha, beta, gamma = tensor_eigen_system(tensor)

        # Set the parameters.
        set(value=[Di[0], Di[1], Di[2]], param=['Dx', 'Dy', 'Dz'])

        # Change the angular units.
        angle_units = 'rad'

    # Unknown parameter combination.
    else:
        raise RelaxUnknownParamCombError('param_types', param_types)

    # Convert the angles to radians.
    if angle_units == 'deg':
        print("Converting the angles from degrees to radian units.")
        alpha = (alpha / 360.0) * 2.0 * pi
        beta = (beta / 360.0) * 2.0 * pi
        gamma = (gamma / 360.0) * 2.0 * pi

    # Set the orientational parameters.
    set(value=[alpha, beta, gamma], param=['alpha', 'beta', 'gamma'])


def fold_angles(sim_index=None):
    """Wrap the Euler or spherical angles and remove the glide reflection and translational symmetries.

    Wrap the angles such that::

        0 <= theta <= pi,
        0 <= phi <= 2pi,

    and::

        0 <= alpha <= 2pi,
        0 <= beta <= pi,
        0 <= gamma <= 2pi.


    For the simulated values, the angles are wrapped as::

        theta - pi/2 <= theta_sim <= theta + pi/2
        phi - pi <= phi_sim <= phi + pi

    and::

        alpha - pi <= alpha_sim <= alpha + pi
        beta - pi/2 <= beta_sim <= beta + pi/2
        gamma - pi <= gamma_sim <= gamma + pi


    @param sim_index:   The simulation index.  If set to None then the actual values will be folded
                        rather than the simulation values.
    @type sim_index:    int or None
    """


    # Wrap the angles.
    ##################

    # Spheroid.
    if cdp.diff_tensor.type == 'spheroid':
        # Get the current angles.
        theta = cdp.diff_tensor.theta
        phi = cdp.diff_tensor.phi

        # Simulated values.
        if sim_index != None:
            theta_sim = cdp.diff_tensor.theta_sim[sim_index]
            phi_sim   = cdp.diff_tensor.phi_sim[sim_index]

        # Normal value.
        if sim_index == None:
            cdp.diff_tensor.set(param='theta', value=wrap_angles(theta, 0.0, 2.0*pi))
            cdp.diff_tensor.set(param='phi', value=wrap_angles(phi, 0.0, 2.0*pi))

        # Simulated theta and phi values.
        else:
            cdp.diff_tensor.set(param='theta', value=wrap_angles(theta_sim, theta - pi, theta + pi), category='sim', sim_index=sim_index)
            cdp.diff_tensor.set(param='phi', value=wrap_angles(phi_sim, phi - pi, phi + pi), category='sim', sim_index=sim_index)

    # Ellipsoid.
    elif cdp.diff_tensor.type == 'ellipsoid':
        # Get the current angles.
        alpha = cdp.diff_tensor.alpha
        beta  = cdp.diff_tensor.beta
        gamma = cdp.diff_tensor.gamma

        # Simulated values.
        if sim_index != None:
            alpha_sim = cdp.diff_tensor.alpha_sim[sim_index]
            beta_sim  = cdp.diff_tensor.beta_sim[sim_index]
            gamma_sim = cdp.diff_tensor.gamma_sim[sim_index]

        # Normal value.
        if sim_index == None:
            cdp.diff_tensor.set(param='alpha', value=wrap_angles(alpha, 0.0, 2.0*pi))
            cdp.diff_tensor.set(param='beta', value= wrap_angles(beta, 0.0, 2.0*pi))
            cdp.diff_tensor.set(param='gamma', value=wrap_angles(gamma, 0.0, 2.0*pi))

        # Simulated alpha, beta, and gamma values.
        else:
            cdp.diff_tensor.set(param='alpha', value=wrap_angles(alpha_sim, alpha - pi, alpha + pi), category='sim', sim_index=sim_index)
            cdp.diff_tensor.set(param='beta', value= wrap_angles(beta_sim, beta - pi, beta + pi), category='sim', sim_index=sim_index)
            cdp.diff_tensor.set(param='gamma', value=wrap_angles(gamma_sim, gamma - pi, gamma + pi), category='sim', sim_index=sim_index)


    # Remove the glide reflection and translational symmetries.
    ###########################################################

    # Spheroid.
    if cdp.diff_tensor.type == 'spheroid':
        # Normal value.
        if sim_index == None:
            # Fold phi inside 0 and pi.
            if cdp.diff_tensor.phi >= pi:
                theta, phi = fold_spherical_angles(cdp.diff_tensor.theta, cdp.diff_tensor.phi)
                cdp.diff_tensor.set(param='theta', value=theta)
                cdp.diff_tensor.set(param='phi', value=phi)

        # Simulated theta and phi values.
        else:
            # Fold phi_sim inside phi-pi/2 and phi+pi/2.
            if cdp.diff_tensor.phi_sim[sim_index] >= cdp.diff_tensor.phi + pi/2.0:
                cdp.diff_tensor.set(param='theta', value=pi - cdp.diff_tensor.theta_sim[sim_index], category='sim', sim_index=sim_index)
                cdp.diff_tensor.set(param='phi', value=cdp.diff_tensor.phi_sim[sim_index] - pi, category='sim', sim_index=sim_index)
            elif cdp.diff_tensor.phi_sim[sim_index] <= cdp.diff_tensor.phi - pi/2.0:
                cdp.diff_tensor.set(param='theta', value=pi - cdp.diff_tensor.theta_sim[sim_index], category='sim', sim_index=sim_index)
                cdp.diff_tensor.set(param='phi', value=cdp.diff_tensor.phi_sim[sim_index] + pi, category='sim', sim_index=sim_index)

    # Ellipsoid.
    elif cdp.diff_tensor.type == 'ellipsoid':
        # Normal value.
        if sim_index == None:
            # Fold alpha inside 0 and pi.
            if cdp.diff_tensor.alpha >= pi:
                cdp.diff_tensor.set(param='alpha', value=cdp.diff_tensor.alpha - pi)

            # Fold beta inside 0 and pi.
            if cdp.diff_tensor.beta >= pi:
                cdp.diff_tensor.set(param='alpha', value=pi - cdp.diff_tensor.alpha)
                cdp.diff_tensor.set(param='beta', value=cdp.diff_tensor.beta - pi)

            # Fold gamma inside 0 and pi.
            if cdp.diff_tensor.gamma >= pi:
                cdp.diff_tensor.set(param='alpha', value=pi - cdp.diff_tensor.alpha)
                cdp.diff_tensor.set(param='beta', value=pi - cdp.diff_tensor.beta)
                cdp.diff_tensor.set(param='gamma', value=cdp.diff_tensor.gamma - pi)

        # Simulated theta and phi values.
        else:
            # Fold alpha_sim inside alpha-pi/2 and alpha+pi/2.
            if cdp.diff_tensor.alpha_sim[sim_index] >= cdp.diff_tensor.alpha + pi/2.0:
                cdp.diff_tensor.set(param='alpha', value=cdp.diff_tensor.alpha_sim[sim_index] - pi, category='sim', sim_index=sim_index)
            elif cdp.diff_tensor.alpha_sim[sim_index] <= cdp.diff_tensor.alpha - pi/2.0:
                cdp.diff_tensor.set(param='alpha', value=cdp.diff_tensor.alpha_sim[sim_index] + pi, category='sim', sim_index=sim_index)

            # Fold beta_sim inside beta-pi/2 and beta+pi/2.
            if cdp.diff_tensor.beta_sim[sim_index] >= cdp.diff_tensor.beta + pi/2.0:
                cdp.diff_tensor.set(param='alpha', value=pi - cdp.diff_tensor.alpha_sim[sim_index], category='sim', sim_index=sim_index)
                cdp.diff_tensor.set(param='beta', value=cdp.diff_tensor.beta_sim[sim_index] - pi, category='sim', sim_index=sim_index)
            elif cdp.diff_tensor.beta_sim[sim_index] <= cdp.diff_tensor.beta - pi/2.0:
                cdp.diff_tensor.set(param='alpha', value=pi - cdp.diff_tensor.alpha_sim[sim_index], category='sim', sim_index=sim_index)
                cdp.diff_tensor.set(param='beta', value=cdp.diff_tensor.beta_sim[sim_index] + pi, category='sim', sim_index=sim_index)

            # Fold gamma_sim inside gamma-pi/2 and gamma+pi/2.
            if cdp.diff_tensor.gamma_sim[sim_index] >= cdp.diff_tensor.gamma + pi/2.0:
                cdp.diff_tensor.set(param='alpha', value=pi - cdp.diff_tensor.alpha_sim[sim_index], category='sim', sim_index=sim_index)
                cdp.diff_tensor.set(param='beta', value=pi - cdp.diff_tensor.beta_sim[sim_index], category='sim', sim_index=sim_index)
                cdp.diff_tensor.set(param='gamma', value=cdp.diff_tensor.gamma_sim[sim_index] - pi, category='sim', sim_index=sim_index)
            elif cdp.diff_tensor.gamma_sim[sim_index] <= cdp.diff_tensor.gamma - pi/2.0:
                cdp.diff_tensor.set(param='alpha', value=pi - cdp.diff_tensor.alpha_sim[sim_index], category='sim', sim_index=sim_index)
                cdp.diff_tensor.set(param='beta', value=pi - cdp.diff_tensor.beta_sim[sim_index], category='sim', sim_index=sim_index)
                cdp.diff_tensor.set(param='gamma', value=cdp.diff_tensor.gamma_sim[sim_index] + pi, category='sim', sim_index=sim_index)


def init(params=None, time_scale=1.0, d_scale=1.0, angle_units='deg', param_types=0, spheroid_type=None, fixed=1):
    """Function for initialising the diffusion tensor.

    @param params:          The diffusion tensor parameters.
    @type params:           float
    @param time_scale:      The correlation time scaling value.
    @type time_scale:       float
    @param d_scale:         The diffusion tensor eigenvalue scaling value.
    @type d_scale:          float
    @param angle_units:     The units for the angle parameters.
    @type angle_units:      str (either 'deg' or 'rad')
    @param param_types:     The type of parameters supplied.  For spherical diffusion, the flag
                            values correspond to 0: tm, 1: Diso.  For spheroidal diffusion, 0: {tm,
                            Da, theta, phi}, 1: {Diso, Da, theta, phi}, 2: {tm, Dratio, theta, phi},
                            3:  {Dpar, Dper, theta, phi}, 4: {Diso, Dratio, theta, phi}.  For
                            ellipsoidal diffusion, 0: {tm, Da, Dr, alpha, beta, gamma}, 1: {Diso,
                            Da, Dr, alpha, beta, gamma}, 2: {Dx, Dy, Dz, alpha, beta, gamma}.
    @type param_types:      int
    @param spheroid_type:   A string which, if supplied together with spheroid parameters, will
                            restrict the tensor to either being 'oblate' or 'prolate'.
    @type spheroid_type:    str
    @param fixed:           A flag specifying whether the diffusion tensor is fixed or can be
                            optimised.
    @type fixed:            bin
    """

    # Test if the current data pipe exists.
    pipes.test()

    # Test if diffusion tensor data already exists.
    if diff_data_exists():
        raise RelaxTensorError('diffusion')

    # Check the validity of the angle_units argument.
    valid_types = ['deg', 'rad']
    if not angle_units in valid_types:
        raise RelaxError("The diffusion tensor 'angle_units' argument " + repr(angle_units) + " should be either 'deg' or 'rad'.")

    # Add the diff_tensor object to the data pipe.
    cdp.diff_tensor = DiffTensorData()

    # Set the fixed flag.
    cdp.diff_tensor.set_fixed(fixed)

    # Spherical diffusion.
    if isinstance(params, float):
        num_params = 1
        sphere(params, time_scale, param_types)

    # Spheroidal diffusion.
    elif (isinstance(params, tuple) or isinstance(params, list)) and len(params) == 4:
        num_params = 4
        spheroid(params, time_scale, d_scale, angle_units, param_types, spheroid_type)

    # Ellipsoidal diffusion.
    elif (isinstance(params, tuple) or isinstance(params, list)) and len(params) == 6:
        num_params = 6
        ellipsoid(params, time_scale, d_scale, angle_units, param_types)

    # Unknown.
    else:
        raise RelaxError("The diffusion tensor parameters " + repr(params) + " are of an unknown type.")

    # Test the validity of the parameters.
    test_params(num_params)


def map_bounds(param, spin_id=None):
    """The function for creating bounds for the mapping function.

    @param param:       The name of the parameter to return the bounds for.
    @type param:        str
    @keyword spin_id:   The spin identification string.  This arg is unused.
    @type spin_id:      None or str
    @return:            The bounds for the parameter.
    @rtype:             list of len 2 of floats
    """

    # tm.
    if param == 'tm':
        return [0, 10.0 * 1e-9]

    # {Diso, Dx, Dy, Dz, Dpar, Dper}.
    if param == 'Diso' or param == 'Dx' or param == 'Dy' or param == 'Dz' or param == 'Dpar' or param == 'Dper':
        return [1e6, 1e7]

    # Da.
    if param == 'Da':
        return [-3.0/2.0 * 1e7, 3.0 * 1e7]

    # Dr.
    if param == 'Dr':
        return [0, 1]

    # Dratio.
    if param == 'Dratio':
        return [1.0/3.0, 3.0]

    # theta.
    if param == 'theta':
        return [0, pi]

    # phi.
    if param == 'phi':
        return [0, 2*pi]

    # alpha.
    if param == 'alpha':
        return [0, 2*pi]

    # beta.
    if param == 'beta':
        return [0, pi]

    # gamma.
    if param == 'gamma':
        return [0, 2*pi]


def map_labels(index, params, bounds, swap, inc):
    """Function for creating labels, tick locations, and tick values for an OpenDX map."""

    # Initialise.
    labels = "{"
    tick_locations = []
    tick_values = []
    n = len(params)
    axis_incs = 5
    loc_inc = inc / axis_incs

    # Increment over the model parameters.
    for i in range(n):
        # Parameter conversion factors.
        factor = return_conversion_factor(params[swap[i]])

        # Parameter units.
        units = return_units(params[swap[i]])

        # Labels.
        if units:
            labels = labels + "\"" + params[swap[i]] + " (" + units + ")\""
        else:
            labels = labels + "\"" + params[swap[i]] + "\""

        # Tick values.
        vals = bounds[swap[i], 0] / factor
        val_inc = (bounds[swap[i], 1] - bounds[swap[i], 0]) / (axis_incs * factor)

        if i < n - 1:
            labels = labels + " "
        else:
            labels = labels + "}"

        # Tick locations.
        string = "{"
        val = 0.0
        for j in range(axis_incs + 1):
            string = string + " " + repr(val)
            val = val + loc_inc
        string = string + " }"
        tick_locations.append(string)

        # Tick values.
        string = "{"
        for j in range(axis_incs + 1):
            string = string + "\"" + "%.2f" % vals + "\" "
            vals = vals + val_inc
        string = string + "}"
        tick_values.append(string)

    return labels, tick_locations, tick_values


def return_conversion_factor(param):
    """Function for returning the factor of conversion between different parameter units.

    For example, the internal representation of tm is in seconds, whereas the external
    representation is in nanoseconds, therefore this function will return 1e-9 for tm.


    @param param:       The name of the parameter to return the conversion factor for.
    @type param:        str
    @return:            The conversion factor.
    @rtype:             float
    """

    # Get the object name.
    object_name = return_data_name(param)

    # tm (nanoseconds).
    if object_name == 'tm':
        return 1e-9

    # Diso, Da, Dx, Dy, Dz, Dpar, Dper.
    if object_name in ['Diso', 'Da', 'Dx', 'Dy', 'Dz', 'Dpar', 'Dper']:
        return 1e6

    # Angles.
    if object_name in ['theta', 'phi', 'alpha', 'beta', 'gamma']:
        return (2.0*pi) / 360.0

    # No conversion factor.
    return 1.0


def return_data_name(name):
    """Return the parameter name.

    @param name:    The name of the parameter to return the name of.
    @type name:     str
    @return:        The parameter name.
    @rtype:         str
    """

    # Enforce that the name must be a string.
    if not isinstance(name, str):
        raise RelaxStrError('name', name)

    # Local tm.
    if search('^tm$', name):
        return 'tm'

    # Diso.
    if search('[Dd]iso', name):
        return 'Diso'

    # Da.
    if search('[Dd]a', name):
        return 'Da'

    # Dr.
    if search('[Dd]r$', name):
        return 'Dr'

    # Dx.
    if search('[Dd]x', name):
        return 'Dx'

    # Dy.
    if search('[Dd]y', name):
        return 'Dy'

    # Dz.
    if search('[Dd]z', name):
        return 'Dz'

    # Dpar.
    if search('[Dd]par', name):
        return 'Dpar'

    # Dper.
    if search('[Dd]per', name):
        return 'Dper'

    # Dratio.
    if search('[Dd]ratio', name):
        return 'Dratio'

    # alpha.
    if search('^a$', name) or search('alpha', name):
        return 'alpha'

    # beta.
    if search('^b$', name) or search('beta', name):
        return 'beta'

    # gamma.
    if search('^g$', name) or search('gamma', name):
        return 'gamma'

    # theta.
    if search('theta', name):
        return 'theta'

    # phi.
    if search('phi', name):
        return 'phi'

# User function documentation.
__return_data_name_doc__ = Desc_container("Diffusion tensor parameter string matching patterns")
table = uf_tables.add_table(label="table: diff data type patterns", caption="Diffusion tensor parameter string matching patterns.")
table.add_headings(["Data type", "Object name", "Patterns"])
table.add_row(["Global correlation time - tm", "'tm'", "'^tm$'"])
table.add_row(["Isotropic component of the diffusion tensor - Diso", "'Diso'", "'[Dd]iso'"])
table.add_row(["Anisotropic component of the diffusion tensor - Da", "'Da'", "'[Dd]a'"])
table.add_row(["Rhombic component of the diffusion tensor - Dr", "'Dr'", "'[Dd]r$'"])
table.add_row(["Eigenvalue associated with the x-axis of the diffusion tensor - Dx", "'Dx'", "'[Dd]x'"])
table.add_row(["Eigenvalue associated with the y-axis of the diffusion tensor - Dy", "'Dy'", "'[Dd]y'"])
table.add_row(["Eigenvalue associated with the z-axis of the diffusion tensor - Dz", "'Dz'", "'[Dd]z'"])
table.add_row(["Diffusion coefficient parallel to the major axis of  the spheroid diffusion tensor - Dpar", "'Dpar'", "'[Dd]par'"])
table.add_row(["Diffusion coefficient perpendicular to the major axis of the spheroid diffusion tensor - Dper", "'Dper'", "'[Dd]per'"])
table.add_row(["Ratio of the parallel and perpendicular components of the spheroid diffusion tensor - Dratio", "'Dratio'", "'[Dd]ratio'"])
table.add_row(["The first Euler angle of the ellipsoid diffusion tensor - alpha", "'alpha'", "'^a$' or 'alpha'"])
table.add_row(["The second Euler angle of the ellipsoid diffusion tensor - beta", "'beta'", "'^b$' or 'beta'"])
table.add_row(["The third Euler angle of the ellipsoid diffusion tensor - gamma", "'gamma'", "'^g$' or 'gamma'"])
table.add_row(["The polar angle defining the major axis of the spheroid diffusion tensor - theta", "'theta'", "'theta'"])
table.add_row(["The azimuthal angle defining the major axis of the spheroid diffusion tensor - phi", "'phi'", "'phi'"])
__return_data_name_doc__.add_table(table.label)


def return_eigenvalues():
    """Function for returning Dx, Dy, and Dz."""

    # Reassign the data.
    data = cdp.diff_tensor

    # Diso.
    Diso = 1.0 / (6.0 * data.tm)

    # Dx.
    Dx = Diso - 1.0/3.0 * data.Da * (1.0  +  3.0 * data.Dr)

    # Dy.
    Dy = Diso - 1.0/3.0 * data.Da * (1.0  -  3.0 * data.Dr)

    # Dz.
    Dz = Diso + 2.0/3.0 * data.Da

    # Return the eigenvalues.
    return Dx, Dy, Dz


def return_units(param):
    """Function for returning a string representing the parameters units.

    For example, the internal representation of tm is in seconds, whereas the external
    representation is in nanoseconds, therefore this function will return the string
    'nanoseconds' for tm.


    @param param:       The name of the parameter to return the units for.
    @type param:        str
    @return:            The parameter units string.
    @rtype:             str
    """

    # Get the object name.
    object_name = return_data_name(param)

    # tm (nanoseconds).
    if object_name == 'tm':
        return 'ns'

    # Diso, Da, Dx, Dy, Dz, Dpar, Dper.
    if object_name in ['Diso', 'Da', 'Dx', 'Dy', 'Dz', 'Dpar', 'Dper']:
        return '1e6 1/s'

    # Angles.
    if object_name in ['theta', 'phi', 'alpha', 'beta', 'gamma']:
        return 'deg'


def set(value=None, param=None):
    """Set the diffusion tensor parameters.

    @keyword tensor:    The diffusion tensor object.
    @type tensor:       DiffTensorData instance
    @keyword value:     The list of values to set the parameters to.
    @type value:        list of float
    @keyword param:     The list of parameter names.
    @type param:        list of str
    """

    # Set up the diffusion tensor data if it doesn't exist.
    if not diff_data_exists():
        raise RelaxNoTensorError('diffusion')

    # Initialise.
    geo_params = []
    geo_values = []
    orient_params = []
    orient_values = []

    # Loop over the parameters.
    for i in range(len(param)):
        # Get the object name.
        param[i] = return_data_name(param[i])

        # Unknown parameter.
        if not param[i]:
            raise RelaxUnknownParamError("diffusion tensor", param[i])

        # Default value.
        if value[i] == None:
            value[i] = default_value(param[i])

        # Geometric parameter.
        if param[i] in ['tm', 'Diso', 'Da', 'Dratio', 'Dper', 'Dpar', 'Dr', 'Dx', 'Dy', 'Dz']:
            geo_params.append(param[i])
            geo_values.append(value[i])

        # Orientational parameter.
        if param[i] in ['theta', 'phi', 'alpha', 'beta', 'gamma']:
            orient_params.append(param[i])
            orient_values.append(value[i])


    # Spherical diffusion.
    ######################

    if cdp.diff_tensor.type == 'sphere':
        # Geometric parameters.
        #######################

        # A single geometric parameter.
        if len(geo_params) == 1:
            # The single parameter tm.
            if geo_params[0] == 'tm':
                cdp.diff_tensor.set(param='tm', value=geo_values[0])

            # The single parameter Diso.
            elif geo_params[0] == 'Diso':
                cdp.diff_tensor.set(param='tm', value=1.0 / (6.0 * geo_values[0]))

            # Cannot set the single parameter.
            else:
                raise RelaxError("The geometric diffusion parameter " + repr(geo_params[0]) + " cannot be set.")

        # More than one geometric parameters.
        elif len(geo_params) > 1:
            raise RelaxUnknownParamCombError('geometric parameter set', geo_params)


        # Orientational parameters.
        ###########################

        # ???
        if len(orient_params):
            raise RelaxError("For spherical diffusion, the orientation parameters " + repr(orient_params) + " should not exist.")


    # Spheroidal diffusion.
    #######################

    elif cdp.diff_tensor.type == 'spheroid':
        # Geometric parameters.
        #######################

        # A single geometric parameter.
        if len(geo_params) == 1:
            # The single parameter tm.
            if geo_params[0] == 'tm':
                cdp.diff_tensor.set(param='tm', value=geo_values[0])

            # The single parameter Diso.
            elif geo_params[0] == 'Diso':
                cdp.diff_tensor.set(param='tm', value=1.0 / (6.0 * geo_values[0]))

            # The single parameter Da.
            elif geo_params[0] == 'Da':
                cdp.diff_tensor.set(param='Da', value=geo_values[0])

            # The single parameter Dratio.
            elif geo_params[0] == 'Dratio':
                Dratio = geo_values[0]
                cdp.diff_tensor.set(param='Da', value=(Dratio - 1.0) / (2.0 * cdp.diff_tensor.tm * (Dratio + 2.0)))

            # Cannot set the single parameter.
            else:
                raise RelaxError("The geometric diffusion parameter " + repr(geo_params[0]) + " cannot be set.")

        # Two geometric parameters.
        elif len(geo_params) == 2:
            # The geometric parameter set {tm, Da}.
            if geo_params.count('tm') == 1 and geo_params.count('Da') == 1:
                # The parameters.
                tm = geo_values[geo_params.index('tm')]
                Da = geo_values[geo_params.index('Da')]

                # Set the internal parameter values.
                cdp.diff_tensor.set(param='tm', value=tm)
                cdp.diff_tensor.set(param='Da', value=Da)

            # The geometric parameter set {Diso, Da}.
            elif geo_params.count('Diso') == 1 and geo_params.count('Da') == 1:
                # The parameters.
                Diso = geo_values[geo_params.index('Diso')]
                Da = geo_values[geo_params.index('Da')]

                # Set the internal parameter values.
                cdp.diff_tensor.set(param='tm', value=1.0 / (6.0 * Diso))
                cdp.diff_tensor.set(param='Da', value=Da)

            # The geometric parameter set {tm, Dratio}.
            elif geo_params.count('tm') == 1 and geo_params.count('Dratio') == 1:
                # The parameters.
                tm = geo_values[geo_params.index('tm')]
                Dratio = geo_values[geo_params.index('Dratio')]

                # Set the internal parameter values.
                cdp.diff_tensor.set(param='tm', value=tm)
                cdp.diff_tensor.set(param='Da', value=(Dratio - 1.0) / (2.0 * tm * (Dratio + 2.0)))

            # The geometric parameter set {Dpar, Dper}.
            elif geo_params.count('Dpar') == 1 and geo_params.count('Dper') == 1:
                # The parameters.
                Dpar = geo_values[geo_params.index('Dpar')]
                Dper = geo_values[geo_params.index('Dper')]

                # Set the internal parameter values.
                cdp.diff_tensor.set(param='tm', value=1.0 / (2.0 * (Dpar + 2.0*Dper)))
                cdp.diff_tensor.set(param='Da', value=Dpar - Dper)

            # The geometric parameter set {Diso, Dratio}.
            elif geo_params.count('Diso') == 1 and geo_params.count('Dratio') == 1:
                # The parameters.
                Diso = geo_values[geo_params.index('Diso')]
                Dratio = geo_values[geo_params.index('Dratio')]

                # Set the internal parameter values.
                cdp.diff_tensor.set(param='tm', value=1.0 / (6.0 * Diso))
                cdp.diff_tensor.set(param='Da', value=3.0 * Diso * (Dratio - 1.0) / (Dratio + 2.0))

            # Unknown parameter combination.
            else:
                raise RelaxUnknownParamCombError('geometric parameter set', geo_params)

        # More than two geometric parameters.
        elif len(geo_params) > 2:
            raise RelaxUnknownParamCombError('geometric parameter set', geo_params)


        # Orientational parameters.
        ###########################

        # A single orientational parameter.
        if len(orient_params) == 1:
            # The single parameter theta.
            if orient_params[0] == 'theta':
                cdp.diff_tensor.set(param='theta', value=orient_values[orient_params.index('theta')])

            # The single parameter phi.
            elif orient_params[0] == 'phi':
                cdp.diff_tensor.set(param='phi', value=orient_values[orient_params.index('phi')])

            # Disallowed parameter.
            else:
                raise RelaxError("For spheroidal diffusion, the orientation parameter " + repr(orient_params) + " cannot be set.")

        # Two orientational parameters.
        elif len(orient_params) == 2:
            # The orientational parameter set {theta, phi}.
            if orient_params.count('theta') == 1 and orient_params.count('phi') == 1:
                cdp.diff_tensor.set(param='theta', value=orient_values[orient_params.index('theta')])
                cdp.diff_tensor.set(param='phi', value=orient_values[orient_params.index('phi')])

            # Unknown parameter combination.
            else:
                raise RelaxUnknownParamCombError('orientational parameter set', orient_params)

        # More than two orientational parameters.
        elif len(orient_params) > 2:
            raise RelaxUnknownParamCombError('orientational parameter set', orient_params)


    # Ellipsoidal diffusion.
    ########################

    elif cdp.diff_tensor.type == 'ellipsoid':
        # Geometric parameters.
        #######################

        # A single geometric parameter.
        if len(geo_params) == 1:
            # The single parameter tm.
            if geo_params[0] == 'tm':
                cdp.diff_tensor.set(param='tm', value=geo_values[0])

            # The single parameter Diso.
            elif geo_params[0] == 'Diso':
                cdp.diff_tensor.set(param='tm', value=1.0 / (6.0 * geo_values[0]))

            # The single parameter Da.
            elif geo_params[0] == 'Da':
                cdp.diff_tensor.set(param='Da', value=geo_values[0])

            # The single parameter Dr.
            elif geo_params[0] == 'Dr':
                cdp.diff_tensor.set(param='Dr', value=geo_values[0])

            # Cannot set the single parameter.
            else:
                raise RelaxError("The geometric diffusion parameter " + repr(geo_params[0]) + " cannot be set.")

        # Two geometric parameters.
        elif len(geo_params) == 2:
            # The geometric parameter set {tm, Da}.
            if geo_params.count('tm') == 1 and geo_params.count('Da') == 1:
                # The parameters.
                tm = geo_values[geo_params.index('tm')]
                Da = geo_values[geo_params.index('Da')]

                # Set the internal parameter values.
                cdp.diff_tensor.set(param='tm', value=tm)
                cdp.diff_tensor.set(param='Da', value=Da)

            # The geometric parameter set {tm, Dr}.
            elif geo_params.count('tm') == 1 and geo_params.count('Dr') == 1:
                # The parameters.
                tm = geo_values[geo_params.index('tm')]
                Dr = geo_values[geo_params.index('Dr')]

                # Set the internal parameter values.
                cdp.diff_tensor.set(param='tm', value=tm)
                cdp.diff_tensor.set(param='Dr', value=Dr)

            # The geometric parameter set {Diso, Da}.
            elif geo_params.count('Diso') == 1 and geo_params.count('Da') == 1:
                # The parameters.
                Diso = geo_values[geo_params.index('Diso')]
                Da = geo_values[geo_params.index('Da')]

                # Set the internal parameter values.
                cdp.diff_tensor.set(param='tm', value=1.0 / (6.0 * Diso))
                cdp.diff_tensor.set(param='Da', value=Da)

            # The geometric parameter set {Diso, Dr}.
            elif geo_params.count('Diso') == 1 and geo_params.count('Dr') == 1:
                # The parameters.
                Diso = geo_values[geo_params.index('Diso')]
                Dr = geo_values[geo_params.index('Dr')]

                # Set the internal parameter values.
                cdp.diff_tensor.set(param='tm', value=1.0 / (6.0 * Diso))
                cdp.diff_tensor.set(param='Dr', value=Dr)

            # The geometric parameter set {Da, Dr}.
            elif geo_params.count('Da') == 1 and geo_params.count('Dr') == 1:
                # The parameters.
                Da = geo_values[geo_params.index('Da')]
                Dr = geo_values[geo_params.index('Dr')]

                # Set the internal parameter values.
                cdp.diff_tensor.set(param='Da', value=Da)
                cdp.diff_tensor.set(param='Da', value=Dr)

            # Unknown parameter combination.
            else:
                raise RelaxUnknownParamCombError('geometric parameter set', geo_params)

        # Three geometric parameters.
        elif len(geo_params) == 3:
            # The geometric parameter set {tm, Da, Dr}.
            if geo_params.count('tm') == 1 and geo_params.count('Da') == 1 and geo_params.count('Dr') == 1:
                # The parameters.
                tm = geo_values[geo_params.index('tm')]
                Da = geo_values[geo_params.index('Da')]
                Dr = geo_values[geo_params.index('Dr')]

                # Set the internal parameter values.
                cdp.diff_tensor.set(param='tm', value=tm)
                cdp.diff_tensor.set(param='Da', value=Da)
                cdp.diff_tensor.set(param='Dr', value=Dr)

            # The geometric parameter set {Diso, Da, Dr}.
            elif geo_params.count('Diso') == 1 and geo_params.count('Da') == 1 and geo_params.count('Dr') == 1:
                # The parameters.
                Diso = geo_values[geo_params.index('Diso')]
                Da = geo_values[geo_params.index('Da')]
                Dr = geo_values[geo_params.index('Dr')]

                # Set the internal parameter values.
                cdp.diff_tensor.set(param='tm', value=1.0 / (6.0 * Diso))
                cdp.diff_tensor.set(param='Da', value=Da)
                cdp.diff_tensor.set(param='Dr', value=Dr)

            # The geometric parameter set {Dx, Dy, Dz}.
            elif geo_params.count('Dx') == 1 and geo_params.count('Dy') == 1 and geo_params.count('Dz') == 1:
                # The parameters.
                Dx = geo_values[geo_params.index('Dx')]
                Dy = geo_values[geo_params.index('Dy')]
                Dz = geo_values[geo_params.index('Dz')]

                # Set the internal tm value.
                if Dx + Dy + Dz == 0.0:
                    cdp.diff_tensor.set(param='tm', value=1e99)
                else:
                    cdp.diff_tensor.set(param='tm', value=0.5 / (Dx + Dy + Dz))

                # Set the internal Da value.
                cdp.diff_tensor.set(param='Da', value=Dz - 0.5*(Dx + Dy))

                # Set the internal Dr value.
                if cdp.diff_tensor.Da == 0.0:
                    cdp.diff_tensor.set(param='Dr', value=(Dy - Dx) * 1e99)
                else:
                    cdp.diff_tensor.set(param='Dr', value=(Dy - Dx) / (2.0*cdp.diff_tensor.Da))

            # Unknown parameter combination.
            else:
                raise RelaxUnknownParamCombError('geometric parameter set', geo_params)


        # More than three geometric parameters.
        elif len(geo_params) > 3:
            raise RelaxUnknownParamCombError('geometric parameter set', geo_params)


        # Orientational parameters.
        ###########################

        # A single orientational parameter.
        if len(orient_params) == 1:
            # The single parameter alpha.
            if orient_params[0] == 'alpha':
                cdp.diff_tensor.set(param='alpha', value=orient_values[orient_params.index('alpha')])

            # The single parameter beta.
            elif orient_params[0] == 'beta':
                cdp.diff_tensor.set(param='beta', value=orient_values[orient_params.index('beta')])

            # The single parameter gamma.
            elif orient_params[0] == 'gamma':
                cdp.diff_tensor.set(param='gamma', value=orient_values[orient_params.index('gamma')])

            # Disallowed parameter.
            else:
                raise RelaxError("For ellipsoidal diffusion, the orientation parameter " + repr(orient_params) + " cannot be set.")

        # Two orientational parameters.
        elif len(orient_params) == 2:
            # The orientational parameter set {alpha, beta}.
            if orient_params.count('alpha') == 1 and orient_params.count('beta') == 1:
                cdp.diff_tensor.set(param='alpha', value=orient_values[orient_params.index('alpha')])
                cdp.diff_tensor.set(param='beta', value=orient_values[orient_params.index('beta')])

            # The orientational parameter set {alpha, gamma}.
            if orient_params.count('alpha') == 1 and orient_params.count('gamma') == 1:
                cdp.diff_tensor.set(param='alpha', value=orient_values[orient_params.index('alpha')])
                cdp.diff_tensor.set(param='gamma', value=orient_values[orient_params.index('gamma')])

            # The orientational parameter set {beta, gamma}.
            if orient_params.count('beta') == 1 and orient_params.count('gamma') == 1:
                cdp.diff_tensor.set(param='beta', value=orient_values[orient_params.index('beta')])
                cdp.diff_tensor.set(param='gamma', value=orient_values[orient_params.index('gamma')])

            # Unknown parameter combination.
            else:
                raise RelaxUnknownParamCombError('orientational parameter set', orient_params)

        # Three orientational parameters.
        elif len(orient_params) == 3:
            # The orientational parameter set {alpha, beta, gamma}.
            if orient_params.count('alpha') == 1 and orient_params.count('beta') == 1:
                cdp.diff_tensor.set(param='alpha', value=orient_values[orient_params.index('alpha')])
                cdp.diff_tensor.set(param='beta', value=orient_values[orient_params.index('beta')])
                cdp.diff_tensor.set(param='gamma', value=orient_values[orient_params.index('gamma')])

            # Unknown parameter combination.
            else:
                raise RelaxUnknownParamCombError('orientational parameter set', orient_params)

        # More than three orientational parameters.
        elif len(orient_params) > 3:
            raise RelaxUnknownParamCombError('orientational parameter set', orient_params)


    # Fold the angles in.
    #####################

    if orient_params:
        fold_angles()

# User function documentation.
__set_doc__ = Desc_container("Diffusion tensor set details")
__set_doc__.add_paragraph("If the diffusion tensor has not been setup, use the more powerful function 'diffusion_tensor.init' to initialise the tensor parameters.  This function cannot be used to initialise a diffusion tensor.")
__set_doc__.add_paragraph("The units of the parameters are:")
__set_doc__.add_list_element("Inverse seconds for tm.")
__set_doc__.add_list_element("Seconds for Diso, Da, Dx, Dy, Dz, Dpar, Dper.")
__set_doc__.add_list_element("Unitless for Dratio and Dr.")
__set_doc__.add_list_element("Radians for all angles (alpha, beta, gamma, theta, phi).")
__set_doc__.add_paragraph("When setting a diffusion tensor parameter, the residue number has no effect.  As the internal parameters of spherical diffusion are {tm}, spheroidal diffusion are {tm, Da, theta, phi}, and ellipsoidal diffusion are {tm, Da, Dr, alpha, beta, gamma}, supplying geometric parameters must be done in the following way.  If a single geometric parameter is supplied, it must be one of tm, Diso, Da, Dr, or Dratio.  For the parameters Dpar, Dper, Dx, Dy, and Dx, it is not possible to determine how to use the currently set values together with the supplied value to calculate the new internal parameters.  For spheroidal diffusion, when supplying multiple geometric parameters, the set must belong to one of")
__set_doc__.add_list_element("{tm, Da},")
__set_doc__.add_list_element("{Diso, Da},")
__set_doc__.add_list_element("{tm, Dratio},")
__set_doc__.add_list_element("{Dpar, Dper},")
__set_doc__.add_list_element("{Diso, Dratio},")
__set_doc__.add_paragraph("where either theta, phi, or both orientational parameters can be additionally supplied.  For ellipsoidal diffusion, again when supplying multiple geometric parameters, the set must belong to one of")
__set_doc__.add_list_element("{tm, Da, Dr},")
__set_doc__.add_list_element("{Diso, Da, Dr},")
__set_doc__.add_list_element("{Dx, Dy, Dz},")
__set_doc__.add_paragraph("where any number of the orientational parameters, alpha, beta, or gamma can be additionally supplied.")


def sphere(params=None, time_scale=None, param_types=None):
    """Function for setting up a spherical diffusion tensor.
    
    @param params:      The diffusion tensor parameter.
    @type params:       float
    @param time_scale:  The correlation time scaling value.
    @type time_scale:   float
    @param param_types: The type of parameter supplied.  If 0, then the parameter is tm.  If 1, then
                        the parameter is Diso.
    @type param_types:  int
    """

    # The diffusion type.
    cdp.diff_tensor.set_type('sphere')

    # tm.
    if param_types == 0:
        # Scaling.
        tm = params * time_scale

        # Set the parameters.
        set(value=[tm], param=['tm'])

    # Diso
    elif param_types == 1:
        # Scaling.
        Diso = params * d_scale

        # Set the parameters.
        set(value=[Diso], param=['Diso'])

    # Unknown parameter combination.
    else:
        raise RelaxUnknownParamCombError('param_types', param_types)


def spheroid(params=None, time_scale=None, d_scale=None, angle_units=None, param_types=None, spheroid_type=None):
    """Function for setting up a spheroidal diffusion tensor.
    
    @param params:          The diffusion tensor parameter.
    @type params:           float
    @param time_scale:      The correlation time scaling value.
    @type time_scale:       float
    @param d_scale:         The diffusion tensor eigenvalue scaling value.
    @type d_scale:          float
    @param angle_units:     The units for the angle parameters which can be either 'deg' or 'rad'.
    @type angle_units:      str
    @param param_types:     The type of parameters supplied.  These correspond to 0: {tm, Da, theta,
                            phi}, 1: {Diso, Da, theta, phi}, 2: {tm, Dratio, theta, phi}, 3:  {Dpar,
                            Dper, theta, phi}, 4: {Diso, Dratio, theta, phi}.
    @type param_types:      int
    @param spheroid_type:   A string which, if supplied together with spheroid parameters, will
                            restrict the tensor to either being 'oblate' or 'prolate'.
    @type spheroid_type:    str
    """

    # The diffusion type.
    cdp.diff_tensor.set_type('spheroid')

    # Spheroid diffusion type.
    allowed_types = [None, 'oblate', 'prolate']
    if spheroid_type not in allowed_types:
        raise RelaxError("The 'spheroid_type' argument " + repr(spheroid_type) + " should be 'oblate', 'prolate', or None.")
    cdp.diff_tensor.set(param='spheroid_type', value=spheroid_type)

    # (tm, Da, theta, phi).
    if param_types == 0:
        # Unpack the tuple.
        tm, Da, theta, phi = params

        # Scaling.
        tm = tm * time_scale
        Da = Da * d_scale

        # Set the parameters.
        set(value=[tm, Da], param=['tm', 'Da'])

    # (Diso, Da, theta, phi).
    elif param_types == 1:
        # Unpack the tuple.
        Diso, Da, theta, phi = params

        # Scaling.
        Diso = Diso * d_scale
        Da = Da * d_scale

        # Set the parameters.
        set(value=[Diso, Da], param=['Diso', 'Da'])

    # (tm, Dratio, theta, phi).
    elif param_types == 2:
        # Unpack the tuple.
        tm, Dratio, theta, phi = params

        # Scaling.
        tm = tm * time_scale

        # Set the parameters.
        set(value=[tm, Dratio], param=['tm', 'Dratio'])

    # (Dpar, Dper, theta, phi).
    elif param_types == 3:
        # Unpack the tuple.
        Dpar, Dper, theta, phi = params

        # Scaling.
        Dpar = Dpar * d_scale
        Dper = Dper * d_scale

        # Set the parameters.
        set(value=[Dpar, Dper], param=['Dpar', 'Dper'])

    # (Diso, Dratio, theta, phi).
    elif param_types == 4:
        # Unpack the tuple.
        Diso, Dratio, theta, phi = params

        # Scaling.
        Diso = Diso * d_scale

        # Set the parameters.
        set(value=[Diso, Dratio], param=['Diso', 'Dratio'])

    # Unknown parameter combination.
    else:
        raise RelaxUnknownParamCombError('param_types', param_types)

    # Convert the angles to radians.
    if angle_units == 'deg':
        print("Converting the angles from degrees to radian units.")
        theta = (theta / 360.0) * 2.0 * pi
        phi = (phi / 360.0) * 2.0 * pi

    # Set the orientational parameters.
    set(value=[theta, phi], param=['theta', 'phi'])


def tensor_eigen_system(tensor):
    """Determine the eigenvalues and vectors for the tensor, sorting the entries.

    @return:    The eigenvalues, rotation matrix, and the Euler angles in zyz notation.
    @rtype:     3D rank-1 array, 3D rank-2 array, float, float, float
    """

    # Eigenvalues.
    R, Di, A = svd(tensor)
    D_diag = zeros((3, 3), float64)
    for i in range(3):
        D_diag[i, i] = Di[i]

    # Reordering structure.
    reorder_data = []
    for i in range(3):
        reorder_data.append([Di[i], i])
    reorder_data.sort()

    # The indices.
    reorder = zeros(3, int)
    Di_sort = zeros(3, float)
    for i in range(3):
        Di_sort[i], reorder[i] = reorder_data[i]

    # Reorder columns.
    R_new = zeros((3, 3), float64)
    for i in range(3):
        R_new[:, i] = R[:, reorder[i]]

    # Switch from the left handed to right handed universes (if needed).
    if norm(cross(R_new[:, 0], R_new[:, 1]) - R_new[:, 2]) > 1e-7:
        R_new[:, 2] = -R_new[:, 2]

    # Reverse the rotation.
    R_new = transpose(R_new)

    # Euler angles (reverse rotation in the rotated axis system).
    gamma, beta, alpha = R_to_euler_zyz(R_new)

    # Collapse the pi axis rotation symmetries.
    if alpha >= pi:
        alpha = alpha - pi
    if gamma >= pi:
        alpha = pi - alpha
        beta = pi - beta
        gamma = gamma - pi
    if beta >= pi:
        alpha = pi - alpha
        beta = beta - pi

    # Return the values.
    return Di_sort, R_new, alpha, beta, gamma


def test_params(num_params):
    """Function for testing the validity of the input parameters."""

    # An allowable error to account for machine precision, optimisation quality, etc.
    error = 1e-4

    # tm.
    tm = cdp.diff_tensor.tm
    if tm <= 0.0 or tm > 1e-6:
        raise RelaxError("The tm value of " + repr(tm) + " should be between zero and one microsecond.")

    # Spheroid.
    if num_params == 4:
        # Parameters.
        Diso = 1.0 / (6.0 * cdp.diff_tensor.tm)
        Da = cdp.diff_tensor.Da

        # Da.
        if Da < (-1.5*Diso - error*Diso) or Da > (3.0*Diso + error*Diso):
            raise RelaxError("The Da value of " + repr(Da) + " should be between -3/2 * Diso and 3Diso.")

    # Ellipsoid.
    if num_params == 6:
        # Parameters.
        Diso = 1.0 / (6.0 * cdp.diff_tensor.tm)
        Da = cdp.diff_tensor.Da
        Dr = cdp.diff_tensor.Dr

        # Da.
        if Da < (0.0 - error*Diso) or Da > (3.0*Diso + error*Diso):
            raise RelaxError("The Da value of " + repr(Da) + " should be between zero and 3Diso.")

        # Dr.
        if Dr < (0.0 - error) or Dr > (1.0 + error):
            raise RelaxError("The Dr value of " + repr(Dr) + " should be between zero and one.")


def unit_axes():
    """Function for calculating the unit axes of the diffusion tensor.

    Spheroid
    ========

    The unit Dpar vector is::

                 | sin(theta) * cos(phi) |
        Dpar  =  | sin(theta) * sin(phi) |
                 |      cos(theta)       |


    Ellipsoid
    =========

    The unit Dx vector is::

               | -sin(alpha) * sin(gamma) + cos(alpha) * cos(beta) * cos(gamma) |
        Dx  =  | -sin(alpha) * cos(gamma) - cos(alpha) * cos(beta) * sin(gamma) |
               |                    cos(alpha) * sin(beta)                      |

    The unit Dy vector is::

               | cos(alpha) * sin(gamma) + sin(alpha) * cos(beta) * cos(gamma) |
        Dy  =  | cos(alpha) * cos(gamma) - sin(alpha) * cos(beta) * sin(gamma) |
               |                   sin(alpha) * sin(beta)                      |

    The unit Dz vector is::

               | -sin(beta) * cos(gamma) |
        Dz  =  |  sin(beta) * sin(gamma) |
               |        cos(beta)        |

    """

    # Spheroid.
    if cdp.diff_tensor.type == 'spheroid':
        # Initialise.
        Dpar = zeros(3, float64)

        # Trig.
        sin_theta = sin(cdp.diff_tensor.theta)
        cos_theta = cos(cdp.diff_tensor.theta)
        sin_phi = sin(cdp.diff_tensor.phi)
        cos_phi = cos(cdp.diff_tensor.phi)

        # Unit Dpar axis.
        Dpar[0] = sin_theta * cos_phi
        Dpar[1] = sin_theta * sin_phi
        Dpar[2] = cos_theta

        # Return the vector.
        return Dpar

    # Ellipsoid.
    if cdp.diff_tensor.type == 'ellipsoid':
        # Initialise.
        Dx = zeros(3, float64)
        Dy = zeros(3, float64)
        Dz = zeros(3, float64)

        # Trig.
        sin_alpha = sin(cdp.diff_tensor.alpha)
        cos_alpha = cos(cdp.diff_tensor.alpha)
        sin_beta = sin(cdp.diff_tensor.beta)
        cos_beta = cos(cdp.diff_tensor.beta)
        sin_gamma = sin(cdp.diff_tensor.gamma)
        cos_gamma = cos(cdp.diff_tensor.gamma)

        # Unit Dx axis.
        Dx[0] = -sin_alpha * sin_gamma  +  cos_alpha * cos_beta * cos_gamma
        Dx[1] = -sin_alpha * cos_gamma  -  cos_alpha * cos_beta * sin_gamma
        Dx[2] =  cos_alpha * sin_beta

        # Unit Dy axis.
        Dx[0] = cos_alpha * sin_gamma  +  sin_alpha * cos_beta * cos_gamma
        Dx[1] = cos_alpha * cos_gamma  -  sin_alpha * cos_beta * sin_gamma
        Dx[2] = sin_alpha * sin_beta

        # Unit Dz axis.
        Dx[0] = -sin_beta * cos_gamma
        Dx[1] =  sin_beta * sin_gamma
        Dx[2] =  cos_beta

        # Return the vectors.
        return Dx, Dy, Dz
