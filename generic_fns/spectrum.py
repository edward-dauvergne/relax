###############################################################################
#                                                                             #
# Copyright (C) 2004-2013 Edward d'Auvergne                                   #
# Copyright (C) 2008 Sebastien Morin                                          #
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
"""Module containing functions for the handling of peak intensities."""


# Python module imports.
from math import sqrt
from re import split
import sys
from warnings import warn

# relax module imports.
from generic_fns.mol_res_spin import exists_mol_res_spin_data, generate_spin_id_unique, return_spin, spin_loop
from generic_fns import pipes
from relax_errors import RelaxArgNotNoneError, RelaxError, RelaxImplementError, RelaxNoSequenceError, RelaxNoSpectraError
from relax_io import extract_data, read_spin_data, strip, write_data
from relax_warnings import RelaxWarning, RelaxNoSpinWarning



class Bruker_import:
    def __init__(self, dir=None, exp_type=None, file=None, UI='prompt', output_file=None):
        """Function to import Bruker Protein Dynamic Center (PDC) files.

        @param dir:         The directory to save the new file in.
        @type dir:          str
        @param file:        The Bruker PDC output file.
        @type file:         str
        @param exp_type:    The type of experiment, e.g. NOE, T1 or T2
        @type exp_type:     str
        @param UI:          The relax user interface (either 'prompt' or 'GUI').
        @type UI:           str
        @param output_file: The file to save the imported list.
        @type output_file:  str
        """

        # Create experiment type
        self.exp_type = exp_type

        # The output file
        self.output_file = output_file
        self.dir = dir

        # The user interface.
        self.UI = UI

        # Read the file.
        if file:
            self.read_file(file)
        else:
            raise RelaxError('No file selected.')

        # Collect the entries for the file.
        self.collect_entries()

        # Create dummy file.
        self.create_file()


    def __str__(self):
        """Function to allow to return a value."""
        return str(self.value)


    def collect_entries(self):
        """Function to collect entries for the NOE/R1/R2 relax dummy file."""

        # storage for file entries
        # [ [Mol_name, Res_num, Res_name, Spin_num, value, error], ... ]
        self.file_entries = []

        # Data flag
        is_data = False

        # Spin name
        spinname = 'N'

        # loop over line
        for line in range(0, len(self.entries)):
            # Detect the experiment
            if 'Project:' in self.entries[line][0]:
                exp_type = ''

                # NOE
                if 'Dynamic method/Hetero NOE' in self.entries[line][1]:
                    exp_type = 'NOE'
                # T1
                elif 'Dynamic method/T1' in self.entries[line][1]:
                    exp_type = 'T1'
                # T2
                elif 'Dynamic method/T2' in self.entries[line][1]:
                    exp_type = 'T2'

                # Check agreement of file and user input.
                if self.exp_type:
                    if not self.exp_type == exp_type:
                        raise RelaxError('Selected file is not a '+self.exp_type+'-file.')
                        return

                # Feedback
                print("Reading BRUKER PDC "+exp_type+" file.\n")

            # The entries
            if 'SECTION:' in self.entries[line][0]:
                # NOE/T1/T2 results
                if 'results' in self.entries[line][1]:
                    is_data = True
                    continue

                # Other entries
                else:
                    is_data = False

            # Spin name
            if 'Labelling:' in self.entries[line][0]:
                # 15N
                if 'N' in self.entries[line][0]:
                    spinname = 'N'

                # 13C
                if 'C' in self.entries[line][0]:
                    spinname = 'C'

            # Collect NOE/T1/T2 values
            if is_data:
                # Exclued header or blank line.
                if self.entries[line][0] in ['Peak name', '']:
                    continue

                # Label
                label_tmp = self.entries[line][0]
                label_tmp = label_tmp.replace(' ', '')
                label_tmp = label_tmp.replace('[', '')
                label_tmp = label_tmp.replace(']', '')

                # Detect residue number
                resnum = label_tmp
                # find start of number
                start = 0
                while resnum[start].isdigit()==False: start = start+1

                # find end of number
                end = start
                try:
                    while resnum[end].isdigit()==True: end = end+1
                # Label ends with number
                except:
                    end = end

                # cut out residue number integer
                resnum = resnum[start:end]

                # Residue name
                resname = label_tmp[0:start]

                # Spin num
                spin_no = line

                # The value
                value_tmp = float(self.entries[line][3])

                # Convert T1/T2 to R1/R2
                if exp_type in ['T1', 'T2']:
                    value_tmp = 1.0/value_tmp

                # error
                error = float(self.entries[line][4])

                # Store file entry
                self.file_entries.append(['Bruker_PDC_'+exp_type, resnum, resname, spin_no, spinname, value_tmp, error])


    def create_file(self):
        """Function to write the file."""

        # The Sparky header
        text = 'Mol_name\tRes_num\tRes_name\tSpin_num\tSpin_name\tValue\tError \n'

        for line in range(0, len(self.file_entries)):
            # Build entries.
            tmp_text = ''
            for i in range(0, len(self.file_entries[line])):
                tmp_text = tmp_text + str(self.file_entries[line][i])+'\t'

            # Add entries.
            text = text+tmp_text + '\n'

        # Print entries
        if not self.UI == 'GUI':
            print(text)

        # craete output file
        if self.output_file:
            if self.dir:
                file = open(self.dir+sep+self.output_file, 'w')
            else:
                file = open(self.output_file, 'w')
        # create dummy file
        else:
            file = DummyFileObject()

        # Write the file
        file.write(text)
        file.close()

        # Feedback
        if self.output_file:
            if self.dir:
                print('Created BRUKER PDC file '+self.dir+sep+self.output_file)
                # The return value
                self.value = self.dir+sep+self.output_file
            else:
                print('Created BRUKER PDC file '+self.output_file)
                # The return value
                self.value = self.output_file
        else:
            print('Created BRUKER PDC file.')
            # Return the dummy file
            self.value = file


    def read_file(self, filename):
        """Function to read the file."""

        # Open the file.
        file = open(filename, 'r')

        # Storage of lines.
        self.entries = []

        # Loop over line in PDC file
        for line in file:
            # Read entries in line
            entry = line
            entry = line.strip()
            entry = entry.split('\t')

            # Add entries to storage
            self.entries.append(entry)

        # close the file
        file.close()


