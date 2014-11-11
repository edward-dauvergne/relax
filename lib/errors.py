###############################################################################
#                                                                             #
# Copyright (C) 2003-2014 Edward d'Auvergne                                   #
# Copyright (C) 2014 Troels E. Linnet                                         #
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
"""Module containing all of the RelaxError objects."""


# Python module imports.
try:
    from bz2 import BZ2File
    bz2 = True
except ImportError:
    bz2 = False
from re import match
import sys
import time

# relax module imports.
from lib import ansi
from lib.compat import pickle


# Module variables for changing the behaviour of the warning system.
SAVE_ERROR_STATE = False    # If True, then a pickled state file will be saved when a RelaxError occurs.

# Text variables.
BIN = 'a binary number (0 or 1)'
BOOL = 'a Boolean (True or False)'
INT = 'an integer'
FILE = 'a file object'
FLOAT = 'a floating point number'
FUNC = 'a function'
LIST = 'a list'
LIST_FLOAT = 'a list of floating point numbers'
LIST_INT = 'a list of integers'
LIST_NUM = 'a list of numbers'
LIST_STR = 'a list of strings'
LIST_VAL = 'a list of values'
MATRIX_FLOAT = 'a matrix of floating point numbers'
NONE = 'None'
NUM = 'a number'
TUPLE = 'a tuple'
TUPLE_FLOAT = 'a tuple of floating point numbers'
TUPLE_INT = 'a tuple of integers'
TUPLE_NUM = 'a tuple of numbers'
TUPLE_STR = 'a tuple of strings'
STR = 'a string'
VAL = 'a value'


def save_state():
    """Save the program state, for debugging purposes."""

    # relax data store singleton import.  Must be done here!
    try:
        from data_store import Relax_data_store; ds = Relax_data_store()

    # Ok, this is not relax so don't do anything!
    except ImportError:
        return

    # Append the date and time to the save file.
    now = time.localtime()
    file_name = "relax_state_%i%02i%02i_%02i%02i%02i" % (now[0], now[1], now[2], now[3], now[4], now[5])

    # Open the file for writing.
    if bz2:
        sys.stderr.write("\nStoring the relax state in the file '%s.bz2'.\n\n" % file_name)
        file = BZ2File(file_name+'.bz2', 'w')
    else:
        sys.stderr.write("\nStoring the relax state in the file '%s'.\n\n" % file_name)
        file = open(file_name, 'w')

    # Pickle the data class and write it to file
    pickle.dump(ds, file, 1)

    # Close the file.
    file.close()


def list_to_text(data):
    """Convert the given Python list to a text representation.

    @param data:    The list of Python objects.
    @type data:     list
    @return:        The English text version of the list.
    @rtype:         str
    """

    # Initialise.
    text = ''

    # Loop over the elements, adding the to the list.
    for i in range(len(data)):
        # Add the text.
        text += repr(data[i])

        # Comma separators.
        if i < len(data) - 2:
            text += ', '

        # Last separator.
        if i == len(data) - 2:
            text += ' and '

    # Return the text.
    return text


# Base class for all errors.
############################

class BaseError(Exception):
    """The base class for all RelaxErrors."""

    def __str__(self):
        """Modify the behaviour of the error system."""

        # Save the state if the escalate flag is turned on.
        if SAVE_ERROR_STATE:
            save_state()

        # Modify the error message to include 'RelaxError' at the start (using coloured text if a TTY).
        if ansi.enable_control_chars(stream=2):
            return ("%sRelaxError: %s%s\n" % (ansi.relax_error, self.text, ansi.end))
        else:
            return ("RelaxError: %s\n" % self.text)


