###############################################################################
#                                                                             #
# Copyright (C) 2007-2014 Edward d'Auvergne                                   #
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
"""The module for the N-state model parameter list object."""

# relax module imports.
from specific_analyses.parameter_object import Param_list


class N_state_params(Param_list):
    """The N-state model parameter list singleton."""

    # Class variable for storing the class instance (for the singleton design pattern).
    _instance = None

    def __init__(self):
        """Define all the parameters of the analysis."""

        # The object is already initialised.
        if self._initialised: return

        # Execute the base class __init__() method.
        Param_list.__init__(self)

        # Add the base data.
        self._add_align_data()

        # Add up the model parameters.
        self._add('probs', scope='global', default=0.0, desc='The probabilities of each state', py_type=list, set='params', err=True, sim=True)
        self._add('alpha', scope='global', units='rad', default=0.0, desc='The alpha Euler angles (for the rotation of each state)', py_type=list, set='params', err=True, sim=True)
        self._add('beta', scope='global', units='rad', default=0.0, desc='The beta Euler angles (for the rotation of each state)', py_type=list, set='params', err=True, sim=True)
        self._add('gamma', scope='global', units='rad', default=0.0, desc='The gamma Euler angles (for the rotation of each state)', py_type=list, set='params', err=True, sim=True)
        self._add('paramagnetic_centre', scope='global', units='Angstrom', desc='The paramagnetic centre', py_type=list, set='params', err=True, sim=True)

        # Add the minimisation data.
        self._add_min_data(min_stats_global=False, min_stats_spin=True)

        # Set up the user function documentation.
        self._set_uf_title("N-state model parameters")
