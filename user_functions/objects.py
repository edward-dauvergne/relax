###############################################################################
#                                                                             #
# Copyright (C) 2012-2014 Edward d'Auvergne                                   #
# Copyright (C) 2014 Troels E. Linnet                                         #
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
"""The module of all the objects used to hold the user function details."""

# Python module imports.
import dep_check
if dep_check.wx_module:
    from wx import DD_DEFAULT_STYLE, FileSelectorDefaultWildcardStr
else:
    DD_DEFAULT_STYLE = -1
    FileSelectorDefaultWildcardStr = -1

# relax module imports.
from graphics import IMAGE_PATH
from lib.errors import RelaxError


class Class_container:
    """This class is used to process and store all of the user function class information.

    @ivar title:            The user function class description.
    @type title:            str
    @ivar menu_text:        The text to use for the GUI menu entry.
    @type menu_text:        str
    @ivar gui_icon:         The code for the icon to use in the GUI.
    @type gui_icon:         str or None
    """

    # The list of modifiable objects (anything else will be rejected to prevent coding errors).
    __mod_attr__ = [
            'title',
            'menu_text',
            'gui_icon'
    ]

    def __init__(self):
        """Initialise all the data."""

        # Initialise the variables for all user function classes.
        self.title = None
        self.menu_text = None
        self.gui_icon = None


    def __setattr__(self, name, value):
        """Override the class __setattr__ method.

        @param name:    The name of the attribute to modify.
        @type name:     str
        @param value:   The new value of the attribute.
        @type value:    anything
        """

        # Test if the attribute that is trying to be set is modifiable.
        if not name in self.__mod_attr__:
            raise RelaxError("The object '%s' is not a modifiable attribute." % name)

        # Set the attribute normally.
        self.__dict__[name] = value



class Container:
    """An empty container object."""



class Desc_container(object):
    """A special object for holding and processing user function description information."""

    def __init__(self, title="Description"):
        """Set up the container.

        @keyword section:   The section title.
        @type section:      str
        """

        # Store the title.
        self._title = title

        # Initialise internal storage objects.
        self._data = []
        self._types = []


    def add_item_list_element(self, item, text):
        """Add the element of an itemised list to the description.

        @param item:    The item text.
        @type item:     str
        @param text:    The itemised list element text.
        @type text:     str
        """

        # Create a new block if needed.
        if not len(self._types) or self._types[-1] != 'item list':
            self._data.append([[item, text]])
            self._types.append('item list')

        # Append the element to an existing itemised list structure.
        else:
            self._data[-1].append([item, text])


    def add_list_element(self, text):
        """Add the element of a list to the description.

        @param text:    The list element text.
        @type text:     str
        """

        # Create a new block if needed.
        if not len(self._types) or self._types[-1] != 'list':
            self._data.append([text])
            self._types.append('list')

        # Append the element to an existing list structure.
        else:
            self._data[-1].append(text)


    def add_paragraph(self, text):
        """Add a paragraph of text to the description.

        @param text:    The paragraph text.
        @type text:     str
        """

        # Store the text.
        self._data.append(text)
        self._types.append('paragraph')


    def add_prompt(self, text):
        """Add the text of a relax prompt example to the description.

        @param text:    The relax prompt text.
        @type text:     str
        """

        # Create a new block if needed.
        if not len(self._types) or self._types[-1] != 'prompt':
            self._data.append([text])
            self._types.append('prompt')

        # Append the example to an existing example block.
        else:
            self._data[-1].append(text)


    def add_table(self, label):
        """Add a table to the description.

        @param label:   The unique label corresponding to a user_functions.objects.Table instance.
        @type label:    str
        """

        # Check.
        if not isinstance(label, str):
            raise RelaxError("The table label '%s' is not a valid string.")

        # Add the table.
        self._data.append(label)
        self._types.append('table')


    def add_verbatim(self, text):
        """Add a section of verbatim text to the description.

        @param text:    The verbatim text.
        @type text:     str
        """

        # Store the text.
        self._data.append(text)
        self._types.append('verbatim')


    def element_loop(self, title=False):
        """Iterator method yielding the description elements.

        @keyword title:     A flag which if True will cause the title to be yielded first.
        @type title:        bool
        @return:            The element type and corresponding data. 
        @rtype:             str and anything
        """

        # The title.
        if title:
            yield 'title', self._title

        # Loop over the elements.
        for i in range(len(self._data)):
            yield self._types[i], self._data[i]


    def get_title(self):
        """Return the title of the section.

        @return:    The section title.
        @rtype:     str
        """

        # The title.
        return self._title



