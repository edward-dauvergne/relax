###############################################################################
#                                                                             #
# Copyright (C) 2008-2014 Edward d'Auvergne                                   #
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
"""Module containing functions for BMRB support."""

# Python module imports.
from os import F_OK, access
import sys

# relax module imports.
from data_store import Relax_data_store; ds = Relax_data_store()
import dep_check
from info import Info_box
from lib.errors import RelaxError, RelaxFileError, RelaxFileOverwriteError, RelaxNoModuleInstallError, RelaxNoPipeError
from lib.io import get_file_path, mkdir_nofail
from pipe_control import exp_info
from pipe_control.mol_res_spin import create_spin, generate_spin_id, metadata_cleanup, return_spin, set_spin_element, set_spin_isotope
from pipe_control.pipes import cdp_name
from pipe_control.result_files import add_result_file
from specific_analyses.api import return_api
from status import Status; status = Status()
from version import version_full


def display(version='3.1'):
    """Display the results in the BMRB NMR-STAR format.

    @keyword version:   The NMR-STAR version to create.  This can be either '2.1', '3.0', or '3.1'.
    @type version:      str
    """

    # Call the write() function with stdout.
    write(file=sys.stdout, version=version)


def generate_sequence(N=0, spin_ids=None, spin_nums=None, spin_names=None, res_nums=None, res_names=None, mol_names=None, isotopes=None, elements=None):
    """Generate the sequence data from the BRMB information.

    @keyword N:             The number of spins.
    @type N:                int
    @keyword spin_ids:      The list of spin IDs.
    @type spin_ids:         list of str
    @keyword spin_nums:     The list of spin numbers.
    @type spin_nums:        list of int or None
    @keyword spin_names:    The list of spin names.
    @type spin_names:       list of str or None
    @keyword res_nums:      The list of residue numbers.
    @type res_nums:         list of int or None
    @keyword res_names:     The list of residue names.
    @type res_names:        list of str or None
    @keyword mol_names:     The list of molecule names.
    @type mol_names:        list of str or None
    @keyword isotopes:      The optional list of isotope types.
    @type isotopes:         list of str or None
    @keyword elements:      The optional list of element types.
    @type elements:         list of str or None
    """

    # The blank data.
    if not spin_nums:
        spin_nums = [None] * N
    if not spin_names:
        spin_names = [None] * N
    if not res_nums:
        res_nums = [None] * N
    if not res_names:
        res_names = [None] * N
    if not mol_names:
        mol_names = [None] * N

    # Generate the spin IDs.
    spin_ids = []
    for i in range(N):
        spin_ids.append(generate_spin_id(mol_name=mol_names[i], res_num=res_nums[i], spin_name=spin_names[i]))

    # Loop over the spin data.
    for i in range(N):
        # The spin already exists.
        spin = return_spin(spin_ids[i])
        if spin:
            continue

        # Create the spin.
        spin = create_spin(spin_num=spin_nums[i], spin_name=spin_names[i], res_num=res_nums[i], res_name=res_names[i], mol_name=mol_names[i])

        # Set the spin isotope and element.
        spin_id = spin._spin_ids[0]
        if elements:
            set_spin_element(spin_id=spin_id, element=elements[i], force=True)
        if isotopes and elements:
            isotope = "%s%s" % (isotopes[i], elements[i])
            set_spin_isotope(spin_id=spin_id, isotope=isotope, force=True)

    # Clean up the spin metadata.
    metadata_cleanup()


def list_sample_conditions(star):
    """Get a listing of all the sample conditions.

    @param star:    The NMR-STAR dictionary object.
    @type star:     NMR_STAR instance
    @return:        The list of sample condition names.
    @rtype:         list of str
    """

    # Init.
    sample_conds = []

    # Get the sample conditions.
    for data in star.sample_conditions.loop():
        # Store the framecode.
        sample_conds.append(data['sf_framecode'])

    # Return the names.
    return sample_conds


def molecule_names(data, N=0):
    """Generate the molecule names list.

    @param data:    An element of data from bmrblib.
    @type data:     dict
    @return:        The list of molecule names.
    @rtype:         list of str
    """

    # The molecule index and name.
    mol_index = []
    for i in range(N):
        if 'entity_ids' in data and data['entity_ids'] != None and data['entity_ids'][i] != None:
            mol_index.append(int(data['entity_ids'][i]) -1 )
        else:
            mol_index = [0]*N
    mol_names = []
    for i in range(N):
        mol_names.append(cdp.mol[mol_index[i]].name)

    # Return the names.
    return mol_names


