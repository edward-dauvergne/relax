# Script for generating the distribution of PDB structures.

# Modify the system path to load the base module.
import sys
sys.path.append('..')

# Python module imports.
from math import cos, pi, sin, sqrt
from numpy import dot, transpose

# relax module imports.
from lib.geometry.angles import wrap_angles
from lib.geometry.rotations import R_random_hypersphere, R_to_tilt_torsion

# Base module import.
from generate_base import Main


class Generate(Main):
    # The number of structures.
    N = 1000000

    # Cone parameters.
    THETA_X = 1.3
    THETA_Y = 1.1
    SIGMA_MAX = 0.1 * 2.0 * pi / 360.0

    def __init__(self):
        """Model specific setup."""

        # Alias the required methods.
        self.axes_to_pdb = self.axes_to_pdb_full
        self.build_axes = self.build_axes_pivot_com


    def rotation(self, i, motion_index=0):
        """Set up the rotation for state i."""

        # Loop until a valid rotation matrix is found.
        while True:
            # The random rotation matrix.
            R_random_hypersphere(self.R)

            # Rotation in the eigenframe.
            R_eigen = dot(transpose(self.axes), dot(self.R, self.axes))

            # The angles.
            phi, theta, sigma = R_to_tilt_torsion(R_eigen)
            sigma = wrap_angles(sigma, -pi, pi)

            # Skip the rotation if the torsion angle is violated.
            if sigma > self.SIGMA_MAX or sigma < -self.SIGMA_MAX:
                continue

            # Determine theta_max.
            theta_max = 1.0 / sqrt((cos(phi) / self.THETA_X)**2 + (sin(phi) / self.THETA_Y)**2)

            # Skip the rotation if the cone angle is violated.
            if theta > theta_max:
                continue

            # Rotation is ok, so stop looping.
            break


# Execute the code.
generate = Generate()
generate.run()