def __errors_height_no_repl():
    """Calculate the errors for peak heights when no spectra are replicated."""

    # Loop over the spins and set the error to the RMSD of the base plane noise.
    for spin, spin_id in spin_loop(return_id=True):
        # Skip deselected spins.
        if not spin.select:
            continue

        # Skip spins missing intensity data.
        if not hasattr(spin, 'intensities'):
            continue

        # Test if the RMSD has been set.
        if not hasattr(spin, 'baseplane_rmsd'):
            raise RelaxError("The RMSD of the base plane noise for spin '%s' has not been set." % spin_id)

        # Set the error to the RMSD.
        spin.intensity_err = spin.baseplane_rmsd


def __errors_repl(verbosity=0):
    """Calculate the errors for peak intensities from replicated spectra.

    @keyword verbosity: The amount of information to print.  The higher the value, the greater the verbosity.
    @type verbosity:    int
    """

    # Replicated spectra.
    repl = replicated_flags()

    # Are all spectra replicated?
    if False in repl.values():
        all_repl = False
        print("All spectra replicated:  No.")
    else:
        all_repl = True
        print("All spectra replicated:  Yes.")

    # Initialise.
    cdp.sigma_I = {}
    cdp.var_I = {}

    # Loop over the spectra.
    for id in cdp.spectrum_ids:
        # Skip non-replicated spectra.
        if not repl[id]:
            continue

        # Skip replicated spectra which already have been used.
        if id in cdp.var_I and cdp.var_I[id] != 0.0:
            continue

        # The replicated spectra.
        for j in range(len(cdp.replicates)):
            if id in cdp.replicates[j]:
                spectra = cdp.replicates[j]

        # Number of spectra.
        num_spectra = len(spectra)

        # Print out.
        print("\nReplicated spectra:  " + repr(spectra))
        if verbosity:
            print("%-5s%-6s%-20s%-20s" % ("Num", "Name", "Average", "SD"))

        # Calculate the mean value.
        count = 0
        for spin in spin_loop():
            # Skip deselected spins.
            if not spin.select:
                continue

            # Skip and deselect spins which have no data.
            if not hasattr(spin, 'intensities'):
                spin.select = False
                continue

            # Missing data.
            missing = False
            for j in range(num_spectra):
                if not spectra[j] in spin.intensities:
                    missing = True
            if missing:
                continue

            # Average intensity.
            ave_intensity = 0.0
            for j in range(num_spectra):
                ave_intensity = ave_intensity + spin.intensities[spectra[j]]
            ave_intensity = ave_intensity / num_spectra

            # Sum of squared errors.
            SSE = 0.0
            for j in range(num_spectra):
                SSE = SSE + (spin.intensities[spectra[j]] - ave_intensity) ** 2

            # Variance.
            #
            #                   1
            #       sigma^2 = ----- * sum({Xi - Xav}^2)]
            #                 n - 1
            #
            var_I = 1.0 / (num_spectra - 1.0) * SSE

            # Print out.
            if verbosity:
                print("%-5i%-6s%-20s%-20s" % (spin.num, spin.name, repr(ave_intensity), repr(var_I)))

            # Sum of variances (for average).
            if not id in cdp.var_I:
                cdp.var_I[id] = 0.0
            cdp.var_I[id] = cdp.var_I[id] + var_I
            count = count + 1

        # No data catch.
        if not count:
            raise RelaxError("No data is present, unable to calculate errors from replicated spectra.")

        # Average variance.
        cdp.var_I[id] = cdp.var_I[id] / float(count)

        # Set all spectra variances.
        for j in range(num_spectra):
            cdp.var_I[spectra[j]] = cdp.var_I[id]

        # Print out.
        print("Standard deviation:  %s" % sqrt(cdp.var_I[id]))


    # Average across all spectra if there are time points with a single spectrum.
    if not all_repl:
        # Print out.
        print("\nVariance averaging over all spectra.")

        # Initialise.
        var_I = 0.0
        num_dups = 0

        # Loop over all time points.
        for id in cdp.var_I.keys():
            # Single spectrum (or extraordinarily accurate NMR spectra!).
            if cdp.var_I[id] == 0.0:
                continue

            # Sum and count.
            var_I = var_I + cdp.var_I[id]
            num_dups = num_dups + 1

        # Average value.
        var_I = var_I / float(num_dups)

        # Assign the average value to all time points.
        for id in cdp.spectrum_ids:
            cdp.var_I[id] = var_I

        # Print out.
        print("Standard deviation for all spins:  " + repr(sqrt(var_I)))

    # Loop over the spectra.
    for id in cdp.var_I.keys():
        # Create the standard deviation data structure.
        cdp.sigma_I[id] = sqrt(cdp.var_I[id])

    # Set the spin specific errors.
    for spin in spin_loop():
        # Skip deselected spins.
        if not spin.select:
            continue

        # Set the error.
        spin.intensity_err = cdp.sigma_I