class Table(object):
    """A special class defining the tables used in the user function descriptions."""

    def __init__(self, label=None, caption=None, caption_short=None, spacing=True, longtable=False):
        """Set up the table container.

        @keyword label:         The unique label of the table.  This is used to identify tables, and is also used in the table referencing in the LaTeX compilation of the user manual.
        @type label:            str
        @keyword caption:       The caption for the table.
        @type caption:          str
        @keyword caption_short: The optional short caption for the table, used in the LaTeX user manual list of tables section for example.
        @type caption_short:    str
        @keyword spacing:       A flag which if True will cause empty rows to be placed between elements.
        @type spacing:          bool
        @keyword longtable:     A special LaTeX flag which if True will cause the longtables package to be used to spread a table across multiple pages.  This should only be used for tables that do not fit on a single page.
        @type longtable:        bool
        """

        # Store the args.
        self.label = label
        self.caption = caption
        if caption_short:
            self.caption_short = caption_short
        else:
            self.caption_short = caption
        self.spacing = spacing
        self.longtable = longtable

        # Initialise some objects.
        self.headings = None
        self.cells = []
        self.num_cols = 0


    def add_headings(self, headings):
        """Add a row of table headings.

        @param headings:    The table headings.
        @type headings:     list of str
        """

        # Store the headings.
        self.headings = headings

        # The number of columns.
        self.num_cols = len(self.headings)


    def add_row(self, row):
        """Add a table row.

        @param row: The table row.
        @type row:  list of str
        """

        # Checks.
        if self.headings == None:
            raise RelaxError("A row cannot be added as the headings have not been set up.")
        if len(row) != self.num_cols:
            raise RelaxError("The number of columns in %s does not match the %s columns of the headings." % (row, self.num_cols))

        # Append the row.
        self.cells.append(row)



