###############################################################################
#                                                                             #
# Copyright (C) 2006-2014 Edward d'Auvergne                                   #
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
"""Base classes for the GUI tests."""

# Python module imports.
from math import pi    # This is needed for relax scripts as pi is located in the relax prompt namespace.
from os import sep
from tempfile import mktemp, mkdtemp
from unittest import TestCase
import wx

# relax module imports.
from data_store import Relax_data_store; ds = Relax_data_store()
from gui.uf_objects import Uf_storage; uf_store = Uf_storage()
from lib.compat import queue
from lib.errors import RelaxError
from pipe_control.reset import reset
from prompt.interpreter import exec_script
from status import Status; status = Status()
from test_suite.clean_up import deletion
from user_functions.data import Uf_info; uf_info = Uf_info()


class GuiTestCase(TestCase):
    """The GUI test base class."""

    def __init__(self, methodName=None):
        """Set up the test case class for the system tests."""

        # A string used for classifying skipped tests.
        if not hasattr(self, '_skip_type'):
            self._skip_type = 'gui'

        # Execute the TestCase __init__ method.
        super(GuiTestCase, self).__init__(methodName)


    def _execute_uf(self, *args, **kargs):
        """Execute the given user function.

        @keyword uf_name:   The name of the user function.
        @type uf_name:      str
        """

        # Checks.
        if 'uf_name' not in kargs:
            raise RelaxError("The user function name argument 'uf_name' has not been supplied.")

        # Process the user function name.
        uf_name = kargs.pop('uf_name')

        # Get the user function data object.
        uf_data = uf_info.get_uf(uf_name)

        # Convert the args into keyword args.
        for i in range(len(args)):
            # The keyword name for this arg.
            name = uf_data.kargs[i]['name']

            # Check.
            if name in kargs:
                raise RelaxError("The argument '%s' clashes with the %s keyword argument of '%s'." % (arg[i], name, kargs[name]))

            # Set the keyword arg.
            kargs[name] = args[i]

        # Add the keyword args not supplied, using the default value.
        for i in range(len(uf_data.kargs)):
            # Alias.
            arg = uf_data.kargs[i]

            # Already set.
            if arg['name'] in kargs:
                continue

            # Set the default.
            kargs[arg['name']] = arg['default']

        # Merge the file and directory args, as needed.
        for i in range(len(uf_data.kargs)):
            # Alias.
            arg = uf_data.kargs[i]

            # File selection and associated directory arg.
            if arg['arg_type'] == 'dir' and arg['name'] in kargs:
                # Find the associated file selection arg name.
                for j in range(len(uf_data.kargs)):
                    if uf_data.kargs[j]['arg_type'] == 'file sel':
                        file_sel_name = uf_data.kargs[j]['name']

                # Prepend the directory to the file, if needed and supplied.
                if file_sel_name in kargs and kargs[arg['name']]:
                    kargs[file_sel_name] = kargs[arg['name']] + sep + kargs[file_sel_name]

                # Remove the directory argument.
                kargs.pop(arg['name'])

        # The user function object.
        uf = uf_store[uf_name]

        # Force synchronous operation of the user functions.
        status.gui_uf_force_sync = True

        # Call the GUI user function object with all keyword args, but do not execute the wizard.
        uf(wx_wizard_run=False, **kargs)

        # Execute the user function, by mimicking a click on 'ok'.
        uf.wizard._ok()

        # Restore the synchronous or asynchronous operation of the user functions so the GUI can return to normal.
        status.gui_uf_force_sync = False


    def check_exceptions(self):
        """Check that no exception has occurred."""

        # Check.
        try:
            # Get the exception from the queue.
            index, exc = status.exception_queue.get(block=False)

            # Print out.
            print("Exception found, failing the test with an AssertionError:\n")

            # Fail.
            self.fail()

        # No exception.
        except queue.Empty:
            pass


    def script_exec(self, script):
        """Execute a GUI script within the GUI test framework.

        @param script:  The full path of the script to execute.
        @type script:   str
        """

        # The namespace to pass into the script execution environment.
        space = locals()

        # Place some objects in the local namespace.
        space.update({'pi': pi})

        # Execute the script.
        exec_script(script, space)


    def setUp(self):
        """Set up for all the functional tests."""

        # Create a temporary file for the tests that need it.
        ds.tmpfile = mktemp()

        # Create a temporary directory for the results.
        ds.tmpdir = mkdtemp()

        # Get the wx app.
        self.app = wx.GetApp()


    def tearDown(self):
        """Default tearDown operation - delete temp directories and files and reset relax."""

        # Flush all wx events prior to the clean up operations of this method.  This prevents these events from occurring after the GUI elements have been deleted.
        wx.Yield()

        # Remove the temporary directory and variable.
        deletion(obj=ds, name='tmpdir', dir=True)
        deletion(obj=self, name='tmpdir', dir=True)

        # Remove temporary file and variable.
        deletion(obj=ds, name='tmpfile', dir=False)
        deletion(obj=self, name='tmpfile', dir=False)

        # Reset relax.
        reset()

        # Flush all wx events again to allow the reset event to propagate throughout the GUI and the execution lock to be released before the next test starts.
        wx.Yield()
