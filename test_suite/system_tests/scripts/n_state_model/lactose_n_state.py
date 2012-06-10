# Script for determining populations for lactose conformations using RDCs and PCSs.

# Python module imports.
from os import sep
import sys

# relax imports.
from data import Relax_data_store; ds = Relax_data_store()
from specific_fns.setup import n_state_model_obj
from status import Status; status = Status()


# Path of the files.
str_path = status.install_path + sep+'test_suite'+sep+'shared_data'+sep+'structures'+sep+'lactose'
data_path = status.install_path + sep+'test_suite'+sep+'shared_data'+sep+'align_data'

# Create the data pipe.
self._execute_uf('lactose', 'N-state', uf_name='pipe.create')

# The population model for free operation of this script.
if not hasattr(ds, 'model'):
    ds.model = 'population'

# Load the structures.
NUM_STR = 4
for i in range(NUM_STR):
    self._execute_uf(uf_name='structure.read_pdb', file='lactose_MCMM4_S1_'+repr(i+1), dir=str_path, parser='internal', set_model_num=i+1, set_mol_name='lactose_MCMM4_S1')

# Load the sequence information.
self._execute_uf(uf_name='structure.load_spins', spin_id=':UNK@C*', ave_pos=False)
self._execute_uf(uf_name='structure.load_spins', spin_id=':UNK@H*', ave_pos=False)

# Deselect the CH2 protons (the rotation of these doesn't work in the model, but the carbon doesn't move).
self._execute_uf(uf_name='deselect.spin', spin_id=':UNK@H6')
self._execute_uf(uf_name='deselect.spin', spin_id=':UNK@H7')
self._execute_uf(uf_name='deselect.spin', spin_id=':UNK@H17')
self._execute_uf(uf_name='deselect.spin', spin_id=':UNK@H18')

# Load the CH vectors for the C atoms.
self._execute_uf(uf_name='structure.vectors', spin_id='@C*', attached='H*', ave=False)

# Set the values needed to calculate the dipolar constant.
self._execute_uf(1.10 * 1e-10, 'r', spin_id="@C*", uf_name='value.set')
self._execute_uf('13C', 'heteronuc_type', spin_id="@C*", uf_name='value.set')
self._execute_uf('1H', 'proton_type', spin_id="@C*", uf_name='value.set')

# File list.
align_list = ['Dy', 'Tb', 'Tm', 'Er']

# Load the RDCs and PCSs.
for i in xrange(len(align_list)):
    # The RDC.
    self._execute_uf(uf_name='rdc.read', align_id=align_list[i], file='rdc.txt', dir=data_path, mol_name_col=None, res_num_col=None, res_name_col=None, spin_num_col=None, spin_name_col=1, data_col=i+3, error_col=None)
    self._execute_uf(uf_name='rdc.read', align_id=align_list[i], file='rdc_err.txt', dir=data_path, mol_name_col=None, res_num_col=None, res_name_col=None, spin_num_col=None, spin_name_col=1, data_col=None, error_col=i+3)
    self._execute_uf(uf_name='rdc.display', align_id=align_list[i])

    # The PCS.
    self._execute_uf(uf_name='pcs.read', align_id=align_list[i], file='pcs.txt', dir=data_path, mol_name_col=None, res_num_col=None, res_name_col=None, spin_num_col=None, spin_name_col=1, data_col=i+2, error_col=None)
    self._execute_uf(uf_name='pcs.read', align_id=align_list[i], file='pcs_err.txt', dir=data_path, mol_name_col=None, res_num_col=None, res_name_col=None, spin_num_col=None, spin_name_col=1, data_col=None, error_col=i+2)
    self._execute_uf(uf_name='pcs.display', align_id=align_list[i])

    # The temperature.
    self._execute_uf(uf_name='temperature', id=align_list[i], temp=298)

    # The frequency.
    self._execute_uf(uf_name='frq.set', id=align_list[i], frq=900.015 * 1e6)

# Create a data pipe for the aligned tag structures.
self._execute_uf(uf_name='pipe.create', pipe_name='tag', pipe_type='N-state')

# Load all the tag structures.
NUM_TAG = 10
for i in range(NUM_TAG):
    self._execute_uf(uf_name='structure.read_pdb', file='tag_MCMM4_'+repr(i+1), dir=str_path, parser='internal', set_model_num=i+1, set_mol_name='tag')

# Load the lanthanide atoms.
self._execute_uf(uf_name='structure.load_spins', spin_id='@C1', ave_pos=False)

# Switch back to the main analysis data pipe.
self._execute_uf(uf_name='pipe.switch', pipe_name='lactose')

# Calculate the paramagnetic centre (from the structures in the 'tag' data pipe).
self._execute_uf(uf_name='paramag.centre', atom_id=':4@C1', pipe='tag')

# Set up the model.
self._execute_uf(uf_name='n_state_model.select_model', model=ds.model)

# Set to equal probabilities.
if ds.model == 'population':
    for j in xrange(NUM_STR):
        self._execute_uf(1.0/NUM_STR, 'p'+repr(j), uf_name='value.set')

# Minimisation.
self._execute_uf('bfgs', constraints=True, max_iter=5, uf_name='minimise')

# Calculate the AIC value.
k, n, chi2 = n_state_model_obj.model_statistics()
ds[ds.current_pipe].aic = chi2 + 2.0*k

# Write out a results file.
self._execute_uf(uf_name='results.write', file='devnull', force=True)

# Show the tensors.
self._execute_uf(uf_name='align_tensor.display')
