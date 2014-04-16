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
"""The molecule-residue-spin containers of the relax data store."""

# Python module imports.
from re import match

# relax module imports.
from data_store.prototype import Prototype
from lib.errors import RelaxError, RelaxFromXMLNotEmptyError, RelaxImplementError
from lib.xml import fill_object_contents, object_to_xml, xml_to_object
import specific_analyses


# The spin system data.
#######################

class SpinContainer(Prototype):
    """Class containing all the spin system specific data."""

    def __init__(self, spin_name=None, spin_num=None, select=True):
        """Set up the default objects of the spin system data container."""

        # The spin system name and number.
        self.name = spin_name
        self.num = spin_num
        self.select = select

        # The private metadata.
        self._mol_name = None
        self._mol_index = None
        self._res_name = None
        self._res_num = None
        self._res_index = None
        self._spin_index = None
        self._spin_ids = []


    def __repr__(self):
        """The string representation of the object.

        Rather than using the standard Python conventions (either the string representation of the
        value or the "<...desc...>" notation), a rich-formatted description of the object is given.
        """

        # Intro.
        text = "Class containing all the spin system specific data.\n\n"

        # Objects.
        text = text + "\n"
        text = text + "Objects:\n"
        for name in dir(self):
            # Skip the SpinContainer methods.
            if name == 'is_empty':
                continue

            # Skip special objects.
            if match("^_", name):
                continue

            # Add the object's attribute to the text string.
            text = text + "  " + name + ": " + repr(getattr(self, name)) + "\n"

        return text


    def _back_compat_hook(self, file_version=None):
        """Method for converting old spin data structures to the new ones.

        @keyword file_version:  The relax XML version of the XML file.
        @type file_version:     int
        """

        # Model-free parameters.
        if hasattr(self, 'equation') and self.equation in ['mf_orig', 'mf_ext', 'mf_ext2']:
            self._back_compat_hook_mf_data()

        # Relaxation data.
        self._back_compat_hook_ri_data()


    def _back_compat_hook_mf_data(self):
        """Converting the old model-free parameter vector to the new one."""

        # Nothing to do.
        if not hasattr(self, 'params'):
            return

        # Loop over the parameters, converting them to lowercase.
        for i in range(len(self.params)):
            self.params[i] = self.params[i].lower()


    def _back_compat_hook_ri_data(self):
        """Converting the old spin relaxation data structures to the new ones."""

        # Nothing to do.
        if not (hasattr(self, 'frq_labels') and hasattr(self, 'noe_r1_table') and hasattr(self, 'remap_table')):
            return

        # Initialise the new structures.
        self.ri_data = {}
        self.ri_data_err = {}
        sims = False
        if hasattr(self, 'relax_sim_data'):
            sims = True
            self.ri_data_sim = {}

        # Generate the new structures.
        for i in range(self.num_ri):
            # The ID.
            ri_id = "%s_%s" % (self.ri_labels[i], self.frq_labels[self.remap_table[i]])

            # The relaxation data.
            self.ri_data[ri_id] = self.relax_data[i]
            self.ri_data_err[ri_id] = self.relax_error[i]

            # Simulation data.
            if sims:
                self.ri_data_sim[ri_id] = []
                for j in range(cdp.sim_number):
                    self.ri_data_sim[ri_id].append(self.relax_sim_data[j][i])

        # Delete the old structures.
        del self.frq
        del self.frq_labels
        del self.noe_r1_table
        del self.num_frq
        del self.num_ri
        del self.ri_labels
        del self.remap_table
        del self.relax_data
        del self.relax_error
        if sims:
            del self.relax_sim_data


    def is_empty(self):
        """Method for testing if this SpinContainer object is empty.

        @return:    True if this container is empty and the spin number and name have not been set,
                    False otherwise.
        @rtype:     bool
        """

        # The spin number or spin name has been set.
        if self.num != None or self.name != None:
            return False

        # An object has been added to the container.
        for name in dir(self):
            # Skip the objects initialised in __init__().
            if name == 'num' or name == 'name' or name == 'select':
                continue

            # Skip the SpinContainer methods.
            if name == 'is_empty':
                continue

            # Skip special objects.
            if match("^_", name):
                continue

            # An object has been added.
            return False

        # The SpinContainer is unmodified.
        return True


