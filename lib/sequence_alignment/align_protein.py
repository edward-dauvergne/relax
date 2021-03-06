###############################################################################
#                                                                             #
# Copyright (C) 2015 Edward d'Auvergne                                        #
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
"""General sequence alignment functions."""

# Python module imports.
import sys

# relax module imports.
from lib.errors import RelaxError
from lib.sequence_alignment.needleman_wunsch import needleman_wunsch_align
from lib.sequence_alignment.substitution_matrices import BLOSUM62, BLOSUM62_SEQ, PAM250, PAM250_SEQ


def align_pairwise(sequence1, sequence2, algorithm='NW70', matrix='BLOSUM62', gap_open_penalty=1.0, gap_extend_penalty=1.0, end_gap_open_penalty=0.0, end_gap_extend_penalty=0.0, verbosity=1):
    """Align two protein sequences.

    @param sequence1:                   The first protein sequence as one letter codes.
    @type sequence1:                    str
    @param sequence2:                   The second protein sequence as one letter codes.
    @type sequence2:                    str
    @keyword algorithm:                 The pairwise sequence alignment algorithm to use.
    @type algorithm:                    str
    @keyword matrix:                    The substitution matrix to use.
    @type matrix:                       str
    @keyword gap_open_penalty:          The penalty for introducing gaps, as a positive number.
    @type gap_open_penalty:             float
    @keyword gap_extend_penalty:        The penalty for extending a gap, as a positive number.
    @type gap_extend_penalty:           float
    @keyword end_gap_open_penalty:      The optional penalty for opening a gap at the end of a sequence.
    @type end_gap_open_penalty:         float
    @keyword end_gap_extend_penalty:    The optional penalty for extending a gap at the end of a sequence.
    @type end_gap_extend_penalty:       float
    @keyword verbosity:                 The level of verbosity.  Setting this to zero silences all printouts.
    @type verbosity:                    int
    @return:                            The alignment score, two alignment strings and the gap matrix.
    @rtype:                             float, str, str, numpy rank-2 int array
    """

    # Checks.
    allowed_algor = ['NW70']
    if algorithm not in allowed_algor:
        raise RelaxError("The sequence alignment algorithm '%s' is unknown, it must be one of %s." % (algorithm, allowed_algor))
    allowed_matrices = ['BLOSUM62', 'PAM250']
    if matrix not in allowed_matrices:
        raise RelaxError("The substitution matrix '%s' is unknown, it must be one of %s." % (matrix, allowed_matrices))

    # Capitalise the sequences.
    sequence1 = sequence1.upper()
    sequence2 = sequence2.upper()

    # Initial printout.
    if verbosity:
        sys.stdout.write("\nPairwise protein alignment.\n")
        sys.stdout.write("%-30s %s\n" % ("Substitution matrix:", matrix))
        sys.stdout.write("%-30s %s\n" % ("Gap opening penalty:", gap_open_penalty))
        sys.stdout.write("%-30s %s\n" % ("Gap extend penalty:", gap_extend_penalty))
        sys.stdout.write("\n%-30s %s\n" % ("Input sequence 1:", sequence1))
        sys.stdout.write("%-30s %s\n" % ("Input sequence 2:", sequence2))

    # Select the substitution matrix.
    if matrix == 'BLOSUM62':
        sub_matrix = BLOSUM62
        sub_seq = BLOSUM62_SEQ
    elif matrix == 'PAM250':
        sub_matrix = PAM250
        sub_seq = PAM250_SEQ

    # The alignment.
    if algorithm == 'NW70':
        score, align1, align2, gaps = needleman_wunsch_align(sequence1, sequence2, sub_matrix=sub_matrix, sub_seq=sub_seq, gap_open_penalty=gap_open_penalty, gap_extend_penalty=gap_extend_penalty, end_gap_open_penalty=end_gap_open_penalty, end_gap_extend_penalty=end_gap_extend_penalty)

    # Final printout.
    if verbosity:
        sys.stdout.write("\n%-30s %s\n" % ("Aligned sequence 1:", align1))
        sys.stdout.write("%-30s %s\n" % ("Aligned sequence 2:", align2))
        sys.stdout.write("%-30s " % "")
        for i in range(len(align1)):
            if align1[i] == align2[i]:
                sys.stdout.write("*")
            else:
                sys.stdout.write(" ")
        sys.stdout.write("\n\n")

    # Return the results.
    return score, align1, align2, gaps
