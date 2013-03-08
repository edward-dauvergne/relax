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

# relax module imports.
from check_types import is_float


# Special variables.
MULTI_COL = "@@MULTI@@"


def _blank(width=None, prefix=' ', postfix=' '):
    """Create a blank line for the table.

    @keyword width:     The total width of the table.
    @type width:        int
    @keyword prefix:    The text to add to the start of the line.
    @type prefix:       str
    @keyword postfix:   The text to add to the end of the line.
    @type postfix:      str
    @return:            The rule.
    @rtype:             str
    """

    # Return the blank line.
    return prefix + ' '*width + postfix + "\n"


def _convert_to_string(data=None, justification=None, custom_format=None):
    """Convert all elements of the given data structures to strings in place.

    @keyword data:          The headings or content to convert.
    @type data:             list of lists
    @keyword justification: The structure to store the cell justification in.
    @type justification:    list of lists
    @keyword custom_format: This list allows a custom format to be specified for each column.  The number of elements must match the number of columns.  If an element is None, then the default will be used.  Otherwise the elements must be valid string formatting constructs.
    @type custom_format:    None or list of None and str
    """

    # Loop over the rows.
    for i in range(len(data)):
        # Loop over the columns.
        for j in range(len(data[i])):
            # Default left justification.
            justification[i][j] = 'l'

            # Right justify numbers.
            if isinstance(data[i][j], int) or is_float(data[i][j]):
                justification[i][j] = 'r'

            # None types.
            if data[i][j] == None:
                data[i][j] = ''

            # Custom format (defaulting to standard string conversion if all fails).
            elif custom_format and custom_format[j]:
                try:
                    data[i][j] = custom_format[j] % data[i][j]
                except TypeError:
                    data[i][j] = "%s" % data[i][j]

            # Int types.
            elif isinstance(data[i][j], int):
                data[i][j] = "%i" % data[i][j]

            # Float types.
            elif is_float(data[i][j]):
                data[i][j] = "%g" % data[i][j]

            # All other non-string types.
            elif not isinstance(data[i][j], str):
                data[i][j] = "%s" % data[i][j]


def _rule(width=None, prefix=' ', postfix=' '):
    """Create a horizontal rule for the table.

    @keyword width:     The total width of the table.
    @type width:        int
    @keyword prefix:    The text to add to the start of the line.
    @type prefix:       str
    @keyword postfix:   The text to add to the end of the line.
    @type postfix:      str
    @return:            The rule.
    @rtype:             str
    """

    # Return the rule.
    return prefix + '_'*width + postfix + "\n"


def _table_line(text=None, widths=None, separator='   ', pad_left=' ', pad_right=' ', prefix=' ', postfix=' ', justification=None):
    """Format a line of a table.

    @keyword text:          The list of table elements.  If not given, an empty line will be be produced.
    @type text:             list of str or None
    @keyword widths:        The list of column widths for the table.
    @type widths:           list of int
    @keyword separator:     The column separation string.
    @type separator:        str
    @keyword pad_left:      The string to pad the left side of the table with.
    @type pad_left:         str
    @keyword pad_right:     The string to pad the right side of the table with.
    @type pad_right:        str
    @keyword prefix:        The text to add to the start of the line.
    @type prefix:           str
    @keyword postfix:       The text to add to the end of the line.
    @type postfix:          str
    @keyword justification: The cell justification structure.  The elements should be 'l' for left justification and 'r' for right.
    @type justification:    list of str
    @return:                The table line.
    @rtype:                 str
    """

    # Initialise.
    line = prefix + pad_left
    num_col = len(widths)

    # Loop over the columns.
    for i in range(num_col):
        # Multicolumn (middle/end).
        if text[i] == MULTI_COL:
            continue

        # The column separator.
        if i > 0:
            line += separator

        # Multicolumn (start).
        if i < num_col-1 and text[i+1] == MULTI_COL:
            # Find the full multicell width.
            width = widths[i]
            for j in range(i+1, num_col):
                if text[j] == MULTI_COL:
                    width += len(separator) + widths[j]

            # Add the padded text.
            if justification[i] == 'l':
                line += text[i]
            line += " " * (width - len(text[i]))
            if justification[i] == 'r':
                line += text[i]

        # Normal cell.
        else:
            if justification[i] == 'l':
                line += text[i]
            line += " " * (widths[i] - len(text[i]))
            if justification[i] == 'r':
                line += text[i]

    # Close the line.
    line += pad_right + postfix + "\n"

    # Return the text.
    return line


