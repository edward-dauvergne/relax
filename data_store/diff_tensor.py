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
"""The diffusion tensor objects of the relax data store."""

# Python module imports.
from copy import deepcopy
from re import search
from math import cos, sin
from numpy import array, float64, dot, identity, transpose, zeros

# relax module imports.
from data_store.data_classes import Element
from lib.geometry.coord_transform import spherical_to_cartesian
from lib.geometry.rotations import two_vect_to_R
from lib.errors import RelaxError
from lib.xml import fill_object_contents, xml_to_object


def calc_Diso(tm):
    """Function for calculating the Diso value.

    The equation for calculating the parameter is::

        Diso  =  1 / (6tm).

    @keyword tm:    The global correlation time.
    @type tm:       float
    @return:        The isotropic diffusion rate (Diso).
    @rtype:         float
    """

    # Calculated and return the Diso value.
    return 1.0 / (6.0 * tm)


def calc_Dpar(Diso, Da):
    """Function for calculating the Dpar value.

    The equation for calculating the parameter is::

        Dpar  =  Diso + 2/3 Da.

    @keyword Diso:  The isotropic diffusion rate.
    @type Diso:     float
    @keyword Da:    The anisotropic diffusion rate.
    @type Da:       float
    @return:        The diffusion rate parallel to the unique axis of the spheroid.
    @rtype:         float
    """

    # Dpar value.
    return Diso + 2.0/3.0 * Da


def calc_Dpar_unit(theta, phi):
    """Function for calculating the Dpar unit vector.

    The unit vector parallel to the unique axis of the diffusion tensor is::

                      | sin(theta) * cos(phi) |
        Dpar_unit  =  | sin(theta) * sin(phi) |.
                      |      cos(theta)       |

    @keyword theta: The azimuthal angle in radians.
    @type theta:    float
    @keyword phi:   The polar angle in radians.
    @type phi:      float
    @return:        The Dpar unit vector.
    @rtype:         numpy array
    """

    # Initilise the vector.
    Dpar_unit = zeros(3, float64)

    # Calculate the x, y, and z components.
    Dpar_unit[0] = sin(theta) * cos(phi)
    Dpar_unit[1] = sin(theta) * sin(phi)
    Dpar_unit[2] = cos(theta)

    # Return the unit vector.
    return Dpar_unit


def calc_Dper(Diso, Da):
    """Function for calculating the Dper value.

    The equation for calculating the parameter is::

        Dper  =  Diso - 1/3 Da.

    @keyword Diso:  The isotropic diffusion rate.
    @type Diso:     float
    @keyword Da:    The anisotropic diffusion rate.
    @type Da:       float
    @return:        The diffusion rate perpendicular to the unique axis of the spheroid.
    @rtype:         float
    """

    # Dper value.
    return Diso - 1.0/3.0 * Da


def calc_Dratio(Dpar, Dper):
    """Function for calculating the Dratio value.

    The equation for calculating the parameter is::

        Dratio  =  Dpar / Dper.

    @keyword Dpar:  The diffusion rate parallel to the unique axis of the spheroid.
    @type Dpar:     float
    @keyword Dper:  The diffusion rate perpendicular to the unique axis of the spheroid.
    @type Dper:     float
    @return:        The ratio of the parallel and perpendicular diffusion rates.
    @rtype:         float
    """

    # Dratio value.
    return Dpar / Dper


def calc_Dx(Diso, Da, Dr):
    """Function for calculating the Dx value.

    The equation for calculating the parameter is::

        Dx  =  Diso - 1/3 Da(1 + 3Dr).

    @keyword Diso:  The isotropic diffusion rate.
    @type Diso:     float
    @keyword Da:    The anisotropic diffusion rate.
    @type Da:       float
    @keyword Dr:    The rhombic component of the diffusion tensor.
    @type Dr:       float
    @return:        The diffusion rate parallel to the x-axis of the ellipsoid.
    @rtype:         float
    """

    # Dx value.
    return Diso - 1.0/3.0 * Da * (1.0 + 3.0*Dr)


