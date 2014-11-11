###############################################################################
#                                                                             #
# Copyright (C) 2007-2014 Edward d'Auvergne                                   #
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
"""The data pipe objects of the relax data store."""

# Python module imports.
from re import match

# relax module imports.
from data_store.align_tensor import AlignTensorList
from data_store.diff_tensor import DiffTensorData
from data_store.exp_info import ExpInfo
from data_store.interatomic import InteratomList
from data_store.mol_res_spin import MoleculeList
from data_store.prototype import Prototype
from lib.errors import RelaxFromXMLNotEmptyError
from lib.structure.internal.object import Internal
from lib.xml import fill_object_contents, node_value_to_python, xml_to_object


class PipeContainer(Prototype):
    """Class containing all the program data."""

    def __init__(self):
        """Set up all the PipeContainer data structures."""

        # The molecule-residue-spin object.
        self.mol = MoleculeList()

        # The interatomic data object.
        self.interatomic = InteratomList()

        # The data pipe type.
        self.pipe_type = None

        # Hybrid models.
        self.hybrid_pipes = []


    def __repr__(self):
        """The string representation of the object.

        Rather than using the standard Python conventions (either the string representation of the
        value or the "<...desc...>" notation), a rich-formatted description of the object is given.
        """

        # Intro text.
        text = "The data pipe storage object.\n"

        # Special objects/methods (to avoid the getattr() function call on).
        spec_obj = ['exp_info', 'mol', 'interatomic', 'diff_tensor', 'structure']

        # Objects.
        text = text + "\n"
        text = text + "Objects:\n"
        for name in dir(self):
            # Molecular list.
            if name == 'mol':
                text = text + "  mol: The molecule list (for the storage of the spin system specific data)\n"

            # Interatomic data list.
            if name == 'interatomic':
                text = text + "  interatomic: The interatomic data list (for the storage of the inter-spin system data)\n"

            # Diffusion tensor.
            if name == 'diff_tensor':
                text = text + "  diff_tensor: The Brownian rotational diffusion tensor data object\n"

            # Molecular structure.
            if name == 'structure':
                text = text + "  structure: The 3D molecular data object\n"

            # The experimental info data container.
            if name == 'exp_info':
                text = text + "  exp_info: The data container for experimental information\n"

            # Skip the PipeContainer methods.
            if name in self.__class__.__dict__:
                continue

            # Skip certain objects.
            if match("^_", name) or name in spec_obj:
                continue

            # Add the object's attribute to the text string.
            text = text + "  " + name + ": " + repr(getattr(self, name)) + "\n"

        # Return the text representation.
        return text


    def _back_compat_hook(self, file_version=None):
        """Method for converting old data structures to the new ones.

        @keyword file_version:  The relax XML version of the XML file.
        @type file_version:     int
        """

        # Relaxation data.
        self._back_compat_hook_ri_data()


    def _back_compat_hook_ri_data(self):
        """Converting the old relaxation data structures to the new ones."""

        # Nothing to do.
        if not (hasattr(cdp, 'frq_labels') and hasattr(cdp, 'noe_r1_table') and hasattr(cdp, 'remap_table')):
            return

        # Initialise the new structures.
        cdp.ri_ids = []
        cdp.ri_type = {}
        frq = {}    # This will be placed into cdp later as cdp.spectrometer_frq still exists.

        # Generate the new structures.
        for i in range(cdp.num_ri):
            # The ID.
            ri_id = "%s_%s" % (cdp.ri_labels[i], cdp.frq_labels[cdp.remap_table[i]])

            # Not unique.
            if ri_id in cdp.ri_ids:
                # Loop until a unique ID is found.
                for j in range(100):
                    # New id.
                    new_id = "%s_%s" % (ri_id, j)

                    # Unique.
                    if not new_id in cdp.ri_ids:
                        ri_id = new_id
                        break

            # Add the ID.
            cdp.ri_ids.append(ri_id)

            # The relaxation data type.
            cdp.ri_type[ri_id] = cdp.ri_labels[i]

            # The frequency data.
            frq[ri_id] = cdp.frq[cdp.remap_table[i]]

        # Delete the old structures.
        del cdp.frq
        del cdp.frq_labels
        del cdp.noe_r1_table
        del cdp.num_frq
        del cdp.num_ri
        del cdp.remap_table
        del cdp.ri_labels

        # Set the frequencies.
        cdp.frq = frq


    def from_xml(self, pipe_node, file_version=None, dir=None):
        """Read a pipe container XML element and place the contents into this pipe.

        @param pipe_node:       The data pipe XML node.
        @type pipe_node:        xml.dom.minidom.Element instance
        @keyword file_version:  The relax XML version of the XML file.
        @type file_version:     int
        @keyword dir:           The name of the directory containing the results file (needed for loading external files).
        @type dir:              str
        """

        # Test if empty.
        if not self.is_empty():
            raise RelaxFromXMLNotEmptyError(self.__class__.__name__)

        # Get the global data node, and fill the contents of the pipe.
        global_node = pipe_node.getElementsByTagName('global')[0]
        xml_to_object(global_node, self, file_version=file_version)

        # Backwards compatibility transformations.
        self._back_compat_hook(file_version)

        # Get the hybrid node (and its sub-node), and recreate the hybrid object.
        hybrid_node = pipe_node.getElementsByTagName('hybrid')[0]
        pipes_node = hybrid_node.getElementsByTagName('pipes')[0]
        setattr(self, 'hybrid_pipes', node_value_to_python(pipes_node.childNodes[0]))

        # Get the experimental information data nodes and, if they exist, fill the contents.
        exp_info_nodes = pipe_node.getElementsByTagName('exp_info')
        if exp_info_nodes:
            # Create the data container.
            self.exp_info = ExpInfo()

            # Fill its contents.
            self.exp_info.from_xml(exp_info_nodes[0], file_version=file_version)

        # Get the diffusion tensor data nodes and, if they exist, fill the contents.
        diff_tensor_nodes = pipe_node.getElementsByTagName('diff_tensor')
        if diff_tensor_nodes:
            # Create the diffusion tensor object.
            self.diff_tensor = DiffTensorData()

            # Fill its contents.
            self.diff_tensor.from_xml(diff_tensor_nodes[0], file_version=file_version)

        # Get the alignment tensor data nodes and, if they exist, fill the contents.
        align_tensor_nodes = pipe_node.getElementsByTagName('align_tensors')
        if align_tensor_nodes:
            # Create the alignment tensor object.
            self.align_tensors = AlignTensorList()

            # Fill its contents.
            self.align_tensors.from_xml(align_tensor_nodes[0], file_version=file_version)

        # Recreate the interatomic data structure (this needs to be before the 'mol' structure as the backward compatibility hooks can create interatomic data containers!).
        interatom_nodes = pipe_node.getElementsByTagName('interatomic')
        self.interatomic.from_xml(interatom_nodes, file_version=file_version)

        # Recreate the molecule, residue, and spin data structure.
        mol_nodes = pipe_node.getElementsByTagName('mol')
        self.mol.from_xml(mol_nodes, file_version=file_version)

        # Get the structural object nodes and, if they exist, fill the contents.
        str_nodes = pipe_node.getElementsByTagName('structure')
        if str_nodes:
            # Create the structural object.
            fail = False
            self.structure = Internal()

            # Fill its contents.
            if not fail:
                self.structure.from_xml(str_nodes[0], dir=dir, file_version=file_version)


    def is_empty(self):
        """Method for testing if the data pipe is empty.

        @return:    True if the data pipe is empty, False otherwise.
        @rtype:     bool
        """

        # Is the molecule structure data object empty?
        if hasattr(self, 'structure'):
            return False

        # Is the molecule/residue/spin data object empty?
        if not self.mol.is_empty():
            return False

        # Is the interatomic data object empty?
        if not self.interatomic.is_empty():
            return False

        # Tests for the initialised data (the pipe type can be set in an empty data pipe, so this isn't checked).
        if self.hybrid_pipes:
            return False

        # An object has been added to the container.
        for name in dir(self):
            # Skip the objects initialised in __init__().
            if name in ['mol', 'interatomic', 'pipe_type', 'hybrid_pipes']:
                continue

            # Skip the PipeContainer methods.
            if name in self.__class__.__dict__:
                continue

            # Skip special objects.
            if match("^_", name):
                continue

            # An object has been added.
            return False

        # The data pipe is empty.
        return True


    def to_xml(self, doc, element, pipe_type=None):
        """Create a XML element for the current data pipe.

        @param doc:         The XML document object.
        @type doc:          xml.dom.minidom.Document instance
        @param element:     The XML element to add the pipe XML element to.
        @type element:      XML element object
        @keyword pipe_type: The type of the pipe being converted to XML.
        @type pipe_type:    str
        """

        # Add all simple python objects within the PipeContainer to the global element.
        global_element = doc.createElement('global')
        element.appendChild(global_element)
        global_element.setAttribute('desc', 'Global data located in the top level of the data pipe')
        fill_object_contents(doc, global_element, object=self, blacklist=['align_tensors', 'diff_tensor', 'exp_info', 'interatomic', 'hybrid_pipes', 'mol', 'pipe_type', 'structure'] + list(self.__class__.__dict__.keys()))

        # Hybrid info.
        self.xml_create_hybrid_element(doc, element)

        # Add the experimental information.
        if hasattr(self, 'exp_info'):
            self.exp_info.to_xml(doc, element)

        # Add the diffusion tensor data.
        if hasattr(self, 'diff_tensor'):
            self.diff_tensor.to_xml(doc, element)

        # Add the alignment tensor data.
        if hasattr(self, 'align_tensors'):
            self.align_tensors.to_xml(doc, element)

        # Add the molecule-residue-spin data.
        self.mol.to_xml(doc, element, pipe_type=pipe_type)

        # Add the interatomic data.
        self.interatomic.to_xml(doc, element, pipe_type=pipe_type)

        # Add the structural data, if it exists.
        if hasattr(self, 'structure'):
            self.structure.to_xml(doc, element)


    def xml_create_hybrid_element(self, doc, element):
        """Create an XML element for the data pipe hybridisation information.

        @param doc:     The XML document object.
        @type doc:      xml.dom.minidom.Document instance
        @param element: The element to add the hybridisation info to.
        @type element:  XML element object
        """

        # Create the hybrid element and add it to the higher level element.
        hybrid_element = doc.createElement('hybrid')
        element.appendChild(hybrid_element)

        # Set the hybridisation attributes.
        hybrid_element.setAttribute('desc', 'Data pipe hybridisation information')

        # Create an element to store the pipes list.
        list_element = doc.createElement('pipes')
        hybrid_element.appendChild(list_element)

        # Add the pipes list.
        text_val = doc.createTextNode(str(self.hybrid_pipes))
        list_element.appendChild(text_val)
