###############################################################################
#                                                                             #
# Copyright (C) 2005-2014 Edward d'Auvergne                                   #
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

# Module docstring.
"""Module for interfacing with Dasha."""

# Dependencies.
import dep_check

# Python module imports.
from math import pi
from os import F_OK, access, chdir, getcwd, sep
PIPE, Popen = None, None
if dep_check.subprocess_module:
    from subprocess import PIPE, Popen
import sys

# relax module imports.
from lib.errors import RelaxDirError, RelaxError, RelaxFileError, RelaxNoPdbError, RelaxNoSequenceError, RelaxNoTensorError
from lib.io import extract_data, mkdir_nofail, open_write_file, strip, test_binary
from pipe_control import angles, diffusion_tensor, pipes, value
from pipe_control.interatomic import return_interatom_list
from pipe_control.mol_res_spin import exists_mol_res_spin_data, first_residue_num, last_residue_num, residue_loop, return_spin, spin_loop
from pipe_control.spectrometer import loop_frequencies
from specific_analyses.model_free.model import determine_model_type


def __deselect_spins():
    """Deselect spins with no or too little data, that are overfitting, etc."""

    # Test if sequence data exists.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Is structural data required?
    need_vect = False
    if hasattr(cdp, 'diff_tensor') and (cdp.diff_tensor.type == 'spheroid' or cdp.diff_tensor.type == 'ellipsoid'):
        need_vect = True

    # Loop over the sequence.
    for spin in spin_loop():
        # Relaxation data must exist!
        if not hasattr(spin, 'ri_data'):
            spin.select = False

        # Require 3 or more relaxation data points.
        elif len(spin.ri_data) < 3:
            spin.select = False

        # Require at least as many data points as params to prevent over-fitting.
        elif hasattr(spin, 'params') and spin.params and len(spin.params) > len(spin.ri_data):
            spin.select = False


def create(algor='LM', dir=None, force=False):
    """Create the Dasha script file 'dasha_script' for controlling the program.

    @keyword algor: The optimisation algorithm to use.  This can be the Levenberg-Marquardt algorithm 'LM' or the Newton-Raphson algorithm 'NR'.
    @type algor:    str
    @keyword dir:   The optional directory to place the script into.
    @type dir:      str or None
    @keyword force: A flag which if True will cause any pre-existing file to be overwritten.
    @type force:    bool
    """

    # Test if the current pipe exists.
    pipes.test()

    # Test if sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Determine the parameter set.
    model_type = determine_model_type()

    # Test if diffusion tensor data for the data_pipe exists.
    if model_type != 'local_tm' and not hasattr(cdp, 'diff_tensor'):
        raise RelaxNoTensorError('diffusion')

    # Test if the PDB file has been loaded (for the spheroid and ellipsoid).
    if model_type != 'local_tm' and cdp.diff_tensor.type != 'sphere' and not hasattr(cdp, 'structure'):
        raise RelaxNoPdbError

    # Test the optimisation algorithm.
    if algor not in ['LM', 'NR']:
        raise RelaxError("The Dasha optimisation algorithm '%s' is unknown, it should either be 'LM' or 'NR'." % algor)

    # Deselect certain spins.
    __deselect_spins()

    # Directory creation.
    if dir == None:
        dir = pipes.cdp_name()
    mkdir_nofail(dir, verbosity=0)

    # Calculate the angle alpha of the XH vector in the spheroid diffusion frame.
    if cdp.diff_tensor.type == 'spheroid':
        angles.spheroid_frame()

    # Calculate the angles theta and phi of the XH vector in the ellipsoid diffusion frame.
    elif cdp.diff_tensor.type == 'ellipsoid':
        angles.ellipsoid_frame()

    # The 'dasha_script' file.
    script = open_write_file(file_name='dasha_script', dir=dir, force=force)
    create_script(script, model_type, algor)
    script.close()


