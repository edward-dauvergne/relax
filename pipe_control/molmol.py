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

# Module docstring.
"""Module for interfacing with Molmol."""

# Dependencies.
import dep_check

# Python module imports.
from os import F_OK, access, sep
PIPE, Popen = None, None
if dep_check.subprocess_module:
    from subprocess import PIPE, Popen
from time import sleep

# relax module imports.
from lib.errors import RelaxError, RelaxNoSequenceError
from lib.io import get_file_path, open_read_file, open_write_file, test_binary
from pipe_control.mol_res_spin import exists_mol_res_spin_data
from pipe_control import pipes
from pipe_control.result_files import add_result_file
from specific_analyses.api import return_api
from status import Status; status = Status()


class Molmol:
    """The Molmol execution object."""

    def __init__(self):
        """Set up the Molmol execution object."""

        # Variable for storing the Molmol command history.
        self.command_history = ""


    def clear_history(self):
        """Clear the Molmol command history."""

        self.command_history = ""


    def exec_cmd(self, command=None, store_command=True):
        """Write to the Molmol pipe.

        This function is also used to execute a user supplied Molmol command.


        @param command:         The Molmol command to send into the program.
        @type command:          str
        @param store_command:   A flag specifying if the command should be stored in the history
                                variable.
        @type store_command:    bool
        """

        # Reopen the pipe if needed.
        if not self.running():
            self.open_gui()

        # Write the command to the pipe.
        self.molmol.write(command + '\n')

        # Place the command in the command history.
        if store_command:
            self.command_history = self.command_history + command + "\n"


    def open_gui(self):
        """Open a Molmol pipe."""

        # Test that the Molmol binary exists.
        test_binary('molmol')

        # Python 2.3 and earlier.
        if Popen == None:
            raise RelaxError("The subprocess module is not available in this version of Python.")

        # Open Molmol as a pipe.
        self.molmol = Popen(['molmol', '-f', '-'], stdin=PIPE).stdin

        # Execute the command history.
        if len(self.command_history) > 0:
            self.exec_cmd(self.command_history, store_command=0)
            return

        # Wait a little while for Molmol to initialise.
        sleep(2)

        # Test if the PDB file has been loaded.
        if hasattr(cdp, 'structure'):
            self.open_pdb()

        # Run InitAll to remove everything from Molmol.
        else:
            self.molmol.write("InitAll yes\n")


    def open_pdb(self):
        """Open the PDB file in Molmol."""

        # Test if Molmol is running.
        if not self.running():
            return

        # Run InitAll to remove everything from molmol.
        self.exec_cmd("InitAll yes")

        # Open the PDB files.
        open_files = []
        for model in cdp.structure.structural_data:
            for mol in model.mol:
                # The file path as the current directory.
                file_path = None
                if access(mol.file_name, F_OK):
                    file_path = mol.file_name

                # The file path using the relative path.
                if file_path == None and hasattr(mol, 'file_path') and mol.file_path != None:
                    file_path = mol.file_path + sep + mol.file_name
                    if not access(file_path, F_OK):
                        file_path = None

                # The file path using the absolute path.
                if file_path == None and hasattr(mol, 'file_path_abs') and mol.file_path_abs != None:
                    file_path = mol.file_path_abs + sep + mol.file_name
                    if not access(file_path, F_OK):
                        file_path = None

                # Hmmm, maybe the absolute path no longer exists and we are in a results subdirectory?
                if file_path == None and hasattr(mol, 'file_path') and mol.file_path != None:
                    file_path = pardir + sep + mol.file_path + sep + mol.file_name
                    if not access(file_path, F_OK):
                        file_path = None

                # Fall back to the current directory.
                if file_path == None:
                    file_path = mol.file_name

                # Already loaded.
                if file_path in open_files:
                    continue

                # Open the file in Molmol.
                self.exec_cmd("ReadPdb " + file_path)

                # Add to the open file list.
                open_files.append(file_path)


    def running(self):
        """Test if Molmol is running.

        @return:    Whether the Molmol pipe is open or not.
        @rtype:     bool
        """

        # Pipe exists.
        if not hasattr(self, 'molmol'):
            return False

        # Test if the pipe has been broken.
        try:
            self.molmol.write('\n')
        except IOError:
            import sys
            sys.stderr.write("Broken pipe")
            return False

        # Molmol is running
        return True



