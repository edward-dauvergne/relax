###############################################################################
#                                                                             #
# Copyright (C) 2010-2014 Edward d'Auvergne                                   #
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
"""Determination of relative stereochemistry in organic molecules.

The analysis is preformed by using multiple ensembles of structures, randomly sampled from a given set of structures.  The discrimination is performed by comparing the sets of ensembles using NOE violations and RDC Q factors.

This script is split into multiple stages:

    1.  The random sampling of the snapshots to generate the N ensembles (NUM_ENS, usually 10,000 to 100,000) of M members (NUM_MODELS, usually ~10).  The original snapshot files are expected to be named the SNAPSHOT_DIR + CONFIG + a number from SNAPSHOT_MIN to SNAPSHOT_MAX + ".pdb", e.g. "snapshots/R647.pdb".  The ensembles will be placed into the "ensembles" directory.

    2.  The NOE violation analysis.

    3.  The superimposition of ensembles.  For each ensemble, Molmol is used for superimposition using the fit to first algorithm.  The superimposed ensembles will be placed into the "ensembles_superimposed" directory.  This stage is not necessary for the NOE analysis.

    4.  The RDC Q factor analysis.

    5.  Generation of Grace graphs.

    6.  Final ordering of ensembles using the combined RDC and NOE Q factors, whereby the NOE Q factor is defined as::

        Q^2 = U / sum(NOE_i^2),

    where U is the quadratic flat bottom well potential - the NOE violation in Angstrom^2.  The denominator is the sum of all squared NOEs - this must be given as the value of NOE_NORM.  The combined Q is given by::

        Q_total^2 = Q_NOE^2 + Q_RDC^2.
"""

# Dependencies.
import dep_check

# Python module imports.
from math import pi, sqrt
from os import F_OK, access, getcwd, sep
from random import randint
from re import search
if dep_check.subprocess_module:
    from subprocess import PIPE, Popen
import sys

# relax module imports.
from pipe_control.grace import write_xy_data, write_xy_header
from lib.physical_constants import dipolar_constant, g1H, g13C
from prompt.interpreter import Interpreter
from lib.errors import RelaxError
from lib.io import mkdir_nofail
from status import Status; status = Status()



