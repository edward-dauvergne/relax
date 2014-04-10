# Script for determining populations for lactose conformations using RDCs and PCSs.

# Python module imports.
from os import sep

# relax module imports.
from lib.errors import RelaxError
from status import Status; status = Status()

# Path of the files.
str_path = status.install_path + sep+'test_suite'+sep+'shared_data'+sep+'structures'+sep+'lactose'
data_path = status.install_path + sep+'test_suite'+sep+'shared_data'+sep+'align_data'+sep+'population_model'

# Create the data pipe.
self._execute_uf(uf_name='pipe.create', pipe_name='populations', pipe_type='N-state')

# Load the structures.
NUM_STR = 3
i = 1
for model in [1, 3, 2]:
    self._execute_uf(uf_name='structure.read_pdb', file='lactose_MCMM4_S1_%i.pdb' % i, dir=str_path, set_model_num=model, set_mol_name='LE')
    i += 1

# Load the sequence information.
self._execute_uf(uf_name='structure.load_spins', spin_id=':UNK@C*', ave_pos=False)
self._execute_uf(uf_name='structure.load_spins', spin_id=':UNK@H*', ave_pos=False)

# Deselect the CH2 protons (the rotation of these doesn't work in the model, but the carbon doesn't move).
self._execute_uf(uf_name='deselect.spin', spin_id=':UNK@H6')
self._execute_uf(uf_name='deselect.spin', spin_id=':UNK@H7')
self._execute_uf(uf_name='deselect.spin', spin_id=':UNK@H17')
self._execute_uf(uf_name='deselect.spin', spin_id=':UNK@H18')

# Define the magnetic dipole-dipole relaxation interaction.
self._execute_uf(uf_name='interatom.define', spin_id1='@C*', spin_id2='@H*', direct_bond=True)
self._execute_uf(uf_name='interatom.set_dist', spin_id1='@C*', spin_id2='@H*', ave_dist=1.10 * 1e-10)
self._execute_uf(uf_name='interatom.unit_vectors', ave=False)

# Set the nuclear isotope type.
self._execute_uf(uf_name='spin.isotope', isotope='13C', spin_id='@C*')
self._execute_uf(uf_name='spin.isotope', isotope='1H', spin_id='@H*')

# File list.
align_list = ['Dy', 'Tb', 'Tm', 'Er']

# Load the RDCs and PCSs.
for i in range(len(align_list)):
    # The RDC (skip the list at index 1, as this has zero data and now causes a RelaxError).
    if i != 1:
        self._execute_uf(uf_name='rdc.read', align_id=align_list[i], file='missing_rdc_%i' % i, dir=data_path, spin_id1_col=1, spin_id2_col=2, data_col=3, error_col=None)

    # The PCS.
    self._execute_uf(uf_name='pcs.read', align_id=align_list[i], file='missing_pcs_%i' % i, dir=data_path, mol_name_col=1, res_num_col=2, res_name_col=3, spin_num_col=None, spin_name_col=5, data_col=6, error_col=None)

    # The temperature.
    self._execute_uf(uf_name='spectrometer.temperature', id=align_list[i], temp=298)

    # The frequency.
    self._execute_uf(uf_name='spectrometer.frequency', id=align_list[i], frq=799.75376122 * 1e6)

# Try to delete the RDC and PCS data (bug #20335, https://gna.org/bugs/?20335).
self._execute_uf(uf_name='pcs.delete')
self._execute_uf(uf_name='rdc.delete')

# Load the RDCs and PCSs.
for i in range(len(align_list)):
    # The RDC (skip the list at index 1, as this has zero data and now causes a RelaxError).
    if i != 1:
        self._execute_uf(uf_name='rdc.read', align_id=align_list[i], file='missing_rdc_%i' % i, dir=data_path, spin_id1_col=1, spin_id2_col=2, data_col=3, error_col=None)

    # The PCS.
    self._execute_uf(uf_name='pcs.read', align_id=align_list[i], file='missing_pcs_%i' % i, dir=data_path, mol_name_col=1, res_num_col=2, res_name_col=3, spin_num_col=None, spin_name_col=5, data_col=6, error_col=None)

    # The temperature.
    self._execute_uf(uf_name='spectrometer.temperature', id=align_list[i], temp=298)

    # The frequency.
    self._execute_uf(uf_name='spectrometer.frequency', id=align_list[i], frq=799.75376122 * 1e6)

# Set the paramagnetic centre.
self._execute_uf(uf_name='paramag.centre', pos=[ -14.845,    0.969,    0.265])


# The solution.
###############

# Set up the model.
self._execute_uf(uf_name='n_state_model.select_model', model='population')

# Set pc to the exact values.
self._execute_uf(uf_name='value.set', val=0.3, param='probs', index=0)
self._execute_uf(uf_name='value.set', val=0.1, param='probs', index=2)
self._execute_uf(uf_name='value.set', val=0.6, param='probs', index=1)

# Set the tensors.
self._execute_uf(uf_name='align_tensor.init', tensor=align_list[0], params=( 1.42219822168827662867e-04, -1.44543001566521341940e-04, -7.07796211648713973798e-04, -6.01619494082773244303e-04,  2.02008007072950861996e-04), align_id=align_list[0], param_types=2)
self._execute_uf(uf_name='align_tensor.init', tensor=align_list[1], params=( 3.56720663040924505435e-04, -2.68385787902088840916e-04, -1.69361406642305853832e-04,  1.71873715515064501074e-04, -3.05790155096090983822e-04), align_id=align_list[1], param_types=2)
self._execute_uf(uf_name='align_tensor.init', tensor=align_list[2], params=( 2.32088908680377300801e-07,  2.08076808579168379617e-06, -2.21735465435989729223e-06, -3.74311563209448033818e-06, -2.40784858070560310370e-06), align_id=align_list[2], param_types=2)
self._execute_uf(uf_name='align_tensor.init', tensor=align_list[3], params=(-2.62495279588228071048e-04,  7.35617367964106275147e-04,  6.39754192258981332648e-05,  6.27880171180572523460e-05,  2.01197582457700226708e-04), align_id=align_list[3], param_types=2)

# Calculation.
self._execute_uf(uf_name='calc')
print("Chi2: %s" % cdp.chi2)
if abs(cdp.chi2) > 1e-15:
    raise RelaxError("The chi2 at the solution is not zero!")


# The population model opt.
###########################

# Change a probability
self._execute_uf(uf_name='value.set', val=0.6005, param='probs', index=1)

# Minimisation.
self._execute_uf(uf_name='minimise', min_algor='bfgs', max_iter=500)

# Write out a results file.
self._execute_uf(uf_name='results.write', file='devnull', force=True)
