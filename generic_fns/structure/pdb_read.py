###############################################################################
#                                                                             #
# Copyright (C) 2013 Edward d'Auvergne                                        #
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
"""Module for parsing PDB records.

This module currently used the PDB format version 3.30 from July, 2011 U{http://www.wwpdb.org/documentation/format33/v3.3.html}.
"""

# relax module imports.
from lib.errors import RelaxImplementError


def atom(record):
    """Parse the ATOM record.

    The following is the PDB v3.3 documentation U{http://www.wwpdb.org/documentation/format33/sect9.html#ATOM}.

    ATOM
    ====

    Overview
    --------

    The ATOM records present the atomic coordinates for standard amino acids and nucleotides.  They also present the occupancy and temperature factor for each atom.  Non-polymer chemical coordinates use the HETATM record type.  The element symbol is always present on each ATOM record; charge is optional.

    Changes in ATOM/HETATM records result from the standardization atom and residue nomenclature.  This nomenclature is described in the Chemical Component Dictionary (U{ftp://ftp.wwpdb.org/pub/pdb/data/monomers}).


    Record Format
    -------------

    The format is::
     __________________________________________________________________________________________
     |         |              |              |                                                |
     | Columns | Data type    | Field        | Definition                                     |
     |_________|______________|______________|________________________________________________|
     |         |              |              |                                                |
     |  1 -  6 | Record name  | "ATOM"       |                                                |
     |  7 - 11 | Integer      | serial       | Atom serial number.                            |
     | 13 - 16 | Atom         | name         | Atom name.                                     |
     | 17      | Character    | altLoc       | Alternate location indicator.                  |
     | 18 - 20 | Residue name | resName      | Residue name.                                  |
     | 22      | Character    | chainID      | Chain identifier.                              |
     | 23 - 26 | Integer      | resSeq       | Residue sequence number.                       |
     | 27      | AChar        | iCode        | Code for insertion of residues.                |
     | 31 - 38 | Real(8.3)    | x            | Orthogonal coordinates for X in Angstroms.     |
     | 39 - 46 | Real(8.3)    | y            | Orthogonal coordinates for Y in Angstroms.     |
     | 47 - 54 | Real(8.3)    | z            | Orthogonal coordinates for Z in Angstroms.     |
     | 55 - 60 | Real(6.2)    | occupancy    | Occupancy.                                     |
     | 61 - 66 | Real(6.2)    | tempFactor   | Temperature factor.                            |
     | 77 - 78 | LString(2)   | element      | Element symbol, right-justified.               |
     | 79 - 80 | LString(2)   | charge       | Charge on the atom.                            |
     |_________|______________|______________|________________________________________________|


    Details
    -------

    ATOM records for proteins are listed from amino to carboxyl terminus.

    Nucleic acid residues are listed from the 5' to the 3' terminus.

    Alignment of one-letter atom name such as C starts at column 14, while two-letter atom name such as FE starts at column 13.

    Atom nomenclature begins with atom type.

    No ordering is specified for polysaccharides.

    Non-blank alphanumerical character is used for chain identifier.

    The list of ATOM records in a chain is terminated by a TER record.

    If more than one model is present in the entry, each model is delimited by MODEL and ENDMDL records.

    AltLoc is the place holder to indicate alternate conformation.  The alternate conformation can be in the entire polymer chain, or several residues or partial residue (several atoms within one residue).  If an atom is provided in more than one position, then a non-blank alternate location indicator must be used for each of the atomic positions.  Within a residue, all atoms that are associated with each other in a given conformation are assigned the same alternate position indicator.  There are two ways of representing alternate conformation- either at atom level or at residue level (see examples).

    For atoms that are in alternate sites indicated by the alternate site indicator, sorting of atoms in the ATOM/HETATM list uses the following general rules:

      - In the simple case that involves a few atoms or a few residues with alternate sites, the coordinates occur one after the other in the entry.
      - In the case of a large heterogen groups which are disordered, the atoms for each conformer are listed together.

    Alphabet letters are commonly used for insertion code.  The insertion code is used when two residues have the same numbering.  The combination of residue numbering and insertion code defines the unique residue.

    If the depositor provides the data, then the isotropic B value is given for the temperature factor.

    If there are neither isotropic B values from the depositor, nor anisotropic temperature factors in ANISOU, then the default value of 0.0 is used for the temperature factor.

    Columns 79 - 80 indicate any charge on the atom, e.g., 2+, 1-.  In most cases, these are blank.

    For refinements with program REFMAC prior 5.5.0042 which use TLS refinement, the values of B may include only the TLS contribution to the isotropic temperature factor rather than the full isotropic value.


    Verification/Validation/Value Authority Control
    -----------------------------------------------

    The ATOM/HETATM records are checked for PDB file format, sequence information, and packing.


    Relationships to Other Record Types
    -----------------------------------

    The ATOM records are compared to the corresponding sequence database.  Sequence discrepancies appear in the SEQADV record.  Missing atoms are annotated in the remarks.  HETATM records are formatted in the same way as ATOM records.  The sequence implied by ATOM records must be identical to that given in SEQRES, with the exception that residues that have no coordinates, e.g., due to disorder, must appear in SEQRES.


    Example
    -------

    Example 1::

                 1         2         3         4         5         6         7         8
        12345678901234567890123456789012345678901234567890123456789012345678901234567890
        ATOM     32  N  AARG A  -3      11.281  86.699  94.383  0.50 35.88           N  
        ATOM     33  N  BARG A  -3      11.296  86.721  94.521  0.50 35.60           N  
        ATOM     34  CA AARG A  -3      12.353  85.696  94.456  0.50 36.67           C  
        ATOM     35  CA BARG A  -3      12.333  85.862  95.041  0.50 36.42           C  
        ATOM     36  C  AARG A  -3      13.559  86.257  95.222  0.50 37.37           C  
        ATOM     37  C  BARG A  -3      12.759  86.530  96.365  0.50 36.39           C  
        ATOM     38  O  AARG A  -3      13.753  87.471  95.270  0.50 37.74           O  
        ATOM     39  O  BARG A  -3      12.924  87.757  96.420  0.50 37.26           O  
        ATOM     40  CB AARG A  -3      12.774  85.306  93.039  0.50 37.25           C  
        ATOM     41  CB BARG A  -3      13.428  85.746  93.980  0.50 36.60           C  
        ATOM     42  CG AARG A  -3      11.754  84.432  92.321  0.50 38.44           C  
        ATOM     43  CG BARG A  -3      12.866  85.172  92.651  0.50 37.31           C  
        ATOM     44  CD AARG A  -3      11.698  84.678  90.815  0.50 38.51           C  
        ATOM     45  CD BARG A  -3      13.374  85.886  91.406  0.50 37.66           C  
        ATOM     46  NE AARG A  -3      12.984  84.447  90.163  0.50 39.94           N  
        ATOM     47  NE BARG A  -3      12.644  85.487  90.195  0.50 38.24           N  
        ATOM     48  CZ AARG A  -3      13.202  84.534  88.850  0.50 40.03           C  
        ATOM     49  CZ BARG A  -3      13.114  85.582  88.947  0.50 39.55           C  
        ATOM     50  NH1AARG A  -3      12.218  84.840  88.007  0.50 40.76           N  
        ATOM     51  NH1BARG A  -3      14.338  86.056  88.706  0.50 40.23           N  
        ATOM     52  NH2AARG A  -3      14.421  84.308  88.373  0.50 40.45           N  

    Example 2::

                 1         2         3         4         5         6         7         8
        12345678901234567890123456789012345678901234567890123456789012345678901234567890
        ATOM     32  N  AARG A  -3      11.281  86.699  94.383  0.50 35.88           N  
        ATOM     33  CA AARG A  -3      12.353  85.696  94.456  0.50 36.67           C  
        ATOM     34  C  AARG A  -3      13.559  86.257  95.222  0.50 37.37           C  
        ATOM     35  O  AARG A  -3      13.753  87.471  95.270  0.50 37.74           O  
        ATOM     36  CB AARG A  -3      12.774  85.306  93.039  0.50 37.25           C  
        ATOM     37  CG AARG A  -3      11.754  84.432  92.321  0.50 38.44           C  
        ATOM     38  CD AARG A  -3      11.698  84.678  90.815  0.50 38.51           C  
        ATOM     39  NE AARG A  -3      12.984  84.447  90.163  0.50 39.94           N  
        ATOM     40  CZ AARG A  -3      13.202  84.534  88.850  0.50 40.03           C  
        ATOM     41  NH1AARG A  -3      12.218  84.840  88.007  0.50 40.76           N  
        ATOM     42  NH2AARG A  -3      14.421  84.308  88.373  0.50 40.45           N  
        ATOM     43  N  BARG A  -3      11.296  86.721  94.521  0.50 35.60           N  
        ATOM     44  CA BARG A  -3      12.333  85.862  95.041  0.50 36.42           C  
        ATOM     45  C  BARG A  -3      12.759  86.530  96.365  0.50 36.39           C  
        ATOM     46  O  BARG A  -3      12.924  87.757  96.420  0.50 37.26           O  
        ATOM     47  CB BARG A  -3      13.428  85.746  93.980  0.50 36.60           C  
        ATOM     48  CG BARG A  -3      12.866  85.172  92.651  0.50 37.31           C  
        ATOM     49  CD BARG A  -3      13.374  85.886  91.406  0.50 37.66           C  
        ATOM     50  NE BARG A  -3      12.644  85.487  90.195  0.50 38.24           N  
        ATOM     51  CZ BARG A  -3      13.114  85.582  88.947  0.50 39.55           C  
        ATOM     52  NH1BARG A  -3      14.338  86.056  88.706  0.50 40.23           N  


    @param record:          The PDB ATOM record.
    @type record:           str
    @return:                The atom serial number, atom name, alternate location indicator, residue name, chain identifier, sequence number, insertion code, orthogonal coordinates for X in Angstroms, orthogonal coordinates for Y in Angstroms, orthogonal coordinates for Z in Angstroms, occupancy, temperature factor, element symbol, charge on the atom.
    @rtype:                 tuple of int, str, str, str, str, int, str, float, float, float, float, float, str, int
    """

    # Initialise.
    fields = []

    # Split up the record.
    fields.append(record[0:6])
    fields.append(record[6:11])
    fields.append(record[12:16])
    fields.append(record[16])
    fields.append(record[17:20])
    fields.append(record[21])
    fields.append(record[22:26])
    fields.append(record[26])
    fields.append(record[30:38])
    fields.append(record[38:46])
    fields.append(record[46:54])
    fields.append(record[54:60])
    fields.append(record[60:66])
    fields.append(record[76:78])
    fields.append(record[78:80])

    # Loop over the fields.
    for i in range(len(fields)):
        # Strip all whitespace.
        fields[i] = fields[i].strip()

        # Replace nothingness with None.
        if fields[i] == '':
            fields[i] = None

    # Convert strings to numbers.
    if fields[1]:
        fields[1] = int(fields[1])
    if fields[6]:
        fields[6] = int(fields[6])
    if fields[8]:
        fields[8] = float(fields[8])
    if fields[9]:
        fields[9] = float(fields[9])
    if fields[10]:
        fields[10] = float(fields[10])
    if fields[11]:
        fields[11] = float(fields[11])
    if fields[12]:
        fields[12] = float(fields[12])

    # Return the data.
    return tuple(fields)


