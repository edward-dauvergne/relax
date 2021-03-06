# Python module imports.
from numpy import array, cross, float64, transpose
from numpy.linalg import inv, norm
import sys

# relax module imports.
from lib.text.sectioning import title


# The paramagnetic centre in the 1J7O_1st_NH.pdb file.
centre = array([35.934, 12.194, -4.206], float64)

# Calculate and store the C-domain centre of mass.
pipe.create('C-dom', 'N-state')
structure.read_pdb('1J7P_1st_NH.pdb', dir='../cam')
structure.com()
c_com = cdp.com

# Create a new data pipe for building the base system.
pipe.create('base system', 'N-state')

# Load both domains.
structure.read_pdb('1J7O_1st_NH.pdb', dir='../cam', set_mol_name='N-dom')
structure.read_pdb('1J7P_1st_NH.pdb', dir='../cam', set_mol_name='C-dom')

# The paramagnetic centre-CoM distance.
dist = norm(c_com - centre)

# The frame of the CoM system.
z_ax = (c_com - centre) / dist
x_ax = array([1, 0, 0], float64)
y_ax = cross(z_ax, x_ax)
y_ax /= norm(y_ax)
R = transpose(array([x_ax, y_ax, z_ax], float64))

# Translate the paramagnetic centre to the origin.
structure.translate(T=-centre)

# Inverted frame rotation.
structure.rotate(R=inv(R))

# Add atoms for the CoMs.
structure.add_atom(atom_name='N', res_name='COM', res_num=1, chain_id='A', pos=[0., 0., 0.], element='Ti', pdb_record='HETATM')
structure.add_atom(atom_name='C', res_name='COM', res_num=1, chain_id='B', pos=[0., 0., dist], element='Ti', pdb_record='HETATM')

# Write out the final structure.
structure.write_pdb('base_system.pdb', force=True)

# The new CoM.
structure.com(atom_id="#C-dom")
c_com_new = cdp.com

# The new paramagnetic centre.
structure.load_spins(spin_id="#N-dom:1001")
centre_new = cdp.mol[0].res[0].spin[0].pos

# Printout.
title(file=sys.stdout, text="The base system")
print("The original system:\n")
print("%-25s %-70s" % ("Paramagnetic centre:", centre))
print("%-25s %-70s" % ("C-domain CoM:", c_com))
print("%-25s %-70s" % ("Inter-CoM distance:", dist))
print("%s\n%s" % ("R:", R))
print("\nThe new system:\n")
print("%-25s %-70s" % ("Paramagnetic centre:", centre_new))
print("%-25s %-70s" % ("C-domain CoM:", c_com_new))
print("%-25s %-70s" % ("Inter-CoM distance:", norm(c_com_new - centre_new)))
