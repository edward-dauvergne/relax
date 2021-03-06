###############################################################################
#                                                                             #
# Copyright (C) 2012-2014 Edward d'Auvergne                                   #
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
"""Script for optimising the second rotor frame order test model of CaM."""

# relax module imports.
from base_script import Base_script
from lib.frame_order.variables import MODEL_ROTOR


class Analysis(Base_script):

    # Set up some class variables.
    DIRECTORY = 'rotor2'
    MODEL = MODEL_ROTOR
    AXIS_THETA = 0.69828059079619353433
    AXIS_PHI = 4.03227550621962294031
    CONE_SIGMA_MAX = 30.0 / 360.0 * 2.0 * pi


# Execute the analysis.
Analysis(self._execute_uf)
