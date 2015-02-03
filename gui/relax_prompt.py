###############################################################################
#                                                                             #
# Copyright (C) 2010-2014 Edward d'Auvergne                                   #
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
"""The relax prompt GUI element."""

# Python module imports.
import sys
import wx
import wx.py
import wx.stc as stc

# relax module imports
from gui.icons import relax_icons
from info import Info_box
from prompt import interpreter
from status import Status; status = Status()


class Prompt(wx.Frame):
    """The relax prompt window object."""

    def __init__(self, *args, **kwds):
        """Set up the relax prompt."""

        # Store the parent object.
        self.gui = kwds.pop('parent')

        # Create GUI elements
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)

        # Set up the window icon.
        self.SetIcons(relax_icons)

        # Some default values.
        self.size_x = 1000
        self.size_y = 500
        self.border = 0

        # Set up the frame.
        sizer = self.setup_frame()

        # The shell.
        self.add_shell(sizer)

        # Register functions with the observer objects.
        status.observers.exec_lock.register('GUI prompt', self.enable, method_name='enable')


    def Destroy(self):
        """Cleanly destroy the window."""

        # First unregister with the observer objects.
        status.observers.exec_lock.unregister('GUI prompt')

        # Destroy the prompt.
        self.prompt.Destroy()
        del self.prompt

        # Call the parent Destroy() method.
        super(Prompt, self).Destroy()


    def add_shell(self, sizer):
        """Add the relax prompt to the sizer.

        @param sizer:   The sizer element to pack the relax prompt into.
        @type sizer:    wx.Sizer instance
        """

        # The shell.
        self.prompt = wx.py.shell.Shell(self, InterpClass=InterpClass)

        # Colours.
        self.prompt.StyleSetBackground(style=stc.STC_STYLE_DEFAULT, back='white')
        self.prompt.SetCaretForeground(fore="black")
        self.prompt.StyleClearAll()
        self.prompt.StyleSetSpec(stc.STC_STYLE_DEFAULT, "fore:black")
        self.prompt.StyleSetSpec(stc.STC_P_COMMENTLINE, "fore:#0000ff")
        self.prompt.StyleSetSpec(stc.STC_P_NUMBER, "fore:#125a0a")
        self.prompt.StyleSetSpec(stc.STC_P_STRING, "fore:#ff00ff")
        self.prompt.StyleSetSpec(stc.STC_P_CHARACTER, "fore:#ff00ff")
        self.prompt.StyleSetSpec(stc.STC_P_WORD, "fore:#a52a2a")
        self.prompt.StyleSetSpec(stc.STC_P_DEFNAME, "fore:#008b8b")
        self.prompt.StyleSetSpec(stc.STC_P_CLASSNAME, "fore:#008b8b")

        # Set the focus.
        self.prompt.setFocus()

        # Override the exiting commands.
        for name in ['exit', 'bye', 'quit', 'q']:
            self.prompt.interp.locals[name] = _Exit(fn=self.gui.exit_gui)

        # Add the shell to the sizer.
        sizer.Add(self.prompt, 1, wx.EXPAND|wx.ALL, self.border)


    def enable(self):
        """Enable and disable the prompt with the execution lock."""

        # Flag for enabling or disabling the prompt.
        enable = False
        if not status.exec_lock.locked():
            enable = True

        # Enable/disable.
        wx.CallAfter(self.prompt.Enable, enable)


    def handler_close(self, event):
        """Event handler for the close window action.

        @param event:   The wx event.
        @type event:    wx event
        """

        # Close the window.
        self.Hide()


    def setup_frame(self):
        """Set up the relax controller frame.

        @return:    The sizer object.
        @rtype:     wx.Sizer instance
        """

        # Set the frame title.
        self.SetTitle("The relax prompt")

        # Use a box sizer for packing the shell.
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        # Close the window cleanly (hide so it can be reopened).
        self.Bind(wx.EVT_CLOSE, self.handler_close)

        # Set the default size of the controller.
        self.SetSize((self.size_x, self.size_y))

        # Return the sizer.
        return sizer


class _Exit:
    def __init__(self, fn=None):
        """Store the exiting function.

        @keyword fn:    The exiting function.
        @type fn:       func
        """

        # Store.
        self.fn = fn


    def __repr__(self):
        """Exit the program."""

        # Execute the exiting function.
        self.fn()

        # Return nothing.
        return ''


class InterpClass(wx.py.interpreter.Interpreter):
    def __init__(self, locals=None, rawin=None, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, showInterpIntro=True):
        """Redefine the interpreter."""

        # Execute the base class __init__() method.
        wx.py.interpreter.Interpreter.__init__(self, locals=locals, rawin=rawin, stdin=stdin, stdout=stdout, stderr=stderr, showInterpIntro=showInterpIntro)

        # The introductory text.
        info = Info_box()
        self.introText = info.intro_text()

        # The relax interpreter.
        interp = interpreter.Interpreter(show_script=False, raise_relax_error=True)

        # The locals.
        self.locals = interp._locals