def conect(record):
    """Parse the CONECT record.

    The following is the PDB v3.3 documentation U{http://www.wwpdb.org/documentation/format33/sect10.html#CONECT}.

    CONECT
    ======

    Overview
    --------

    The CONECT records specify connectivity between atoms for which coordinates are supplied.  The connectivity is described using the atom serial number as shown in the entry.  CONECT records are mandatory for HET groups (excluding water) and for other bonds not specified in the standard residue connectivity table.  These records are generated automatically.

    Record Format
    -------------

    The format is::
     ______________________________________________________________________________________________
     |         |              |              |                                                    |
     | Columns | Data type    | Field        | Definition                                         |
     |_________|______________|______________|____________________________________________________|
     |         |              |              |                                                    |
     |  1 -  6 | Record name  | "CONECT"     |                                                    |
     |  7 - 11 | Integer      | serial       | Atom serial number                                 |
     | 12 - 16 | Integer      | serial       | Serial number of bonded atom                       |
     | 17 - 21 | Integer      | serial       | Serial number of bonded atom                       |
     | 22 - 26 | Integer      | serial       | Serial number of bonded atom                       |
     | 27 - 31 | Integer      | serial       | Serial number of bonded atom                       |
     |_________|______________|______________|____________________________________________________|


    Details
    -------

    CONECT records are present for:

      - Intra-residue connectivity within non-standard (HET) residues (excluding water).
      - Inter-residue connectivity of HET groups to standard groups (including water) or to other HET groups.
      - Disulfide bridges specified in the SSBOND records have corresponding records.

    No differentiation is made between atoms with delocalized charges (excess negative or positive charge).

    Atoms specified in the CONECT records have the same numbers as given in the coordinate section.

    All atoms connected to the atom with serial number in columns 7 - 11 are listed in the remaining fields of the record.

    If more than four fields are required for non-hydrogen and non-salt bridges, a second CONECT record with the same atom serial number in columns 7 - 11 will be used.

    These CONECT records occur in increasing order of the atom serial numbers they carry in columns 7 - 11.  The target-atom serial numbers carried on these records also occur in increasing order.

    The connectivity list given here is redundant in that each bond indicated is given twice, once with each of the two atoms involved specified in columns 7 - 11.

    For hydrogen bonds, when the hydrogen atom is present in the coordinates, a CONECT record between the hydrogen atom and its acceptor atom is generated.

    For NMR entries, CONECT records for one model are generated describing heterogen connectivity and others for LINK records assuming that all models are homogeneous models.


    Verification/Validation/Value Authority Control
    -----------------------------------------------

    Connectivity is checked for unusual bond lengths.


    Relationships to Other Record Types
    -----------------------------------

    CONECT records must be present in an entry that contains either non-standard groups or disulfide bonds.


    Example
    -------

    Example 1::

                 1         2         3         4         5         6         7         8
        12345678901234567890123456789012345678901234567890123456789012345678901234567890
        CONECT 1179  746 1184 1195 1203
        CONECT 1179 1211 1222
        CONECT 1021  544 1017 1020 1022


    Known Problems
    --------------

    CONECT records involving atoms for which the coordinates are not present in the entry (e.g., symmetry-generated) are not given.

    CONECT records involving atoms for which the coordinates are missing due to disorder, are also not provided.


    @param record:          The PDB CONECT record.
    @type record:           str
    @return:                The atom serial number, serial number of the bonded atom 1, serial number of the bonded atom 2, serial number of the bonded atom 3, serial number of the bonded atom 4.
    @rtype:                 tuple of int, int, int, int, int
    """

    # Initialise.
    fields = []

    # Split up the record.
    fields.append(record[0:6])
    fields.append(record[6:11])
    fields.append(record[11:16])
    fields.append(record[16:21])
    fields.append(record[21:26])
    fields.append(record[26:31])

    # Loop over the fields.
    for i in range(len(fields)):
        # Strip all whitespace.
        fields[i] = fields[i].strip()

        # Replace nothingness with None.
        if fields[i] == '':
            fields[i] = None

    # Convert strings to numbers.
    if fields[1]:
        fields[1] = int(fields[1])
    if fields[2]:
        fields[2] = int(fields[2])
    if fields[3]:
        fields[3] = int(fields[3])
    if fields[4]:
        fields[4] = int(fields[4])
    if fields[5]:
        fields[5] = int(fields[5])

    # Return the data.
    return tuple(fields)