class SpinList(list):
    """List type data container for spin system specific data."""

    def __init__(self):
        """Set up the first spin system data container."""

        # Add the initial spin system container at index 0.
        self.append(SpinContainer())


    def __repr__(self):
        """The string representation of the object.

        Rather than using the standard Python conventions (either the string representation of the
        value or the "<...desc...>" notation), a rich-formatted description of the object is given.
        """

        # Intro.
        text = "Spin systems.\n\n"

        # Residue data.
        text = text + "%-8s%-8s%-8s%-10s" % ("Index", "Number", "Name", "Selected") + "\n"
        for i in range(len(self)):
            text = text + "%-8i%-8s%-8s%-10s" % (i, repr(self[i].num), self[i].name, self[i].select) + "\n"
        text = text + "\nThese can be accessed by typing 'D.mol[i].res[j].spin[k]', where D is the relax data storage object.\n"

        return text


    def add_item(self, spin_name=None, spin_num=None, select=True):
        """Appending an empty container to the list.

        @keyword spin_name: The name of the new spin.
        @type spin_name:    str or None
        @keyword spin_num:  The number of the new spin.
        @type spin_num:     str or None
        @keyword select:    The selection flag.
        @type select:       bool
        @return:            The new container.
        @rtype:             SpinContainer instance
        """

        # If no spin data exists, replace the empty first spin with this spin.
        if self.is_empty():
            self[0].num = spin_num
            self[0].name = spin_name
            self[0].select = select

            # Return the container.
            return self[0]

        # Otherwise append a new SpinContainer.
        else:
            # Test if the spin number (or name if unnumbered) already exists.
            for i in range(len(self)):
                # Spin number has been supplied.
                if spin_num != None and spin_name != None:
                    if self[i].num == spin_num and self[i].name == spin_name:
                        raise RelaxError("The spin with name '%s' and number '%s' already exists." % (spin_name, spin_num))

                # No spin numbers.
                if spin_num == None and  self[i].name == spin_name:
                    raise RelaxError("The unnumbered spin name '%s' already exists." % spin_name)

            # Append a new SpinContainer.
            self.append(SpinContainer(spin_name, spin_num, select))

            # Return the container.
            return self[-1]


    def is_empty(self):
        """Method for testing if this SpinList object is empty.

        @return:    True if this list only has one SpinContainer and the spin number and name have
                    not been set, False otherwise.
        @rtype:     bool
        """

        # There is only one SpinContainer and it is empty.
        if len(self) == 1 and self[0].is_empty():
            return True

        # Otherwise.
        return False


    def from_xml(self, spin_nodes, file_version=None):
        """Recreate a spin list data structure from the XML spin nodes.

        @param spin_nodes:      The spin XML nodes.
        @type spin_nodes:       xml.dom.minicompat.NodeList instance
        @keyword file_version:  The relax XML version of the XML file.
        @type file_version:     int
        """

        # Test if empty.
        if not self.is_empty():
            raise RelaxFromXMLNotEmptyError(self.__class__.__name__)

        # Loop over the spins.
        for spin_node in spin_nodes:
            # Get the spin details and add the spin to the SpinList structure.
            name = str(spin_node.getAttribute('name'))
            if name == 'None':
                name = None
            num = eval(spin_node.getAttribute('num'))
            self.add_item(spin_name=name, spin_num=num)

            # Recreate the current spin container.
            xml_to_object(spin_node, self[-1], file_version=file_version)

            # Backwards compatibility transformations.
            self[-1]._back_compat_hook(file_version)


    def to_xml(self, doc, element, pipe_type=None):
        """Create XML elements for each spin.

        @param doc:         The XML document object.
        @type doc:          xml.dom.minidom.Document instance
        @param element:     The element to add the spin XML elements to.
        @type element:      XML element object
        @keyword pipe_type: The type of the pipe being converted to XML.
        @type pipe_type:    str
        """

        # The specific analysis API object.
        api = specific_analyses.api.return_api(analysis_type=pipe_type)

        # Loop over the spins.
        for i in range(len(self)):
            # Create an XML element for this spin and add it to the higher level element.
            spin_element = doc.createElement('spin')
            element.appendChild(spin_element)

            # Set the spin attributes.
            spin_element.setAttribute('desc', 'Spin container')
            spin_element.setAttribute('name', str(self[i].name))
            spin_element.setAttribute('num', str(self[i].num))

            # Get the spin specific object names and loop over them to get their descriptions.
            object_info = []
            try:
                for name in api.data_names(error_names=True, sim_names=True):
                    # Get the description.
                    if hasattr(api, 'return_data_desc'):
                        desc = api.return_data_desc(name)
                    else:
                        desc = None

                    # Append the two.
                    object_info.append([name, desc])
            except RelaxImplementError:
                pass

            # Add the ordered objects.
            blacklist = []
            for name, desc in object_info:
                # Add the name to the blacklist.
                blacklist.append(name)

                # Skip the object if it is missing from the SpinContainer.
                if not hasattr(self[i], name):
                    continue

                # Create a new element for this object, and add it to the main element.
                sub_element = doc.createElement(name)
                spin_element.appendChild(sub_element)

                # Add the object description.
                if desc:
                    sub_element.setAttribute('desc', desc)

                # Get the object.
                object = getattr(self[i], name)

                # Convert to XML.
                object_to_xml(doc, sub_element, value=object)

            # Add all simple python objects within the SpinContainer to the XML element.
            fill_object_contents(doc, spin_element, object=self[i], blacklist=['name', 'num', 'spin'] + blacklist + list(self[i].__class__.__dict__.keys()))



