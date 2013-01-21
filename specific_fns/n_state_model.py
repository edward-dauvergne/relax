###############################################################################
#                                                                             #
# Copyright (C) 2007-2013 Edward d'Auvergne                                   #
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
"""Module for the specific analysis of the N-state dynamic model."""

# Python module imports.
from copy import deepcopy
from math import acos, cos, pi
from minfx.generic import generic_minimise
from minfx.grid import grid
from numpy import array, dot, float64, identity, ones, zeros
from numpy.linalg import inv, norm
from re import search
from warnings import warn

# relax module imports.
import arg_check
from float import isNaN, isInf
from generic_fns import align_tensor, pcs, pipes, rdc
from generic_fns.interatomic import interatomic_loop
from generic_fns.mol_res_spin import return_spin, spin_loop
from generic_fns.structure import geometric
from generic_fns.structure.cones import Iso_cone
from generic_fns.structure.internal import Internal
from generic_fns.structure.mass import centre_of_mass
from maths_fns.n_state_model import N_state_opt
from maths_fns.potential import quad_pot
from maths_fns.rotation_matrix import euler_to_R_zyz, two_vect_to_R
from physical_constants import dipolar_constant, g1H, return_gyromagnetic_ratio
from relax_errors import RelaxError, RelaxInfError, RelaxNaNError, RelaxNoModelError, RelaxNoValueError, RelaxSpinTypeError
from relax_io import open_write_file
from relax_warnings import RelaxWarning
from specific_fns.api_base import API_base
from specific_fns.api_common import API_common
from user_functions.data import Uf_tables; uf_tables = Uf_tables()
from user_functions.objects import Desc_container