def formul(record):
    """Parse the FORMUL record.

    The following is the PDB v3.3 documentation U{http://www.wwpdb.org/documentation/format33/sect4.html#FORMUL}.

    FORMUL
    ======

    Overview
    --------

    The FORMUL record presents the chemical formula and charge of a non-standard group.


    Record Format
    -------------

    The format is::
     ______________________________________________________________________________________________
     |         |              |              |                                                    |
     | Columns | Data type    | Field        | Definition                                         |
     |_________|______________|______________|____________________________________________________|
     |         |              |              |                                                    |
     |  1 -  6 | Record name  | "FORMUL"     |                                                    |
     |  9 - 10 | Integer      | compNum      | Component number.                                  |
     | 13 - 15 | LString(3)   | hetID        | Het identifier.                                    |
     | 17 - 18 | Integer      | continuation | Continuation number.                               |
     | 19      | Character    | asterisk     | "*" for water.                                     |
     | 20 - 70 | String       | text         | Chemical formula.                                  |
     |_________|______________|______________|____________________________________________________|


    Details
    -------

    The elements of the chemical formula are given in the order following Hill ordering.  The order of elements depends on whether carbon is present or not.  If carbon is present, the order should be: C, then H, then the other elements in alphabetical order of their symbol.  If carbon is not present, the elements are listed purely in alphabetic order of their symbol.  This is the 'Hill' system used by Chemical Abstracts.

    The number of each atom type present immediately follows its chemical symbol without an intervening blank space.  There will be no number indicated if there is only one atom for a particular atom type.

    Each set of SEQRES records and each HET group is assigned a component number in an entry.  These numbers are assigned serially, beginning with 1 for the first set of SEQRES records.  In addition:

      - If a HET group is presented on a SEQRES record its FORMUL is assigned the component number of the chain in which it appears.
      - If the HET group occurs more than once and is not presented on SEQRES records, the component number of its first occurrence is used.

    All occurrences of the HET group within a chain are grouped together with a multiplier.  The remaining occurrences are also grouped with a multiplier.  The sum of the multipliers is the number equaling the number of times that that HET group appears in the entry.

    A continuation field is provided in the event that more space is needed for the formula.  Columns 17 - 18 are used in order to maintain continuity with the existing format.


    Verification/Validation/Value Authority Control
    -----------------------------------------------

    For each het group that appears in the entry, the corresponding HET, HETNAM, FORMUL, HETATM, and CONECT records must appear.  The FORMUL record is generated automatically by PDB processing programs using the het group template file and information from HETATM records.  UNL, UNK and UNX will not be listed in FORMUL even though these het groups present in the coordinate section.


    Relationships to Other Record Types
    -----------------------------------

    For each het group that appears in the entry, the corresponding HET, HETNAM, FORMUL, HETATM, and CONECT records must appear.


    Example
    -------

    Example 1::

                 1         2         3         4         5         6         7         8
        12345678901234567890123456789012345678901234567890123456789012345678901234567890
        FORMUL   3   MG    2(MG 2+)
        FORMUL   5  SO4    6(O4 S 2-)
        FORMUL  13  HOH   *360(H2 O)

        FORMUL   3  NAP    2(C21 H28 N7 O17 P3)
        FORMUL   4  FOL    2(C19 H19 N7 O6)
        FORMUL   5  1PE    C10 H22 O6

        FORMUL   2  NX5    C14 H10 O2 CL2 S


    @param record:          The PDB FORMUL record.
    @type record:           str
    @raises RelaxImplementError:    Always.
    """

    # Not implemented yet.
    raise RelaxImplementError('formul')