class BaseArgError(BaseError):
    """The base class for all the argument related RelaxErrors."""

    # The allowed simple types.
    simple_types = []

    # The allowed list types (anything with a size).
    list_types = []


    def __init__(self, name, value, size=None):
        """A default initialisation and error message formatting method."""

        # The initial part of the message.
        self.text = "The %s argument '%s' must be " % (name, value)

        # Append the fixed size to the list types.
        if size != None:
            for i in range(len(self.list_types)):
                self.list_types[i] = self.list_types[i] + " of size %s" % repr(size)

        # Combine all elements.
        all_types = self.simple_types + self.list_types

        # Multiple elements.
        if len(all_types) > 1:
            self.text = self.text + "either "

        # Generate the list string.
        for i in range(len(all_types)):
            # Separators.
            if i > 0:
                # Or.
                if i == len(all_types)-1:
                    self.text = self.text + ", or "

                # Commas.
                else:
                    self.text = self.text + ", "

            # Append the text.
            self.text = self.text + all_types[i]

        # The end.
        self.text = self.text + "."


# Standard errors.
##################

class RelaxError(BaseError):
    def __init__(self, text):
        self.text = text


# Module import errors.
#######################

class RelaxNoModuleInstallError(BaseError):
    def __init__(self, desc, name):
        self.text = "The %s module '%s' cannot be found.  Please check that it is installed." % (desc, name)


# Fault.
########

class RelaxFault(BaseError):
    def __init__(self):
        self.text = "Impossible to be here, please re-run relax with the '--debug' flag and summit a bug report at https://gna.org/projects/relax/."

    def __str__(self):
        # Save the program state, no matter what.
        save_state()

        # Modify the error message to include 'RelaxError' at the start.
        return ("RelaxError: " + self.text + "\n")


# Code implementation errors.
#############################

# Not implemented yet.
class RelaxImplementError(BaseError):
    def __init__(self, fn_name=None):
        if fn_name:
            self.text = "The %s function has not yet been implemented for the current data pipe." % fn_name
        else:
            self.text = "This has not yet been implemented for the current data pipe."


# Program errors.
#################

# Cannot locate the program.
class RelaxProgError(BaseError):
    def __init__(self, name):
        self.text = "The program " + repr(name) + " cannot be found."


# The binary executable file does not exist (full path has been given!).
class RelaxMissingBinaryError(BaseError):
    def __init__(self, name):
        self.text = "The binary executable file " + repr(name) + " does not exist."


# The binary executable file is not executable.
class RelaxNonExecError(BaseError):
    def __init__(self, name):
        self.text = "The binary executable file " + repr(name) + " is not executable."


# The binary executable file is not located within the system path.
class RelaxNoInPathError(BaseError):
    def __init__(self, name):
        self.text = "The binary executable file " + repr(name) + " is not located within the system path."


# Program execution failure.
class RelaxProgFailError(BaseError):
    def __init__(self, name):
        self.text = "Execution of the program " + name + " has failed."


# PDB errors.
#############

# PDB data corresponding to the data pipe already exists.
class RelaxPdbError(BaseError):
    def __init__(self, pipe=None):
        if pipe != None:
            self.text = "PDB data corresponding to the data pipe " + repr(pipe) + " already exists."
        else:
            self.text = "PDB data already exists."

# No PDB loaded.
class RelaxNoPdbError(BaseError):
    def __init__(self, pipe=None):
        if pipe != None:
            self.text = "No PDB file has been loaded for the data pipe " + repr(pipe) + "."
        else:
            self.text = "No PDB file has been loaded."

# Loading error.
class RelaxPdbLoadError(BaseError):
    def __init__(self, name):
        self.text = "The PDB file " + repr(name) + " could not be loaded properly, no molecular chains could be extracted."

# Multiple unit vectors.
class RelaxMultiVectorError(BaseError):
    def __init__(self, spin_id=None):
        if spin_id != None:
            self.text = "The multiple unit XH bond vectors for the spin '%s' - this is not supported by the current data pipe type." % spin_id
        else:
            self.text = "The multiple unit XH bond vectors per spin - this is not supported by the current data pipe type."

# No unit vectors.
class RelaxNoVectorsError(BaseError):
    def __init__(self, pipe=None):
        if pipe:
            self.text = "No unit vectors have been calculated for the data pipe '%s'" % pipe
        else:
            self.text = "No unit vectors have been calculated."

# No chains within the PDB file.
class RelaxNoPdbChainError(BaseError):
    def __init__(self):
        self.text = "No peptide or nucleotide chains can be found within the PDB file."


