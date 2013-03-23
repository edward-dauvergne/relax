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

# Python module imports.
import os

# relax module imports.
import lib.arg_check
from status import Status; status = Status()


class Lh:
    def __repr__(self):
        """Function which executes the Unix command 'ls -alh'"""

        stat = os.system('ls -alh')
        return "ls -alh"


class Ll:
    def __repr__(self):
        """Function which executes the Unix command 'ls -l'"""

        stat = os.system('ls -l')
        return "ls -l"


class Ls:
    def __repr__(self):
        """Function which executes the Unix command 'ls'"""

        stat = os.system('ls')
        return "ls"


def system(command):
    """Function which executes the user supplied shell command."""

    lib.arg_check.is_str(command, 'command')
    stat = os.system(command)