def helix(record):
    """Parse the HELIX record.

    The following is the PDB v3.3 documentation U{http://www.wwpdb.org/documentation/format33/sect5.html#HELIX}.

    HELIX
    =====

    Overview
    --------

    HELIX records are used to identify the position of helices in the molecule.  Helices are named, numbered, and classified by type.  The residues where the helix begins and ends are noted, as well as the total length.


    Record Format
    -------------

    The format is::
     ______________________________________________________________________________________________
     |         |              |              |                                                    |
     | Columns | Data type    | Field        | Definition                                         |
     |_________|______________|______________|____________________________________________________|
     |         |              |              |                                                    |
     |  1 -  6 | Record name  | "HELIX "     |                                                    |
     |  8 - 10 | Integer      | serNum       | Serial number of the helix.  This starts at 1 and  |
     |         |              |              |      increases incrementally.                      |
     | 12 - 14 | LString(3)   | helixID      | Helix identifier.  In addition to a serial number, |
     |         |              |              |      each helix is given an alphanumeric character |
     |         |              |              |      helix identifier.                             |
     | 16 - 18 | Residue name | initResName  | Name of the initial residue.                       |
     | 20      | Character    | initChainID  | Chain identifier for the chain containing this     |
     |         |              |              |      helix.                                        |
     | 22 - 25 | Integer      | initSeqNum   | Sequence number of the initial residue.            |
     | 26      | AChar        | initICode    | Insertion code of the initial residue.             |
     | 28 - 30 | Residue name | endResName   | Name of the terminal residue of the helix.         |
     | 32      | Character    | endChainID   | Chain identifier for the chain containing this     |
     |         |              |              |      helix.                                        |
     | 34 - 37 | Integer      | endSeqNum    | Sequence number of the terminal residue.           |
     | 38      | AChar        | endICode     | Insertion code of the terminal residue.            |
     | 39 - 40 | Integer      | helixClass   | Helix class (see below).                           |
     | 41 - 70 | String       | comment      | Comment about this helix.                          |
     | 72 - 76 | Integer      | length       | Length of this helix.                              |
     |_________|______________|______________|____________________________________________________|


    Details
    -------

    Additional HELIX records with different serial numbers and identifiers occur if more than one helix is present.

    The initial residue of the helix is the N-terminal residue.

    Helices are classified as follows::

     _____________________________________________________
     |                               |  CLASS NUMBER     |
     | TYPE OF  HELIX                | (COLUMNS 39 - 40) |
     |_______________________________|___________________|
     |                               |                   |
     | Right-handed alpha (default)  |          1        |
     | Right-handed omega            |          2        |
     | Right-handed pi               |          3        |
     | Right-handed gamma            |          4        |
     | Right-handed 3 - 10           |          5        |
     | Left-handed alpha             |          6        |
     | Left-handed omega             |          7        |
     | Left-handed gamma             |          8        |
     | 2 - 7 ribbon/helix            |          9        |
     | Polyproline                   |         10        |
     |_______________________________|___________________|


    Relationships to Other Record Types
    -----------------------------------

    There may be related information in the REMARKs.


    Example
    -------

    Example 1::

                 1         2         3         4         5         6         7         8
        12345678901234567890123456789012345678901234567890123456789012345678901234567890
        HELIX    1  HA GLY A   86  GLY A   94  1                                   9
        HELIX    2  HB GLY B   86  GLY B   94  1                                   9

        HELIX   21  21 PRO J  385  LEU J  388  5                                   4
        HELIX   22  22 PHE J  397  PHE J  402  5                                   6


    @param record:          The PDB HELIX record.
    @type record:           str
    @return:                The record name, helix serial number, helix identifier, name of the initial residue, chain identifier, sequence number of the initial residue, insertion code of the initial residue, name of the terminal residue, chain identifier, sequence number of the terminal residue, insertion code of the terminal residue, helix class, comment, helix length.
    @rtype:                 tuple of str, int, str, str, str, int, str, str, str, int, str, int, str, int
    """

    # Initialise.
    fields = []

    # Split up the record.
    fields.append(record[0:6])
    fields.append(record[7:10])
    fields.append(record[11:14])
    fields.append(record[15:18])
    fields.append(record[19])
    fields.append(record[21:25])
    fields.append(record[25])
    fields.append(record[27:30])
    fields.append(record[31])
    fields.append(record[33:37])
    fields.append(record[37])
    fields.append(record[38:40])
    fields.append(record[40:70])
    fields.append(record[71:76])

    # Loop over the fields.
    for i in range(len(fields)):
        # Strip all whitespace.
        fields[i] = fields[i].strip()

        # Replace nothingness with None.
        if fields[i] == '':
            fields[i] = None

    # Convert strings to numbers.
    if fields[1]:
        fields[1] = int(fields[1])
    if fields[5]:
        fields[5] = int(fields[5])
    if fields[9]:
        fields[9] = int(fields[9])
    if fields[11]:
        fields[11] = int(fields[11])
    if fields[13]:
        fields[13] = int(fields[13])

    # Return the data.
    return tuple(fields)


def het(record):
    """Parse the HET record.

    The following is the PDB v3.3 documentation U{http://www.wwpdb.org/documentation/format33/sect4.html#HET}.

    HET
    ===

    Overview
    --------

    HET records are used to describe non-standard residues, such as prosthetic groups, inhibitors, solvent molecules, and ions for which coordinates are supplied.  Groups are considered HET if they are not part of a biological polymer described in SEQRES and considered to be a molecule bound to the polymer, or they are a chemical species that constitute part of a biological polymer and is not one of the following:

        - standard amino acids, or
        - standard nucleic acids (C, G, A, U, I, DC, DG, DA, DU, DT and DI), or
        - unknown amino acid (UNK) or nucleic acid (N) where UNK and N are used to indicate the unknown residue name.

    HET records also describe chemical components for which the chemical identity is unknown, in which case the group is assigned the hetID UNL (Unknown Ligand).

    The heterogen section of a PDB formatted file contains the complete description of non-standard residues in the entry.


    Record Format
    -------------

    The format is::
     ______________________________________________________________________________________________
     |         |              |              |                                                    |
     | Columns | Data type    | Field        | Definition                                         |
     |_________|______________|______________|____________________________________________________|
     |         |              |              |                                                    |
     |  1 -  6 | Record name  | "HET   "     |                                                    |
     |  8 - 10 | LString(3)   | hetID        | Het identifier, right-justified.                   |
     | 13      | Character    | ChainID      | Chain identifier.                                  |
     | 14 - 17 | Integer      | seqNum       | Sequence number.                                   |
     | 18      | AChar        | iCode        | Insertion code.                                    |
     | 21 - 25 | Integer      | numHetAtoms  | Number of HETATM records for the group present in  |
     |         |              |              | the entry.                                         |
     | 31 - 70 | String       | text         | Text describing Het group.                         |
     |_________|______________|______________|____________________________________________________|


    Details
    -------

    Each HET group is assigned a hetID of not more than three (3) alphanumeric characters.  The sequence number, chain identifier, insertion code, and number of coordinate records are given for each occurrence of the HET group in the entry.  The chemical name of the HET group is given in the HETNAM record and synonyms for the chemical name are given in the HETSYN records, see U{ftp://ftp.wwpdb.org/pub/pdb/data/monomers}.

    There is a separate HET record for each occurrence of the HET group in an entry.

    A particular HET group is represented in the PDB archive with a unique hetID.

    PDB entries do not have HET records for water molecules, deuterated water, or methanol (when used as solvent).

    Unknown atoms or ions will be represented as UNX with the chemical formula X1.  Unknown ligands are UNL; unknown amino acids are UNK.


    Verification/Validation/Value Authority Control
    -----------------------------------------------

    For each het group that appears in the entry, the wwPDB checks that the corresponding HET, HETNAM, HETSYN, FORMUL, HETATM, and CONECT records appear, if applicable.  The HET record is generated automatically using the Chemical Component Dictionary and information from the HETATM records.

    Each unique hetID represents a unique molecule.


    Relationships to Other Record Types
    -----------------------------------

    For each het group that appears in the entry, there must be corresponding HET, HETNAM, HETSYN, FORMUL,HETATM, and CONECT records.  LINK records may also be created.


    Example
    -------

    Example 1::

                 1         2         3         4         5         6         7         8
        12345678901234567890123456789012345678901234567890123456789012345678901234567890
        HET    TRS  B 975       8

        HET    UDP  A1457      25
        HET    B3P  A1458      19

        HET    NAG  Y   3      15
        HET    FUC  Y   4      10
        HET    NON  Y   5      12
        HET    UNK  A 161       1


    @param record:          The PDB HET record.
    @type record:           str
    @raises RelaxImplementError:    Always.
    """

    # Not implemented yet.
    raise RelaxImplementError('het')


