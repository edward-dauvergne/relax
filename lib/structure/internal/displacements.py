###############################################################################
#                                                                             #
# Copyright (C) 2008-2014 Edward d'Auvergne                                   #
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
"""The objects representing displacement information in the internal structural object."""

# relax module import.
from lib.structure.superimpose import kabsch
from lib.structure.internal.models import ModelContainer
from lib.xml import object_to_xml, xml_to_object


class Displacements:
    """A special object for representing rotational and translational displacements between models."""

    def __init__(self):
        """Initialise the storage objects."""

        # The displacement structures.
        self._translation_vector = {}
        self._translation_distance = {}
        self._rotation_matrix = {}
        self._rotation_axis = {}
        self._rotation_angle = {}


    def _calculate(self, id_from=None, id_to=None, coord_from=None, coord_to=None, centroid=None):
        """Calculate the rotational and translational displacements using the given coordinate sets.

        This uses the U{Kabsch algorithm<http://en.wikipedia.org/wiki/Kabsch_algorithm>}.


        @keyword id_from:       The ID string of the starting structure.
        @type id_from:          str
        @keyword id_to:         The ID string of the ending structure.
        @type id_to:            str
        @keyword coord_from:    The list of atomic coordinates for the starting structure.
        @type coord_from:       numpy rank-2, Nx3 array
        @keyword coord_to:      The list of atomic coordinates for the ending structure.
        @type coord_to:         numpy rank-2, Nx3 array
        @keyword centroid:      An alternative position of the centroid, used for studying pivoted systems.
        @type centroid:         list of float or numpy rank-1, 3D array
        """

        # Initialise structures if necessary.
        if not id_from in self._translation_vector:
            self._translation_vector[id_from] = {}
        if not id_from in self._translation_distance:
            self._translation_distance[id_from] = {}
        if not id_from in self._rotation_matrix:
            self._rotation_matrix[id_from] = {}
        if not id_from in self._rotation_axis:
            self._rotation_axis[id_from] = {}
        if not id_from in self._rotation_angle:
            self._rotation_angle[id_from] = {}

        # The Kabsch algorithm.
        trans_vect, trans_dist, R, axis, angle, pivot = kabsch(name_from="'%s'"%id_from, name_to="'%s'"%id_to, coord_from=coord_from, coord_to=coord_to, centroid=centroid)

        # Store the data.
        self._translation_vector[id_from][id_to] = trans_vect
        self._translation_distance[id_from][id_to] = trans_dist
        self._rotation_matrix[id_from][id_to] = R
        self._rotation_axis[id_from][id_to] = axis
        self._rotation_angle[id_from][id_to] = angle


    def from_xml(self, str_node, dir=None, file_version=1):
        """Recreate the structural object from the XML structural object node.

        @param str_node:        The structural object XML node.
        @type str_node:         xml.dom.minicompat.Element instance
        @keyword dir:           The name of the directory containing the results file.
        @type dir:              str
        @keyword file_version:  The relax XML version of the XML file.
        @type file_version:     int
        """

        # Get the pairs of displacements.
        pair_nodes = str_node.getElementsByTagName('pair')

        # Loop over the pairs.
        for pair_node in pair_nodes:
            # Get the two models.
            id_from = str(pair_node.getAttribute('id_from'))
            id_to = str(pair_node.getAttribute('id_to'))

            # Initialise structures if necessary.
            if not id_from in self._translation_vector:
                self._translation_vector[id_from] = {}
            if not id_from in self._translation_distance:
                self._translation_distance[id_from] = {}
            if not id_from in self._rotation_matrix:
                self._rotation_matrix[id_from] = {}
            if not id_from in self._rotation_axis:
                self._rotation_axis[id_from] = {}
            if not id_from in self._rotation_angle:
                self._rotation_angle[id_from] = {}

            # A temporary container to place the Python objects into.
            cont = ModelContainer()

            # Recreate the Python objects.
            xml_to_object(pair_node, cont, file_version=file_version)

            # Repackage the data.
            for name in ['translation_vector', 'translation_distance', 'rotation_matrix', 'rotation_axis', 'rotation_angle']:
                # The objects.
                obj = getattr(self, '_'+name)
                obj_temp = getattr(cont, name)

                # Store.
                obj[id_from][id_to] = obj_temp


    def to_xml(self, doc, element):
        """Create XML elements for each model.

        @param doc:     The XML document object.
        @type doc:      xml.dom.minidom.Document instance
        @param element: The element to add the displacement XML elements to.
        @type element:  XML element object
        """

        # Loop over the starting models.
        start_models = sorted(self._translation_vector.keys())
        for id_from in start_models:
            # Loop over the ending models.
            end_models = sorted(self._translation_vector[id_from].keys())
            for id_to in end_models:
                # Create an XML element for each pair.
                pair_element = doc.createElement('pair')
                element.appendChild(pair_element)

                # Set the attributes.
                pair_element.setAttribute('desc', 'The displacement from model %s to model %s' % (id_from, id_to))
                pair_element.setAttribute('id_from', id_from)
                pair_element.setAttribute('id_to', id_to)

                # The objects to store.
                obj_names = [
                    '_translation_vector',
                    '_translation_distance',
                    '_rotation_matrix',
                    '_rotation_axis',
                    '_rotation_angle'
                ]

                # Store the objects.
                for i in range(len(obj_names)):
                    # Create a new element for this object, and add it to the main element.
                    sub_elem = doc.createElement(obj_names[i][1:])
                    pair_element.appendChild(sub_elem)

                    # Get the sub-object.
                    subobj = getattr(self, obj_names[i])[id_from][id_to]

                    # Add the value to the sub element.
                    object_to_xml(doc, sub_elem, value=subobj)