def __errors_volume_no_repl():
    """Calculate the errors for peak volumes when no spectra are replicated."""

    # Loop over the spins and set the error to the RMSD of the base plane noise.
    for spin, spin_id in spin_loop(return_id=True):
        # Skip deselected spins.
        if not spin.select:
            continue

        # Skip spins missing intensity data.
        if not hasattr(spin, 'intensities'):
            continue

        # Test if the RMSD has been set.
        if not hasattr(spin, 'baseplane_rmsd'):
            raise RelaxError("The RMSD of the base plane noise for spin '%s' has not been set." % spin_id)

        # Test that the total number of points have been set.
        if not hasattr(spin, 'N'):
            raise RelaxError("The total number of points used in the volume integration has not been specified for spin '%s'." % spin_id)

        # Set the error to the RMSD multiplied by the square root of the total number of points.
        for key in spin.intensity.keys():
            spin.intensity_err[key] = spin.baseplane_rmsd[key] * sqrt(spin.N)


def autodetect_format(file_data):
    """Automatically detect the format of the peak list.

    @param file_data:   The processed results file data.
    @type file_data:    list of lists of str
    """

    # The first header line.
    for line in file_data:
        if line != []:
            break

    # Sparky format.
    if line[0] == 'Assignment':
        return 'sparky'

    # NMRView format.
    if line == ['label', 'dataset', 'sw', 'sf']:
        return 'nmrview'

    # XEasy format.
    if line == ['No.', 'Color', 'w1', 'w2', 'ass.', 'in', 'w1', 'ass.', 'in', 'w2', 'Volume', 'Vol.', 'Err.', 'Method', 'Comment']:
        return 'xeasy'

    # Assume a generic format.
    return 'generic'


def baseplane_rmsd(error=0.0, spectrum_id=None, spin_id=None):
    """Set the peak intensity errors, as defined as the baseplane RMSD.

    @param error:           The peak intensity error value defined as the RMSD of the base plane
                            noise.
    @type error:            float
    @keyword spectrum_id:   The spectrum id.
    @type spectrum_id:      str
    @param spin_id:         The spin identification string.
    @type spin_id:          str
    """

    # Test if the current pipe exists
    pipes.test()

    # Test if the sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Test the spectrum id string.
    if spectrum_id not in cdp.spectrum_ids:
        raise RelaxError("The peak intensities corresponding to the spectrum id '%s' do not exist." % spectrum_id)

    # The scaling by NC_proc.
    if hasattr(cdp, 'ncproc') and spectrum_id in cdp.ncproc:
        scale = 1.0 / 2**cdp.ncproc[spectrum_id]
    else:
        scale = 1.0

    # Loop over the spins.
    for spin in spin_loop(spin_id):
        # Skip deselected spins.
        if not spin.select:
            continue

        # Initialise or update the baseplane_rmsd data structure as necessary.
        if not hasattr(spin, 'baseplane_rmsd'):
            spin.baseplane_rmsd = {}

        # Set the error.
        spin.baseplane_rmsd[spectrum_id] = float(error) * scale


