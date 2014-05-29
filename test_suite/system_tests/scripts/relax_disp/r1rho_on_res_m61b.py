# Optimise the R1rho on-resonance synthetic data using the M61 model.


# Python module imports.
from os import sep

# relax module imports.
from auto_analyses.relax_disp import Relax_disp
from data_store import Relax_data_store; ds = Relax_data_store()
from status import Status; status = Status()


# Analysis variables.
#####################

# The dispersion models.
MODELS = ['R2eff', 'M61 skew']

# The grid search size (the number of increments per dimension).
GRID_INC = 4

# The number of Monte Carlo simulations to be used for error analysis at the end of the analysis.
MC_NUM = 3



# Set up the data pipe.
#######################

# The results directory.
if not hasattr(ds, 'tmpdir'):
    ds.tmpdir = None

# Create the data pipe.
pipe_name = 'base pipe'
pipe_bundle = 'relax_disp'
pipe.create(pipe_name=pipe_name, bundle=pipe_bundle, pipe_type='relax_disp')

# The path to the data files.
data_path = status.install_path + sep+'test_suite'+sep+'shared_data'+sep+'dispersion'+sep+'r1rho_on_res_m61b'

# Create the sequence data.
spin.create(res_name='Trp', res_num=1, spin_name='N')
spin.create(res_name='Trp', res_num=1, spin_name='NE1')

# Set the isotope information.
spin.isotope(isotope='15N')

# Set the relaxation dispersion experiment type.
relax_disp.exp_type(spectrum_id='ref', exp_type='R1rho')

# The spectral data - spectrum ID, peak lists, offset frequency (Hz), relaxation time period (s), baseplane RMSD estimate.
data = []
spin_lock = [1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000]
for spin_lock_index in range(len(spin_lock)):
    data.append(["nu_%s_time_0.1" % spin_lock[spin_lock_index], "nu_%s_time_0.1.list" % spin_lock[spin_lock_index], spin_lock[spin_lock_index], 0.1, 100000.0])

# Load the reference spectrum.
spectrum.read_intensities(file="nu_%s_ref.list" % spin_lock[0], dir=data_path, spectrum_id='ref', int_method='height', dim=1)
spectrum.baseplane_rmsd(spectrum_id='ref', error=data[0][4])

# Set as the reference.
relax_disp.spin_lock_field(spectrum_id='ref', field=None)

# Set the spectrometer frequency.
spectrometer.frequency(id='ref', frq=800, units='MHz')

# Loop over the spectral data, loading it and setting the metadata.
for i in range(len(data)):
    # Load the peak intensities and set the errors.
    spectrum.read_intensities(file=data[i][1], dir=data_path, spectrum_id=data[i][0], int_method='height')
    spectrum.read_intensities(file=data[i][1], dir=data_path, spectrum_id=data[i][0], int_method='height')
    spectrum.baseplane_rmsd(spectrum_id=data[i][0], error=data[i][4])

    # Set the relaxation dispersion experiment type.
    relax_disp.exp_type(spectrum_id=data[i][0], exp_type='R1rho')

    # Set the relaxation dispersion spin-lock field strength (nu1).
    relax_disp.spin_lock_field(spectrum_id=data[i][0], field=data[i][2])

    # Set the relaxation times.
    relax_disp.relax_time(spectrum_id=data[i][0], time=data[i][3])

    # Set the spectrometer frequency.
    spectrometer.frequency(id=data[i][0], frq=800, units='MHz')

# Clustering.
#relax_disp.cluster(cluster_id='cluster', spin_id='@N,NE1')



# Auto-analysis execution.
##########################

# Run faster.
#Relax_disp.opt_func_tol = 1e-5
#Relax_disp.opt_max_iterations = 10000

# Do not change!
Relax_disp(pipe_name=pipe_name, pipe_bundle=pipe_bundle, results_dir=ds.tmpdir, models=MODELS, grid_inc=GRID_INC, mc_sim_num=MC_NUM)

# Save the program state.
state.save('devnull', force=True)