def hetatm(record):
    """Parse the HETATM record.

    The following is the PDB v3.3 documentation U{http://www.wwpdb.org/documentation/format33/sect9.html#HETATM}.

    HETATM
    ======

    Overview
    --------

    Non-polymer or other "non-standard" chemical coordinates, such as water molecules or atoms presented in HET groups use the HETATM record type.  They also present the occupancy and temperature factor for each atom.  The ATOM records present the atomic coordinates for standard residues.  The element symbol is always present on each HETATM record; charge is optional.

    Changes in ATOM/HETATM records will require standardization in atom and residue nomenclature.  This nomenclature is described in the Chemical Component Dictionary, U{ftp://ftp.wwpdb.org/pub/pdb/data/monomers}.


    Record Format
    -------------

    The format is::
     ______________________________________________________________________________________________
     |         |              |              |                                                    |
     | Columns | Data type    | Field        | Definition                                         |
     |_________|______________|______________|____________________________________________________|
     |         |              |              |                                                    |
     |  1 -  6 | Record name  | "HETATM"     |                                                    |
     |  7 - 11 | Integer      | serial       | Atom serial number.                                |
     | 13 - 16 | Atom         | name         | Atom name.                                         |
     | 17      | Character    | altLoc       | Alternate location indicator.                      |
     | 18 - 20 | Residue name | resName      | Residue name.                                      |
     | 22      | Character    | chainID      | Chain identifier.                                  |
     | 23 - 26 | Integer      | resSeq       | Residue sequence number.                           |
     | 27      | AChar        | iCode        | Code for insertion of residues.                    |
     | 31 - 38 | Real(8.3)    | x            | Orthogonal coordinates for X.                      |
     | 39 - 46 | Real(8.3)    | y            | Orthogonal coordinates for Y.                      |
     | 47 - 54 | Real(8.3)    | z            | Orthogonal coordinates for Z.                      |
     | 55 - 60 | Real(6.2)    | occupancy    | Occupancy.                                         |
     | 61 - 66 | Real(6.2)    | tempFactor   | Temperature factor.                                |
     | 77 - 78 | LString(2)   | element      | Element symbol; right-justified.                   |
     | 79 - 80 | LString(2)   | charge       | Charge on the atom.                                |
     |_________|______________|______________|____________________________________________________|


    Details
    -------

    The x, y, z coordinates are in Angstrom units.

    No ordering is specified for polysaccharides.

    See the HET section of this document regarding naming of heterogens.  See the Chemical Component Dictionary for residue names, formulas, and topology of the HET groups that have appeared so far in the PDB (see U{ftp://ftp.wwpdb.org/pub/pdb/data/monomers}).

    If the depositor provides the data, then the isotropic B value is given for the temperature factor.

    If there are neither isotropic B values provided by the depositor, nor anisotropic temperature factors in ANISOU, then the default value of 0.0 is used for the temperature factor.

    Insertion codes and element naming are fully described in the ATOM section of this document.


    Verification/Validation/Value Authority Control
    -----------------------------------------------

    Processing programs check ATOM/HETATM records for PDB file format, sequence information, and packing.


    Relationships to Other Record Types
    -----------------------------------

    HETATM records must have corresponding HET, HETNAM, FORMUL and CONECT records, except for waters.


    Example
    -------

    Example 1::

                 1         2         3         4         5         6         7         8
        12345678901234567890123456789012345678901234567890123456789012345678901234567890
        HETATM 8237 MG    MG A1001      13.872  -2.555 -29.045  1.00 27.36          MG

        HETATM 3835 FE   HEM A   1      17.140   3.115  15.066  1.00 14.14          FE
        HETATM 8238  S   SO4 A2001      10.885 -15.746 -14.404  1.00 47.84           S
        HETATM 8239  O1  SO4 A2001      11.191 -14.833 -15.531  1.00 50.12           O
        HETATM 8240  O2  SO4 A2001       9.576 -16.338 -14.706  1.00 48.55           O
        HETATM 8241  O3  SO4 A2001      11.995 -16.703 -14.431  1.00 49.88           O
        HETATM 8242  O4  SO4 A2001      10.932 -15.073 -13.100  1.00 49.91           O


    @param record:          The PDB HETATM record.
    @type record:           str
    @return:                The atom serial number, atom name, alternate location indicator, residue name, chain identifier, sequence number, insertion code, orthogonal coordinates for X in Angstroms, orthogonal coordinates for Y in Angstroms, orthogonal coordinates for Z in Angstroms, occupancy, temperature factor, element symbol, charge on the atom.
    @rtype:                 tuple of int, str, str, str, str, int, str, float, float, float, float, float, str, int
    """

    # Initialise.
    fields = []

    # Split up the record.
    fields.append(record[0:6])
    fields.append(record[6:11])
    fields.append(record[12:16])
    fields.append(record[16])
    fields.append(record[17:20])
    fields.append(record[21])
    fields.append(record[22:26])
    fields.append(record[26])
    fields.append(record[30:38])
    fields.append(record[38:46])
    fields.append(record[46:54])
    fields.append(record[54:60])
    fields.append(record[60:66])
    fields.append(record[76:78])
    fields.append(record[78:80])

    # Loop over the fields.
    for i in range(len(fields)):
        # Strip all whitespace.
        fields[i] = fields[i].strip()

        # Replace nothingness with None.
        if fields[i] == '':
            fields[i] = None

    # Convert strings to numbers.
    if fields[1]:
        fields[1] = int(fields[1])
    if fields[6]:
        fields[6] = int(fields[6])
    if fields[8]:
        fields[8] = float(fields[8])
    if fields[9]:
        fields[9] = float(fields[9])
    if fields[10]:
        fields[10] = float(fields[10])
    if fields[11]:
        fields[11] = float(fields[11])
    if fields[12]:
        fields[12] = float(fields[12])

    # Return the data.
    return tuple(fields)


def hetnam(record):
    """Parse the HETNAM record.

    The following is the PDB v3.3 documentation U{http://www.wwpdb.org/documentation/format33/sect4.html#HETNAM}.

    HETNAM
    ======

    Overview
    --------

    This record gives the chemical name of the compound with the given hetID.


    Record Format
    -------------

    The format is::
     ______________________________________________________________________________________________
     |         |              |              |                                                    |
     | Columns | Data type    | Field        | Definition                                         |
     |_________|______________|______________|____________________________________________________|
     |         |              |              |                                                    |
     |  1 -  6 | Record name  | "HETNAM"     |                                                    |
     |  9 - 10 | Continuation | continuation | Allows concatenation of multiple records.          |
     | 12 - 14 | LString(3)   | hetID        | Het identifier, right-justified.                   |
     | 16 - 70 | String       | text         | Chemical name.                                     |
     |_________|______________|______________|____________________________________________________|


    Details
    -------

    Each hetID is assigned a unique chemical name for the HETNAM record, see U{ftp://ftp.wwpdb.org/pub/pdb/data/monomers}.

    Other names for the group are given on HETSYN records.

    PDB entries follow IUPAC/IUB naming conventions to describe groups systematically.

    The special character "~" is used to indicate superscript in a heterogen name.  For example: N6 will be listed in the HETNAM section as N~6~, with the ~ character indicating both the start and end of the superscript in the name, e.g.:

      - N-(BENZYLSULFONYL)SERYL-N~1~-{4-[AMINO(IMINO)METHYL]BENZYL}GLYCINAMIDE

    Continuation of chemical names onto subsequent records is allowed.

    Only one HETNAM record is included for a given hetID, even if the same hetID appears on more than one HET record.


    Verification/Validation/Value Authority Control
    -----------------------------------------------

    For each het group that appears in the entry, the corresponding HET, HETNAM, FORMUL, HETATM, and CONECT records must appear.  The HETNAM record is generated automatically using the Chemical Component Dictionary and information from HETATM records.


    Relationships to Other Record Types
    -----------------------------------

    For each het group that appears in the entry, there must be corresponding HET, HETNAM, FORMUL, HETATM, and CONECT records.  HETSYN and LINK records may also be created.


    Example
    -------

    Example 1::

                 1         2         3         4         5         6         7         8
        12345678901234567890123456789012345678901234567890123456789012345678901234567890
        HETNAM     NAG N-ACETYL-D-GLUCOSAMINE
        HETNAM     SAD BETA-METHYLENE SELENAZOLE-4-CARBOXAMIDE ADENINE
        HETNAM  2  SAD DINUCLEOTIDE

        HETNAM     UDP URIDINE-5'-DIPHOSPHATE

        HETNAM     UNX UNKNOWN ATOM OR ION
        HETNAM     UNL UNKNOWN LIGAND

        HETNAM     B3P 2-[3-(2-HYDROXY-1,1-DIHYDROXYMETHYL-ETHYLAMINO)-
        HETNAM   2 B3P  PROPYLAMINO]-2-HYDROXYMETHYL-PROPANE-1,3-DIOL


    @param record:          The PDB HETNAM record.
    @type record:           str
    @raises RelaxImplementError:    Always.
    """

    # Not implemented yet.
    raise RelaxImplementError('hetnam')