# The residue data.
###################

class ResidueContainer(Prototype):
    """Class containing all the residue specific data."""

    def __init__(self, res_name=None, res_num=None):
        """Set up the default objects of the residue data container."""

        # The residue name and number.
        self.name = res_name
        self.num = res_num

        # The private metadata.
        self._mol_name = None
        self._mol_index = None
        self._res_index = None

        # The empty spin system list.
        self.spin = SpinList()


    def __repr__(self):
        """The string representation of the object.

        Rather than using the standard Python conventions (either the string representation of the
        value or the "<...desc...>" notation), a rich-formatted description of the object is given.
        """

        # Intro.
        text = "Class containing all the residue specific data.\n"

        # Objects.
        text = text + "\n"
        text = text + "Objects:\n"
        for name in dir(self):
            # Spin systems.
            if name == 'spin':
                text = text + "  spin: The list of spin systems of the residues\n"
                continue

            # Skip the ResidueContainer methods.
            if name == 'is_empty':
                continue

            # Skip special objects.
            if match("^_", name):
                continue

            # Add the object's attribute to the text string.
            text = text + "  " + name + ": " + repr(getattr(self, name)) + "\n"

        return text


    def is_empty(self):
        """Method for testing if this ResidueContainer object is empty.

        @return:    True if this container is empty and the residue number and name have not been
                    set, False otherwise.
        @rtype:     bool
        """

        # The residue number or residue name have been set.
        if self.num != None or self.name != None:
            return False

        # An object has been added to the container.
        for name in dir(self):
            # Skip the objects initialised in __init__().
            if name == 'num' or name == 'name' or name == 'spin':
                continue

            # Skip the ResidueContainer methods.
            if name == 'is_empty':
                continue

            # Skip special objects.
            if match("^_", name):
                continue

            # An object has been added.
            return False

        # The spin list is not empty.
        if not self.spin.is_empty():
            return False

        # The ResidueContainer is unmodified.
        return True