def calc_Dx_unit(alpha, beta, gamma):
    """Function for calculating the Dx unit vector.

    The unit Dx vector is::

                    | -sin(alpha) * sin(gamma) + cos(alpha) * cos(beta) * cos(gamma) |
        Dx_unit  =  | -sin(alpha) * cos(gamma) - cos(alpha) * cos(beta) * sin(gamma) |.
                    |                    cos(alpha) * sin(beta)                      |

    @keyword alpha: The Euler angle alpha in radians using the z-y-z convention.
    @type alpha:    float
    @keyword beta:  The Euler angle beta in radians using the z-y-z convention.
    @type beta:     float
    @keyword gamma: The Euler angle gamma in radians using the z-y-z convention.
    @type gamma:    float
    @return:        The Dx unit vector.
    @rtype:         numpy array
    """

    # Initilise the vector.
    Dx_unit = zeros(3, float64)

    # Calculate the x, y, and z components.
    Dx_unit[0] = -sin(alpha) * sin(gamma)  +  cos(alpha) * cos(beta) * cos(gamma)
    Dx_unit[1] = -sin(alpha) * cos(gamma)  -  cos(alpha) * cos(beta) * sin(gamma)
    Dx_unit[2] = cos(alpha) * sin(beta)

    # Return the unit vector.
    return Dx_unit


def calc_Dy(Diso, Da, Dr):
    """Function for calculating the Dy value.

    The equation for calculating the parameter is::

        Dy  =  Diso - 1/3 Da(1 - 3Dr),

    @keyword Diso:  The isotropic diffusion rate.
    @type Diso:     float
    @keyword Da:    The anisotropic diffusion rate.
    @type Da:       float
    @keyword Dr:    The rhombic component of the diffusion tensor.
    @type Dr:       float
    @return:        The Dy value.
    @rtype:         float
    """

    # Dy value.
    return Diso - 1.0/3.0 * Da * (1.0 - 3.0*Dr)


def calc_Dy_unit(alpha, beta, gamma):
    """Function for calculating the Dy unit vector.

    The unit Dy vector is::

                    | cos(alpha) * sin(gamma) + sin(alpha) * cos(beta) * cos(gamma) |
        Dy_unit  =  | cos(alpha) * cos(gamma) - sin(alpha) * cos(beta) * sin(gamma) |.
                    |                   sin(alpha) * sin(beta)                      |

    @keyword alpha: The Euler angle alpha in radians using the z-y-z convention.
    @type alpha:    float
    @keyword beta:  The Euler angle beta in radians using the z-y-z convention.
    @type beta:     float
    @keyword gamma: The Euler angle gamma in radians using the z-y-z convention.
    @type gamma:    float
    @return:        The Dy unit vector.
    @rtype:         numpy array
    """

    # Initilise the vector.
    Dy_unit = zeros(3, float64)

    # Calculate the x, y, and z components.
    Dy_unit[0] = cos(alpha) * sin(gamma)  +  sin(alpha) * cos(beta) * cos(gamma)
    Dy_unit[1] = cos(alpha) * cos(gamma)  -  sin(alpha) * cos(beta) * sin(gamma)
    Dy_unit[2] = sin(alpha) * sin(beta)

    # Return the unit vector.
    return Dy_unit


def calc_Dz(Diso, Da):
    """Function for calculating the Dz value.

    The equation for calculating the parameter is::

        Dz  =  Diso + 2/3 Da.

    @keyword Diso:  The isotropic diffusion rate.
    @type Diso:     float
    @keyword Da:    The anisotropic diffusion rate.
    @type Da:       float
    @return:        The Dz value.
    @rtype:         float
    """

    # Dz value.
    return Diso + 2.0/3.0 * Da