class Uf_container(object):
    """This class is used to process and store all of the user function specific information.

    @ivar title:                The long title of the user function.
    @type title:                str
    @ivar title_short:          The optional short title.
    @type title_short:          str or None
    @ivar kargs:                The list of keyword argument details.
    @type kargs:                list of dict
    @ivar backend:              The user function back end.  This should be a string version with full module path of the function which executes the back end.  For example 'pipe_control.pipes.create'.  Note, this should be importable as __import__(backend)!
    @type backend:              executable object
    @ivar display:              A flag specifying if the user function displays output to STDOUT.  This is used for certain UIs to display that output.
    @type display:              str
    @ivar desc:                 The multi-paragraph description defined via the Desc_container class.
    @type desc:                 list of Desc_container instances
    @ivar menu_text:            The text to use for the GUI menu entry.
    @type menu_text:            str
    @ivar gui_icon:             The code for the icon to use in the GUI.
    @type gui_icon:             str or None
    @ivar wizard_size:          The size for the GUI user function wizard.  This defaults to (700, 500) if not supplied.
    @type wizard_size:          tuple of int or None
    @ivar wizard_image:         The 200 pixel wide image to use for the user function wizard.  This should be the path to the bitmap image.  This defaults to the relax Ulysses butterfly image.
    @type wizard_image:         str
    @ivar wizard_height_desc:   The height in pixels of the description part of the wizard.
    @type wizard_height_desc:   int
    @ivar wizard_apply_button:  A flag specifying if the apply button should be shown or not.  This defaults to True.
    @type wizard_apply_button:  bool
    @ivar gui_sync:             A GUI flag which if left on the default of False will cause user functions to be called in asynchronous mode.  If changed to True, then synchronous operation of the user functions will occur.
    @type gui_sync:             bool
    """

    # The list of modifiable objects (anything else will be rejected to prevent coding errors).
    __mod_attr__ = [
            'title',
            'title_short',
            'kargs',
            'backend',
            'display',
            'desc',
            'menu_text',
            'gui_icon',
            'wizard_size',
            'wizard_image',
            'wizard_height_desc',
            'wizard_apply_button',
            'gui_sync',
    ]


    def __init__(self):
        """Initialise all the data."""

        # Initialise the variables for all user functions.
        self.title = None
        self.title_short = None
        self.kargs = []
        self.backend = None
        self.display = False
        self.desc = []
        self.menu_text = ''
        self.gui_icon = None
        self.wizard_size = (700, 500)
        self.wizard_image = IMAGE_PATH + "relax.gif"
        self.wizard_height_desc = 300
        self.wizard_apply_button = True
        self.gui_sync = False


    def __setattr__(self, name, value):
        """Override the class __setattr__ method.

        @param name:    The name of the attribute to modify.
        @type name:     str
        @param value:   The new value of the attribute.
        @type value:    anything
        """

        # Test if the attribute that is trying to be set is modifiable.
        if not name in self.__mod_attr__:
            raise RelaxError("The object '%s' is not a modifiable attribute." % name)

        # Check for duplicative modifications (to catch typo coding errors).
        if name in ['title', 'title_short', 'backend', 'gui_icon']:
            # No object set yet.
            if not hasattr(self, name):
                obj = None

            # Get the current object.
            else:
                obj = getattr(self, name)

            # Not None!
            if obj != None:
                raise RelaxError("The variable '%s' is already set to %s." % (name, repr(obj)))

        # Set the attribute normally.
        self.__dict__[name] = value


    def add_keyarg(self, name=None, default=None, py_type=None, arg_type=None, dim=None, min=0, max=1000, desc_short=None, desc=None, list_titles=None, wiz_element_type='default', wiz_combo_choices=None, wiz_combo_data=None, wiz_combo_iter=None, wiz_combo_list_min=None, wiz_filesel_wildcard=FileSelectorDefaultWildcardStr, wiz_filesel_style=None, wiz_dirsel_style=DD_DEFAULT_STYLE, wiz_read_only=None, wiz_filesel_preview=True, can_be_none=False, can_be_empty=False, none_elements=False):
        """Wrapper method for adding keyword argument information to the container.

        @keyword name:                  The name of the argument.
        @type name:                     str
        @keyword default:               The default value of the argument.
        @type default:                  anything
        @keyword py_type:               The Python object type that the argument must match (taking the can_be_none flag into account).
        @type py_type:                  str
        @keyword arg_type:              The type of argument.  This is reserved for special UI elements:
                                            - 'file sel' will indicate to certain UIs that a file selection dialog is required.
                                            - 'dir' will cause the argument to not be shown in certain UIs, as this indicates that the user function already has a 'file sel' type argument and hence a directory is not required.
                                            - 'dir sel' will indicate to certain UIs that a dir selection dialog is required.
        @type arg_type:                 str
        @keyword dim:                   The fixed dimensions that a list or tuple must conform to.  For a 1D sequence, this can be a single value or a tuple of possible sizes.  For a 2D sequence (a numpy matrix or list of lists), this must be a tuple of the fixed dimension sizes, e.g. a 3x5 matrix should be specified as (3, 5).
        @type dim:                      int, tuple of int or None
        @keyword min:                   The minimum value allowed for integer types.  This is used in the wx.SpinCtrl for example.
        @type min:                      int
        @keyword max:                   The maximum value allowed for integer types.  This is used in the wx.SpinCtrl for example.
        @type max:                      int
        @keyword desc_short:            The short human-readable description of the argument.  This is used in the RelaxError messages to refer to the argument, as well as in the GUI user function page elements.
        @type desc_short:               str
        @keyword desc:                  The long human-readable description of the argument.
        @type desc:                     str
        @keyword list_titles:           The titles of each of the elements of the fixed length lists.  This only applies to lists or list of lists.
        @type list_titles:              list of str
        @keyword wiz_element_type:      The type of GUI element to create.  If left to 'default', then the currently set default element will be used.  If set to 'text', a wx.TextCtrl element will be used.  If set to 'combo', a wx.ComboBox element will be used.
        @type wiz_element_type:         str
        @keyword wiz_combo_choices:     The list of choices to present to the user.  This is only used if the element_type is set to 'combo'.
        @type wiz_combo_choices:        list of str
        @keyword wiz_combo_data:        The data returned by a call to GetValue().  This is only used if the element_type is set to 'combo'.  If supplied, it should be the same length at the combo_choices list.  If not supplied, the combo_choices list will be used for the returned data.
        @type wiz_combo_data:           list
        @keyword wiz_combo_iter:        An iterator method for regenerating the ComboBox choices.
        @type wiz_combo_iter:           iterator or None
        @keyword wiz_combo_list_min:    The minimum length of the Combo_list element.
        @type wiz_combo_list_min:       int or None
        @keyword wiz_filesel_wildcard:  The file selection dialog wildcard string.  For example for opening PDB files, this could be "PDB files (*.pdb)|*.pdb;*.PDB".
        @type wiz_filesel_wildcard:     str or None
        @keyword wiz_filesel_style:     The file selection dialog style.
        @type wiz_filesel_style:        int
        @keyword wiz_dirsel_style:      The directory selection dialog style.
        @type wiz_dirsel_style:         int
        @keyword wiz_read_only:         A flag which if True means that the text of the GUI wizard page element cannot be edited.  If the default of None is given, then each UI element will decide for itself what to do.
        @type wiz_read_only:            bool or None
        @keyword wiz_filesel_preview:   A flag which if True will enable the preview button in the file selection GUI wizard page element.
        @type wiz_filesel_preview:      bool
        @keyword can_be_none:           A flag which specifies if the argument is allowed to have the None value.
        @type can_be_none:              bool
        @keyword can_be_empty:          A flag which if True allows the sequence type object to be empty.
        @type can_be_empty:             bool
        @keyword none_elements:         A flag which if True allows the sequence type object to contain None elements.
        @type none_elements:            bool
        """

        # Check that the args have been properly supplied.
        if name == None:
            raise RelaxError("The 'name' argument must be supplied.")
        if py_type == None:
            raise RelaxError("The 'py_type' argument must be supplied.")
        if desc_short == None:
            raise RelaxError("The 'desc_short' argument must be supplied.")
        if desc == None:
            raise RelaxError("The 'desc' argument must be supplied.")

        # Check the file selection dialog.
        if arg_type == "file sel" and wiz_filesel_style == None:
            raise RelaxError("The file selection style must always be provided.")

        # Append a new argument dictionary to the list, and alias it.
        self.kargs.append({})
        arg = self.kargs[-1]

        # Add the data.
        arg['name'] = name
        arg['default'] = default
        arg['py_type'] = py_type
        arg['arg_type'] = arg_type
        arg['dim'] = dim
        arg['min'] = min
        arg['max'] = max
        arg['desc_short'] = desc_short
        arg['desc'] = desc
        arg['list_titles'] = list_titles
        arg['wiz_element_type'] = wiz_element_type
        if wiz_combo_choices == None:
            arg['wiz_combo_choices'] = []
        else:
            arg['wiz_combo_choices'] = wiz_combo_choices
        arg['wiz_combo_data'] = wiz_combo_data
        arg['wiz_combo_iter'] = wiz_combo_iter
        arg['wiz_combo_list_min'] = wiz_combo_list_min
        arg['wiz_filesel_wildcard'] = wiz_filesel_wildcard
        arg['wiz_filesel_style'] = wiz_filesel_style
        arg['wiz_dirsel_style'] = wiz_dirsel_style
        arg['wiz_read_only'] = wiz_read_only
        arg['wiz_filesel_preview'] = wiz_filesel_preview
        arg['can_be_none'] = can_be_none
        arg['can_be_empty'] = can_be_empty
        arg['none_elements'] = none_elements
