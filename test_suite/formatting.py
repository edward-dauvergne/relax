###############################################################################
#                                                                             #
# Copyright (C) 2007-2011 Edward d'Auvergne                                   #
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
import sys


def subtitle(text):
    """Function for printing the subtitles.

    @param text:    The text of the subtitle to be printed.
    @type text:     str
    """

    # The width of the subtitle string.
    width = len(text) + 2

    # Text.
    sys.stdout.write("# %s\n" % text)

    # Bottom bar.
    sys.stdout.write("#" * width)

    # Spacing.
    sys.stdout.write("\n\n")


def summary_line(name, passed, width=100):
    """Print a summary line.

    @param name:    The name of the test, test category, etc.
    @type name:     str
    @param passed:  An argument which if True causes '[ OK ]' to be printed and if False causes '[ Failed ]' to be printed.  The special string 'skip' is used to indicate that this has been skipped.
    @type passed:   bool or str
    @keyword width: The width of the line, excluding the terminal '[ OK ]' or '[ Failed ]'.
    @type width:    int
    """

    # Passed.
    if passed == True:
        state = "OK"

    # Skipped.
    elif passed == 'skip':
        state = "Skipped"

    # Failed.
    else:
        state = "Failed"

    # Dots.
    dots = ''
    for j in range(width - len(name) - len(state) - 6):
        dots += '.'

    # Write out the line.
    sys.stdout.write("%s %s [ %s ]\n" % (name, dots, state))


def title(text):
    """Function for printing the titles.

    @param text:    The text of the title to be printed.
    @type text:     str
    """

    # The width of the title string.
    width = len(text) + 4

    # Top spacing.
    sys.stdout.write("\n\n\n\n")

    # Top bar.
    sys.stdout.write("#" * width)
    sys.stdout.write("\n")

    # Text.
    sys.stdout.write("# %s #\n" % text)

    # Bottom bar.
    sys.stdout.write("#" * width)

    # Spacing.
    sys.stdout.write("\n\n\n")
