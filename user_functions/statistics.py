###############################################################################
#                                                                             #
# Copyright (C) 2015 Edward d'Auvergne                                        #
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
"""The statistics user function definitions."""

# relax module imports.
from graphics import WIZARD_IMAGE_PATH
from pipe_control.statistics import aic, model_statistics
from user_functions.data import Uf_info; uf_info = Uf_info()
from user_functions.objects import Desc_container


# The user function class.
uf_class = uf_info.add_class('statistics')
uf_class.title = "Class containing the statistics related functions."
uf_class.menu_text = "&statistics"
uf_class.gui_icon = "oxygen.actions.office-chart-pie"


# The statistics.aic user function.
uf = uf_info.add_uf('statistics.aic')
uf.title = "Calculate and store Akaike's Information Criterion (AIC) for each model."
uf.title_short = "Calculate AIC values."
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("This will perform a calculation to obtain the chi-squared statistic for the current parameter values for each model, count the number of parameters per model and calculate Akaike's Information Criterion (AIC) using the formula AIC = chi2 + 2k.  The AIC values, chi-squared values, and number of parameters will be stored in the appropriate location for the model in the relax data store.")
uf.backend = aic
uf.menu_text = "&aic"
uf.gui_icon = "relax.discrepancy_curve"
uf.wizard_apply_button = False
uf.wizard_size = (700, 400)
uf.wizard_image = WIZARD_IMAGE_PATH + 'statistics.png'


# The statistics.model user function.
uf = uf_info.add_uf('statistics.model')
uf.title = "Calculate and store the model statistics."
uf.title_short = "Model statistics."
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("This will perform a back-calculation to obtain the chi-squared statistic for the current parameter values, count the number of parameters and data points per model, and place all the values in the relax data store.")
uf.backend = model_statistics
uf.menu_text = "&model"
uf.gui_icon = "oxygen.categories.applications-education"
uf.wizard_apply_button = False
uf.wizard_size = (700, 400)
uf.wizard_image = WIZARD_IMAGE_PATH + 'statistics.png'
