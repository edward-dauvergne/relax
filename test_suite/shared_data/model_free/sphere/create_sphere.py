#!/usr/bin/python

# Copyright 2004-2011, Edward d'Auvergne

from math import acos, cos, pi, sin, sqrt


def pdb_line(file=None, atom_num=0, atom=None, res_num=0, res_name=None, vector=None):
    """Function for adding a line to the PDB file."""

    # ATOM.
    file.write('%-4s' % 'ATOM')

    # Atom number and type.
    file.write('%7i' % atom_num)
    file.write('  %-4s' % atom)

    # Residue number and name.
    file.write('%-4s' % res_name)
    file.write('%5i    ' % res_num)

    # Vector.
    file.write('%8.3f' % vector[0])
    file.write('%8.3f' % vector[1])
    file.write('%8.3f' % vector[2])

    # I don't know what.
    file.write('%6.2f' % 1.0)
    file.write('%6.2f' % 0.0)

    # End of line.
    file.write('\n')


# Number of increments.
number = 3

# U and V.
u = []
val = 1.0 / float(number)
for i in range(number):
    u.append(float(i) * val)


# Generate the spherical angles theta and phi.
##############################################

theta = []
phi = []
for i in range(len(u)):
    theta.append(acos(2.0 * (u[i] + val/2.0) - 1.0))
    phi.append(2.0 * pi * u[i])
    print("\ni: %s" % i)
    print("u: %s" % u[i])
    print("v: %s" % (u[i] + val/2.0))
    print("theta: %s" % theta[i])
    print("phi: %s" % phi[i])


# Generate the vectors:
#
#                 | sin(theta) * cos(phi) |
#      vector  =  | sin(theta) * sin(phi) |
#                 |      cos(theta)       |
#
###########################################

vectors = []
for i in range(len(u)):
    for j in range(len(u)):
        # X coordinate.
        x = sin(theta[i]) * cos(phi[j])

        # Y coordinate.
        y = sin(theta[i]) * sin(phi[j])

        # Z coordinate.
        z = cos(theta[i])

        # Append the vector.
        vectors.append([x, y, z])


# Create the PDB file.
######################

# PDB file.
file = open('sphere.pdb', 'w')

# Atom number and residue number.
atom_num = 1
res_num = 1

# Used vectors.
used = []

# Loop over the vectors. 
for i in range(len(vectors)):
    # Test if the vector has already been used.
    if vectors[i] in used:
        print("Vector %s already used." % vectors[i])
        continue

    # Nitrogen line.
    pdb_line(file=file, atom_num=atom_num, atom='N', res_num=res_num, res_name='GLY', vector=[0.0, 0.0, 0.0])

    # Hydrogen line.
    pdb_line(file=file, atom_num=atom_num+1, atom='H', res_num=res_num, res_name='GLY', vector=vectors[i])

    # Increment the atom number and residue number.
    atom_num = atom_num + 2
    res_num = res_num + 1

    # Add the vector to the used vector list.
    used.append(vectors[i])

# Add a Trp indole NH for luck ;)
pdb_line(file=file, atom_num=atom_num, atom='NE1', res_num=res_num-1, res_name='GLY', vector=[0.0, 0.0, 0.0])
pdb_line(file=file, atom_num=atom_num+1, atom='HE1', res_num=res_num-1, res_name='GLY', vector=[1/sqrt(3), 1/sqrt(3), 1/sqrt(3)])

# End of PDB.
file.write('END\n')
