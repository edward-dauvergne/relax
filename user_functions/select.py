###############################################################################
#                                                                             #
# Copyright (C) 2003-2012 Edward d'Auvergne                                   #
#                                                                             #
# This file is part of the program relax.                                     #
#                                                                             #
# relax is free software; you can redistribute it and/or modify               #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation; either version 2 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# relax is distributed in the hope that it will be useful,                    #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with relax; if not, write to the Free Software                        #
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA   #
#                                                                             #
###############################################################################

# Module docstring.
"""The select user function definitions."""

# Python module imports.
import wx

# relax module imports.
from generic_fns import selection
from graphics import WIZARD_IMAGE_PATH
from user_functions.data import Uf_info; uf_info = Uf_info()
from user_functions.objects import Desc_container


# The user function class.
uf_class = uf_info.add_class("select")
uf_class.title = "Class for selecting spins."
uf_class.menu_text = "&select"
uf_class.gui_icon = "relax.spin"


# The select.all user function.
uf = uf_info.add_uf("select.all")
uf.title = "Select all spins in the current data pipe."
uf.title_short = "Selection of all spins."
uf.display = True
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("This will select all spins, irregardless of their current state.")
# Prompt examples.
uf.desc.append(Desc_container("Prompt examples"))
uf.desc[-1].add_paragraph("To select all spins, simply type:")
uf.desc[-1].add_prompt("relax> select.all()")
uf.backend = selection.sel_all
uf.menu_text = "&all"
uf.wizard_size = (600, 550)
uf.wizard_apply_button = False
uf.wizard_image = WIZARD_IMAGE_PATH + 'select.png'


# The select.read user function.
uf = uf_info.add_uf("select.read")
uf.title = "Select the spins contained in a file."
uf.title_short = "Selecting spins from file."
uf.display = True
uf.add_keyarg(
    name = "file",
    py_type = "str_or_inst",
    arg_type = "file sel",
    desc_short = "file name",
    desc = "The name of the file containing the list of spins to select.",
    wiz_filesel_style = wx.FD_OPEN
)
uf.add_keyarg(
    name = "dir",
    py_type = "str",
    arg_type = "dir",
    desc_short = "directory name",
    desc = "The directory where the file is located.",
    can_be_none = True
)
uf.add_keyarg(
    name = "spin_id_col",
    py_type = "int",
    arg_type = "free format",
    desc_short = "spin ID string column",
    desc = "The spin ID string column (an alternative to the mol, res, and spin name and number columns).",
    can_be_none = True
)
uf.add_keyarg(
    name = "mol_name_col",
    py_type = "int",
    arg_type = "free format",
    desc_short = "molecule name column",
    desc = "The molecule name column (alternative to the spin_id_col).",
    can_be_none = True
)
uf.add_keyarg(
    name = "res_num_col",
    py_type = "int",
    arg_type = "free format",
    desc_short = "residue number column",
    desc = "The residue number column (alternative to the spin_id_col).",
    can_be_none = True
)
uf.add_keyarg(
    name = "res_name_col",
    py_type = "int",
    arg_type = "free format",
    desc_short = "residue name column",
    desc = "The residue name column (alternative to the spin_id_col).",
    can_be_none = True
)
uf.add_keyarg(
    name = "spin_num_col",
    py_type = "int",
    arg_type = "free format",
    desc_short = "spin number column",
    desc = "The spin number column (alternative to the spin_id_col).",
    can_be_none = True
)
uf.add_keyarg(
    name = "spin_name_col",
    py_type = "int",
    arg_type = "free format",
    desc_short = "spin name column",
    desc = "The spin name column (alternative to the spin_id_col).",
    can_be_none = True
)
uf.add_keyarg(
    name = "sep",
    py_type = "str",
    arg_type = "free format",
    desc_short = "column separator",
    desc = "The column separator (the default is white space).",
    can_be_none = True
)
uf.add_keyarg(
    name = "spin_id",
    py_type = "str",
    arg_type = "spin ID",
    desc_short = "spin ID string",
    desc = "The spin ID string to restrict the loading of data to certain spin subsets.",
    can_be_none = True
)
uf.add_keyarg(
    name = "boolean",
    default = "OR",
    py_type = "str",
    desc_short = "boolean operator",
    desc = "The boolean operator specifying how spins should be selected.",
    wiz_element_type = "combo",
    wiz_combo_choices = [
        "OR",
        "NOR",
        "AND",
        "NAND",
        "XOR",
        "XNOR"
    ],
    wiz_read_only = True
)
uf.add_keyarg(
    name = "change_all",
    default = False,
    py_type = "bool",
    desc_short = "change all",
    desc = "A flag specifying if all other spins should be changed."
)
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("The spin system can be identified in the file using two different formats.  The first is the spin ID string column which can include the molecule name, the residue name and number, and the spin name and number.  Alternatively the molecule name, residue number, residue name, spin number and/or spin name columns can be supplied allowing this information to be in separate columns.  Note that the numbering of columns starts at one.  The spin ID string can be used to restrict the reading to certain spin types, for example only 15N spins when only residue information is in the file.")
uf.desc[-1].add_paragraph("Empty lines and lines beginning with a hash are ignored.")
uf.desc[-1].add_paragraph("The 'change all' flag default is False meaning that all spins currently either selected or deselected will remain that way.  Setting this to True will cause all spins not specified in the file to be deselected.")
uf.desc.append(selection.boolean_doc)
# Prompt examples.
uf.desc.append(Desc_container("Prompt examples"))
uf.desc[-1].add_paragraph("To select all residues listed with residue numbers in the first column of the file 'isolated_peaks', type one of:")
uf.desc[-1].add_prompt("relax> select.read('isolated_peaks', res_num_col=1)")
uf.desc[-1].add_prompt("relax> select.read(file='isolated_peaks', res_num_col=1)")
uf.desc[-1].add_paragraph("To select the spins in the second column of the relaxation data file 'r1.600' while deselecting all other spins, for example type:")
uf.desc[-1].add_prompt("relax> select.read('r1.600', spin_num_col=2, change_all=True)")
uf.desc[-1].add_prompt("relax> select.read(file='r1.600', spin_num_col=2, change_all=True)")
uf.backend = selection.sel_read
uf.menu_text = "&read"
uf.gui_icon = "oxygen.actions.document-open"
uf.wizard_height_desc = 200
uf.wizard_size = (1000, 700)
uf.wizard_image = WIZARD_IMAGE_PATH + 'select.png'