def model(record):
    """Parse the MODEL record.

    The following is the PDB v3.3 documentation U{http://www.wwpdb.org/documentation/format33/sect9.html#MODEL}.

    MODEL
    =====

    Overview
    --------

    The MODEL record specifies the model serial number when multiple models of the same structure are presented in a single coordinate entry, as is often the case with structures determined by NMR.


    Record Format
    -------------

    The format is::
     ______________________________________________________________________________________________
     |         |              |              |                                                    |
     | Columns | Data type    | Field        | Definition                                         |
     |_________|______________|______________|____________________________________________________|
     |         |              |              |                                                    |
     |  1 -  6 | Record name  | "MODEL "     |                                                    |
     | 11 - 14 | Integer      | serial       | Model serial number.                               |
     |_________|______________|______________|____________________________________________________|


    Details
    -------

    This record is used only when more than one model appears in an entry.  Generally, it is employed mainly for NMR structures.  The chemical connectivity should be the same for each model.  ATOM, HETATM, ANISOU, and TER records for each model structure and are interspersed as needed between MODEL and ENDMDL records.

    The numbering of models is sequential, beginning with 1.

    All models in a deposition should be superimposed in an appropriate author determined manner and only one superposition method should be used.  Structures from different experiments, or different domains of a structure should not be superimposed and deposited as models of a deposition.

    All models in an NMR ensemble should be homogeneous - each model should have the exact same atoms (hydrogen and heavy atoms), sequence and chemistry.

    All models in an NMR entry should have hydrogen atoms.

    Deposition of minimized average structure must be accompanied with ensemble and must be homogeneous with ensemble.

    A model cannot have more than 99,999 atoms.  Where the entry does not contain an ensemble of models, then the entry cannot have more than 99,999 atoms.  Entries that go beyond this atom limit must be split into multiple entries, each containing no more than the limits specified above.


    Verification/Validation/Value Authority Control
    -----------------------------------------------

    Entries with multiple models in the NUMMDL record are checked for corresponding pairs of MODEL/ ENDMDL records, and for consecutively numbered models.


    Relationships to Other Record Types
    -----------------------------------

    Each MODEL must have a corresponding ENDMDL record.


    Examples
    --------

    Example 1::

                 1         2         3         4         5         6         7         8
        12345678901234567890123456789012345678901234567890123456789012345678901234567890
        MODEL        1
        ATOM      1  N   ALA A   1      11.104   6.134  -6.504  1.00  0.00           N
        ATOM      2  CA  ALA A   1      11.639   6.071  -5.147  1.00  0.00           C
        ...
        ...
        ...
        ATOM    293 1HG  GLU A   18    -14.861  -4.847   0.361  1.00  0.00           H
        ATOM    294 2HG  GLU A   18    -13.518  -3.769   0.084  1.00  0.00           H
        TER     295      GLU A   18
        ENDMDL
        MODEL        2
        ATOM    296  N   ALA  A   1     10.883   6.779  -6.464  1.00  0.00           N
        ATOM    297  CA  ALA  A   1     11.451   6.531  -5.142  1.00  0.00           C
        ...
        ...
        ATOM    588 1HG  GLU A   18    -13.363  -4.163  -2.372  1.00  0.00           H
        ATOM    589 2HG  GLU A   18    -12.634  -3.023  -3.475  1.00  0.00           H
        TER     590      GLU A   18
        ENDMDL

    Example 2::

                 1         2         3         4         5         6         7         8
        12345678901234567890123456789012345678901234567890123456789012345678901234567890
        MODEL        1
        ATOM      1  N  AALA A   1      72.883  57.697  56.410  0.50 83.80           N
        ATOM      2  CA AALA A   1      73.796  56.531  56.644  0.50 84.78           C
        ATOM      3  C  AALA A   1      74.549  56.551  57.997  0.50 85.05           C
        ATOM      4  O  AALA A   1      73.951  56.413  59.075  0.50 84.77           O
        ...
        ...
        ...
        HETATM37900  O  AHOH   490     -24.915 147.513  36.413  0.50 41.86           O
        HETATM37901  O  AHOH   491     -28.699 130.471  22.248  0.50 36.06           O
        HETATM37902  O  AHOH   492     -33.309 184.488  26.176  0.50 15.00           O
        ENDMDL
        MODEL        2
        ATOM      1  N  BALA A   1      72.883  57.697  56.410  0.50 83.80           N
        ATOM      2  CA BALA A   1      73.796  56.531  56.644  0.50 84.78           C
        ATOM      3  C  BALA A   1      74.549  56.551  57.997  0.50 85.05           C
        ATOM      4  O  BALA A   1      73.951  56.413  59.075  0.50 84.77           O
        ATOM      5  CB BALA A   1      74.804  56.369  55.453  0.50 84.29           C
        ATOM      6  N  BASP A   2      75.872  56.703  57.905  0.50 85.59           N
        ATOM      7  CA BASP A   2      76.801  56.651  59.048  0.50 85.67           C
        ATOM      8  C  BASP A   2      76.283  57.361  60.309  0.50 84.80           C
        ...


    @param record:          The PDB MODEL record.
    @type record:           str
    @raises RelaxImplementError:    Always.
    """

    # Not implemented yet.
    raise RelaxImplementError('model')