class Stereochem_analysis:
    """Class for performing the relative stereochemistry analysis."""

    def __init__(self, stage=1, results_dir=None, num_ens=10000, num_models=10, configs=None, snapshot_dir='snapshots', snapshot_min=None, snapshot_max=None, pseudo=None, noe_file=None, noe_norm=None, rdc_name=None, rdc_file=None, rdc_spin_id1_col=None, rdc_spin_id2_col=None, rdc_data_col=None, rdc_error_col=None, bond_length=None, bond_length_file=None, log=None, bucket_num=200, lower_lim_noe=0.0, upper_lim_noe=600.0, lower_lim_rdc=0.0, upper_lim_rdc=1.0):
        """Set up for the stereochemistry analysis.

        @keyword stage:             Stage of analysis (see the module docstring above for the options).  
        @type stage:                int
        @keyword results_dir:       The optional directory to place all results files into.
        @type results_dir:          None or str
        @keyword num_ens:           Number of ensembles.
        @type num_ens:              int
        @keyword num_models:        Ensemble size.
        @type num_models:           int
        @keyword configs:           All the configurations.
        @type configs:              list of str
        @keyword snapshot_dir:      Snapshot directories (corresponding to the configurations).
        @type snapshot_dir:         list of str
        @keyword snapshot_min:      The number of the first snapshots (corresponding to the configurations).
        @type snapshot_min:         list of int
        @keyword snapshot_max:      The number of the last snapshots (corresponding to the configurations).
        @type snapshot_max:         list of int
        @keyword pseudo:            The list of pseudo-atoms.  Each element is a list of the pseudo-atom name and a list of all those atoms forming the pseudo-atom.  For example, pseudo = [["Q7", ["@H16", "@H17", "@H18"]], ["Q9", ["@H20", "@H21", "@H22"]]].
        @type pseudo:               list of list of str and list of str
        @keyword noe_file:          The name of the NOE restraint file.
        @type noe_file:             str
        @keyword noe_norm:          The NOE normalisation factor (equal to the sum of all NOEs squared).
        @type noe_norm:             float
        @keyword rdc_name:          The label for this RDC data set.
        @type rdc_name:             str
        @keyword rdc_file:          The name of the RDC file.
        @type rdc_file:             str
        @keyword rdc_spin_id1_col:  The spin ID column of the first spin in the RDC file.
        @type rdc_spin_id1_col:     None or int
        @keyword rdc_spin_id2_col:  The spin ID column of the second spin in the RDC file.
        @type rdc_spin_id2_col:     None or int
        @keyword rdc_data_col:      The data column of the RDC file.
        @type rdc_data_col:         int
        @keyword rdc_error_col:     The error column of the RDC file.
        @type rdc_error_col:        int
        @keyword bond_length:       The bond length value in meters.  This overrides the bond_length_file argument.
        @type bond_length:          float or None
        @keyword bond_length_file:  The file of bond lengths for each atom pair in meters.  The first and second columns must be the spin ID strings and the third column must contain the data.
        @type bond_length_file:     float or None
        @keyword log:               Log file output flag (only for certain stages).
        @type log:                  bool
        @keyword bucket_num:        Number of buckets for the distribution plots.
        @type bucket_num:           int
        @keyword lower_lim_noe:     Distribution plot limits.
        @type lower_lim_noe:        int
        @keyword upper_lim_noe:     Distribution plot limits.
        @type upper_lim_noe:        int
        @keyword lower_lim_rdc:     Distribution plot limits.
        @type lower_lim_rdc:        int
        @keyword upper_lim_rdc:     Distribution plot limits.
        @type upper_lim_rdc:        int
        """

        # Execution lock.
        status.exec_lock.acquire('auto stereochem analysis', mode='auto-analysis')

        # Set up the analysis status object.
        status.init_auto_analysis('stereochem', type='stereochem')
        status.current_analysis = 'auto stereochem analysis'

        # Store all the args.
        self.stage = stage
        self.results_dir = results_dir
        self.num_ens = num_ens
        self.num_models = num_models
        self.configs = configs
        self.snapshot_dir = snapshot_dir
        self.snapshot_min = snapshot_min
        self.snapshot_max = snapshot_max
        self.pseudo = pseudo
        self.noe_file = noe_file
        self.noe_norm = noe_norm
        self.rdc_name = rdc_name
        self.rdc_file = rdc_file
        self.rdc_spin_id1_col = rdc_spin_id1_col
        self.rdc_spin_id2_col = rdc_spin_id2_col
        self.rdc_data_col = rdc_data_col
        self.rdc_error_col = rdc_error_col
        self.bond_length = bond_length
        self.bond_length_file = bond_length_file
        self.log = log
        self.bucket_num = bucket_num
        self.lower_lim_noe = lower_lim_noe
        self.upper_lim_noe = upper_lim_noe
        self.lower_lim_rdc = lower_lim_rdc
        self.upper_lim_rdc = upper_lim_rdc

        # Load the interpreter.
        self.interpreter = Interpreter(show_script=False, raise_relax_error=True)
        self.interpreter.populate_self()
        self.interpreter.on(verbose=False)

        # Create the results directory.
        if self.results_dir:
            mkdir_nofail(self.results_dir)

        # Or use the current working directory.
        else:
            self.results_dir = getcwd()

        # Create a directory for log files.
        if self.log:
            mkdir_nofail(self.results_dir + sep + "logs")

        # Finish and unlock execution.
        status.auto_analysis['stereochem'].fin = True
        status.current_analysis = None
        status.exec_lock.release()


    def run(self):
        """Execute the given stage of the analysis."""

        # Store the original STDOUT.
        self.stdout_orig = sys.stdout

        # Sampling of snapshots.
        if self.stage == 1:
            self.sample()

        # NOE violation analysis.
        elif self.stage == 2:
            self.noe_viol()

        # Ensemble superimposition.
        elif self.stage == 3:
            self.superimpose()

        # RDC Q factor analysis.
        elif self.stage == 4:
            self.rdc_analysis()

        # Grace plot creation.
        elif self.stage == 5:
            self.grace_plots()

        # Final combined Q ordering.
        elif self.stage == 6:
            self.combined_q()

        # Unknown stage.
        else:
            raise RelaxError("The stage number %s is unknown." % self.stage)

        # Restore STDOUT.
        sys.stdout = self.stdout_orig


    def combined_q(self):
        """Calculate the combined Q factor.

        The combined Q is defined as::

            Q_total^2 = Q_NOE^2 + Q_RDC^2,

        and the NOE Q factor as::

            Q^2 = U / sum(NOE_i^2),

        where U is the quadratic flat bottom well potential - the NOE violation in Angstrom^2.
        """

        # Checks.
        if not access(self.results_dir+sep+"NOE_viol_" + self.configs[0] + "_sorted", F_OK):
            raise RelaxError("The NOE analysis has not been performed, cannot find the file '%s'." % self.results_dir+sep+"NOE_viol_" + self.configs[0] + "_sorted")
        if not access(self.results_dir+sep+"Q_factors_" + self.configs[0] + "_sorted", F_OK):
            raise RelaxError("The RDC analysis has not been performed, cannot find the file '%s'." % self.results_dir+sep+"Q_factors_" + self.configs[0] + "_sorted")

        # Loop over the configurations.
        for i in range(len(self.configs)):
            # Print out.
            print("Creating the combined Q factor file for configuration '%s'." % self.configs[i])

            # Open the NOE results file and read the data.
            file = open(self.results_dir+sep+"NOE_viol_" + self.configs[i])
            noe_lines = file.readlines()
            file.close()

            # Open the RDC results file and read the data.
            file = open(self.results_dir+sep+"Q_factors_" + self.configs[i])
            rdc_lines = file.readlines()
            file.close()

            # The combined Q factor file.
            out = open(self.results_dir+sep+"Q_total_%s" % self.configs[i], 'w')
            out_sorted = open(self.results_dir+sep+"Q_total_%s_sorted" % self.configs[i], 'w')

            # Loop over the data (skipping the header line).
            data = []
            for j in range(1, len(noe_lines)):
                # Split the lines.
                ens = int(noe_lines[j].split()[0])
                noe_viol = float(noe_lines[j].split()[1])
                q_rdc = float(rdc_lines[j].split()[1])

                # The NOE Q factor.
                q_noe = sqrt(noe_viol/self.noe_norm)

                # Combined Q.
                q = sqrt(q_noe**2 + q_rdc**2)

                # Write out the unsorted list.
                out.write("%-20i%20.15f\n" % (ens, q))

                # Store the values.
                data.append([q, ens])

            # Sort the combined Q.
            data.sort()

            # Write the data.
            for i in range(len(data)):
                out_sorted.write("%-20i%20.15f\n" % (data[i][1], data[i][0]))

            # Close the files.
            out.close()
            out_sorted.close()


    def generate_distribution(self, values, lower=0.0, upper=200.0, inc=None):
        """Create the distribution data structure."""

        # The bin width.
        bin_width = (upper - lower)/float(inc)

        # Init the dist object.
        dist = []
        for i in range(inc):
            dist.append([bin_width*i+lower, 0])

        # Loop over the values.
        for val in values:
            # The bin.
            bin = int((val - lower)/bin_width)

            # Outside of the limits.
            if bin < 0 or bin >= inc:
                print("Outside of the limits: '%s'" % val)
                continue

            # Increment the count.
            dist[bin][1] = dist[bin][1] + 1

        # Convert the counts to frequencies.
        total_pr = 0.0
        for i in range(inc):
            dist[i][1] = dist[i][1] / float(len(values))
            total_pr = total_pr + dist[i][1]

        print("Total Pr: %s" % total_pr)

        # Return the dist.
        return dist


    def grace_plots(self):
        """Generate grace plots of the results."""

        # The number of configs.
        n = len(self.configs)

        # The colours for the different configs.
        defaults = [4, 2]    # Blue and red.
        colours = []
        for i in range(n):
            # Default colours.
            if i < len(defaults):
                colours.append(defaults[i])

            # Otherwise black!
            else:
                colours.append(0)

        # The ensemble number text.
        ens_text = ''
        dividers = [1e15, 1e12, 1e9, 1e6, 1e3, 1]
        num_ens = self.num_ens
        for i in range(len(dividers)):
            # The number.
            num = int(num_ens / dividers[i])

            # The text.
            if num:
                text = repr(num)
            elif not num and ens_text:
                text = '000'
            else:
                continue

            # Update the text.
            ens_text = ens_text + text

            # A comma.
            if i < len(dividers)-1:
                ens_text = ens_text + ','

            # Remove the front part of the number.
            num_ens = num_ens - dividers[i]*num

        # Subtitle for all graphs.
        subtitle = '%s ensembles of %s' % (ens_text, self.num_models)

        # NOE violations.
        if access(self.results_dir+sep+"NOE_viol_" + self.configs[0] + "_sorted", F_OK):
            # Print out.
            print("Generating NOE violation Grace plots.")

            # Open the output files.
            grace_curve = open(self.results_dir+sep+"NOE_viol_curve.agr", 'w')
            grace_dist = open(self.results_dir+sep+"NOE_viol_dist.agr", 'w')

            # Loop over the configurations.
            data = []
            dist = []
            for i in range(n):
                # Open the results file and read the data.
                file = open(self.results_dir+sep+"NOE_viol_" + self.configs[i] + "_sorted")
                lines = file.readlines()
                file.close()

                # Add a new graph set.
                data.append([])

                # Loop over the ensembles and extract the NOE violation.
                noe_viols = []
                for j in range(1, len(lines)):
                    # Extract the violation.
                    viol = float(lines[j].split()[1])
                    noe_viols.append(viol)

                    # Add to the data structure.
                    data[i].append([j, viol])

                # Calculate the R distribution.
                dist.append(self.generate_distribution(noe_viols, inc=self.bucket_num, upper=self.upper_lim_noe, lower=self.lower_lim_noe))

            # Headers.
            write_xy_header(file=grace_curve, title='NOE violation comparison', subtitle=subtitle, sets=[n], set_names=[self.configs], set_colours=[colours], symbols=[[0]*n], axis_labels=[['Ensemble (sorted)', 'NOE violation (Angstrom\\S2\\N)']], legend_pos=[[0.3, 0.8]])
            write_xy_header(file=grace_dist, title='NOE violation comparison', subtitle=subtitle, sets=[n], set_names=[self.configs], set_colours=[colours], symbols=[[1]*n], symbol_sizes=[[0.5]*n], linestyle=[[3]*n], axis_labels=[['NOE violation (Angstrom\\S2\\N)', 'Frequency']], legend_pos=[[1.1, 0.8]])

            # Write the data.
            write_xy_data([data], file=grace_curve, graph_type='xy')
            write_xy_data([dist], file=grace_dist, graph_type='xy')

            # Close the files.
            grace_curve.close()
            grace_dist.close()

        # RDC Q factors.
        if access(self.results_dir+sep+"Q_factors_" + self.configs[0] + "_sorted", F_OK):
            # Print out.
            print("Generating RDC Q factor Grace plots.")

            # Open the Grace output files.
            grace_curve = open(self.results_dir+sep+"RDC_%s_curve.agr" % self.rdc_name, 'w')
            grace_dist = open(self.results_dir+sep+"RDC_%s_dist.agr" % self.rdc_name, 'w')

            # Loop over the configurations.
            data = []
            dist = []
            for i in range(n):
                # Open the results file and read the data.
                file = open(self.results_dir+sep+"Q_factors_" + self.configs[i] + "_sorted")
                lines = file.readlines()
                file.close()

                # Add a new graph set.
                data.append([])

                # Loop over the Q factors.
                values = []
                for j in range(1, len(lines)):
                    # Extract the violation.
                    value = float(lines[j].split()[1])
                    values.append(value)

                    # Add to the data structure.
                    data[i].append([j, value])

                # Calculate the R distribution.
                dist.append(self.generate_distribution(values, inc=self.bucket_num, upper=self.upper_lim_rdc, lower=self.lower_lim_rdc))

            # Headers.
            write_xy_header(file=grace_curve, title='%s RDC Q factor comparison' % self.rdc_name, subtitle=subtitle, sets=[n], set_names=[self.configs], set_colours=[colours], symbols=[[0]*n], axis_labels=[['Ensemble (sorted)', '%s RDC Q factor (pales format)' % self.rdc_name]], legend_pos=[[0.3, 0.8]])
            write_xy_header(file=grace_dist, title='%s RDC Q factor comparison' % self.rdc_name, subtitle=subtitle, sets=[n], set_names=[self.configs], set_colours=[colours], symbols=[[1]*n], symbol_sizes=[[0.5]*n], linestyle=[[3]*n], axis_labels=[['%s RDC Q factor (pales format)' % self.rdc_name, 'Frequency']], legend_pos=[[1.1, 0.8]])

            # Write the data.
            write_xy_data([data], file=grace_curve, graph_type='xy')
            write_xy_data([dist], file=grace_dist, graph_type='xy')

            # Close the files.
            grace_curve.close()
            grace_dist.close()

        # NOE-RDC correlation plots.
        if access(self.results_dir+sep+"NOE_viol_" + self.configs[0] + "_sorted", F_OK) and access(self.results_dir+sep+"Q_factors_" + self.configs[0] + "_sorted", F_OK):
            # Print out.
            print("Generating NOE-RDC correlation Grace plots.")

            # Open the Grace output files.
            grace_file = open(self.results_dir+sep+"correlation_plot.agr", 'w')
            grace_file_scaled = open(self.results_dir+sep+"correlation_plot_scaled.agr", 'w')

            # Grace data.
            data = []
            data_scaled = []
            for i in range(len(self.configs)):
                # Open the NOE results file and read the data.
                file = open(self.results_dir+sep+"NOE_viol_" + self.configs[i])
                noe_lines = file.readlines()
                file.close()

                # Add a new graph set.
                data.append([])
                data_scaled.append([])

                # Open the RDC results file and read the data.
                file = open(self.results_dir+sep+"Q_factors_" + self.configs[i])
                rdc_lines = file.readlines()
                file.close()

                # Loop over the data.
                for j in range(1, len(noe_lines)):
                    # Split the lines.
                    noe_viol = float(noe_lines[j].split()[1])
                    q_factor = float(rdc_lines[j].split()[1])

                    # Add the xy pair.
                    data[i].append([noe_viol, q_factor])
                    data_scaled[i].append([sqrt(noe_viol/self.noe_norm), q_factor])

            # Write the data.
            write_xy_header(file=grace_file, title='Correlation plot - %s RDC vs. NOE' % self.rdc_name, subtitle=subtitle, sets=[n], set_names=[self.configs], set_colours=[colours], symbols=[[9]*n], symbol_sizes=[[0.24]*n], linetype=[[0]*n], axis_labels=[['NOE violation (Angstrom\\S2\\N)', '%s RDC Q factor (pales format)' % self.rdc_name]], legend_pos=[[1.1, 0.8]])
            write_xy_header(file=grace_file_scaled, title='Correlation plot - %s RDC vs. NOE Q factor' % self.rdc_name, subtitle=subtitle, sets=[n], set_names=[self.configs], set_colours=[colours], symbols=[[9]*n], symbol_sizes=[[0.24]*n], linetype=[[0]*n], axis_labels=[['Normalised NOE violation (Q = sqrt(U / \\xS\\f{}NOE\\si\\N\\S2\\N))', '%s RDC Q factor (pales format)' % self.rdc_name]], legend_pos=[[1.1, 0.8]])
            write_xy_data([data], file=grace_file, graph_type='xy')
            write_xy_data([data_scaled], file=grace_file_scaled, graph_type='xy')


    def noe_viol(self):
        """NOE violation calculations."""

        # Redirect STDOUT to a log file.
        if self.log:
            sys.stdout = open(self.results_dir+sep+"logs" + sep + "NOE_viol.log", 'w')

        # Create a directory for the save files.
        dir = self.results_dir + sep + "NOE_results"
        mkdir_nofail(dir=dir)

        # Loop over the configurations.
        for config in self.configs:
            # Print out.
            print("\n"*10 + "# Set up for config " + config + " #" + "\n")

            # Open the results file.
            out = open(self.results_dir+sep+"NOE_viol_" + config, 'w')
            out_sorted = open(self.results_dir+sep+"NOE_viol_" + config + "_sorted", 'w')
            out.write("%-20s%20s\n" % ("# Ensemble", "NOE_volation"))
            out_sorted.write("%-20s%20s\n" % ("# Ensemble", "NOE_volation"))

            # Create the data pipe.
            self.interpreter.pipe.create("noe_viol_%s" % config, "N-state")

            # Read the first structure.
            self.interpreter.structure.read_pdb("ensembles" + sep + config + "0.pdb", dir=self.results_dir, set_mol_name=config, set_model_num=list(range(1, self.num_models+1)))

            # Load all protons as the sequence.
            self.interpreter.structure.load_spins("@H*", ave_pos=False)

            # Create the pseudo-atoms.
            for i in range(len(self.pseudo)):
                self.interpreter.spin.create_pseudo(spin_name=self.pseudo[i][0], members=self.pseudo[i][1], averaging="linear")
            self.interpreter.sequence.display()

            # Read the NOE list.
            self.interpreter.noe.read_restraints(file=self.noe_file)

            # Set up the N-state model.
            self.interpreter.n_state_model.select_model(model="fixed")

            # Print out.
            print("\n"*2 + "# Set up complete #" + "\n"*10)

            # Loop over each ensemble.
            noe_viol = []
            for ens in range(self.num_ens):
                # Print out the ensemble to both the log and screen.
                if self.log:
                    sys.stdout.write(config + repr(ens) + "\n")
                sys.stderr.write(config + repr(ens) + "\n")

                # Delete the old structures and rename the molecule.
                self.interpreter.structure.delete()

                # Read the ensemble.
                self.interpreter.structure.read_pdb("ensembles" + sep + config + repr(ens) + ".pdb", dir=self.results_dir, set_mol_name=config, set_model_num=list(range(1, self.num_models+1)))

                # Get the atomic positions.
                self.interpreter.structure.get_pos(ave_pos=False)

                # Calculate the average NOE potential.
                self.interpreter.calc()

                # Sum the violations.
                cdp.sum_viol = 0.0
                for i in range(len(cdp.ave_dist)):
                    if cdp.quad_pot[i][2]:
                        cdp.sum_viol = cdp.sum_viol + cdp.quad_pot[i][2]

                # Write out the NOE violation.
                noe_viol.append([cdp.sum_viol, ens])
                out.write("%-20i%30.15f\n" % (ens, cdp.sum_viol))

                # Save the state.
                self.interpreter.results.write(file="%s_results_%s" % (config, ens), dir=dir, force=True)

            # Sort the NOE violations.
            noe_viol.sort()

            # Write the data.
            for i in range(len(noe_viol)):
                out_sorted.write("%-20i%20.15f\n" % (noe_viol[i][1], noe_viol[i][0]))


    def rdc_analysis(self):
        """Perform the RDC part of the analysis."""

        # Redirect STDOUT to a log file.
        if self.log:
            sys.stdout = open(self.results_dir+sep+"logs" + sep + "RDC_%s_analysis.log" % self.rdc_name, 'w')

        # The dipolar constant.
        d = 0.0
        if self.bond_length != None:
            d = 3.0 / (2.0*pi) * dipolar_constant(g13C, g1H, self.bond_length)

        # Create a directory for the save files.
        dir = self.results_dir + sep + "RDC_%s_results" % self.rdc_name
        mkdir_nofail(dir=dir)

        # Loop over the configurations.
        for config in self.configs:
            # Print out.
            print("\n"*10 + "# Set up for config " + config + " #" + "\n")

            # Open the results files.
            out = open(self.results_dir+sep+"Q_factors_" + config, 'w')
            out_sorted = open(self.results_dir+sep+"Q_factors_" + config + "_sorted", 'w')
            out.write("%-20s%20s%20s\n" % ("# Ensemble", "RDC_Q_factor(pales)", "RDC_Q_factor(standard)"))
            out_sorted.write("%-20s%20s\n" % ("# Ensemble", "RDC_Q_factor(pales)"))

            # Create the data pipe.
            self.interpreter.pipe.create("rdc_analysis_%s" % config, "N-state")

            # Read the first structure.
            self.interpreter.structure.read_pdb("ensembles_superimposed" + sep + config + "0.pdb", dir=self.results_dir, set_mol_name=config, set_model_num=list(range(1, self.num_models+1)))

            # Load all spins as the sequence.
            self.interpreter.structure.load_spins(ave_pos=False)

            # Create the pseudo-atoms.
            for i in range(len(self.pseudo)):
                self.interpreter.spin.create_pseudo(spin_name=self.pseudo[i][0], members=self.pseudo[i][1], averaging="linear")
            self.interpreter.sequence.display()

            # Read the RDC data.
            self.interpreter.rdc.read(align_id=self.rdc_file, file=self.rdc_file, spin_id1_col=self.rdc_spin_id1_col, spin_id2_col=self.rdc_spin_id2_col, data_col=self.rdc_data_col, error_col=self.rdc_error_col)

            # Define the magnetic dipole-dipole relaxation interaction.
            if self.bond_length != None:
                self.interpreter.interatom.set_dist(spin_id1='@C*', spin_id2='@H*', ave_dist=self.bond_length)
                self.interpreter.interatom.set_dist(spin_id1='@C*', spin_id2='@Q*', ave_dist=self.bond_length)
            else:
                self.interpreter.interatom.read_dist(file=self.bond_length_file, spin_id1_col=1, spin_id2_col=2, data_col=3)

            # Set the nuclear isotope.
            self.interpreter.spin.isotope(isotope='13C', spin_id='@C*')
            self.interpreter.spin.isotope(isotope='1H', spin_id='@H*')
            self.interpreter.spin.isotope(isotope='1H', spin_id='@Q*')

            # Set up the model.
            self.interpreter.n_state_model.select_model(model="fixed")

            # Print out.
            print("\n"*2 + "# Set up complete #" + "\n"*10)

            # Loop over each ensemble.
            q_factors = []
            for ens in range(self.num_ens):
                # Print out the ensemble to both the log and screen.
                if self.log:
                    sys.stdout.write(config + repr(ens) + "\n")
                sys.stderr.write(config + repr(ens) + "\n")

                # Delete the old structures.
                self.interpreter.structure.delete()

                # Read the ensemble.
                self.interpreter.structure.read_pdb("ensembles_superimposed" + sep + config + repr(ens) + ".pdb", dir=self.results_dir, set_mol_name=config, set_model_num=list(range(1, self.num_models+1)))

                # Get the positional information, then load the CH vectors.
                self.interpreter.structure.get_pos(ave_pos=False)
                if self.bond_length != None:
                    self.interpreter.interatom.set_dist(spin_id1='@C*', spin_id2='@H*', ave_dist=self.bond_length)
                else:
                    self.interpreter.interatom.read_dist(file=self.bond_length_file, spin_id1_col=1, spin_id2_col=2, data_col=3)
                self.interpreter.interatom.unit_vectors(ave=False)

                # Minimisation.
                #grid_search(inc=4)
                self.interpreter.minimise("simplex", constraints=False)

                # Store and write out the Q factors.
                q_factors.append([cdp.q_rdc, ens])
                out.write("%-20i%20.15f%20.15f\n" % (ens, cdp.q_rdc, cdp.q_rdc_norm2))

                # Calculate the alignment tensor in Hz, and store it for reference.
                cdp.align_tensor_Hz = d * cdp.align_tensors[0].A
                cdp.align_tensor_Hz_5D = d * cdp.align_tensors[0].A_5D

                # Save the state.
                self.interpreter.results.write(file="%s_results_%s" % (config, ens), dir=dir, force=True)

            # Sort the NOE violations.
            q_factors.sort()

            # Write the data.
            for i in range(len(q_factors)):
                out_sorted.write("%-20i%20.15f\n" % (q_factors[i][1], q_factors[i][0]))


    def sample(self):
        """Generate the ensembles by random sampling of the snapshots."""

        # Create the directory for the ensembles, if needed.
        mkdir_nofail(dir=self.results_dir + sep + "ensembles")

        # Loop over the configurations.
        for conf_index in range(len(self.configs)):
            # Loop over each ensemble.
            for ens in range(self.num_ens):
                # Random sampling.
                rand = []
                for j in range(self.num_models):
                    rand.append(randint(self.snapshot_min[conf_index], self.snapshot_max[conf_index]))

                # Print out.
                print("Generating ensemble %s%s from structures %s." % (self.configs[conf_index], ens, rand))

                # The file name.
                file_name = "ensembles" + sep + self.configs[conf_index] + repr(ens) + ".pdb"

                # Open the output file.
                out = open(self.results_dir+sep+file_name, 'w')

                # Header.
                out.write("REM Structures: " + repr(rand) + "\n")

                # Concatenation the files.
                for j in range(self.num_models):
                    # The random file.
                    rand_name = self.snapshot_dir[conf_index] + sep + self.configs[conf_index] + repr(rand[j]) + ".pdb"

                    # Append the file.
                    out.write(open(rand_name).read())

                # Close the file.
                out.close()


    def superimpose(self):
        """Superimpose the ensembles using fit to first in Molmol."""

        # Create the output directory.
        mkdir_nofail("ensembles_superimposed")

        # Logging turned on.
        if self.log:
            log = open(self.results_dir+sep+"logs" + sep + "superimpose_molmol.stderr", 'w')
            sys.stdout = open(self.results_dir+sep+"logs" + sep + "superimpose.log", 'w')

        # Loop over S and R.
        for config in ["R", "S"]:
            # Loop over each ensemble.
            for ens in range(self.num_ens):
                # The file names.
                file_in = "ensembles" + sep + config + repr(ens) + ".pdb"
                file_out = "ensembles_superimposed" + sep + config + repr(ens) + ".pdb"

                # Print out.
                sys.stderr.write("Superimposing %s with Molmol, output to %s.\n" % (file_in, file_out))
                if self.log:
                    log.write("\n\n\nSuperimposing %s with Molmol, output to %s.\n" % (file_in, file_out))

                # Failure handling (if a failure occurred and this is rerun, skip all existing files).
                if access(self.results_dir+sep+file_out, F_OK):
                    continue

                # Open the Molmol pipe.
                pipe = Popen("molmol -t -f -", shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE, close_fds=False)

                # Init all.
                pipe.stdin.write("InitAll yes\n")

                # Read the PDB.
                pipe.stdin.write("ReadPdb " + self.results_dir+sep+file_in + "\n")

                # Fitting to mean.
                pipe.stdin.write("Fit to_first 'selected'\n")
                pipe.stdin.write("Fit to_mean 'selected'\n")

                # Write the result.
                pipe.stdin.write("WritePdb " + self.results_dir+sep+file_out + "\n")

                # End Molmol.
                pipe.stdin.close()

                # Get STDOUT and STDERR.
                sys.stdout.write(pipe.stdout.read())
                if self.log:
                    log.write(pipe.stderr.read())

                # Close the pipe.
                pipe.stdout.close()
                pipe.stderr.close()

                # Open the superimposed file in relax.
                self.interpreter.reset()
                self.interpreter.pipe.create('out', 'N-state')
                self.interpreter.structure.read_pdb(file_out)

                # Fix the retarded MOLMOL proton naming.
                for model in cdp.structure.structural_data:
                    # Alias.
                    mol = model.mol[0]

                    # Loop over all atoms.
                    for i in range(len(mol.atom_name)):
                        # A proton.
                        if search('H', mol.atom_name[i]):
                            mol.atom_name[i] = mol.atom_name[i][1:] + mol.atom_name[i][0]

                # Replace the superimposed file.
                self.interpreter.structure.write_pdb(config + repr(ens) + ".pdb", dir=self.results_dir+sep+"ensembles_superimposed", force=True)
