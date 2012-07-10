###############################################################################
#                                                                             #
# Copyright (C) 2011 Edward d'Auvergne                                        #
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

"""Set up the data pipe for testing optimisation against tm8 relaxation data."""

# relax module imports.
from opt_tm_fns import create_sequence, opt_and_check, setup_data


# The model-free parameters.
tm = [10e-9]                
s2 = [0.2, 0.8]             
s2f = [0.7, 0.8]            
tf = [2e-12, 40e-12]        
ts = [2e-11, 1.8e-9]        
rex = [0.5, 4]              

# Create the sequence.
create_sequence(len(tm)*len(s2)*len(s2f)*len(tf)*len(ts)*len(rex))

# Set up the data.
setup_data(dir='tm8_grid')

# Residue index.
res_index = 0

# Loop over the parameters.
for rex_index in range(len(rex)):
    for ts_index in range(len(ts)):
        for tf_index in range(len(tf)):
            for s2f_index in range(len(s2f)):
                for s2_index in range(len(s2)):
                    for tm_index in range(len(tm)):
                        # Optimise and validate.
                        opt_and_check(spin=cdp.mol[0].res[res_index].spin[0], tm=tm[tm_index], s2=s2[s2_index], s2f=s2f[s2f_index], tf=tf[tf_index], ts=ts[ts_index], rex=rex[rex_index])
        
                        # Increment the residue index.
                        res_index += 1