# Nuclear errors.
#################

# Nucleus not set.
class RelaxNucleusError(BaseError):
    def __init__(self, spin_id=None):
        if spin_id != None:
            self.text = "The type of nucleus for the spin '%s' has not yet been set." % spin_id
        else:
            self.text = "The type of nucleus has not yet been set."

# Spin type not set.
class RelaxSpinTypeError(BaseError):
    def __init__(self, spin_id=None):
        if spin_id != None:
            self.text = "The nuclear isotope type for the spin '%s' has not yet been set.  Please use the spin.isotope user function to set the type." % spin_id
        else:
            self.text = "The nuclear isotope type has not yet been set.  Please use the spin.isotope user function to set the type."


# Argument errors.
##################


# Misc.
#~~~~~~

# Invalid argument.
class RelaxInvalidError(BaseArgError):
    def __init__(self, name, value):
        self.text = "The " + name + " argument " + repr(value) + " is invalid."

# Argument not in the list.
class RelaxArgNotInListError(BaseArgError):
    def __init__(self, name, value, list):
        self.text = "The " + name + " argument " + repr(value) + " is neither "
        for i in range(len(list)-1):
            self.text = self.text + repr(list[i]) + ', '
        self.text = self.text + 'nor ' + repr(list[-1]) + "."

# Length of the list.
class RelaxLenError(BaseArgError):
    def __init__(self, name, len):
        self.text = "The " + name + " argument must be of length " + repr(len) + "."

# None.
class RelaxNoneError(BaseArgError):
    def __init__(self, name):
        self.text = "The " + name + " argument has not been supplied."

# Not None.
class RelaxArgNotNoneError(BaseArgError):
    def __init__(self, name, value):
        self.text = "The %s argument of '%s' must be None."


# Simple types.
#~~~~~~~~~~~~~~

# Boolean - the values True and False.
class RelaxBoolError(BaseArgError):
    simple_types = [BOOL]

# Binary - integers 0 and 1.
class RelaxBinError(BaseArgError):
    simple_types = [BIN]

# Float.
class RelaxFloatError(BaseArgError):
    simple_types = [FLOAT]

class RelaxNoneFloatError(BaseArgError):
    simple_types = [NONE, FLOAT]

# Number.
class RelaxNumError(BaseArgError):
    simple_types = [NUM]

class RelaxNoneNumError(BaseArgError):
    simple_types = [NONE, NUM]

# Function.
class RelaxFunctionError(BaseArgError):
    simple_types = [FUNC]

class RelaxNoneFunctionError(BaseArgError):
    simple_types = [NONE, FUNC]

# Integer.
class RelaxIntError(BaseArgError):
    simple_types = [INT]

class RelaxNoneIntError(BaseArgError):
    simple_types = [NONE, INT]

# String.
class RelaxStrError(BaseArgError):
    simple_types = [STR]

class RelaxNoneStrError(BaseArgError):
    simple_types = [NONE, STR]


# Simple mixes.
#~~~~~~~~~~~~~~

# Integer or string.
class RelaxIntStrError(BaseArgError):
    simple_types = [INT, STR]

class RelaxNoneIntStrError(BaseArgError):
    simple_types = [NONE, INT, STR]

# String or file descriptor.
class RelaxStrFileError(BaseArgError):
    simple_types = [STR, FILE]

class RelaxNoneStrFileError(BaseArgError):
    simple_types = [NONE, STR, FILE]


# List types.
#~~~~~~~~~~~~


# List.
class RelaxListError(BaseArgError):
    list_types = [LIST]

class RelaxNoneListError(BaseArgError):
    simple_types = [NONE]
    list_types = [LIST]

# List of floating point numbers.
class RelaxListFloatError(BaseArgError):
    list_types = [LIST_FLOAT]

class RelaxNoneListFloatError(BaseArgError):
    list_types = [LIST_FLOAT]

# List of floating point numbers or strings.
class RelaxListFloatStrError(BaseArgError):
    list_types = [LIST_FLOAT, LIST_STR]