class ResidueList(list):
    """List type data container for residue specific data."""

    def __init__(self):
        """Set up the first residue data container."""

        # Add the initial residue container at index 0.
        self.append(ResidueContainer())


    def __repr__(self):
        """The string representation of the object.

        Rather than using the standard Python conventions (either the string representation of the
        value or the "<...desc...>" notation), a rich-formatted description of the object is given.
        """

        # Intro.
        text = "Residues.\n\n"

        # Residue data.
        text = text + "%-8s%-8s%-8s" % ("Index", "Number", "Name") + "\n"
        for i in range(len(self)):
            text = text + "%-8i%-8s%-8s" % (i, repr(self[i].num), self[i].name) + "\n"
        text = text + "\nThese can be accessed by typing 'D.mol[i].res[j]', where D is the relax data storage object.\n"

        return text


    def add_item(self, res_name=None, res_num=None):
        """Append an empty ResidueContainer to the ResidueList."""

        # If no residue data exists, replace the empty first residue with this residue.
        if self.is_empty():
            self[0].num = res_num
            self[0].name = res_name

        # Otherwise append a new ResidueContainer.
        else:
            # Test if the residue number (or name if unnumbered) already exists.
            for i in range(len(self)):
                # Residue number has been supplied.
                if res_num != None:
                    if self[i].num == res_num:
                        raise RelaxError("The residue number '" + repr(res_num) + "' already exists in the sequence.")

                # No residue numbers.
                else:
                    if self[i].name == res_name:
                        raise RelaxError("The unnumbered residue name '" + repr(res_name) + "' already exists.")

            # Append a new ResidueContainer.
            self.append(ResidueContainer(res_name, res_num))


    def is_empty(self):
        """Method for testing if this ResidueList object is empty.

        @return:    True if this list only has one ResidueContainer and the residue number and name
                    have not been set, False otherwise.
        @rtype:     bool
        """

        # There is only one ResidueContainer and it is empty.
        if len(self) == 1 and self[0].is_empty():
            return True

        # Otherwise.
        return False


    def from_xml(self, res_nodes, file_version=None):
        """Recreate a residue list data structure from the XML residue nodes.

        @param res_nodes:       The residue XML nodes.
        @type res_nodes:        xml.dom.minicompat.NodeList instance
        @keyword file_version:  The relax XML version of the XML file.
        @type file_version:     int
        """

        # Test if empty.
        if not self.is_empty():
            raise RelaxFromXMLNotEmptyError(self.__class__.__name__)

        # Loop over the residues.
        for res_node in res_nodes:
            # Get the residue details and add the residue to the ResidueList structure.
            name = str(res_node.getAttribute('name'))
            if name == 'None':
                name = None
            num = eval(res_node.getAttribute('num'))
            self.add_item(res_name=name, res_num=num)

            # Get the spin nodes.
            spin_nodes = res_node.getElementsByTagName('spin')

            # Recreate the spin data structures for the current residue.
            self[-1].spin.from_xml(spin_nodes, file_version=file_version)


    def to_xml(self, doc, element, pipe_type=None):
        """Create XML elements for each residue.

        @param doc:         The XML document object.
        @type doc:          xml.dom.minidom.Document instance
        @param element:     The element to add the residue XML elements to.
        @type element:      XML element object
        @keyword pipe_type: The type of the pipe being converted to XML.
        @type pipe_type:    str
        """

        # Loop over the residues.
        for i in range(len(self)):
            # Create an XML element for this residue and add it to the higher level element.
            res_element = doc.createElement('res')
            element.appendChild(res_element)

            # Set the residue attributes.
            res_element.setAttribute('desc', 'Residue container')
            res_element.setAttribute('name', str(self[i].name))
            res_element.setAttribute('num', str(self[i].num))

            # Add all simple python objects within the ResidueContainer to the XML element.
            fill_object_contents(doc, res_element, object=self[i], blacklist=['name', 'num', 'spin'] + list(self[i].__class__.__dict__.keys()))

            # Add the residue data.
            self[i].spin.to_xml(doc, res_element, pipe_type=pipe_type)



# The molecule data.
###################

class MoleculeContainer(Prototype):
    """Class containing all the molecule specific data."""

    def __init__(self, mol_name=None, mol_type=None):
        """Set up the default objects of the molecule data container."""

        # The name of the molecule, corresponding to that of the structure file if specified.
        self.name = mol_name

        # The type of molecule.
        self.type = mol_type

        # The private metadata.
        self._mol_index = None

        # The empty residue list.
        self.res = ResidueList()


    def __repr__(self):
        """The string representation of the object.

        Rather than using the standard Python conventions (either the string representation of the
        value or the "<...desc...>" notation), a rich-formatted description of the object is given.
        """

        # Intro.
        text = "Class containing all the molecule specific data.\n"

        # Objects.
        text = text + "\n"
        text = text + "Objects:\n"
        for name in dir(self):
            # Residue list.
            if name == 'res':
                text = text + "  res: The list of the residues of the molecule\n"
                continue

            # Skip the MoleculeContainer methods.
            if name == 'is_empty':
                continue

            # Skip special objects.
            if match("^_", name):
                continue

            # Add the object's attribute to the text string.
            text = text + "  " + name + ": " + repr(getattr(self, name)) + "\n"

        return text


    def is_empty(self):
        """Method for testing if this MoleculeContainer object is empty.

        @return:    True if this container is empty and the molecule name has not been set, False
                    otherwise.
        @rtype:     bool
        """

        # The molecule name has been set.
        if self.name != None:
            return False

        # An object has been added to the container.
        for name in dir(self):
            # Skip the objects initialised in __init__().
            if name in ['name', 'res', 'type']:
                continue

            # Skip the MoleculeContainer methods.
            if name == 'is_empty':
                continue

            # Skip special objects.
            if match("^_", name):
                continue

            # An object has been added.
            return False

        # The residue list is not empty.
        if not self.res.is_empty():
            return False

        # The MoleculeContainer is unmodified.
        return True