def delete(spectrum_id=None):
    """Delete spectral data corresponding to the spectrum ID.

    @keyword spectrum_id:   The spectrum ID string.
    @type spectrum_id:      str
    """

    # Test if the current pipe exists.
    pipes.test()

    # Test if the sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Test if data exists.
    if not hasattr(cdp, 'spectrum_ids') or spectrum_id not in cdp.spectrum_ids:
        raise RelaxNoSpectraError(spectrum_id)

    # Remove the ID.
    cdp.spectrum_ids.pop(cdp.spectrum_ids.index(spectrum_id))

    # The ncproc parameter.
    if hasattr(cdp, 'ncproc') and spectrum_id in cdp.ncproc:
        del cdp.ncproc[spectrum_id]

    # Replicates.
    if hasattr(cdp, 'replicates'):
        # Loop over the replicates.
        for i in range(len(cdp.replicates)):
            # The spectrum is replicated.
            if spectrum_id in cdp.replicates[i]:
                # Duplicate.
                if len(cdp.replicates[i]) == 2:
                    cdp.replicates.pop(i)

                # More than two spectra:
                else:
                    cdp.replicates[i].pop(cdp.replicates[i].index(spectrum_id))

                # No need to check further.
                break

    # Errors.
    if hasattr(cdp, 'sigma_I') and spectrum_id in cdp.sigma_I:
        del cdp.sigma_I[spectrum_id]
    if hasattr(cdp, 'var_I') and spectrum_id in cdp.var_I:
        del cdp.var_I[spectrum_id]

    # Loop over the spins.
    for spin in spin_loop():
        # Intensity data.
        if hasattr(spin, 'intensities') and spectrum_id in spin.intensities:
            del spin.intensities[spectrum_id]


def error_analysis():
    """Determine the peak intensity standard deviation."""

    # Test if the current pipe exists
    pipes.test()

    # Test if the sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Test if spectra have been loaded.
    if not hasattr(cdp, 'spectrum_ids'):
        raise RelaxError("Error analysis is not possible, no spectra have been loaded.")

    # Peak height category.
    if cdp.int_method == 'height':
        # Print out.
        print("Intensity measure:  Peak heights.")

        # Do we have replicated spectra?
        if hasattr(cdp, 'replicates'):
            # Print out.
            print("Replicated spectra:  Yes.")

            # Set the errors.
            __errors_repl()

        # No replicated spectra.
        else:
            # Print out.
            print("Replicated spectra:  No.")

            # Set the errors.
            __errors_height_no_repl()

    # Peak volume category.
    if cdp.int_method == 'point sum':
        # Print out.
        print("Intensity measure:  Peak volumes.")

        # Do we have replicated spectra?
        if hasattr(cdp, 'replicates'):
            # Print out.
            print("Replicated spectra:  Yes.")

            # Set the errors.
            __errors_repl()

        # No replicated spectra.
        else:
            # Print out.
            print("Replicated spectra:  No.")

            # No implemented.
            raise RelaxImplementError

            # Set the errors.
            __errors_vol_no_repl()


def get_ids():
    """Return a list of all spectrum IDs.

    @return:    The list of spectrum IDs.
    @rtype:     list of str
    """

    # No IDs.
    if not hasattr(cdp, 'spectrum_ids'):
        return []

    # Return the IDs.
    return cdp.spectrum_ids


def integration_points(N=0, spectrum_id=None, spin_id=None):
    """Set the number of integration points for the given spectrum.

    @param N:               The number of integration points.
    @type N:                int
    @keyword spectrum_id:   The spectrum ID string.
    @type spectrum_id:      str
    @keyword spin_id:       The spin ID string used to restrict the value to.
    @type spin_id:          None or str
    """

    raise RelaxImplementError


