###############################################################################
#                                                                             #
# Copyright (C) 2009-2011 Michael Bieri                                       #
# Copyright (C) 2010-2013 Edward d'Auvergne                                   #
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
"""Module containing the base class for the automatic R1 and R2 analysis frames."""

# Python module imports.
from os import sep
import sys
import wx

# relax module imports.
from auto_analyses.relax_fit import Relax_fit
from data_store import Relax_data_store; ds = Relax_data_store()
from pipe_control.mol_res_spin import are_spins_named, exists_mol_res_spin_data
from pipe_control.pipes import has_bundle, has_pipe
from status import Status; status = Status()

# relax GUI module imports.
from gui.analyses.base import Base_analysis, Spectral_error_type_page
from gui.analyses.elements.spin_element import Spin_ctrl
from gui.analyses.elements.text_element import Text_ctrl
from gui.analyses.execute import Execute
from gui.base_classes import Container
from gui.components.spectrum import Spectra_list
from gui.filedialog import RelaxDirDialog
from gui.message import error_message, Missing_data, Question
from gui.misc import protected_exec
from gui import paths
from gui.string_conv import gui_to_int, gui_to_str, int_to_gui, str_to_gui
from gui.uf_objects import Uf_storage; uf_store = Uf_storage()
from gui.wizard import Wiz_window



