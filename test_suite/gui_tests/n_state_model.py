###############################################################################
#                                                                             #
# Copyright (C) 2012 Edward d'Auvergne                                        #
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
"""GUI tests for the N-state model related activities."""

# relax module imports.
from status import Status; status = Status()
from test_suite.gui_tests.base_classes import GuiTestCase
from test_suite import system_tests


class N_state_model(GuiTestCase, system_tests.n_state_model.N_state_model):
    """Class for testing the N-state model related functions in the GUI."""

    def __init__(self, methodName=None):
        """Set up the test case class for the system tests."""

        # Execute the base __init__ methods.
        super(N_state_model, self).__init__(methodName)

        # Tests to skip.
        blacklist = [
            'test_populations'
        ]

        # Skip the blacklisted tests.
        if methodName in blacklist:
            status.skipped_tests.append([methodName, None, self._skip_type])
