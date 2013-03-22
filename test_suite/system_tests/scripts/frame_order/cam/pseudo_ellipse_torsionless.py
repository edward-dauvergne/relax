###############################################################################
#                                                                             #
# Copyright (C) 2012-2013 Edward d'Auvergne                                   #
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
"""Script for optimising the torsionless pseudo-ellipse frame order test model of CaM."""

# relax module imports.
from base_script import Base_script
from maths_fns.rotation_matrix import reverse_euler_zyz


class Analysis(Base_script):

    # Set up some class variables.
    directory = 'pseudo_ellipse_torsionless'
    model = 'pseudo-ellipse, torsionless'
    ave_pos_alpha, ave_pos_beta, ave_pos_gamma = reverse_euler_zyz(4.3434999280669997, 0.43544332764249905, 3.8013235235956007)
    eigen_alpha = 3.1415926535897931
    eigen_beta = 0.96007997859534311
    eigen_gamma = 4.0322755062196229
    cone_theta_x = 1.3
    cone_theta_y = 1.1
    cone = True
    num_int_pts = 50


# Execute the analysis.
Analysis(self._execute_uf)