def calc_Dz_unit(beta, gamma):
    """Function for calculating the Dz unit vector.

    The unit Dz vector is::

                    | -sin(beta) * cos(gamma) |
        Dz_unit  =  |  sin(beta) * sin(gamma) |.
                    |        cos(beta)        |

    @keyword beta:  The Euler angle beta in radians using the z-y-z convention.
    @type beta:     float
    @keyword gamma: The Euler angle gamma in radians using the z-y-z convention.
    @type gamma:    float
    @return:        The Dz unit vector.
    @rtype:         numpy array
    """

    # Initilise the vector.
    Dz_unit = zeros(3, float64)

    # Calculate the x, y, and z components.
    Dz_unit[0] = -sin(beta) * cos(gamma)
    Dz_unit[1] = sin(beta) * sin(gamma)
    Dz_unit[2] = cos(beta)

    # Return the unit vector.
    return Dz_unit


def calc_rotation(diff_type, *args):
    """Function for calculating the rotation matrix.

    Spherical diffusion
    ===================

    As the orientation of the diffusion tensor within the structural frame is undefined when the molecule diffuses as a sphere, the rotation matrix is simply the identity matrix::

              | 1  0  0 |
        R  =  | 0  1  0 |.
              | 0  0  1 |


    Spheroidal diffusion
    ====================

    The rotation matrix required to shift from the diffusion tensor frame to the structural frame is generated from the unique axis of the diffusion tensor.


    Ellipsoidal diffusion
    =====================

    The rotation matrix required to shift from the diffusion tensor frame to the structural frame is equal to::

        R  =  | Dx_unit  Dy_unit  Dz_unit |,

              | Dx_unit[0]  Dy_unit[0]  Dz_unit[0] |
           =  | Dx_unit[1]  Dy_unit[1]  Dz_unit[1] |.
              | Dx_unit[2]  Dy_unit[2]  Dz_unit[2] |

    @param args:        All the function arguments.  For the spheroid, this includes the spheroid_type (str), the azimuthal angle theta in radians (float), and the polar angle phi in radians (float).  For the ellipsoid, this includes the Dx unit vector (numpy 3D, rank-1 array), the Dy unit vector (numpy 3D, rank-1 array), and the Dz unit vector (numpy 3D, rank-1 array).
    @type args:         tuple
    @return:            The rotation matrix.
    @rtype:             numpy 3x3 array
    """

    # The rotation matrix for the sphere.
    if diff_type == 'sphere':
        return identity(3, float64)

    # The rotation matrix for the spheroid.
    elif diff_type == 'spheroid':
        # Unpack the arguments.
        spheroid_type, theta, phi = args

        # Initialise the rotation matrix.
        R = zeros((3, 3), float64)

        # The unique axis in the diffusion frame.
        if spheroid_type == 'prolate':
            axis = array([0, 0, 1], float64)
        else:
            axis = array([1, 0, 0], float64)

        # The spherical coordinate vector.
        spher_vect = array([1, theta, phi], float64)

        # The diffusion tensor axis in the PDB frame.
        diff_axis = zeros(3, float64)
        spherical_to_cartesian(spher_vect, diff_axis)

        # The rotation matrix.
        two_vect_to_R(diff_axis, axis, R)

        # Return the rotation.
        return R

    # The rotation matrix for the ellipsoid.
    elif diff_type == 'ellipsoid':
        # Unpack the arguments.
        Dx_unit, Dy_unit, Dz_unit = args

        # Initialise the rotation matrix.
        rotation = identity(3, float64)

        # First column of the rotation matrix.
        rotation[:, 0] = Dx_unit

        # Second column of the rotation matrix.
        rotation[:, 1] = Dy_unit

        # Third column of the rotation matrix.
        rotation[:, 2] = Dz_unit

        # Return the tensor.
        return rotation

    # Raise an error.
    else:
        raise RelaxError('The diffusion tensor has not been specified')


def calc_spheroid_type(Da, spheroid_type, flag):
    """Determine the spheroid type.

    @param Da:              The diffusion tensor anisotropy.
    @type Da:               float
    @param spheroid_type:   The current value of spheroid_type.
    @type spheroid_type:    str
    @param flag:            A flag which if True will cause the current spheroid_type value to be returned.
    @type flag:             bool
    @return:                The spheroid type, either 'oblate' or 'prolate'.
    @rtype:                 str
    """

    # Do not change.
    if flag:
        return spheroid_type

    # The spheroid type.
    if Da > 0.0:
        return 'prolate'
    else:
        return 'oblate'


