###############################################################################
#                                                                             #
# Copyright (C) 2009-2012 Edward d'Auvergne                                   #
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
"""Module containing the target functions of the Frame Order theories."""

# Python module imports.
from copy import deepcopy
from math import sqrt
from numpy import array, dot, float64, ones, transpose, zeros

# relax module imports.
from float import isNaN
from generic_fns.frame_order import print_frame_order_2nd_degree
from maths_fns.alignment_tensor import to_5D, to_tensor
from maths_fns.chi2 import chi2
from maths_fns.frame_order_matrix_ops import compile_2nd_matrix_free_rotor, compile_2nd_matrix_iso_cone, compile_2nd_matrix_iso_cone_free_rotor, compile_2nd_matrix_iso_cone_torsionless, compile_2nd_matrix_pseudo_ellipse, compile_2nd_matrix_pseudo_ellipse_free_rotor, compile_2nd_matrix_pseudo_ellipse_torsionless, compile_2nd_matrix_rotor, reduce_alignment_tensor
from maths_fns.rotation_matrix import euler_to_R_zyz as euler_to_R
from pcs import pcs_tensor
from rdc import rdc_tensor
from relax_errors import RelaxError


class Frame_order:
    """Class containing the target function of the optimisation of Frame Order matrix components."""

    def __init__(self, model=None, init_params=None, full_tensors=None, full_in_ref_frame=None, rdcs=None, rdc_errors=None, rdc_weights=None, rdc_vect=None, rdc_const=None, pcs=None, pcs_errors=None, pcs_weights=None, pcs_atoms=None, temp=None, frq=None, paramag_centre=None, scaling_matrix=None, pivot_opt=False):
        """Set up the target functions for the Frame Order theories.
        
        @keyword model:             The name of the Frame Order model.
        @type model:                str
        @keyword init_params:       The initial parameter values.
        @type init_params:          numpy float64 array
        @keyword full_tensors:      An array of the {Axx, Ayy, Axy, Axz, Ayz} values for all full alignment tensors.  The format is [Axx1, Ayy1, Axy1, Axz1, Ayz1, Axx2, Ayy2, Axy2, Axz2, Ayz2, ..., Axxn, Ayyn, Axyn, Axzn, Ayzn].
        @type full_tensors:         numpy nx5D, rank-1 float64 array
        @keyword full_in_ref_frame: An array of flags specifying if the tensor in the reference frame is the full or reduced tensor.
        @type full_in_ref_frame:    numpy rank-1 array
        @keyword rdcs:              The RDC lists.  The first index must correspond to the different alignment media i and the second index to the spin systems j.
        @type rdcs:                 numpy rank-2 array
        @keyword rdc_errors:        The RDC error lists.  The dimensions of this argument are the same as for 'rdcs'.
        @type rdc_errors:           numpy rank-2 array
        @keyword rdc_weights:       The RDC weight lists.  The dimensions of this argument are the same as for 'rdcs'.
        @type rdc_weights:          numpy rank-2 array
        @keyword rdc_vect:          The unit XH vector lists corresponding to the RDC values.  The first index must correspond to the spin systems and the second index to the x, y, z elements.
        @type rdc_vect:             numpy rank-2 array
        @keyword rdc_const:         The dipolar constants for each RDC.  The indices correspond to the spin systems j.
        @type rdc_const:            numpy rank-1 array
        @keyword pcs:               The PCS lists.  The first index must correspond to the different alignment media i and the second index to the spin systems j.
        @type pcs:                  numpy rank-2 array
        @keyword pcs_errors:        The PCS error lists.  The dimensions of this argument are the same as for 'pcs'.
        @type pcs_errors:           numpy rank-2 array
        @keyword pcs_weights:       The PCS weight lists.  The dimensions of this argument are the same as for 'pcs'.
        @type pcs_weights:          numpy rank-2 array
        @keyword pcs_atoms:         The atomic positions of the spins with PCS values.  The first index is the spin systems j and the second is the coordinate.
        @type pcs_atoms:            numpy rank-2 array
        @keyword temp:              The temperature of each PCS data set.
        @type temp:                 numpy rank-1 array
        @keyword frq:               The frequency of each PCS data set.
        @type frq:                  numpy rank-1 array
        @keyword paramag_centre:    The paramagnetic centre position (or positions).
        @type paramag_centre:       numpy rank-1, 3D array or rank-2, Nx3 array
        @keyword scaling_matrix:    The square and diagonal scaling matrix.
        @type scaling_matrix:       numpy rank-2 array
        @keyword pivot_opt:         A flag which if True will allow the pivot point of the motion to be optimised.
        @type pivot_opt:            bool
        """

        # Model test.
        if not model:
            raise RelaxError("The type of Frame Order model must be specified.")

        # Store the initial parameter (as a copy).
        self.params = deepcopy(init_params)

        # Store the agrs.
        self.model = model
        self.full_tensors = full_tensors
        self.full_in_ref_frame = full_in_ref_frame
        self.rdc = rdcs
        self.rdc_weights = rdc_weights
        self.rdc_vect = rdc_vect
        self.rdc_const = rdc_const
        self.pcs = pcs
        self.pcs_weights = pcs_weights
        self.pcs_atoms = pcs_atoms
        self.temp = temp
        self.frq = frq
        self.paramag_centre = paramag_centre
        self.total_num_params = len(init_params)
        self.pivot_opt = pivot_opt

        # Tensor setup.
        self.__init_tensors()

        # Scaling initialisation.
        self.scaling_matrix = scaling_matrix
        if self.scaling_matrix != None:
            self.scaling_flag = True
        else:
            self.scaling_flag = False

        # Set the RDC and PCS flags (indicating the presence of data).
        self.rdc_flag = True
        self.pcs_flag = True
        if rdcs == None or len(rdcs) == 0:
            self.rdc_flag = False
        if pcs == None or len(pcs) == 0:
            self.pcs_flag = False

        # Some checks.
        if self.rdc_flag and (rdc_vect == None or not len(rdc_vect)):
            raise RelaxError("The rdc_vect argument " + repr(rdc_vect) + " must be supplied.")
        if self.pcs_flag and (pcs_atoms == None or not len(pcs_atoms)):
            raise RelaxError("The pcs_atoms argument " + repr(pcs_atoms) + " must be supplied.")

        # The total number of spins.
        self.num_spins = 0
        if self.rdc_flag:
            self.num_spins = len(rdcs[0])
        elif self.pcs_flag:
            self.num_spins = len(pcs[0])

        # The total number of alignments.
        self.num_align = 0
        if self.rdc_flag:
            self.num_align = len(rdcs)
        elif self.pcs_flag:
            self.num_align = len(pcs)

        # Alignment tensor function and gradient matrices.
        self.A = zeros((self.num_align, 3, 3), float64)
        self.dA = zeros((5, 3, 3), float64)

        # Set up the alignment data.
        self.num_align_params = 0
        for i in range(self.num_align):
            to_tensor(self.A[i], self.full_tensors[5*i:5*i+5])
            self.num_align_params += 5

        # PCS errors.
        if self.pcs_flag:
            err = False
            for i in xrange(len(pcs_errors)):
                for j in xrange(len(pcs_errors[i])):
                    if not isNaN(pcs_errors[i, j]):
                        err = True
            if err:
                self.pcs_error = pcs_errors
            else:
                # Missing errors (the values need to be small, close to ppm units, so the chi-squared value is comparable to the RDC).
                self.pcs_error = 0.03 * 1e-6 * ones((self.num_align, self.num_spins), float64)

        # RDC errors.
        if self.rdc_flag:
            err = False
            for i in xrange(len(rdc_errors)):
                for j in xrange(len(rdc_errors[i])):
                    if not isNaN(rdc_errors[i, j]):
                        err = True
            if err:
                self.rdc_error = rdc_errors
            else:
                # Missing errors.
                self.rdc_error = ones((self.num_align, self.num_spins), float64)

        # Missing data matrices (RDC).
        if self.rdc_flag:
            self.missing_rdc = zeros((self.num_align, self.num_spins), float64)

        # Missing data matrices (PCS).
        if self.pcs_flag:
            self.missing_pcs = zeros((self.num_align, self.num_spins), float64)

        # Clean up problematic data and put the weights into the errors..
        if self.rdc_flag or self.pcs_flag:
            for i in xrange(self.num_align):
                for j in xrange(self.num_spins):
                    if self.rdc_flag:
                        if isNaN(self.rdc[i, j]):
                            # Set the flag.
                            self.missing_rdc[i, j] = 1

                            # Change the NaN to zero.
                            self.rdc[i, j] = 0.0

                            # Change the error to one (to avoid zero division).
                            self.rdc_error[i, j] = 1.0

                            # Change the weight to one.
                            rdc_weights[i, j] = 1.0

                    if self.pcs_flag:
                        if isNaN(self.pcs[i, j]):
                            # Set the flag.
                            self.missing_pcs[i, j] = 1

                            # Change the NaN to zero.
                            self.pcs[i, j] = 0.0

                            # Change the error to one (to avoid zero division).
                            self.pcs_error[i, j] = 1.0

                            # Change the weight to one.
                            pcs_weights[i, j] = 1.0

                    # The RDC weights.
                    if self.rdc_flag:
                        self.rdc_error[i, j] = self.rdc_error[i, j] / sqrt(rdc_weights[i, j])

                    # The PCS weights.
                    if self.pcs_flag:
                        self.pcs_error[i, j] = self.pcs_error[i, j] / sqrt(pcs_weights[i, j])


        # The paramagnetic centre vectors and distances.
        if self.pcs_flag:
            # Initialise the data structures.
            self.paramag_unit_vect = zeros(pcs_atoms.shape, float64)
            self.paramag_dist = zeros((self.num_spins, self.N), float64)
            self.pcs_const = zeros((self.num_align, self.num_spins, self.N), float64)
            if self.paramag_centre == None:
                self.paramag_centre = zeros(3, float64)

            # Set up the paramagnetic info.
            self.paramag_info()

        # PCS function, gradient, and Hessian matrices.
        self.pcs_theta = zeros((self.num_align, self.num_spins), float64)
        self.dpcs_theta = zeros((self.total_num_params, self.num_align, self.num_spins), float64)
        self.d2pcs_theta = zeros((self.total_num_params, self.total_num_params, self.num_align, self.num_spins), float64)

        # RDC function, gradient, and Hessian matrices.
        self.rdc_theta = zeros((self.num_align, self.num_spins), float64)
        self.drdc_theta = zeros((self.total_num_params, self.num_align, self.num_spins), float64)
        self.d2rdc_theta = zeros((self.total_num_params, self.total_num_params, self.num_align, self.num_spins), float64)

        # The target function aliases.
        if model == 'pseudo-ellipse':
            self.func = self.func_pseudo_ellipse
        elif model == 'pseudo-ellipse, torsionless':
            self.func = self.func_pseudo_ellipse_torsionless
        elif model == 'pseudo-ellipse, free rotor':
            self.func = self.func_pseudo_ellipse_free_rotor
        elif model == 'iso cone':
            self.func = self.func_iso_cone
        elif model == 'iso cone, torsionless':
            self.func = self.func_iso_cone_torsionless
        elif model == 'iso cone, free rotor':
            self.func = self.func_iso_cone_free_rotor
        elif model == 'line':
            self.func = self.func_line
        elif model == 'line, torsionless':
            self.func = self.func_line_torsionless
        elif model == 'line, free rotor':
            self.func = self.func_line_free_rotor
        elif model == 'rotor':
            self.func = self.func_rotor
        elif model == 'rigid':
            self.func = self.func_rigid
        elif model == 'free rotor':
            self.func = self.func_free_rotor


    def __init_tensors(self):
        """Set up isotropic cone optimisation against the alignment tensor data."""

        # Some checks.
        if self.full_tensors == None or not len(self.full_tensors):
            raise RelaxError("The full_tensors argument " + repr(self.full_tensors) + " must be supplied.")
        if self.full_in_ref_frame == None or not len(self.full_in_ref_frame):
            raise RelaxError("The full_in_ref_frame argument " + repr(self.full_in_ref_frame) + " must be supplied.")

        # Tensor set up.
        self.num_tensors = int(len(self.full_tensors) / 5)
        self.red_tensors_bc = zeros(self.num_tensors*5, float64)

        # The rotation to the Frame Order eigenframe.
        self.rot = zeros((3, 3), float64)
        self.tensor_3D = zeros((3, 3), float64)

        # The cone axis storage and molecular frame z-axis.
        self.cone_axis = zeros(3, float64)
        self.z_axis = array([0, 0, 1], float64)

        # Initialise the Frame Order matrices.
        self.frame_order_2nd = zeros((9, 9), float64)


    def func_free_rotor(self, params):
        """Target function for free rotor model optimisation.

        This function optimises against alignment tensors.  The Euler angles for the tensor rotation are the first 3 parameters optimised in this model, followed by the polar and azimuthal angles of the cone axis.

        @param params:  The vector of parameter values.  These are the tensor rotation angles {alpha, beta, gamma, theta, phi}.
        @type params:   list of float
        @return:        The chi-squared or SSE value.
        @rtype:         float
        """

        # Unpack the parameters.
        ave_pos_beta, ave_pos_gamma, axis_theta, axis_phi = params

        # Generate the 2nd degree Frame Order super matrix.
        frame_order_2nd = compile_2nd_matrix_free_rotor(self.frame_order_2nd, self.rot, self.z_axis, self.cone_axis, axis_theta, axis_phi)

        # Reduce and rotate the tensors.
        self.reduce_and_rot(0.0, ave_pos_beta, ave_pos_gamma, frame_order_2nd)

        # Return the chi-squared value.
        return chi2(self.red_tensors, self.red_tensors_bc, self.red_errors)


    def func_iso_cone_elements(self, params):
        """Target function for isotropic cone model optimisation using the Frame Order matrix.

        This function optimises by directly matching the elements of the 2nd degree Frame Order
        super matrix.  The cone axis spherical angles theta and phi and the cone angle theta are the
        3 parameters optimised in this model.

        @param params:  The vector of parameter values {theta, phi, theta_cone} where the first two are the polar and azimuthal angles of the cone axis theta_cone is the isotropic cone angle.
        @type params:   list of float
        @return:        The chi-squared or SSE value.
        @rtype:         float
        """

        # Break up the parameters.
        theta, phi, theta_cone = params

        # Generate the 2nd degree Frame Order super matrix.
        self.frame_order_2nd = compile_2nd_matrix_iso_cone_free_rotor(self.frame_order_2nd, self.rot, self.z_axis, self.cone_axis, theta, phi, theta_cone)

        # Make the Frame Order matrix contiguous.
        self.frame_order_2nd = self.frame_order_2nd.copy()

        # Reshape the numpy arrays for use in the chi2() function.
        self.data.shape = (81,)
        self.frame_order_2nd.shape = (81,)
        self.errors.shape = (81,)

        # Get the chi-squared value.
        val = chi2(self.data, self.frame_order_2nd, self.errors)

        # Reshape the arrays back to normal.
        self.data.shape = (9, 9)
        self.frame_order_2nd.shape = (9, 9)
        self.errors.shape = (9, 9)

        # Return the chi2 value.
        return val


    def func_iso_cone(self, params):
        """Target function for isotropic cone model optimisation.

        This function optimises against alignment tensors.

        @param params:  The vector of parameter values {beta, gamma, theta, phi, s1} where the first 2 are the tensor rotation Euler angles, the next two are the polar and azimuthal angles of the cone axis, and s1 is the isotropic cone order parameter.
        @type params:   list of float
        @return:        The chi-squared or SSE value.
        @rtype:         float
        """

        # Unpack the parameters.
        ave_pos_alpha, ave_pos_beta, ave_pos_gamma, eigen_alpha, eigen_beta, eigen_gamma, cone_theta, sigma_max = params

        # Generate the 2nd degree Frame Order super matrix.
        frame_order_2nd = compile_2nd_matrix_iso_cone(self.frame_order_2nd, self.rot, eigen_alpha, eigen_beta, eigen_gamma, cone_theta, sigma_max)

        # Reduce and rotate the tensors.
        self.reduce_and_rot(ave_pos_alpha, ave_pos_beta, ave_pos_gamma, frame_order_2nd)

        # Return the chi-squared value.
        return chi2(self.red_tensors, self.red_tensors_bc, self.red_errors)


    def func_iso_cone_free_rotor(self, params):
        """Target function for free rotor isotropic cone model optimisation.

        This function optimises against alignment tensors.

        @param params:  The vector of parameter values {beta, gamma, theta, phi, s1} where the first 2 are the tensor rotation Euler angles, the next two are the polar and azimuthal angles of the cone axis, and s1 is the isotropic cone order parameter.
        @type params:   list of float
        @return:        The chi-squared or SSE value.
        @rtype:         float
        """

        # Unpack the parameters.
        ave_pos_beta, ave_pos_gamma, axis_theta, axis_phi, cone_s1 = params

        # Generate the 2nd degree Frame Order super matrix.
        frame_order_2nd = compile_2nd_matrix_iso_cone_free_rotor(self.frame_order_2nd, self.rot, self.z_axis, self.cone_axis, axis_theta, axis_phi, cone_s1)

        # Reduce and rotate the tensors.
        self.reduce_and_rot(0.0, ave_pos_beta, ave_pos_gamma, frame_order_2nd)

        # Return the chi-squared value.
        return chi2(self.red_tensors, self.red_tensors_bc, self.red_errors)


    def func_iso_cone_torsionless(self, params):
        """Target function for torsionless isotropic cone model optimisation.

        This function optimises against alignment tensors.

        @param params:  The vector of parameter values {beta, gamma, theta, phi, cone_theta} where the first 2 are the tensor rotation Euler angles, the next two are the polar and azimuthal angles of the cone axis, and cone_theta is cone opening angle.
        @type params:   list of float
        @return:        The chi-squared or SSE value.
        @rtype:         float
        """

        # Unpack the parameters.
        ave_pos_beta, ave_pos_gamma, axis_theta, axis_phi, cone_theta = params

        # Generate the 2nd degree Frame Order super matrix.
        frame_order_2nd = compile_2nd_matrix_iso_cone_torsionless(self.frame_order_2nd, self.rot, self.z_axis, self.cone_axis, axis_theta, axis_phi, cone_theta)

        # Reduce and rotate the tensors.
        self.reduce_and_rot(0.0, ave_pos_beta, ave_pos_gamma, frame_order_2nd)

        # Return the chi-squared value.
        return chi2(self.red_tensors, self.red_tensors_bc, self.red_errors)


    def func_pseudo_ellipse(self, params):
        """Target function for pseudo-elliptic cone model optimisation.

        @param params:  The vector of parameter values {alpha, beta, gamma, eigen_alpha, eigen_beta, eigen_gamma, cone_theta_x, cone_theta_y, cone_sigma_max} where the first 3 are the average position rotation Euler angles, the next 3 are the Euler angles defining the eigenframe, and the last 3 are the pseudo-elliptic cone geometric parameters.
        @type params:   list of float
        @return:        The chi-squared or SSE value.
        @rtype:         float
        """

        # Unpack the parameters.
        ave_pos_alpha, ave_pos_beta, ave_pos_gamma, eigen_alpha, eigen_beta, eigen_gamma, cone_theta_x, cone_theta_y, cone_sigma_max = params

        # Generate the 2nd degree Frame Order super matrix.
        frame_order_2nd = compile_2nd_matrix_pseudo_ellipse(self.frame_order_2nd, self.rot, eigen_alpha, eigen_beta, eigen_gamma, cone_theta_x, cone_theta_y, cone_sigma_max)

        # Reduce and rotate the tensors.
        self.reduce_and_rot(ave_pos_alpha, ave_pos_beta, ave_pos_gamma, frame_order_2nd)

        # Return the chi-squared value.
        return chi2(self.red_tensors, self.red_tensors_bc, self.red_errors)


    def func_pseudo_ellipse_free_rotor(self, params):
        """Target function for free_rotor pseudo-elliptic cone model optimisation.

        @param params:  The vector of parameter values {alpha, beta, gamma, eigen_alpha, eigen_beta, eigen_gamma, cone_theta_x, cone_theta_y} where the first 3 are the average position rotation Euler angles, the next 3 are the Euler angles defining the eigenframe, and the last 2 are the free_rotor pseudo-elliptic cone geometric parameters.
        @type params:   list of float
        @return:        The chi-squared or SSE value.
        @rtype:         float
        """

        # Unpack the parameters.
        ave_pos_alpha, ave_pos_beta, ave_pos_gamma, eigen_alpha, eigen_beta, eigen_gamma, cone_theta_x, cone_theta_y = params

        # Generate the 2nd degree Frame Order super matrix.
        frame_order_2nd = compile_2nd_matrix_pseudo_ellipse_free_rotor(self.frame_order_2nd, self.rot, eigen_alpha, eigen_beta, eigen_gamma, cone_theta_x, cone_theta_y)

        # Reduce and rotate the tensors.
        self.reduce_and_rot(ave_pos_alpha, ave_pos_beta, ave_pos_gamma, frame_order_2nd)

        # Return the chi-squared value.
        return chi2(self.red_tensors, self.red_tensors_bc, self.red_errors)


    def func_pseudo_ellipse_torsionless(self, params):
        """Target function for torsionless pseudo-elliptic cone model optimisation.

        @param params:  The vector of parameter values {alpha, beta, gamma, eigen_alpha, eigen_beta, eigen_gamma, cone_theta_x, cone_theta_y} where the first 3 are the average position rotation Euler angles, the next 3 are the Euler angles defining the eigenframe, and the last 2 are the torsionless pseudo-elliptic cone geometric parameters.
        @type params:   list of float
        @return:        The chi-squared or SSE value.
        @rtype:         float
        """

        # Unpack the parameters.
        ave_pos_alpha, ave_pos_beta, ave_pos_gamma, eigen_alpha, eigen_beta, eigen_gamma, cone_theta_x, cone_theta_y = params

        # Generate the 2nd degree Frame Order super matrix.
        frame_order_2nd = compile_2nd_matrix_pseudo_ellipse_torsionless(self.frame_order_2nd, self.rot, eigen_alpha, eigen_beta, eigen_gamma, cone_theta_x, cone_theta_y)

        # Reduce and rotate the tensors.
        self.reduce_and_rot(ave_pos_alpha, ave_pos_beta, ave_pos_gamma, frame_order_2nd)

        # Return the chi-squared value.
        return chi2(self.red_tensors, self.red_tensors_bc, self.red_errors)


    def func_rigid(self, params):
        """Target function for rigid model optimisation.

        This function optimises against alignment tensors.  The Euler angles for the tensor rotation are the 3 parameters optimised in this model.

        @param params:  The vector of parameter values.  These are the tensor rotation angles {alpha, beta, gamma}.
        @type params:   list of float
        @return:        The chi-squared or SSE value.
        @rtype:         float
        """

        # Unpack the parameters.
        ave_pos_alpha, ave_pos_beta, ave_pos_gamma = params

        # Reduce and rotate the tensors.
        self.reduce_and_rot(ave_pos_alpha, ave_pos_beta, ave_pos_gamma)

        # Return the chi-squared value.
        return chi2(self.red_tensors, self.red_tensors_bc, self.red_errors)


    def func_rotor(self, params):
        """Target function for rotor model optimisation.

        This function optimises against alignment tensors.  The Euler angles for the tensor rotation are the first 3 parameters optimised in this model, followed by the polar and azimuthal angles of the cone axis and the torsion angle restriction.

        @param params:  The vector of parameter values.  These are the tensor rotation angles {alpha, beta, gamma, theta, phi, sigma_max}.
        @type params:   list of float
        @return:        The chi-squared or SSE value.
        @rtype:         float
        """

        # Initial chi-squared (or SSE) value.
        chi2_sum = 0.0

        # Scaling.
        if self.scaling_flag:
            params = dot(params, self.scaling_matrix)

        # Unpack the parameters.
        if self.pivot_opt:
            pivot = params[:3]
            ave_pos_alpha, ave_pos_beta, ave_pos_gamma, axis_theta, axis_phi, sigma_max = params[3:]
        else:
            ave_pos_alpha, ave_pos_beta, ave_pos_gamma, axis_theta, axis_phi, sigma_max = params

        # Generate the 2nd degree Frame Order super matrix.
        frame_order_2nd = compile_2nd_matrix_rotor(self.frame_order_2nd, self.rot, self.z_axis, self.cone_axis, axis_theta, axis_phi, sigma_max)

        # Reduce and rotate the tensors.
        self.reduce_and_rot(ave_pos_alpha, ave_pos_beta, ave_pos_gamma, frame_order_2nd)

        # Loop over each alignment.
        for i in xrange(self.num_align):
            # Loop over the spin systems j.
            for j in xrange(self.num_spins):
                # The back calculated RDC.
                if self.rdc_flag and not self.missing_rdc[i, j]:
                    self.rdc_theta[i, j] = rdc_tensor(self.rdc_const[j], self.rdc_vect[j], self.red_tensors_bc[i])

                # The back calculated PCS.
                if self.pcs_flag and not self.missing_pcs[i, j]:
                    self.pcs_theta[i, j] = pcs_tensor(self.pcs_const[i, j], self.pcs_unit_vect[j], self.red_tensors_bc[i])

            # Calculate and sum the single alignment chi-squared value (for the RDC).
            if self.rdc_flag:
                chi2_sum = chi2_sum + chi2(self.rdc[i], self.rdc_theta[i], self.rdc_error[i])

            # Calculate and sum the single alignment chi-squared value (for the PCS).
            if self.pcs_flag:
                chi2_sum = chi2_sum + chi2(self.pcs[i], self.pcs_theta[i], self.pcs_error[i])

        # Return the chi-squared value.
        return chi2_sum


    def reduce_and_rot(self, ave_pos_alpha=None, ave_pos_beta=None, ave_pos_gamma=None, daeg=None):
        """Reduce and rotate the alignments tensors using the frame order matrix and Euler angles.

        @keyword ave_pos_alpha: The alpha Euler angle describing the average domain position, the tensor rotation.
        @type ave_pos_alpha:    float
        @keyword ave_pos_beta:  The beta Euler angle describing the average domain position, the tensor rotation.
        @type ave_pos_beta:     float
        @keyword ave_pos_gamma: The gamma Euler angle describing the average domain position, the tensor rotation.
        @type ave_pos_gamma:    float
        @keyword daeg:          The 2nd degree frame order matrix.
        @type daeg:             rank-2, 9D array
        """

        # Alignment tensor rotation.
        euler_to_R(ave_pos_alpha, ave_pos_beta, ave_pos_gamma, self.rot)

        # Back calculate the rotated tensors.
        for i in range(self.num_tensors):
            # Tensor indices.
            index1 = i*5
            index2 = i*5+5

            # Reduction.
            if daeg != None:
                # Reduce the tensor.
                reduce_alignment_tensor(daeg, self.full_tensors[index1:index2], self.red_tensors_bc[index1:index2])

                # Convert the reduced tensor to 3D, rank-2 form.
                to_tensor(self.tensor_3D, self.red_tensors_bc[index1:index2])

            # No reduction:
            else:
                # Convert the original tensor to 3D, rank-2 form.
                to_tensor(self.tensor_3D, self.full_tensors[index1:index2])

            # Rotate the tensor (normal R.X.RT rotation).
            if self.full_in_ref_frame[i]:
                tensor_3D = dot(self.rot, dot(self.tensor_3D, transpose(self.rot)))

            # Rotate the tensor (inverse RT.X.R rotation).
            else:
                tensor_3D = dot(transpose(self.rot), dot(self.tensor_3D, self.rot))

            # Convert the tensor back to 5D, rank-1 form, as the back-calculated reduced tensor.
            to_5D(self.red_tensors_bc[index1:index2], tensor_3D)
