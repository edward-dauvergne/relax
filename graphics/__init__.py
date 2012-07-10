###############################################################################
#                                                                             #
# Copyright (C) 2012 Edward d'Auvergne                                        #
#                                                                             #
# This file is part of the program relax (http://www.nmr-relax.com).          #
#                                                                             #
# relax is free software; you can redistribute it and/or modify               #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation; either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# relax is distributed in the hope that it will be useful,                    #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with relax.  If not, see <http://www.gnu.org/licenses/>.              #
#                                                                             #
###############################################################################

# Package docstring.
"""The relax graphics package."""

# Python module imports.
from os import sep
from string import split

# relax module imports.
from relax_errors import RelaxError
from status import Status; status = Status()

# GUI image and icon paths.
ANALYSIS_IMAGE_PATH = status.install_path + sep + 'graphics' + sep + 'analyses' + sep
IMAGE_PATH = status.install_path + sep + 'graphics' + sep + 'misc' + sep
WIZARD_IMAGE_PATH = status.install_path + sep + 'graphics' + sep + 'wizards' + sep


def fetch_icon(icon=None, size='16x16'):
    """Return the path to the specified icon.

    The icon code consists of two parts separated by the '.' character.  These are:

        - The first part corresponds to the icon type, and can either be 'relax' or 'oxygen'.
        - The second part is the icon name, as a path.  The directories and files are separated by '.' characters.  So for the 'actions/dialog-close.png' icon, the second part would be 'actions.dialog-close'.

    To specify the 'graphics/oxygen_icons/16x16/actions/document-open.png' icon, the icon code string would therefore be 'oxygen.actions.document-open'.

    @keyword icon:  The special icon code.
    @type icon:     str
    @keyword size:  The icon size to fetch.
    @type size:     str
    @return:        The icon path, for example 'oxygen_icons/16x16/actions/document-open.png'.
    @rtype:         str
    """

    # No icon.
    if icon == None:
        return None

    # Initialise the path.
    path = status.install_path + sep + 'graphics' + sep

    # Split up the icon code.
    elements = split(icon, '.')

    # The icon type.
    if elements[0] == 'relax':
        path += 'relax_icons' + sep
    elif elements[0] == 'oxygen':
        path += 'oxygen_icons' + sep
    else:
        raise RelaxError("The icon type '%s' is unknown." % elements[0])

    # The icon size.
    path += size + sep

    # The subdirectory.
    if len(elements) == 3:
        path += elements[1] + sep

    # The file.
    path += "%s.png" % elements[-1]

    # Return the path.
    return path