def calc_tensor(rotation, tensor_diag):
    """Function for calculating the diffusion tensor (in the structural frame).

    The diffusion tensor is calculated using the diagonalised tensor and the rotation matrix
    through the equation::

        R . tensor_diag . R^T.

    @keyword rotation:      The rotation matrix.
    @type rotation:         numpy 3x3 array
    @keyword tensor_diag:   The diagonalised diffusion tensor.
    @type tensor_diag:      numpy 3x3 array
    @return:                The diffusion tensor (within the structural frame).
    @rtype:                 numpy 3x3 array
    """

    # Rotation (R . tensor_diag . R^T).
    return dot(rotation, dot(tensor_diag, transpose(rotation)))


def calc_tensor_diag(diff_type, *args):
    """Function for calculating the diagonalised diffusion tensor.

    The diagonalised spherical diffusion tensor is defined as::

                   | Diso     0     0 |
        tensor  =  |    0  Diso     0 |.
                   |    0     0  Diso |

    The diagonalised spheroidal tensor is defined as::

                   | Dper     0     0 |
        tensor  =  |    0  Dper     0 |.
                   |    0     0  Dpar |

    The diagonalised ellipsoidal diffusion tensor is defined as::

                   | Dx   0   0 |
        tensor  =  |  0  Dy   0 |.
                   |  0   0  Dz |

    @param args:    All the arguments.  For the sphere, this includes the Diso parameter (float).  For the spheroid, this includes Dpar and Dper parameters (floats).  For the ellipsoid, this includes the Dx, Dy, and Dz parameters (floats).
    @type args:     tuple
    @return:        The diagonalised diffusion tensor.
    @rtype:         numpy 3x3 array
    """

    # Spherical diffusion tensor.
    if diff_type == 'sphere':
        # Unpack the arguments.
        Diso, = args

        # Initialise the tensor.
        tensor = zeros((3, 3), float64)

        # Populate the diagonal elements.
        tensor[0, 0] = Diso
        tensor[1, 1] = Diso
        tensor[2, 2] = Diso

        # Return the tensor.
        return tensor

    # Spheroidal diffusion tensor.
    elif diff_type == 'spheroid':
        # Unpack the arguments.
        Dpar, Dper = args

        # Initialise the tensor.
        tensor = zeros((3, 3), float64)

        # Populate the diagonal elements.
        if Dpar > Dper:
            tensor[0, 0] = Dper
            tensor[1, 1] = Dper
            tensor[2, 2] = Dpar
        else:
            tensor[0, 0] = Dpar
            tensor[1, 1] = Dper
            tensor[2, 2] = Dper

        # Return the tensor.
        return tensor

    # Ellipsoidal diffusion tensor.
    elif diff_type == 'ellipsoid':
        # Unpack the arguments.
        Dx, Dy, Dz = args

        # Initialise the tensor.
        tensor = zeros((3, 3), float64)

        # Populate the diagonal elements.
        tensor[0, 0] = Dx
        tensor[1, 1] = Dy
        tensor[2, 2] = Dz

        # Return the tensor.
        return tensor


