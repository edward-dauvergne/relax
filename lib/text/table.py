###############################################################################
#                                                                             #
# Copyright (C) 2009-2013 Edward d'Auvergne                                   #
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
"""Functions for the text formatting of tables."""

# Python module imports.
from copy import deepcopy
from textwrap import wrap


def _table_line(text=None, widths=None, bottom=False):
    """Format a line of a table.

    @keyword text:      The list of table elements.  If not given, an empty line will be be produced.
    @type text:         list of str or None
    @keyword widths:    The list of column widths for the table.
    @type widths:       list of int
    @keyword botton:    A flag which if True will cause a table bottom line to be produced.
    @type bottom:       bool
    @return:            The table line.
    @rtype:             str
    """

    # Initialise.
    if bottom:
        line = " _"
    else:
        line = "  "

    # Loop over the columns.
    for i in range(len(widths)):
        # The column separator.
        if i > 0:
            if bottom:
                line += "___"
            else:
                line += "   "

        # A bottom line.
        if bottom:
            line += "_" * widths[i]

        # Empty line.
        elif text == None:
            line += " " * widths[i]

        # The text.
        else:
            line += text[i]
            line += " " * (widths[i] - len(text[i]))

    # Close the line.
    if bottom:
        line += "_ \n"
    else:
        line += "  \n"

    # Return the text.
    return line


def format_table(headings=None, contents=None, max_width=None, spacing=False, debug=False):
    """Format and return the table as text.

    @keyword headings:  The table header.
    @type headings:     list of lists of str
    @keyword contents:  The table contents.
    @type contents:     list of lists of str
    @keyword max_width: The maximum width of the table.
    @type max_width:    int
    @keyword spacing:   A flag which if True will add blank line between each row.
    @type spacing:      bool
    @keyword debug:     A flag which if True will activate a number of debugging printouts.
    @type debug:        bool
    @return:            The formatted table.
    @rtype:             str
    """

    # Initialise some variables.
    text = ''
    num_rows = len(contents)
    num_cols = len(contents[0])
    num_head_rows = len(headings)

    # The column widths.
    widths = [0] * num_cols
    for i in range(num_head_rows):
        for j in range(num_cols):
            # The element is larger than the previous.
            if len(headings[i][j]) > widths[j]:
                widths.append(len(headings[i][j]))
    for i in range(num_rows):
        for j in range(num_cols):
            # The element is larger than the previous.
            if len(contents[i][j]) > widths[j]:
                widths[j] = len(contents[i][j])

    # The free space for the text.
    used = 0
    used += 2    # Start of the table '  '.
    used += 2    # End of the table '  '.
    used += 3 * (num_cols - 1)   # Middle of the table '   '.
    if max_width:
        free_space = max_width - used
    else:
        free_space = 1e10

    # The maximal width for all cells.
    free_width = sum(widths)

    # Column wrapping.
    if free_width > free_space:
        # Debugging printouts.
        if debug:
            print
            print("Table column wrapping algorithm:")
            print("%-20s %s" % ("num_cols:", num_cols))
            print("%-20s %s" % ("free space:", free_space))

        # New structures.
        new_widths = deepcopy(widths)
        num_cols_wrap = num_cols
        free_space_wrap = free_space
        col_wrap = [True] * num_cols

        # Loop.
        while True:
            # The average column width.
            ave_width = int(free_space_wrap / num_cols_wrap)

            # Debugging printout.
            if debug:
                print("    %-20s %s" % ("ave_width:", ave_width))

            # Rescale.
            rescale = False
            for i in range(num_cols):
                # Remove the column from wrapping if smaller than the average wrapped width.
                if col_wrap[i] and new_widths[i] < ave_width:
                    # Recalculate.
                    free_space_wrap = free_space_wrap - new_widths[i]
                    num_cols_wrap -= 1
                    rescale = True

                    # Remove the column from wrapping.
                    col_wrap[i] = False

                    # Debugging printout.
                    if debug:
                        print("        %-20s %s" % ("remove column:", i))

            # Done.
            if not rescale:
                # Set the column widths.
                for i in range(num_cols):
                    if new_widths[i] > ave_width:
                        new_widths[i] = ave_width
                break

        # Debugging printouts.
        if debug:
            print("    %-20s %s" % ("widths:", widths))
            print("    %-20s %s" % ("new_widths:", new_widths))
            print("    %-20s %s" % ("num_cols:", num_cols))
            print("    %-20s %s" % ("num_cols_wrap:", num_cols_wrap))
            print("    %-20s %s" % ("free_space:", free_space))
            print("    %-20s %s" % ("free_space_wrap:", free_space_wrap))
            print("    %-20s %s" % ("col_wrap:", col_wrap))

    # No column wrapping.
    else:
        new_widths = widths
        col_wrap = [False] * num_cols

    # The total table width.
    total_width = sum(new_widths) + used

    # The header.
    text += " " + "_" * (total_width - 2) + "\n"    # Top rule.
    text += _table_line(widths=new_widths)    # Blank line.
    for i in range(num_head_rows):
        text += _table_line(text=headings[i], widths=new_widths)    # The headings.
    text += _table_line(widths=new_widths, bottom=True)    # Middle rule.

    # The table contents.
    for i in range(num_rows):
        # Column text, with wrapping.
        col_text = [contents[i]]
        num_lines = 1
        for j in range(num_cols):
            if col_wrap[j]:
                # Wrap.
                lines = wrap(col_text[0][j], new_widths[j])

                # Count the lines.
                num_lines = len(lines)

                # Replace the column text.
                for k in range(num_lines):
                    # New row of empty text.
                    if len(col_text) <= k:
                        col_text.append(['']*num_cols)

                    # Pack the data.
                    col_text[k][j] = lines[k]

        # Blank line (between rows when asked, and for the first row after the header).
        if spacing or i == 0:
            text += _table_line(widths=new_widths)

        # The contents.
        for k in range(num_lines):
            text += _table_line(text=col_text[k], widths=new_widths)

    # The bottom.
    text += _table_line(widths=new_widths, bottom=True)    # Bottom rule.

    # Add a newline.
    text += '\n'

    # Return the table text.
    return text
