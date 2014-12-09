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
"""The grace user function definitions for controlling the Grace data viewing software."""

# Python module imports.
import dep_check
if dep_check.wx_module:
    from wx import FD_OPEN, FD_SAVE
else:
    FD_OPEN = -1
    FD_SAVE = -1

# relax module imports.
from graphics import WIZARD_IMAGE_PATH
from pipe_control import grace
from specific_analyses.consistency_tests.parameter_object import Consistency_tests_params; consistency_test_params = Consistency_tests_params()
from specific_analyses.jw_mapping.parameter_object import Jw_mapping_params; jw_mapping_params = Jw_mapping_params()
from specific_analyses.model_free.parameter_object import Model_free_params; model_free_params = Model_free_params()
from specific_analyses.noe.parameter_object import Noe_params; noe_params = Noe_params()
from specific_analyses.relax_disp.parameter_object import Relax_disp_params; relax_disp_params = Relax_disp_params()
from specific_analyses.relax_fit.parameter_object import Relax_fit_params; relax_fit_params = Relax_fit_params()
from user_functions.data import Uf_info; uf_info = Uf_info()
from user_functions.objects import Desc_container
from user_functions.wildcards import WILDCARD_GRACE_ALL


# The user function class.
uf_class = uf_info.add_class('grace')
uf_class.title = "Class for interfacing with Grace."
uf_class.menu_text = "&grace"
uf_class.gui_icon = "relax.grace_icon"


# The grace.view user function.
uf = uf_info.add_uf('grace.view')
uf.title = "Visualise the file within Grace."
uf.title_short = "Grace execution."
uf.add_keyarg(
    name = "file",
    py_type = "str",
    arg_type = "file sel",
    desc_short = "file name",
    desc = "The name of the file.",
    wiz_filesel_wildcard = WILDCARD_GRACE_ALL,
    wiz_filesel_style = FD_OPEN
)
uf.add_keyarg(
    name = "dir",
    default = "grace",
    py_type = "str",
    arg_type = "dir",
    desc_short = "directory name",
    desc = "The directory name.",
    can_be_none = True
)
uf.add_keyarg(
    name = "grace_exe",
    default = "xmgrace",
    py_type = "str",
    arg_type = "file sel",
    desc_short = "Grace executable file",
    desc = "The Grace executable file.",
    wiz_filesel_style = FD_OPEN,
    wiz_filesel_preview = False
)
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("This can be used to view the specified Grace '*.agr' file by opening it with the Grace program.")
# Prompt examples.
uf.desc.append(Desc_container("Prompt examples"))
uf.desc[-1].add_paragraph("To view the file 's2.agr' in the directory 'grace', type:")
uf.desc[-1].add_prompt("relax> grace.view(file='s2.agr')")
uf.desc[-1].add_prompt("relax> grace.view(file='s2.agr', dir='grace')")
uf.backend = grace.view
uf.menu_text = "&view"
uf.gui_icon = "relax.grace_icon"
uf.wizard_size = (900, 500)
uf.wizard_image = WIZARD_IMAGE_PATH + 'grace.png'


