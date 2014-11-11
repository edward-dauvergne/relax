###############################################################################
#                                                                             #
# Copyright (C) 2004-2014 Edward d'Auvergne                                   #
# Copyright (C) 2008 Sebastien Morin                                          #
# Copyright (C) 2013-2014 Troels E. Linnet                                    #
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
import sys
from warnings import warn

# relax module imports.
from lib.errors import RelaxError, RelaxImplementError, RelaxNoSpectraError
from lib.io import write_data
from lib.spectrum.peak_list import read_peak_list
from lib.statistics import std
from lib.warnings import RelaxWarning, RelaxNoSpinWarning
from pipe_control.mol_res_spin import check_mol_res_spin_data, create_spin, generate_spin_id_unique, return_spin, spin_loop
from pipe_control.pipes import check_pipe


def __errors_height_no_repl():
    """Calculate the errors for peak heights when no spectra are replicated."""

    # Loop over the spins and set the error to the RMSD of the base plane noise.
    for spin, spin_id in spin_loop(return_id=True):
        # Skip deselected spins.
        if not spin.select:
            continue

        # Skip spins missing intensity data.
        if not hasattr(spin, 'peak_intensity'):
            continue

        # Test if the RMSD has been set.
        if not hasattr(spin, 'baseplane_rmsd'):
            raise RelaxError("The RMSD of the base plane noise for spin '%s' has not been set." % spin_id)

        # Set the error to the RMSD.
        spin.peak_intensity_err = spin.baseplane_rmsd


def __errors_repl(subset=None, verbosity=0):
    """Calculate the errors for peak intensities from replicated spectra.

    @keyword subset:    The list of spectrum ID strings to restrict the analysis to.
    @type subset:       list of str
    @keyword verbosity: The amount of information to print.  The higher the value, the greater the verbosity.
    @type verbosity:    int
    """

    # Replicated spectra.
    repl = replicated_flags()

    # Are all spectra replicated?
    if False in list(repl.values()):
        all_repl = False
        print("All spectra replicated:  No.")
    else:
        all_repl = True
        print("All spectra replicated:  Yes.")

    # Initialise.
    if not hasattr(cdp, 'sigma_I'):
        cdp.sigma_I = {}
    if not hasattr(cdp, 'var_I'):
        cdp.var_I = {}

    # The subset.
    subset_flag = False
    if not subset:
        subset_flag = True
        subset = cdp.spectrum_ids

    # Loop over the spectra.
    for id in subset:
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

        # Printout.
        print("\nReplicated spectra:  " + repr(spectra))
        if verbosity:
            print("%-20s%-20s" % ("Spin_ID", "SD"))

        # Calculate the mean value.
        count = 0
        for spin, spin_id in spin_loop(return_id=True):
            # Skip deselected spins.
            if not spin.select:
                continue

            # Skip and deselect spins which have no data.
            if not hasattr(spin, 'peak_intensity'):
                spin.select = False
                continue

            # Missing data.
            missing = False
            for j in range(num_spectra):
                if not spectra[j] in spin.peak_intensity:
                    missing = True
            if missing:
                continue

            # The peak intensities.
            values = []
            for j in range(num_spectra):
                values.append(spin.peak_intensity[spectra[j]])

            # The standard deviation.
            sd = std(values=values, dof=1)

            # Printout.
            if verbosity:
                print("%-20s%-20s" % (spin_id, sd))

            # Sum of variances (for average).
            if not id in cdp.var_I:
                cdp.var_I[id] = 0.0
            cdp.var_I[id] = cdp.var_I[id] + sd**2
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
        if subset_flag:
            print("\nVariance averaging over the spectra subset.")
        else:
            print("\nVariance averaging over all spectra.")

        # Initialise.
        var_I = 0.0
        num_dups = 0

        # Loop over all time points.
        for id in cdp.var_I:
            # Only use id's defined in subset
            if id not in subset:
                continue

            # Single spectrum (or extraordinarily accurate NMR spectra!).
            if cdp.var_I[id] == 0.0:
                continue

            # Sum and count.
            var_I = var_I + cdp.var_I[id]
            num_dups = num_dups + 1

        # Average value.
        var_I = var_I / float(num_dups)

        # Assign the average value to all time points.
        for id in subset:
            cdp.var_I[id] = var_I

        # Print out.
        print("Standard deviation for all spins:  " + repr(sqrt(var_I)))

    # Loop over the spectra.
    for id in cdp.var_I:
        # Create the standard deviation data structure.
        cdp.sigma_I[id] = sqrt(cdp.var_I[id])

    # Set the spin specific errors.
    for spin in spin_loop():
        # Skip deselected spins.
        if not spin.select:
            continue

        # Set the error.
        spin.peak_intensity_err = cdp.sigma_I


