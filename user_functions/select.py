###############################################################################
#                                                                             #
# Copyright (C) 2003-2014 Edward d'Auvergne                                   #
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
"""The select user function definitions."""

# Python module imports.
import dep_check
if dep_check.wx_module:
    from wx import FD_OPEN
else:
    FD_OPEN = -1

# relax module imports.
from graphics import WIZARD_IMAGE_PATH
from pipe_control import domain, selection
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


# The select.display user function.
uf = uf_info.add_uf('select.display')
uf.title = "Display the current spin selection status."
uf.title_short = "Display spin selection status."
uf.display = True
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("This simply prints out the current spin selections.")
# Prompt examples.
uf.desc.append(Desc_container("Prompt examples"))
uf.desc[-1].add_paragraph("To show the current selections, type:")
uf.desc[-1].add_prompt("relax> select.display()")
uf.backend = selection.display
uf.menu_text = "dis&play"
uf.gui_icon = "oxygen.actions.document-preview"
uf.wizard_size = (600, 550)
uf.wizard_apply_button = False
uf.wizard_image = WIZARD_IMAGE_PATH + 'select.png'


# The select.domain user function.
uf = uf_info.add_uf("select.domain")
uf.title = "Select all spins and interatomic data containers of a domain."
uf.title_short = "Selection of whole domains."
uf.display = True
uf.add_keyarg(
    name = "domain_id",
    py_type = "str",
    arg_type = "domain ID",
    desc_short = "domain ID string",
    desc = "The domain ID string of the domain to select.",
    wiz_element_type = 'combo',
    wiz_combo_iter = domain.get_domain_ids,
    can_be_none = False
)
uf.add_keyarg(
    name = "boolean",
    default = "AND",
    py_type = "str",
    desc_short = "boolean operator",
    desc = "The boolean operator specifying how interatomic data containers should be selected.",
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
    default = True,
    py_type = "bool",
    desc_short = "change all flag",
    desc = "A flag specifying if all non-matching spin and interatomic data containers should be deselected."
)
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("This will select all spins and interatomic data containers of a given domain.  This is defined by the domain ID string as specified by the previously executed domain-related user functions.")
uf.desc.append(selection.boolean_doc)
# Prompt examples.
uf.desc.append(Desc_container("Prompt examples"))
uf.desc[-1].add_paragraph("To select all spins of the domain 'N-dom', simply type one of:")
uf.desc[-1].add_prompt("relax> select.domain('N-dom', change_all=True)")
uf.desc[-1].add_prompt("relax> select.domain(domain_id='N-dom', change_all=True)")
uf.desc[-1].add_paragraph("To select all spins of the domain 'N-dom', preserving the current selections, simply type one of:")
uf.desc[-1].add_prompt("relax> select.domain('N-dom', 'AND', True)")
uf.desc[-1].add_prompt("relax> select.domain(domain_id='N-dom', boolean='AND', change_all=True)")
uf.backend = selection.sel_domain
uf.menu_text = "&domain"
uf.wizard_height_desc = 500
uf.wizard_size = (1000, 750)
uf.wizard_apply_button = True
uf.wizard_image = WIZARD_IMAGE_PATH + 'select.png'


# The select.interatom user function.
uf = uf_info.add_uf("select.interatom")
uf.title = "Select specific interatomic data containers."
uf.title_short = "Interatomic data container selection."
uf.display = True
uf.add_keyarg(
    name = "spin_id1",
    py_type = "str",
    arg_type = "spin ID",
    desc_short = "first spin ID string",
    desc = "The spin ID string of the first spin of the interatomic data container.",
    can_be_none = True
)
uf.add_keyarg(
    name = "spin_id2",
    py_type = "str",
    arg_type = "spin ID",
    desc_short = "second spin ID string",
    desc = "The spin ID string of the second spin of the interatomic data container.",
    can_be_none = True
)
uf.add_keyarg(
    name = "boolean",
    default = "OR",
    py_type = "str",
    desc_short = "boolean operator",
    desc = "The boolean operator specifying how interatomic data containers should be selected.",
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
    desc = "A flag specifying if all other interatomic data containers should be changed."
)
# Description.
uf.desc.append(Desc_container())
uf.desc[-1].add_paragraph("This is used to select specific interatomic data containers which store information about spin pairs such as RDCs, NOEs, dipole-dipole pairs involved in relaxation, etc.  The 'change all' flag default is False meaning that all interatomic data containers currently either selected or deselected will remain that way.  Setting this to True will cause all interatomic data containers not specified by the spin ID strings to be selected.")
uf.desc.append(selection.boolean_doc)
# Prompt examples.
uf.desc.append(Desc_container("Prompt examples"))
uf.desc[-1].add_paragraph("To select all N-H backbone bond vectors of a protein, assuming these interatomic data containers have been already set up, type one of:")
uf.desc[-1].add_prompt("relax> select.interatom('@N', '@H')")
uf.desc[-1].add_prompt("relax> select.interatom(spin_id1='@N', spin_id2='@H')")
uf.desc[-1].add_paragraph("To select all H-H interatomic vectors of a small organic molecule, type one of:")
uf.desc[-1].add_prompt("relax> select.interatom('@H*', '@H*')")
uf.desc[-1].add_prompt("relax> select.interatom(spin_id1='@H*', spin_id2='@H*')")
uf.backend = selection.sel_interatom
uf.menu_text = "&interatom"
uf.wizard_height_desc = 450
uf.wizard_size = (1000, 750)
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
    wiz_filesel_style = FD_OPEN
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
uf.wizard_height_desc = 400
uf.wizard_size = (1000, 750)
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
