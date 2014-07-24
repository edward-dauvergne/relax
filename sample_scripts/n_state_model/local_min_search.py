###############################################################################
#                                                                             #
# Copyright (C) 2011-2014 Edward d'Auvergne                                   #
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

"""Script for finding the global minimum in the population optimisation for lactose conformations using RDCs and PCSs.

This script follows on from the results obtained from conformation_analysis_rdc+pcs.py

The reference for this script is:

    Erdelyi, M., d'Auvergne E., Navarro-Vazquez, A., Leonov, A., and Griesinger, C. (2011) Dynamics of the Glycosidic Bond: Conformational Space of Lactose. Chemistry-A European Journal, 17(34), 9368-9376 (http://dx.doi.org/10.1002/chem.201100854).
"""


# Python imports.
from numpy import float64, zeros
from numpy.linalg import norm
from random import uniform

# relax imports.
from data_store import Relax_data_store; ds = Relax_data_store()
from specific_analyses.api import return_api


# The specific analysis API object.
api = return_api(analysis_type='N-state')

# Loop over random positions.
for rand_index in range(200):
    # Reset.
    reset()

    # Create the datapipe.
    pipe.create('lactose', 'N-state')

    # Read the results file.
    results.read('results_fixed_rdc+pcs')


    # Random starts.
    ################

    # Set up the model.
    n_state_model.select_model(model='population')

    # Random array.
    probs = zeros(cdp.N, float64)
    for j in range(cdp.N):
        probs[j] = uniform(0, 1)
    probs = probs / norm(probs)

    # Set the random probabilities.
    for j in range(cdp.N):
        value.set(probs[j], 'probs', index=j)

    # Reset the tensors.
    #for i in range(len(cdp.align_tensors)):
    #    cdp.align_tensors[i].Axx = 0.0
    #    cdp.align_tensors[i].Ayy = 0.0
    #    cdp.align_tensors[i].Axy = 0.0
    #    cdp.align_tensors[i].Axz = 0.0
    #    cdp.align_tensors[i].Ayz = 0.0

    # Minimisation.
    minimise.execute('bfgs', constraints=True)

    # Calculate the AIC value.
    k, n, chi2 = api.model_statistics()
    ds[ds.current_pipe].aic = chi2 + 2.0*k

    # Write out a results file.
    results.write('results_population_rdc+pcs_rand%i' % rand_index, dir=None, force=True)

    # Show the tensors.
    align_tensor.display()

    # Show the populations.
    for i in range(len(cdp.structure.structural_data)):
        if abs(cdp.probs[i]) > 1e-7:
            print("%16.10f %s" % (cdp.probs[i], cdp.structure.structural_data[i].mol[0].file_name))
