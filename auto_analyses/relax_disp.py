###############################################################################
#                                                                             #
# Copyright (C) 2013-2014 Edward d'Auvergne                                   #
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
"""The automatic relaxation dispersion protocol."""

# Python module imports.
from copy import deepcopy
from os import F_OK, access, getcwd, sep
import sys
from warnings import warn

# relax module imports.
from lib.errors import RelaxError, RelaxNoPipeError
from lib.text.sectioning import section, subsection, subtitle, title
from lib.warnings import RelaxWarning
from pipe_control.mol_res_spin import return_spin, spin_loop
from pipe_control.pipes import has_pipe
from prompt.interpreter import Interpreter
from specific_analyses.relax_disp.data import has_exponential_exp_type, has_cpmg_exp_type, has_fixed_time_exp_type, has_r1rho_exp_type, loop_frq
from specific_analyses.relax_disp.data import INTERPOLATE_DISP, INTERPOLATE_OFFSET, X_AXIS_DISP, X_AXIS_W_EFF, X_AXIS_THETA, Y_AXIS_R2_R1RHO, Y_AXIS_R2_EFF
from specific_analyses.relax_disp.variables import MODEL_B14, MODEL_B14_FULL, MODEL_CR72, MODEL_CR72_FULL, MODEL_DPL94, MODEL_IT99, MODEL_LIST_ANALYTIC, MODEL_LIST_R1RHO, MODEL_LIST_R1RHO_FULL, MODEL_LM63, MODEL_LM63_3SITE, MODEL_M61, MODEL_M61B, MODEL_MP05, MODEL_MMQ_CR72, MODEL_NS_CPMG_2SITE_3D, MODEL_NS_CPMG_2SITE_3D_FULL, MODEL_NS_CPMG_2SITE_EXPANDED, MODEL_NS_CPMG_2SITE_STAR, MODEL_NS_CPMG_2SITE_STAR_FULL, MODEL_NS_MMQ_2SITE, MODEL_NS_MMQ_3SITE, MODEL_NS_MMQ_3SITE_LINEAR, MODEL_NS_R1RHO_2SITE, MODEL_NS_R1RHO_3SITE, MODEL_NS_R1RHO_3SITE_LINEAR, MODEL_PARAMS, MODEL_R2EFF, MODEL_TAP03, MODEL_TP02, MODEL_TSMFK01
from status import Status; status = Status()