def create_script(file, model_type, algor):
    """Create the Dasha script file.

    @param file:        The opened file descriptor.
    @type file:         file object
    @param model_type:  The model-free model type.
    @type model_type:   str
    @param algor:       The optimisation algorithm to use.  This can be the Levenberg-Marquardt algorithm 'LM' or the Newton-Raphson algorithm 'NR'.
    @type algor:        str
    """

    # Delete all data.
    file.write("# Delete all data.\n")
    file.write("del 1 10000\n")

    # Nucleus type.
    file.write("\n# Nucleus type.\n")
    nucleus = None
    for spin in spin_loop():
        # Skip protons.
        if spin.isotope == '1H':
            continue

        # Can only handle one spin type.
        if nucleus and spin.isotope != nucleus:
            raise RelaxError("The nuclei '%s' and '%s' do not match, relax can only handle one nucleus type in Dasha." % (nucleus, spin.isotope))

        # Set the nucleus.
        if not nucleus:
            nucleus = spin.isotope

    # Convert the name and write it.
    if nucleus == '15N':
        nucleus = 'N15'
    elif nucleus == '13C':
        nucleus = 'C13'
    else:
        raise RelaxError("Cannot handle the nucleus type '%s' within Dasha." % nucleus)
    file.write("set nucl %s\n" % nucleus)

    # Number of frequencies.
    file.write("\n# Number of frequencies.\n")
    file.write("set n_freq %s\n" % cdp.spectrometer_frq_count)

    # Frequency values.
    file.write("\n# Frequency values.\n")
    count = 1
    for frq in loop_frequencies():
        file.write("set H1_freq %s %s\n" % (frq / 1e6, count))
        count += 1

    # Set the diffusion tensor.
    file.write("\n# Set the diffusion tensor.\n")
    if model_type != 'local_tm':
        # Sphere.
        if cdp.diff_tensor.type == 'sphere':
            file.write("set tr %s\n" % (cdp.diff_tensor.tm / 1e-9))

        # Spheroid.
        elif cdp.diff_tensor.type == 'spheroid':
            file.write('set tr %s\n' % (cdp.diff_tensor.tm / 1e-9))

        # Ellipsoid.
        elif cdp.diff_tensor.type == 'ellipsoid':
            # Get the eigenvales.
            Dx, Dy, Dz = diffusion_tensor.return_eigenvalues()

            # Geometric parameters.
            file.write("set tr %s\n" % (cdp.diff_tensor.tm / 1e-9))
            file.write("set D1/D3 %s\n" % (Dx / Dz))
            file.write("set D2/D3 %s\n" % (Dy / Dz))

            # Orientational parameters.
            file.write("set alfa %s\n" % (cdp.diff_tensor.alpha / (2.0 * pi) * 360.0))
            file.write("set betta %s\n" % (cdp.diff_tensor.beta / (2.0 * pi) * 360.0))
            file.write("set gamma %s\n" % (cdp.diff_tensor.gamma / (2.0 * pi) * 360.0))

    # Reading the relaxation data.
    file.write("\n# Reading the relaxation data.\n")
    file.write("echo Reading the relaxation data.\n")
    noe_index = 1
    r1_index = 1
    r2_index = 1
    for ri_id in cdp.ri_ids:
        # NOE.
        if cdp.ri_type[ri_id] == 'NOE':
            # Data set number.
            number = noe_index

            # Data type.
            data_type = 'noe'

            # Increment the data set index.
            noe_index = noe_index + 1

        # R1.
        elif cdp.ri_type[ri_id] == 'R1':
            # Data set number.
            number = r1_index

            # Data type.
            data_type = '1/T1'

            # Increment the data set index.
            r1_index = r1_index + 1

        # R2.
        elif cdp.ri_type[ri_id] == 'R2':
            # Data set number.
            number = r2_index

            # Data type.
            data_type = '1/T2'

            # Increment the data set index.
            r2_index = r2_index + 1

        # Set the data type.
        if number == 1:
            file.write("\nread < %s\n" % data_type)
        else:
            file.write("\nread < %s %s\n" % (data_type, number))

        # The relaxation data.
        for residue in residue_loop():
            # Alias the spin.
            spin = residue.spin[0]

            # Skip deselected spins.
            if not spin.select:
                continue

            # Skip and deselect spins for which relaxation data is missing.
            if len(spin.ri_data) != len(cdp.ri_ids) or spin.ri_data[ri_id] == None:
                spin.select = False
                continue

            # Data and errors.
            file.write("%s %s %s\n" % (residue.num, spin.ri_data[ri_id], spin.ri_data_err[ri_id]))

        # Terminate the reading.
        file.write("exit\n")

    # Individual residue optimisation.
    if model_type == 'mf':
        # Loop over the residues.
        for residue in residue_loop():
            # Alias the spin.
            spin = residue.spin[0]

            # Skip deselected spins.
            if not spin.select:
                continue

            # Get the interatomic data containers.
            interatoms = return_interatom_list(spin._spin_ids[0])
            if len(interatoms) == 0:
                raise RelaxNoInteratomError
            elif len(interatoms) > 1:
                raise RelaxError("Only one interatomic data container, hence dipole-dipole interaction, is supported per spin.")

            # Comment.
            file.write("\n\n\n# Residue %s\n\n" % residue.num)

            # Echo.
            file.write("echo Optimisation of residue %s\n" % residue.num)

            # Select the spin.
            file.write("\n# Select the residue.\n")
            file.write("set cres %s\n" % residue.num)

            # The angle alpha of the XH vector in the spheroid diffusion frame.
            if cdp.diff_tensor.type == 'spheroid':
                file.write("set teta %s\n" % spin.alpha)

            # The angles theta and phi of the XH vector in the ellipsoid diffusion frame.
            elif cdp.diff_tensor.type == 'ellipsoid':
                file.write("\n# Setting the spherical angles of the XH vector in the ellipsoid diffusion frame.\n")
                file.write("set teta %s\n" % spin.theta)
                file.write("set fi %s\n" % spin.phi)

            # The 'jmode'.
            if 'ts' in spin.params:
                jmode = 3
            elif 'te' in spin.params:
                jmode = 2
            elif 's2' in spin.params:
                jmode = 1

            # Chemical exchange.
            if 'rex' in spin.params:
                exch = True
            else:
                exch = False

            # Anisotropic diffusion.
            if cdp.diff_tensor.type == 'sphere':
                anis = False
            else:
                anis = True

            # Axial symmetry.
            if cdp.diff_tensor.type == 'spheroid':
                sym = True
            else:
                sym = False

            # Set the jmode.
            file.write("\n# Set the jmode.\n")
            file.write("set def jmode %s" % jmode)
            if exch:
                file.write(" exch")
            if anis:
                file.write(" anis")
            if sym:
                file.write(" sym")
            file.write("\n")

            # Parameter default values.
            file.write("\n# Parameter default values.\n")
            file.write("reset jmode %s\n" % residue.num)

            # Bond length.
            file.write("\n# Bond length.\n")
            file.write("set r_hx %s\n" % (interatoms[0].r / 1e-10))

            # CSA value.
            file.write("\n# CSA value.\n")
            file.write("set csa %s\n" % (spin.csa / 1e-6))

            # Fix the tf parameter if it isn't in the model.
            if not 'tf' in spin.params and jmode == 3:
                file.write("\n# Fix the tf parameter.\n")
                file.write("fix tf 0\n")

        # Optimisation of all residues.
        file.write("\n\n\n# Optimisation of all residues.\n")
        if algor == 'LM':
            file.write("lmin %s %s" % (first_residue_num(), last_residue_num()))
        elif algor == 'NR':
            file.write("min %s %s" % (first_residue_num(), last_residue_num()))

        # Show the results.
        file.write("\n# Show the results.\n")
        file.write("echo\n")
        file.write("show all\n")

        # Write the results.
        file.write("\n# Write the results.\n")
        file.write("write s2.out S\n")
        file.write("write s2f.out Sf\n")
        file.write("write s2s.out Ss\n")
        file.write("write te.out te\n")
        file.write("write tf.out tf\n")
        file.write("write ts.out ts\n")
        file.write("write rex.out rex\n")
        file.write("write chi2.out F\n")

    else:
        raise RelaxError("Optimisation of the parameter set '%s' currently not supported." % model_type)