class N_state_model(API_base, API_common):
    """Class containing functions for the N-state model."""

    def __init__(self):
        """Initialise the class by placing API_common methods into the API."""

        # Execute the base class __init__ method.
        super(N_state_model, self).__init__()

        # Place methods into the API.
        self.model_loop = self._model_loop_single_global
        self.overfit_deselect = self._overfit_deselect_dummy
        self.return_conversion_factor = self._return_no_conversion_factor
        self.set_selected_sim = self._set_selected_sim_global
        self.sim_return_selected = self._sim_return_selected_global
        self.test_grid_ops = self._test_grid_ops_general

        # Set up the spin parameters.
        self.PARAMS.add('csa', scope='spin', units='ppm', desc='CSA value', py_type=float, grace_string='\\qCSA\\Q')

        # Add the minimisation data.
        self.PARAMS.add_min_data(min_stats_global=False, min_stats_spin=True)


    def _assemble_param_vector(self, sim_index=None):
        """Assemble all the parameters of the model into a single array.

        @param sim_index:       The index of the simulation to optimise.  This should be None if normal optimisation is desired.
        @type sim_index:        None or int
        @return:                The parameter vector used for optimisation.
        @rtype:                 numpy array
        """

        # Test if the model is selected.
        if not hasattr(cdp, 'model') or not isinstance(cdp.model, str):
            raise RelaxNoModelError

        # Determine the data type.
        data_types = self._base_data_types()

        # Initialise the parameter vector.
        param_vector = []

        # A RDC or PCS data type requires the alignment tensors to be at the start of the parameter vector (unless the tensors are fixed).
        if ('rdc' in data_types or 'pcs' in data_types) and not align_tensor.all_tensors_fixed():
            # Loop over the alignments, adding the alignment tensor parameters to the parameter vector.
            for i in range(len(cdp.align_tensors)):
                # No alignment ID, so skip the tensor as it will not be optimised.
                if cdp.align_tensors[i].name not in cdp.align_ids:
                    continue

                # Fixed tensor.
                if cdp.align_tensors[i].fixed:
                    continue

                # Add the parameters.
                param_vector = param_vector + list(cdp.align_tensors[i].A_5D)

        # Monte Carlo simulation data structures.
        if sim_index != None:
            # Populations.
            if cdp.model in ['2-domain', 'population']:
                probs = cdp.probs_sim[sim_index]

            # Euler angles.
            if cdp.model == '2-domain':
                alpha = cdp.alpha_sim[sim_index]
                beta = cdp.beta_sim[sim_index]
                gamma = cdp.gamma_sim[sim_index]

        # Normal data structures.
        else:
            # Populations.
            if cdp.model in ['2-domain', 'population']:
                probs = cdp.probs

            # Euler angles.
            if cdp.model == '2-domain':
                alpha = cdp.alpha
                beta = cdp.beta
                gamma = cdp.gamma

        # The probabilities (exclude that of state N).
        if cdp.model in ['2-domain', 'population']:
            param_vector = param_vector + probs[0:-1]

        # The Euler angles.
        if cdp.model == '2-domain':
            for i in range(cdp.N):
                param_vector.append(alpha[i])
                param_vector.append(beta[i])
                param_vector.append(gamma[i])

        # The paramagnetic centre.
        if hasattr(cdp, 'paramag_centre_fixed') and not cdp.paramag_centre_fixed:
            if not hasattr(cdp, 'paramagnetic_centre'):
                param_vector.append(0.0)
                param_vector.append(0.0)
                param_vector.append(0.0)

            elif sim_index != None:
                param_vector.append(cdp.paramagnetic_centre_sim[sim_index][0])
                param_vector.append(cdp.paramagnetic_centre_sim[sim_index][1])
                param_vector.append(cdp.paramagnetic_centre_sim[sim_index][2])

            else:
                param_vector.append(cdp.paramagnetic_centre[0])
                param_vector.append(cdp.paramagnetic_centre[1])
                param_vector.append(cdp.paramagnetic_centre[2])

        # Convert all None values to zero (to avoid conversion to NaN).
        for i in range(len(param_vector)):
            if param_vector[i] == None:
                param_vector[i] = 0.0

        # Return a numpy arrary.
        return array(param_vector, float64)


    def _assemble_scaling_matrix(self, data_types=None, scaling=True):
        """Create and return the scaling matrix.

        @keyword data_types:    The base data types used in the optimisation.  This list can contain
                                the elements 'rdc', 'pcs' or 'tensor'.
        @type data_types:       list of str
        @keyword scaling:       If False, then the identity matrix will be returned.
        @type scaling:          bool
        @return:                The square and diagonal scaling matrix.
        @rtype:                 numpy rank-2 array
        """

        # Initialise.
        scaling_matrix = identity(self._param_num(), float64)

        # Return the identity matrix.
        if not scaling:
            return scaling_matrix

        # Starting point of the populations.
        pop_start = 0
        if ('rdc' in data_types or 'pcs' in data_types) and not align_tensor.all_tensors_fixed():
            # Loop over the alignments.
            tensor_num = 0
            for i in range(len(cdp.align_tensors)):
                # Fixed tensor.
                if cdp.align_tensors[i].fixed:
                    continue

                # Add the 5 alignment parameters.
                pop_start = pop_start + 5

                # The alignment parameters.
                for j in range(5):
                    scaling_matrix[5*tensor_num + j, 5*tensor_num + j] = 1.0

                # Increase the tensor number.
                tensor_num += 1

        # Loop over the populations, and set the scaling factor.
        if cdp.model in ['2-domain', 'population']:
            factor = 0.1
            for i in range(pop_start, pop_start + (cdp.N-1)):
                scaling_matrix[i, i] = factor

        # The paramagnetic centre.
        if hasattr(cdp, 'paramag_centre_fixed') and not cdp.paramag_centre_fixed:
            for i in range(-3, 0):
                scaling_matrix[i, i] = 1e2

        # Return the matrix.
        return scaling_matrix


    def _base_data_types(self):
        """Determine all the base data types.

        The base data types can include::
            - 'rdc', residual dipolar couplings.
            - 'pcs', pseudo-contact shifts.
            - 'noesy', NOE restraints.
            - 'tensor', alignment tensors.

        @return:    A list of all the base data types.
        @rtype:     list of str
        """

        # Array of data types.
        list = []

        # RDC search.
        for interatom in interatomic_loop():
            if hasattr(interatom, 'rdc'):
                list.append('rdc')
                break

        # PCS search.
        for spin in spin_loop():
            if hasattr(spin, 'pcs'):
                list.append('pcs')
                break

        # Alignment tensor search.
        if not ('rdc' in list or 'pcs' in list) and hasattr(cdp, 'align_tensors'):
            list.append('tensor')

        # NOESY data search.
        if hasattr(cdp, 'noe_restraints'):
            list.append('noesy')

        # No data is present.
        if not list:
            raise RelaxError("Neither RDC, PCS, NOESY nor alignment tensor data is present.")

        # Return the list.
        return list


    def _calc_ave_dist(self, atom1, atom2, exp=1):
        """Calculate the average distances.

        The formula used is::

                      _N_
                  / 1 \                  \ 1/exp
            <r> = | -  > |p1i - p2i|^exp |
                  \ N /__                /
                       i

        where i are the members of the ensemble, N is the total number of structural models, and p1
        and p2 at the two atom positions.


        @param atom1:   The atom identification string of the first atom.
        @type atom1:    str
        @param atom2:   The atom identification string of the second atom.
        @type atom2:    str
        @keyword exp:   The exponent used for the averaging, e.g. 1 for linear averaging and -6 for
                        r^-6 NOE averaging.
        @type exp:      int
        @return:        The average distance between the two atoms.
        @rtype:         float
        """

        # Get the spin containers.
        spin1 = return_spin(atom1)
        spin2 = return_spin(atom2)

        # Loop over each model.
        num_models = len(spin1.pos)
        ave_dist = 0.0
        for i in range(num_models):
            # Distance to the minus sixth power.
            dist = norm(spin1.pos[i] - spin2.pos[i])
            ave_dist = ave_dist + dist**(exp)

        # Average.
        ave_dist = ave_dist / num_models

        # The exponent.
        ave_dist = ave_dist**(1.0/exp)

        # Return the average distance.
        return ave_dist


    def _CoM(self, pivot_point=None, centre=None):
        """Centre of mass analysis.

        This function does an analysis of the centre of mass (CoM) of the N states.  This includes
        calculating the order parameter associated with the pivot-CoM vector, and the associated
        cone of motions.  The pivot_point argument must be supplied.  If centre is None, then the
        CoM will be calculated from the selected parts of the loaded structure.  Otherwise it will
        be set to the centre arg.

        @param pivot_point: The pivot point in the structural file(s).
        @type pivot_point:  list of float of length 3
        @param centre:      The optional centre of mass vector.
        @type centre:       list of float of length 3
        """

        # Test if the current data pipe exists.
        pipes.test()

        # Set the pivot point.
        cdp.pivot_point = pivot_point

        # The centre has been supplied.
        if centre:
            cdp.CoM = centre

        # Calculate from the structure file.
        else:
            cdp.CoM = centre_of_mass()

        # Calculate the vector between the pivot and CoM points.
        cdp.pivot_CoM = array(cdp.CoM, float64) - array(cdp.pivot_point, float64)

        # Calculate the unit vector between the pivot and CoM points.
        unit_vect = cdp.pivot_CoM / norm(cdp.pivot_CoM)

        # Initilise some data structures.
        R = zeros((3, 3), float64)
        vectors = zeros((cdp.N, 3), float64)

        # Loop over the N states.
        for c in range(cdp.N):
            # Generate the rotation matrix.
            euler_to_R_zyz(cdp.alpha[c], cdp.beta[c], cdp.gamma[c], R)

            # Rotate the unit vector.
            vectors[c] = dot(R, unit_vect)

            # Multiply by the probability.
            vectors[c] = vectors[c] * cdp.probs[c]

        # Average of the unit vectors.
        cdp.ave_unit_pivot_CoM = sum(vectors)

        # The length reduction.
        cdp.ave_pivot_CoM_red = norm(cdp.ave_unit_pivot_CoM)

        # The aveage pivot-CoM vector.
        cdp.ave_pivot_CoM = norm(cdp.pivot_CoM) * cdp.ave_unit_pivot_CoM

        # The full length rotated pivot-CoM vector.
        cdp.full_ave_pivot_CoM = cdp.ave_pivot_CoM / cdp.ave_pivot_CoM_red

        # The cone angle for diffusion on an axially symmetric cone.
        cdp.theta_diff_on_cone = acos(cdp.ave_pivot_CoM_red)
        cdp.S_diff_on_cone = (3.0*cos(cdp.theta_diff_on_cone)**2 - 1.0) / 2.0

        # The cone angle and order parameter for diffusion in an axially symmetric cone.
        cdp.theta_diff_in_cone = acos(2.*cdp.ave_pivot_CoM_red - 1.)
        cdp.S_diff_in_cone = cos(cdp.theta_diff_in_cone) * (1 + cos(cdp.theta_diff_in_cone)) / 2.0

        # Print out.
        print("\n%-40s %-20s" % ("Pivot point:", repr(cdp.pivot_point)))
        print("%-40s %-20s" % ("Moving domain CoM (prior to rotation):", repr(cdp.CoM)))
        print("%-40s %-20s" % ("Pivot-CoM vector", repr(cdp.pivot_CoM)))
        print("%-40s %-20s" % ("Pivot-CoM unit vector:", repr(unit_vect)))
        print("%-40s %-20s" % ("Average of the unit pivot-CoM vectors:", repr(cdp.ave_unit_pivot_CoM)))
        print("%-40s %-20s" % ("Average of the pivot-CoM vector:", repr(cdp.ave_pivot_CoM)))
        print("%-40s %-20s" % ("Full length rotated pivot-CoM vector:", repr(cdp.full_ave_pivot_CoM)))
        print("%-40s %-20s" % ("Length reduction from unity:", repr(cdp.ave_pivot_CoM_red)))
        print("%-40s %.5f rad (%.5f deg)" % ("Cone angle (diffusion on a cone)", cdp.theta_diff_on_cone, cdp.theta_diff_on_cone / (2*pi) *360.))
        print("%-40s S_cone = %.5f (S^2 = %.5f)" % ("S_cone (diffusion on a cone)", cdp.S_diff_on_cone, cdp.S_diff_on_cone**2))
        print("%-40s %.5f rad (%.5f deg)" % ("Cone angle (diffusion in a cone)", cdp.theta_diff_in_cone, cdp.theta_diff_in_cone / (2*pi) *360.))
        print("%-40s S_cone = %.5f (S^2 = %.5f)" % ("S_cone (diffusion in a cone)", cdp.S_diff_in_cone, cdp.S_diff_in_cone**2))
        print("\n\n")


    def _check_rdcs(self, interatom, spin1, spin2):
        """Check if the RDCs for the given interatomic data container should be used.

        @param interatom:   The interatomic data container.
        @type interatom:    InteratomContainer instance
        @param spin1:       The first spin container.
        @type spin1:        SpinContainer instance
        @param spin2:       The second spin container.
        @type spin2:        SpinContainer instance
        @return:            True if the RDCs should be used, False otherwise.
        """

        # Skip deselected spins.
        if not spin1.select or not spin2.select:
            return False

        # Only use interatomic data containers with RDC data.
        if not hasattr(interatom, 'rdc'):
            return False

        # RDC data exists but the interatomic vectors are missing?
        if not hasattr(interatom, 'vector'):
            # Throw a warning.
            warn(RelaxWarning("RDC data exists but the interatomic vectors are missing, skipping the spin pair '%s' and '%s'." % (interatom.spin_id1, interatom.spin_id2)))

            # Jump to the next spin.
            return False

        # Skip non-Me pseudo-atoms for the first spin.
        if hasattr(spin1, 'members') and len(spin1.members) != 3:
            warn(RelaxWarning("Only methyl group pseudo atoms are supported due to their fast rotation, skipping the spin pair '%s' and '%s'." % (interatom.spin_id1, interatom.spin_id2)))
            return False

        # Skip non-Me pseudo-atoms for the second spin.
        if hasattr(spin2, 'members') and len(spin2.members) != 3:
            warn(RelaxWarning("Only methyl group pseudo atoms are supported due to their fast rotation, skipping the spin pair '%s' and '%s'." % (interatom.spin_id1, interatom.spin_id2)))
            return False

        # Checks.
        if not hasattr(spin1, 'isotope'):
            raise RelaxSpinTypeError(interatom.spin_id1)
        if not hasattr(spin2, 'isotope'):
            raise RelaxSpinTypeError(interatom.spin_id2)
        if not hasattr(interatom, 'r'):
            raise RelaxNoValueError("averaged interatomic distance")

        # Everything is ok.
        return True


    def _cone_pdb(self, cone_type=None, scale=1.0, file=None, dir=None, force=False):
        """Create a PDB file containing a geometric object representing the various cone models.

        Currently the only cone types supported are 'diff in cone' and 'diff on cone'.


        @param cone_type:   The type of cone model to represent.
        @type cone_type:    str
        @param scale:       The size of the geometric object is eqaul to the average pivot-CoM
                            vector length multiplied by this scaling factor.
        @type scale:        float
        @param file:        The name of the PDB file to create.
        @type file:         str
        @param dir:         The name of the directory to place the PDB file into.
        @type dir:          str
        @param force:       Flag which if set to True will cause any pre-existing file to be
                            overwritten.
        @type force:        int
        """

        # Test if the cone models have been determined.
        if cone_type == 'diff in cone':
            if not hasattr(cdp, 'S_diff_in_cone'):
                raise RelaxError("The diffusion in a cone model has not yet been determined.")
        elif cone_type == 'diff on cone':
            if not hasattr(cdp, 'S_diff_on_cone'):
                raise RelaxError("The diffusion on a cone model has not yet been determined.")
        else:
            raise RelaxError("The cone type " + repr(cone_type) + " is unknown.")

        # The number of increments for the filling of the cone objects.
        inc = 20

        # The rotation matrix.
        R = zeros((3, 3), float64)
        two_vect_to_R(array([0, 0, 1], float64), cdp.ave_pivot_CoM/norm(cdp.ave_pivot_CoM), R)

        # The isotropic cone object.
        if cone_type == 'diff in cone':
            angle = cdp.theta_diff_in_cone
        elif cone_type == 'diff on cone':
            angle = cdp.theta_diff_on_cone
        cone = Iso_cone(angle)

        # Create the structural object.
        structure = Internal()

        # Add a structure.
        structure.add_molecule(name='cone')

        # Alias the single molecule from the single model.
        mol = structure.structural_data[0].mol[0]

        # Add the pivot point.
        mol.atom_add(pdb_record='HETATM', atom_num=1, atom_name='R', res_name='PIV', res_num=1, pos=cdp.pivot_point, element='C')

        # Generate the average pivot-CoM vectors.
        print("\nGenerating the average pivot-CoM vectors.")
        sim_vectors = None
        if hasattr(cdp, 'ave_pivot_CoM_sim'):
            sim_vectors = cdp.ave_pivot_CoM_sim
        res_num = geometric.generate_vector_residues(mol=mol, vector=cdp.ave_pivot_CoM, atom_name='Ave', res_name_vect='AVE', sim_vectors=sim_vectors, res_num=2, origin=cdp.pivot_point, scale=scale)

        # Generate the cone outer edge.
        print("\nGenerating the cone outer edge.")
        cap_start_atom = mol.atom_num[-1]+1
        geometric.cone_edge(mol=mol, cone=cone, res_name='CON', res_num=3, apex=cdp.pivot_point, R=R, scale=norm(cdp.pivot_CoM), inc=inc)

        # Generate the cone cap, and stitch it to the cone edge.
        if cone_type == 'diff in cone':
            print("\nGenerating the cone cap.")
            cone_start_atom = mol.atom_num[-1]+1
            geometric.generate_vector_dist(mol=mol, res_name='CON', res_num=3, centre=cdp.pivot_point, R=R, limit_check=cone.limit_check, scale=norm(cdp.pivot_CoM), inc=inc)
            geometric.stitch_cone_to_edge(mol=mol, cone=cone, dome_start=cone_start_atom, edge_start=cap_start_atom+1, inc=inc)

        # Create the PDB file.
        print("\nGenerating the PDB file.")
        pdb_file = open_write_file(file, dir, force=force)
        structure.write_pdb(pdb_file)
        pdb_file.close()


    def _disassemble_param_vector(self, param_vector=None, data_types=None, sim_index=None):
        """Disassemble the parameter vector and place the values into the relevant variables.

        For the 2-domain N-state model, the parameters are stored in the probability and Euler angle data structures.  For the population N-state model, only the probabilities are stored.  If RDCs are present and alignment tensors are optimised, then these are stored as well.

        @keyword data_types:    The base data types used in the optimisation.  This list can contain the elements 'rdc', 'pcs' or 'tensor'.
        @type data_types:       list of str
        @keyword param_vector:  The parameter vector returned from optimisation.
        @type param_vector:     numpy array
        @keyword sim_index:     The index of the simulation to optimise.  This should be None if normal optimisation is desired.
        @type sim_index:        None or int
        """

        # Test if the model is selected.
        if not hasattr(cdp, 'model') or not isinstance(cdp.model, str):
            raise RelaxNoModelError

        # Unpack and strip off the alignment tensor parameters.
        if ('rdc' in data_types or 'pcs' in data_types) and not align_tensor.all_tensors_fixed():
            # Loop over the alignments, adding the alignment tensor parameters to the tensor data container.
            tensor_num = 0
            for i in range(len(cdp.align_tensors)):
                # No alignment ID, so skip the tensor as it will not be optimised.
                if cdp.align_tensors[i].name not in cdp.align_ids:
                    continue

                # Fixed tensor.
                if cdp.align_tensors[i].fixed:
                    continue

                # Normal tensors.
                if sim_index == None:
                    cdp.align_tensors[i].set(param='Axx', value=param_vector[5*tensor_num])
                    cdp.align_tensors[i].set(param='Ayy', value=param_vector[5*tensor_num+1])
                    cdp.align_tensors[i].set(param='Axy', value=param_vector[5*tensor_num+2])
                    cdp.align_tensors[i].set(param='Axz', value=param_vector[5*tensor_num+3])
                    cdp.align_tensors[i].set(param='Ayz', value=param_vector[5*tensor_num+4])

                # Monte Carlo simulated tensors.
                else:
                    cdp.align_tensors[i].set(param='Axx', value=param_vector[5*tensor_num], category='sim', sim_index=sim_index)
                    cdp.align_tensors[i].set(param='Ayy', value=param_vector[5*tensor_num+1], category='sim', sim_index=sim_index)
                    cdp.align_tensors[i].set(param='Axy', value=param_vector[5*tensor_num+2], category='sim', sim_index=sim_index)
                    cdp.align_tensors[i].set(param='Axz', value=param_vector[5*tensor_num+3], category='sim', sim_index=sim_index)
                    cdp.align_tensors[i].set(param='Ayz', value=param_vector[5*tensor_num+4], category='sim', sim_index=sim_index)

                # Increase the tensor number.
                tensor_num += 1

            # Create a new parameter vector without the tensors.
            param_vector = param_vector[5*tensor_num:]

        # Monte Carlo simulation data structures.
        if sim_index != None:
            # Populations.
            if cdp.model in ['2-domain', 'population']:
                probs = cdp.probs_sim[sim_index]

            # Euler angles.
            if cdp.model == '2-domain':
                alpha = cdp.alpha_sim[sim_index]
                beta = cdp.beta_sim[sim_index]
                gamma = cdp.gamma_sim[sim_index]

        # Normal data structures.
        else:
            # Populations.
            if cdp.model in ['2-domain', 'population']:
                probs = cdp.probs

            # Euler angles.
            if cdp.model == '2-domain':
                alpha = cdp.alpha
                beta = cdp.beta
                gamma = cdp.gamma

        # The probabilities for states 0 to N-1.
        if cdp.model in ['2-domain', 'population']:
            for i in range(cdp.N-1):
                probs[i] = param_vector[i]

            # The probability for state N.
            probs[-1] = 1 - sum(probs[0:-1])

        # The Euler angles.
        if cdp.model == '2-domain':
            for i in range(cdp.N):
                alpha[i] = param_vector[cdp.N-1 + 3*i]
                beta[i] = param_vector[cdp.N-1 + 3*i + 1]
                gamma[i] = param_vector[cdp.N-1 + 3*i + 2]

        # The paramagnetic centre.
        if hasattr(cdp, 'paramag_centre_fixed') and not cdp.paramag_centre_fixed:
            # Create the structure if needed.
            if not hasattr(cdp, 'paramagnetic_centre'):
                cdp.paramagnetic_centre = zeros(3, float64)

            # The position.
            if sim_index == None:
                cdp.paramagnetic_centre[0] = param_vector[-3]
                cdp.paramagnetic_centre[1] = param_vector[-2]
                cdp.paramagnetic_centre[2] = param_vector[-1]

            # Monte Carlo simulated positions.
            else:
                cdp.paramagnetic_centre_sim[sim_index][0] = param_vector[-3]
                cdp.paramagnetic_centre_sim[sim_index][1] = param_vector[-2]
                cdp.paramagnetic_centre_sim[sim_index][2] = param_vector[-1]


    def _elim_no_prob(self):
        """Remove all structures or states which have no probability."""

        # Test if the current data pipe exists.
        pipes.test()

        # Test if the model is setup.
        if not hasattr(cdp, 'model'):
            raise RelaxNoModelError('N-state')

        # Test if there are populations.
        if not hasattr(cdp, 'probs'):
            raise RelaxError("The N-state model populations do not exist.")

        # Create the data structure if needed.
        if not hasattr(cdp, 'select_models'):
            cdp.state_select = [True] * cdp.N

        # Loop over the structures.
        for i in range(len(cdp.N)):
            # No probability.
            if cdp.probs[i] < 1e-5:
                cdp.state_select[i] = False


    def _linear_constraints(self, data_types=None, scaling_matrix=None):
        """Function for setting up the linear constraint matrices A and b.

        Standard notation
        =================

        The N-state model constraints are::

            0 <= pc <= 1,

        where p is the probability and c corresponds to state c.


        Matrix notation
        ===============

        In the notation A.x >= b, where A is an matrix of coefficients, x is an array of parameter
        values, and b is a vector of scalars, these inequality constraints are::

            | 1  0  0 |                   |    0    |
            |         |                   |         |
            |-1  0  0 |                   |   -1    |
            |         |                   |         |
            | 0  1  0 |                   |    0    |
            |         |     |  p0  |      |         |
            | 0 -1  0 |     |      |      |   -1    |
            |         |  .  |  p1  |  >=  |         |
            | 0  0  1 |     |      |      |    0    |
            |         |     |  p2  |      |         |
            | 0  0 -1 |                   |   -1    |
            |         |                   |         |
            |-1 -1 -1 |                   |   -1    |
            |         |                   |         |
            | 1  1  1 |                   |    0    |

        This example is for a 4-state model, the last probability pn is not included as this
        parameter does not exist (because the sum of pc is equal to 1).  The Euler angle parameters
        have been excluded here but will be included in the returned A and b objects.  These
        parameters simply add columns of zero to the A matrix and have no effect on b.  The last two
        rows correspond to the inequality::

            0 <= pN <= 1.

        As::
                    N-1
                    \
            pN = 1 - >  pc,
                    /__
                    c=1

        then::

            -p1 - p2 - ... - p(N-1) >= -1,

             p1 + p2 + ... + p(N-1) >= 0.


        @keyword data_types:        The base data types used in the optimisation.  This list can
                                    contain the elements 'rdc', 'pcs' or 'tensor'.
        @type data_types:           list of str
        @keyword scaling_matrix:    The diagonal scaling matrix.
        @type scaling_matrix:       numpy rank-2 square matrix
        @return:                    The matrices A and b.
        @rtype:                     tuple of len 2 of a numpy rank-2, size NxM matrix and numpy
                                    rank-1, size N array
        """

        # Starting point of the populations.
        pop_start = 0
        if ('rdc' in data_types or 'pcs' in data_types) and not align_tensor.all_tensors_fixed():
            # Loop over the alignments.
            for i in range(len(cdp.align_tensors)):
                # Fixed tensor.
                if cdp.align_tensors[i].fixed:
                    continue

                # Add 5 parameters.
                pop_start += 5

        # Initialisation (0..j..m).
        A = []
        b = []
        zero_array = zeros(self._param_num(), float64)
        i = pop_start
        j = 0

        # Probability parameters.
        if cdp.model in ['2-domain', 'population']:
            # Loop over the prob parameters (N - 1, because the sum of pc is 1).
            for k in range(cdp.N - 1):
                # 0 <= pc <= 1.
                A.append(zero_array * 0.0)
                A.append(zero_array * 0.0)
                A[j][i] = 1.0
                A[j+1][i] = -1.0
                b.append(0.0)
                b.append(-1.0 / scaling_matrix[i, i])
                j = j + 2

                # Increment i.
                i = i + 1

            # Add the inequalities for pN.
            A.append(zero_array * 0.0)
            A.append(zero_array * 0.0)
            for i in range(pop_start, self._param_num()):
                A[-2][i] = -1.0
                A[-1][i] = 1.0
            b.append(-1.0 / scaling_matrix[i, i])
            b.append(0.0)

        # Convert to numpy data structures.
        A = array(A, float64)
        b = array(b, float64)

        # Return the constraint objects.
        return A, b


    def _minimise_bc_data(self, model):
        """Extract and unpack the back calculated data.

        @param model:   The instantiated class containing the target function.
        @type model:    class instance
        """

        # No alignment tensors, so nothing to do.
        if not hasattr(cdp, 'align_tensors'):
            return

        # Loop over each alignment.
        for align_index in range(len(cdp.align_ids)):
            # Fixed tensor.
            if cdp.align_tensors[align_index].fixed:
                continue

            # The alignment ID.
            align_id = cdp.align_ids[align_index]

            # Data flags
            rdc_flag = False
            if hasattr(cdp, 'rdc_ids') and align_id in cdp.rdc_ids:
                rdc_flag = True
            pcs_flag = False
            if hasattr(cdp, 'pcs_ids') and align_id in cdp.pcs_ids:
                pcs_flag = True

            # Spin loop.
            pcs_index = 0
            for spin in spin_loop():
                # Skip deselected spins.
                if not spin.select:
                    continue

                # Spins with PCS data.
                if pcs_flag and hasattr(spin, 'pcs'):
                    # Initialise the data structure if necessary.
                    if not hasattr(spin, 'pcs_bc'):
                        spin.pcs_bc = {}

                    # Add the back calculated PCS (in ppm).
                    spin.pcs_bc[align_id] = model.deltaij_theta[align_index, pcs_index] * 1e6

                    # Increment the data index if the spin container has data.
                    pcs_index = pcs_index + 1

            # Interatomic data container loop.
            rdc_index = 0
            for interatom in interatomic_loop():
                # Get the spins.
                spin1 = return_spin(interatom.spin_id1)
                spin2 = return_spin(interatom.spin_id2)

                # RDC checks.
                if not self._check_rdcs(interatom, spin1, spin2):
                    continue

                # Containers with RDC data.
                if rdc_flag and hasattr(interatom, 'rdc'):
                    # Initialise the data structure if necessary.
                    if not hasattr(interatom, 'rdc_bc'):
                        interatom.rdc_bc = {}

                    # Append the back calculated PCS.
                    interatom.rdc_bc[align_id] = model.Dij_theta[align_index, rdc_index]

                    # Increment the data index if the interatom container has data.
                    rdc_index = rdc_index + 1


    def _minimise_setup_atomic_pos(self, sim_index=None):
        """Set up the atomic position data structures for optimisation using PCSs and PREs as base data sets.

        @keyword sim_index: The index of the simulation to optimise.  This should be None if normal optimisation is desired.
        @type sim_index:    None or int
        @return:            The atomic positions (the first index is the spins, the second is the structures, and the third is the atomic coordinates) and the paramagnetic centre.
        @rtype:             numpy rank-3 array, numpy rank-1 array.
        """

        # Initialise.
        atomic_pos = []

        # Store the atomic positions.
        for spin in spin_loop():
            # Skip deselected spins.
            if not spin.select:
                continue

            # Only use spins with alignment/paramagnetic data.
            if not hasattr(spin, 'pcs') and not hasattr(spin, 'pre'):
                continue

            # The position list.
            if type(spin.pos[0]) in [float, float64]:
                atomic_pos.append([spin.pos])
            else:
                atomic_pos.append(spin.pos)

        # Convert to numpy objects.
        atomic_pos = array(atomic_pos, float64)

        # The paramagnetic centre.
        if hasattr(cdp, 'paramagnetic_centre'):
            if sim_index != None and hasattr(cdp, 'paramag_centre_fixed') and not cdp.paramag_centre_fixed:
                paramag_centre = array(cdp.paramagnetic_centre_sim[sim_index])
            else:
                paramag_centre = array(cdp.paramagnetic_centre)
        else:
            paramag_centre = zeros(3, float64)

        # Return the data structures.
        return atomic_pos, paramag_centre


    def _minimise_setup_pcs(self, sim_index=None):
        """Set up the data structures for optimisation using PCSs as base data sets.

        @keyword sim_index: The index of the simulation to optimise.  This should be None if normal optimisation is desired.
        @type sim_index:    None or int
        @return:            The assembled data structures for using PCSs as the base data for optimisation.  These include:
                                - the PCS values.
                                - the unit vectors connecting the paramagnetic centre (the electron spin) to
                                - the PCS weight.
                                - the nuclear spin.
                                - the pseudocontact shift constants.
        @rtype:             tuple of (numpy rank-2 array, numpy rank-2 array, numpy rank-2 array, numpy rank-1 array, numpy rank-1 array)
        """

        # Data setup tests.
        if not hasattr(cdp, 'paramagnetic_centre') and (hasattr(cdp, 'paramag_centre_fixed') and cdp.paramag_centre_fixed):
            raise RelaxError("The paramagnetic centre has not yet been specified.")
        if not hasattr(cdp, 'temperature'):
            raise RelaxError("The experimental temperatures have not been set.")
        if not hasattr(cdp, 'frq'):
            raise RelaxError("The spectrometer frequencies of the experiments have not been set.")

        # Initialise.
        pcs = []
        pcs_err = []
        pcs_weight = []
        temp = []
        frq = []

        # The PCS data.
        for align_id in cdp.align_ids:
            # No RDC or PCS data, so jump to the next alignment.
            if (hasattr(cdp, 'rdc_ids') and not align_id in cdp.rdc_ids) and (hasattr(cdp, 'pcs_ids') and not align_id in cdp.pcs_ids):
                continue

            # Append empty arrays to the PCS structures.
            pcs.append([])
            pcs_err.append([])
            pcs_weight.append([])

            # Get the temperature for the PCS constant.
            if align_id in cdp.temperature:
                temp.append(cdp.temperature[align_id])

            # The temperature must be given!
            else:
                raise RelaxError("The experimental temperature for the alignment ID '%s' has not been set." % align_id)

            # Get the spectrometer frequency in Tesla units for the PCS constant.
            if align_id in cdp.frq:
                frq.append(cdp.frq[align_id] * 2.0 * pi / g1H)

            # The frequency must be given!
            else:
                raise RelaxError("The spectrometer frequency for the alignment ID '%s' has not been set." % align_id)

            # Spin loop.
            j = 0
            for spin in spin_loop():
                # Skip deselected spins.
                if not spin.select:
                    continue

                # Skip spins without PCS data.
                if not hasattr(spin, 'pcs'):
                    continue

                # Append the PCSs to the list.
                if align_id in spin.pcs.keys():
                    if sim_index != None:
                        pcs[-1].append(spin.pcs_sim[align_id][sim_index])
                    else:
                        pcs[-1].append(spin.pcs[align_id])
                else:
                    pcs[-1].append(None)

                # Append the PCS errors.
                if hasattr(spin, 'pcs_err') and align_id in spin.pcs_err.keys():
                    pcs_err[-1].append(spin.pcs_err[align_id])
                else:
                    pcs_err[-1].append(None)

                # Append the weight.
                if hasattr(spin, 'pcs_weight') and align_id in spin.pcs_weight.keys():
                    pcs_weight[-1].append(spin.pcs_weight[align_id])
                else:
                    pcs_weight[-1].append(1.0)

                # Spin index.
                j = j + 1

        # Convert to numpy objects.
        pcs = array(pcs, float64)
        pcs_err = array(pcs_err, float64)
        pcs_weight = array(pcs_weight, float64)

        # Convert the PCS from ppm to no units.
        pcs = pcs * 1e-6
        pcs_err = pcs_err * 1e-6

        # Return the data structures.
        return pcs, pcs_err, pcs_weight, temp, frq


    def _minimise_setup_rdcs(self, sim_index=None):
        """Set up the data structures for optimisation using RDCs as base data sets.

        @keyword sim_index: The index of the simulation to optimise.  This should be None if normal optimisation is desired.
        @type sim_index:    None or int
        @return:            The assembled data structures for using RDCs as the base data for optimisation.  These include:
                                - rdc, the RDC values.
                                - rdc_err, the RDC errors.
                                - rdc_weight, the RDC weights.
                                - vectors, the interatomic vectors.
                                - rdc_const, the dipolar constants.
                                - absolute, the absolute value flags (as 1's and 0's).
        @rtype:             tuple of (numpy rank-2 array, numpy rank-2 array, numpy rank-2 array, numpy rank-3 array, numpy rank-2 array, numpy rank-2 array)
        """

        # Initialise.
        rdc = []
        rdc_err = []
        rdc_weight = []
        unit_vect = []
        rdc_const = []
        absolute = []

        # The unit vectors and RDC constants.
        for interatom in interatomic_loop():
            # Get the spins.
            spin1 = return_spin(interatom.spin_id1)
            spin2 = return_spin(interatom.spin_id2)

            # RDC checks.
            if not self._check_rdcs(interatom, spin1, spin2):
                continue

            # Add the vectors.
            if arg_check.is_float(interatom.vector[0], raise_error=False):
                unit_vect.append([interatom.vector])
            else:
                unit_vect.append(interatom.vector)

            # Gyromagnetic ratios.
            g1 = return_gyromagnetic_ratio(spin1.isotope)
            g2 = return_gyromagnetic_ratio(spin2.isotope)

            # Calculate the RDC dipolar constant (in Hertz, and the 3 comes from the alignment tensor), and append it to the list.
            rdc_const.append(3.0/(2.0*pi) * dipolar_constant(g1, g2, interatom.r))

        # Fix the unit vector data structure.
        num = None
        for rdc_index in range(len(unit_vect)):
            # Number of vectors.
            if num == None:
                if unit_vect[rdc_index] != None:
                    num = len(unit_vect[rdc_index])
                continue

            # Check.
            if unit_vect[rdc_index] != None and len(unit_vect[rdc_index]) != num:
                raise RelaxError("The number of interatomic vectors for all no match:\n%s" % unit_vect)

        # Missing unit vectors.
        if num == None:
            raise RelaxError("No interatomic vectors could be found.")

        # Update None entries.
        for i in range(len(unit_vect)):
            if unit_vect[i] == None:
                unit_vect[i] = [[None, None, None]]*num

        # The RDC data.
        for align_id in cdp.align_ids:
            # No RDC or PCS data, so jump to the next alignment.
            if (hasattr(cdp, 'rdc_ids') and not align_id in cdp.rdc_ids) and (hasattr(cdp, 'pcs_ids') and not align_id in cdp.pcs_ids):
                continue

            # Append empty arrays to the RDC structures.
            rdc.append([])
            rdc_err.append([])
            rdc_weight.append([])
            absolute.append([])

            # Interatom loop.
            for interatom in interatomic_loop():
                # Get the spins.
                spin1 = return_spin(interatom.spin_id1)
                spin2 = return_spin(interatom.spin_id2)

                # Skip deselected spins.
                if not spin1.select or not spin2.select:
                    continue

                # Only use interatomic data containers with RDC and vector data.
                if not hasattr(interatom, 'rdc') or not hasattr(interatom, 'vector'):
                    continue

                # Defaults of None.
                value = None
                error = None

                # Pseudo-atom set up.
                if (hasattr(spin1, 'members') or hasattr(spin2, 'members')) and align_id in interatom.rdc.keys():
                    # Skip non-Me groups.
                    if (hasattr(spin1, 'members') and len(spin1.members) != 3) or (hasattr(spin2, 'members') and len(spin2.members) != 3):
                        continue

                    # The RDC for the Me-pseudo spin where:
                    #     <D> = -1/3 Dpar.
                    # See Verdier, et al., JMR, 2003, 163, 353-359.
                    if sim_index != None:
                        value = -3.0 * interatom.rdc_sim[align_id][sim_index]
                    else:
                        value = -3.0 * interatom.rdc[align_id]

                    # The error.
                    if hasattr(interatom, 'rdc_err') and align_id in interatom.rdc_err.keys():
                        error = -3.0 * interatom.rdc_err[align_id]

                # Normal set up.
                elif align_id in interatom.rdc.keys():
                    # The RDC.
                    if sim_index != None:
                        value = interatom.rdc_sim[align_id][sim_index]
                    else:
                        value = interatom.rdc[align_id]

                    # The error.
                    if hasattr(interatom, 'rdc_err') and align_id in interatom.rdc_err.keys():
                        error = interatom.rdc_err[align_id]

                # Append the RDCs to the list.
                rdc[-1].append(value)

                # Append the RDC errors.
                rdc_err[-1].append(error)

                # Append the weight.
                if hasattr(interatom, 'rdc_weight') and align_id in interatom.rdc_weight.keys():
                    rdc_weight[-1].append(interatom.rdc_weight[align_id])
                else:
                    rdc_weight[-1].append(1.0)

                # Append the absolute value flag.
                if hasattr(interatom, 'absolute_rdc') and align_id in interatom.absolute_rdc.keys():
                    absolute[-1].append(interatom.absolute_rdc[align_id])
                else:
                    absolute[-1].append(False)

        # Convert to numpy objects.
        rdc = array(rdc, float64)
        rdc_err = array(rdc_err, float64)
        rdc_weight = array(rdc_weight, float64)
        unit_vect = array(unit_vect, float64)
        rdc_const = array(rdc_const, float64)
        absolute = array(absolute, float64)

        # Return the data structures.
        return rdc, rdc_err, rdc_weight, unit_vect, rdc_const, absolute


    def _minimise_setup_tensors(self, sim_index=None):
        """Set up the data structures for optimisation using alignment tensors as base data sets.

        @keyword sim_index: The index of the simulation to optimise.  This should be None if
                            normal optimisation is desired.
        @type sim_index:    None or int
        @return:            The assembled data structures for using alignment tensors as the base
                            data for optimisation.  These include:
                                - full_tensors, the data of the full alignment tensors.
                                - red_tensor_elem, the tensors as concatenated rank-1 5D arrays.
                                - red_tensor_err, the tensor errors as concatenated rank-1 5D
                                arrays.
                                - full_in_ref_frame, flags specifying if the tensor in the reference
                                frame is the full or reduced tensor.
        @rtype:             tuple of (list, numpy rank-1 array, numpy rank-1 array, numpy rank-1
                            array)
        """

        # Initialise.
        n = len(cdp.align_tensors.reduction)
        full_tensors = zeros(n*5, float64)
        red_tensors  = zeros(n*5, float64)
        red_err = ones(n*5, float64) * 1e-5
        full_in_ref_frame = zeros(n, float64)

        # Loop over the full tensors.
        for i, tensor in self._tensor_loop(red=False):
            # The full tensor.
            full_tensors[5*i + 0] = tensor.Axx
            full_tensors[5*i + 1] = tensor.Ayy
            full_tensors[5*i + 2] = tensor.Axy
            full_tensors[5*i + 3] = tensor.Axz
            full_tensors[5*i + 4] = tensor.Ayz

            # The full tensor corresponds to the frame of reference.
            if cdp.ref_domain == tensor.domain:
                full_in_ref_frame[i] = 1

        # Loop over the reduced tensors.
        for i, tensor in self._tensor_loop(red=True):
            # The reduced tensor (simulation data).
            if sim_index != None:
                red_tensors[5*i + 0] = tensor.Axx_sim[sim_index]
                red_tensors[5*i + 1] = tensor.Ayy_sim[sim_index]
                red_tensors[5*i + 2] = tensor.Axy_sim[sim_index]
                red_tensors[5*i + 3] = tensor.Axz_sim[sim_index]
                red_tensors[5*i + 4] = tensor.Ayz_sim[sim_index]

            # The reduced tensor.
            else:
                red_tensors[5*i + 0] = tensor.Axx
                red_tensors[5*i + 1] = tensor.Ayy
                red_tensors[5*i + 2] = tensor.Axy
                red_tensors[5*i + 3] = tensor.Axz
                red_tensors[5*i + 4] = tensor.Ayz

            # The reduced tensor errors.
            if hasattr(tensor, 'Axx_err'):
                red_err[5*i + 0] = tensor.Axx_err
                red_err[5*i + 1] = tensor.Ayy_err
                red_err[5*i + 2] = tensor.Axy_err
                red_err[5*i + 3] = tensor.Axz_err
                red_err[5*i + 4] = tensor.Ayz_err

        # Return the data structures.
        return full_tensors, red_tensors, red_err, full_in_ref_frame


    def _minimise_setup_fixed_tensors(self):
        """Set up the data structures for the fixed alignment tensors.

        @return:            The assembled data structures for the fixed alignment tensors.
        @rtype:             numpy rank-1 array.
        """

        # Initialise.
        n = align_tensor.num_tensors(skip_fixed=False) - align_tensor.num_tensors(skip_fixed=True)
        tensors = zeros(n*5, float64)

        # Nothing to do.
        if n == 0:
            return None

        # Loop over the tensors.
        index = 0
        for i in range(len(cdp.align_tensors)):
            # Skip unfixed tensors.
            if not cdp.align_tensors[i].fixed:
                continue

            # The real tensors.
            tensors[5*index + 0] = cdp.align_tensors[i].Axx
            tensors[5*index + 1] = cdp.align_tensors[i].Ayy
            tensors[5*index + 2] = cdp.align_tensors[i].Axy
            tensors[5*index + 3] = cdp.align_tensors[i].Axz
            tensors[5*index + 4] = cdp.align_tensors[i].Ayz

            # Increment the index.
            index += 1

        # Return the data structure.
        return tensors


    def _num_data_points(self):
        """Determine the number of data points used in the model.

        @return:    The number, n, of data points in the model.
        @rtype:     int
        """

        # Determine the data type.
        data_types = self._base_data_types()

        # Init.
        n = 0

        # Spin loop.
        for spin in spin_loop():
            # Skip deselected spins.
            if not spin.select:
                continue

            # PCS data (skipping array elements set to None).
            if 'pcs' in data_types:
                if hasattr(spin, 'pcs'):
                    for pcs in spin.pcs:
                        if isinstance(pcs, float):
                            n = n + 1

        # Interatomic data loop.
        for interatom in interatomic_loop():
            # RDC data (skipping array elements set to None).
            if 'rdc' in data_types:
                if hasattr(interatom, 'rdc'):
                    for rdc in interatom.rdc:
                        if isinstance(rdc, float):
                            n = n + 1

        # Alignment tensors.
        if 'tensor' in data_types:
            n = n + 5*len(cdp.align_tensors)

        # Return the value.
        return n


    def _number_of_states(self, N=None):
        """Set the number of states in the N-state model.

        @param N:   The number of states.
        @type N:    int
        """

        # Test if the current data pipe exists.
        pipes.test()

        # Test if the model is setup.
        if not hasattr(cdp, 'model'):
            raise RelaxNoModelError('N-state')

        # Set the value of N.
        cdp.N = N

        # Update the model.
        self._update_model()


    def _param_model_index(self, param):
        """Return the N-state model index for the given parameter.

        @param param:   The N-state model parameter.
        @type param:    str
        @return:        The N-state model index.
        @rtype:         str
        """

        # Probability.
        if search('^p[0-9]*$', param):
            return int(param[1:])

        # Alpha Euler angle.
        if search('^alpha', param):
            return int(param[5:])

        # Beta Euler angle.
        if search('^beta', param):
            return int(param[4:])

        # Gamma Euler angle.
        if search('^gamma', param):
            return int(param[5:])

        # Model independent parameter.
        return None


    def _param_num(self):
        """Determine the number of parameters in the model.

        @return:    The number of model parameters.
        @rtype:     int
        """

        # Determine the data type.
        data_types = self._base_data_types()

        # Init.
        num = 0

        # Alignment tensor params.
        if ('rdc' in data_types or 'pcs' in data_types) and not align_tensor.all_tensors_fixed():
            # Loop over the alignments.
            for i in range(len(cdp.align_tensors)):
                # No alignment ID, so skip the tensor as it is not part of the parameter set.
                if cdp.align_tensors[i].name not in cdp.align_ids:
                    continue

                # Fixed tensor.
                if cdp.align_tensors[i].fixed:
                    continue

                # Add 5 tensor parameters.
                num += 5

        # Populations.
        if cdp.model in ['2-domain', 'population']:
            num = num + (cdp.N - 1)

        # Euler angles.
        if cdp.model == '2-domain':
            num = num + 3*cdp.N

        # The paramagnetic centre.
        if hasattr(cdp, 'paramag_centre_fixed') and not cdp.paramag_centre_fixed:
            num = num + 3

         # Return the param number.
        return num


    def _ref_domain(self, ref=None):
        """Set the reference domain for the '2-domain' N-state model.

        @param ref: The reference domain.
        @type ref:  str
        """

        # Test if the current data pipe exists.
        pipes.test()

        # Test if the model is setup.
        if not hasattr(cdp, 'model'):
            raise RelaxNoModelError('N-state')

        # Test that the correct model is set.
        if cdp.model != '2-domain':
            raise RelaxError("Setting the reference domain is only possible for the '2-domain' N-state model.")

        # Test if the reference domain exists.
        exists = False
        for tensor_cont in cdp.align_tensors:
            if tensor_cont.domain == ref:
                exists = True
        if not exists:
            raise RelaxError("The reference domain cannot be found within any of the loaded tensors.")

        # Set the reference domain.
        cdp.ref_domain = ref

        # Update the model.
        self._update_model()


    def _select_model(self, model=None):
        """Select the N-state model type.

        @param model:   The N-state model type.  Can be one of '2-domain', 'population', or 'fixed'.
        @type model:    str
        """

        # Test if the current data pipe exists.
        pipes.test()

        # Test if the model name exists.
        if not model in ['2-domain', 'population', 'fixed']:
            raise RelaxError("The model name " + repr(model) + " is invalid.")

        # Test if the model is setup.
        if hasattr(cdp, 'model'):
            warn(RelaxWarning("The N-state model has already been set up.  Switching from model '%s' to '%s'." % (cdp.model, model)))

        # Set the model
        cdp.model = model

        # Initialise the list of model parameters.
        cdp.params = []

        # Update the model.
        self._update_model()


    def _target_fn_setup(self, sim_index=None, scaling=True):
        """Initialise the target function for optimisation or direct calculation.

        @param sim_index:       The index of the simulation to optimise.  This should be None if normal optimisation is desired.
        @type sim_index:        None or int
        @param scaling:         If True, diagonal scaling is enabled during optimisation to allow the problem to be better conditioned.
        @type scaling:          bool
        """

        # Test if the N-state model has been set up.
        if not hasattr(cdp, 'model'):
            raise RelaxNoModelError('N-state')

        # '2-domain' model setup tests.
        if cdp.model == '2-domain':
            # The number of states.
            if not hasattr(cdp, 'N'):
                raise RelaxError("The number of states has not been set.")

            # The reference domain.
            if not hasattr(cdp, 'ref_domain'):
                raise RelaxError("The reference domain has not been set.")

        # Update the model parameters if necessary.
        self._update_model()

        # Create the initial parameter vector.
        param_vector = self._assemble_param_vector(sim_index=sim_index)

        # Determine if alignment tensors or RDCs are to be used.
        data_types = self._base_data_types()

        # The probabilities.
        probs = None
        if hasattr(cdp, 'probs'):
            probs = cdp.probs

        # Diagonal scaling.
        scaling_matrix = None
        if len(param_vector):
            scaling_matrix = self._assemble_scaling_matrix(data_types=data_types, scaling=scaling)
            param_vector = dot(inv(scaling_matrix), param_vector)

        # Get the data structures for optimisation using the tensors as base data sets.
        full_tensors, red_tensor_elem, red_tensor_err, full_in_ref_frame = None, None, None, None
        if 'tensor' in data_types:
            full_tensors, red_tensor_elem, red_tensor_err, full_in_ref_frame = self._minimise_setup_tensors(sim_index=sim_index)

        # Get the data structures for optimisation using PCSs as base data sets.
        pcs, pcs_err, pcs_weight, temp, frq = None, None, None, None, None
        if 'pcs' in data_types:
            pcs, pcs_err, pcs_weight, temp, frq = self._minimise_setup_pcs(sim_index=sim_index)

        # Get the data structures for optimisation using RDCs as base data sets.
        rdcs, rdc_err, rdc_weight, rdc_vector, rdc_dj, absolute_rdc = None, None, None, None, None, None
        if 'rdc' in data_types:
            rdcs, rdc_err, rdc_weight, rdc_vector, rdc_dj, absolute_rdc = self._minimise_setup_rdcs(sim_index=sim_index)

        # Get the fixed tensors.
        fixed_tensors = None
        if 'rdc' in data_types or 'pcs' in data_types:
            full_tensors = self._minimise_setup_fixed_tensors()

            # The flag list.
            fixed_tensors = []
            for i in range(len(cdp.align_tensors)):
                if cdp.align_tensors[i].fixed:
                    fixed_tensors.append(True)
                else:
                    fixed_tensors.append(False)

        # Get the atomic_positions.
        atomic_pos, paramag_centre, centre_fixed = None, None, True
        if 'pcs' in data_types or 'pre' in data_types:
            atomic_pos, paramag_centre = self._minimise_setup_atomic_pos(sim_index=sim_index)

            # Optimisation of the centre.
            if hasattr(cdp, 'paramag_centre_fixed'):
                centre_fixed = cdp.paramag_centre_fixed

        # Set up the class instance containing the target function.
        model = N_state_opt(model=cdp.model, N=cdp.N, init_params=param_vector, probs=probs, full_tensors=full_tensors, red_data=red_tensor_elem, red_errors=red_tensor_err, full_in_ref_frame=full_in_ref_frame, fixed_tensors=fixed_tensors, pcs=pcs, rdcs=rdcs, pcs_errors=pcs_err, rdc_errors=rdc_err, pcs_weights=pcs_weight, rdc_weights=rdc_weight, rdc_vect=rdc_vector, temp=temp, frq=frq, dip_const=rdc_dj, absolute_rdc=absolute_rdc, atomic_pos=atomic_pos, paramag_centre=paramag_centre, scaling_matrix=scaling_matrix, centre_fixed=centre_fixed)

        # Return the data.
        return model, param_vector, data_types, scaling_matrix


    def _tensor_loop(self, red=False):
        """Generator method for looping over the full or reduced tensors.

        @keyword red:   A flag which if True causes the reduced tensors to be returned, and if False
                        the full tensors are returned.
        @type red:      bool
        @return:        The tensor index and the tensor.
        @rtype:         (int, AlignTensorData instance)
        """

        # Number of tensor pairs.
        n = len(cdp.align_tensors.reduction)

        # Alias.
        data = cdp.align_tensors
        list = data.reduction

        # Full or reduced index.
        if red:
            index = 1
        else:
            index = 0

        # Loop over the reduction list.
        for i in range(n):
            yield i, data[list[i][index]]


    def _update_model(self):
        """Update the model parameters as necessary."""

        # Initialise the list of model parameters.
        if not hasattr(cdp, 'params'):
            cdp.params = []

        # Determine the number of states (loaded as structural models), if not already set.
        if not hasattr(cdp, 'N'):
            # Set the number.
            if hasattr(cdp, 'structure'):
                cdp.N = cdp.structure.num_models()

            # Otherwise return as the rest cannot be updated without N.
            else:
                return

        # Set up the parameter arrays.
        if not cdp.params:
            # Add the probability or population weight parameters.
            if cdp.model in ['2-domain', 'population']:
                for i in range(cdp.N-1):
                    cdp.params.append('p' + repr(i))

            # Add the Euler angle parameters.
            if cdp.model == '2-domain':
                for i in range(cdp.N):
                    cdp.params.append('alpha' + repr(i))
                    cdp.params.append('beta' + repr(i))
                    cdp.params.append('gamma' + repr(i))

        # Initialise the probability and Euler angle arrays.
        if cdp.model in ['2-domain', 'population']:
            if not hasattr(cdp, 'probs'):
                cdp.probs = [None] * cdp.N
        if cdp.model == '2-domain':
            if not hasattr(cdp, 'alpha'):
                cdp.alpha = [None] * cdp.N
            if not hasattr(cdp, 'beta'):
                cdp.beta = [None] * cdp.N
            if not hasattr(cdp, 'gamma'):
                cdp.gamma = [None] * cdp.N

        # Determine the data type.
        data_types = self._base_data_types()

        # Set up tensors for each alignment.
        if hasattr(cdp, 'align_ids'):
            for id in cdp.align_ids:
                # No tensors initialised.
                if not hasattr(cdp, 'align_tensors'):
                    align_tensor.init(tensor=id, params=[0.0, 0.0, 0.0, 0.0, 0.0])

                # Find if the tensor corresponding to the id exists.
                exists = False
                for tensor in cdp.align_tensors:
                    if id == tensor.name:
                        exists = True

                # Initialise the tensor.
                if not exists:
                    align_tensor.init(tensor=id, params=[0.0, 0.0, 0.0, 0.0, 0.0])


    def base_data_loop(self):
        """Loop over the base data of the spins - RDCs, PCSs, and NOESY data.

        This loop iterates for each data point (RDC, PCS, NOESY) for each spin or interatomic data container, returning the identification information.

        @return:            A list of the spin or interatomic data container, the data type ('rdc', 'pcs', 'noesy'), and the alignment ID if required.
        @rtype:             list of [SpinContainer instance, str, str] or [InteratomContainer instance, str, str]
        """

        # Loop over the interatomic data containers.
        for interatom in interatomic_loop():
            # Re-initialise the data structure.
            data = [interatom, None, None]

            # RDC data.
            if hasattr(interatom, 'rdc'):
                data[1] = 'rdc'

                # Loop over the alignment IDs.
                for id in cdp.rdc_ids:
                    # Add the ID.
                    data[2] = id

                    # Yield the set.
                    yield data

            # NOESY data.
            if hasattr(interatom, 'noesy'):
                data[1] = 'noesy'

                # Loop over the alignment IDs.
                for id in cdp.noesy_ids:
                    # Add the ID.
                    data[2] = id

                    # Yield the set.
                    yield data

        # Loop over the spins.
        for spin in spin_loop():
            # Re-initialise the data structure.
            data = [spin, None, None]

            # PCS data.
            if hasattr(spin, 'pcs'):
                data[1] = 'pcs'

                # Loop over the alignment IDs.
                for id in cdp.pcs_ids:
                    # Add the ID.
                    data[2] = id

                    # Yield the set.
                    yield data


    def calculate(self, spin_id=None, verbosity=1, sim_index=None):
        """Calculation function.

        Currently this function simply calculates the NOESY flat-bottom quadratic energy potential,
        if NOE restraints are available.

        @keyword spin_id:   The spin identification string (unused).
        @type spin_id:      None or str
        @keyword verbosity: The amount of information to print.  The higher the value, the greater the verbosity.
        @type verbosity:    int
        @keyword sim_index: The MC simulation index (unused).
        @type sim_index:    None
        """

        # Set up the target function for direct calculation.
        model, param_vector, data_types, scaling_matrix = self._target_fn_setup()

        # Calculate the chi-squared value.
        if model:
            # Make a function call.
            chi2 = model.func(param_vector)

            # Store the global chi-squared value.
            cdp.chi2 = chi2

            # Store the back-calculated data.
            self._minimise_bc_data(model)

            # Calculate the RDC Q-factors.
            if 'rdc' in data_types:
                rdc.q_factors()

            # Calculate the PCS Q-factors.
            if 'pcs' in data_types:
                pcs.q_factors()

        # NOE potential.
        if hasattr(cdp, 'noe_restraints'):
            # Init some numpy arrays.
            num_restraints = len(cdp.noe_restraints)
            dist = zeros(num_restraints, float64)
            pot = zeros(num_restraints, float64)
            lower = zeros(num_restraints, float64)
            upper = zeros(num_restraints, float64)

            # Loop over the NOEs.
            for i in range(num_restraints):
                # Create arrays of the NOEs.
                lower[i] = cdp.noe_restraints[i][2]
                upper[i] = cdp.noe_restraints[i][3]

                # Calculate the average distances, using -6 power averaging.
                dist[i] = self._calc_ave_dist(cdp.noe_restraints[i][0], cdp.noe_restraints[i][1], exp=-6)

            # Calculate the quadratic potential.
            quad_pot(dist, pot, lower, upper)

            # Store the distance and potential information.
            cdp.ave_dist = []
            cdp.quad_pot = []
            for i in range(num_restraints):
                cdp.ave_dist.append([cdp.noe_restraints[i][0], cdp.noe_restraints[i][1], dist[i]])
                cdp.quad_pot.append([cdp.noe_restraints[i][0], cdp.noe_restraints[i][1], pot[i]])


    def create_mc_data(self, data_id=None):
        """Create the Monte Carlo data by back-calculation.

        @keyword data_id:   The list of spin ID, data type, and alignment ID, as yielded by the base_data_loop() generator method.
        @type data_id:      str
        @return:            The Monte Carlo Ri data.
        @rtype:             list of floats
        """

        # Initialise the MC data structure.
        mc_data = []

        # Alias the spin or interatomic data container.
        container = data_id[0]

        # RDC data.
        if data_id[1] == 'rdc' and hasattr(container, 'rdc'):
            # Does back-calculated data exist?
            if not hasattr(container, 'rdc_bc'):
                self.calculate()

            # The data.
            if not hasattr(container, 'rdc_bc') or not data_id[2] in container.rdc_bc:
                data = None
            else:
                data = container.rdc_bc[data_id[2]]

            # Append the data.
            mc_data.append(data)

        # NOESY data.
        elif data_id[1] == 'noesy' and hasattr(container, 'noesy'):
            # Does back-calculated data exist?
            if not hasattr(container, 'noesy_bc'):
                self.calculate()

            # Append the data.
            mc_data.append(container.noesy_bc)

        # PCS data.
        elif data_id[1] == 'pcs' and hasattr(container, 'pcs'):
            # Does back-calculated data exist?
            if not hasattr(container, 'pcs_bc'):
                self.calculate()

            # The data.
            if not hasattr(container, 'pcs_bc') or not data_id[2] in container.pcs_bc:
                data = None
            else:
                data = container.pcs_bc[data_id[2]]

            # Append the data.
            mc_data.append(data)

        # Return the data.
        return mc_data


    default_value_doc = Desc_container("N-state model default values")
    _table = uf_tables.add_table(label="table: N-state default values", caption="N-state model default values.")
    _table.add_headings(["Data type", "Object name", "Value"])
    _table.add_row(["Probabilities", "'p0', 'p1', 'p2', ..., 'pN'", "1/N"])
    _table.add_row(["Euler angle alpha", "'alpha0', 'alpha1', ...", "(c+1) * pi / (N+1)"])
    _table.add_row(["Euler angle beta", "'beta0', 'beta1', ...", "(c+1) * pi / (N+1)"])
    _table.add_row(["Euler angle gamma", "'gamma0', 'gamma1', ...", "(c+1) * pi / (N+1)"])
    default_value_doc.add_table(_table.label)
    default_value_doc.add_paragraph("In this table, N is the total number of states and c is the index of a given state ranging from 0 to N-1.  The default probabilities are all set to be equal whereas the angles are given a range of values so that no 2 states are equal at the start of optimisation.")
    default_value_doc.add_paragraph("Note that setting the probability for state N will do nothing as it is equal to one minus all the other probabilities.")

    def default_value(self, param):
        """The default N-state model parameter values.

        @param param:   The N-state model parameter.
        @type param:    str
        @return:        The default value.
        @rtype:         float
        """

        # Split the parameter into its base name and index.
        name = self.return_data_name(param)
        index = self._param_model_index(param)

        # The number of states as a float.
        N = float(cdp.N)

        # Probability.
        if name == 'probs':
            return 1.0 / N

        # Euler angles.
        elif name == 'alpha' or name == 'beta' or name == 'gamma':
            return (float(index)+1) * pi / (N+1.0)


    def grid_search(self, lower=None, upper=None, inc=None, constraints=False, verbosity=0, sim_index=None):
        """The grid search function.

        @param lower:       The lower bounds of the grid search which must be equal to the number of parameters in the model.
        @type lower:        array of numbers
        @param upper:       The upper bounds of the grid search which must be equal to the number of parameters in the model.
        @type upper:        array of numbers
        @param inc:         The increments for each dimension of the space for the grid search.  The number of elements in the array must equal to the number of parameters in the model.
        @type inc:          array of int
        @param constraints: If True, constraints are applied during the grid search (elinating parts of the grid).  If False, no constraints are used.
        @type constraints:  bool
        @param verbosity:   A flag specifying the amount of information to print.  The higher the value, the greater the verbosity.
        @type verbosity:    int
        """

        # Test if the N-state model has been set up.
        if not hasattr(cdp, 'model'):
            raise RelaxNoModelError('N-state')

        # The number of parameters.
        n = self._param_num()

        # Make sure that the length of the parameter array is > 0.
        if n == 0:
            print("Cannot run a grid search on a model with zero parameters, skipping the grid search.")
            return

        # Test the grid search options.
        self.test_grid_ops(lower=lower, upper=upper, inc=inc, n=n)

        # If inc is a single int, convert it into an array of that value.
        if isinstance(inc, int):
            inc = [inc]*n

        # Setup the default bounds.
        if not lower:
            # Init.
            lower = []
            upper = []

            # Loop over the parameters.
            for i in range(n):
                # i is in the parameter array.
                if i < len(cdp.params):
                    # Probabilities (default values).
                    if search('^p', cdp.params[i]):
                        lower.append(0.0)
                        upper.append(1.0)

                    # Angles (default values).
                    if search('^alpha', cdp.params[i]) or search('^gamma', cdp.params[i]):
                        lower.append(0.0)
                        upper.append(2*pi)
                    elif search('^beta', cdp.params[i]):
                        lower.append(0.0)
                        upper.append(pi)

                # The paramagnetic centre.
                elif hasattr(cdp, 'paramag_centre_fixed') and not cdp.paramag_centre_fixed and (n - i) <= 3:
                    lower.append(-100)
                    upper.append(100)

                # Otherwise this must be an alignment tensor component.
                else:
                    lower.append(-1e-3)
                    upper.append(1e-3)

        # Determine the data type.
        data_types = self._base_data_types()

        # The number of tensors to optimise.
        tensor_num = align_tensor.num_tensors(skip_fixed=True)

        # Custom sub-grid search for when only tensors are optimised (as each tensor is independent, the number of points collapses from inc**(5*N) to N*inc**5).
        if cdp.model == 'fixed' and tensor_num > 1 and ('rdc' in data_types or 'pcs' in data_types) and not align_tensor.all_tensors_fixed() and hasattr(cdp, 'paramag_centre_fixed') and cdp.paramag_centre_fixed:
            # Print out.
            print("Optimising each alignment tensor separately.")

            # Store the alignment tensor fixed flags.
            fixed_flags = []
            for i in range(len(cdp.align_ids)):
                # Get the tensor object.
                tensor = align_tensor.return_tensor(index=i, skip_fixed=False)

                # Store the flag.
                fixed_flags.append(tensor.fixed)

                # Fix the tensor.
                tensor.set('fixed', True)

            # Loop over each sub-grid.
            for i in range(len(cdp.align_ids)):
                # Skip the tensor if originally fixed.
                if fixed_flags[i]:
                    continue

                # Get the tensor object.
                tensor = align_tensor.return_tensor(index=i, skip_fixed=False)

                # Unfix the current tensor.
                tensor.set('fixed', False)

                # Grid search parameter subsets.
                lower_sub = lower[i*5:i*5+5]
                upper_sub = upper[i*5:i*5+5]
                inc_sub = inc[i*5:i*5+5]

                # Minimisation of the sub-grid.
                self.minimise(min_algor='grid', lower=lower_sub, upper=upper_sub, inc=inc_sub, constraints=constraints, verbosity=verbosity, sim_index=sim_index)

                # Fix the tensor again.
                tensor.set('fixed', True)

            # Reset the state of the tensors.
            for i in range(len(cdp.align_ids)):
                # Get the tensor object.
                tensor = align_tensor.return_tensor(index=i, skip_fixed=False)

                # Fix the tensor.
                tensor.set('fixed', fixed_flags[i])

        # All other minimisation.
        else:
            self.minimise(min_algor='grid', lower=lower, upper=upper, inc=inc, constraints=constraints, verbosity=verbosity, sim_index=sim_index)


    def is_spin_param(self, name):
        """Determine whether the given parameter is spin specific.

        @param name:    The name of the parameter.
        @type name:     str
        @return:        False
        @rtype:         bool
        """

        # Spin specific parameters.
        if name in ['r', 'heteronuc_type', 'proton_type']:
            return True

        # All other parameters are global.
        return False


    def map_bounds(self, param, spin_id=None):
        """Create bounds for the OpenDX mapping function.

        @param param:       The name of the parameter to return the lower and upper bounds of.
        @type param:        str
        @param spin_id:     The spin identification string (unused).
        @type spin_id:      None
        @return:            The upper and lower bounds of the parameter.
        @rtype:             list of float
        """

        # Paramagnetic centre.
        if search('^paramag_[xyz]$', param):
            return [-100.0, 100.0]


    def minimise(self, min_algor=None, min_options=None, func_tol=None, grad_tol=None, max_iterations=None, constraints=False, scaling=True, verbosity=0, sim_index=None, lower=None, upper=None, inc=None):
        """Minimisation function.

        @param min_algor:       The minimisation algorithm to use.
        @type min_algor:        str
        @param min_options:     An array of options to be used by the minimisation algorithm.
        @type min_options:      array of str
        @param func_tol:        The function tolerance which, when reached, terminates optimisation. Setting this to None turns of the check.
        @type func_tol:         None or float
        @param grad_tol:        The gradient tolerance which, when reached, terminates optimisation. Setting this to None turns of the check.
        @type grad_tol:         None or float
        @param max_iterations:  The maximum number of iterations for the algorithm.
        @type max_iterations:   int
        @param constraints:     If True, constraints are used during optimisation.
        @type constraints:      bool
        @param scaling:         If True, diagonal scaling is enabled during optimisation to allow the problem to be better conditioned.
        @type scaling:          bool
        @param verbosity:       A flag specifying the amount of information to print.  The higher the value, the greater the verbosity.
        @type verbosity:        int
        @param sim_index:       The index of the simulation to optimise.  This should be None if normal optimisation is desired.
        @type sim_index:        None or int
        @keyword lower:         The lower bounds of the grid search which must be equal to the number of parameters in the model.  This optional argument is only used when doing a grid search.
        @type lower:            array of numbers
        @keyword upper:         The upper bounds of the grid search which must be equal to the number of parameters in the model.  This optional argument is only used when doing a grid search.
        @type upper:            array of numbers
        @keyword inc:           The increments for each dimension of the space for the grid search.  The number of elements in the array must equal to the number of parameters in the model.  This argument is only used when doing a grid search.
        @type inc:              array of int
        """

        # Set up the target function for direct calculation.
        model, param_vector, data_types, scaling_matrix = self._target_fn_setup(sim_index=sim_index, scaling=scaling)

        # Nothing to do!
        if not len(param_vector):
            warn(RelaxWarning("The model has no parameters, minimisation cannot be performed."))
            return

        # Right, constraints cannot be used for the 'fixed' model.
        if constraints and cdp.model == 'fixed':
            warn(RelaxWarning("Turning constraints off.  These cannot be used for the 'fixed' model."))
            constraints = False

            # Pop out the Method of Multipliers algorithm.
            if min_algor == 'Method of Multipliers':
                min_algor = min_options[0]
                min_options = min_options[1:]

        # And constraints absolutely must be used for the 'population' model.
        if not constraints and cdp.model == 'population':
            warn(RelaxWarning("Turning constraints on.  These absolutely must be used for the 'population' model."))
            constraints = True

            # Add the Method of Multipliers algorithm.
            min_options = (min_algor,) + min_options
            min_algor = 'Method of Multipliers'

        # Linear constraints.
        if constraints:
            A, b = self._linear_constraints(data_types=data_types, scaling_matrix=scaling_matrix)
        else:
            A, b = None, None

        # Grid search.
        if search('^[Gg]rid', min_algor):
            # Scaling.
            if scaling:
                for i in range(len(param_vector)):
                    lower[i] = lower[i] / scaling_matrix[i, i]
                    upper[i] = upper[i] / scaling_matrix[i, i]

            # The search.
            results = grid(func=model.func, args=(), num_incs=inc, lower=lower, upper=upper, A=A, b=b, verbosity=verbosity)

            # Unpack the results.
            param_vector, func, iter_count, warning = results
            f_count = iter_count
            g_count = 0.0
            h_count = 0.0

        # Minimisation.
        else:
            results = generic_minimise(func=model.func, dfunc=model.dfunc, d2func=model.d2func, args=(), x0=param_vector, min_algor=min_algor, min_options=min_options, func_tol=func_tol, grad_tol=grad_tol, maxiter=max_iterations, A=A, b=b, full_output=1, print_flag=verbosity)

            # Unpack the results.
            if results == None:
                return
            param_vector, func, iter_count, f_count, g_count, h_count, warning = results

        # Catch infinite chi-squared values.
        if isInf(func):
            raise RelaxInfError('chi-squared')

        # Catch chi-squared values of NaN.
        if isNaN(func):
            raise RelaxNaNError('chi-squared')

        # Make a last function call to update the back-calculated RDC and PCS structures to the optimal values.
        chi2 = model.func(param_vector)

        # Scaling.
        if scaling:
            param_vector = dot(scaling_matrix, param_vector)

        # Disassemble the parameter vector.
        self._disassemble_param_vector(param_vector=param_vector, data_types=data_types, sim_index=sim_index)

        # Monte Carlo minimisation statistics.
        if sim_index != None:
            # Chi-squared statistic.
            cdp.chi2_sim[sim_index] = func

            # Iterations.
            cdp.iter_sim[sim_index] = iter_count

            # Function evaluations.
            cdp.f_count_sim[sim_index] = f_count

            # Gradient evaluations.
            cdp.g_count_sim[sim_index] = g_count

            # Hessian evaluations.
            cdp.h_count_sim[sim_index] = h_count

            # Warning.
            cdp.warning_sim[sim_index] = warning

        # Normal statistics.
        else:
            # Chi-squared statistic.
            cdp.chi2 = func

            # Iterations.
            cdp.iter = iter_count

            # Function evaluations.
            cdp.f_count = f_count

            # Gradient evaluations.
            cdp.g_count = g_count

            # Hessian evaluations.
            cdp.h_count = h_count

            # Warning.
            cdp.warning = warning

        # Statistical analysis.
        if sim_index == None and ('rdc' in data_types or 'pcs' in data_types):
            # Get the final back calculated data (for the Q-factor and
            self._minimise_bc_data(model)

            # Calculate the RDC Q-factors.
            if 'rdc' in data_types:
                rdc.q_factors()

            # Calculate the PCS Q-factors.
            if 'pcs' in data_types:
                pcs.q_factors()


    def model_statistics(self, model_info=None, spin_id=None, global_stats=None):
        """Return the k, n, and chi2 model statistics.

        k - number of parameters.
        n - number of data points.
        chi2 - the chi-squared value.


        @keyword model_info:    The data returned from model_loop() (unused).
        @type model_info:       None
        @keyword spin_id:       The spin identification string.  This is ignored in the N-state model.
        @type spin_id:          None or str
        @keyword global_stats:  A parameter which determines if global or local statistics are returned.  For the N-state model, this argument is ignored.
        @type global_stats:     None or bool
        @return:                The optimisation statistics, in tuple format, of the number of parameters (k), the number of data points (n), and the chi-squared value (chi2).
        @rtype:                 tuple of (int, int, float)
        """

        # Return the values.
        return self._param_num(), self._num_data_points(), cdp.chi2


    return_data_name_doc = Desc_container("N-state model data type string matching patterns")
    _table = uf_tables.add_table(label="table: N-state data type patterns", caption="N-state model data type string matching patterns.")
    _table.add_headings(["Data type", "Object name", "Patterns"])
    _table.add_row(["Probabilities", "'probs'", "'p0', 'p1', 'p2', ..., 'pN'"])
    _table.add_row(["Euler angle alpha", "'alpha'", "'alpha0', 'alpha1', ..."])
    _table.add_row(["Euler angle beta", "'beta'", "'beta0', 'beta1', ..."])
    _table.add_row(["Euler angle gamma", "'gamma'", "'gamma0', 'gamma1', ..."])
    _table.add_row(["Bond length", "'r'", "'^r$' or '[Bb]ond[ -_][Ll]ength'"])
    _table.add_row(["Heteronucleus type", "'heteronuc_type'", "'^[Hh]eteronucleus$'"])
    _table.add_row(["Proton type", "'proton_type'", "'^[Pp]roton$'"])
    return_data_name_doc.add_table(_table.label)
    return_data_name_doc.add_paragraph("The objects corresponding to the object names are lists (or arrays) with each element corrsponding to each state.")

    def return_data_name(self, param):
        """Return a unique identifying string for the N-state model parameter.

        @param param:   The N-state model parameter.
        @type param:    str
        @return:        The unique parameter identifying string.
        @rtype:         str
        """

        # Probability.
        if search('^p[0-9]*$', param):
            return 'probs'

        # Alpha Euler angle.
        if search('^alpha', param):
            return 'alpha'

        # Beta Euler angle.
        if search('^beta', param):
            return 'beta'

        # Gamma Euler angle.
        if search('^gamma', param):
            return 'gamma'

        # Bond length.
        if search('^r$', param) or search('[Bb]ond[ -_][Ll]ength', param):
            return 'r'

        # Heteronucleus type.
        if param == 'heteronuc_type':
            return 'heteronuc_type'

        # Proton type.
        if param == 'proton_type':
            return 'proton_type'

        # Paramagnetic centre.
        if search('^paramag_[xyz]$', param):
            return param


    def return_error(self, data_id=None):
        """Create and return the spin specific Monte Carlo Ri error structure.

        @keyword data_id:   The list of spin ID, data type, and alignment ID, as yielded by the base_data_loop() generator method.
        @type data_id:      str
        @return:            The Monte Carlo simulation data errors.
        @rtype:             list of floats
        """

        # Initialise the MC data structure.
        mc_errors = []

        # Alias the spin or interatomic data container.
        container = data_id[0]

        # Skip deselected spins.
        if data_id[1] == 'pcs' and not container.select:
            return

        # RDC data.
        if data_id[1] == 'rdc' and hasattr(container, 'rdc'):
            # Do errors exist?
            if not hasattr(container, 'rdc_err'):
                raise RelaxError("The RDC errors are missing for the spin pair '%s' and '%s'." % (container.spin_id1, container.spin_id2))

            # The error.
            if data_id[2] not in container.rdc_err:
                err = None
            else:
                err = container.rdc_err[data_id[2]]

            # Append the data.
            mc_errors.append(err)

        # NOESY data.
        elif data_id[1] == 'noesy' and hasattr(container, 'noesy'):
            # Do errors exist?
            if not hasattr(container, 'noesy_err'):
                raise RelaxError("The NOESY errors are missing for the spin pair '%s' and '%s'." % (container.spin_id1, container.spin_id2))

            # Append the data.
            mc_errors.append(container.noesy_err)

        # PCS data.
        elif data_id[1] == 'pcs' and hasattr(container, 'pcs'):
            # Do errors exist?
            if not hasattr(container, 'pcs_err'):
                raise RelaxError("The PCS errors are missing for spin '%s'." % data_id[0])

            # The error.
            if data_id[2] not in container.pcs_err:
                err = None
            else:
                err = container.pcs_err[data_id[2]]

            # Append the data.
            mc_errors.append(err)

        # Return the errors.
        return mc_errors


    def return_grace_string(self, param):
        """Return the Grace string representation of the parameter.

        This is used for axis labelling.

        @param param:   The specific analysis parameter.
        @type param:    str
        @return:        The Grace string representation of the parameter.
        @rtype:         str
        """

        # The measured PCS.
        if param == 'pcs':
            return "Measured PCS"

        # The back-calculated PCS.
        if param == 'pcs_bc':
            return "Back-calculated PCS"

        # The measured RDC.
        if param == 'rdc':
            return "Measured RDC"

        # The back-calculated RDC.
        if param == 'rdc_bc':
            return "Back-calculated RDC"


    def return_units(self, param):
        """Return a string representing the parameters units.

        @param param:   The name of the parameter to return the units string for.
        @type param:    str
        @return:        The parameter units string.
        @rtype:         str
        """

        # PCSs.
        if param == 'pcs' or param == 'pcs_bc':
            return 'ppm'

        # RDCs.
        if param == 'rdc' or param == 'rdc_bc':
            return 'Hz'


    set_doc = Desc_container("N-state model set details")
    set_doc.add_paragraph("Setting parameters for the N-state model is a little different from the other type of analyses as each state has a set of parameters with the same names as the other states. To set the parameters for a specific state c (ranging from 0 for the first to N-1 for the last, the number c should be added to the end of the parameter name.  So the Euler angle gamma of the third state is specified using the string 'gamma2'.")


    def set_error(self, model_info, index, error):
        """Set the parameter errors.

        @param model_info:  The global model index originating from model_loop().
        @type model_info:   int
        @param index:       The index of the parameter to set the errors for.
        @type index:        int
        @param error:       The error value.
        @type error:        float
        """

        # Align parameters.
        names = ['Axx', 'Ayy', 'Axy', 'Axz', 'Ayz']

        # Alignment tensor parameters.
        if index < len(cdp.align_ids)*5:
            # The tensor and parameter index.
            param_index = index % 5
            tensor_index = (index - index % 5) / 5

            # Set the error.
            tensor = align_tensor.return_tensor(index=tensor_index, skip_fixed=True)
            tensor.set(param=names[param_index], value=error, category='err')

            # Return the object.
            return getattr(tensor, names[param_index]+'_err')


    def set_param_values(self, param=None, value=None, spin_id=None, force=True):
        """Set the N-state model parameter values.

        @keyword param:     The parameter name list.
        @type param:        list of str
        @keyword value:     The parameter value list.
        @type value:        list
        @keyword spin_id:   The spin identification string (unused).
        @type spin_id:      None
        @keyword force:     A flag which if True will cause current values to be overwritten.  If False, a RelaxError will raised if the parameter value is already set.
        @type force:        bool
        """

        # Checks.
        arg_check.is_str_list(param, 'parameter name')
        arg_check.is_list(value, 'parameter value')

        # Loop over the parameters.
        for i in range(len(param)):
            # Get the object's name.
            obj_name = self.return_data_name(param[i])

            # Is the parameter is valid?
            if not obj_name:
                raise RelaxError("The parameter '%s' is not valid for this data pipe type." % param[i])

            # Set the indexed parameter.
            if obj_name in ['probs', 'alpha', 'beta', 'gamma']:
                # The index.
                index = self._param_model_index(param[i])

                # Set.
                obj = getattr(cdp, obj_name)
                obj[index] = value[i]

            # The paramagnetic centre.
            if search('^paramag_[xyz]$', obj_name):
                # Init.
                if not hasattr(cdp, 'paramagnetic_centre'):
                    cdp.paramagnetic_centre = zeros(3, float64)

                # Set the coordinate.
                if obj_name == 'paramag_x':
                    index = 0
                elif obj_name == 'paramag_y':
                    index = 1
                else:
                    index = 2

                # Set the value in Angstrom.
                cdp.paramagnetic_centre[index] = value[i]

            # Set the spin parameters.
            else:
                for spin in spin_loop(spin_id):
                    setattr(spin, obj_name, value[i])


    def sim_init_values(self):
        """Initialise the Monte Carlo parameter values."""

        # Get the minimisation statistic object names.
        sim_names = self.data_names(set='min')

        # Add the paramagnetic centre, if optimised.
        if hasattr(cdp, 'paramag_centre_fixed') and not cdp.paramag_centre_fixed:
            sim_names += ['paramagnetic_centre']

        # Alignments.
        if hasattr(cdp, 'align_tensors'):
            # The parameter names.
            names = ['Axx', 'Ayy', 'Axy', 'Axz', 'Ayz']

            # Loop over the alignments, adding the alignment tensor parameters to the tensor data container.
            for i in range(len(cdp.align_tensors)):
                # Fixed tensor.
                if cdp.align_tensors[i].fixed:
                    continue

                # Set up the number of simulations.
                cdp.align_tensors[i].set_sim_num(cdp.sim_number)

                # Loop over all the parameter names, setting the initial simulation values to those of the parameter value.
                for object_name in names:
                    for j in range(cdp.sim_number):
                        cdp.align_tensors[i].set(param=object_name, value=deepcopy(getattr(cdp.align_tensors[i], object_name)), category='sim', sim_index=j)

            # Create all other simulation objects.
            for object_name in sim_names:
                # Name for the simulation object.
                sim_object_name = object_name + '_sim'

                # Create the simulation object.
                setattr(cdp, sim_object_name, [])

                # Get the simulation object.
                sim_object = getattr(cdp, sim_object_name)

                # Loop over the simulations.
                for j in range(cdp.sim_number):
                    # Append None to fill the structure.
                    sim_object.append(None)


    def sim_pack_data(self, data_id, sim_data):
        """Pack the Monte Carlo simulation data.

        @keyword data_id:   The list of spin ID, data type, and alignment ID, as yielded by the base_data_loop() generator method.
        @type data_id:      list of str
        @param sim_data:    The Monte Carlo simulation data.
        @type sim_data:     list of float
        """

        # Alias the spin or interatomic data container.
        container = data_id[0]

        # RDC data.
        if data_id[1] == 'rdc' and hasattr(container, 'rdc'):
            # Initialise.
            if not hasattr(container, 'rdc_sim'):
                container.rdc_sim = {}
                
            # Store the data structure.
            container.rdc_sim[data_id[2]] = []
            for i in range(cdp.sim_number):
                container.rdc_sim[data_id[2]].append(sim_data[i][0])

        # NOESY data.
        elif data_id[1] == 'noesy' and hasattr(container, 'noesy'):
            # Store the data structure.
            container.noesy_sim = []
            for i in range(cdp.sim_number):
                container.noesy_sim[data_id[2]].append(sim_data[i][0])

        # PCS data.
        elif data_id[1] == 'pcs' and hasattr(container, 'pcs'):
            # Initialise.
            if not hasattr(container, 'pcs_sim'):
                container.pcs_sim = {}
                
            # Store the data structure.
            container.pcs_sim[data_id[2]] = []
            for i in range(cdp.sim_number):
                container.pcs_sim[data_id[2]].append(sim_data[i][0])


    def sim_return_param(self, model_info, index):
        """Return the array of simulation parameter values.

        @param model_info:  The global model index originating from model_loop().
        @type model_info:   int
        @param index:       The index of the parameter to return the array of values for.
        @type index:        int
        @return:            The array of simulation parameter values.
        @rtype:             list of float
        """

        # Align parameters.
        names = ['Axx', 'Ayy', 'Axy', 'Axz', 'Ayz']

        # Alignment tensor parameters.
        if index < align_tensor.num_tensors(skip_fixed=True)*5:
            # The tensor and parameter index.
            param_index = index % 5
            tensor_index = (index - index % 5) / 5

            # Return the simulation parameter array.
            tensor = align_tensor.return_tensor(index=tensor_index, skip_fixed=True)
            return getattr(tensor, names[param_index]+'_sim')