def __errors_volume_no_repl(subset=None):
    """Calculate the errors for peak volumes when no spectra are replicated."""

    # Loop over the spins and set the error to the RMSD of the base plane noise.
    for spin, spin_id in spin_loop(return_id=True):
        # Skip deselected spins.
        if not spin.select:
            continue

        # Skip spins missing intensity data.
        if not hasattr(spin, 'peak_intensity'):
            continue

        # Test if the RMSD has been set.
        if not hasattr(spin, 'baseplane_rmsd'):
            raise RelaxError("The RMSD of the base plane noise for spin '%s' has not been set." % spin_id)

        # Test that the total number of points have been set.
        if not hasattr(spin, 'N'):
            raise RelaxError("The total number of points used in the volume integration has not been specified for spin '%s'." % spin_id)

        # Set the error to the RMSD multiplied by the square root of the total number of points.
        for key in spin.peak_intensity:
            spin.peak_intensity_err[key] = spin.baseplane_rmsd[key] * sqrt(spin.N)


def add_spectrum_id(spectrum_id=None):
    """Add the spectrum ID to the data store.

    @keyword spectrum_id:   The spectrum ID string.
    @type spectrum_id:      str
    """

    # Initialise the structure, if needed.
    if not hasattr(cdp, 'spectrum_ids'):
        cdp.spectrum_ids = []

    # The ID already exists.
    if spectrum_id in cdp.spectrum_ids:
        return

    # Add the ID.
    cdp.spectrum_ids.append(spectrum_id)


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

    # Data checks.
    check_pipe()
    check_mol_res_spin_data()
    check_spectrum_id(spectrum_id)

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


def check_spectrum_id(id):
    """Check that the give spectrum ID exists.

    @param id:                      The spectrum ID to check for.
    @type id:                       str
    @raises RelaxNoSpectraError:    If the ID does not exist.
    """

    # Check that the spectrum ID structure exists.
    if not hasattr(cdp, 'spectrum_ids'):
        raise RelaxNoSpectraError(id)

    # Test if the spectrum ID exists.
    if id not in cdp.spectrum_ids:
        raise RelaxNoSpectraError(id)


def delete(spectrum_id=None):
    """Delete spectral data corresponding to the spectrum ID.

    @keyword spectrum_id:   The spectrum ID string.
    @type spectrum_id:      str
    """

    # Data checks.
    check_pipe()
    check_mol_res_spin_data()
    check_spectrum_id(spectrum_id)

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
        if hasattr(spin, 'peak_intensity') and spectrum_id in spin.peak_intensity:
            del spin.peak_intensity[spectrum_id]


def error_analysis(subset=None):
    """Determine the peak intensity standard deviation.

    @keyword subset:    The list of spectrum ID strings to restrict the analysis to.
    @type subset:       list of str
    """

    # Tests.
    check_pipe()
    check_mol_res_spin_data()

    # Test if spectra have been loaded.
    if not hasattr(cdp, 'spectrum_ids'):
        raise RelaxError("Error analysis is not possible, no spectra have been loaded.")

    # Check the IDs.
    if subset:
        for id in subset:
            if id not in cdp.spectrum_ids:
                raise RelaxError("The spectrum ID '%s' has not been loaded into relax." % id)

    # Peak height category.
    if cdp.int_method == 'height':
        # Print out.
        print("Intensity measure:  Peak heights.")

        # Do we have replicated spectra?
        if hasattr(cdp, 'replicates'):
            # Print out.
            print("Replicated spectra:  Yes.")

            # Set the errors.
            __errors_repl(subset=subset)

        # No replicated spectra.
        else:
            # Print out.
            print("Replicated spectra:  No.")
            if subset:
                print("Spectra ID subset ignored.")

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
            __errors_repl(subset=subset)

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