def intensity_generic(file_data=None, spin_id_col=None, mol_name_col=None, res_num_col=None, res_name_col=None, spin_num_col=None, spin_name_col=None, data_col=None, sep=None, spin_id=None):
    """Return the process data from the generic peak intensity file.

    The residue number, heteronucleus and proton names, and peak intensity will be returned.


    @keyword file_data:     The data extracted from the file converted into a list of lists.
    @type file_data:        list of lists of str
    @keyword spin_id_col:   The column containing the spin ID strings (used by the generic intensity
                            file format).  If supplied, the mol_name_col, res_name_col, res_num_col,
                            spin_name_col, and spin_num_col arguments must be none.
    @type spin_id_col:      int or None
    @keyword mol_name_col:  The column containing the molecule name information (used by the generic
                            intensity file format).  If supplied, spin_id_col must be None.
    @type mol_name_col:     int or None
    @keyword res_name_col:  The column containing the residue name information (used by the generic
                            intensity file format).  If supplied, spin_id_col must be None.
    @type res_name_col:     int or None
    @keyword res_num_col:   The column containing the residue number information (used by the
                            generic intensity file format).  If supplied, spin_id_col must be None.
    @type res_num_col:      int or None
    @keyword spin_name_col: The column containing the spin name information (used by the generic
                            intensity file format).  If supplied, spin_id_col must be None.
    @type spin_name_col:    int or None
    @keyword spin_num_col:  The column containing the spin number information (used by the generic
                            intensity file format).  If supplied, spin_id_col must be None.
    @type spin_num_col:     int or None
    @keyword data_col:      The column containing the peak intensities.
    @type data_col:         int
    @keyword sep:           The column separator which, if None, defaults to whitespace.
    @type sep:              str or None
    @keyword spin_id:       The spin ID string used to restrict data loading to a subset of all
                            spins.
    @type spin_id:          None or str
    @raises RelaxError:     When the expected peak intensity is not a float.
    @return:                The extracted data as a list of lists.  The first dimension corresponds
                            to the spin.  The second dimension consists of the proton name,
                            heteronucleus name, spin ID string, and the intensity value.
    @rtype:                 list of lists of str, str, str, float
    """

    # Strip the data.
    file_data = strip(file_data)

    # Loop over the data.
    data = []
    for mol_name, res_num, res_name, spin_num, spin_name, value in read_spin_data(file_data=file_data, spin_id_col=spin_id_col, mol_name_col=mol_name_col, res_num_col=res_num_col, res_name_col=res_name_col, spin_num_col=spin_num_col, spin_name_col=spin_name_col, data_col=data_col, sep=sep, spin_id=spin_id):
        id = generate_spin_id_unique(mol_name=mol_name, res_num=res_num, res_name=res_name, spin_num=spin_num, spin_name=spin_name)
        data.append([None, None, id, value, id])

    # Return the data.
    return data


def intensity_nmrview(file_data=None, int_col=None):
    """Return the process data from the NMRView peak intensity file.

    The residue number, heteronucleus and proton names, and peak intensity will be returned.


    @keyword file_data: The data extracted from the file converted into a list of lists.
    @type file_data:    list of lists of str
    @keyword int_col:   The column containing the peak intensity data. The default is 16 for intensities. Setting the int_col argument to 15 will use the volumes (or evolumes). For a non-standard formatted file, use a different value.
    @type int_col:      int
    @raises RelaxError: When the expected peak intensity is not a float.
    @return:            The extracted data as a list of lists.  The first dimension corresponds to the spin.  The second dimension consists of the proton name, heteronucleus name, spin ID string, the intensity value, and the original line of text
    @rtype:             list of lists of str, str, str, float, str
    """

    # Assume the NMRView file has six header lines!
    num = 6
    print("Number of header lines: " + repr(num))

    # Remove the header.
    file_data = file_data[num:]

    # Strip the data.
    file_data = strip(file_data)

    # The peak intensity column.
    if int_col == None:
        int_col = 16
    if int_col == 16:
        print('Using peak heights.')
    if int_col == 15:
        print('Using peak volumes (or evolumes).')

    # Loop over the file data.
    data = []
    for line in file_data:
        # Unknown assignment.
        if line[1] == '{}':
            warn(RelaxWarning("The assignment '%s' is unknown, skipping this peak." % line[1]))
            continue

        # The residue number
        res_num = ''
        try:
            res_num = line[1].strip('{')
            res_num = res_num.strip('}')
            res_num = res_num.split('.')
            res_num = res_num[0]
        except ValueError:
            raise RelaxError("The peak list is invalid.")

        # Nuclei names.
        x_name = ''
        if line[8]!='{}':
            x_name = line[8].strip('{')
            x_name = x_name.strip('}')
            x_name = x_name.split('.')
            x_name = x_name[1]
        h_name = ''
        if line[1]!='{}':
            h_name = line[1].strip('{')
            h_name = h_name.strip('}')
            h_name = h_name.split('.')
            h_name = h_name[1]

        # Intensity.
        try:
            intensity = float(line[int_col])
        except ValueError:
            raise RelaxError("The peak intensity value " + repr(intensity) + " from the line " + repr(line) + " is invalid.")

        # Generate the spin_id.
        spin_id = generate_spin_id_unique(res_num=res_num, spin_name=x_name)

        # Append the data.
        data.append([h_name, x_name, spin_id, intensity, line])

    # Return the data.
    return data


