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

# Python module imports.
from math import pi
from os import F_OK, R_OK, W_OK, X_OK, access, getcwd, listdir, sep
from os.path import isdir
from re import search
import sys
from time import sleep

# relax module imports.
from info import Info_box; info = Info_box()
from lib.errors import RelaxError, RelaxNoSequenceError, RelaxNoValueError
from lib.float import floatAsByteArray
from lib.text.string import LIST, PARAGRAPH, SECTION, SUBSECTION, TITLE, to_docstring
from pipe_control.interatomic import interatomic_loop
from pipe_control.mol_res_spin import exists_mol_res_spin_data, return_spin, spin_loop
from pipe_control.pipes import cdp_name, get_pipe, has_pipe, pipe_names, switch
from pipe_control.spectrometer import get_frequencies
from prompt.interpreter import Interpreter
from status import Status; status = Status()


doc = [
        [TITLE, "Automatic analysis for black-box model-free results."],
        [PARAGRAPH, "The dauvergne_protocol auto-analysis is designed for those who appreciate black-boxes or those who appreciate complex code.  Importantly, data at multiple magnetic field strengths is essential for this analysis.  If you would like to change how model-free analysis is performed, the code in the file auto_analyses/dauvergne_protocol.py in the base relax directory can be copied and modified as needed and used with the relax script interface.  This file is simply a complex relax script.  For a description of object-oriented coding in python using classes, functions/methods, self, etc., please see the python tutorial."],

        [SECTION, "References"],

        [SUBSECTION, "Auto-analysis primary reference"],
        [PARAGRAPH, "The model-free optimisation methodology herein is that of:"],
        [LIST, info.bib['dAuvergneGooley08b'].cite_short()],

        [SUBSECTION, "Techniques used in the auto-analysis"],
        [PARAGRAPH, "Other references for features of this dauvergne_protocol auto-analysis include model-free model selection using Akaike's Information Criterion:"],
        [LIST, info.bib['dAuvergneGooley03'].cite_short()],
        [PARAGRAPH, "The elimination of failed model-free models and Monte Carlo simulations:"],
        [LIST, info.bib['dAuvergneGooley06'].cite_short()],
        [PARAGRAPH, "Significant model-free optimisation improvements:"],
        [LIST, info.bib['dAuvergneGooley08a'].cite_short()],
        [PARAGRAPH, "Rather than searching for the lowest chi-squared value, this auto-analysis searches for the model with the lowest AIC criterion.  This complex multi-universe, multi-dimensional problem is formulated, using set theory, as the universal solution:"],
        [LIST, info.bib['dAuvergneGooley07'].cite_short()],
        [PARAGRAPH, "The basic three references for the original and extended model-free theories are:"],
        [LIST, info.bib['LipariSzabo82a'].cite_short()],
        [LIST, info.bib['LipariSzabo82b'].cite_short()],
        [LIST, info.bib['Clore90'].cite_short()],

        [SECTION, "How to use this auto-analysis"],
        [PARAGRAPH, "The five diffusion models used in this auto-analysis are:"],
        [LIST, "Model I   (MI)   - Local tm."],
        [LIST, "Model II  (MII)  - Sphere."],
        [LIST, "Model III (MIII) - Prolate spheroid."],
        [LIST, "Model IV  (MIV)  - Oblate spheroid."],
        [LIST, "Model V   (MV)   - Ellipsoid."],
        [PARAGRAPH, "If using the script-based user interface (UI), changing the value of the variable diff_model will determine the behaviour of this auto-analysis.  Model I must be optimised prior to any of the other diffusion models, while the Models II to V can be optimised in any order.  To select the various models, set the variable diff_model to the following strings:"],
        [LIST, "MI   - 'local_tm'"],
        [LIST, "MII  - 'sphere'"],
        [LIST, "MIII - 'prolate'"],
        [LIST, "MIV  - 'oblate'"],
        [LIST, "MV   - 'ellipsoid'"],
        [PARAGRAPH, "This approach has the advantage of eliminating the need for an initial estimate of a global diffusion tensor and removing all the problems associated with the initial estimate."],
        [PARAGRAPH, "It is important that the number of parameters in a model does not exceed the number of relaxation data sets for that spin.  If this is the case, the list of models in the mf_models and local_tm_models variables will need to be trimmed."],

        [SUBSECTION, "Model I - Local tm"],
        [PARAGRAPH, "This will optimise the diffusion model whereby all spin of the molecule have a local tm value, i.e. there is no global diffusion tensor.  This model needs to be optimised prior to optimising any of the other diffusion models.  Each spin is fitted to the multiple model-free models separately, where the parameter tm is included in each model."],
        [PARAGRAPH, "AIC model selection is used to select the models for each spin."],

        [SUBSECTION, "Model II - Sphere"],
        [PARAGRAPH, "This will optimise the isotropic diffusion model.  Multiple steps are required, an initial optimisation of the diffusion tensor, followed by a repetitive optimisation until convergence of the diffusion tensor.  In the relax script UI each of these steps requires this script to be rerun, unless the conv_loop flag is True.  In the GUI (graphical user interface), the procedure is repeated automatically until convergence.  For the initial optimisation, which will be placed in the directory './sphere/init/', the following steps are used:"],
        [PARAGRAPH, "The model-free models and parameter values for each spin are set to those of diffusion model MI."],
        [PARAGRAPH, "The local tm parameter is removed from the models."],
        [PARAGRAPH, "The model-free parameters are fixed and a global spherical diffusion tensor is minimised."],
        [PARAGRAPH, "For the repetitive optimisation, each minimisation is named from 'round_1' onwards.  The initial 'round_1' optimisation will extract the diffusion tensor from the results file in './sphere/init/', and the results will be placed in the directory './sphere/round_1/'.  Each successive round will take the diffusion tensor from the previous round.  The following steps are used:"],
        [PARAGRAPH, "The global diffusion tensor is fixed and the multiple model-free models are fitted to each spin."],
        [PARAGRAPH, "AIC model selection is used to select the models for each spin."],
        [PARAGRAPH, "All model-free and diffusion parameters are allowed to vary and a global optimisation of all parameters is carried out."],

        [SUBSECTION, "Model III - Prolate spheroid"],
        [PARAGRAPH, "The methods used are identical to those of diffusion model MII, except that an axially symmetric diffusion tensor with Da >= 0 is used.  The base directory containing all the results is './prolate/'."],

        [SUBSECTION, "Model IV - Oblate spheroid"],
        [PARAGRAPH, "The methods used are identical to those of diffusion model MII, except that an axially symmetric diffusion tensor with Da <= 0 is used.  The base directory containing all the results is './oblate/'."],

        [SUBSECTION, "Model V - Ellipsoid"],
        [PARAGRAPH, "The methods used are identical to those of diffusion model MII, except that a fully anisotropic diffusion tensor is used (also known as rhombic or asymmetric diffusion).  The base directory is './ellipsoid/'."],

        [SUBSECTION, "Final run"],
        [PARAGRAPH, "Once all the diffusion models have converged, the final run can be executed.  This is done by setting the variable diff_model to 'final'.  This consists of two steps, diffusion tensor model selection, and Monte Carlo simulations.  Firstly AIC model selection is used to select between the diffusion tensor models.  Monte Carlo simulations are then run solely on this selected diffusion model.  Minimisation of the model is bypassed as it is assumed that the model is already fully optimised (if this is not the case the final run is not yet appropriate)."],
        [PARAGRAPH, "The final black-box model-free results will be placed in the file 'final/results'."]
]