def dependency_generator(diff_type):
    """Generator for the automatic updating the diffusion tensor data structures.

    The order of the yield statements is important!

    @param diff_type:   The type of Brownian rotational diffusion.
    @type diff_type:    str
    @return:            This generator successively yields three objects, the target object to update, the list of parameters which if modified cause the target to be updated, and the list of parameters that the target depends upon.
    """

    # Spherical diffusion.
    if diff_type == 'sphere':
        yield ('Diso',          ['tm'], ['tm'])
        yield ('tensor_diag',   ['tm'], ['type', 'Diso'])
        yield ('rotation',      ['tm'], ['type'])
        yield ('tensor',        ['tm'], ['rotation', 'tensor_diag'])

    # Spheroidal diffusion.
    elif diff_type == 'spheroid':
        yield ('Diso',          ['tm'],                         ['tm'])
        yield ('Dpar',          ['tm', 'Da'],                   ['Diso', 'Da'])
        yield ('Dper',          ['tm', 'Da'],                   ['Diso', 'Da'])
        yield ('Dratio',        ['tm', 'Da'],                   ['Dpar', 'Dper'])
        yield ('Dpar_unit',     ['theta', 'phi'],               ['theta', 'phi'])
        yield ('tensor_diag',   ['tm', 'Da'],                   ['type', 'Dpar', 'Dper'])
        yield ('rotation',      ['theta', 'phi'],               ['type', 'spheroid_type', 'theta', 'phi'])
        yield ('tensor',        ['tm', 'Da', 'theta', 'phi'],   ['rotation', 'tensor_diag'])
        yield ('spheroid_type', ['Da'],                         ['Da', 'spheroid_type', '_spheroid_type'])

    # Ellipsoidal diffusion.
    elif diff_type == 'ellipsoid':
        yield ('Diso',          ['tm'],                                         ['tm'])
        yield ('Dx',            ['tm', 'Da', 'Dr'],                             ['Diso', 'Da', 'Dr'])
        yield ('Dy',            ['tm', 'Da', 'Dr'],                             ['Diso', 'Da', 'Dr'])
        yield ('Dz',            ['tm', 'Da'],                                   ['Diso', 'Da'])
        yield ('Dx_unit',       ['alpha', 'beta', 'gamma'],                     ['alpha', 'beta', 'gamma'])
        yield ('Dy_unit',       ['alpha', 'beta', 'gamma'],                     ['alpha', 'beta', 'gamma'])
        yield ('Dz_unit',       ['beta', 'gamma'],                              ['beta', 'gamma'])
        yield ('tensor_diag',   ['tm', 'Da', 'Dr'],                             ['type', 'Dx', 'Dy', 'Dz'])
        yield ('rotation',      ['alpha', 'beta', 'gamma'],                     ['type', 'Dx_unit', 'Dy_unit', 'Dz_unit'])
        yield ('tensor',        ['tm', 'Da', 'Dr', 'alpha', 'beta', 'gamma'],   ['rotation', 'tensor_diag'])



# Diffusion tensor specific data.
#################################