def intensity_sparky(file_data=None, int_col=None):
    """Return the process data from the Sparky peak intensity file.

    The residue number, heteronucleus and proton names, and peak intensity will be returned.


    @keyword file_data: The data extracted from the file converted into a list of lists.
    @type file_data:    list of lists of str
    @keyword int_col:   The column containing the peak intensity data (for a non-standard formatted file).
    @type int_col:      int
    @raises RelaxError: When the expected peak intensity is not a float.
    @return:            The extracted data as a list of lists.  The first dimension corresponds to the spin.  The second dimension consists of the proton name, heteronucleus name, spin ID string, the intensity value, and the original line of text.
    @rtype:             list of lists of str, str, str, float, str
    """

    # The number of header lines.
    num = 0
    if file_data[0][0] == 'Assignment':
        num = num + 1
    if file_data[1] == '':
        num = num + 1
    print("Number of header lines found: %s" % num)

    # Remove the header.
    file_data = file_data[num:]

    # Strip the data.
    file_data = strip(file_data)

    # Loop over the file data.
    data = []
    for line in file_data:
        # The Sparky assignment.
        assignment = ''
        res_num = ''
        h_name = ''
        x_name = ''
        intensity = ''

        # Skip non-assigned peaks.
        if line[0] == '?-?':
            continue

        # First split by the 2D separator.
        x_assign, h_assign = split('-', line[0])

        # The proton info.
        h_row = split('([A-Z]+)', h_assign)
        h_name = h_row[-2] + h_row[-1]

        # The heteronucleus info.
        x_row = split('([A-Z]+)', x_assign)
        x_name = x_row[-2] + x_row[-1]

        # The residue number.
        try:
            res_num = int(x_row[-3])
        except:
            raise RelaxError("Improperly formatted Sparky file.")

        # The peak intensity column.
        if int_col == None:
            int_col = 3

        # Intensity.
        try:
            intensity = float(line[int_col])
        except ValueError:
            raise RelaxError("The peak intensity value " + repr(intensity) + " from the line " + repr(line) + " is invalid.")

        # Generate the spin_id.
        spin_id = generate_spin_id_unique(res_num=res_num, spin_name=x_name)

        # Append the data.
        data.append([h_name, x_name, spin_id, intensity, line])

    # Return the data.
    return data


def intensity_xeasy(file_data=None, heteronuc=None, proton=None, int_col=None):
    """Return the process data from the XEasy peak intensity file.

    The residue number, heteronucleus and proton names, and peak intensity will be returned.


    @keyword file_data: The data extracted from the file converted into a list of lists.
    @type file_data:    list of lists of str
    @keyword heteronuc: The name of the heteronucleus as specified in the peak intensity file.
    @type heteronuc:    str
    @keyword proton:    The name of the proton as specified in the peak intensity file.
    @type proton:       str
    @keyword int_col:   The column containing the peak intensity data (for a non-standard formatted file).
    @type int_col:      int
    @raises RelaxError: When the expected peak intensity is not a float.
    @return:            The extracted data as a list of lists.  The first dimension corresponds to the spin.  The second dimension consists of the proton name, heteronucleus name, spin ID string, the intensity value, and the original line of text.
    @rtype:             list of lists of str, str, str, float, str
    """

    # The columns.
    w1_col = 4
    w2_col = 7
    if int_col == None:
        int_col = 10

    # Set the default proton dimension.
    H_dim = 'w1'

    # Determine the number of header lines.
    num = 0
    for line in file_data:
        # Try to see if the intensity can be extracted.
        try:
            intensity = float(line[int_col])
        except ValueError:
            num = num + 1
        except IndexError:
            num = num + 1
        else:
            break
    print("Number of header lines found: " + repr(num))

    # Remove the header.
    file_data = file_data[num:]

    # Strip the data.
    file_data = strip(file_data)

    # Determine the proton and heteronucleus dimensions.
    for line in file_data:
        # Proton in w1, heteronucleus in w2.
        if line[w1_col] == proton and line[w2_col] == heteronuc:
            # Set the proton dimension.
            H_dim = 'w1'

            # Print out.
            print("The proton dimension is w1")

            # Don't continue (waste of time).
            break

        # Heteronucleus in w1, proton in w2.
        if line[w1_col] == heteronuc and line[w2_col] == proton:
            # Set the proton dimension.
            H_dim = 'w2'

            # Print out.
            print("The proton dimension is w2")

            # Don't continue (waste of time).
            break

    # Loop over the file data.
    data = []
    for line in file_data:
        # Test for invalid assignment lines which have the column numbers changed and return empty data.
        if line[w1_col] == 'inv.':
            continue

        # The residue number.
        try:
            res_num = int(line[5])
        except:
            raise RelaxError("Improperly formatted XEasy file.")

        # Nuclei names.
        if H_dim == 'w1':
            h_name = line[w1_col]
            x_name = line[w2_col]
        else:
            x_name = line[w1_col]
            h_name = line[w2_col]

        # Intensity.
        try:
            intensity = float(line[int_col])
        except ValueError:
            raise RelaxError("The peak intensity value " + repr(intensity) + " from the line " + repr(line) + " is invalid.")

        # Generate the spin_id.
        spin_id = generate_spin_id_unique(res_num=res_num, spin_name=x_name)

        # Append the data.
        data.append([h_name, x_name, spin_id, intensity, line])

    # Return the data.
    return data