def read(file=None, dir=None, spectrum_id=None, dim=1, int_col=None, int_method=None, spin_id_col=None, mol_name_col=None, res_num_col=None, res_name_col=None, spin_num_col=None, spin_name_col=None, sep=None, spin_id=None, ncproc=None, verbose=True):
    """Read the peak intensity data.

    @keyword file:          The name of the file(s) containing the peak intensities.
    @type file:             str or list of str
    @keyword dir:           The directory where the file is located.
    @type dir:              str
    @keyword spectrum_id:   The spectrum identification string.
    @type spectrum_id:      str or list of str
    @keyword dim:           The dimension of the peak list to associate the data with.
    @type dim:              int
    @keyword int_col:       The column containing the peak intensity data (used by the generic intensity file format).
    @type int_col:          int or list of int
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
    @keyword spin_id:       The spin ID string used to restrict data loading to a subset of all spins.  If 'auto' is provided for a NMRPipe seriesTab formatted file, the ID's are auto generated in form of Z_Ai.
    @type spin_id:          None or str
    @keyword ncproc:        The Bruker ncproc binary intensity scaling factor.
    @type ncproc:           int or None
    @keyword verbose:       A flag which if True will cause all relaxation data loaded to be printed out.
    @type verbose:          bool
    """

    # Data checks.
    check_pipe()
    check_mol_res_spin_data()

    # Check the file name.
    if file == None:
        raise RelaxError("The file name must be supplied.")

    # Test that the intensity measures are identical.
    if hasattr(cdp, 'int_method') and cdp.int_method != int_method:
        raise RelaxError("The '%s' measure of peak intensities does not match '%s' of the previously loaded spectra." % (int_method, cdp.int_method))

    # Multiple ID flags.
    flag_multi = False
    flag_multi_file = False
    flag_multi_col = False
    if isinstance(spectrum_id, list) or spectrum_id == 'auto':
        flag_multi = True
    if isinstance(file, list):
        flag_multi_file = True
    if isinstance(int_col, list) or spectrum_id == 'auto':
        flag_multi_col = True

    # List argument checks.
    if flag_multi:
        # Too many lists.
        if flag_multi_file and flag_multi_col:
            raise RelaxError("If a list of spectrum IDs is supplied, the file names and intensity column arguments cannot both be lists.")

        # Not enough lists.
        if not flag_multi_file and not flag_multi_col:
            raise RelaxError("If a list of spectrum IDs is supplied, either the file name or intensity column arguments must be a list of equal length.")

        # List lengths for multiple files.
        if flag_multi_file and len(spectrum_id) != len(file):
                raise RelaxError("The file list %s and spectrum ID list %s do not have the same number of elements." % (file, spectrum_id))

        # List lengths for multiple intensity columns.
        if flag_multi_col and spectrum_id != 'auto' and len(spectrum_id) != len(int_col):
            raise RelaxError("The spectrum ID list %s and intensity column list %s do not have the same number of elements." % (spectrum_id, int_col))

    # More list argument checks (when only one spectrum ID is supplied).
    else:
        # Multiple files.
        if flag_multi_file:
            raise RelaxError("If multiple files are supplied, then multiple spectrum IDs must also be supplied.")

        # Multiple intensity columns.
        if flag_multi_col:
            raise RelaxError("If multiple intensity columns are supplied, then multiple spectrum IDs must also be supplied.")

    # Intensity column checks.
    if spectrum_id != 'auto' and not flag_multi and flag_multi_col:
        raise RelaxError("If a list of intensity columns is supplied, the spectrum ID argument must also be a list of equal length.")

    # Check the intensity measure.
    if not int_method in ['height', 'point sum', 'other']:
        raise RelaxError("The intensity measure '%s' is not one of 'height', 'point sum', 'other'." % int_method)

    # Set the peak intensity measure.
    cdp.int_method = int_method

    # Convert the file argument to a list if necessary.
    if not isinstance(file, list):
        file = [file]

    # Loop over all files.
    for file_index in range(len(file)):
        # Read the peak list data.
        peak_list = read_peak_list(file=file[file_index], dir=dir, int_col=int_col, spin_id_col=spin_id_col, mol_name_col=mol_name_col, res_num_col=res_num_col, res_name_col=res_name_col, spin_num_col=spin_num_col, spin_name_col=spin_name_col, sep=sep, spin_id=spin_id)

        # Automatic spectrum IDs.
        if spectrum_id == 'auto':
            spectrum_id = peak_list[0].intensity_name

        # Loop over the assignments.
        data = []
        data_flag = False
        for assign in peak_list:
            # Generate the spin_id.
            spin_id = generate_spin_id_unique(res_num=assign.res_nums[dim-1], spin_name=assign.spin_names[dim-1])

            # Convert the intensity data to a list if needed.
            intensity = assign.intensity
            if not isinstance(intensity, list):
                intensity = [intensity]

            # Loop over the intensity data.
            for int_index in range(len(intensity)):
                # Sanity check.
                if intensity[int_index] == 0.0:
                    warn(RelaxWarning("A peak intensity of zero has been encountered for the spin '%s' - this could be fatal later on." % spin_id))

                # Get the spin container.
                spin = return_spin(spin_id)
                if not spin:
                    warn(RelaxNoSpinWarning(spin_id))
                    continue

                # Skip deselected spins.
                if not spin.select:
                    continue

                # Initialise.
                if not hasattr(spin, 'peak_intensity'):
                    spin.peak_intensity = {}

                # Intensity scaling.
                if ncproc != None:
                    intensity[int_index] = intensity[int_index] / float(2**ncproc)

                # Add the data.
                if flag_multi_file:
                    id = spectrum_id[file_index]
                elif flag_multi_col:
                    id = spectrum_id[int_index]
                else:
                    id = spectrum_id
                spin.peak_intensity[id] = intensity[int_index]

                # Switch the flag.
                data_flag = True

                # Append the data for printing out.
                data.append([spin_id, repr(intensity[int_index])])

        # Add the spectrum id (and ncproc) to the relax data store.
        spectrum_ids = spectrum_id
        if isinstance(spectrum_id, str):
            spectrum_ids = [spectrum_id]
        if ncproc != None and not hasattr(cdp, 'ncproc'):
            cdp.ncproc = {}
        for i in range(len(spectrum_ids)):
            add_spectrum_id(spectrum_ids[i])
            if ncproc != None:
                cdp.ncproc[spectrum_ids[i]] = ncproc

        # No data.
        if not data_flag:
            # Delete all the data.
            delete(spectrum_id)

            # Raise the error.
            raise RelaxError("No data could be loaded from the peak list")

        # Printout.
        if verbose:
            print("\nThe following intensities have been loaded into the relax data store:\n")
            write_data(out=sys.stdout, headings=["Spin_ID", "Intensity"], data=data)
        print('')


