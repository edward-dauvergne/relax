###############################################################################
#                                                                             #
# Copyright (C) 2011-2013 Edward d'Auvergne                                   #
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
"""The pipe editor GUI element."""

# Python module imports.
import wx
import wx.grid

# relax module imports.
from data_store import Relax_data_store; ds = Relax_data_store()
from graphics import WIZARD_IMAGE_PATH, fetch_icon
from gui.components.menu import build_menu_item
from gui.fonts import font
from gui.icons import relax_icons
from gui.message import Question
from gui.misc import add_border, bitmap_setup
from gui.string_conv import gui_to_str, str_to_gui
from gui.uf_objects import Uf_storage; uf_store = Uf_storage()
from lib.errors import RelaxError
from pipe_control.pipes import cdp_name, delete, get_bundle, get_type, pipe_names, switch
from status import Status; status = Status()


class Pipe_editor(wx.Frame):
    """The pipe editor window object."""

    def __init__(self, gui=None, size_x=1000, size_y=600, border=10):
        """Set up the relax controller frame.
        
        @keyword gui:       The main GUI object.
        @type gui:          wx.Frame instance
        @keyword size_x:    The initial and minimum width of the window.
        @type size_x:       int
        @keyword size_y:    The initial and minimum height of the window.
        @type size_y:       int
        @keyword border:    The size of the internal border of the window.
        @type border:       int
        """

        # Store the args.
        self.gui = gui
        self.border = border

        # Create GUI elements
        wx.Frame.__init__(self, None, id=-1, title="Data pipe editor")

        # Set up the window icon.
        self.SetIcons(relax_icons)

        # Initialise some data.
        self.width_col_label = 40

        # Set the normal and minimum window sizes.
        self.SetMinSize((size_x, size_y))
        self.SetSize((size_x, size_y))

        # Place all elements within a panel (to remove the dark grey in MS Windows).
        self.main_panel = wx.Panel(self, -1)

        # Pack a sizer into the panel.
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_panel.SetSizer(main_sizer)

        # Build the central sizer, with borders.
        sizer = add_border(main_sizer, border=border, packing=wx.VERTICAL)

        # Add the contents.
        sizer.AddSpacer(10)
        self.add_logo(sizer)
        sizer.AddSpacer(20)
        self.add_buttons(sizer)
        sizer.AddSpacer(10)
        self.add_table(sizer)

        # Bind some events.
        self.grid.Bind(wx.EVT_SIZE, self.resize)
        self.Bind(wx.EVT_CLOSE, self.handler_close)
        self.grid.Bind(wx.grid.EVT_GRID_CELL_RIGHT_CLICK, self.menu)

        # Initialise the observer name.
        self.name = 'pipe editor'

        # Update the grid.
        self.update_grid()


    def activate(self):
        """Activate or deactivate certain elements in response to the execution lock."""

        # Turn off all buttons.
        if status.exec_lock.locked():
            wx.CallAfter(self.button_bundle.Enable, False)
            wx.CallAfter(self.button_create.Enable, False)
            wx.CallAfter(self.button_copy.Enable, False)
            wx.CallAfter(self.button_delete.Enable, False)
            wx.CallAfter(self.button_hybrid.Enable, False)
            wx.CallAfter(self.button_switch.Enable, False)

        # Turn on all buttons.
        else:
            wx.CallAfter(self.button_bundle.Enable, True)
            wx.CallAfter(self.button_create.Enable, True)
            wx.CallAfter(self.button_copy.Enable, True)
            wx.CallAfter(self.button_delete.Enable, True)
            wx.CallAfter(self.button_hybrid.Enable, True)
            wx.CallAfter(self.button_switch.Enable, True)


    def menu(self, event):
        """The pop up menu.

        @param event:   The wx event.
        @type event:    wx event
        """

        # Get the row.
        row = event.GetRow()

        # Get the name of the data pipe.
        self.selected_pipe = gui_to_str(self.grid.GetCellValue(row, 0))

        # No data pipe.
        if not self.selected_pipe:
            return

        # The pipe type and bundle.
        pipe_type = get_type(self.selected_pipe)
        pipe_bundle = get_bundle(self.selected_pipe)

        # Initialise the menu.
        menu = wx.Menu()
        items = []

        # Menu entry:  add the data pipe to a bundle.
        if not pipe_bundle:
            items.append(build_menu_item(menu, parent=self, text="&Add the pipe to a bundle", icon=fetch_icon("relax.pipe_bundle"), fn=self.pipe_bundle))

        # Menu entry:  delete the data pipe.
        items.append(build_menu_item(menu, parent=self, text="&Delete the pipe", icon=fetch_icon('oxygen.actions.list-remove', "16x16"), fn=self.pipe_delete))
 
        # Menu entry:  switch to this data pipe.
        items.append(build_menu_item(menu, parent=self, text="&Switch to this pipe", icon=fetch_icon('oxygen.actions.system-switch-user', "16x16"), fn=self.pipe_switch))
 
        # Menu entry:  new auto-analysis tab.
        if pipe_bundle and self.gui.analysis.page_index_from_bundle(pipe_bundle) == None and pipe_type in ['noe', 'r1', 'r2', 'mf', 'relax_disp']:
            items.append(build_menu_item(menu, parent=self, text="&Associate with a new auto-analysis", icon=fetch_icon('oxygen.actions.document-new', "16x16"), fn=self.associate_auto))
 
        # Set up the entries.
        for item in items:
            menu.AppendItem(item)
            if status.exec_lock.locked():
                item.Enable(False)

        # Show the menu.
        if status.show_gui:
            self.PopupMenu(menu)

        # Kill the menu once done.
        menu.Destroy()


    def add_buttons(self, sizer):
        """Add the buttons to the sizer.

        @param sizer:   The sizer element to pack the buttons into.
        @type sizer:    wx.Sizer instance
        """

        # Create a horizontal layout for the buttons.
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(button_sizer, 0, wx.ALL|wx.EXPAND, 0)

        # The bundle button.
        self.button_bundle = wx.lib.buttons.ThemedGenBitmapTextButton(self.main_panel, -1, None, " Bundle")
        self.button_bundle.SetBitmapLabel(wx.Bitmap(fetch_icon("relax.pipe_bundle", size="22x22"), wx.BITMAP_TYPE_ANY))
        self.button_bundle.SetFont(font.normal)
        self.button_bundle.SetToolTipString("Add a data pipe to a data pipe bundle.")
        button_sizer.Add(self.button_bundle, 1, wx.ALL|wx.EXPAND, 0)
        self.Bind(wx.EVT_BUTTON, self.uf_launch, self.button_bundle)

        # The create button.
        self.button_create = wx.lib.buttons.ThemedGenBitmapTextButton(self.main_panel, -1, None, " Create")
        self.button_create.SetBitmapLabel(wx.Bitmap(fetch_icon('oxygen.actions.list-add-relax-blue', "22x22"), wx.BITMAP_TYPE_ANY))
        self.button_create.SetFont(font.normal)
        self.button_create.SetToolTipString("Create a new data pipe.")
        button_sizer.Add(self.button_create, 1, wx.ALL|wx.EXPAND, 0)
        self.Bind(wx.EVT_BUTTON, self.uf_launch, self.button_create)

        # The copy button.
        self.button_copy = wx.lib.buttons.ThemedGenBitmapTextButton(self.main_panel, -1, None, " Copy")
        self.button_copy.SetBitmapLabel(wx.Bitmap(fetch_icon('oxygen.actions.list-add', "22x22"), wx.BITMAP_TYPE_ANY))
        self.button_copy.SetFont(font.normal)
        self.button_copy.SetToolTipString("Copy a data pipe.")
        button_sizer.Add(self.button_copy, 1, wx.ALL|wx.EXPAND, 0)
        self.Bind(wx.EVT_BUTTON, self.uf_launch, self.button_copy)

        # The delete button.
        self.button_delete = wx.lib.buttons.ThemedGenBitmapTextButton(self.main_panel, -1, None, " Delete")
        self.button_delete.SetBitmapLabel(wx.Bitmap(fetch_icon('oxygen.actions.list-remove', "22x22"), wx.BITMAP_TYPE_ANY))
        self.button_delete.SetFont(font.normal)
        self.button_delete.SetToolTipString("Delete a data pipe.")
        button_sizer.Add(self.button_delete, 1, wx.ALL|wx.EXPAND, 0)
        self.Bind(wx.EVT_BUTTON, self.uf_launch, self.button_delete)

        # The hybridise button.
        self.button_hybrid = wx.lib.buttons.ThemedGenBitmapTextButton(self.main_panel, -1, None, " Hybridise")
        self.button_hybrid.SetBitmapLabel(wx.Bitmap(fetch_icon('relax.pipe_hybrid', "22x22"), wx.BITMAP_TYPE_ANY))
        self.button_hybrid.SetFont(font.normal)
        self.button_hybrid.SetToolTipString("Hybridise data pipes.")
        button_sizer.Add(self.button_hybrid, 1, wx.ALL|wx.EXPAND, 0)
        self.Bind(wx.EVT_BUTTON, self.uf_launch, self.button_hybrid)

        # The switch button.
        self.button_switch = wx.lib.buttons.ThemedGenBitmapTextButton(self.main_panel, -1, None, " Switch")
        self.button_switch.SetBitmapLabel(wx.Bitmap(fetch_icon('oxygen.actions.system-switch-user', "22x22"), wx.BITMAP_TYPE_ANY))
        self.button_switch.SetFont(font.normal)
        self.button_switch.SetToolTipString("Switch data pipes.")
        button_sizer.Add(self.button_switch, 1, wx.ALL|wx.EXPAND, 0)
        self.Bind(wx.EVT_BUTTON, self.uf_launch, self.button_switch)


    def uf_launch(self, event):
        """Launch the user function GUI wizards.

        @param event:   The wx event.
        @type event:    wx event
        """

        # Launch the respective user functions.
        if event.GetEventObject() == self.button_bundle:
            uf_store['pipe.bundle'](event, wx_parent=self, wx_wizard_sync=True, wx_wizard_modal=True)
        elif event.GetEventObject() == self.button_create:
            uf_store['pipe.create'](event, wx_parent=self, wx_wizard_sync=True, wx_wizard_modal=True)
        elif event.GetEventObject() == self.button_copy:
            uf_store['pipe.copy'](event, wx_parent=self, wx_wizard_sync=True, wx_wizard_modal=True)
        elif event.GetEventObject() == self.button_delete:
            uf_store['pipe.delete'](event, wx_parent=self, wx_wizard_sync=True, wx_wizard_modal=True)
        elif event.GetEventObject() == self.button_hybrid:
            uf_store['pipe.hybridise'](event, wx_parent=self, wx_wizard_sync=True, wx_wizard_modal=True)
        elif event.GetEventObject() == self.button_switch:
            uf_store['pipe.switch'](event, wx_parent=self, wx_wizard_sync=True, wx_wizard_modal=True)


    def add_logo(self, box):
        """Add the logo to the sizer.

        @param box:     The sizer element to pack the logo into.
        @type box:      wx.Sizer instance
        """

        # The pipe logo.
        logo = wx.StaticBitmap(self.main_panel, -1, bitmap_setup(WIZARD_IMAGE_PATH+'pipe_200x90.png'))

        # Pack the logo.
        box.Add(logo, 0, wx.ALIGN_CENTER_HORIZONTAL, 0)


    def add_table(self, sizer):
        """Add the table to the sizer.

        @param sizer:   The sizer element to pack the table into.
        @type sizer:    wx.Sizer instance
        """

        # Grid of all data pipes.
        self.grid = wx.grid.Grid(self.main_panel, -1)

        # Initialise to a single row and 5 columns.
        self.grid.CreateGrid(1, 5)

        # Set the headers.
        self.grid.SetColLabelValue(0, "Data pipe")
        self.grid.SetColLabelValue(1, "Type")
        self.grid.SetColLabelValue(2, "Bundle")
        self.grid.SetColLabelValue(3, "Current")
        self.grid.SetColLabelValue(4, "Analysis tab")

        # Properties.
        self.grid.SetDefaultCellFont(font.normal)
        self.grid.SetLabelFont(font.normal_bold)

        # Set the row label widths.
        self.grid.SetRowLabelSize(self.width_col_label)

        # No cell resizing allowed.
        self.grid.EnableDragColSize(False)
        self.grid.EnableDragRowSize(False)

        # Add grid to sizer.
        sizer.Add(self.grid, 1, wx.ALL|wx.EXPAND, 0)


    def associate_auto(self, event):
        """Associate the selected data pipe with a new auto-analysis.

        @param event:   The wx event.
        @type event:    wx event
        """

        # Initialise the GUI data store object if needed.
        if not hasattr(ds, 'relax_gui'):
            self.gui.init_data()

        # The type and data pipe bundle.
        type = get_type(self.selected_pipe)
        bundle = get_bundle(self.selected_pipe)

        # Error checking.
        if self.selected_pipe == None:
            raise RelaxError("No data pipe has been selected - this is not possible.")
        if bundle == None:
            raise RelaxError("The selected data pipe is not associated with a data pipe bundle.")

        # The name.
        names = {
            'noe': 'Steady-state NOE',
            'r1': 'R1 relaxation',
            'r2': 'R2 relaxation',
            'mf': 'Model-free',
            'relax_disp': 'Relaxation dispersion'
        }

        # Create a new analysis with the selected data pipe.
        self.gui.analysis.new_analysis(analysis_type=type, analysis_name=names[type], pipe_name=self.selected_pipe, pipe_bundle=bundle)


    def handler_close(self, event):
        """Event handler for the close window action.

        @param event:   The wx event.
        @type event:    wx event
        """

        # Unregister the methods from the observers to avoid unnecessary updating.
        self.observer_setup(register=False)

        # Close the window.
        self.Hide()


    def observer_setup(self, register=True):
        """Register and unregister with the observer objects.

        @keyword register:  A flag which if True will register with the observers and if False will unregister all methods.
        @type register:     bool
        """

        # Register the methods with the observers.
        if register:
            status.observers.pipe_alteration.register(self.name, self.update_grid, method_name='update_grid')
            status.observers.gui_analysis.register(self.name, self.update_grid, method_name='update_grid')
            status.observers.exec_lock.register(self.name, self.activate, method_name='activate')

        # Unregister the methods.
        else:
            status.observers.pipe_alteration.unregister(self.name)
            status.observers.gui_analysis.unregister(self.name)
            status.observers.exec_lock.unregister(self.name)


    def pipe_bundle(self, event):
        """Bundle the date pipe.

        @param event:   The wx event.
        @type event:    wx event
        """

        # Bundle the data pipe.
        uf_store['pipe.bundle'](event, wx_parent=self, pipe=self.selected_pipe)


    def pipe_delete(self, event):
        """Delete the date pipe.

        @param event:   The wx event.
        @type event:    wx event
        """

        # Ask if this should be done.
        msg = "Are you sure you would like to delete the '%s' data pipe?  This operation cannot be undone." % self.selected_pipe
        if status.show_gui and Question(msg, parent=self, default=False).ShowModal() == wx.ID_NO:
            return

        # Delete the data pipe.
        delete(self.selected_pipe)


    def pipe_switch(self, event):
        """Switch to the selected date pipe.

        @param event:   The wx event.
        @type event:    wx event
        """

        # Switch to the selected data pipe.
        switch(self.selected_pipe)

        # Bug fix for MS Windows.
        wx.CallAfter(self.Raise)


    def resize(self, event):
        """Catch the resize to allow the grid to be resized.

        @param event:   The wx event.
        @type event:    wx event
        """

        # Set the column sizes.
        self.size_cols()

        # Continue with the normal resizing.
        event.Skip()


    def size_cols(self):
        """Set the column sizes."""

        # The grid size.
        x, y = self.grid.GetSize()

        # Number of columns.
        n = 5

        # The width of the current data pipe column.
        width_col_curr = 80

        # Set to equal sizes.
        width = int((x - self.width_col_label - width_col_curr) / (n - 1))

        # Set the column sizes.
        for i in range(n):
            # The narrower cdp column.
            if i == 3:
                self.grid.SetColSize(i, width_col_curr)

            # All others.
            else:
                self.grid.SetColSize(i, width)


    def update_grid(self):
        """Update the grid in a thread safe way using wx.CallAfter."""

        # Thread safe.
        wx.CallAfter(self.update_grid_safe)

        # Flush the events.
        wx.GetApp().Yield(True)


    def update_grid_safe(self):
        """Update the grid with the pipe data."""

        # First freeze the grid, so that the GUI element doesn't update until the end.
        self.grid.Freeze()

        # Acquire the pipe lock.
        status.pipe_lock.acquire('pipe editor window')

        # Delete the rows, leaving a single row.
        self.grid.DeleteRows(numRows=self.grid.GetNumberRows()-1)

        # Clear the contents of the first row.
        for i in range(self.grid.GetNumberCols()):
            self.grid.SetCellValue(0, i, str_to_gui(""))

        # The data pipes.
        pipe_list = pipe_names()
        n = len(pipe_list)

        # Append the appropriate number of rows.
        if n >= 1:
            self.grid.AppendRows(numRows=n-1)

        # Loop over the data pipes.
        for i in range(n):
            # Set the pipe name.
            self.grid.SetCellValue(i, 0, str_to_gui(pipe_list[i]))

            # Set the pipe type.
            self.grid.SetCellValue(i, 1, str_to_gui(get_type(pipe_list[i])))

            # Set the pipe bundle.
            self.grid.SetCellValue(i, 2, str_to_gui(get_bundle(pipe_list[i])))

            # Set the current pipe.
            if pipe_list[i] == cdp_name():
                self.grid.SetCellValue(i, 3, str_to_gui("cdp"))

            # Set the tab the pipe belongs to.
            self.grid.SetCellValue(i, 4, str_to_gui(self.gui.analysis.page_name_from_bundle(get_bundle(pipe_list[i]))))

        # Set the grid properties once finalised.
        for i in range(self.grid.GetNumberRows()):
            # Row properties.
            self.grid.SetRowSize(i, 27)

            # Loop over the columns.
            for j in range(self.grid.GetNumberCols()):
                # Cell properties.
                self.grid.SetReadOnly(i, j)

        # Release the lock.
        status.pipe_lock.release('pipe editor window')

        # Unfreeze.
        self.grid.Thaw()