def remark(record):
    """Parse the REMARK record.

    The following is the PDB v3.3 documentation U{http://www.wwpdb.org/documentation/format33/remarks.html}.

    REMARK
    ======

    Overview
    --------

    REMARK records present experimental details, annotations, comments, and information not included in other records.  In a number of cases, REMARKs are used to expand the contents of other record types.  A new level of structure is being used for some REMARK records.  This is expected to facilitate searching and will assist in the conversion to a relational database.

    The very first line of every set of REMARK records is used as a spacer to aid in reading::

     ______________________________________________________________________________________________
     |         |             |             |                                                      |
     | Columns | Data type   | Field       | Definition                                           |
     |_________|_____________|_____________|______________________________________________________|
     |         |             |             |                                                      |
     |  1 -  6 | Record name | "REMARK"    |                                                      |
     |  8 - 10 | Integer     | remarkNum   | Remark number.  It is not an error for remark n to   |
     |         |             |             | exist in an entry when remark n-1 does not.          |
     | 12 - 79 | LString     | empty       | Left as white space in first line of each new        |
     |         |             |             | remark.                                              |
     |_________|_____________|_____________|______________________________________________________|


    @param record:          The PDB REMARK record.
    @type record:           str
    @raises RelaxImplementError:    Always.
    """

    # Not implemented yet.
    raise RelaxImplementError('remark')


def sheet(record):
    """Parse the SHEET record.

    The following is the PDB v3.3 documentation U{http://www.wwpdb.org/documentation/format33/sect5.html#SHEET}.

    SHEET
    =====

    Overview
    --------

    SHEET records are used to identify the position of sheets in the molecule.  Sheets are both named and numbered.  The residues where the sheet begins and ends are noted.


    Record Format
    -------------

    The format is::
     ______________________________________________________________________________________________
     |         |              |              |                                                    |
     | Columns | Data type    | Field        | Definition                                         |
     |_________|______________|______________|____________________________________________________|
     |         |              |              |                                                    |
     |  1 -  6 | Record name  | "SHEET "     |                                                    |
     |  8 - 10 | Integer      | strand       | Strand number which starts at 1 for each strand    |
     |         |              |              | within a sheet and increases by one.               |
     | 12 - 14 | LString(3)   | sheetID      | Sheet identifier.                                  |
     | 15 - 16 | Integer      | numStrands   | Number of strands in sheet.                        |
     | 18 - 20 | Residue name | initResName  | Residue name of initial residue.                   |
     | 22      | Character    | initChainID  | Chain identifier of initial residue in strand.     |
     | 23 - 26 | Integer      | initSeqNum   | Sequence number of initial residue in strand.      |
     | 27      | AChar        | initICode    | Insertion code of initial residue in strand.       |
     | 29 - 31 | Residue name | endResName   | Residue name of terminal residue.                  |
     | 33      | Character    | endChainID   | Chain identifier of terminal residue.              |
     | 34 - 37 | Integer      | endSeqNum    | Sequence number of terminal residue.               |
     | 38      | AChar        | endICode     | Insertion code of terminal residue.                |
     | 39 - 40 | Integer      | sense        | Sense of strand with respect to previous strand in |
     |         |              |              | the sheet. 0 if first strand, 1 if parallel, and   |
     |         |              |              | -1 if anti-parallel.                               |
     | 42 - 45 | Atom         | curAtom      | Registration.  Atom name in current strand.        |
     | 46 - 48 | Residue name | curResName   | Registration.  Residue name in current strand.     |
     | 50      | Character    | curChainId   | Registration.  Chain identifier in current strand. |
     | 51 - 54 | Integer      | curResSeq    | Registration.  Residue sequence number in current  |
     |         |              |              | strand.                                            |
     | 55      | AChar        | curICode     | Registration.  Insertion code in current strand.   |
     | 57 - 60 | Atom         | prevAtom     | Registration.  Atom name in previous strand.       |
     | 61 - 63 | Residue name | prevResName  | Registration.  Residue name in previous strand.    |
     | 65      | Character    | prevChainId  | Registration.  Chain identifier in previous strand.|
     | 66 - 69 | Integer      | prevResSeq   | Registration.  Residue sequence number in previous |
     |         |              |              | strand.                                            |
     | 70      | AChar        | prevICode    | Registration.  Insertion code in previous strand.  |
     |_________|______________|______________|____________________________________________________|


    Details
    -------

    The initial residue for a strand is its N-terminus.  Strand registration information is provided in columns 39 - 70.  Strands are listed starting with one edge of the sheet and continuing to the spatially adjacent strand.

    The sense in columns 39 - 40 indicates whether strand n is parallel (sense = 1) or anti-parallel (sense = -1) to strand n-1.  Sense is equal to zero (0) for the first strand of a sheet.

    The registration (columns 42 - 70) of strand n to strand n-1 may be specified by one hydrogen bond between each such pair of strands.  This is done by providing the hydrogen bonding between the current and previous strands.  No register information should be provided for the first strand.

    Split strands, or strands with two or more runs of residues from discontinuous parts of the amino acid sequence, are explicitly listed.  Detail description can be included in the REMARK 700.


    Relationships to Other Record Types
    -----------------------------------

    If the entry contains bifurcated sheets or beta-barrels, the relevant REMARK 700 records must be provided.  See the REMARK section for details.


    Examples
    --------

    Example 1::

                 1         2         3         4         5         6         7         8
        12345678901234567890123456789012345678901234567890123456789012345678901234567890
        SHEET    1   A 5 THR A 107  ARG A 110  0
        SHEET    2   A 5 ILE A  96  THR A  99 -1  N  LYS A  98   O  THR A 107
        SHEET    3   A 5 ARG A  87  SER A  91 -1  N  LEU A  89   O  TYR A  97
        SHEET    4   A 5 TRP A  71  ASP A  75 -1  N  ALA A  74   O  ILE A  88
        SHEET    5   A 5 GLY A  52  PHE A  56 -1  N  PHE A  56   O  TRP A  71
        SHEET    1   B 5 THR B 107  ARG B 110  0
        SHEET    2   B 5 ILE B  96  THR B  99 -1  N  LYS B  98   O  THR B 107
        SHEET    3   B 5 ARG B  87  SER B  91 -1  N  LEU B  89   O  TYR B  97
        SHEET    4   B 5 TRP B  71  ASP B  75 -1  N  ALA B  74   O  ILE B  88
        SHEET    5   B 5 GLY B  52  ILE B  55 -1  N  ASP B  54   O  GLU B  73

    The sheet presented as BS1 below is an eight-stranded beta-barrel.  This is represented by a nine-stranded sheet in which the first and last strands are identical::

        SHEET    1 BS1 9  VAL   13  ILE    17  0                               
        SHEET    2 BS1 9  ALA   70  ILE    73  1  O  TRP    72   N  ILE    17  
        SHEET    3 BS1 9  LYS  127  PHE   132  1  O  ILE   129   N  ILE    73  
        SHEET    4 BS1 9  GLY  221  ASP   225  1  O  GLY   221   N  ILE   130  
        SHEET    5 BS1 9  VAL  248  GLU   253  1  O  PHE   249   N  ILE   222  
        SHEET    6 BS1 9  LEU  276  ASP   278  1  N  LEU   277   O  GLY   252  
        SHEET    7 BS1 9  TYR  310  THR   318  1  O  VAL   317   N  ASP   278  
        SHEET    8 BS1 9  VAL  351  TYR   356  1  O  VAL   351   N  THR   318  
        SHEET    9 BS1 9  VAL   13  ILE    17  1  N  VAL    14   O  PRO   352  

    The sheet structure of this example is bifurcated.  In order to represent this feature, two sheets are defined.  Strands 2 and 3 of BS7 and BS8 are identical::

        SHEET    1 BS7 3  HIS  662  THR   665  0                               
        SHEET    2 BS7 3  LYS  639  LYS   648 -1  N  PHE   643   O  HIS   662  
        SHEET    3 BS7 3  ASN  596  VAL   600 -1  N  TYR   598   O  ILE   646  
        SHEET    1 BS8 3  ASN  653  TRP   656  0                               
        SHEET    2 BS8 3  LYS  639  LYS   648 -1  N  LYS   647   O  THR   655  
        SHEET    3 BS8 3  ASN  596  VAL   600 -1  N  TYR   598   O  ILE   646  


    @param record:          The PDB SHEET record.
    @type record:           str
    @return:                The record name, strand number, sheet identifier, number of strands in sheet, residue name of initial residue, chain identifier of initial residue in strand, sequence number of initial residue in strand, insertion code of initial residue in strand, residue name of terminal residue, chain identifier of terminal residue, sequence number of terminal residue, insertion code of terminal residue, sense of strand with respect to previous strand, atom name in current strand, residue name in current strand, chain identifier in current strand, residue sequence number in current strand, insertion code in current strand, atom name in previous strand, residue name in previous strand, chain identifier in previous strand, residue sequence number in previous strand, insertion code in previous strand.
    @rtype:                 tuple of str, int, str, int, str, str, int, str, str, str, int, str, int, str, str, str, int, str, str, str, str, int, str
    """

    # Initialise.
    fields = []

    # Split up the record.
    fields.append(record[0:6])
    fields.append(record[7:10])
    fields.append(record[11:14])
    fields.append(record[14:16])
    fields.append(record[17:20])
    fields.append(record[21])
    fields.append(record[22:26])
    fields.append(record[26])
    fields.append(record[28:31])
    fields.append(record[32])
    fields.append(record[33:37])
    fields.append(record[37])
    fields.append(record[38:40])
    fields.append(record[41:45])
    fields.append(record[45:48])
    fields.append(record[49])
    fields.append(record[50:54])
    fields.append(record[54])
    fields.append(record[56:60])
    fields.append(record[60:63])
    fields.append(record[64])
    fields.append(record[65:69])
    fields.append(record[69])

    # Loop over the fields.
    for i in range(len(fields)):
        # Strip all whitespace.
        fields[i] = fields[i].strip()

        # Replace nothingness with None.
        if fields[i] == '':
            fields[i] = None

    # Convert strings to numbers.
    if fields[1]:
        fields[1] = int(fields[1])
    if fields[3]:
        fields[3] = int(fields[3])
    if fields[6]:
        fields[6] = int(fields[6])
    if fields[10]:
        fields[10] = int(fields[10])
    if fields[12]:
        fields[12] = int(fields[12])
    if fields[16]:
        fields[16] = int(fields[16])
    if fields[21]:
        fields[21] = int(fields[21])

    # Return the data.
    return tuple(fields)


