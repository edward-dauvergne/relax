# Script for optimising the free rotor frame order test model of CaM.

# Python module imports.
from numpy import array, float64, transpose, zeros
from os import sep

# relax module imports.
from generic_fns.structure.mass import centre_of_mass
from maths_fns.rotation_matrix import euler_to_R_zyz
from status import Status; status = Status()


# Some variables.
DATA_PATH = status.install_path + sep+'test_suite'+sep+'shared_data'+sep+'frame_order'+sep


class Analysis:
    def __init__(self, exec_fn):
        """Execute the frame order analysis."""

        # Alias the user function executor method.
        self._execute_uf = exec_fn

        # Optimise.
        self.optimisation()

        # The rotation matrix.
        R = zeros((3, 3), float64)
        euler_to_R_zyz(0.0, cdp.ave_pos_beta, cdp.ave_pos_gamma, R)
        print("Rotation matrix:\n%s\n" % R)
        R = transpose(R)
        print("Inverted rotation:\n%s\n" % R)

        # Load the original structure.
        self.original_structure()

        # Domain transformation.
        self.transform(R, array([ 37.254, 0.5, 16.7465]))


    def optimisation(self):
        """Optimise the frame order model."""

        # The file paths.
        PATH_N_DOM = DATA_PATH
        PATH_C_DOM = PATH_N_DOM+sep+'free_rotor'+sep

        # Create the data pipe.
        self._execute_uf(uf_name='pipe.create', pipe_name='frame order', pipe_type='frame order')

        # Load the tensors.
        self._execute_uf(uf_name='script', file=PATH_N_DOM + 'tensors.py')
        self._execute_uf(uf_name='script', file=PATH_C_DOM + 'tensors.py')

        # The tensor domains and reductions.
        full = ['Dy N-dom', 'Tb N-dom', 'Tm N-dom', 'Er N-dom']
        red =  ['Dy C-dom', 'Tb C-dom', 'Tm C-dom', 'Er C-dom']
        for i in range(len(full)):
            self._execute_uf(uf_name='align_tensor.set_domain', tensor=full[i], domain='N')
            self._execute_uf(uf_name='align_tensor.set_domain', tensor=red[i], domain='C')
            self._execute_uf(uf_name='align_tensor.reduction', full_tensor=full[i], red_tensor=red[i])

        # Select the model.
        self._execute_uf(uf_name='frame_order.select_model', model='free rotor')

        # Set the reference domain.
        self._execute_uf(uf_name='frame_order.ref_domain', ref='N')

        # Optimise.
        self._execute_uf(uf_name='grid_search', inc=11)
        self._execute_uf(uf_name='minimise', min_algor='simplex', constraints=False)

        # Test Monte Carlo simulations.
        self._execute_uf(uf_name='monte_carlo.setup', number=3)
        self._execute_uf(uf_name='monte_carlo.create_data')
        self._execute_uf(uf_name='monte_carlo.initial_values')
        self._execute_uf(uf_name='minimise', min_algor='simplex', constraints=False)
        self._execute_uf(uf_name='eliminate')
        self._execute_uf(uf_name='monte_carlo.error_analysis')

        # Write the results.
        self._execute_uf(uf_name='results.write', file='devnull', dir=None, force=True)


    def original_structure(self):
        """Load the original structure into a dedicated data pipe."""

        # Create a special data pipe for the original rigid body position.
        self._execute_uf(uf_name='pipe.create', pipe_name='orig pos', pipe_type='frame order')

        # Load the structure.
        self._execute_uf(uf_name='structure.read_pdb', file=DATA_PATH+'1J7P_1st_NH.pdb')

        # Store the centre of mass.
        cdp.CoM = centre_of_mass()


    def transform(self, R, pivot):
        """Transform the domain to the average position."""

        # Create a special data pipe for the average rigid body position.
        self._execute_uf(uf_name='pipe.create', pipe_name='ave pos', pipe_type='frame order')

        # Load the structure.
        self._execute_uf(uf_name='structure.read_pdb', file=DATA_PATH+'1J7P_1st_NH_rot.pdb')

        # Rotate all atoms.
        self._execute_uf(uf_name='structure.rotate', R=R, origin=pivot)

        # Write out the new PDB.
        self._execute_uf(uf_name='structure.write_pdb', file='devnull')

        # Store the centre of mass.
        cdp.CoM = centre_of_mass()


# Execute the analysis.
Analysis(self._execute_uf)
