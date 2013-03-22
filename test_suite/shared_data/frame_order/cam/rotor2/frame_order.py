# Script for optimising the second rotor frame order test model of CaM.

# Python module imports.
from numpy import array, float64, transpose, zeros
from os import sep

# relax module imports.
from maths_fns.rotation_matrix import euler_to_R_zyz


class Analysis:
    def __init__(self):
        """Execute the frame order analysis."""

        # Optimise.
        self.optimisation()

        # Load the original structure.
        self.original_structure()

        # Domain transformation.
        self.transform()

        # Display in pymol.
        self.pymol_display()

        # Save the state.
        state.save('frame_order', force=True)


    def optimisation(self):
        """Optimise the frame order model."""

        # Create the data pipe.
        pipe.create(pipe_name='frame order', pipe_type='frame order')

        # Read the structures.
        structure.read_pdb('1J7O_1st_NH.pdb', dir='..', set_mol_name='N-dom')
        structure.read_pdb('1J7P_1st_NH_rot.pdb', dir='..', set_mol_name='C-dom')

        # Set up the 15N and 1H spins.
        structure.load_spins(spin_id='@N', ave_pos=False)
        structure.load_spins(spin_id='@H', ave_pos=False)
        spin.isotope(isotope='15N', spin_id='@N')
        spin.isotope(isotope='1H', spin_id='@H')

        # Define the magnetic dipole-dipole relaxation interaction.
        dipole_pair.define(spin_id1='@N', spin_id2='@H', direct_bond=True)
        dipole_pair.set_dist(spin_id1='@N', spin_id2='@H', ave_dist=1.041 * 1e-10)
        dipole_pair.unit_vectors()

        # Loop over the alignments.
        ln = ['dy', 'tb', 'tm', 'er']
        for i in range(len(ln)):
            # Load the RDCs.
            rdc.read(align_id=ln[i], file='rdc_%s.txt'%ln[i], spin_id1_col=1, spin_id2_col=2, data_col=3, error_col=4)

            # The PCS.
            pcs.read(align_id=ln[i], file='pcs_%s.txt'%ln[i], mol_name_col=1, res_num_col=2, spin_name_col=5, data_col=6, error_col=7)

            # The temperature and field strength.
            temperature(id=ln[i], temp=303)
            frq.set(id=ln[i], frq=900e6)

        # Load the N-domain tensors (the full tensors).
        script('../tensors.py')

        # Define the domains.
        domain(id='N', spin_id=":1-78")
        domain(id='C', spin_id=":80-148")

        # The tensor domains and reductions.
        full = ['Dy N-dom', 'Tb N-dom', 'Tm N-dom', 'Er N-dom']
        red =  ['Dy C-dom', 'Tb C-dom', 'Tm C-dom', 'Er C-dom']
        for i in range(len(full)):
            # Initialise the reduced tensor.
            align_tensor.init(tensor=red[i], params=(0,0,0,0,0))

            # Set the domain info.
            align_tensor.set_domain(tensor=full[i], domain='N')
            align_tensor.set_domain(tensor=red[i], domain='C')

            # Specify which tensor is reduced.
            align_tensor.reduction(full_tensor=full[i], red_tensor=red[i])

        # Select the model.
        frame_order.select_model('rotor')

        # Set the reference domain.
        frame_order.ref_domain('N')

        # Set the initial pivot point.
        pivot = array([ 37.254, 0.5, 16.7465])
        frame_order.pivot(pivot, fix=True)

        # Set the paramagnetic centre.
        paramag.centre(pos=[35.934, 12.194, -4.206])

        # The optimisation settings.
        frame_order.num_int_pts(num=50)
        frame_order.quad_int(flag=False)

        # Check the minimum.
        value.set(param='ave_pos_alpha', val=4.3434999280669997)
        value.set(param='ave_pos_beta', val=0.43544332764249905)
        value.set(param='ave_pos_gamma', val=3.8013235235956007)
        value.set(param='axis_theta', val=0.69828059079619353433)
        value.set(param='axis_phi', val=4.03227550621962294031)
        value.set(param='cone_sigma_max', val=30.0 / 360.0 * 2.0 * pi)
        calc()
        print("\nchi2: %s" % repr(cdp.chi2))

        # Optimise.
        grid_search(inc=3)
        minimise('simplex', constraints=False)

        # Optimise the pivot and model.
        #frame_order.pivot(pivot, fix=False)
        #minimise('simplex', constraints=False)

        # Test Monte Carlo simulations.
        monte_carlo.setup(number=5)
        monte_carlo.create_data()
        monte_carlo.initial_values()
        minimise('simplex', constraints=False)
        eliminate()
        monte_carlo.error_analysis()


    def original_structure(self):
        """Load the original structure into a dedicated data pipe."""

        # Create a special data pipe for the original rigid body position.
        pipe.create(pipe_name='orig pos', pipe_type='frame order')

        # Load the structure.
        structure.read_pdb('1J7P_1st_NH_rot.pdb', dir='..')


    def pymol_display(self):
        """Display the results in PyMOL."""

        # Switch back to the main data pipe.
        pipe.switch('frame order')

        # Load the PDBs of the 2 domains.
        structure.read_pdb('1J7O_1st_NH.pdb', dir='..')
        structure.read_pdb('1J7P_1st_NH_rot.pdb', dir='..')

        # Create the cone PDB file.
        frame_order.cone_pdb(file='cone.pdb', force=True)

        # Set the domains.
        frame_order.domain_to_pdb(domain='N', pdb='1J7O_1st_NH.pdb')
        frame_order.domain_to_pdb(domain='C', pdb='1J7P_1st_NH_rot.pdb')

        # PyMOL.
        pymol.view()
        pymol.command('show spheres')
        pymol.cone_pdb('cone.pdb')


    def transform(self):
        """Transform the domain to the average position."""

        # Switch back to the main data pipe.
        pipe.switch('frame order')

        # The rotation matrix.
        R = zeros((3, 3), float64)
        euler_to_R_zyz(cdp.ave_pos_alpha, cdp.ave_pos_beta, cdp.ave_pos_gamma, R)
        print("Rotation matrix:\n%s\n" % R)
        R = transpose(R)
        print("Inverted rotation:\n%s\n" % R)
        pivot = cdp.pivot

        # Create a special data pipe for the average rigid body position.
        pipe.create(pipe_name='ave pos', pipe_type='frame order')

        # Load the structure.
        structure.read_pdb('1J7P_1st_NH_rot.pdb', dir='..')

        # Rotate all atoms.
        structure.rotate(R=R, origin=pivot)

        # Write out the new PDB.
        structure.write_pdb('ave_pos', force=True)


# Execute the analysis.
Analysis()