def format_table(headings=None, contents=None, max_width=None, separator='   ', pad_left=' ', pad_right=' ', prefix=' ', postfix=' ', custom_format=None, spacing=False, debug=False):
    """Format and return the table as text.

    If the heading or contents contains the value of the MULTI_COL constant defined in this module, then that cell will be merged with the previous cell to allow elements to span multiple columns.


    @keyword headings:      The table header.
    @type headings:         list of lists of str
    @keyword contents:      The table contents.
    @type contents:         list of lists of str
    @keyword max_width:     The maximum width of the table.
    @type max_width:        int
    @keyword separator:     The column separation string.
    @type separator:        str
    @keyword pad_left:      The string to pad the left side of the table with.
    @type pad_left:         str
    @keyword pad_right:     The string to pad the right side of the table with.
    @type pad_right:        str
    @keyword prefix:        The text to add to the start of the line.
    @type prefix:           str
    @keyword postfix:       The text to add to the end of the line.
    @type postfix:          str
    @keyword custom_format: This list allows a custom format to be specified for each column.  The number of elements must match the number of columns.  If an element is None, then the default will be used.  Otherwise the elements must be valid string formatting constructs.
    @type custom_format:    None or list of None and str
    @keyword spacing:       A flag which if True will add blank line between each row.
    @type spacing:          bool
    @keyword debug:         A flag which if True will activate a number of debugging printouts.
    @type debug:            bool
    @return:                The formatted table.
    @rtype:                 str
    """

    # Initialise some variables.
    text = ''
    num_rows = len(contents)
    num_cols = len(contents[0])
    num_head_rows = len(headings)

    # Deepcopy so that modifications to the data are not seen.
    headings = deepcopy(headings)
    contents = deepcopy(contents)

    # Create data structures for specifying the cell justification.
    justification_headings = deepcopy(headings)
    justification_contents = deepcopy(contents)

    # Convert all data to strings.
    _convert_to_string(data=headings, justification=justification_headings, custom_format=custom_format)
    _convert_to_string(data=contents, justification=justification_contents, custom_format=custom_format)

    # Initialise the pre-wrapping column widths.
    prewrap_widths = [0] * num_cols

    # Determine the maximum column widths from the headers.
    for i in range(num_head_rows):
        for j in range(num_cols):
            # Skip multicolumn entries.
            if headings[i][j] == MULTI_COL or (j < num_cols-1 and headings[i][j+1] == MULTI_COL):
                continue

            # The element is larger than the previous.
            if len(headings[i][j]) > prewrap_widths[j]:
                prewrap_widths[j] = len(headings[i][j])

    # Determine the maximum column widths from the content.
    for i in range(num_rows):
        for j in range(num_cols):
            # Skip multicolumn entries.
            if contents[i][j] == MULTI_COL or (j < num_cols-1 and contents[i][j+1] == MULTI_COL):
                continue

            # The element is larger than the previous.
            if len(contents[i][j]) > prewrap_widths[j]:
                prewrap_widths[j] = len(contents[i][j])

    # The free space for the text (subtracting the space used for the formatting).
    used = len(pad_left)
    used += len(pad_right)
    used += len(separator) * (num_cols - 1)
    if max_width:
        free_space = max_width - used
    else:
        free_space = 1000

    # The maximal width for all cells.
    free_width = sum(prewrap_widths)

    # Column wrapping.
    if free_width > free_space:
        # Debugging printouts.
        if debug:
            print
            print("Table column wrapping algorithm:")
            print("%-20s %s" % ("num_cols:", num_cols))
            print("%-20s %s" % ("free space:", free_space))

        # New structures.
        new_widths = deepcopy(prewrap_widths)
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
            print("    %-20s %s" % ("prewrap_widths:", prewrap_widths))
            print("    %-20s %s" % ("new_widths:", new_widths))
            print("    %-20s %s" % ("num_cols:", num_cols))
            print("    %-20s %s" % ("num_cols_wrap:", num_cols_wrap))
            print("    %-20s %s" % ("free_space:", free_space))
            print("    %-20s %s" % ("free_space_wrap:", free_space_wrap))
            print("    %-20s %s" % ("col_wrap:", col_wrap))

    # No column wrapping.
    else:
        new_widths = prewrap_widths
        col_wrap = [False] * num_cols

    # The total table width.
    total_width = sum(new_widths) + used

    # The header.
    text += _rule(width=total_width)    # Top rule.
    text += _blank(width=total_width)    # Blank line.
    for i in range(num_head_rows):
        text += _table_line(text=headings[i], widths=new_widths, separator='   ', pad_left=pad_left, pad_right=pad_right, prefix=prefix, postfix=postfix, justification=justification_headings[i])
        if i < num_head_rows-1 and spacing:
            text += _blank(width=total_width)
    text += _rule(width=total_width)    # Middle rule.

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
            text += _blank(width=total_width)

        # The contents.
        for k in range(num_lines):
            text += _table_line(text=col_text[k], widths=new_widths, separator=separator, pad_left=pad_left, pad_right=pad_right, prefix=prefix, postfix=postfix, justification=justification_contents[i])

    # The bottom rule, followed by a blank line.
    text += _rule(width=total_width)
    text += _blank(width=total_width)

    # Return the table text.
    return text
