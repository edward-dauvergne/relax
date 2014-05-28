###############################################################################
#                                                                             #
# Copyright (C) 2012-2013 Edward d'Auvergne                                   #
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

# Package docstring.
"""Package containing all of the user function details.

This package contains all information and details about user functions, from documentation to icons to be used in the GUI.  This package contains a special data structure which will be used by the different UIs to automatically generate their interfaces to the user functions.
"""

# The __all__ package list (main modules).
__all__ = [
    'data',
    'objects'
]

# The __all__ package list (user function modules).
__all__ += [
    'align_tensor',
    'angles',
    'bmrb',
    'bruker',
    'chemical_shift',
    'consistency_tests',
    'dasha',
    'deselect',
    'diffusion_tensor',
    'domain',
    'dx',
    'eliminate',
    'fix',
    'frame_order',
    'grace',
    'interatom',
    'j_coupling',
    'jw_mapping',
    'minimisation',
    'model_free',
    'model_selection',
    'molecule',
    'molmol',
    'monte_carlo',
    'n_state_model',
    'noe',
    'palmer',
    'paramag',
    'pcs',
    'pipe',
    'pymol_control',
    'rdc',
    'relax_data',
    'relax_disp',
    'relax_fit',
    'residue',
    'reset',
    'results',
    'script',
    'select',
    'sequence',
    'spectrometer',
    'spectrum',
    'spin',
    'state',
    'structure',
    'sys_info',
    'wildcards',
    'value',
    'vmd'
]


def initialise():
    """Initialise all of the user function definitions by importing then validating them."""

    # Import all the modules to set up the data.
    import user_functions.align_tensor
    import user_functions.angles
    import user_functions.bmrb
    import user_functions.bruker
    import user_functions.chemical_shift
    import user_functions.consistency_tests
    import user_functions.dasha
    import user_functions.deselect
    import user_functions.diffusion_tensor
    import user_functions.domain
    import user_functions.dx
    import user_functions.eliminate
    import user_functions.fix
    import user_functions.frame_order
    import user_functions.grace
    import user_functions.interatom
    import user_functions.j_coupling
    import user_functions.jw_mapping
    import user_functions.minimisation
    import user_functions.model_free
    import user_functions.model_selection
    import user_functions.molecule
    import user_functions.molmol
    import user_functions.monte_carlo
    import user_functions.n_state_model
    import user_functions.noe
    import user_functions.palmer
    import user_functions.paramag
    import user_functions.pcs
    import user_functions.pipe
    import user_functions.pymol_control
    import user_functions.rdc
    import user_functions.relax_data
    import user_functions.relax_disp
    import user_functions.relax_fit
    import user_functions.residue
    import user_functions.reset
    import user_functions.results
    import user_functions.script
    import user_functions.select
    import user_functions.sequence
    import user_functions.spectrometer
    import user_functions.spectrum
    import user_functions.spin
    import user_functions.state
    import user_functions.structure
    import user_functions.sys_info
    import user_functions.value
    import user_functions.vmd

    # Import the data structure.
    from user_functions.data import Uf_info; uf_info = Uf_info()

    # Check the validity of the data.
    uf_info.validate()
