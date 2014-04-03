# Script for generating the distribution of PDB structures.

# Modify the system path to load the base module.
import sys
sys.path.append('..')

# Python module imports.
from math import pi

# relax module imports.
from lib.geometry.rotations import axis_angle_to_R

# Base module import.
from generate_base import Main


class Generate(Main):
    # The number of structures.
    INC = 0.00036
    N = int(360 / INC)

    def __init__(self):
        """Model specific setup."""

        # Alias the required methods.
        self.axes_to_pdb = self.axes_to_pdb_main_axis
        self.build_axes = self.build_axes_pivot_com


    def rotation(self, i, motion_index=0):
        """Set up the rotation for state i."""

        # The rotation angle.
        angle = i * self.INC / 360.0 * 2.0 * pi

        # The rotation matrix.
        axis_angle_to_R(self.axes[:, 2], angle, self.R)


# Execute the code.
generate = Generate()
generate.run()