class DiffTensorData(Element):
    """An empty data container for the diffusion tensor elements."""

    # List of modifiable attributes.
    _mod_attr = [
        'type',
        'fixed',
        'spheroid_type',
        'tm',       'tm_sim',       'tm_err',
        'Da',       'Da_sim',       'Da_err',
        'Dr',       'Dr_sim',       'Dr_err',
        'theta',    'theta_sim',    'theta_err',
        'phi',      'phi_sim',      'phi_err',
        'alpha',    'alpha_sim',    'alpha_err',
        'beta',     'beta_sim',     'beta_err',
        'gamma',    'gamma_sim',    'gamma_err'
    ]

    def __deepcopy__(self, memo):
        """Replacement deepcopy method."""

        # Make a new object.
        new_obj = self.__class__.__new__(self.__class__)

        # Initialise it.
        new_obj.__init__()

        # Copy over the simulation number.
        new_obj.__dict__['_sim_num'] = self._sim_num

        # Loop over all modifiable objects in self and make deepcopies of them.
        for name in self._mod_attr:
            # Skip if missing from the object.
            if not hasattr(self, name):
                continue

            # The category.
            if search('_err$', name):
                category = 'err'
                param = name.replace('_err', '')
            elif search('_sim$', name):
                category = 'sim'
                param = name.replace('_sim', '')
            else:
                category = 'val'
                param = name

            # Get the object.
            value = getattr(self, name)

            # Normal parameters.
            if category == 'val':
                new_obj.set(param=param, value=deepcopy(value, memo))

            # Errors.
            elif category == 'err':
                new_obj.set(param=param, value=deepcopy(value, memo), category='err')

            # Simulation objects objects.
            else:
                # Recreate the list elements.
                for i in range(len(value)):
                    new_obj.set(param=param, value=value[i], category='sim', sim_index=i)

        # Return the new object.
        return new_obj


    def __init__(self):
        """Initialise a few instance variables."""

        # Set the initial diffusion type to None.
        self.__dict__['type'] = None

        # Initialise the spheroid type flag.
        self.__dict__['_spheroid_type'] = False

        # The number of simulations.
        self.__dict__['_sim_num'] = None


    def __setattr__(self, name, value):
        """Make this object read-only."""

        raise RelaxError("The diffusion tensor is a read-only object.  The diffusion tensor set() method must be used instead.")


    def _update_object(self, param_name, target, update_if_set, depends, category):
        """Function for updating the target object, its error, and the MC simulations.

        If the base name of the object is not within the 'update_if_set' list, this function returns
        without doing anything (to avoid wasting time).  Dependant upon the category the object
        (target), its error (target+'_err'), or all Monte Carlo simulations (target+'_sim') are
        updated.

        @param param_name:      The parameter name which is being set in the __setattr__() function.
        @type param_name:       str
        @param target:          The name of the object to update.
        @type target:           str
        @param update_if_set:   If the parameter being set by the __setattr__() function is not
            within this list of parameters, don't waste time updating the
            target.
        @param depends:         An array of names objects that the target is dependent upon.
        @type depends:          array of str
        @param category:        The category of the object to update (one of 'val', 'err', or
            'sim').
        @type category:         str
        @return:                None
        """

        # Only update if the parameter name is within the 'update_if_set' list.
        if not param_name in update_if_set:
            return

        # Get the function for calculating the value.
        fn = globals()['calc_'+target]


        # The value.
        ############

        if category == 'val':
            # Get all the dependencies if possible.
            missing_dep = 0
            deps = ()
            for dep_name in depends:
                # Test if the object exists.
                if not hasattr(self, dep_name):
                    missing_dep = 1
                    break

                # Get the object and place it into the 'deps' tuple.
                deps = deps+(getattr(self, dep_name),)

            # Only update the object if its dependencies exist.
            if not missing_dep:
                # Calculate the value.
                value = fn(*deps)

                # Set the attribute.
                self.__dict__[target] = value


        # The error.
        ############

        if category == 'err':
            # Get all the dependencies if possible.
            missing_dep = 0
            deps = ()
            for dep_name in depends:
                # Test if the error object exists.
                if not hasattr(self, dep_name+'_err'):
                    missing_dep = 1
                    break

                # Get the object and place it into the 'deps' tuple.
                deps = deps+(getattr(self, dep_name+'_err'),)

            # Only update the error object if its dependencies exist.
            if not missing_dep:
                # Calculate the value.
                value = fn(*deps)

                # Set the attribute.
                self.__dict__[target+'_err'] = value


        # The Monte Carlo simulations.
        ##############################

        if category == 'sim':
            # Get all the dependencies if possible.
            missing_dep = 0
            deps = []
            for dep_name in depends:
                # Modify the dependency name.
                if dep_name not in ['type', 'spheroid_type']:
                    dep_name = dep_name+'_sim'

                # Test if the MC sim object exists.
                if not hasattr(self, dep_name) or getattr(self, dep_name) == None or not len(getattr(self, dep_name)):
                    missing_dep = 1
                    break

                # Get the object and place it into the 'deps' tuple.
                deps.append(getattr(self, dep_name))

            # Only create the MC simulation object if its dependencies exist.
            if not missing_dep:
                # Initialise an empty array to store the MC simulation object elements (if it doesn't already exist).
                if not target+'_sim' in self.__dict__:
                    self.__dict__[target+'_sim'] = DiffTensorSimList(elements=self._sim_num)

                # Repackage the deps structure.
                args = []
                skip = False
                for i in range(self._sim_num):
                    args.append(())

                    # Loop over the dependent structures.
                    for j in range(len(deps)):
                        # None, so skip.
                        if deps[j] == None or deps[j][i] == None:
                            skip = True

                        # String data type.
                        if isinstance(deps[j], str):
                            args[-1] = args[-1] + (deps[j],)

                        # List data type.
                        else:
                            args[-1] = args[-1] + (deps[j][i],)

                # Loop over the sims and set the values.
                if not skip:
                    for i in range(self._sim_num):
                        # Calculate the value.
                        value = fn(*args[i])

                        # Set the attribute.
                        self.__dict__[target+'_sim']._set(value=value, sim_index=i)


    def from_xml(self, diff_tensor_node, file_version=1):
        """Recreate the diffusion tensor data structure from the XML diffusion tensor node.

        @param diff_tensor_node:    The diffusion tensor XML node.
        @type diff_tensor_node:     xml.dom.minicompat.Element instance
        @keyword file_version:      The relax XML version of the XML file.
        @type file_version:         int
        """

        # First set the diffusion type.  Doing this first is essential for the proper reconstruction of the object.
        self.__dict__['type'] = str(diff_tensor_node.getAttribute('type'))

        # A temporary object to pack the structures from the XML data into.
        temp_obj = Element()

        # Recreate all the other data structures (into the temporary object).
        xml_to_object(diff_tensor_node, temp_obj, file_version=file_version)

        # Loop over all modifiable objects in the temporary object and make soft copies of them.
        for name in self._mod_attr:
            # Skip if missing from the object.
            if not hasattr(temp_obj, name):
                continue

            # The category.
            if search('_err$', name):
                category = 'err'
                param = name.replace('_err', '')
            elif search('_sim$', name):
                category = 'sim'
                param = name.replace('_sim', '')
            else:
                category = 'val'
                param = name

            # Get the object.
            value = getattr(temp_obj, name)

            # Normal parameters.
            if category == 'val':
                self.set(param=param, value=value)

            # Errors.
            elif category == 'err':
                self.set(param=param, value=value, category='err')

            # Simulation objects objects.
            else:
                # Recreate the list elements.
                for i in range(len(value)):
                    self.set(param=param, value=value[i], category='sim', sim_index=i)

        # Delete the temporary object.
        del temp_obj


    def set(self, param=None, value=None, category='val', sim_index=None):
        """Set a diffusion tensor parameter.

        @keyword param:     The name of the parameter to set.
        @type param:        str
        @keyword value:     The parameter value.
        @type value:        anything
        @keyword category:  The type of parameter to set.  This can be 'val' for the normal parameter, 'err' for the parameter error, or 'sim' for Monte Carlo or other simulated parameters.
        @type category:     str
        @keyword sim_index: The index for a Monte Carlo simulation for simulated parameter.
        @type sim_index:    int or None
        """

        # Check the type.
        if category not in ['val', 'err', 'sim']:
            raise RelaxError("The category of the parameter '%s' is incorrectly set to %s - it must be one of 'val', 'err' or 'sim'." % (param, category))

        # Test if the attribute that is trying to be set is modifiable.
        if not param in self._mod_attr:
            raise RelaxError("The object '%s' is not a modifiable attribute." % param)

        # Set a parameter value.
        if category == 'val':
            self.__dict__[param] = value

        # Set an error.
        elif category == 'err':
            self.__dict__[param+'_err'] = value

        # Set a simulation value.
        else:
            # Check that the simulation number has been set.
            if self._sim_num == None:
                raise RelaxError("The diffusion tensor simulation number has not yet been specified, therefore a simulation value cannot be set.")

            # The simulation parameter name.
            sim_param = param+'_sim'

            # No object, so create it.
            if not hasattr(self, sim_param):
                self.__dict__[sim_param] = DiffTensorSimList(elements=self._sim_num)

            # The object.
            obj = getattr(self, sim_param)

            # Set the value.
            obj._set(value=value, sim_index=sim_index)

        # Flag for the spheroid type.
        if param == 'spheroid_type' and value:
            self.__dict__['_spheroid_type'] = True

        # Skip the updating process for certain objects.
        if param in ['type', 'fixed', 'spheroid_type']:
            return

        # Update the data structures.
        for target, update_if_set, depends in dependency_generator(self.type):
            self._update_object(param, target, update_if_set, depends, category)


    def set_fixed(self, flag):
        """Set if the diffusion tensor should be fixed during optimisation or not.

        @param flag:    The fixed flag.
        @type flag:     bool
        """

        self.__dict__['fixed'] = flag


    def set_sim_num(self, sim_number=None):
        """Set the number of Monte Carlo simulations for the construction of the simulation structures.

        @keyword sim_number:    The number of Monte Carlo simulations.
        @type sim_number:       int
        """

        # Check if not already set.
        if self._sim_num != None:
            raise RelaxError("The number of simulations has already been set.")

        # Store the value.
        self.__dict__['_sim_num'] = sim_number


    def set_type(self, value):
        """Set the diffusion tensor type.

        @param value:   The diffusion tensor type.  This can be one of 'sphere', 'spheroid' or 'ellipsoid'.
        @type value:    str
        """

        # Checks.
        allowed = ['sphere', 'spheroid', 'ellipsoid']
        if value not in allowed:
            raise RelaxError("The diffusion tensor type '%s' must be one of %s." % (value, allowed))

        # Set the type.
        self.__dict__['type'] = value


    def to_xml(self, doc, element):
        """Create an XML element for the diffusion tensor.

        @param doc:     The XML document object.
        @type doc:      xml.dom.minidom.Document instance
        @param element: The element to add the diffusion tensor element to.
        @type element:  XML element object
        """

        # Create the diffusion tensor element and add it to the higher level element.
        tensor_element = doc.createElement('diff_tensor')
        element.appendChild(tensor_element)

        # Set the diffusion tensor attributes.
        tensor_element.setAttribute('desc', 'Diffusion tensor')
        tensor_element.setAttribute('type', self.type)

        # The blacklist.
        blacklist = ['type', 'is_empty'] + list(self.__class__.__dict__.keys())
        for name in dir(self):
            if name not in self._mod_attr:
                blacklist.append(name)

        # Add all simple python objects within the PipeContainer to the pipe element.
        fill_object_contents(doc, tensor_element, object=self, blacklist=blacklist)