# List of integers.
class RelaxListIntError(BaseArgError):
    list_types = [LIST_INT]

# List of integers.
class RelaxNoneListIntError(BaseArgError):
    simple_types = [NONE]
    list_types = [LIST_INT]

# List of numbers.
class RelaxListNumError(BaseArgError):
    list_types = [LIST_NUM]

class RelaxNoneListNumError(BaseArgError):
    simple_types = [NONE]
    list_types = [LIST_NUM]

# List of strings.
class RelaxListStrError(BaseArgError):
    list_types = [LIST_STR]

class RelaxNoneListStrError(BaseArgError):
    simple_types = [NONE]
    list_types = [LIST_STR]


# Simple or list types.
#~~~~~~~~~~~~~~~~~~~~~~

# Float or list.
class RelaxNoneFloatListError(BaseArgError):
    simple_types = [NONE, FLOAT]
    list_types = [LIST]

# Float, str, or list.
class RelaxNoneFloatStrListError(BaseArgError):
    simple_types = [NONE, FLOAT, STR]
    list_types = [LIST]

# Integer or list of integers.
class RelaxIntListIntError(BaseArgError):
    simple_types = [INT]
    list_types = [LIST_INT]

class RelaxNoneIntListIntError(BaseArgError):
    simple_types = [NONE, INT]
    list_types = [LIST_INT]

# Number, string, or list of numbers or strings.
class RelaxNumStrListNumStrError(BaseArgError):
    simple_types = [NUM, STR]
    list_types = [LIST_NUM, LIST_STR]

class RelaxNoneNumStrListNumStrError(BaseArgError):
    simple_types = [NONE, NUM, STR]
    list_types = [LIST_NUM, LIST_STR]

# String or list.
class RelaxNoneStrListError(BaseArgError):
    simple_types = [NONE, STR]
    list_types = [LIST]

# String or list of numbers.
class RelaxStrListNumError(BaseArgError):
    simple_types = [STR]
    list_types = [LIST_NUM]

class RelaxNoneStrListNumError(BaseArgError):
    simple_types = [NONE, STR]
    list_types = [LIST_NUM]

# String or list of strings.
class RelaxStrListStrError(BaseArgError):
    simple_types = [STR]
    list_types = [LIST_STR]

class RelaxNoneStrListStrError(BaseArgError):
    simple_types = [NONE, STR]
    list_types = [LIST_STR]

# Value or list of values.
class RelaxValListValError(BaseArgError):
    simple_types = [VAL]
    list_types = [LIST_VAL]

class RelaxNoneValListValError(BaseArgError):
    simple_types = [NONE, VAL]
    list_types = [LIST_VAL]


# Tuple types.
#~~~~~~~~~~~~~

# Tuple.
class RelaxTupleError(BaseArgError):
    list_types = [TUPLE]

class RelaxNoneTupleError(BaseArgError):
    simple_types = [NONE]
    list_types = [TUPLE]

# Tuple of numbers.
class RelaxTupleNumError(BaseArgError):
    list_types = [TUPLE_NUM]


# Simple or tuple types.
#~~~~~~~~~~~~~~~~~~~~~~~

# Number or tuple.
class RelaxNumTupleError(BaseArgError):
    simple_types = [NUM]
    list_types = [TUPLE]

# Number or tuple of numbers.
class RelaxNumTupleNumError(BaseArgError):
    simple_types = [NUM]
    list_types = [TUPLE_NUM]

class RelaxNoneNumTupleNumError(BaseArgError):
    simple_types = [NONE, NUM]
    list_types = [TUPLE_NUM]


# Matrix types.
#~~~~~~~~~~~~~~

# Matrix of floating point numbers.
class RelaxMatrixFloatError(BaseArgError):
    list_types = [MATRIX_FLOAT]

class RelaxNoneMatrixFloatError(BaseArgError):
    list_types = [MATRIX_FLOAT]



# Sequence errors.
##################

# No sequence loaded.
class RelaxNoSequenceError(BaseError):
    def __init__(self, pipe=None):
        if pipe == None:
            self.text = "The sequence data does not exist."
        else:
            self.text = "The sequence data for the data pipe " + repr(pipe) + " does not exist."