# Initialise the Molmol executable object.
molmol_obj = Molmol()
"""Molmol data container instance."""




def command(command):
    """Function for sending Molmol commands to the program pipe.

    @param command: The command to send into the program.
    @type command:  str
    """

    # Pass the command to Molmol.
    molmol_obj.exec_cmd(command)


def create_macro(data_type=None, style="classic", colour_start=None, colour_end=None, colour_list=None):
    """Create an array of Molmol commands.

    @keyword data_type:     The data type to map to the structure.
    @type data_type:        str
    @keyword style:         The style of the macro.
    @type style:            str
    @keyword colour_start:  The starting colour of the linear gradient.
    @type colour_start:     str or RBG colour array (len 3 with vals from 0 to 1)
    @keyword colour_end:    The ending colour of the linear gradient.
    @type colour_end:       str or RBG colour array (len 3 with vals from 0 to 1)
    @keyword colour_list:   The colour list to search for the colour names.  Can be either 'molmol' or 'x11'.
    @type colour_list:      str or None
    @return:                The list of Molmol commands.
    @rtype:                 list of str
    """

    # Get the specific macro.
    api = return_api()
    commands = api.molmol_macro(data_type, style, colour_start, colour_end, colour_list)

    # Return the macro commands.
    return commands


def macro_apply(data_type=None, style="classic", colour_start_name=None, colour_start_rgb=None, colour_end_name=None, colour_end_rgb=None, colour_list=None):
    """Execute a Molmol macro.

    @keyword data_type:         The data type to map to the structure.
    @type data_type:            str
    @keyword style:             The style of the macro.
    @type style:                str
    @keyword colour_start_name: The name of the starting colour of the linear gradient.
    @type colour_start_name:    str
    @keyword colour_start_rgb:  The RGB array starting colour of the linear gradient.
    @type colour_start_rgb:     RBG colour array (len 3 with vals from 0 to 1)
    @keyword colour_end_name:   The name of the ending colour of the linear gradient.
    @type colour_end_name:      str
    @keyword colour_end_rgb:    The RGB array ending colour of the linear gradient.
    @type colour_end_rgb:       RBG colour array (len 3 with vals from 0 to 1)
    @keyword colour_list:       The colour list to search for the colour names.  Can be either 'molmol' or 'x11'.
    @type colour_list:          str or None
    """

    # Test if the current data pipe exists.
    pipes.test()

    # Test if sequence data exists.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Check the arguments.
    if colour_start_name != None and colour_start_rgb != None:
        raise RelaxError("The starting colour name and RGB colour array cannot both be supplied.")
    if colour_end_name != None and colour_end_rgb != None:
        raise RelaxError("The ending colour name and RGB colour array cannot both be supplied.")

    # Merge the colour args.
    if colour_start_name != None:
        colour_start = colour_start_name
    else:
        colour_start = colour_start_rgb
    if colour_end_name != None:
        colour_end = colour_end_name
    else:
        colour_end = colour_end_rgb

    # Create the macro.
    commands = create_macro(data_type=data_type, style=style, colour_start=colour_start, colour_end=colour_end, colour_list=colour_list)

    # Loop over the commands and execute them.
    for command in commands:
        molmol_obj.exec_cmd(command)


def macro_run(file=None, dir=None):
    """Execute the Molmol macro from the given text file.

    @keyword file:          The name of the macro file to execute.
    @type file:             str
    @keyword dir:           The name of the directory where the macro file is located.
    @type dir:              str
    """

    # Open the file for reading.
    file_path = get_file_path(file, dir)
    file = open_read_file(file, dir)

    # Loop over the commands and apply them.
    for command in file.readlines():
        molmol_obj.exec_cmd(command)