def read(file=None, dir=None, spectrum_id=None, heteronuc=None, proton=None, int_col=None, int_method=None, spin_id_col=None, mol_name_col=None, res_num_col=None, res_name_col=None, spin_num_col=None, spin_name_col=None, sep=None, spin_id=None, ncproc=None, verbose=True):
    """Read the peak intensity data.

    @keyword file:          The name of the file containing the peak intensities.
    @type file:             str
    @keyword dir:           The directory where the file is located.
    @type dir:              str
    @keyword spectrum_id:   The spectrum identification string.
    @type spectrum_id:      str
    @keyword heteronuc:     The name of the heteronucleus as specified in the peak intensity file.
    @type heteronuc:        str
    @keyword proton:        The name of the proton as specified in the peak intensity file.
    @type proton:           str
    @keyword int_col:       The column containing the peak intensity data (used by the generic intensity file format).
    @type int_col:          int
    @keyword int_method:    The integration method, one of 'height', 'point sum' or 'other'.
    @type int_method:       str
    @keyword spin_id_col:   The column containing the spin ID strings (used by the generic intensity file format).  If supplied, the mol_name_col, res_name_col, res_num_col, spin_name_col, and spin_num_col arguments must be none.
    @type spin_id_col:      int or None
    @keyword mol_name_col:  The column containing the molecule name information (used by the generic intensity file format).  If supplied, spin_id_col must be None.
    @type mol_name_col:     int or None
    @keyword res_name_col:  The column containing the residue name information (used by the generic intensity file format).  If supplied, spin_id_col must be None.
    @type res_name_col:     int or None
    @keyword res_num_col:   The column containing the residue number information (used by the generic intensity file format).  If supplied, spin_id_col must be None.
    @type res_num_col:      int or None
    @keyword spin_name_col: The column containing the spin name information (used by the generic intensity file format).  If supplied, spin_id_col must be None.
    @type spin_name_col:    int or None
    @keyword spin_num_col:  The column containing the spin number information (used by the generic intensity file format).  If supplied, spin_id_col must be None.
    @type spin_num_col:     int or None
    @keyword sep:           The column separator which, if None, defaults to whitespace.
    @type sep:              str or None
    @keyword spin_id:       The spin ID string used to restrict data loading to a subset of all spins.
    @type spin_id:          None or str
    @keyword ncproc:        The Bruker ncproc binary intensity scaling factor.
    @type ncproc:           int or None
    @keyword verbose:       A flag which if True will cause all relaxation data loaded to be printed out.
    @type verbose:          bool
    """

    # Test if the current data pipe exists.
    pipes.test()

    # Test if sequence data is loaded.
    if not exists_mol_res_spin_data():
        raise RelaxNoSequenceError

    # Check the file name.
    if file == None:
        raise RelaxError("The file name must be supplied.")

    # Test that the intensity measures are identical.
    if hasattr(cdp, 'int_method') and cdp.int_method != int_method:
        raise RelaxError("The '%s' measure of peak intensities does not match '%s' of the previously loaded spectra." % (int_method, cdp.int_method))

    # Check the intensity measure.
    if not int_method in ['height', 'point sum', 'other']:
        raise RelaxError("The intensity measure '%s' is not one of 'height', 'point sum', 'other'." % int_method)

    # Set the peak intensity measure.
    cdp.int_method = int_method

    # Extract the data from the file.
    file_data = extract_data(file, dir, sep=sep)

    # Automatic format detection.
    format = autodetect_format(file_data)

    # Generic.
    if format == 'generic':
        # Print out.
        print("Generic formatted data file.\n")

        # Extract the data.
        intensity_data = intensity_generic(file_data=file_data, spin_id_col=spin_id_col, mol_name_col=mol_name_col, res_num_col=res_num_col, res_name_col=res_name_col, spin_num_col=spin_num_col, spin_name_col=spin_name_col, data_col=int_col, sep=sep, spin_id=spin_id)

    # NMRView.
    elif format == 'nmrview':
        # Print out.
        print("NMRView formatted data file.\n")

        # Extract the data.
        intensity_data = intensity_nmrview(file_data=file_data)

    # Sparky.
    elif format == 'sparky':
        # Print out.
        print("Sparky formatted data file.\n")

        # Extract the data.
        intensity_data = intensity_sparky(file_data=file_data, int_col=int_col)

    # XEasy.
    elif format == 'xeasy':
        # Print out.
        print("XEasy formatted data file.\n")

        # Extract the data.
        intensity_data = intensity_xeasy(file_data=file_data, proton=proton, heteronuc=heteronuc, int_col=int_col)

    # Add the spectrum id (and ncproc) to the relax data store.
    if not hasattr(cdp, 'spectrum_ids'):
        cdp.spectrum_ids = []
        if ncproc != None:
            cdp.ncproc = {}
    if not spectrum_id in cdp.spectrum_ids:
        cdp.spectrum_ids.append(spectrum_id)
        if ncproc != None:
            cdp.ncproc[spectrum_id] = ncproc

    # Loop over the peak intensity data.
    data = []
    data_flag = False
    for i in range(len(intensity_data)):
        # Extract the data.
        H_name, X_name, spin_id, intensity, line = intensity_data[i]

        # Skip data.
        if (X_name and X_name != heteronuc) or (H_name and H_name != proton):
            warn(RelaxWarning("Proton and heteronucleus names do not match, skipping the data %s." % line))
            continue

        # Get the spin container.
        spin = return_spin(spin_id)
        if not spin:
            warn(RelaxNoSpinWarning(spin_id))
            continue

        # Skip deselected spins.
        if not spin.select:
            continue

        # Initialise.
        if not hasattr(spin, 'intensities'):
            spin.intensities = {}

        # Intensity scaling.
        if ncproc != None:
            intensity = intensity / float(2**ncproc)

        # Add the data.
        spin.intensities[spectrum_id] = intensity

        # Switch the flag.
        data_flag = True

        # Append the data for printing out.
        data.append([spin_id, repr(intensity)])

    # No data.
    if not data_flag:
        # Delete all the data.
        delete(spectrum_id)

        # Raise the error.
        raise RelaxError("No data could be loaded from the peak list")

    # Print out.
    if verbose:
        print("\nThe following intensities have been loaded into the relax data store:\n")
        write_data(out=sys.stdout, headings=["Spin_ID", "Intensity"], data=data)