# The select.reverse user function.
uf = uf_info.add_uf("select.reverse")
uf.title = "Reversal of the spin selection for the given spins."
uf.title_short = "Spin selection reversal."
uf.display = True
uf.add_keyarg(
    name = "spin_id",
    py_type = "str",
    desc_short = "spin ID string",
    desc = "The spin ID string.",
    can_be_none = True
)
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("By supplying the spin ID string, a subset of spins can have their selection status reversed.")
# Prompt examples.
uf.desc.append(Desc_container("Prompt examples"))
uf.desc[-1].add_paragraph("To select all currently deselected spins and deselect those which are selected type:")
uf.desc[-1].add_prompt("relax> select.reverse()")
uf.backend = selection.reverse
uf.menu_text = "re&verse"
uf.gui_icon = "oxygen.actions.system-switch-user"
uf.wizard_size = (700, 550)
uf.wizard_apply_button = False
uf.wizard_image = WIZARD_IMAGE_PATH + 'select.png'


# The select.spin user function.
uf = uf_info.add_uf("select.spin")
uf.title = "Select specific spins."
uf.title_short = "Spin selection."
uf.display = True
uf.add_keyarg(
    name = "spin_id",
    py_type = "str",
    desc_short = "spin ID string",
    desc = "The spin ID string.",
    can_be_none = True
)
uf.add_keyarg(
    name = "boolean",
    default = "OR",
    py_type = "str",
    desc_short = "boolean operator",
    desc = "The boolean operator specifying how spins should be selected.",
    wiz_element_type = "combo",
    wiz_combo_choices = [
        "OR",
        "NOR",
        "AND",
        "NAND",
        "XOR",
        "XNOR"
    ],
    wiz_read_only = True
)
uf.add_keyarg(
    name = "change_all",
    default = False,
    py_type = "bool",
    desc_short = "change all",
    desc = "A flag specifying if all other spins should be changed."
)
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("The 'change all' flag default is False meaning that all spins currently either selected or deselected will remain that way.  Setting this to True will cause all spins not specified by the spin ID string to be selected.")
uf.desc.append(selection.boolean_doc)
# Prompt examples.
uf.desc.append(Desc_container("Prompt examples"))
uf.desc[-1].add_paragraph("To select only glycines and alanines, assuming they have been loaded with the names GLY and ALA, type one of:")
uf.desc[-1].add_prompt("relax> select.spin(spin_id=':GLY|:ALA')")
uf.desc[-1].add_paragraph("To select residue 5 CYS in addition to the currently selected residues, type one of:")
uf.desc[-1].add_prompt("relax> select.spin(':5')")
uf.desc[-1].add_prompt("relax> select.spin(':5&:CYS')")
uf.desc[-1].add_prompt("relax> select.spin(spin_id=':5&:CYS')")
uf.backend = selection.sel_spin
uf.menu_text = "&spin"
uf.gui_icon = "relax.spin"
uf.wizard_height_desc = 500
uf.wizard_size = (1000, 750)
uf.wizard_image = WIZARD_IMAGE_PATH + 'select.png'