# The sequence already exists.
class RelaxSequenceError(BaseError):
    def __init__(self, pipe=None):
        if pipe == None:
            self.text = "The sequence data already exists."
        else:
            self.text = "The sequence data for the data pipe " + repr(pipe) + " already exists."

# The two sequences are different.
class RelaxDiffSeqError(BaseError):
    def __init__(self, pipe1, pipe2):
        self.text = "The sequences for the data pipes " + repr(pipe1) + " and " + repr(pipe2) + " are not the same."

# The number of molecules are different.
class RelaxDiffMolNumError(BaseError):
    def __init__(self, pipe1, pipe2):
        self.text = "The number of molecules do not match between pipes '%s' and '%s'." % (pipe1, pipe2)

# The number of residues are different.
class RelaxDiffResNumError(BaseError):
    def __init__(self, pipe1, pipe2):
        self.text = "The number of residues do not match between pipes '%s' and '%s'." % (pipe1, pipe2)

# The number of spins are different.
class RelaxDiffSpinNumError(BaseError):
    def __init__(self, pipe1, pipe2):
        self.text = "The number of spins do not match between pipes '%s' and '%s'." % (pipe1, pipe2)

# Multiple spins matching the ID.
class RelaxMultiMolIDError(BaseError):
    def __init__(self, id):
        if id == '':
            self.text = "The empty molecule ID corresponds to more than a single molecule in the current data pipe."
        else:
            self.text = "The molecule ID '%s' corresponds to more than a single molecule in the current data pipe." % id

# Multiple spins matching the ID.
class RelaxMultiResIDError(BaseError):
    def __init__(self, id):
        if id == '':
            self.text = "The empty residue ID corresponds to more than a single residue in the current data pipe."
        else:
            self.text = "The residue ID '%s' corresponds to more than a single residue in the current data pipe." % id

# Multiple spins matching the ID.
class RelaxMultiSpinIDError(BaseError):
    def __init__(self, id, id_list=None):
        if id_list != None and id == '':
            self.text = "The empty spin ID corresponds to multiple spins, including %s." % list_to_text(id_list)
        elif id_list == None and id == '':
            self.text = "The empty spin ID corresponds to more than a single spin in the current data pipe."
        elif id_list != None:
            self.text = "The spin ID '%s' corresponds to multiple spins, including %s." % (id, list_to_text(id_list))
        else:
            self.text = "The spin ID '%s' corresponds to more than a single spin in the current data pipe." % id

# Cannot find the residue in the sequence.
class RelaxNoResError(BaseError):
    def __init__(self, number, name=None):
        if name == None:
            self.text = "The residue '" + repr(number) + "' cannot be found in the sequence."
        else:
            self.text = "The residue '" + repr(number) + " " + name + "' cannot be found in the sequence."

# Cannot find the spin in the sequence.
class RelaxNoSpinError(BaseError):
    def __init__(self, id, pipe=None):
        if pipe == None:
            self.text = "The spin '%s' does not exist." % id
        else:
            self.text = "The spin '%s' does not exist in the '%s' data pipe." % (id, pipe)

# The sequence data is not valid.
class RelaxInvalidSeqError(BaseError):
    def __init__(self, line, problem=None):
        if problem == None:
            self.text = "The sequence data in the line %s is invalid." % line
        else:
            self.text = "The sequence data in the line %s is invalid, %s." % (line, problem)

# The spins have not been loaded
class RelaxSpinsNotLoadedError(BaseError):
    def __init__(self, spin_id):
        self.text = "The spin information for the spin " + repr(spin_id) + " has not yet been loaded, please use the structure.load_spins user function."


# Interatomic data errors.
##########################

# No interatomic data.
class RelaxNoInteratomError(BaseError):
    def __init__(self, spin_id1=None, spin_id2=None, pipe=None):
        if spin_id1 and pipe:
            self.text = "The interatomic data between the spins '%s' and '%s' for the data pipe '%s' does not exist." % (spin_id1, spin_id2, pipe)
        elif spin_id1:
            self.text = "The interatomic data between the spins '%s' and '%s' does not exist." % (spin_id1, spin_id2)
        elif pipe:
            self.text = "The interatomic data for the data pipe '%s' does not exist." % pipe
        else:
            self.text = "The interatomic data does not exist."