def replicated(spectrum_ids=None):
    """Set which spectra are replicates.

    @keyword spectrum_ids:  A list of spectrum ids corresponding to replicated spectra.
    @type spectrum_ids:     list of str
    """

    # Test if the current pipe exists
    pipes.test()

    # Test if spectra have been loaded.
    if not hasattr(cdp, 'spectrum_ids'):
        raise RelaxError("No spectra have been loaded therefore replicates cannot be specified.")

    # Test the spectrum id strings.
    for spectrum_id in spectrum_ids:
        if spectrum_id not in cdp.spectrum_ids:
            raise RelaxError("The peak intensities corresponding to the spectrum id '%s' do not exist." % spectrum_id)

    # Test for None.
    if spectrum_ids == None:
        warn(RelaxWarning("The spectrum ID list cannot be None."))
        return

    # Test for more than one element.
    if len(spectrum_ids) == 1:
        warn(RelaxWarning("The number of spectrum IDs in the list %s must be greater than one." % spectrum_ids))
        return

    # Initialise.
    if not hasattr(cdp, 'replicates'):
        cdp.replicates = []

    # Check if the spectrum IDs are already in the list.
    found = False
    for i in range(len(cdp.replicates)):
        # Loop over all elements of the first.
        for j in range(len(spectrum_ids)):
            if spectrum_ids[j] in cdp.replicates[i]:
                found = True

        # One of the spectrum IDs already have a replicate specified.
        if found:
            # Add the remaining replicates to the list and quit this function.
            for j in range(len(spectrum_ids)):
                if spectrum_ids[j] not in cdp.replicates[i]:
                    cdp.replicates[i].append(spectrum_ids[j])

            # Nothing more to do.
            return

    # A new set of replicates.
    cdp.replicates.append(spectrum_ids)


def replicated_flags():
    """Create and return a dictionary of flags of whether the spectrum is replicated or not.

    @return:    The dictionary of flags of whether the spectrum is replicated or not.
    @rtype:     dict of bool
    """

    # Initialise all IDs to false.
    repl = {}
    for id in cdp.spectrum_ids:
        repl[id] = False

    # Loop over the replicates.
    for i in range(len(cdp.replicates)):
        for j in range(len(cdp.replicates[i])):
            repl[cdp.replicates[i][j]] = True

    # Return the dictionary.
    return repl


def replicated_ids(spectrum_id):
    """Create and return a list of spectra ID which are replicates of the given ID.

    @param spectrum_id: The spectrum ID to find all the replicates of.
    @type spectrum_id:  str
    @return:            The list of spectrum IDs which are replicates of spectrum_id.
    @rtype:             list of str
    """

    # Initialise the ID list.
    repl = []

    # Loop over the replicate lists.
    for i in range(len(cdp.replicates)):
        # The spectrum ID is in the list.
        if spectrum_id in cdp.replicates[i]:
            # Loop over the inner list.
            for j in range(len(cdp.replicates[i])):
                # Spectrum ID match.
                if spectrum_id == cdp.replicates[i][j]:
                    continue

                # Append the replicated ID.
                repl.append(cdp.replicates[i][j])

    # Nothing.
    if repl == []:
        return repl

    # Sort the list.
    repl.sort()

    # Remove duplicates (backward).
    id = repl[-1]
    for i in range(len(repl)-2, -1, -1):
        # Duplicate.
        if id == repl[i]:
            del repl[i]

        # Unique.
        else:
            id = repl[i]

    # Return the list.
    return repl