class Relax_disp:
    """The relaxation dispersion auto-analysis."""

    # Some class variables.
    opt_func_tol = 1e-25
    opt_max_iterations = int(1e7)

    def __init__(self, pipe_name=None, pipe_bundle=None, results_dir=None, models=[MODEL_R2EFF], grid_inc=11, mc_sim_num=500, exp_mc_sim_num=None, modsel='AIC', pre_run_dir=None, insignificance=0.0, numeric_only=False, mc_sim_all_models=False, eliminate=True, set_grid_r20=False):
        """Perform a full relaxation dispersion analysis for the given list of models.

        @keyword pipe_name:         The name of the data pipe containing all of the data for the analysis.
        @type pipe_name:            str
        @keyword pipe_bundle:       The data pipe bundle to associate all spawned data pipes with.
        @type pipe_bundle:          str
        @keyword results_dir:       The directory where results files are saved.
        @type results_dir:          str
        @keyword models:            The list of relaxation dispersion models to optimise.
        @type models:               list of str
        @keyword grid_inc:          Number of grid search increments.  If set to None, then the grid search will be turned off and the default parameter values will be used instead.
        @type grid_inc:             int or None
        @keyword mc_sim_num:        The number of Monte Carlo simulations to be used for error analysis at the end of the analysis.
        @type mc_sim_num:           int
        @keyword exp_mc_sim_num:    The number of Monte Carlo simulations for the error analysis in the 'R2eff' model when exponential curves are fitted.  This defaults to the value of the mc_sim_num argument when not given.  For the 2-point fixed-time calculation for the 'R2eff' model, this argument is ignored.
        @type exp_mc_sim_num:       int or None
        @type
        @keyword modsel:            The model selection technique to use in the analysis to determine which model is the best for each spin cluster.  This can currently be one of 'AIC', 'AICc', and 'BIC'.
        @type modsel:               str
        @keyword pre_run_dir:       The optional directory containing the dispersion auto-analysis results from a previous run.  The optimised parameters from these previous results will be used as the starting point for optimisation rather than performing a grid search.  This is essential for when large spin clusters are specified, as a grid search becomes prohibitively expensive with clusters of three or more spins.  At some point a RelaxError will occur because the grid search is impossibly large.  For the cluster specific parameters, i.e. the populations of the states and the exchange parameters, an average value will be used as the starting point.  For all other parameters, the R20 values for each spin and magnetic field, as well as the parameters related to the chemical shift difference dw, the optimised values of the previous run will be directly copied.
        @type pre_run_dir:          None or str
        @keyword insignificance:    The R2eff/R1rho value in rad/s by which to judge insignificance.  If the maximum difference between two points on all dispersion curves for a spin is less than this value, that spin will be deselected.  This does not affect the 'No Rex' model.  Set this value to 0.0 to use all data.  The value will be passed on to the relax_disp.insignificance user function.
        @type insignificance:       float
        @keyword numeric_only:      The class of models to use in the model selection.  The default of False allows all dispersion models to be used in the analysis (no exchange, the analytic models and the numeric models).  The value of True will activate a pure numeric solution - the analytic models will be optimised, as they are very useful for replacing the grid search for the numeric models, but the final model selection will not include them.
        @type numeric_only:         bool
        @keyword mc_sim_all_models: A flag which if True will cause Monte Carlo simulations to be performed for each individual model.  Otherwise Monte Carlo simulations will be reserved for the final model.
        @type mc_sim_all_models:    bool
        @keyword eliminate:         A flag which if True will enable the elimination of failed models and failed Monte Carlo simulations through the eliminate user function.
        @type eliminate:            bool
        @keyword set_grid_r20:      A flag which if True will set the grid R20 values from the minimum R2eff values through the r20_from_min_r2eff user function. This will speed up the grid search with a factor GRID_INC^(Nr_spec_freq). For a CPMG experiment with two fields and standard GRID_INC=21, the speed-up is a factor 441.
        @type set_grid_r20:         bool
        """

        # Printout.
        title(file=sys.stdout, text="Relaxation dispersion auto-analysis", prespace=4)

        # Execution lock.
        status.exec_lock.acquire(pipe_bundle, mode='auto-analysis')

        # Set up the analysis status object.
        status.init_auto_analysis(pipe_bundle, type='relax_disp')
        status.current_analysis = pipe_bundle

        # Store the args.
        self.pipe_name = pipe_name
        self.pipe_bundle = pipe_bundle
        self.results_dir = results_dir
        self.models = models
        self.grid_inc = grid_inc
        self.mc_sim_num = mc_sim_num
        self.exp_mc_sim_num = exp_mc_sim_num
        self.modsel = modsel
        self.pre_run_dir = pre_run_dir
        self.insignificance = insignificance
        self.set_grid_r20 = set_grid_r20
        self.numeric_only = numeric_only
        self.mc_sim_all_models = mc_sim_all_models
        self.eliminate = eliminate

        # No results directory, so default to the current directory.
        if not self.results_dir:
            self.results_dir = getcwd()

        # Data checks.
        self.check_vars()

        # Load the interpreter.
        self.interpreter = Interpreter(show_script=False, raise_relax_error=True)
        self.interpreter.populate_self()
        self.interpreter.on(verbose=False)

        # Execute.
        try:
            self.run()

        # Finish and unlock execution.
        finally:
            status.auto_analysis[self.pipe_bundle].fin = True
            status.current_analysis = None
            status.exec_lock.release()


    def is_model_for_selection(self, model=None):
        """Determine if the model should be used for model selection.

        @keyword model: The model to check.
        @type model:    str
        @return:        True if the model should be included in the model selection list, False if not.
        @rtype:         bool
        """

        # Skip the 'R2eff' base model.
        if model == 'R2eff':
            return False

        # Do not use the analytic models.
        if self.numeric_only and model in MODEL_LIST_ANALYTIC:
            return False

        # All models allowed.
        return True


    def check_vars(self):
        """Check that the user has set the variables correctly."""

        # Printout.
        section(file=sys.stdout, text="Variable checking", prespace=2)

        # The pipe name.
        if not has_pipe(self.pipe_name):
            raise RelaxNoPipeError(self.pipe_name)

        # Check the model selection.
        allowed = ['AIC', 'AICc', 'BIC']
        if self.modsel not in allowed:
            raise RelaxError("The model selection technique '%s' is not in the allowed list of %s." % (self.modsel, allowed))

        # Some warning for the user if the pure numeric solution is selected.
        if self.numeric_only:
            # Loop over all models.
            for model in self.models:
                # Skip the models used for nesting.
                if model in [MODEL_CR72, MODEL_MMQ_CR72, MODEL_MP05]:
                    continue

                # Warnings for all other analytic models.
                if model in MODEL_LIST_ANALYTIC:
                    warn(RelaxWarning("The analytic model '%s' will be optimised but will not be used in any way in this numeric model only auto-analysis." % model))

        # Printout.
        print("The dispersion auto-analysis variables are OK.")


    def error_analysis(self):
        """Perform an error analysis of the peak intensities for each field strength separately."""

        # Printout.
        section(file=sys.stdout, text="Error analysis", prespace=2)

        # Check if intensity errors have already been calculated by the user.
        precalc = True
        for spin in spin_loop(skip_desel=True):
            # No structure.
            if not hasattr(spin, 'peak_intensity_err'):
                precalc = False
                break

            # Determine if a spectrum ID is missing from the list.
            for id in cdp.spectrum_ids:
                if id not in spin.peak_intensity_err:
                    precalc = False
                    break

        # Skip.
        if precalc:
            print("Skipping the error analysis as it has already been performed.")
            return

        # Loop over the spectrometer frequencies.
        for frq in loop_frq():
            # Generate a list of spectrum IDs matching the frequency.
            ids = []
            for id in cdp.spectrum_ids:
                # Check that the spectrometer frequency matches.
                match_frq = True
                if frq != None and cdp.spectrometer_frq[id] != frq:
                    match_frq = False

                # Add the ID.
                if match_frq:
                    ids.append(id)

            # Run the error analysis on the subset.
            self.interpreter.spectrum.error_analysis(subset=ids)


    def name_pipe(self, prefix):
        """Generate a unique name for the data pipe.

        @param prefix:  The prefix of the data pipe name.
        @type prefix:   str
        """

        # The unique pipe name.
        name = "%s - %s" % (prefix, self.pipe_bundle)

        # Return the name.
        return name


    def nesting(self, model=None):
        """Support for model nesting.

        If model nesting is detected, the optimised parameters from the simpler model will be used for the more complex model.  The method will then signal if the nesting condition is met for the model, allowing the grid search to be skipped.


        @keyword model: The model to be optimised.
        @type model:    str
        @return:        True if the model is the more complex model in a nested pair and the parameters of the simpler model have been copied.  False otherwise.
        @rtype:         bool
        """

        # Printout. 
        subsection(file=sys.stdout, text="Nesting and model equivalence checks", prespace=1)

        # The simpler model.
        nested_pipe = None
        if model == MODEL_LM63_3SITE and MODEL_LM63 in self.models:
            nested_pipe = self.name_pipe(MODEL_LM63)
        if model == MODEL_CR72_FULL and MODEL_CR72 in self.models:
            nested_pipe = self.name_pipe(MODEL_CR72)
        if model == MODEL_MMQ_CR72 and MODEL_CR72 in self.models:
            nested_pipe = self.name_pipe(MODEL_CR72)
        if model == MODEL_NS_CPMG_2SITE_3D_FULL and MODEL_NS_CPMG_2SITE_3D in self.models:
            nested_pipe = self.name_pipe(MODEL_NS_CPMG_2SITE_3D)
        if model == MODEL_NS_CPMG_2SITE_STAR_FULL and MODEL_NS_CPMG_2SITE_STAR in self.models:
            nested_pipe = self.name_pipe(MODEL_NS_CPMG_2SITE_STAR)
        if model == MODEL_NS_MMQ_3SITE_LINEAR and MODEL_NS_MMQ_2SITE in self.models:
            nested_pipe = self.name_pipe(MODEL_NS_MMQ_2SITE)
        if model == MODEL_NS_MMQ_3SITE:
            if MODEL_NS_MMQ_3SITE_LINEAR in self.models:
                nested_pipe = self.name_pipe(MODEL_NS_MMQ_3SITE_LINEAR)
            elif MODEL_NS_MMQ_2SITE in self.models:
                nested_pipe = self.name_pipe(MODEL_NS_MMQ_2SITE)
        if model == MODEL_NS_R1RHO_3SITE_LINEAR and MODEL_NS_R1RHO_2SITE in self.models:
            nested_pipe = self.name_pipe(MODEL_NS_R1RHO_2SITE)
        if model == MODEL_NS_R1RHO_3SITE:
            if MODEL_NS_R1RHO_3SITE_LINEAR in self.models:
                nested_pipe = self.name_pipe(MODEL_NS_R1RHO_3SITE_LINEAR)
            elif MODEL_NS_R1RHO_2SITE in self.models:
                nested_pipe = self.name_pipe(MODEL_NS_R1RHO_2SITE)


        # Using the analytic solution.
        analytic = False
        if model in [MODEL_NS_CPMG_2SITE_3D, MODEL_NS_CPMG_2SITE_EXPANDED, MODEL_NS_CPMG_2SITE_STAR] and MODEL_CR72 in self.models:
            nested_pipe = self.name_pipe(MODEL_CR72)
            analytic = True
        elif model == MODEL_NS_MMQ_2SITE and MODEL_MMQ_CR72 in self.models:
            nested_pipe = self.name_pipe(MODEL_MMQ_CR72)
            analytic = True
        if model == MODEL_NS_R1RHO_2SITE and MODEL_MP05 in self.models:
            nested_pipe = self.name_pipe(MODEL_MP05)
            analytic = True

        # No nesting.
        if not nested_pipe:
            print("No model nesting or model equivalence detected.")
            return False

        # Printout.
        if analytic:
            print("Model equivalence detected, copying the optimised parameters from the analytic '%s' model rather than performing a grid search." % nested_pipe)
        else:
            print("Model nesting detected, copying the optimised parameters from the '%s' model rather than performing a grid search." % nested_pipe)

        # Loop over the spins to copy the parameters.
        for spin, spin_id in spin_loop(return_id=True, skip_desel=True):
            # Get the nested spin.
            nested_spin = return_spin(spin_id=spin_id, pipe=nested_pipe)

            # The R20 parameters.
            if hasattr(nested_spin, 'r2'):
                if model in [MODEL_CR72_FULL, MODEL_NS_CPMG_2SITE_3D_FULL, MODEL_NS_CPMG_2SITE_STAR_FULL]:
                    setattr(spin, 'r2a', deepcopy(nested_spin.r2))
                    setattr(spin, 'r2b', deepcopy(nested_spin.r2))
                else:
                    setattr(spin, 'r2', deepcopy(nested_spin.r2))

            # The LM63 3-site model parameters.
            if model == MODEL_LM63_3SITE:
                setattr(spin, 'phi_ex_B', deepcopy(nested_spin.phi_ex))
                setattr(spin, 'phi_ex_C', deepcopy(nested_spin.phi_ex))
                setattr(spin, 'kB', deepcopy(nested_spin.kex))
                setattr(spin, 'kC', deepcopy(nested_spin.kex))

            # All other spin parameters.
            for param in spin.params:
                if param in ['r2', 'r2a', 'r2b']:
                    continue

                # The parameter does not exist.
                if not hasattr(nested_spin, param):
                    continue

                # Skip the LM63 3-site model parameters
                if model == MODEL_LM63_3SITE and param in ['phi_ex', 'kex']:
                    continue

                # Copy the parameter.
                setattr(spin, param, deepcopy(getattr(nested_spin, param)))

        # Nesting.
        return True


    def optimise(self, model=None):
        """Optimise the model, taking model nesting into account.

        @keyword model: The model to be optimised.
        @type model:    str
        """

        # Printout. 
        section(file=sys.stdout, text="Optimisation", prespace=2)

        # Deselect insignificant spins.
        if model not in ['R2eff', 'No Rex']:
            self.interpreter.relax_disp.insignificance(level=self.insignificance)

        # Speed-up grid-search by using minium R2eff value.
        if self.set_grid_r20 and model != MODEL_R2EFF:
            self.interpreter.relax_disp.r20_from_min_r2eff(force=True)

        # Use pre-run results as the optimisation starting point.
        if self.pre_run_dir:
            self.pre_run_parameters(model=model)

        # Otherwise use the normal nesting check and grid search if not nested.
        else:
            # Nested model simplification.
            nested = self.nesting(model=model)

            # Otherwise use a grid search of default values to start optimisation with.
            if not nested:
                # Grid search.
                if self.grid_inc:
                    self.interpreter.minimise.grid_search(inc=self.grid_inc)

                # Default values.
                else:
                    for param in MODEL_PARAMS[model]:
                        self.interpreter.value.set(param=param, index=None)

        # Minimise.
        self.interpreter.minimise.execute('simplex', func_tol=self.opt_func_tol, max_iter=self.opt_max_iterations, constraints=True)

        # Model elimination.
        if self.eliminate:
            self.interpreter.eliminate()

        # Monte Carlo simulations.
        if self.mc_sim_all_models or len(self.models) < 2 or model == 'R2eff':
            if model == 'R2eff' and self.exp_mc_sim_num != None:
                self.interpreter.monte_carlo.setup(number=self.exp_mc_sim_num)
            else:
                self.interpreter.monte_carlo.setup(number=self.mc_sim_num)
            self.interpreter.monte_carlo.create_data()
            self.interpreter.monte_carlo.initial_values()
            self.interpreter.minimise.execute('simplex', func_tol=self.opt_func_tol, max_iter=self.opt_max_iterations, constraints=True)
            if self.eliminate:
                self.interpreter.eliminate()
            self.interpreter.monte_carlo.error_analysis()


    def pre_run_parameters(self, model=None):
        """Copy parameters from an earlier analysis.

        @keyword model: The model to be optimised.
        @type model:    str
        """

        # Printout.
        subsection(file=sys.stdout, text="Pre-run parameters", prespace=1)

        # The data pipe name.
        pipe_name = self.name_pipe('pre')

        # Create a temporary data pipe for the previous run.
        self.interpreter.pipe.create(pipe_name=pipe_name, pipe_type='relax_disp')

        # Load the previous results.
        path = self.pre_run_dir + sep + model
        self.interpreter.results.read(file='results', dir=path)

        # Copy the parameters.
        self.interpreter.relax_disp.parameter_copy(pipe_from=pipe_name, pipe_to=self.name_pipe(model))

        # Finally, switch back to the original data pipe and delete the temporary one.
        self.interpreter.pipe.switch(pipe_name=self.name_pipe(model))
        self.interpreter.pipe.delete(pipe_name=pipe_name)


    def run(self):
        """Execute the auto-analysis."""

        # Peak intensity error analysis.
        if MODEL_R2EFF in self.models:
            self.error_analysis()

        # Loop over the models.
        self.model_pipes = []
        for model in self.models:
            # Printout.
            subtitle(file=sys.stdout, text="The '%s' model" % model, prespace=3)

            # The results directory path.
            path = self.results_dir+sep+model

            # The name of the data pipe for the model.
            model_pipe = self.name_pipe(model)
            if self.is_model_for_selection(model):
                self.model_pipes.append(model_pipe)

            # Check that results do not already exist - i.e. a previous run was interrupted.
            path1 = path + sep + 'results'
            path2 = path1 + '.bz2'
            path3 = path1 + '.gz'
            if access(path1, F_OK) or access(path2, F_OK) or access(path2, F_OK):
                # Printout.
                print("Detected the presence of results files for the '%s' model - loading these instead of performing optimisation for a second time." % model)

                # Create a data pipe and switch to it.
                self.interpreter.pipe.create(pipe_name=model_pipe, pipe_type='relax_disp', bundle=self.pipe_bundle)
                self.interpreter.pipe.switch(model_pipe)

                # Load the results.
                self.interpreter.results.read(file='results', dir=path)

                # Jump to the next model.
                continue

            # Create the data pipe by copying the base pipe, then switching to it.
            self.interpreter.pipe.copy(pipe_from=self.pipe_name, pipe_to=model_pipe, bundle_to=self.pipe_bundle)
            self.interpreter.pipe.switch(model_pipe)

            # Select the model.
            self.interpreter.relax_disp.select_model(model)

            # Copy the R2eff values from the R2eff model data pipe.
            if model != MODEL_R2EFF and MODEL_R2EFF in self.models:
                self.interpreter.value.copy(pipe_from=self.name_pipe(MODEL_R2EFF), pipe_to=model_pipe, param='r2eff')

            # Calculate the R2eff values for the fixed relaxation time period data types.
            if model == MODEL_R2EFF and not has_exponential_exp_type():
                self.interpreter.minimise.calculate()

            # Optimise the model.
            else:
                self.optimise(model=model)

            # Write out the results.
            self.write_results(path=path, model=model)

        # The final model selection data pipe.
        if len(self.models) >= 2:
            # Printout.
            section(file=sys.stdout, text="Final results", prespace=2)

            # Perform model selection.
            self.interpreter.model_selection(method=self.modsel, modsel_pipe=self.name_pipe('final'), bundle=self.pipe_bundle, pipes=self.model_pipes)

            # Final Monte Carlo simulations only.
            if not self.mc_sim_all_models:
                self.interpreter.monte_carlo.setup(number=self.mc_sim_num)
                self.interpreter.monte_carlo.create_data()
                self.interpreter.monte_carlo.initial_values()
                self.interpreter.minimise.execute('simplex', func_tol=self.opt_func_tol, max_iter=self.opt_max_iterations, constraints=True)
                if self.eliminate:
                    self.interpreter.eliminate()
                self.interpreter.monte_carlo.error_analysis()

            # Writing out the final results.
            self.write_results(path=self.results_dir+sep+'final')

        # No model selection.
        else:
            warn(RelaxWarning("Model selection in the dispersion auto-analysis has been skipped as only %s models have been optimised." % len(self.model_pipes)))

        # Finally save the program state.
        self.interpreter.state.save(state='final_state', dir=self.results_dir, force=True)


    def write_results(self, path=None, model=None):
        """Create a set of results, text and Grace files for the current data pipe.

        @keyword path:  The directory to place the files into.
        @type path:     str
        """

        # Printout.
        section(file=sys.stdout, text="Results writing", prespace=2)

        # Exponential curves.
        if model == 'R2eff' and has_exponential_exp_type():
            self.interpreter.relax_disp.plot_exp_curves(file='intensities.agr', dir=path, force=True)    # Average peak intensities.
            self.interpreter.relax_disp.plot_exp_curves(file='intensities_norm.agr', dir=path, force=True, norm=True)    # Average peak intensities (normalised).

        # Dispersion curves.
        self.interpreter.relax_disp.plot_disp_curves(dir=path, force=True)
        self.interpreter.relax_disp.write_disp_curves(dir=path, force=True)

        # Plot specific R1rho graphs.
        if has_r1rho_exp_type() and model in [None] + MODEL_LIST_R1RHO_FULL:
            self.interpreter.relax_disp.plot_disp_curves(dir=path, x_axis=X_AXIS_THETA, force=True)
            self.interpreter.relax_disp.plot_disp_curves(dir=path, y_axis=Y_AXIS_R2_R1RHO, x_axis=X_AXIS_W_EFF, force=True)
            self.interpreter.relax_disp.plot_disp_curves(dir=path, y_axis=Y_AXIS_R2_EFF, x_axis=X_AXIS_THETA, interpolate=INTERPOLATE_OFFSET, force=True)

        # The selected models for the final run.
        if model == None:
            self.interpreter.value.write(param='model', file='model.out', dir=path, force=True)

        # The R2eff parameter.
        if model == 'R2eff':
            self.interpreter.value.write(param='r2eff', file='r2eff.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='r2eff', file='r2eff.agr', dir=path, force=True)

        # The I0 parameter.
        if model == 'R2eff' and has_exponential_exp_type():
            self.interpreter.value.write(param='i0', file='i0.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='i0', file='i0.agr', dir=path, force=True)

        # The calculation of theta and w_eff parameter in R1rho experiments.
        if model in MODEL_LIST_R1RHO_FULL and has_r1rho_exp_type():
            self.interpreter.value.write(param='theta', file='theta.out', dir=path, force=True)
            self.interpreter.value.write(param='w_eff', file='w_eff.out', dir=path, force=True)

        # The R20 parameter.
        if has_cpmg_exp_type() and model in [None, MODEL_LM63, MODEL_B14, MODEL_CR72, MODEL_IT99, MODEL_M61, MODEL_DPL94, MODEL_M61B, MODEL_MMQ_CR72, MODEL_NS_CPMG_2SITE_3D, MODEL_NS_CPMG_2SITE_STAR, MODEL_NS_CPMG_2SITE_EXPANDED, MODEL_NS_MMQ_2SITE, MODEL_NS_MMQ_3SITE, MODEL_NS_MMQ_3SITE_LINEAR]:
            self.interpreter.value.write(param='r2', file='r20.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='r2', file='r20.agr', dir=path, force=True)

        # The R20A and R20B parameters.
        if has_cpmg_exp_type() and model in [None, MODEL_B14_FULL, MODEL_CR72_FULL, MODEL_NS_CPMG_2SITE_3D_FULL, MODEL_NS_CPMG_2SITE_STAR_FULL]:
            self.interpreter.value.write(param='r2a', file='r20a.out', dir=path, force=True)
            self.interpreter.value.write(param='r2b', file='r20b.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='r2a', file='r20a.agr', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='r2b', file='r20b.agr', dir=path, force=True)

        # The R1rho0 parameter.
        if has_r1rho_exp_type() and model in [None] + MODEL_LIST_R1RHO:
            self.interpreter.value.write(param='r2', file='r1rho0.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='r2', file='r1rho0.agr', dir=path, force=True)

        # The pA, pB, and pC parameters.
        if model in [None, MODEL_B14, MODEL_B14_FULL, MODEL_CR72, MODEL_CR72_FULL, MODEL_IT99, MODEL_M61B, MODEL_MMQ_CR72, MODEL_NS_CPMG_2SITE_3D, MODEL_NS_CPMG_2SITE_3D_FULL, MODEL_NS_CPMG_2SITE_STAR, MODEL_NS_CPMG_2SITE_STAR_FULL, MODEL_NS_CPMG_2SITE_EXPANDED, MODEL_NS_MMQ_2SITE, MODEL_NS_R1RHO_2SITE, MODEL_NS_R1RHO_3SITE, MODEL_NS_R1RHO_3SITE_LINEAR, MODEL_TP02, MODEL_TAP03, MODEL_MP05, MODEL_NS_MMQ_3SITE, MODEL_NS_MMQ_3SITE_LINEAR]:
            self.interpreter.value.write(param='pA', file='pA.out', dir=path, force=True)
            self.interpreter.value.write(param='pB', file='pB.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='pA', file='pA.agr', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='pB', file='pB.agr', dir=path, force=True)
        if model in [MODEL_NS_MMQ_3SITE, MODEL_NS_MMQ_3SITE_LINEAR, MODEL_NS_R1RHO_3SITE, MODEL_NS_R1RHO_3SITE_LINEAR]:
            self.interpreter.value.write(param='pC', file='pC.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='pC', file='pC.agr', dir=path, force=True)

        # The Phi_ex parameter.
        if model in [None, MODEL_LM63, MODEL_M61, MODEL_DPL94]:
            self.interpreter.value.write(param='phi_ex', file='phi_ex.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='phi_ex', file='phi_ex.agr', dir=path, force=True)

        # The Phi_ex_B nd Phi_ex_C parameters.
        if model in [None, MODEL_LM63_3SITE]:
            self.interpreter.value.write(param='phi_ex_B', file='phi_ex_B.out', dir=path, force=True)
            self.interpreter.value.write(param='phi_ex_C', file='phi_ex_C.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='phi_ex_B', file='phi_ex_B.agr', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='phi_ex_C', file='phi_ex_C.agr', dir=path, force=True)

        # The dw parameter.
        if model in [None, MODEL_B14, MODEL_B14_FULL, MODEL_CR72, MODEL_CR72_FULL, MODEL_IT99, MODEL_M61B, MODEL_MMQ_CR72, MODEL_NS_CPMG_2SITE_3D, MODEL_NS_CPMG_2SITE_3D_FULL, MODEL_NS_CPMG_2SITE_STAR, MODEL_NS_CPMG_2SITE_STAR_FULL, MODEL_NS_CPMG_2SITE_EXPANDED, MODEL_NS_MMQ_2SITE, MODEL_NS_R1RHO_2SITE, MODEL_TP02, MODEL_TAP03, MODEL_MP05, MODEL_TSMFK01]:
            self.interpreter.value.write(param='dw', file='dw.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='dw', file='dw.agr', dir=path, force=True)
        if model in [MODEL_NS_MMQ_3SITE, MODEL_NS_MMQ_3SITE_LINEAR, MODEL_NS_R1RHO_3SITE, MODEL_NS_R1RHO_3SITE_LINEAR]:
            self.interpreter.value.write(param='dw_AB', file='dw_AB.out', dir=path, force=True)
            self.interpreter.value.write(param='dw_BC', file='dw_BC.out', dir=path, force=True)
            self.interpreter.value.write(param='dw_AC', file='dw_AC.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='dw_AB', file='dw_AB.agr', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='dw_BC', file='dw_BC.agr', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='dw_AC', file='dw_AC.agr', dir=path, force=True)

        # The dwH parameter.
        if model in [None, MODEL_MMQ_CR72, MODEL_NS_MMQ_2SITE]:
            self.interpreter.value.write(param='dwH', file='dwH.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='dwH', file='dwH.agr', dir=path, force=True)
        if model in [MODEL_NS_MMQ_3SITE, MODEL_NS_MMQ_3SITE_LINEAR]:
            self.interpreter.value.write(param='dwH_AB', file='dwH_AB.out', dir=path, force=True)
            self.interpreter.value.write(param='dwH_BC', file='dwH_BC.out', dir=path, force=True)
            self.interpreter.value.write(param='dwH_AC', file='dwH_AC.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='dwH_AB', file='dwH_AB.agr', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='dwH_BC', file='dwH_BC.agr', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='dwH_AC', file='dwH_AC.agr', dir=path, force=True)

        # The k_AB, kex and tex parameters.
        if model in [None, MODEL_LM63, MODEL_B14, MODEL_B14_FULL, MODEL_CR72, MODEL_CR72_FULL, MODEL_IT99, MODEL_M61, MODEL_DPL94, MODEL_M61B, MODEL_MMQ_CR72, MODEL_NS_CPMG_2SITE_3D, MODEL_NS_CPMG_2SITE_3D_FULL, MODEL_NS_CPMG_2SITE_STAR, MODEL_NS_CPMG_2SITE_STAR_FULL, MODEL_NS_CPMG_2SITE_EXPANDED, MODEL_NS_MMQ_2SITE, MODEL_NS_R1RHO_2SITE, MODEL_TP02, MODEL_TAP03, MODEL_MP05]:
            self.interpreter.value.write(param='k_AB', file='k_AB.out', dir=path, force=True)
            self.interpreter.value.write(param='kex', file='kex.out', dir=path, force=True)
            self.interpreter.value.write(param='tex', file='tex.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='k_AB', file='k_AB.agr', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='kex', file='kex.agr', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='tex', file='tex.agr', dir=path, force=True)
        if model in [MODEL_NS_MMQ_3SITE, MODEL_NS_MMQ_3SITE_LINEAR, MODEL_NS_R1RHO_3SITE, MODEL_NS_R1RHO_3SITE_LINEAR]:
            self.interpreter.value.write(param='kex_AB', file='kex_AB.out', dir=path, force=True)
            self.interpreter.value.write(param='kex_BC', file='kex_BC.out', dir=path, force=True)
            self.interpreter.value.write(param='kex_AC', file='kex_AC.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='kex_AB', file='kex_AB.agr', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='kex_BC', file='kex_BC.agr', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='kex_AC', file='kex_AC.agr', dir=path, force=True)

        # The k_AB parameter.
        if model in [None, MODEL_TSMFK01]:
            self.interpreter.value.write(param='k_AB', file='k_AB.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='k_AB', file='k_AB.agr', dir=path, force=True)

        # The kB and kC parameters.
        if model in [None, MODEL_LM63_3SITE]:
            self.interpreter.value.write(param='kB', file='kB.out', dir=path, force=True)
            self.interpreter.value.write(param='kC', file='kC.out', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='kB', file='kB.agr', dir=path, force=True)
            self.interpreter.grace.write(x_data_type='res_num', y_data_type='kC', file='kC.agr', dir=path, force=True)

        # Minimisation statistics.
        if not (model == 'R2eff' and has_fixed_time_exp_type()):
            self.interpreter.value.write(param='chi2', file='chi2.out', dir=path, force=True)
            self.interpreter.grace.write(y_data_type='chi2', file='chi2.agr', dir=path, force=True)

        # Finally save the results.  This is last to allow the continuation of an interrupted analysis while ensuring that all results files have been created.
        self.interpreter.results.write(file='results', dir=path, force=True)

