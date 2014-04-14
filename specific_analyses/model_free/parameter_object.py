###############################################################################
#                                                                             #
# Copyright (C) 2007-2014 Edward d'Auvergne                                   #
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
"""The module for the Lipari-Szabo model-free parameter list object."""

# relax module imports.
from lib.physical_constants import N15_CSA
from pipe_control import relax_data
from specific_analyses.parameter_object import Param_list
from specific_analyses.model_free.parameters import conv_factor_rex, units_rex


class Model_free_params(Param_list):
    """The Lipari-Szabo model-free parameter list singleton."""

    # Class variable for storing the class instance (for the singleton design pattern).
    _instance = None

    def __init__(self):
        """Define all the parameters of the analysis."""

        # The object is already initialised.
        if self._initialised: return

        # Execute the base class __init__ method.
        Param_list.__init__(self)

        # Add the base data for the models.
        self._add('ri_data', scope='spin', desc=relax_data.return_data_desc('ri_data'), py_type=dict, err=False, sim=True)
        self._add('ri_data_err', scope='spin', desc=relax_data.return_data_desc('ri_data_err'), py_type=dict, err=False, sim=False)

        # Add the model variables.
        self._add_model_info(equation_flag=True)

        # Add up the global model parameters.
        self._add_diffusion_params()

        # Add up the spin model parameters.
        self._add('s2', scope='spin', default=0.8, desc='S2, the model-free generalised order parameter (S2 = S2f.S2s)', py_type=float, set='params', grace_string='\\qS\\v{0.4}\\z{0.71}2\\Q', err=True, sim=True)
        self._add('s2f', scope='spin', default=0.8, desc='S2f, the faster motion model-free generalised order parameter', py_type=float, set='params', grace_string='\\qS\\sf\\N\\h{-0.2}\\v{0.4}\\z{0.71}2\\Q', err=True, sim=True)
        self._add('s2s', scope='spin', default=0.8, desc='S2s, the slower motion model-free generalised order parameter', py_type=float, set='params', grace_string='\\qS\\ss\\N\\h{-0.2}\\v{0.4}\\z{0.71}2\\Q', err=True, sim=True)
        self._add('local_tm', scope='spin', default=10.0 * 1e-9, desc='The spin specific global correlation time (seconds)', py_type=float, set='params', grace_string='\\xt\\f{}\\sm', units='ns', err=True, sim=True)
        self._add('te', scope='spin', default=100.0 * 1e-12, desc='Single motion effective internal correlation time (seconds)', py_type=float, set='params', conv_factor=1e-12, grace_string='\\xt\\f{}\\se', units='ps', err=True, sim=True)
        self._add('tf', scope='spin', default=10.0 * 1e-12, desc='Faster motion effective internal correlation time (seconds)', py_type=float, set='params', conv_factor=1e-12, grace_string='\\xt\\f{}\\sf', units='ps', err=True, sim=True)
        self._add('ts', scope='spin', default=1000.0 * 1e-12, desc='Slower motion effective internal correlation time (seconds)', py_type=float, set='params', conv_factor=1e-12, grace_string='\\xt\\f{}\\ss', units='ps', err=True, sim=True)
        self._add('rex', scope='spin', default=0.0, desc='Chemical exchange relaxation (sigma_ex = Rex / omega**2)', py_type=float, set='params', conv_factor=conv_factor_rex, units=units_rex, grace_string='\\qR\\sex\\Q', err=True, sim=True)
        self._add_csa(default=N15_CSA, set='params', err=True, sim=True)

        # Add the minimisation data.
        self._add_min_data(min_stats_global=True, min_stats_spin=True)

        # Set up the user function documentation.
        self._set_uf_title("Model-free parameters")
        self._uf_param_table(label="table: model-free parameters", caption="Model-free parameters.")
        self._uf_param_table(label="table: model-free parameters and min stats", caption="Model-free parameters and minimisation statistics.", sets=['params', 'fixed', 'min'])
        self._uf_param_table(label="table: all model-free parameters", caption="Model-free parameters.", scope=None)
        self._uf_param_table(label="table: mf parameter value setting", caption="Model-free parameter value setting.", default=True)

        # Parameter setting documentation.
        for doc in self._uf_doc_loop(["table: model-free parameters", "table: mf parameter value setting"]):
            doc.add_paragraph("Setting a parameter value may have no effect depending on which model-free model is chosen.  For example if S2f values and S2s values are set but the data pipe corresponds to the model-free model 'm4' then because these data values are not parameters of the model they will have no effect.")
            doc.add_paragraph("Note that the Rex values are scaled quadratically with field strength and should be supplied as a field strength independent value.  Use the following formula to obtain the correct value:")
            doc.add_verbatim("    value = rex / (2.0 * pi * frequency) ** 2")
            doc.add_paragraph("where:")
            doc.add_list_element("rex is the chemical exchange value for the current frequency.")
            doc.add_list_element("frequency is the proton frequency corresponding to the data.")
