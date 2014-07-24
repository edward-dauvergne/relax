###############################################################################
#                                                                             #
# Copyright (C) 2004-2014 Edward d'Auvergne                                   #
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

"""Script for calculating NOEs."""


# Create the NOE data pipe.
pipe.create('NOE', 'noe')

# Load the backbone amide 15N spins from a PDB file.
structure.read_pdb('Ap4Aase_new_3.pdb')
structure.load_spins(spin_id='@N')
structure.load_spins(spin_id='@NE1')

# Load the reference spectrum and saturated spectrum peak intensities.
spectrum.read_intensities(file='ref.list', spectrum_id='ref_ave')
spectrum.read_intensities(file='sat.list', spectrum_id='sat_ave')

# Set the spectrum types.
noe.spectrum_type('ref', 'ref_ave')
noe.spectrum_type('sat', 'sat_ave')

# Set the errors.
spectrum.baseplane_rmsd(error=3600, spectrum_id='ref_ave')
spectrum.baseplane_rmsd(error=3000, spectrum_id='sat_ave')

# Individual residue errors.
spectrum.baseplane_rmsd(error=122000, spectrum_id='ref_ave', spin_id=":114")
spectrum.baseplane_rmsd(error=8500, spectrum_id='sat_ave', spin_id=":114")

# Peak intensity error analysis.
spectrum.error_analysis()

# Deselect unresolved residues.
deselect.read(file='unresolved', mol_name_col=1, res_num_col=2, res_name_col=3, spin_num_col=4, spin_name_col=5)

# Calculate the NOEs.
minimise.calculate()

# Save the NOEs.
value.write(param='noe', file='noe.out', force=True)

# Create grace files.
grace.write(y_data_type='peak_intensity', file='intensities.agr', force=True)
grace.write(y_data_type='noe', file='noe.agr', force=True)

# View the grace files.
grace.view(file='intensities.agr')
grace.view(file='noe.agr')

# Write the results.
results.write(file='results', dir=None, force=True)

# Save the program state.
state.save('save', force=True)