class DiffTensorSimList(list):
    """Empty data container for Monte Carlo simulation diffusion tensor data."""

    def __deepcopy__(self, memo):
        """Replacement deepcopy method."""

        # Make a new object.
        new_obj = self.__class__.__new__(self.__class__)

        # Loop over all objects in self and make deepcopies of them.
        for name in dir(self):
            # Skip all names begining with '_'.
            if search('^_', name):
                continue

            # Skip the class methods.
            if name in self.__class__.__dict__ or name in dir(list):
                continue

            # Get the object.
            value = getattr(self, name)

            # Replace the object with a deepcopy of it.
            setattr(new_obj, name, deepcopy(value, memo))

        # Return the new object.
        return new_obj


    def __init__(self, elements=None):
        """Initialise the Monte Carlo simulation parameter list.

        @keyword elements:      The number of elements to initialise the length of the list to.
        @type elements:         None or int
        """

        # Initialise a length.
        for i in range(elements):
            self._append(None)


    def __setitem__(self, slice_obj, value):
        """This is a read-only object!"""

        raise RelaxError("The diffusion tensor is a read-only object.  The diffusion tensor set() method must be used instead.")


    def _append(self, value):
        """The secret append method.

        @param value:   The value to append to the list.
        @type value:    anything
        """

        # Execute the base class method.
        super(DiffTensorSimList, self).append(value)


    def _set(self, value=None, sim_index=None):
        """Replacement secret method for __setitem__().

        @keyword value:     The value to set.
        @type value:        anything
        @keyword sim_index: The index of the simulation value to set.
        @type sim_index:    int
        """

        # Execute the base class method.
        super(DiffTensorSimList, self).__setitem__(sim_index, value)


    def append(self, value):
        """This is a read-only object!"""

        raise RelaxError("The diffusion tensor is a read-only object.  The diffusion tensor set() method must be used instead.")