def num_spins(data):
    """Determine the number of spins in the given data.

    @param data:    An element of data from bmrblib.
    @type data:     dict
    @return:        The number of spins.
    @rtype:         int
    """

    # The number of spins.
    N = 0

    # List of keys containing sequence information.
    keys = ['data_ids', 'entity_ids', 'res_names', 'res_nums', 's2']

    # Loop over the keys until a list is found.
    for key in keys:
        if key in data and data[key]:
            N = len(data[key])
            break

    # Return the number.
    return N


def read(file=None, dir=None, version=None, sample_conditions=None):
    """Read the contents of a BMRB NMR-STAR formatted file.

    @keyword file:              The name of the BMRB STAR formatted file.
    @type file:                 str
    @keyword dir:               The directory where the file is located.
    @type dir:                  None or str
    @keyword version:           The BMRB version to force the reading.
    @type version:              None or str
    @keyword sample_conditions: The sample condition label to read.  Only one sample condition can be read per data pipe.
    @type sample_conditions:    None or str
    """

    # Test if bmrblib is installed.
    if not dep_check.bmrblib_module:
        raise RelaxNoModuleInstallError('BMRB library', 'bmrblib')

    # Test if the current data pipe exists.
    pipe_name = cdp_name()
    if not pipe_name:
        raise RelaxNoPipeError

    # Make sure that the data pipe is empty.
    if not ds[pipe_name].is_empty():
        raise RelaxError("The current data pipe is not empty.")

    # Get the full file path.
    file_path = get_file_path(file_name=file, dir=dir)

    # Fail if the file does not exist.
    if not access(file_path, F_OK):
        raise RelaxFileError(file_path)

    # Read the results.
    api = return_api(pipe_name=pipe_name)
    api.bmrb_read(file_path, version=version, sample_conditions=sample_conditions)


def write(file=None, dir=None, version='3.1', force=False):
    """Create a BMRB NMR-STAR formatted file.

    @keyword file:      The name of the file to create or a file object.
    @type file:         str or file object
    @keyword dir:       The optional directory to place the file into.  If set to 'pipe_name', then it will be placed in a directory with the same name as the current data pipe.
    @type dir:          str or None
    @keyword version:   The NMR-STAR version to create.  This can be either '2.1', '3.0', or '3.1'.
    @type version:      str
    @keyword force:     A flag which if True will allow a currently existing file to be overwritten.
    @type force:        bool
    """

    # Test if bmrblib is installed.
    if not dep_check.bmrblib_module:
        raise RelaxNoModuleInstallError('BMRB library', 'bmrblib')

    # Test if the current data pipe exists.
    pipe_name = cdp_name()
    if not pipe_name:
        raise RelaxNoPipeError

    # Check the file name.
    if file == None:
        raise RelaxError("The file name must be specified.")

    # A file object.
    if isinstance(file, str):
        # The special data pipe name directory.
        if dir == 'pipe_name':
            dir = pipe_name

        # Get the full file path.
        file = get_file_path(file, dir)

        # Fail if the file already exists and the force flag is False.
        if access(file, F_OK) and not force:
            raise RelaxFileOverwriteError(file, 'force flag')

        # Print out.
        print("Opening the file '%s' for writing." % file)

        # Create the directories.
        mkdir_nofail(dir, verbosity=0)

    # Get the info box.
    info = Info_box()

    # Add the relax citations.
    for id, key in zip(['relax_ref1', 'relax_ref2'], ['dAuvergneGooley08a', 'dAuvergneGooley08b']):
        # Alias the bib entry.
        bib = info.bib[key]

        # Add.
        exp_info.citation(cite_id=id, authors=bib.author2, doi=bib.doi, pubmed_id=bib.pubmed_id, full_citation=bib.cite_short(doi=False, url=False), title=bib.title, status=bib.status, type=bib.type, journal_abbrev=bib.journal, journal_full=bib.journal_full, volume=bib.volume, issue=bib.number, page_first=bib.page_first, page_last=bib.page_last, year=bib.year)

    # Add the relax software package.
    exp_info.software(name=exp_info.SOFTWARE['relax'].name, version=version_full(), vendor_name=exp_info.SOFTWARE['relax'].authors, url=exp_info.SOFTWARE['relax'].url, cite_ids=['relax_ref1', 'relax_ref2'], tasks=exp_info.SOFTWARE['relax'].tasks)

    # Execute the specific BMRB writing code.
    api = return_api(pipe_name=pipe_name)
    api.bmrb_write(file, version=version)

    # Add the file to the results file list.
    if isinstance(file, str):
        add_result_file(type='text', label='BMRB', file=file)