# Build the module docstring.
__doc__ = to_docstring(doc)



class dAuvergne_protocol:
    """The model-free auto-analysis."""

    # Some class variables.
    opt_func_tol = 1e-25
    opt_max_iterations = int(1e7)

    def __init__(self, pipe_name=None, pipe_bundle=None, results_dir=None, write_results_dir=None, diff_model=None, mf_models=['m0', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8', 'm9'], local_tm_models=['tm0', 'tm1', 'tm2', 'tm3', 'tm4', 'tm5', 'tm6', 'tm7', 'tm8', 'tm9'], grid_inc=11, diff_tensor_grid_inc={'sphere': 11, 'prolate': 11, 'oblate': 11, 'ellipsoid': 6}, min_algor='newton', mc_sim_num=500, max_iter=None, user_fns=None, conv_loop=True):
        """Perform the full model-free analysis protocol of d'Auvergne and Gooley, 2008b.

        @keyword pipe_name:             The name of the data pipe containing the sequence info.  This data pipe should have all values set including the CSA value, the bond length, the heteronucleus name and proton name.  It should also have all relaxation data loaded.
        @type pipe_name:                str
        @keyword pipe_bundle:           The data pipe bundle to associate all spawned data pipes with.
        @type pipe_bundle:              str
        @keyword results_dir:           The directory where optimisation results will read from.  Results will also be saved to this directory if the write_results_dir argument is not given.
        @type results_dir:              str
        @keyword write_results_dir:     The directory where optimisation results will be saved in.  If None, it will default to the value of the results_dir argument.  This is mainly used for debugging.
        @type write_results_dir:        str or None
        @keyword diff_model:            The global diffusion model to optimise.  This can be one of 'local_tm', 'sphere', 'oblate', 'prolate', 'ellipsoid', or 'final'.  If all or a subset of these are supplied as a list, then these will be automatically looped over and calculated.
        @type diff_model:               str or list of str
        @keyword mf_models:             The model-free models.
        @type mf_models:                list of str
        @keyword local_tm_models:       The model-free models.
        @type local_tm_models:          list of str
        @keyword grid_inc:              The grid search size (the number of increments per dimension).
        @type grid_inc:                 int
        @keyword diff_tensor_grid_inc:  A list of grid search sizes for the optimisation of the sphere, prolate spheroid, oblate spheroid, and ellipsoid.
        @type diff_tensor_grid_inc:     list of int
        @keyword min_algor:             The minimisation algorithm (in most cases this should not be changed).
        @type min_algor:                str
        @keyword mc_sim_num:            The number of Monte Carlo simulations to be used for error analysis at the end of the analysis.
        @type mc_sim_num:               int
        @keyword max_iter:              The maximum number of iterations for the global iteration.  Set to None, then the algorithm iterates until convergence.
        @type max_iter:                 int or None.
        @keyword user_fns:              A dictionary of replacement user functions.  These will overwrite the standard user functions.  The key should be the name of the user function or user function class and the value should be the function or class instance.
        @type user_fns:                 dict
        @keyword conv_loop:             Automatic looping over all rounds until convergence.
        @type conv_loop:                bool
        """

        # Execution lock.
        status.exec_lock.acquire(pipe_bundle, mode='auto-analysis')

        # Store the args.
        self.pipe_name = pipe_name
        self.pipe_bundle = pipe_bundle
        self.mf_models = mf_models
        self.local_tm_models = local_tm_models
        self.grid_inc = grid_inc
        self.diff_tensor_grid_inc = diff_tensor_grid_inc
        self.min_algor = min_algor
        self.mc_sim_num = mc_sim_num
        self.max_iter = max_iter
        self.conv_loop = conv_loop

        # The model-free data pipe names.
        self.mf_model_pipes = []
        for i in range(len(self.mf_models)):
            self.mf_model_pipes.append(self.name_pipe(self.mf_models[i]))
        self.local_tm_model_pipes = []
        for i in range(len(self.local_tm_models)):
            self.local_tm_model_pipes.append(self.name_pipe(self.local_tm_models[i]))

        # The diffusion models.
        if isinstance(diff_model, list):
            self.diff_model_list = diff_model
        else:
            self.diff_model_list = [diff_model]

        # Project directory (i.e. directory containing the model-free model results and the newly generated files)
        if results_dir:
            self.results_dir = results_dir + sep
        else:
            self.results_dir = getcwd() + sep
        if write_results_dir:
            self.write_results_dir = write_results_dir + sep
        else:
            self.write_results_dir = self.results_dir

        # Data checks.
        self.check_vars()

        # Set the data pipe to the current data pipe.
        if self.pipe_name != cdp_name():
            switch(self.pipe_name)

        # Some info for the status.
        self.status_setup()

        # Load the interpreter.
        self.interpreter = Interpreter(show_script=False, raise_relax_error=True)
        self.interpreter.populate_self()
        self.interpreter.on(verbose=False)

        # Replacement user functions.
        if user_fns:
            for name in user_fns:
                setattr(self.interpreter, name, user_fns[name])

        # Execute the protocol.
        try:
            # Loop over the models.
            for self.diff_model in self.diff_model_list:
                # Wait a little while between diffusion models.
                sleep(1)

                # Set the global model name.
                status.auto_analysis[self.pipe_bundle].diff_model = self.diff_model

                # Initialise the convergence data structures.
                self.conv_data = Container()
                self.conv_data.chi2 = []
                self.conv_data.models = []
                self.conv_data.diff_vals = []
                if self.diff_model == 'sphere':
                    self.conv_data.diff_params = ['tm']
                elif self.diff_model == 'oblate' or self.diff_model == 'prolate':
                    self.conv_data.diff_params = ['tm', 'Da', 'theta', 'phi']
                elif self.diff_model == 'ellipsoid':
                    self.conv_data.diff_params = ['tm', 'Da', 'Dr', 'alpha', 'beta', 'gamma']
                self.conv_data.spin_ids = []
                self.conv_data.mf_params = []
                self.conv_data.mf_vals = []

                # Execute the analysis for each diffusion model.
                self.execute()

        # Clean up.
        finally:
            # Finish and unlock execution.
            status.auto_analysis[self.pipe_bundle].fin = True
            status.current_analysis = None
            status.exec_lock.release()


    def check_vars(self):
        """Check that the user has set the variables correctly."""

        # The pipe bundle.
        if not isinstance(self.pipe_bundle, str):
            raise RelaxError("The pipe bundle name '%s' is invalid." % self.pipe_bundle)

        # The diff model.
        valid_models = ['local_tm', 'sphere', 'oblate', 'prolate', 'ellipsoid', 'final']
        for i in range(len(self.diff_model_list)):
            if self.diff_model_list[i] not in valid_models:
                raise RelaxError("The diff_model value '%s' is incorrectly set.  It must be one of %s." % (self.diff_model_list[i], valid_models))

        # Model-free models.
        mf_models = ['m0', 'm1', 'm2', 'm3', 'm4', 'm5', 'm6', 'm7', 'm8', 'm9']
        local_tm_models = ['tm0', 'tm1', 'tm2', 'tm3', 'tm4', 'tm5', 'tm6', 'tm7', 'tm8', 'tm9']
        if not isinstance(self.mf_models, list):
            raise RelaxError("The self.mf_models user variable must be a list.")
        if not isinstance(self.local_tm_models, list):
            raise RelaxError("The self.local_tm_models user variable must be a list.")
        for i in range(len(self.mf_models)):
            if self.mf_models[i] not in mf_models:
                raise RelaxError("The self.mf_models user variable '%s' is incorrectly set.  It must be one of %s." % (self.mf_models, mf_models))
        for i in range(len(self.local_tm_models)):
            if self.local_tm_models[i] not in local_tm_models:
                raise RelaxError("The self.local_tm_models user variable '%s' is incorrectly set.  It must be one of %s." % (self.local_tm_models, local_tm_models))

        # Sequence data.
        if not exists_mol_res_spin_data():
            raise RelaxNoSequenceError(self.pipe_name)

        # Relaxation data.
        if not hasattr(cdp, 'ri_ids') or len(cdp.ri_ids) == 0:
            raise RelaxNoRiError(ri_id)

        # Insufficient data.
        if len(cdp.ri_ids) <= 3:
            raise RelaxError("Insufficient relaxation data, 4 or more data sets are essential for the execution of this script.")

        # Spin vars.
        for spin, spin_id in spin_loop(return_id=True):
            # Skip deselected spins.
            if not spin.select:
                continue

            # Test if the isotope type has been set.
            if not hasattr(spin, 'isotope') or spin.isotope == None:
                raise RelaxNoValueError("nuclear isotope type", spin_id=spin_id)

            # Skip spins with no relaxation data.
            if not hasattr(spin, 'ri_data') or spin.ri_data == None:
                continue

            # Test if the CSA value has been set.
            if not hasattr(spin, 'csa') or spin.csa == None:
                raise RelaxNoValueError("CSA", spin_id=spin_id)

        # Interatomic vars.
        for interatom in interatomic_loop():
            # Get the corresponding spins.
            spin1 = return_spin(interatom.spin_id1)
            spin2 = return_spin(interatom.spin_id2)

            # Skip deselected spins.
            if not spin1.select or not spin2.select:
                continue

            # Test if the interatomic distance has been set.
            if not hasattr(interatom, 'r') or interatom.r == None:
                raise RelaxNoValueError("interatomic distance", spin_id=interatom.spin_id1, spin_id2=interatom.spin_id2)

        # Min vars.
        if not isinstance(self.grid_inc, int):
            raise RelaxError("The grid_inc user variable '%s' is incorrectly set.  It should be an integer." % self.grid_inc)
        if not isinstance(self.diff_tensor_grid_inc, dict):
            raise RelaxError("The diff_tensor_grid_inc user variable '%s' is incorrectly set.  It should be a dictionary." % self.diff_tensor_grid_inc)
        for tensor in ['sphere', 'prolate', 'oblate', 'ellipsoid']:
            if not tensor in self.diff_tensor_grid_inc:
                raise RelaxError("The diff_tensor_grid_inc user variable '%s' is incorrectly set.  It should contain the '%s' key." % (self.diff_tensor_grid_inc, tensor))
            if not isinstance(self.diff_tensor_grid_inc[tensor], int):
                raise RelaxError("The diff_tensor_grid_inc user variable '%s' is incorrectly set.  The value corresponding to the key '%s' should be an integer." % (self.diff_tensor_grid_inc, tensor))
        if not isinstance(self.min_algor, str):
            raise RelaxError("The min_algor user variable '%s' is incorrectly set.  It should be a string." % self.min_algor)
        if not isinstance(self.mc_sim_num, int):
            raise RelaxError("The mc_sim_num user variable '%s' is incorrectly set.  It should be an integer." % self.mc_sim_num)

        # Looping.
        if not isinstance(self.conv_loop, bool):
            raise RelaxError("The conv_loop user variable '%s' is incorrectly set.  It should be one of the booleans True or False." % self.conv_loop)


    def convergence(self):
        """Test for the convergence of the global model."""

        # Print out.
        print("\n\n\n")
        print("#####################")
        print("# Convergence tests #")
        print("#####################\n")

        # Maximum number of iterations reached.
        if self.max_iter and self.round > self.max_iter:
            print("Maximum number of global iterations reached.  Terminating the protocol before convergence has been reached.")
            return True

        # Store the data of the current data pipe.
        self.conv_data.chi2.append(cdp.chi2)

        # Create a string representation of the model-free models of the current data pipe.
        curr_models = ''
        for spin in spin_loop():
            if hasattr(spin, 'model'):
                if not spin.model == 'None':
                    curr_models = curr_models + spin.model
        self.conv_data.models.append(curr_models)

        # Store the diffusion tensor parameters.
        self.conv_data.diff_vals.append([])
        for param in self.conv_data.diff_params:
            # Get the parameter values.
            self.conv_data.diff_vals[-1].append(getattr(cdp.diff_tensor, param))

        # Store the model-free parameters.
        self.conv_data.mf_vals.append([])
        self.conv_data.mf_params.append([])
        self.conv_data.spin_ids.append([])
        for spin, spin_id in spin_loop(return_id=True):
            # Skip spin systems with no 'params' object.
            if not hasattr(spin, 'params'):
                continue

            # Add the spin ID, parameters, and empty value list.
            self.conv_data.spin_ids[-1].append(spin_id)
            self.conv_data.mf_params[-1].append([])
            self.conv_data.mf_vals[-1].append([])

            # Loop over the parameters.
            for j in range(len(spin.params)):
                # Get the parameters and values.
                self.conv_data.mf_params[-1][-1].append(spin.params[j])
                self.conv_data.mf_vals[-1][-1].append(getattr(spin, spin.params[j].lower()))

        # No need for tests.
        if self.round == 1:
            print("First round of optimisation, skipping the convergence tests.\n\n\n")
            return False

        # Loop over the iterations.
        converged = False
        for i in range(self.start_round, self.round - 1):
            # Print out.
            print("\n\n\n# Comparing the current iteration to iteration %i.\n" % (i+1))

            # Index.
            index = i - self.start_round

            # Chi-squared test.
            print("Chi-squared test:")
            print("    chi2 (iter %i):  %s" % (i+1, self.conv_data.chi2[index]))
            print("        (as an IEEE-754 byte array:  %s)" % floatAsByteArray(self.conv_data.chi2[index]))
            print("    chi2 (iter %i):  %s" % (self.round, self.conv_data.chi2[-1]))
            print("        (as an IEEE-754 byte array:  %s)" % floatAsByteArray(self.conv_data.chi2[-1]))
            print("    chi2 (difference):  %s" % (self.conv_data.chi2[index] - self.conv_data.chi2[-1]))
            if self.conv_data.chi2[index] == self.conv_data.chi2[-1]:
                print("    The chi-squared value has converged.\n")
            else:
                print("    The chi-squared value has not converged.\n")
                continue

            # Identical model-free model test.
            print("Identical model-free models test:")
            if self.conv_data.models[index] == self.conv_data.models[-1]:
                print("    The model-free models have converged.\n")
            else:
                print("    The model-free models have not converged.\n")
                continue

            # Identical diffusion tensor parameter value test.
            print("Identical diffusion tensor parameter test:")
            params_converged = True
            for k in range(len(self.conv_data.diff_params)):
                # Test if not identical.
                if self.conv_data.diff_vals[index][k] != self.conv_data.diff_vals[-1][k]:
                    print("    Parameter:   %s" % param)
                    print("    Value (iter %i):  %s" % (i+1, self.conv_data.diff_vals[index][k]))
                    print("        (as an IEEE-754 byte array:  %s)" % floatAsByteArray(self.conv_data.diff_vals[index][k]))
                    print("    Value (iter %i):  %s" % (self.round, self.conv_data.diff_vals[-1][k]))
                    print("        (as an IEEE-754 byte array:  %s)" % floatAsByteArray(self.conv_data.diff_vals[-1][k]))
                    print("    The diffusion parameters have not converged.\n")
                    params_converged = False
                    break
            if not params_converged:
                continue
            print("    The diffusion tensor parameters have converged.\n")

            # Identical model-free parameter value test.
            print("\nIdentical model-free parameter test:")
            if len(self.conv_data.spin_ids[index]) != len(self.conv_data.spin_ids[-1]):
                print("    Different number of spins.")
                continue
            for j in range(len(self.conv_data.spin_ids[-1])):
                # Loop over the parameters.
                for k in range(len(self.conv_data.mf_params[-1][j])):
                    # Test if not identical.
                    if self.conv_data.mf_vals[index][j][k] != self.conv_data.mf_vals[-1][j][k]:
                        print("    Spin ID:     %s" % self.conv_data.spin_ids[-1][j])
                        print("    Parameter:   %s" % self.conv_data.mf_params[-1][j][k])
                        print("    Value (iter %i): %s" % (i+1, self.conv_data.mf_vals[index][j][k]))
                        print("        (as an IEEE-754 byte array:  %s)" % floatAsByteArray(self.conv_data.mf_vals[index][j][k]))
                        print("    Value (iter %i): %s" % (self.round, self.conv_data.mf_vals[-1][j][k]))
                        print("        (as an IEEE-754 byte array:  %s)" % floatAsByteArray(self.conv_data.mf_vals[index][j][k]))
                        print("    The model-free parameters have not converged.\n")
                        params_converged = False
                        break
            if not params_converged:
                continue
            print("    The model-free parameters have converged.\n")

            # Convergence.
            converged = True
            break


        # Final printout.
        ##################

        print("\nConvergence:")
        if converged:
            # Update the status.
            status.auto_analysis[self.pipe_bundle].convergence = True

            # Print out.
            print("    [ Yes ]")

            # Return the termination condition.
            return True
        else:
            # Print out.
            print("    [ No ]")

            # Return False to not terminate.
            return False


    def determine_rnd(self, model=None):
        """Function for returning the name of next round of optimisation."""

        # The base model directory.
        base_dir = self.results_dir+sep+model

        # Printout.
        sys.stdout.write("\n\nDetermining the next round of optimisation for '%s':  " % base_dir)

        # Catch if a file exists with the name of the directory.
        if not isdir(base_dir) and access(base_dir, F_OK):
            raise RelaxError("The base model directory '%s' is not usable as a file with the same name already exists." % base_dir)

        # If no directory exists, set the round to 'init' or 0.
        if not isdir(base_dir):
            sys.stdout.write(" 0.\n\n")
            return 0

        # Is the directory readable, writable, and executable.
        if not access(base_dir, R_OK):
            raise RelaxError("The base model directory '%s' is not readable." % base_dir)
        if not access(base_dir, W_OK):
            raise RelaxError("The base model directory '%s' is not writable." % base_dir)
        if not access(base_dir, X_OK):
            raise RelaxError("The base model directory '%s' is not executable." % base_dir)

        # Get a list of all files in the directory model.
        dir_list = listdir(base_dir)

        # Set the round to 'init' or 0 if there is no directory called 'init'.
        if 'init' not in dir_list:
            sys.stdout.write(" 0.\n\n")
            return 0

        # Create a list of all files which begin with 'round_'.
        rnd_dirs = []
        for file in dir_list:
            if search('^round_', file):
                rnd_dirs.append(file)

        # Create a sorted list of integer round numbers.
        numbers = []
        for dir in rnd_dirs:
            try:
                numbers.append(int(dir[6:]))
            except:
                pass
        numbers.sort()

        # No directories beginning with 'round_' exist, set the round to 1.
        if not len(numbers):
            sys.stdout.write(" 1.\n\n")
            return 1

        # The highest number.
        max_round = numbers[-1]

        # Check that the opt/results file exists for the round (working backwards).
        for i in range(max_round, -1, -1):
            # Assume the round is complete.
            complete_round = i

            # The file root.
            file_root = base_dir + sep + "round_%i" % i + sep + 'opt' + sep + 'results'

            # Stop looping when the opt/results file is found.
            if access(file_root + '.bz2', F_OK):
                break
            if access(file_root + '.gz', F_OK):
                break
            if access(file_root, F_OK):
                break

        # No round, so assume the initial state.
        if complete_round == 0:
            sys.stdout.write(" 0.\n\n")
            return 0

        # Determine the number for the next round (add 1 to the highest completed round).
        sys.stdout.write(" %i.\n\n" % complete_round + 1)
        return complete_round + 1


    def execute(self):
        """Execute the protocol."""

        # MI - Local tm.
        ################

        if self.diff_model == 'local_tm':
            # Base directory to place files into.
            self.base_dir = self.results_dir+'local_tm'+sep

            # Sequential optimisation of all model-free models (function must be modified to suit).
            self.multi_model(local_tm=True)

            # Model selection.
            self.model_selection(modsel_pipe=self.name_pipe('aic'), dir=self.base_dir + 'aic')


        # Diffusion models MII to MV.
        #############################

        elif self.diff_model == 'sphere' or self.diff_model == 'prolate' or self.diff_model == 'oblate' or self.diff_model == 'ellipsoid':
            # No local_tm directory!
            dir_list = listdir(self.results_dir)
            if 'local_tm' not in dir_list:
                raise RelaxError("The local_tm model must be optimised first.")

            # The initial round of optimisation - not zero if calculations were interrupted.
            self.start_round = self.determine_rnd(model=self.diff_model)

            # Loop until convergence if conv_loop is set, otherwise just loop once.
            # This looping could be made much cleaner by removing the dependence on the determine_rnd() function.
            while True:
                # Determine which round of optimisation to do (init, round_1, round_2, etc).
                self.round = self.determine_rnd(model=self.diff_model)
                status.auto_analysis[self.pipe_bundle].round = self.round

                # Inital round of optimisation for diffusion models MII to MV.
                if self.round == 0:
                    # Base directory to place files into.
                    self.base_dir = self.results_dir+self.diff_model+sep+'init'+sep

                    # Run name.
                    name = self.name_pipe(self.diff_model)

                    # Create the data pipe (deleting the old one if it exists).
                    if has_pipe(name):
                        self.interpreter.pipe.delete(name)
                    self.interpreter.pipe.create(name, 'mf', bundle=self.pipe_bundle)

                    # Load the local tm diffusion model MI results.
                    self.interpreter.results.read(file='results', dir=self.results_dir+'local_tm'+sep+'aic')

                    # Remove the tm parameter.
                    self.interpreter.model_free.remove_tm()

                    # Initialise the diffusion tensor.
                    if self.diff_model == 'sphere':
                        self.interpreter.diffusion_tensor.init(None, fixed=False)
                        inc = self.diff_tensor_grid_inc['sphere']
                    elif self.diff_model == 'prolate':
                        self.interpreter.diffusion_tensor.init((None, None, None, None), spheroid_type='prolate', fixed=False)
                        inc = self.diff_tensor_grid_inc['prolate']
                    elif self.diff_model == 'oblate':
                        self.interpreter.diffusion_tensor.init((None, None, None, None), spheroid_type='oblate', fixed=False)
                        inc = self.diff_tensor_grid_inc['oblate']
                    elif self.diff_model == 'ellipsoid':
                        self.interpreter.diffusion_tensor.init((None, None, None, None, None, None), fixed=False)
                        inc = self.diff_tensor_grid_inc['ellipsoid']

                    # Minimise just the diffusion tensor.
                    self.interpreter.fix('all_spins')
                    self.interpreter.minimise.grid_search(inc=inc)
                    self.interpreter.minimise.execute(self.min_algor, func_tol=self.opt_func_tol, max_iter=self.opt_max_iterations)

                    # Write the results.
                    self.interpreter.results.write(file='results', dir=self.base_dir, force=True)


                # Normal round of optimisation for diffusion models MII to MV.
                else:
                    # Base directory to place files into.
                    self.base_dir = self.results_dir+self.diff_model + sep+'round_'+repr(self.round)+sep

                    # Load the optimised diffusion tensor from either the previous round.
                    self.load_tensor()

                    # Sequential optimisation of all model-free models (function must be modified to suit).
                    self.multi_model()

                    # Model selection.
                    self.model_selection(modsel_pipe=self.name_pipe('aic'), dir=self.base_dir + 'aic')

                    # Final optimisation of all diffusion and model-free parameters.
                    self.interpreter.fix('all', fixed=False)

                    # Minimise all parameters.
                    self.interpreter.minimise.execute(self.min_algor, func_tol=self.opt_func_tol, max_iter=self.opt_max_iterations)

                    # Write the results.
                    dir = self.base_dir + 'opt'
                    self.interpreter.results.write(file='results', dir=dir, force=True)

                    # Test for convergence.
                    converged = self.convergence()

                    # Break out of the infinite while loop if automatic looping is not activated or if convergence has occurred.
                    if converged or not self.conv_loop:
                        break

            # Unset the status.
            status.auto_analysis[self.pipe_bundle].round = None


        # Final run.
        ############

        elif self.diff_model == 'final':
            # Diffusion model selection.
            ############################

            # The contents of the results directory.
            dir_list = listdir(self.results_dir)

            # Check that the minimal set of global diffusion models required for the protocol has been optimised.
            min_models = ['local_tm', 'sphere']
            for model in min_models:
                if model not in dir_list:
                    raise RelaxError("The minimum set of global diffusion models required for the protocol have not been optimised, the '%s' model results cannot be found." % model)

            # Build a list of all global diffusion models optimised.
            all_models = ['local_tm', 'sphere', 'prolate', 'oblate', 'ellipsoid']
            self.opt_models = []
            self.pipes = []
            for model in all_models:
                if model in dir_list:
                    self.opt_models.append(model)
                    self.pipes.append(self.name_pipe(model))

            # Remove all temporary pipes used in this auto-analysis.
            for name in pipe_names(bundle=self.pipe_bundle):
                if name in self.pipes + self.mf_model_pipes + self.local_tm_model_pipes + [self.name_pipe('aic'), self.name_pipe('previous')]:
                    self.interpreter.pipe.delete(name)

            # Create the local_tm data pipe.
            self.interpreter.pipe.create(self.name_pipe('local_tm'), 'mf', bundle=self.pipe_bundle)

            # Load the local tm diffusion model MI results.
            self.interpreter.results.read(file='results', dir=self.results_dir+'local_tm'+sep+'aic')

            # Loop over models MII to MV.
            for model in ['sphere', 'prolate', 'oblate', 'ellipsoid']:
                # Skip missing models.
                if model not in self.opt_models:
                    continue

                # Determine which was the last round of optimisation for each of the models.
                self.round = self.determine_rnd(model=model) - 1

                # If no directories begining with 'round_' exist, the script has not been properly utilised!
                if self.round < 1:
                    # Construct the name of the diffusion tensor.
                    name = model
                    if model == 'prolate' or model == 'oblate':
                        name = name + ' spheroid'

                    # Throw an error to prevent misuse of the script.
                    raise RelaxError("Multiple rounds of optimisation of the " + name + " (between 8 to 15) are required for the proper execution of this script.")

                # Create the data pipe.
                self.interpreter.pipe.create(self.name_pipe(model), 'mf', bundle=self.pipe_bundle)

                # Load the diffusion model results.
                self.interpreter.results.read(file='results', dir=self.results_dir+model + sep+'round_'+repr(self.round)+sep+'opt')

            # Model selection between MI to MV.
            self.model_selection(modsel_pipe=self.name_pipe('final'), write_flag=False)


            # Monte Carlo simulations.
            ##########################

            # Fix the diffusion tensor, if it exists.
            if hasattr(get_pipe(self.name_pipe('final')), 'diff_tensor'):
                self.interpreter.fix('diff')

            # Simulations.
            self.interpreter.monte_carlo.setup(number=self.mc_sim_num)
            self.interpreter.monte_carlo.create_data()
            self.interpreter.monte_carlo.initial_values()
            self.interpreter.minimise.execute(self.min_algor, func_tol=self.opt_func_tol, max_iter=self.opt_max_iterations)
            self.interpreter.eliminate()
            self.interpreter.monte_carlo.error_analysis()


            # Write the final results.
            ##########################

            # Create results files and plots of the data.
            self.write_results()


        # Unknown script behaviour.
        ###########################

        else:
            raise RelaxError("Unknown diffusion model, change the value of 'self.diff_model'")


    def load_tensor(self):
        """Function for loading the optimised diffusion tensor."""

        # Create the data pipe for the previous data (deleting the old data pipe first if necessary).
        if has_pipe(self.name_pipe('previous')):
            self.interpreter.pipe.delete(self.name_pipe('previous'))
        self.interpreter.pipe.create(self.name_pipe('previous'), 'mf', bundle=self.pipe_bundle)

        # Load the optimised diffusion tensor from the initial round.
        if self.round == 1:
            self.interpreter.results.read('results', self.results_dir+self.diff_model + sep+'init')

        # Load the optimised diffusion tensor from the previous round.
        else:
            self.interpreter.results.read('results', self.results_dir+self.diff_model + sep+'round_'+repr(self.round-1)+sep+'opt')


    def model_selection(self, modsel_pipe=None, dir=None, write_flag=True):
        """Model selection function."""

        # Model selection (delete the model selection pipe if it already exists).
        if has_pipe(modsel_pipe):
            self.interpreter.pipe.delete(modsel_pipe)
        self.interpreter.model_selection(method='AIC', modsel_pipe=modsel_pipe, bundle=self.pipe_bundle, pipes=self.pipes)

        # Write the results.
        if write_flag:
            self.interpreter.results.write(file='results', dir=dir, force=True)


    def multi_model(self, local_tm=False):
        """Function for optimisation of all model-free models."""

        # Set the data pipe names (also the names of preset model-free models).
        if local_tm:
            models = self.local_tm_models
            self.pipes = self.local_tm_models
        else:
            models = self.mf_models
        self.pipes = []
        for i in range(len(models)):
            self.pipes.append(self.name_pipe(models[i]))

        # Loop over the data pipes.
        for i in range(len(models)):
            # Place the model name into the status container.
            status.auto_analysis[self.pipe_bundle].current_model = models[i]

            # Create the data pipe (by copying).
            if has_pipe(self.pipes[i]):
                self.interpreter.pipe.delete(self.pipes[i])
            self.interpreter.pipe.copy(self.pipe_name, self.pipes[i], bundle_to=self.pipe_bundle)
            self.interpreter.pipe.switch(self.pipes[i])

            # Copy the diffusion tensor from the 'opt' data pipe and prevent it from being minimised.
            if not local_tm:
                self.interpreter.diffusion_tensor.copy(self.name_pipe('previous'))
                self.interpreter.fix('diff')

            # Select the model-free model.
            self.interpreter.model_free.select_model(model=models[i])

            # Minimise.
            self.interpreter.minimise.grid_search(inc=self.grid_inc)
            self.interpreter.minimise.execute(self.min_algor, func_tol=self.opt_func_tol, max_iter=self.opt_max_iterations)

            # Model elimination.
            self.interpreter.eliminate()

            # Write the results.
            dir = self.base_dir + models[i]
            self.interpreter.results.write(file='results', dir=dir, force=True)

        # Unset the status.
        status.auto_analysis[self.pipe_bundle].current_model = None


    def name_pipe(self, prefix):
        """Generate a unique name for the data pipe.

        @param prefix:  The prefix of the data pipe name.
        @type prefix:   str
        """

        # The unique pipe name.
        name = "%s - %s" % (prefix, self.pipe_bundle)

        # Return the name.
        return name


    def status_setup(self):
        """Initialise the status object."""

        # Initialise the status object for this auto-analysis.
        status.init_auto_analysis(self.pipe_bundle, type='dauvergne_protocol')
        status.current_analysis = self.pipe_bundle

        # The global diffusion model.
        status.auto_analysis[self.pipe_bundle].diff_model = None

        # The round of optimisation, i.e. the global iteration.
        status.auto_analysis[self.pipe_bundle].round = None

        # The list of model-free local tm models for optimisation, i.e. the global iteration.
        status.auto_analysis[self.pipe_bundle].local_tm_models = self.local_tm_models

        # The list of model-free models for optimisation, i.e. the global iteration.
        status.auto_analysis[self.pipe_bundle].mf_models = self.mf_models

        # The current model-free model.
        status.auto_analysis[self.pipe_bundle].current_model = None

        # The maximum number of iterations of the global model.
        status.auto_analysis[self.pipe_bundle].max_iter = self.max_iter

        # The convergence of the global model.
        status.auto_analysis[self.pipe_bundle].convergence = False


    def write_results(self):
        """Create Grace plots of the final model-free results."""

        # Save the results file.
        dir = self.write_results_dir + 'final'
        self.interpreter.results.write(file='results', dir=dir, force=True)

        # The Grace plots.
        dir = self.write_results_dir + 'final' + sep + 'grace'
        self.interpreter.grace.write(x_data_type='res_num', y_data_type='s2',  file='s2.agr',        dir=dir, force=True)
        self.interpreter.grace.write(x_data_type='res_num', y_data_type='s2f', file='s2f.agr',       dir=dir, force=True)
        self.interpreter.grace.write(x_data_type='res_num', y_data_type='s2s', file='s2s.agr',       dir=dir, force=True)
        self.interpreter.grace.write(x_data_type='res_num', y_data_type='te',  file='te.agr',        dir=dir, force=True)
        self.interpreter.grace.write(x_data_type='res_num', y_data_type='tf',  file='tf.agr',        dir=dir, force=True)
        self.interpreter.grace.write(x_data_type='res_num', y_data_type='ts',  file='ts.agr',        dir=dir, force=True)
        self.interpreter.grace.write(x_data_type='res_num', y_data_type='rex', file='rex.agr',       dir=dir, force=True)
        self.interpreter.grace.write(x_data_type='s2',      y_data_type='te',  file='s2_vs_te.agr',  dir=dir, force=True)
        self.interpreter.grace.write(x_data_type='s2',      y_data_type='rex', file='s2_vs_rex.agr', dir=dir, force=True)
        self.interpreter.grace.write(x_data_type='te',      y_data_type='rex', file='te_vs_rex.agr', dir=dir, force=True)

        # Write the values to text files.
        dir = self.write_results_dir + 'final'
        self.interpreter.value.write(param='s2',       file='s2.txt',       dir=dir, force=True)
        self.interpreter.value.write(param='s2f',      file='s2f.txt',      dir=dir, force=True)
        self.interpreter.value.write(param='s2s',      file='s2s.txt',      dir=dir, force=True)
        self.interpreter.value.write(param='te',       file='te.txt',       dir=dir, force=True)
        self.interpreter.value.write(param='tf',       file='tf.txt',       dir=dir, force=True)
        self.interpreter.value.write(param='ts',       file='ts.txt',       dir=dir, force=True)
        self.interpreter.value.write(param='rex',      file='rex.txt',      dir=dir, force=True)
        self.interpreter.value.write(param='local_tm', file='local_tm.txt', dir=dir, force=True)
        frqs = get_frequencies()
        for i in range(len(frqs)):
            comment = "This is the Rex value with units rad.s^-1 scaled to a magnetic field strength of %s MHz." % (frqs[i]/1e6)
            self.interpreter.value.write(param='rex', file='rex_%s.txt'%int(frqs[i]/1e6), dir=dir, scaling=(2.0*pi*frqs[i])**2, comment=comment, force=True)

        # Create the PyMOL macros.
        dir = self.write_results_dir + 'final' + sep + 'pymol'
        self.interpreter.pymol.macro_write(data_type='s2',        dir=dir, force=True)
        self.interpreter.pymol.macro_write(data_type='s2f',       dir=dir, force=True)
        self.interpreter.pymol.macro_write(data_type='s2s',       dir=dir, force=True)
        self.interpreter.pymol.macro_write(data_type='amp_fast',  dir=dir, force=True)
        self.interpreter.pymol.macro_write(data_type='amp_slow',  dir=dir, force=True)
        self.interpreter.pymol.macro_write(data_type='te',        dir=dir, force=True)
        self.interpreter.pymol.macro_write(data_type='tf',        dir=dir, force=True)
        self.interpreter.pymol.macro_write(data_type='ts',        dir=dir, force=True)
        self.interpreter.pymol.macro_write(data_type='time_fast', dir=dir, force=True)
        self.interpreter.pymol.macro_write(data_type='time_slow', dir=dir, force=True)
        self.interpreter.pymol.macro_write(data_type='rex',       dir=dir, force=True)

        # Create the Molmol macros.
        dir = self.write_results_dir + 'final' + sep + 'molmol'
        self.interpreter.molmol.macro_write(data_type='s2',        dir=dir, force=True)
        self.interpreter.molmol.macro_write(data_type='s2f',       dir=dir, force=True)
        self.interpreter.molmol.macro_write(data_type='s2s',       dir=dir, force=True)
        self.interpreter.molmol.macro_write(data_type='amp_fast',  dir=dir, force=True)
        self.interpreter.molmol.macro_write(data_type='amp_slow',  dir=dir, force=True)
        self.interpreter.molmol.macro_write(data_type='te',        dir=dir, force=True)
        self.interpreter.molmol.macro_write(data_type='tf',        dir=dir, force=True)
        self.interpreter.molmol.macro_write(data_type='ts',        dir=dir, force=True)
        self.interpreter.molmol.macro_write(data_type='time_fast', dir=dir, force=True)
        self.interpreter.molmol.macro_write(data_type='time_slow', dir=dir, force=True)
        self.interpreter.molmol.macro_write(data_type='rex',       dir=dir, force=True)

        # Create a diffusion tensor representation of the tensor, if a PDB file is present and the local tm global model has not been selected.
        if hasattr(cdp, 'structure') and hasattr(cdp, 'diff_tensor'):
            dir = self.write_results_dir + 'final'
            self.interpreter.structure.create_diff_tensor_pdb(file="tensor.pdb", dir=dir, force=True)



class Container:
    """Empty container for data storage."""
