###############################################################################
#                                                                             #
# Copyright (C) 2000-2001 Nikolai Skrynnikov                                  #
# Copyright (C) 2000-2001 Martin Tollinger                                    #
# Copyright (C) 2010-2013 Paul Schanda (https://gna.org/users/pasa)           #
# Copyright (C) 2013 Mathilde Lescanne                                        #
# Copyright (C) 2013 Dominique Marion                                         #
# Copyright (C) 2013-2014 Edward d'Auvergne                                   #
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
"""The numerical fit of 2-site Bloch-McConnell equations for CPMG-type experiments, the U{NS CPMG 2-site star<http://wiki.nmr-relax.com/NS_CPMG_2-site_star>} and U{NS CPMG 2-site star full<http://wiki.nmr-relax.com/NS_CPMG_2-site_star_full>} models.

Description
===========

The function uses an explicit matrix that contains relaxation, exchange and chemical shift terms. It does the 180deg pulses in the CPMG train with conjugate complex matrices.  The approach of Bloch-McConnell can be found in chapter 3.1 of Palmer, A. G. 2004 I{Chem. Rev.}, B{104}, 3623-3640.  This function was written, initially in MATLAB, in 2010.


Code origin
===========

The code was submitted at U{http://thread.gmane.org/gmane.science.nmr.relax.devel/4132} by Paul Schanda.


Links
=====

More information on the NS CPMG 2-site star model can be found in the:

    - U{relax wiki<http://wiki.nmr-relax.com/NS_CPMG_2-site_star>},
    - U{relax manual<http://www.nmr-relax.com/manual/reduced_NS_2_site_star_CPMG_model.html>},
    - U{relaxation dispersion page of the relax website<http://www.nmr-relax.com/analyses/relaxation_dispersion.html#NS_CPMG_2-site_star>}.

More information on the NS CPMG 2-site star full model can be found in the:

    - U{relax wiki<http://wiki.nmr-relax.com/NS_CPMG_2-site_star_full>},
    - U{relax manual<http://www.nmr-relax.com/manual/full_NS_2_site_star_CPMG_model.html>},
    - U{relaxation dispersion page of the relax website<http://www.nmr-relax.com/analyses/relaxation_dispersion.html#NS_CPMG_2-site_star_full>}.
"""

# Python module imports.
from math import log
from numpy import add, complex, conj, dot

# relax module imports.
from lib.float import isNaN
from lib.linear_algebra.matrix_exponential import matrix_exponential
from lib.linear_algebra.matrix_power import square_matrix_power


def r2eff_ns_cpmg_2site_star(Rr=None, Rex=None, RCS=None, R=None, M0=None, r20a=None, r20b=None, dw=None, inv_tcpmg=None, tcp=None, back_calc=None, num_points=None, power=None):
    """The 2-site numerical solution to the Bloch-McConnell equation using complex conjugate matrices.

    This function calculates and stores the R2eff values.


    @keyword Rr:            The matrix that contains only the R2 relaxation terms ("Redfield relaxation", i.e. non-exchange broadening).
    @type Rr:               numpy complex64, rank-2, 2D array
    @keyword Rex:           The matrix that contains the exchange terms between the two states A and B.
    @type Rex:              numpy complex64, rank-2, 2D array
    @keyword RCS:           The matrix that contains the chemical shift evolution.  It works here only with X magnetization, and the complex notation allows to evolve in the transverse plane (x, y).
    @type RCS:              numpy complex64, rank-2, 2D array
    @keyword R:             The matrix that contains all the contributions to the evolution, i.e. relaxation, exchange and chemical shift evolution.
    @type R:                numpy complex64, rank-2, 2D array
    @keyword M0:            This is a vector that contains the initial magnetizations corresponding to the A and B state transverse magnetizations.
    @type M0:               numpy float64, rank-1, 2D array
    @keyword r20a:          The R2 value for state A in the absence of exchange.
    @type r20a:             float
    @keyword r20b:          The R2 value for state B in the absence of exchange.
    @type r20b:             float
    @keyword dw:            The chemical exchange difference between states A and B in rad/s.
    @type dw:               float
    @keyword inv_tcpmg:     The inverse of the total duration of the CPMG element (in inverse seconds).
    @type inv_tcpmg:        float
    @keyword tcp:           The tau_CPMG times (1 / 4.nu1).
    @type tcp:              numpy rank-1 float array
    @keyword back_calc:     The array for holding the back calculated R2eff values.  Each element corresponds to one of the CPMG nu1 frequencies.
    @type back_calc:        numpy rank-1 float array
    @keyword num_points:    The number of points on the dispersion curve, equal to the length of the tcp and back_calc arguments.
    @type num_points:       int
    @keyword power:         The matrix exponential power array.
    @type power:            numpy int16, rank-1 array
    """

    # The matrix that contains only the R2 relaxation terms ("Redfield relaxation", i.e. non-exchange broadening).
    Rr[0, 0] = -r20a
    Rr[1, 1] = -r20b

    # The matrix that contains the chemical shift evolution.  It works here only with X magnetization, and the complex notation allows to evolve in the transverse plane (x, y).  The chemical shift for state A is assumed to be zero.
    RCS[1, 1] = complex(0.0, -dw)

    # The matrix R that contains all the contributions to the evolution, i.e. relaxation, exchange and chemical shift evolution.
    R = add(Rr, Rex)
    R = add(R, RCS)

    # This is the complex conjugate of the above.  It allows the chemical shift to run in the other direction, i.e. it is used to evolve the shift after a 180 deg pulse.  The factor of 2 is to minimise the number of multiplications for the prop_2 matrix calculation.
    cR2 = conj(R) * 2.0

    # Loop over the time points, back calculating the R2eff values.
    for i in range(num_points):
        # This matrix is a propagator that will evolve the magnetization with the matrix R for a delay tcp.
        eR_tcp = matrix_exponential(R*tcp[i])

        # This is the propagator for an element of [delay tcp; 180 deg pulse; 2 times delay tcp; 180 deg pulse; delay tau], i.e. for 2 times tau-180-tau.
        prop_2 = dot(dot(eR_tcp, matrix_exponential(cR2*tcp[i])), eR_tcp)

        # Now create the total propagator that will evolve the magnetization under the CPMG train, i.e. it applies the above tau-180-tau-tau-180-tau so many times as required for the CPMG frequency under consideration.
        prop_total = square_matrix_power(prop_2, power[i])

        # Now we apply the above propagator to the initial magnetization vector - resulting in the magnetization that remains after the full CPMG pulse train.  It is called M of t (t is the time after the CPMG train).
        Moft = dot(prop_total, M0)

        # The next lines calculate the R2eff using a two-point approximation, i.e. assuming that the decay is mono-exponential.
        Mx = Moft[0].real / M0[0]
        if Mx <= 0.0 or isNaN(Mx):
            back_calc[i] = 1e99
        else:
            back_calc[i]= -inv_tcpmg * log(Mx)