# The interatomic data already exists.
class RelaxInteratomError(BaseError):
    def __init__(self, pipe=None):
        if pipe == None:
            self.text = "The interatomic data already exists."
        else:
            self.text = "The interatomic data for the data pipe " + repr(pipe) + " already exists."

# Inconsistency in the interatomic data.
class RelaxInteratomInconsistentError(BaseError):
    def __init__(self, pipe1, pipe2):
        self.text = "The interatomic data is inconsistent between the data pipes '%s' and '%s'." % (pipe1, pipe2)



# Domain errors.
################

# No domain defined.
class RelaxNoDomainError(BaseError):
    def __init__(self, id=None):
        if id == None:
            self.text = "No domains are defined."
        else:
            self.text = "The domain '%s' is not defined." % id



# Spectrometer information errors.
##################################

# No frequency information.
class RelaxNoFrqError(BaseError):
    def __init__(self, pipe_name=None, id=None):
        self.text = "No spectrometer frequency information"
        if id != None:
            self.text += " for the '%s' experiment ID" % id
        self.text += " is present"
        if pipe_name != None:
            self.text += " in the '%s' data pipe" % pipe_name
        self.text += "."



# Spectral data errors.
#######################

# No peak intensity data.
class RelaxNoPeakIntensityError(BaseError):
    def __init__(self, spectrum_id=None):
        if spectrum_id == None:
            self.text = "No peak intensity data has been loaded."
        else:
            self.text = "Peak intensity data for the '%s' spectrum ID does not exist."

# No spectral data.
class RelaxNoSpectraError(BaseError):
    def __init__(self, spectrum_id):
        self.text = "Spectral data corresponding to the ID string '%s' does not exist." % spectrum_id

# Spectral data already exists.
class RelaxSpectraError(BaseError):
    def __init__(self, spectrum_id):
        self.text = "Spectral data corresponding to the ID string '%s' already exists." % spectrum_id


# Relaxation data errors.
#########################

# No relaxation data.
class RelaxNoRiError(BaseError):
    def __init__(self, ri_id):
        self.text = "Relaxation data corresponding to the ID string '%s' does not exist." % ri_id

# Relaxation data already exists.
class RelaxRiError(BaseError):
    def __init__(self, ri_id):
        self.text = "Relaxation data corresponding to the ID string '%s' already exists." % ri_id


# J coupling errors.
####################

# No J data.
class RelaxNoJError(BaseError):
    def __init__(self):
        self.text = "No J coupling data exists."

# J data already exists.
class RelaxJError(BaseError):
    def __init__(self):
        self.text = "J coupling data already exists."


# RDC and PCS data errors.
##########################

# No alignment data.
class RelaxNoAlignError(BaseError):
    def __init__(self, align_id, pipe=None):
        if pipe != None:
            self.text = "The alignment ID string '%s' is missing from the data pipe '%s'." % (align_id, pipe)
        else:
            self.text = "The alignment ID string '%s' is missing." % align_id

# Alignment data already exists.
class RelaxAlignError(BaseError):
    def __init__(self, align_id):
        self.text = "Alignment data corresponding to the ID string '%s' already exists." % align_id

# No RDC data.
class RelaxNoRDCError(BaseError):
    def __init__(self, id=None):
        if id:
            self.text = "RDC data corresponding to the identification string " + repr(id) + " does not exist."
        else:
            self.text = "No RDC data exists."

# RDC data already exists.
class RelaxRDCError(BaseError):
    def __init__(self, id):
        self.text = "RDC data corresponding to the identification string " + repr(id) + " already exists."

# No PCS data.
class RelaxNoPCSError(BaseError):
    def __init__(self, id=None):
        if id:
            self.text = "PCS data corresponding to the identification string " + repr(id) + " does not exist."
        else:
            self.text = "No PCS data exists."