def read_spins(file=None, dir=None, dim=1, spin_id_col=None, mol_name_col=None, res_num_col=None, res_name_col=None, spin_num_col=None, spin_name_col=None, sep=None, spin_id=None, verbose=True):
    """Read the peak intensity data.

    @keyword file:          The name of the file containing the peak intensities.
    @type file:             str
    @keyword dir:           The directory where the file is located.
    @type dir:              str
    @keyword dim:           The dimension of the peak list to associate the data with.
    @type dim:              int
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
    @keyword spin_id:       The spin ID string used to restrict data loading to a subset of all spins.  If 'auto' is provided for a NMRPipe seriesTab formatted file, the ID's are auto generated in form of Z_Ai.
    @type spin_id:          None or str
    @keyword verbose:       A flag which if True will cause all relaxation data loaded to be printed out.
    @type verbose:          bool
    """

    # Data checks.
    check_pipe()

    # Check the file name.
    if file == None:
        raise RelaxError("The file name must be supplied.")

    # Read the peak list data.
    peak_list = read_peak_list(file=file, dir=dir, spin_id_col=spin_id_col, mol_name_col=mol_name_col, res_num_col=res_num_col, res_name_col=res_name_col, spin_num_col=spin_num_col, spin_name_col=spin_name_col, sep=sep, spin_id=spin_id)

    # Loop over the peak_list.
    created_spins = []
    for assign in peak_list:
        mol_name = assign.mol_names[dim-1]
        res_num = assign.res_nums[dim-1]
        res_name = assign.res_names[dim-1]
        spin_num = assign.spin_nums[dim-1]
        spin_name = assign.spin_names[dim-1]

        # Generate the spin_id.
        spin_id = generate_spin_id_unique(mol_name=mol_name, res_num=res_num, res_name=res_name, spin_name=spin_name)

        # Check if the spin already exist.
        if return_spin(spin_id=spin_id) == None:
            # Create the spin if not exist.
            create_spin(spin_num=spin_num, spin_name=spin_name, res_num=res_num, res_name=res_name, mol_name=mol_name)

    # Test that data exists.
    check_mol_res_spin_data()

def replicated(spectrum_ids=None):
    """Set which spectra are replicates.

    @keyword spectrum_ids:  A list of spectrum ids corresponding to replicated spectra.
    @type spectrum_ids:     list of str
    """

    # Test if the current pipe exists.
    check_pipe()

    # Test for None.
    if spectrum_ids == None:
        warn(RelaxWarning("The spectrum ID list cannot be None."))
        return

    # Test if spectra have been loaded.
    if not hasattr(cdp, 'spectrum_ids'):
        raise RelaxError("No spectra have been loaded therefore replicates cannot be specified.")

    # Test the spectrum id strings.
    for spectrum_id in spectrum_ids:
        check_spectrum_id(spectrum_id)

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