def ter(record):
    """Parse the TER record.

    The following is the PDB v3.3 documentation U{http://www.wwpdb.org/documentation/format33/sect9.html#TER}.

    TER
    ===

    Overview
    --------

    The TER record indicates the end of a list of ATOM/HETATM records for a chain.


    Record Format
    -------------

    The format is::
     ______________________________________________________________________________________________
     |         |              |              |                                                    |
     | Columns | Data type    | Field        | Definition                                         |
     |_________|______________|______________|____________________________________________________|
     |         |              |              |                                                    |
     |  1 -  6 | Record name  | "TER   "     |                                                    |
     |  7 - 11 | Integer      | serial       | Serial number.                                     |
     | 18 - 20 | Residue name | resName      | Residue name.                                      |
     | 22      | Character    | chainID      | Chain identifier.                                  |
     | 23 - 26 | Integer      | resSeq       | Residue sequence number.                           |
     | 27      | AChar        | iCode        | Insertion code.                                    |
     |_________|______________|______________|____________________________________________________|


    Details
    -------

    Every chain of ATOM/HETATM records presented on SEQRES records is terminated with a TER record.

    The TER records occur in the coordinate section of the entry, and indicate the last residue presented for each polypeptide and/or nucleic acid chain for which there are determined coordinates.  For proteins, the residue defined on the TER record is the carboxy-terminal residue; for nucleic acids it is the 3'-terminal residue.

    For a cyclic molecule, the choice of termini is arbitrary.

    Terminal oxygen atoms are presented as OXT for proteins, and as O5' or OP3 for nucleic acids.  These atoms are present only if the last residue in the polymer is truly the last residue in the SEQRES.

    The TER record has the same residue name, chain identifier, sequence number and insertion code as the terminal residue.  The serial number of the TER record is one number greater than the serial number of the ATOM/HETATM preceding the TER.


    Verification/Validation/Value Authority Control
    -----------------------------------------------

    TER must appear at the terminal carboxyl end or 3' end of a chain.  For proteins, there is usually a terminal oxygen, labeled OXT.  The validation program checks for the occurrence of TER and OXT records.


    Relationships to Other Record Types
    -----------------------------------

    The residue name appearing on the TER record must be the same as the residue name of the immediately preceding ATOM or non-water HETATM record.


    Example
    -------

    Example 1::

                 1         2         3         4         5         6         7         8
        12345678901234567890123456789012345678901234567890123456789012345678901234567890
        ATOM    601  N   LEU A  75     -17.070 -16.002   2.409  1.00 55.63           N
        ATOM    602  CA  LEU A  75     -16.343 -16.746   3.444  1.00 55.50           C
        ATOM    603  C   LEU A  75     -16.499 -18.263   3.300  1.00 55.55           C
        ATOM    604  O   LEU A  75     -16.645 -18.789   2.195  1.00 55.50           O
        ATOM    605  CB  LEU A  75     -16.776 -16.283   4.844  1.00 55.51           C
        TER     606      LEU A  75
        ...
        ATOM   1185  O   LEU B  75      26.292  -4.310  16.940  1.00 55.45           O
        ATOM   1186  CB  LEU B  75      23.881  -1.551  16.797  1.00 55.32           C
        TER    1187      LEU B  75
        HETATM 1188  H2  SRT A1076     -17.263  11.260  28.634  1.00 59.62           H
        HETATM 1189  HA  SRT A1076     -19.347  11.519  28.341  1.00 59.42           H
        HETATM 1190  H3  SRT A1076     -17.157  14.303  28.677  1.00 58.00           H
        HETATM 1191  HB  SRT A1076     -15.110  13.610  28.816  1.00 57.77           H
        HETATM 1192  O1  SRT A1076     -17.028  11.281  31.131  1.00 62.63           O

        ATOM    295  HB2 ALA A  18       4.601  -9.393   7.275  1.00  0.00           H
        ATOM    296  HB3 ALA A  18       3.340  -9.147   6.043  1.00  0.00           H
        TER     297      ALA A  18
        ENDMDL


    @param record:          The PDB TER record.
    @type record:           str
    @raises RelaxImplementError:    Always.
    """

    # Not implemented yet.
    raise RelaxImplementError('ter')
