###############################################################################
#                                                                             #
# Copyright (C) 2003-2013 Edward d'Auvergne                                   #
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
"""The prompt UI help system."""

# Python module imports.
import pydoc
from textwrap import wrap

# relax module imports.
from status import Status; status = Status()


# Generic string printed out for function classes.
##################################################

relax_class_help = "This is a python class which contains user functions.  To list these functions, either place a period at the end of class name and hit the tab key, or type 'dir(class_name)'."


# Helper classes.
#################

class _Helper:
    text = """\
For assistance in using a function, simply type 'help(function)'.  All functions can be viewed by hitting the [TAB] key.  In addition to functions, if 'help(object)' is typed, the help for the python object is returned.  This system is similar to the help function built into the python interpreter, which has been renamed to help_python, with the interactive component removed.  For the interactive python help system, type 'help_python()'.
    """

    def __repr__(self):
        """String representation of the object.

        @return:    The help description.
        @rtype:     str
        """

        # Wrap the text.
        string = ''
        for line in wrap(self.text, status.text_width):
            string += line + '\n'

        # Return the wrapped text.
        return string


    def __call__(self, *args, **kwds):
        """Make the object executable."""

        # Catch strange callings of the object.
        if len(args) != 1 or isinstance(args[0], str):
            print(self.text)
            return

        # Alias the object.
        obj = args[0]

        # Automatically create the user function docstring help text, storing it so it only needs to be built once.
        if not hasattr(obj, '__relax_help__') and hasattr(obj, '_build_doc'):
            obj.__relax_help__ = obj._build_doc()

        # The relax help system.
        if hasattr(obj, '__relax_help__'):
            pydoc.pager(obj.__relax_help__)
            return

        # Default to the normal Python help system.
        return pydoc.help(*args, **kwds)


class _Helper_python:
    text = """\
For the interactive python help system, type 'help_python()'.  The help_python function is identical
to the help function built into the normal python interpreter.
    """


    def __repr__(self):
        return self.text


    def __call__(self, *args, **kwds):
        return pydoc.help(*args, **kwds)
