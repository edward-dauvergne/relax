# Script for generating the distribution of PDB structures.

# Modify the system path to load the base module.
import sys
sys.path.append('..')

# Python module imports.
from math import acos
from numpy import dot

# relax module imports.
from lib.geometry.rotations import R_random_hypersphere

# Base module import.
from generate_base import Main


class Generate(Main):
    # The number of structures.
    N = 1000000

    # Cone parameters.
    THETA_MAX = 1.2
    TILT_ANGLE = 15.0

    def __init__(self):
        """Model specific setup."""

        # Alias the required methods.
        self.axes_to_pdb = self.axes_to_pdb_main_axis
        self.build_axes = self.build_axes_alt


    def rotation(self, i, motion_index=0):
        """Set up the rotation for state i."""

        # Loop until a valid rotation matrix is found.
        while True:
            # The random rotation matrix.
            R_random_hypersphere(self.R)

            # Rotate the Z-axis.
            rot_axis = dot(self.R, self.axes[:, 2])

            # Calculate the projection and angle.
            proj = dot(self.axes[:, 2], rot_axis)

            # Calculate the angle, taking float16 truncation errors into account.
            if proj > 1.0:
                proj = 1.0
            elif proj < -1.0:
                proj = -1.0
            theta = acos(proj)

            # Skip the rotation if the angle is violated.
            if theta > self.THETA_MAX:
                continue

            # Rotation is ok, so stop looping.
            break


# Execute the code.
generate = Generate()
generate.run()
