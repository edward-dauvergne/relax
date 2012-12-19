###############################################################################
#                                                                             #
# Copyright (C) 2011-2012 Edward d'Auvergne                                   #
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
"""Module for handling errors in the GUI."""

# Python module imports.
import sys
import wx

# relax module imports.
from status import Status; status = Status()


def gui_raise(relax_error, raise_flag=False):
    """Handle errors in the GUI to be reported to the user.

    @param relax_error:     The error object.
    @type relax_error:      RelaxError instance
    @keyword raise_flag:    A flag which if True will cause the error to be raised, terminating execution.
    @type raise_flag:       bool
    @raises RelaxError:     This raises all RelaxErrors, if the raise flag is given.
    """

    # Turn off the busy cursor if needed.
    if wx.IsBusy():
        wx.EndBusyCursor()

    # Non-fatal - the error is not raised so just send the text to STDERR.
    if not raise_flag:
        sys.stderr.write(relax_error.__str__())
        sys.stderr.write("\n")

    # Show the relax controller (so that the window doesn't hide the dialog).
    app = wx.GetApp()
    app.gui.show_controller(None)
    app.Yield(True)

    # Show a dialog explaining the error.
    dlg = wx.MessageDialog(None, relax_error.text, caption="RelaxError", style=wx.OK|wx.ICON_ERROR)
    if status.show_gui:
        dlg.ShowModal()

    # Throw the error to terminate execution.
    if raise_flag:
        raise relax_error