# PCS data already exists.
class RelaxPCSError(BaseError):
    def __init__(self, id):
        self.text = "PCS data corresponding to the identification string " + repr(id) + " already exists."


# Model-free errors.
####################

# Model-free data already exists.
class RelaxMfError(BaseError):
    def __init__(self, pipe):
        self.text = "Model-free data corresponding to the data pipe " + repr(pipe) + " already exists."


# Tensor errors.
################

# Tensor data corresponding to the data pipe already exists.
class RelaxTensorError(BaseError):
    def __init__(self, tensor_type):
        self.text = "The " + tensor_type + " tensor data already exists."

# No tensor data exists.
class RelaxNoTensorError(BaseError):
    def __init__(self, tensor_type, tensor_label=None):
        if not tensor_label:
            self.text = "No " + tensor_type + " tensor data exists."
        else:
            self.text = "No " + tensor_type + " tensor data exists for the tensor " + repr(tensor_label) + "."


# File errors.
##############

# No directory.
class RelaxDirError(BaseError):
    def __init__(self, name, dir):
        if name == None:
            self.text = "The directory " + repr(dir) + " does not exist."
        else:
            self.text = "The " + name + " directory " + repr(dir) + " does not exist."

# No file.
class RelaxFileError(BaseError):
    def __init__(self, name, file_name=None):
        if file_name == None:
            self.text = "The file " + repr(name) + " does not exist."
        else:
            self.text = "The " + name + " file " + repr(file_name) + " does not exist."

# No data in file.
class RelaxFileEmptyError(BaseError):
    def __init__(self):
        self.text = "The file contains no data."

# Overwrite file.
class RelaxFileOverwriteError(BaseError):
    def __init__(self, file_name, flag):
        self.text = "The file " + repr(file_name) + " already exists.  Set the " + flag + " to True to overwrite."

# Invalid data format.
class RelaxInvalidDataError(BaseError):
    def __init__(self):
        self.text = "The format of the data is invalid."


# Data pipe errors.
###################

# The data pipe bundle already exists.
class RelaxBundleError(BaseError):
    def __init__(self, bundle):
        self.text = "The data pipe bundle '%s' already exists." % bundle

# No data pipe bundles exist.
class RelaxNoBundleError(BaseError):
    def __init__(self, bundle=None):
        if bundle != None:
            self.text = "The data pipe bundle '%s' has not been created yet." % bundle
        else:
            self.text = "No data pipe bundles currently exist.  Please use the pipe.bundle user function first."

# The data pipe already exists.
class RelaxPipeError(BaseError):
    def __init__(self, pipe):
        self.text = "The data pipe " + repr(pipe) + " already exists."

# No data pipe exists.
class RelaxNoPipeError(BaseError):
    def __init__(self, pipe=None):
        if pipe != None:
            self.text = "The data pipe " + repr(pipe) + " has not been created yet."
        else:
            self.text = "No data pipes currently exist.  Please use the pipe.create user function first."


# Spin-Residue-Molecule errors.
###############################

# Disallow molecule selection.
class RelaxMolSelectDisallowError(BaseError):
    def __init__(self):
        self.text = "The selection of molecules is not allowed."

# Disallow residue selection.
class RelaxResSelectDisallowError(BaseError):
    def __init__(self):
        self.text = "The selection of residues is not allowed."

# Disallow spin selection.
class RelaxSpinSelectDisallowError(BaseError):
    def __init__(self):
        self.text = "The selection of spin systems is not allowed."

# The spin must be specified.
class RelaxNoSpinSpecError(BaseError):
    def __init__(self):
        self.text = "The spin system must be specified."



# Setup errors.
###############

# Cannot setup the functions.
class RelaxFuncSetupError(BaseError):
    def __init__(self, string):
        self.text = "This function is not available for " + string + "."

# The model already exists.
class RelaxModelError(BaseError):
    def __init__(self, name=None):
        if name != None:
            self.text = "The " + name + " model already exists."
        else:
            self.text = "The model already exists."


# The model has not been setup.
class RelaxNoModelError(BaseError):
    def __init__(self, name=None):
        if name != None:
            self.text = "The specific " + name + " model has not been selected or set up."
        else:
            self.text = "The specific model has not been selected or set up."