# The grace.write user function.
uf = uf_info.add_uf('grace.write')
uf.title = "Create a grace '.agr' file to visualise the 2D data."
uf.title_short = "Grace file creation."
uf.add_keyarg(
    name = "x_data_type",
    default = "res_num",
    py_type = "str",
    desc_short = "x data type",
    desc = "The data type for the X-axis (no regular expression is allowed).",
    wiz_element_type = 'combo',
    wiz_combo_iter = grace.get_data_types
)
uf.add_keyarg(
    name = "y_data_type",
    py_type = "str",
    desc_short = "y data type",
    desc = "The data type for the Y-axis (no regular expression is allowed).",
    wiz_element_type = 'combo',
    wiz_combo_iter = grace.get_data_types
)
uf.add_keyarg(
    name = "spin_id",
    py_type = "str",
    desc_short = "spin ID string",
    desc = "The spin ID string.",
    can_be_none = True
)
uf.add_keyarg(
    name = "plot_data",
    default = "value",
    py_type = "str",
    desc_short = "plot data",
    desc = "The data to use for the plot.",
    wiz_element_type = "combo",
    wiz_combo_choices = [
        "Values",
        "Errors",
        "Simulation values"
    ],
    wiz_combo_data = [
        "value",
        "error",
        "sims"
    ],
    wiz_read_only = True
)
uf.add_keyarg(
    name = "norm_type",
    default = "first",
    py_type = "str",
    desc_short = "normalisation point",
    desc = "How the graph should be normalised, if the norm flag is set.",
    wiz_element_type = "combo",
    wiz_combo_choices = [
        "First point normalisation",
        "Last point normalisation"
    ],
    wiz_combo_data = [
        "first",
        "last"
    ],
    wiz_read_only = True
)
uf.add_keyarg(
    name = "file",
    py_type = "str",
    arg_type = "file sel",
    desc_short = "file name",
    desc = "The name of the file.",
    wiz_filesel_wildcard = WILDCARD_GRACE_ALL,
    wiz_filesel_style = FD_SAVE
)
uf.add_keyarg(
    name = "dir",
    default = "grace",
    py_type = "str",
    arg_type = "dir",
    desc_short = "directory name",
    desc = "The directory name.",
    can_be_none = True
)
uf.add_keyarg(
    name = "force",
    default = False,
    py_type = "bool",
    desc_short = "force flag",
    desc = "A flag which, if set to True, will cause the file to be overwritten."
)
uf.add_keyarg(
    name = "norm",
    default = False,
    py_type = "bool",
    desc_short = "normalisation flag",
    desc = "A flag which, if set to True, will cause all graphs to be normalised to 1.  This is for the normalisation of series type data.  The point for normalisation is set with the norm_type argument."
)
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("This is designed to be as flexible as possible so that any combination of data can be plotted.  The output is in the format of a Grace plot (also known as ACE/gr, Xmgr, and xmgrace) which only supports two dimensional plots.  Three types of information can be used to create various types of plot.  These include the x-axis and y-axis data types, the spin ID string, and the type of data plot.")
uf.desc[-1].add_paragraph("The x-axis and y-axis data types should be plain strings, regular expression is not allowed.  The two axes of the Grace plot can be any of the data types listed in the tables below.  The only limitation is that the data must belong to the same data pipe.")
uf.desc[-1].add_paragraph("If the x-axis data type is not given, the plot will default to having the residue numbering along the x-axis.Two special data types for the axes are:")
uf.desc[-1].add_item_list_element("'res_num'", "The axis will consist of the residue numbering.")
uf.desc[-1].add_item_list_element("'spin_num'", "The axis will consist of the spin numbering.")
uf.desc[-1].add_paragraph("The spin ID string can be used to limit which spins are used in the plot.  The default is that all spins will be used, however, the ID string can be used to select a subset of all spins, or a single spin for plots of Monte Carlo simulations, etc.")
uf.desc[-1].add_paragraph("The property which is actually plotted can be controlled by the plot data setting.  This can be one of the following:")
uf.desc[-1].add_item_list_element("'value'", "Plot values (with errors if they exist).")
uf.desc[-1].add_item_list_element("'error'", "Plot errors.")
uf.desc[-1].add_item_list_element("'sims'", "Plot the simulation values.")
uf.desc[-1].add_paragraph("Normalisation is only allowed for series type data, for example the R2 exponential curves, and will be ignored for all other data types.  If the norm flag is set to True then the y-value of the first point of the series will be set to 1.  This normalisation is useful for highlighting errors in the data sets.")
uf.desc.append(relax_fit_params.uf_doc(label="table: curve-fit parameters and min stats"))
uf.desc.append(noe_params.uf_doc(label="table: NOE parameters"))
uf.desc.append(model_free_params.uf_doc(label="table: model-free parameters and min stats"))
uf.desc.append(jw_mapping_params.uf_doc(label="table: J(w) parameters"))
uf.desc.append(consistency_test_params.uf_doc(label="table: consistency testing parameters"))
uf.desc.append(relax_disp_params.uf_doc(label="table: dispersion parameters and min stats"))
# Prompt examples.
uf.desc.append(Desc_container("Prompt examples"))
uf.desc[-1].add_paragraph("To write the NOE values for all spins to the Grace file 'noe.agr', type one of:")
uf.desc[-1].add_prompt("relax> grace.write('res_num', 'noe', file='noe.agr')")
uf.desc[-1].add_prompt("relax> grace.write(y_data_type='noe', file='noe.agr')")
uf.desc[-1].add_prompt("relax> grace.write(x_data_type='res_num', y_data_type='noe', file='noe.agr')")
uf.desc[-1].add_prompt("relax> grace.write(y_data_type='noe', file='noe.agr', force=True)")
uf.desc[-1].add_paragraph("To create a Grace file of 's2' vs. 'te' for all spins, type one of:")
uf.desc[-1].add_prompt("relax> grace.write('s2', 'te', file='s2_te.agr')")
uf.desc[-1].add_prompt("relax> grace.write(x_data_type='s2', y_data_type='te', file='s2_te.agr')")
uf.desc[-1].add_prompt("relax> grace.write(x_data_type='s2', y_data_type='te', file='s2_te.agr', force=True)")
uf.desc[-1].add_paragraph("To create a Grace file of the Monte Carlo simulation values of 'rex' vs. 'te' for residue 123, type one of:")
uf.desc[-1].add_prompt("relax> grace.write('rex', 'te', spin_id=':123', plot_data='sims', file='s2_te.agr')")
uf.desc[-1].add_prompt("relax> grace.write(x_data_type='rex', y_data_type='te', spin_id=':123', plot_data='sims', file='s2_te.agr')")
uf.desc[-1].add_paragraph("By plotting the peak intensities, the integrity of exponential relaxation curves can be checked and anomalies searched for prior to model-free analysis or reduced spectral density mapping.  For example the normalised average peak intensities can be plotted verses the relaxation time periods for the relaxation curves of all residues of a protein.  The normalisation, whereby the initial peak intensity of each residue I(0) is set to 1, emphasises any problems.  To produce this Grace file, type:")
uf.desc[-1].add_prompt("relax> grace.write(x_data_type='relax_times', y_data_type='ave_int', file='intensities_norm.agr', force=True, norm=True)")
uf.backend = grace.write
uf.menu_text = "&write"
uf.gui_icon = "oxygen.actions.document-save"
uf.wizard_size = (1000, 700)
uf.wizard_image = WIZARD_IMAGE_PATH + 'grace.png'