def macro_write(data_type=None, style="classic", colour_start_name=None, colour_start_rgb=None, colour_end_name=None, colour_end_rgb=None, colour_list=None, file=None, dir=None, force=False):
    """Create a Molmol macro.

    @keyword data_type:         The data type to map to the structure.
    @type data_type:            str
    @keyword style:             The style of the macro.
    @type style:                str
    @keyword colour_start_name: The name of the starting colour of the linear gradient.
    @type colour_start_name:    str
    @keyword colour_start_rgb:  The RGB array starting colour of the linear gradient.
    @type colour_start_rgb:     RBG colour array (len 3 with vals from 0 to 1)
    @keyword colour_end_name:   The name of the ending colour of the linear gradient.
    @type colour_end_name:      str
    @keyword colour_end_rgb:    The RGB array ending colour of the linear gradient.
    @type colour_end_rgb:       RBG colour array (len 3 with vals from 0 to 1)
    @keyword colour_list:       The colour list to search for the colour names.  Can be either 'molmol' or 'x11'.
    @type colour_list:          str or None
    @keyword file:              The name of the macro file to create.
    @type file:                 str
    @keyword dir:               The name of the directory to place the macro file into.
    @type dir:                  str
    @keyword force:             Flag which if set to True will cause any pre-existing file to be overwritten.
    @type force:                bool
    """

    # Test if the current data pipe exists.
    pipes.test()

    # Test if sequence data exists.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Check the arguments.
    if colour_start_name != None and colour_start_rgb != None:
        raise RelaxError("The starting colour name and RGB colour array cannot both be supplied.")
    if colour_end_name != None and colour_end_rgb != None:
        raise RelaxError("The ending colour name and RGB colour array cannot both be supplied.")

    # Merge the colour args.
    if colour_start_name != None:
        colour_start = colour_start_name
    else:
        colour_start = colour_start_rgb
    if colour_end_name != None:
        colour_end = colour_end_name
    else:
        colour_end = colour_end_rgb

    # Create the macro.
    commands = create_macro(data_type=data_type, style=style, colour_start=colour_start, colour_end=colour_end, colour_list=colour_list)

    # File name.
    if file == None:
        file = data_type + '.mac'

    # Open the file for writing.
    file_path = get_file_path(file, dir)
    file = open_write_file(file, dir, force)

    # Loop over the commands and write them.
    for command in commands:
        file.write(command + "\n")

    # Close the file.
    file.close()

    # Add the file to the results file list.
    add_result_file(type='molmol', label='Molmol', file=file_path)


def ribbon():
    """Apply the Molmol ribbon style."""

    # Calculate the protons.
    molmol_obj.exec_cmd("CalcAtom 'H'")
    molmol_obj.exec_cmd("CalcAtom 'HN'")

    # Calculate the secondary structure.
    molmol_obj.exec_cmd("CalcSecondary")

    # Execute the ribbon macro.
    molmol_obj.exec_cmd("XMacStand ribbon.mac")


def tensor_pdb(file=None):
    """Display the diffusion tensor geometric structure.

    @keyword file:  The name of the PDB file containing the tensor geometric object.
    @type file:     str
    """

    # Test if the current data pipe exists.
    pipes.test()

    # To overlay the structure with the diffusion tensor, select all and reorient to the PDB frame.
    molmol_obj.exec_cmd("SelectAtom ''")
    molmol_obj.exec_cmd("SelectBond ''")
    molmol_obj.exec_cmd("SelectAngle ''")
    molmol_obj.exec_cmd("SelectDist ''")
    molmol_obj.exec_cmd("SelectPrim ''")
    molmol_obj.exec_cmd("RotateInit")
    molmol_obj.exec_cmd("MoveInit")

    # Read in the tensor PDB file and force Molmol to recognise the CONECT records (not that it will show the bonds)!
    molmol_obj.exec_cmd("ReadPdb " + file)
    file_parts = file.split('.')
    molmol_obj.exec_cmd("SelectMol '@" + file_parts[0] + "'")
    molmol_obj.exec_cmd("CalcBond 1 1 1")

    # Apply the 'ball/stick' style to the tensor.
    molmol_obj.exec_cmd("SelectAtom '0'")
    molmol_obj.exec_cmd("SelectBond '0'")
    molmol_obj.exec_cmd("SelectAtom ':TNS'")
    molmol_obj.exec_cmd("SelectBond ':TNS'")
    molmol_obj.exec_cmd("XMacStand ball_stick.mac")

    # Touch up.
    molmol_obj.exec_cmd("RadiusAtom 1")
    molmol_obj.exec_cmd("SelectAtom ':TNS@C*'")
    molmol_obj.exec_cmd("RadiusAtom 1.5")


def view():
    """Start Molmol."""

    # Open a Molmol pipe.
    if molmol_obj.running():
        raise RelaxError("The Molmol pipe already exists.")
    else:
        molmol_obj.open_gui()