# Regular expression errors.
############################

# Bad regular expression.
class RelaxRegExpError(BaseError):
    def __init__(self, name, value):
        self.text = "The " + name + " argument " + repr(value) + " is not valid regular expression."


# Data type errors.
###################

# Parameter cannot be set.
class RelaxParamSetError(BaseError):
    def __init__(self, name, param_type=None):
        if param_type != None:
            self.text = "The " + name + " parameter, " + repr(param_type) + ", cannot be set."
        else:
            self.text = "The " + name + " parameter cannot be set."

# Value already exists.
class RelaxValueError(BaseError):
    def __init__(self, data_type, pipe=None):
        if pipe != None:
            self.text = "The data type " + repr(data_type) + " already exists for the data pipe " + repr(pipe) + "."
        else:
            self.text = "The data type " + repr(data_type) + " already exists."

# No data value.
class RelaxNoValueError(BaseError):
    def __init__(self, name, spin_id=None, spin_id2=None):
        if spin_id2 != None:
            self.text = "The %s value has not yet been set for spins '%s' and '%s'." % (name, spin_id, spin_id2)
        elif spin_id != None:
            self.text = "The %s value has not yet been set for spin '%s'." % (name, spin_id)
        else:
            self.text = "The " + repr(name) + " value has not yet been set."

# Unknown data type.
class RelaxUnknownDataTypeError(BaseError):
    def __init__(self, name):
        self.text = "The data type " + repr(name) + " is unknown."

# Unknown parameter.
class RelaxUnknownParamError(BaseError):
    def __init__(self, name, param_type=None):
        if param_type != None:
            self.text = "The " + name + " parameter, " + repr(param_type) + ", is unknown."
        else:
            self.text = "The " + name + " parameter is unknown."

# Unknown parameter combination.
class RelaxUnknownParamCombError(BaseError):
    def __init__(self, name, data):
        self.text = "The " + repr(name) + " argument " + repr(data) + " represents an unknown parameter combination."


# Simulation errors.
####################

# No simulations.
class RelaxNoSimError(BaseError):
    def __init__(self, pipe=None):
        if pipe:
            self.text = "Simulations for the data pipe " + repr(pipe) + " have not been setup."
        else:
            self.text = "Simulations have not been setup."


# Style errors.
###############

# Unknown style.
class RelaxStyleError(BaseError):
    def __init__(self, style):
        self.text = "The style " + repr(style) + " is unknown."


# Colour errors.
################

# Invalid colour.
class RelaxInvalidColourError(BaseError):
    def __init__(self, colour):
        self.text = "The colour " + repr(colour) + " is invalid."


# Value errors.
###############

# Infinity.
class RelaxInfError(BaseError):
    def __init__(self, name):
        self.text = "The invalid " + name + " floating point value of infinity has occurred."

# NaN (Not a Number).
class RelaxNaNError(BaseError):
    def __init__(self, name):
        self.text = "The invalid " + name + " floating point value of NaN (Not a Number) has occurred."


# XML errors.
#############

# Cannot recreate from the XML - the structure is not empty.
class RelaxFromXMLNotEmptyError(BaseError):
    def __init__(self, name):
        self.text = "The " + name + " data structure cannot be recreated from the XML elements as the structure is not empty."



# An object of all the RelaxErrors.
###################################

# Function for setting up the AllRelaxErrors object.
def all_errors(names):
    """Function for returning all the RelaxErrors to allow the AllRelaxError object to be created."""

    # Empty list.
    list = []

    # Loop over all objects of this module.
    for name in names:
        # Get the object.
        object = globals()[name]

        # Skip over all non error class objects.
        if not (isinstance(object, type(RelaxError)) or isinstance(object, type(type))) or not match('Relax', name):
            continue

        # Append to the list.
        list.append(object)

    # Return the list of RelaxErrors
    return list

# Initialise the AllRelaxErrors structure, as a tuple for the except statements, so it can be imported.
AllRelaxErrors = tuple(all_errors(dir()))