def execute(dir, force, binary):
    """Execute Dasha.

    @param dir:     The optional directory where the script is located.
    @type dir:      str or None
    @param force:   A flag which if True will cause any pre-existing files to be overwritten by Dasha.
    @type force:    bool
    @param binary:  The name of the Dasha binary file.  This can include the path to the binary.
    @type binary:   str
    """

    # Test the binary file string corresponds to a valid executable.
    test_binary(binary)

    # The current directory.
    orig_dir = getcwd()

    # The directory.
    if dir == None:
        dir = pipes.cdp_name()
    if not access(dir, F_OK):
        raise RelaxDirError('Dasha', dir)

    # Change to this directory.
    chdir(dir)

    # Catch failures and return to the correct directory.
    try:
        # Test if the 'dasha_script' script file exists.
        if not access('dasha_script', F_OK):
            raise RelaxFileError('dasha script', 'dasha_script')

        # Python 2.3 and earlier.
        if Popen == None:
            raise RelaxError("The subprocess module is not available in this version of Python.")

        # Execute Dasha.
        pipe = Popen(binary, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=False)

        # Get the contents of the script and pump it into Dasha.
        script = open('dasha_script')
        lines = script.readlines()
        script.close()
        for line in lines:
            # Encode to a Python 3 byte array.
            if hasattr(line, 'encode'):
                line = line.encode()

            # Write out.
            pipe.stdin.write(line)

        # Close the pipe.
        pipe.stdin.close()

        # Write to stdout.
        for line in pipe.stdout.readlines():
            # Decode Python 3 byte arrays.
            if hasattr(line, 'decode'):
                line = line.decode()

            # Write.
            sys.stdout.write(line)

        # Write to stderr.
        for line in pipe.stderr.readlines():
            # Decode Python 3 byte arrays.
            if hasattr(line, 'decode'):
                line = line.decode()

            # Write.
            sys.stderr.write(line)

    # Failure.
    except:
        # Change back to the original directory.
        chdir(orig_dir)

        # Reraise the error.
        raise

    # Change back to the original directory.
    chdir(orig_dir)

    # Print some blank lines (aesthetics)
    sys.stdout.write("\n\n")