class MoleculeList(list):
    """List type data container for the molecule specific data."""

    def __init__(self):
        """Set up the first molecule data container."""

        # Add the initial molecule container at index 0.
        self.append(MoleculeContainer())

        # Create a special private lookup table for fast spin accesses.
        self._spin_id_lookup = {}


    def __repr__(self):
        """The string representation of the object.

        Rather than using the standard Python conventions (either the string representation of the
        value or the "<...desc...>" notation), a rich-formatted description of the object is given.
        """

        text = "Molecules.\n\n"
        text = text + "%-8s%-8s" % ("Index", "Name") + "\n"
        for i in range(len(self)):
            text = text + "%-8i%-8s" % (i, self[i].name) + "\n"
        text = text + "\nThese can be accessed by typing 'D.mol[i]', where D is the relax data storage object.\n"
        return text


    def add_item(self, mol_name=None, mol_type=None):
        """Append an empty MoleculeContainer to the MoleculeList."""

        # If no molecule data exists, replace the empty first molecule with this molecule (just a renaming).
        if self.is_empty():
            self[0].name = mol_name
            self[0].type = mol_type

        # Otherwise append an empty MoleculeContainer.
        else:
            # Test if the molecule name already exists.
            for i in range(len(self)):
                if self[i].name == mol_name:
                    raise RelaxError("The molecule '%s' already exists in the sequence." % mol_name)

            # Append an empty MoleculeContainer.
            self.append(MoleculeContainer(mol_name, mol_type))


    def is_empty(self):
        """Method for testing if this MoleculeList object is empty.

        @return:    True if this list only has one MoleculeContainer and the molecule name has not
                    been set, False otherwise.
        @rtype:     bool
        """

        # There is only one MoleculeContainer and it is empty.
        if len(self) == 1 and self[0].is_empty():
            return True

        # Otherwise.
        return False


    def from_xml(self, mol_nodes, file_version=None):
        """Recreate a molecule list data structure from the XML molecule nodes.

        @param mol_nodes:       The molecule XML nodes.
        @type mol_nodes:        xml.dom.minicompat.NodeList instance
        @keyword file_version:  The relax XML version of the XML file.
        @type file_version:     int
        """

        # Test if empty.
        if not self.is_empty():
            raise RelaxFromXMLNotEmptyError(self.__class__.__name__)

        # Loop over the molecules.
        for mol_node in mol_nodes:
            # Get the molecule details and add the molecule to the MoleculeList structure.
            name = str(mol_node.getAttribute('name'))
            if name == 'None':
                name = None
            type = str(mol_node.getAttribute('type'))
            if type == 'None':
                type = None
            self.add_item(mol_name=name, mol_type=type)

            # Get the residue nodes.
            res_nodes = mol_node.getElementsByTagName('res')

            # Recreate the residue data structures for the current molecule.
            self[-1].res.from_xml(res_nodes, file_version=file_version)


    def to_xml(self, doc, element, pipe_type=None):
        """Create XML elements for each molecule.

        @param doc:         The XML document object.
        @type doc:          Xml.dom.minidom.Document instance
        @param element:     The element to add the molecule XML elements to.
        @type element:      XML element object
        @keyword pipe_type: The type of the pipe being converted to XML.
        @type pipe_type:    str
        """

        # Loop over the molecules.
        for i in range(len(self)):
            # Create an XML element for this molecule and add it to the higher level element.
            mol_element = doc.createElement('mol')
            element.appendChild(mol_element)

            # Set the molecule attributes.
            mol_element.setAttribute('desc', 'Molecule container')
            mol_element.setAttribute('name', str(self[i].name))
            mol_element.setAttribute('type', str(self[i].type))

            # Add all simple python objects within the MoleculeContainer to the XML element.
            fill_object_contents(doc, mol_element, object=self[i], blacklist=['name', 'res', 'type'] + list(self[i].__class__.__dict__.keys()))

            # Add the residue data.
            self[i].res.to_xml(doc, mol_element, pipe_type=pipe_type)
