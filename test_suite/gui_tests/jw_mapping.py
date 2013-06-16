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

# Module docstring.
"""GUI tests for the J(w) mapping related activities."""

# relax module imports.
from test_suite.gui_tests.base_classes import GuiTestCase
from test_suite import system_tests


class Jw_mapping(GuiTestCase, system_tests.jw_mapping.Jw):
    """Class for testing the J(w) mapping related functions in the GUI."""

    def __init__(self, methodName=None):
        """Set up the test case class for the system tests."""

        # Execute the base __init__ methods.
        super(Jw_mapping, self).__init__(methodName)


    def setUp(self):
        """Set up the tests by executing all base class setUp() methods."""

        # Call the base class methods.
        GuiTestCase.setUp(self)
        system_tests.jw_mapping.Jw.setUp(self)