def extract(dir):
    """Extract the data from the Dasha results files.

    @param dir:     The optional directory where the results file is located.
    @type dir:      str or None
    """

    # Test if sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # The directory.
    if dir == None:
        dir = pipes.cdp_name()
    if not access(dir, F_OK):
        raise RelaxDirError('Dasha', dir)

    # Loop over the parameters.
    for param in ['s2', 's2f', 's2s', 'te', 'tf', 'ts', 'rex']:
        # The file name.
        file_name = dir + sep + param + '.out'

        # Test if the file exists.
        if not access(file_name, F_OK):
            raise RelaxFileError('Dasha', file_name)

        # Scaling.
        if param in ['te', 'tf', 'ts']:
            scaling = 1e-9
        elif param == 'rex':
            scaling = 1.0 / (2.0 * pi * cdp.spectrometer_frq[cdp.ri_ids[0]]) ** 2
        else:
            scaling = 1.0

        # Read the values.
        data = read_results(file=file_name, scaling=scaling)

        # Set the values.
        for i in range(len(data)):
            value.set(val=data[i][1], param=param, spin_id=data[i][0])
            value.set(val=data[i][0], param=param, spin_id=data[i][0], error=True)

        # Clean up of non-existent parameters (set the parameter to None!).
        for spin in spin_loop():
            # Skip the spin (don't set the parameter to None) if the parameter exists in the model.
            if param in spin.params:
                continue

            # Set the parameter to None.
            setattr(spin, param.lower(), None)

    # Extract the chi-squared values.
    file_name = dir + sep+'chi2.out'

    # Test if the file exists.
    if not access(file_name, F_OK):
        raise RelaxFileError('Dasha', file_name)

    # Read the values.
    data = read_results(file=file_name)

    # Set the values.
    for i in range(len(data)):
        spin = return_spin(data[i][0])
        spin.chi2 = data[i][1]


def read_results(file=None, dir=None, scaling=1.0):
    """Extract the data from the Dasha results file.

    @keyword file:          The name of the file to open.
    @type file:             str
    @keyword dir:           The directory containing the file (defaults to the current directory if None).
    @type dir:              str or None
    @keyword scaling:       The parameter scaling factor.
    @type scaling:          float
    """

    # Extract the data.
    data = extract_data(file=file, dir=dir)

    # Remove comments.
    data = strip(data)

    # Repackage the data as a list of lists of spin ID, value, error.
    new_data = []
    for i in range(len(data)):
        spin_id = ':%s@N' % data[i][0]
        value = float(data[i][1]) * scaling
        error = float(data[i][2]) * scaling
        new_data.append([spin_id, value, error])

    # Return the data.
    return new_data