class Auto_rx(Base_analysis):
    """The base class for the R1 and R2 frames."""

    # Hardcoded variables.
    analysis_type = None
    bitmap = None
    label = None

    def __init__(self, parent, id=-1, pos=wx.Point(-1, -1), size=wx.Size(-1, -1), style=524288, name='scrolledpanel', gui=None, analysis_name=None, pipe_name=None, pipe_bundle=None, uf_exec=[], data_index=None):
        """Build the automatic R1 and R2 analysis GUI frame elements.

        @param parent:          The parent wx element.
        @type parent:           wx object
        @keyword id:            The unique ID number.
        @type id:               int
        @keyword pos:           The position.
        @type pos:              wx.Size object
        @keyword size:          The size.
        @type size:             wx.Size object
        @keyword style:         The style.
        @type style:            int
        @keyword name:          The name for the panel.
        @type name:             unicode
        @keyword gui:           The main GUI class.
        @type gui:              gui.relax_gui.Main instance
        @keyword analysis_name: The name of the analysis (the name in the tab part of the notebook).
        @type analysis_name:    str
        @keyword pipe_name:     The name of the data pipe associated with this analysis.
        @type pipe_name:        str
        @keyword pipe_bundle:   The name of the data pipe bundle associated with this analysis.
        @type pipe_bundle:      str
        @keyword uf_exec:       The list of user function on_execute methods returned from the new analysis wizard.
        @type uf_exec:          list of methods
        @keyword data_index:    The index of the analysis in the relax data store (set to None if no data currently exists).
        @type data_index:       None or int
        """

        # Store the GUI main class.
        self.gui = gui

        # Init.
        self.init_flag = True

        # New data container.
        if data_index == None:
            # First create the data pipe if not already in existence.
            if not has_pipe(pipe_name):
                self.gui.interpreter.apply('pipe.create', pipe_name=pipe_name, pipe_type='relax_fit', bundle=pipe_bundle)

            # Create the data pipe bundle if needed.
            if not has_bundle(pipe_bundle):
                self.gui.interpreter.apply('pipe.bundle', bundle=pipe_bundle, pipe=pipe_name)

            # Generate a storage container in the relax data store, and alias it for easy access.
            data_index = ds.relax_gui.analyses.add(self.label)

            # Store the analysis and pipe names.
            ds.relax_gui.analyses[data_index].analysis_name = analysis_name
            ds.relax_gui.analyses[data_index].pipe_name = pipe_name
            ds.relax_gui.analyses[data_index].pipe_bundle = pipe_bundle

            # Initialise the variables.
            ds.relax_gui.analyses[data_index].frq = ''
            ds.relax_gui.analyses[data_index].grid_inc = None
            ds.relax_gui.analyses[data_index].mc_sim_num = None
            ds.relax_gui.analyses[data_index].save_dir = self.gui.launch_dir

        # Alias the data.
        self.data = ds.relax_gui.analyses[data_index]
        self.data_index = data_index

        # Register the method for updating the spin count for the completion of user functions.
        self.observer_register()

        # Execute the base class method to build the panel.
        super(Auto_rx, self).__init__(parent, id=id, pos=pos, size=size, style=style, name=name)


    def activate(self):
        """Activate or deactivate certain elements of the analysis in response to the execution lock."""

        # Flag for enabling or disabling the elements.
        enable = False
        if not status.exec_lock.locked():
            enable = True

        # Activate or deactivate the elements.
        wx.CallAfter(self.field_nmr_frq.Enable, enable)
        wx.CallAfter(self.field_results_dir.Enable, enable)
        wx.CallAfter(self.spin_systems.Enable, enable)
        wx.CallAfter(self.peak_intensity.Enable, enable)
        wx.CallAfter(self.grid_inc.Enable, enable)
        wx.CallAfter(self.mc_sim_num.Enable, enable)
        wx.CallAfter(self.button_exec_relax.Enable, enable)


    def assemble_data(self):
        """Assemble the data required for the auto-analysis.

        See the docstring for auto_analyses.relax_fit for details.  All data is taken from the relax data store, so data upload from the GUI to there must have been previously performed.

        @return:    A container with all the data required for the auto-analysis.
        @rtype:     class instance, list of str
        """

        # The data container.
        data = Container()
        missing = []

        # The pipe name and bundle.
        data.pipe_name = self.data.pipe_name
        data.pipe_bundle = self.data.pipe_bundle

        # The frequency.
        frq = gui_to_str(self.field_nmr_frq.GetValue())
        if frq == None:
            missing.append('NMR frequency')

        # File root.
        data.file_root = '%s.%s' % (self.analysis_type, frq)

        # Check if sequence data is loaded
        if not exists_mol_res_spin_data():
            missing.append("Sequence data")

        # Spectral data.
        if not hasattr(cdp, 'spectrum_ids') or len(cdp.spectrum_ids) < 3:
            missing.append("Spectral data")

        # Increment size.
        data.inc = gui_to_int(self.grid_inc.GetValue())

        # The number of Monte Carlo simulations to be used for error analysis at the end of the analysis.
        data.mc_sim_num = gui_to_int(self.mc_sim_num.GetValue())

        # Results directory.
        data.save_dir = self.data.save_dir

        # Return the container and list of missing data.
        return data, missing


    def build_right_box(self):
        """Construct the right hand box to pack into the main Rx box.

        @return:    The right hand box element containing all Rx GUI elements (excluding the bitmap) to pack into the main Rx box.
        @rtype:     wx.BoxSizer instance
        """

        # Use a vertical packing of elements.
        box = wx.BoxSizer(wx.VERTICAL)

        # Add the frame title.
        self.add_title(box, "Setup for %s relaxation analysis" % self.label)

        # Display the data pipe.
        Text_ctrl(box, self, text="The data pipe bundle:", default=self.data.pipe_bundle, tooltip="This is the data pipe bundle associated with this analysis.", editable=False, width_text=self.width_text, width_button=self.width_button, spacer=self.spacer_horizontal)

        # Add the frequency selection GUI element.
        self.field_nmr_frq = Text_ctrl(box, self, text="NMR frequency label [MHz]:", default=self.data.frq, tooltip="This label is added to the output files.  For example if the label is '600', the %s values will be located in the file '%s.600.out'." % (self.label, self.label.lower()), width_text=self.width_text, width_button=self.width_button, spacer=self.spacer_horizontal)

        # Add the results directory GUI element.
        self.field_results_dir = Text_ctrl(box, self, text="Results directory:", icon=paths.icon_16x16.open_folder, default=self.data.save_dir, tooltip="The directory in which all automatically created files will be saved.", tooltip_button="Select the results directory.", fn=self.results_directory, button=True, width_text=self.width_text, width_button=self.width_button, spacer=self.spacer_horizontal)

        # Add the spin GUI element.
        self.add_spin_systems(box, self)

        # Add the peak list selection GUI element, with spacing.
        box.AddSpacer(20)
        self.peak_intensity = Spectra_list(gui=self.gui, parent=self, box=box, id=str(self.data_index), fn_add=self.peak_wizard, relax_times=True)
        box.AddSpacer(10)

        # The optimisation settings.
        self.grid_inc = Spin_ctrl(box, self, text="Grid search increments:", default=21, min=1, max=100, tooltip="This is the number of increments per dimension of the grid search performed prior to numerical optimisation.", width_text=self.width_text, width_button=self.width_button, spacer=self.spacer_horizontal)
        self.mc_sim_num = Spin_ctrl(box, self, text="Monte Carlo simulation number:", default=500, min=1, max=100000, tooltip="This is the number of Monte Carlo simulations performed for error propagation and analysis.  For best results, at least 500 is recommended.", width_text=self.width_text, width_button=self.width_button, spacer=self.spacer_horizontal)

        # Stretchable spacing (with a minimal space).
        box.AddSpacer(30)
        box.AddStretchSpacer()

        # Add the execution GUI element.
        self.button_exec_relax = self.add_execute_relax(box, self.execute)

        # Return the box.
        return box


    def delete(self):
        """Unregister the spin count from the user functions."""

        # Unregister the observer methods.
        self.observer_register(remove=True)

        # Clean up the peak intensity object.
        self.peak_intensity.delete()


    def execute(self, event):
        """Set up, execute, and process the automatic Rx analysis.

        @param event:   The wx event.
        @type event:    wx event
        """

        # Flush the GUI interpreter internal queue to make sure all user functions are complete.
        self.gui.interpreter.flush()

        # relax execution lock.
        if status.exec_lock.locked():
            error_message("relax is currently executing.", "relax execution lock")
            event.Skip()
            return

        # User warning to close windows.
        self.gui.close_windows()

        # Synchronise the frame data to the relax data store.
        self.sync_ds(upload=True)

        # Assemble all the data needed for the auto-analysis.
        data, missing = self.assemble_data()

        # Missing data.
        if len(missing):
            Missing_data(missing)
            return

        # Display the relax controller, and go to the end of the log window.
        self.gui.show_controller(None)
        self.gui.controller.log_panel.on_goto_end(None)

        # Start the thread.
        self.thread = Execute_rx(self.gui, data, self.data_index)
        self.thread.start()

        # Terminate the event.
        event.Skip()


    def observer_register(self, remove=False):
        """Register and unregister methods with the observer objects.

        @keyword remove:    If set to True, then the methods will be unregistered.
        @type remove:       False
        """

        # Register.
        if not remove:
            status.observers.gui_uf.register(self.data.pipe_bundle, self.update_spin_count, method_name='update_spin_count')
            status.observers.exec_lock.register(self.data.pipe_bundle, self.activate, method_name='activate')

        # Unregister.
        else:
            # The model-free methods.
            status.observers.gui_uf.unregister(self.data.pipe_bundle)
            status.observers.exec_lock.unregister(self.data.pipe_bundle)

            # The embedded objects methods.
            self.peak_intensity.observer_register(remove=True)


    def peak_wizard(self, event):
        """Launch the Rx peak loading wizard.

        @param event:   The wx event.
        @type event:    wx event
        """

        # Change the cursor to busy.
        wx.BeginBusyCursor()

        # Initialise a wizard.
        self.wizard = Wiz_window(parent=self.gui, size_x=1000, size_y=750, title="Set up the %s peak intensities" % self.label)
        self.page_indices = {}

        # First check that at least a single spin is named!
        if not are_spins_named():
            # The message.
            msg = "No spins have been named.  Please use the spin.name user function first, otherwise it is unlikely that any data will be loaded from the peak intensity file.\n\nThis message can be ignored if the generic file format is used and spin names have not been specified.  Would you like to name the spins already loaded into the relax data store?"

            # Ask about naming spins, and add the spin.name user function page.
            if status.show_gui and Question(msg, title="Incomplete setup", size=(450, 250), default=True).ShowModal() == wx.ID_YES:
                page = uf_store['spin.name'].create_page(self.wizard, sync=True)
                self.page_indices['read'] = self.wizard.add_page(page, proceed_on_error=False)


        # The spectrum.read_intensities page.
        self.page_intensity = uf_store['spectrum.read_intensities'].create_page(self.wizard, sync=True)
        self.page_indices['read'] = self.wizard.add_page(self.page_intensity, skip_button=True, proceed_on_error=False)

        # Error type selection page.
        self.page_error_type = Spectral_error_type_page(parent=self.wizard, height_desc=520)
        self.page_indices['err_type'] = self.wizard.add_page(self.page_error_type, apply_button=False)
        self.wizard.set_seq_next_fn(self.page_indices['err_type'], self.wizard_page_after_error_type)

        # The spectrum.replicated page.
        page = uf_store['spectrum.replicated'].create_page(self.wizard, sync=True)
        self.page_indices['repl'] = self.wizard.add_page(page, skip_button=True, proceed_on_error=False)
        self.wizard.set_seq_next_fn(self.page_indices['repl'], self.wizard_page_after_repl)
        page.on_init = self.wizard_update_repl

        # The spectrum.baseplane_rmsd page.
        page = uf_store['spectrum.baseplane_rmsd'].create_page(self.wizard, sync=True)
        self.page_indices['rmsd'] = self.wizard.add_page(page, skip_button=True, proceed_on_error=False)
        self.wizard.set_seq_next_fn(self.page_indices['rmsd'], self.wizard_page_after_rmsd)
        page.on_init = self.wizard_update_rmsd

        # The spectrum.integration_points page.
        page = uf_store['spectrum.integration_points'].create_page(self.wizard, sync=True)
        self.page_indices['pts'] = self.wizard.add_page(page, skip_button=True, proceed_on_error=False)
        page.on_init = self.wizard_update_pts

        # The relax_fit.relax_time page.
        page = uf_store['relax_fit.relax_time'].create_page(self.wizard, sync=True)
        self.page_indices['relax_time'] = self.wizard.add_page(page, skip_button=False, proceed_on_error=False)
        page.on_init = self.wizard_update_relax_time

        # Reset the cursor.
        if wx.IsBusy():
            wx.EndBusyCursor()

        # Run the wizard.
        self.wizard.run()


    def results_directory(self, event):
        """The results directory selection.

        @param event:   The wx event.
        @type event:    wx event
        """

        # The dialog.
        dialog = RelaxDirDialog(parent=self, message='Select the results directory', defaultPath=self.field_results_dir.GetValue())

        # Show the dialog and catch if no file has been selected.
        if status.show_gui and dialog.ShowModal() != wx.ID_OK:
            # Don't do anything.
            return

        # The path (don't do anything if not set).
        path = gui_to_str(dialog.get_path())
        if not path:
            return

        # Store the path.
        self.data.save_dir = path

        # Place the path in the text box.
        self.field_results_dir.SetValue(str_to_gui(path))


    def sync_ds(self, upload=False):
        """Synchronise the analysis frame and the relax data store, both ways.

        This method allows the frame information to be uploaded into the relax data store, or for the information in the relax data store to be downloaded by the frame.

        @keyword upload:    A flag which if True will cause the frame to send data to the relax data store.  If False, data will be downloaded from the relax data store to update the frame.
        @type upload:       bool
        """

        # The frequency.
        if upload:
            self.data.frq = gui_to_str(self.field_nmr_frq.GetValue())
        else:
            self.field_nmr_frq.SetValue(str_to_gui(self.data.frq))

        # The grid incs.
        if upload:
            self.data.grid_inc = gui_to_int(self.grid_inc.GetValue())
        elif hasattr(self.data, 'grid_inc'):
            self.grid_inc.SetValue(int(self.data.grid_inc))

        # The MC sim number.
        if upload:
            self.data.mc_sim_num = gui_to_int(self.mc_sim_num.GetValue())
        elif hasattr(self.data, 'mc_sim_num'):
            self.mc_sim_num.SetValue(int(self.data.mc_sim_num))

        # The results directory.
        if upload:
            self.data.save_dir = gui_to_str(self.field_results_dir.GetValue())
        else:
            self.field_results_dir.SetValue(str_to_gui(self.data.save_dir))


    def wizard_page_after_error_type(self):
        """Set the page after the error type choice.

        @return:    The index of the next page, which is the current page index plus one.
        @rtype:     int
        """

        # Go to the spectrum.baseplane_rmsd page.
        if self.page_error_type.selection == 'rmsd':
            return self.page_indices['rmsd']

        # Go to the spectrum.replicated page.
        elif self.page_error_type.selection == 'repl':
            return self.page_indices['repl']


    def wizard_page_after_repl(self):
        """Set the page that comes after the spectrum.replicated page.

        @return:    The index of the next page.
        @rtype:     int
        """

        # Go to the spectrum.integration_points page.
        int_method = gui_to_str(self.page_intensity.uf_args['int_method'].GetValue())
        if int_method != 'height':
            return self.page_indices['pts']

        # Skip to the relax_fit.relax_time page.
        else:
            return self.page_indices['relax_time']


    def wizard_page_after_rmsd(self):
        """Set the page that comes after the spectrum.baseplane_rmsd page.

        @return:    The index of the next page.
        @rtype:     int
        """

        # Go to the spectrum.integration_points page.
        int_method = gui_to_str(self.page_intensity.uf_args['int_method'].GetValue())
        if int_method != 'height':
            return self.page_indices['pts']

        # Skip to the relax_fit.relax_time page.
        else:
            return self.page_indices['relax_time']


    def wizard_update_pts(self):
        """Update the spectrum.replicated page based on previous data."""

        # The spectrum.read_intensities page.
        page = self.wizard.get_page(self.page_indices['read'])

        # Set the spectrum ID.
        id = page.uf_args['spectrum_id'].GetValue()

        # Set the ID in the spectrum.replicated page.
        page = self.wizard.get_page(self.page_indices['pts'])
        page.uf_args['spectrum_id'].SetValue(id)


    def wizard_update_repl(self):
        """Update the spectrum.replicated page based on previous data."""

        # The spectrum.read_intensities page.
        page = self.wizard.get_page(self.page_indices['read'])

        # Set the spectrum ID.
        id = page.uf_args['spectrum_id'].GetValue()

        # Set the ID in the spectrum.replicated page.
        page = self.wizard.get_page(self.page_indices['repl'])
        page.uf_args['spectrum_ids'].SetValue(value=id, index=0)


    def wizard_update_rmsd(self):
        """Update the spectrum.baseplane_rmsd page based on previous data."""

        # The spectrum.read_intensities page.
        page = self.wizard.get_page(self.page_indices['read'])

        # Set the spectrum ID.
        id = page.uf_args['spectrum_id'].GetValue()

        # Set the ID in the spectrum.baseplane_rmsd page.
        page = self.wizard.get_page(self.page_indices['rmsd'])
        page.uf_args['spectrum_id'].SetValue(id)


    def wizard_update_relax_time(self):
        """Update the relax_fit.relax_time page based on previous data."""

        # The spectrum.read_intensities page.
        page = self.wizard.get_page(self.page_indices['read'])

        # Set the spectrum ID.
        id = page.uf_args['spectrum_id'].GetValue()

        # Set the ID in the relax_fit.relax_time page.
        page = self.wizard.get_page(self.page_indices['relax_time'])
        page.uf_args['spectrum_id'].SetValue(id)



class Execute_rx(Execute):
    """The Rx analysis execution object."""

    def run_analysis(self):
        """Execute the calculation."""

        # Execute.
        Relax_fit(pipe_name=self.data.pipe_name, pipe_bundle=self.data.pipe_bundle, file_root=self.data.file_root, results_dir=self.data.save_dir, grid_inc=self.data.inc, mc_sim_num=self.data.mc_sim_num, view_plots=False)

        # Alias the relax data store data.
        data = ds.relax_gui.analyses[self.data_index]
