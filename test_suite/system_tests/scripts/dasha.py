# Script for model-free analysis using the program Dasha.

# Python module imports.
from os import sep

# relax module imports.
from data_store import Relax_data_store; ds = Relax_data_store()
from status import Status; status = Status()


# Missing temp directory (allow this script to run outside of the system test framework).
if not hasattr(ds, 'tmpdir'):
    ds.tmpdir = 'temp_script'

# Set the data pipe names (also the names of preset model-free models).
pipes = ['m1', 'm2', 'm3']

# Loop over the pipes.
for name in pipes:
    # Create the data pipe.
    pipe.create(name, 'mf')

    # Set up the 15N spins.
    sequence.read(status.install_path + sep+'test_suite'+sep+'shared_data'+sep+'jw_mapping'+sep+'noe.dat', res_num_col=1, res_name_col=2)
    spin.name('N')
    spin.element(element='N', spin_id='@N')
    spin.isotope('15N', spin_id='@N')

    # Load the relaxation data.
    relax_data.read(ri_id='R1_600',  ri_type='R1',  frq=600.0*1e6, file=status.install_path+sep+'test_suite'+sep+'shared_data'+sep+'jw_mapping'+sep+'R1.dat', res_num_col=1, res_name_col=2, data_col=3, error_col=4)
    relax_data.read(ri_id='R2_600',  ri_type='R2',  frq=600.0*1e6, file=status.install_path+sep+'test_suite'+sep+'shared_data'+sep+'jw_mapping'+sep+'R2.dat', res_num_col=1, res_name_col=2, data_col=3, error_col=4)
    relax_data.read(ri_id='NOE_600', ri_type='NOE', frq=600.0*1e6, file=status.install_path+sep+'test_suite'+sep+'shared_data'+sep+'jw_mapping'+sep+'noe.dat', res_num_col=1, res_name_col=2, data_col=3, error_col=4)

    # Set up the diffusion tensor.
    diffusion_tensor.init(1e-8, fixed=True)

    # Generate the 1H spins for the magnetic dipole-dipole relaxation interaction.
    sequence.attach_protons()

    # Define the magnetic dipole-dipole relaxation interaction.
    interatom.define(spin_id1='@N', spin_id2='@H', direct_bond=True)
    interatom.set_dist(spin_id1='@N', spin_id2='@H', ave_dist=1.02 * 1e-10)

    # Define the chemical shift relaxation interaction.
    value.set(-172 * 1e-6, 'csa', spin_id='@N')

    # Select the model-free model.
    model_free.select_model(model=name)

    # Create the Dasha script.
    dasha.create(algor='NR', dir=ds.tmpdir, force=True)

    # Execute Dasha.
    dasha.execute(dir=ds.tmpdir)

    # Read the data.
    dasha.extract(dir=ds.tmpdir)

    # Write the results.
    results.write(file=ds.tmpdir + sep + 'results_dasha', dir=None, force=True)
