###############################################################################
#                                                                             #
# Copyright (C) 2006-2012 Edward d'Auvergne                                   #
#                                                                             #
# This file is part of the program relax (http://www.nmr-relax.com).          #
#                                                                             #
# relax is free software; you can redistribute it and/or modify               #
# it under the terms of the GNU General Public License as published by        #
# the Free Software Foundation; either version 3 of the License, or           #
# (at your option) any later version.                                         #
#                                                                             #
# relax is distributed in the hope that it will be useful,                    #
# but WITHOUT ANY WARRANTY; without even the implied warranty of              #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the               #
# GNU General Public License for more details.                                #
#                                                                             #
# You should have received a copy of the GNU General Public License           #
# along with relax.  If not, see <http://www.gnu.org/licenses/>.              #
#                                                                             #
###############################################################################

# Python module imports.
from math import acos, pi
import platform
import numpy
from numpy import array, dot, float64, zeros
from numpy.linalg import norm
from re import search
from os import sep
import sys

# relax module imports.
from base_classes import SystemTestCase
from data import Relax_data_store; ds = Relax_data_store()
import dep_check
from maths_fns.coord_transform import spherical_to_cartesian
from maths_fns.rotation_matrix import euler_to_R_zyz
from physical_constants import N15_CSA, NH_BOND_LENGTH
from relax_io import DummyFileObject, open_read_file
from status import Status; status = Status()


# Get the platform information.
SYSTEM = platform.system()
RELEASE = platform.release()
VERSION = platform.version()
WIN32_VER = platform.win32_ver()
DIST = platform.dist()
ARCH = platform.architecture()
MACH = platform.machine()
PROC = platform.processor()
PY_VER = platform.python_version()
NUMPY_VER = numpy.__version__
LIBC_VER = platform.libc_ver()

# Windows system name pain.
if SYSTEM == 'Windows' or SYSTEM == 'Microsoft':
    # Set the system to 'Windows' no matter what.
    SYSTEM = 'Windows'



class Frame_order(SystemTestCase):
    """TestCase class for the functional tests of the frame order theories."""

    def __init__(self, methodName='runTest'):
        """Skip the tests if scipy is not installed.

        @keyword methodName:    The name of the test.
        @type methodName:       str
        """

        # Execute the base class method.
        super(Frame_order, self).__init__(methodName)

        # Missing module.
        if not dep_check.scipy_module:
            # Store in the status object. 
            status.skipped_tests.append([methodName, 'Scipy', self._skip_type])


    def setUp(self):
        """Set up for all the functional tests."""

        # Create the data pipe.
        self.interpreter.pipe.create('test', 'frame order')


    def mesg_opt_debug(self):
        """Method for returning a string to help debug the minimisation.

        @return:        The debugging string.
        @rtype:         str
        """

        # Initialise the string.
        string = 'Optimisation failure.\n\n'

        # Create the string.
        string = string + "%-18s%-25s\n" % ("System: ", SYSTEM)
        string = string + "%-18s%-25s\n" % ("Release: ", RELEASE)
        string = string + "%-18s%-25s\n" % ("Version: ", VERSION)
        string = string + "%-18s%-25s\n" % ("Win32 version: ", (WIN32_VER[0] + " " + WIN32_VER[1] + " " + WIN32_VER[2] + " " + WIN32_VER[3]))
        string = string + "%-18s%-25s\n" % ("Distribution: ", (DIST[0] + " " + DIST[1] + " " + DIST[2]))
        string = string + "%-18s%-25s\n" % ("Architecture: ", (ARCH[0] + " " + ARCH[1]))
        string = string + "%-18s%-25s\n" % ("Machine: ", MACH)
        string = string + "%-18s%-25s\n" % ("Processor: ", PROC)
        string = string + "%-18s%-25s\n" % ("Python version: ", PY_VER)
        string = string + "%-18s%-25s\n" % ("Numpy version: ", NUMPY_VER)
        string = string + "%-18s%-25s\n" % ("Libc version: ", (LIBC_VER[0] + " " + LIBC_VER[1]))


        # Minimisation info.
        string = string + "\n%-15s %30.17g\n" % ('ave_pos_alpha:',   cdp.ave_pos_alpha)
        string = string +   "%-15s %30.17g\n" % ('ave_pos_beta:',    cdp.ave_pos_beta)
        string = string +   "%-15s %30.17g\n" % ('ave_pos_gamma:',   cdp.ave_pos_gamma)
        string = string +   "%-15s %30.17g\n" % ('chi2:',    cdp.chi2)
        string = string +   "%-15s %30i\n" % ('iter:',    cdp.iter)
        string = string +   "%-15s %30i\n" % ('f_count:', cdp.f_count)
        string = string +   "%-15s %30i\n" % ('g_count:', cdp.g_count)
        string = string +   "%-15s %30i\n" % ('h_count:', cdp.h_count)
        string = string +   "%-15s %30s\n" % ('warning:', cdp.warning)

        # Return the string.
        return string


    def space_probe(self, ref_chi2=None, params=None, delta=3.0 / 360.0 * 2.0 * pi):
        """Probe the space around the supposed minimum."""

        # No function intros.
        self.interpreter.intro_off()

        # Check the minimum.
        self.interpreter.calc()
        print("%-20s %10.5f" % ("chi2 minimum", cdp.chi2))
        self.assertAlmostEqual(cdp.chi2, ref_chi2)

        # Test around the minimum using small deviations.
        for param in params:
            print("\n\nParam: %s" % param)
            print("%-20s %10.5f" % ("chi2 orig", ref_chi2))

            # Get the current value.
            curr = getattr(cdp, param)

            # Deviate upwards.
            setattr(cdp, param, curr+delta)
            self.interpreter.calc()
            print("%-20s %10.5f" % ("chi2 up", cdp.chi2))
            self.assert_(cdp.chi2 > ref_chi2)

            # Deviate downwards.
            setattr(cdp, param, curr-delta)
            self.interpreter.calc()
            print("%-20s %10.5f" % ("chi2 down", cdp.chi2))
            self.assert_(cdp.chi2 > ref_chi2)

            # Reset.
            setattr(cdp, param, curr)


    def test_cam_free_rotor(self):
        """Test the free rotor frame order model of CaM."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'cam'+sep+'free_rotor.py')

        # Check the average structure CoM matches that of the original position (the average structure is not defined along the rotation axis).
        for i in range(3):
            self.assertAlmostEqual(ds['ave pos'].CoM[i], ds['orig pos'].CoM[i], 0)

        # The rotation axis.
        self.interpreter.pipe.switch('frame order')
        spherical_vect = zeros(3, float64)
        spherical_vect[0] = 1.0
        spherical_vect[1] = cdp.axis_theta
        spherical_vect[2] = cdp.axis_phi
        cart_vect = zeros(3, float64)
        spherical_to_cartesian(spherical_vect, cart_vect)

        # The original rotation axis.
        pivot = array([ 37.254, 0.5, 16.7465])
        com = array([ 26.83678091, -12.37906417,  28.34154128])
        axis = pivot - com
        axis = axis / norm(axis)

        # The dot product.
        angle = acos(dot(cart_vect, axis))

        # Check the angle.
        if angle > 3 and angle < 4:
            self.assertAlmostEqual(angle, pi, 1)
        else:
            self.assertAlmostEqual(angle, 0.0, 1)


    def test_cam_free_rotor2(self):
        """Test the second free rotor frame order model of CaM."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'cam'+sep+'free_rotor2.py')

        # The base data.
        pivot = array([ 37.254, 0.5, 16.7465])
        com = array([ 26.83678091, -12.37906417,  28.34154128])
        pivot_com_axis = com - pivot
        rot_axis = array([ 0.62649633,  0.77455282, -0.08700742])

        # The average position CoM.
        ave_pivot_com_axis = ds['ave pos'].CoM - pivot

        # The projection of the CoMs onto the rotation axis.
        orig_proj = dot(pivot_com_axis, rot_axis)
        ave_proj = dot(ave_pivot_com_axis, rot_axis)

        # Check that the projections are equal.
        self.assertAlmostEqual(orig_proj, ave_proj, 0)

        # The rotation axis.
        self.interpreter.pipe.switch('frame order')
        spherical_vect = zeros(3, float64)
        spherical_vect[0] = 1.0
        spherical_vect[1] = cdp.axis_theta
        spherical_vect[2] = cdp.axis_phi
        cart_vect = zeros(3, float64)
        spherical_to_cartesian(spherical_vect, cart_vect)
        print("\nReal rotation axis:   %s" % repr(rot_axis))
        print("Fitted rotation axis: %s" % repr(cart_vect))

        # The dot product.
        angle = acos(dot(cart_vect, rot_axis))
        if angle > pi/2:
            angle = acos(dot(cart_vect, -rot_axis))

        # Check the angle.
        self.assertAlmostEqual(angle, 0.0, 2)


    def test_cam_iso_cone_free_rotor(self):
        """Test the isotropic cone, free rotor frame order model of CaM."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'cam'+sep+'iso_cone_free_rotor.py')

        # Check the average structure CoM matches that of the original position (the average structure is not defined along the rotation axis).
        for i in range(3):
            self.assertAlmostEqual(ds['ave pos'].CoM[i], ds['orig pos'].CoM[i], 0)

        # Switch to the correct data pipe.
        self.interpreter.pipe.switch('frame order')

        # The base data.
        pivot = array([ 37.254, 0.5, 16.7465])
        com = array([ 26.83678091, -12.37906417,  28.34154128])
        pivot_com_axis = com - pivot
        rot_axis = pivot_com_axis / norm(pivot_com_axis)

        # The average position checks.
        ave_pivot_com_axis = ds['ave pos'].CoM - pivot

        # The projection of the CoMs onto the rotation axis.
        orig_proj = dot(pivot_com_axis, rot_axis)
        ave_proj = dot(ave_pivot_com_axis, rot_axis)
        print("\nReal projection of the central axis to the pivot-CoM:   %s" % repr(orig_proj))
        print("Fitted projection of the central axis to the pivot-CoM: %s" % repr(ave_proj))

        # Check that the projections are equal.
        self.assertAlmostEqual(orig_proj, ave_proj, 1)

        # The rotation axis.
        self.interpreter.pipe.switch('frame order')
        spherical_vect = zeros(3, float64)
        spherical_vect[0] = 1.0
        spherical_vect[1] = cdp.axis_theta
        spherical_vect[2] = cdp.axis_phi
        axis = zeros(3, float64)
        spherical_to_cartesian(spherical_vect, axis)
        print("\nReal rotation axis:   %s" % repr(rot_axis))
        print("Fitted rotation axis: %s" % repr(axis))

        # Check the angle between the real and fitted rotation axes.
        angle = acos(dot(axis, rot_axis))
        if angle > pi/2:
            angle = acos(dot(axis, -rot_axis))
        self.assertAlmostEqual(angle, 0.0, 2)

        # Check the cone angle of 40 deg.
        self.assertAlmostEqual(cdp.cone_theta * 2.0, 40.0 / 360.0 * 2.0 * pi, 1)


    def test_cam_iso_cone_free_rotor2(self):
        """Test the second isotropic cone, free rotor frame order model of CaM."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'cam'+sep+'iso_cone_free_rotor2.py')

        # Switch to the correct data pipe.
        self.interpreter.pipe.switch('frame order')

        # The base data.
        pivot = array([ 37.254, 0.5, 16.7465])
        com = array([ 26.83678091, -12.37906417,  28.34154128])
        pivot_com_axis = com - pivot
        rot_axis = array([-0.4043088, -0.49985692,  0.76594873])

        # The rotation axis.
        self.interpreter.pipe.switch('frame order')
        spherical_vect = zeros(3, float64)
        spherical_vect[0] = 1.0
        spherical_vect[1] = cdp.axis_theta
        spherical_vect[2] = cdp.axis_phi
        axis = zeros(3, float64)
        spherical_to_cartesian(spherical_vect, axis)
        print("\nReal rotation axis:   %s" % repr(rot_axis))
        print("Fitted rotation axis: %s" % repr(axis))

        # Check the angle between the real and fitted rotation axes.
        angle = acos(dot(axis, rot_axis))
        if angle > pi/2:
            angle = acos(dot(axis, -rot_axis))
        self.assertAlmostEqual(angle, 0.0, 2)

        # Check the cone angle of 40 deg.
        self.assertAlmostEqual(cdp.cone_theta * 2.0, 40.0 / 360.0 * 2.0 * pi, 2)


    def test_cam_rigid(self):
        """Test the rigid frame order model of CaM."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'cam'+sep+'rigid.py')

        # Check the average structure atomic positions (to only one decimal point as the PDB file accuracy isn't great).
        ave_pos = ds['ave pos'].structure.structural_data[0].mol[0]
        orig_pos = ds['orig pos'].structure.structural_data[0].mol[0]
        for i in range(len(ave_pos.atom_name)):
            self.assertAlmostEqual(ave_pos.x[i], orig_pos.x[i], 1)
            self.assertAlmostEqual(ave_pos.y[i], orig_pos.y[i], 1)
            self.assertAlmostEqual(ave_pos.z[i], orig_pos.z[i], 1)


    def test_cam_rotor(self):
        """Test the rotor frame order model of CaM."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'cam'+sep+'rotor.py')

        # Switch to the correct data pipe.
        self.interpreter.pipe.switch('frame order')

        # The base data.
        pivot = array([ 37.254, 0.5, 16.7465])
        com = array([ 26.83678091, -12.37906417,  28.34154128])
        pivot_com_axis = com - pivot
        rot_axis = pivot_com_axis / norm(pivot_com_axis)

        # The average position checks.
        real_pos = array([[-0.31334613, -0.88922808, -0.33329811],
                          [ 0.93737972, -0.23341205, -0.2585306 ],
                          [ 0.15209688, -0.39343645,  0.90668313]], float64)
        ave_pos = zeros((3, 3), float64)
        euler_to_R_zyz(cdp.ave_pos_alpha, cdp.ave_pos_beta, cdp.ave_pos_gamma, ave_pos)
        print("\nReal domain position:\n%s" % repr(real_pos))
        print("Fitted domain position:\n%s" % repr(ave_pos))
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(ave_pos[i, j], real_pos[i, j], 3)

        # The axis system.
        axis = zeros(3, float64)
        spherical_to_cartesian(array([1, cdp.axis_theta, cdp.axis_phi]), axis)
        print("\nReal rotation axis:   %s" % repr(rot_axis))
        print("Fitted rotation axis: %s" % repr(axis))

        # Check the angle between the real and fitted rotation axes.
        angle = acos(dot(axis, rot_axis))
        if angle > pi/2:
            angle = acos(dot(axis, -rot_axis))
        self.assertAlmostEqual(angle, 0.0, 2)

        # Check the cone angle of 60 deg.
        self.assertAlmostEqual(cdp.cone_sigma_max * 2.0, 60.0 / 360.0 * 2.0 * pi, 1)


    def test_cam_rotor2(self):
        """Test the second rotor frame order model of CaM."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'cam'+sep+'rotor2.py')

        # Switch to the correct data pipe.
        self.interpreter.pipe.switch('frame order')

        # The base data.
        pivot = array([ 37.254, 0.5, 16.7465])
        com = array([ 26.83678091, -12.37906417,  28.34154128])
        pivot_com_axis = com - pivot
        rot_axis = array([ 0.40416535,  0.49967956,  0.76614014])

        # The average position checks.
        real_pos = array([[-0.31334613, -0.88922808, -0.33329811],
                          [ 0.93737972, -0.23341205, -0.2585306 ],
                          [ 0.15209688, -0.39343645,  0.90668313]], float64)
        ave_pos = zeros((3, 3), float64)
        euler_to_R_zyz(cdp.ave_pos_alpha, cdp.ave_pos_beta, cdp.ave_pos_gamma, ave_pos)
        print("\nReal domain position:\n%s" % repr(real_pos))
        print("Fitted domain position:\n%s" % repr(ave_pos))
        for i in range(3):
            for j in range(3):
                self.assertAlmostEqual(ave_pos[i, j], real_pos[i, j], 1)

        # The axis system.
        axis = zeros(3, float64)
        spherical_to_cartesian(array([1, cdp.axis_theta, cdp.axis_phi]), axis)
        print("\nReal rotation axis:   %s" % repr(rot_axis))
        print("Fitted rotation axis: %s" % repr(axis))

        # Check the angle between the real and fitted rotation axes.
        angle = acos(dot(axis, rot_axis))
        if angle > pi/2:
            angle = acos(dot(axis, -rot_axis))
        self.assertAlmostEqual(angle, 0.0, 2)

        # Check the cone angle of 60 deg.
        self.assertAlmostEqual(cdp.cone_sigma_max * 2.0, 60.0 / 360.0 * 2.0 * pi, 1)


    def test_model_free_rotor(self):
        """Test the free rotor frame order model."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'model_calcs'+sep+'free_rotor.py')

        # Check the calculated chi2 value.
        self.assertAlmostEqual(ds.chi2, 0.0216067401326)


    def test_model_free_rotor_eigenframe(self):
        """Test the free rotor frame order model in the eigenframe."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'model_calcs'+sep+'free_rotor_eigenframe.py')

        # Check the calculated chi2 value.
        self.assertAlmostEqual(ds.chi2, 0.00673210578744)


    def test_model_iso_cone(self):
        """Test the isotropic cone frame order model."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'model_calcs'+sep+'iso_cone.py')

        # The reference chi2 values.
        chi2_ref = []
        chi2_ref.append(0.131890484593)
        chi2_ref.append(0.0539383731611)
        chi2_ref.append(0.0135056297016)
        chi2_ref.append(0.0163432453475)
        chi2_ref.append(0.0775570503917)
        chi2_ref.append(0.0535055367493)
        chi2_ref.append(0.0994746492483)
        chi2_ref.append(0.174830826376)
        chi2_ref.append(0.193036744906)
        chi2_ref.append(0.181480810794)
        chi2_ref.append(0.215863920824)
        chi2_ref.append(0.170088692559)
        chi2_ref.append(0.152634493383)
        chi2_ref.append(0.168711907446)
        chi2_ref.append(0.168405354086)
        chi2_ref.append(0.247439860108)
        chi2_ref.append(0.143487410228)
        chi2_ref.append(0.148318989268)

        # Check the calculated chi2 values.
        for i in range(18):
            self.assertAlmostEqual(ds.chi2[i], chi2_ref[i])


    def test_model_iso_cone_free_rotor(self):
        """Test the free rotor isotropic cone frame order model."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'model_calcs'+sep+'iso_cone_free_rotor.py')

        # The reference chi2 values.
        chi2_ref = []
        chi2_ref.append(0.0177292447567 )
        chi2_ref.append(0.0187585146766 )
        chi2_ref.append(0.0440519894909 )
        chi2_ref.append(0.0225223798489 )
        chi2_ref.append(0.0239979046491 )
        chi2_ref.append(0.0161048633259 )
        chi2_ref.append(0.0267310958091 )
        chi2_ref.append(0.0219820914478 )
        chi2_ref.append(0.0194880630576 )
        chi2_ref.append(0.0348242343833 )
        chi2_ref.append(0.0401631858563 )
        chi2_ref.append(0.0327461783858 )
        chi2_ref.append(0.0391082177884 )
        chi2_ref.append(0.0467056691507 )
        chi2_ref.append(0.0407175857557 )
        chi2_ref.append(0.0441514158832 )
        chi2_ref.append(0.042078718831  )
        chi2_ref.append(0.0403856796359 )

        # Check the calculated chi2 values.
        for i in range(18):
            self.assertAlmostEqual(ds.chi2[i], chi2_ref[i])


    def test_model_iso_cone_free_rotor_eigenframe(self):
        """Test the free rotor isotropic cone frame order model in the eigenframe."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'model_calcs'+sep+'iso_cone_free_rotor_eigenframe.py')

        # The reference chi2 values.
        chi2_ref = []
        chi2_ref.append(0.115175446978 )
        chi2_ref.append(0.156911214374 )
        chi2_ref.append(0.209198723492 )
        chi2_ref.append(0.155297079942 )
        chi2_ref.append(0.0684780584219)
        chi2_ref.append(0.0781922435531)
        chi2_ref.append(0.103777394815 )
        chi2_ref.append(0.173740596864 )
        chi2_ref.append(0.199867814969 )
        chi2_ref.append(0.297587241555 )
        chi2_ref.append(0.308539214325 )
        chi2_ref.append(0.2543934866   )
        chi2_ref.append(0.168985365277 )
        chi2_ref.append(0.190780393086 )
        chi2_ref.append(0.186482798104 )
        chi2_ref.append(0.153839910288 )
        chi2_ref.append(0.160863854198 )
        chi2_ref.append(0.157029368992 )

        # Check the calculated chi2 values.
        for i in range(18):
            self.assertAlmostEqual(ds.chi2[i], chi2_ref[i])


    def test_model_pseudo_ellipse(self):
        """Test the pseudo-ellipse frame order model."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'model_calcs'+sep+'pseudo_ellipse.py')

        # The reference chi2 values.
        chi2_ref = []
        chi2_ref.append(0.0208490007203)
        chi2_ref.append(0.00958146486076)
        chi2_ref.append(0.0405488536626)
        chi2_ref.append(0.0370142845551)
        chi2_ref.append(0.0204537537661)
        chi2_ref.append(0.0186122056988)
        chi2_ref.append(0.0177783016875)
        chi2_ref.append(0.0311747995923)
        chi2_ref.append(0.0225532898175)
        chi2_ref.append(0.0212562065194)
        chi2_ref.append(0.018939663528)
        chi2_ref.append(0.0224686987165)
        chi2_ref.append(0.0201247095045)
        chi2_ref.append(0.0215343817478)
        chi2_ref.append(0.016509302331)
        chi2_ref.append(0.0101988814638)
        chi2_ref.append(0.00989431182393)
        chi2_ref.append(0.0123400971524)

        # Check the calculated chi2 values.
        for i in range(18):
            self.assertAlmostEqual(ds.chi2[i], chi2_ref[i])


    def test_model_pseudo_ellipse_free_rotor(self):
        """Test the free rotor pseudo-elliptic cone frame order model."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'model_calcs'+sep+'pseudo_ellipse_free_rotor.py')

        # The reference chi2 values.
        chi2_ref = [[], []]
        chi2_ref[0].append(0.0493245760341)
        chi2_ref[0].append(0.0322727678945)
        chi2_ref[0].append(0.0399505883966)
        chi2_ref[0].append(0.0122539315721)
        chi2_ref[0].append(0.0263840505182)
        chi2_ref[0].append(0.0324871952484)
        chi2_ref[0].append(0.0247369735031)
        chi2_ref[0].append(0.0231896861006)
        chi2_ref[0].append(0.0285947802273)
        chi2_ref[0].append(0.0345542627808)
        chi2_ref[0].append(0.0289869422491)
        chi2_ref[0].append(0.0243038470127)
        chi2_ref[0].append(0.0226686034191)
        chi2_ref[0].append(0.0215714556045)
        chi2_ref[0].append(0.0173836730495)
        chi2_ref[0].append(0.0182530810025)
        chi2_ref[0].append(0.0212669211551)
        chi2_ref[0].append(0.0194359136977)

        chi2_ref[1].append(0.0205287391277)
        chi2_ref[1].append(0.0246463829816)
        chi2_ref[1].append(0.0590186061204)
        chi2_ref[1].append(0.0441193978727)
        chi2_ref[1].append(0.0424299319779)
        chi2_ref[1].append(0.032589994611)
        chi2_ref[1].append(0.0523532207508)
        chi2_ref[1].append(0.0488535879384)
        chi2_ref[1].append(0.0424063218455)
        chi2_ref[1].append(0.0553525984677)
        chi2_ref[1].append(0.0495587286781)
        chi2_ref[1].append(0.0446625345909)
        chi2_ref[1].append(0.0470718361239)
        chi2_ref[1].append(0.0493615476721)
        chi2_ref[1].append(0.0492208206006)
        chi2_ref[1].append(0.0429966323771)
        chi2_ref[1].append(0.0442849187057)
        chi2_ref[1].append(0.0436756306414)
            
        # Check the calculated chi2 values.
        for j in range(2):
            for i in range(18):
                self.assertAlmostEqual(ds.chi2[j][i], chi2_ref[j][i])


    def test_model_pseudo_ellipse_torsionless(self):
        """Test the pseudo-ellipse frame order model."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'model_calcs'+sep+'pseudo_ellipse_torsionless.py')

        # The reference chi2 values.
        chi2_ref = []
        chi2_ref.append(0.340228489225)
        chi2_ref.append(0.260847963487)
        chi2_ref.append(0.250610744982)
        chi2_ref.append(0.228947619476)
        chi2_ref.append(0.251996758815)
        chi2_ref.append(0.238724080817)
        chi2_ref.append(0.182383602599)
        chi2_ref.append(0.172830852017)
        chi2_ref.append(0.159757813028)
        chi2_ref.append(0.173833227524)
        chi2_ref.append(0.156168102428)
        chi2_ref.append(0.171406869781)
        chi2_ref.append(0.202653838515)
        chi2_ref.append(0.198919351788)
        chi2_ref.append(0.169463187543)
        chi2_ref.append(0.156867571611)
        chi2_ref.append(0.146139931983)
        chi2_ref.append(0.13307108095 )

        # Check the calculated chi2 values.
        for i in range(18):
            self.assertAlmostEqual(ds.chi2[i], chi2_ref[i])


    def test_model_rotor(self):
        """Test the rotor frame order model."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'model_calcs'+sep+'rotor.py')

        # The reference chi2 values.
        chi2_ref = []
        chi2_ref.append(0.00410277546707 )
        chi2_ref.append(0.00112443204411 )
        chi2_ref.append(0.00759196190331 )
        chi2_ref.append(0.0956596925692  )
        chi2_ref.append(0.223717470059   )
        chi2_ref.append(0.136723330704   )
        chi2_ref.append(0.0588253217034  )
        chi2_ref.append(0.0774693384156  )
        chi2_ref.append(0.0855477856492  )
        chi2_ref.append(0.198089516589   )
        chi2_ref.append(0.227537351664   )
        chi2_ref.append(0.202005777915   )
        chi2_ref.append(0.192550395736   )
        chi2_ref.append(0.126007906472   )
        chi2_ref.append(0.124053264662   )
        chi2_ref.append(0.18203965973    )
        chi2_ref.append(0.191062017006   )
        chi2_ref.append(0.13580013153    )

        # Check the calculated chi2 values.
        for i in range(18):
            self.assertAlmostEqual(ds.chi2[i], chi2_ref[i])


    def test_model_rotor_eigenframe(self):
        """Test the rotor frame order model in the eigenframe."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'model_calcs'+sep+'rotor_eigenframe.py')

        # The reference chi2 values.
        chi2_ref = []
        chi2_ref.append(0.00308229284128)
        chi2_ref.append(0.0117874014708 )
        chi2_ref.append(0.0016108171487 )
        chi2_ref.append(0.00532862954549)
        chi2_ref.append(0.097784753109  )
        chi2_ref.append(0.157147901966  )
        chi2_ref.append(0.182397051711  )
        chi2_ref.append(0.338977916543  )
        chi2_ref.append(0.208516866654  )
        chi2_ref.append(0.137660115226  )
        chi2_ref.append(0.0580816149373 )
        chi2_ref.append(0.0476543367845 )
        chi2_ref.append(0.0360689584006 )
        chi2_ref.append(0.0118024492136 )
        chi2_ref.append(0.0824307041139 )
        chi2_ref.append(0.0920614159956 )
        chi2_ref.append(0.0936464288916 )
        chi2_ref.append(0.0823025718101 )

        # Check the calculated chi2 values.
        for i in range(18):
            self.assertAlmostEqual(ds.chi2[i], chi2_ref[i])


    def test_opendx_map(self):
        """Test the mapping of the Euler angle parameters for OpenDx viewing."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'opendx_euler_angle_map.py')


    def test_opt_rigid_no_rot(self):
        """Test the 'rigid' model for unrotated tensors with no motion."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'opt_rigid_no_rot.py')

        # Get the debugging message.
        self.mesg = self.mesg_opt_debug()

        # Test the values.
        self.assertEqual(cdp.iter, 92, msg=self.mesg)
        self.assertEqual(cdp.chi2, 0.0, msg=self.mesg)
        self.assertEqual(cdp.ave_pos_alpha, 0.0, msg=self.mesg)
        self.assertEqual(cdp.ave_pos_beta, 0.0, msg=self.mesg)
        self.assertEqual(cdp.ave_pos_gamma, 0.0, msg=self.mesg)


    def test_opt_rigid_rand_rot(self):
        """Test the 'rigid' model for randomly rotated tensors with no motion."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'opt_rigid_rand_rot.py')

        # Get the debugging message.
        self.mesg = self.mesg_opt_debug()

        # Test the values.
        self.assertAlmostEqual(cdp.chi2, 3.085356555118994e-26, msg=self.mesg)
        self.assertAlmostEqual(cdp.ave_pos_alpha, 5.0700283197712777, msg=self.mesg)
        self.assertAlmostEqual(cdp.ave_pos_beta, 2.5615753919522359, msg=self.mesg)
        self.assertAlmostEqual(cdp.ave_pos_gamma, 0.64895449611163691, msg=self.mesg)


    def test_parametric_restriction_iso_cone_to_iso_cone_free_rotor(self):
        """Parametric restriction of the isotropic cone to the free rotor isotropic cone frame order model."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'parametric_restriction'+sep+'iso_cone_to_iso_cone_free_rotor.py')

        # The reference chi2 values.
        chi2_ref = []
        chi2_ref.append(0.0177292447567 )
        chi2_ref.append(0.0187585146766 )
        chi2_ref.append(0.0440519894909 )
        chi2_ref.append(0.0225223798489 )
        chi2_ref.append(0.0239979046491 )
        chi2_ref.append(0.0161048633259 )
        chi2_ref.append(0.0267310958091 )
        chi2_ref.append(0.0219820914478 )
        chi2_ref.append(0.0194880630576 )
        chi2_ref.append(0.0348242343833 )
        chi2_ref.append(0.0401631858563 )
        chi2_ref.append(0.0327461783858 )
        chi2_ref.append(0.0391082177884 )
        chi2_ref.append(0.0467056691507 )
        chi2_ref.append(0.0407175857557 )
        chi2_ref.append(0.0441514158832 )
        chi2_ref.append(0.042078718831  )
        chi2_ref.append(0.0403856796359 )

        # Check the calculated chi2 values.
        for i in range(18):
            self.assertAlmostEqual(ds.chi2[i], chi2_ref[i])


    def test_parametric_restriction_pseudo_ellipse_to_iso_cone(self):
        """Parametric restriction of the pseudo-ellipse to the isotropic cone frame order model."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'parametric_restriction'+sep+'pseudo_ellipse_to_iso_cone.py')

        # The reference chi2 values.
        chi2_ref = []
        chi2_ref.append(0.131890484593)
        chi2_ref.append(0.0539383731611)
        chi2_ref.append(0.0135056297016)
        chi2_ref.append(0.0163432453475)
        chi2_ref.append(0.0775570503917)
        chi2_ref.append(0.0535055367493)
        chi2_ref.append(0.0994746492483)
        chi2_ref.append(0.174830826376)
        chi2_ref.append(0.193036744906)
        chi2_ref.append(0.181480810794)
        chi2_ref.append(0.215863920824)
        chi2_ref.append(0.170088692559)
        chi2_ref.append(0.152634493383)
        chi2_ref.append(0.168711907446)
        chi2_ref.append(0.168405354086)
        chi2_ref.append(0.247439860108)
        chi2_ref.append(0.143487410228)
        chi2_ref.append(0.148318989268)

        # Check the calculated chi2 values.
        for i in range(18):
            self.assertAlmostEqual(ds.chi2[i], chi2_ref[i])


    def test_parametric_restriction_pseudo_ellipse_to_iso_cone_free_rotor(self):
        """Parametric restriction of the pseudo-ellipse to the free rotor isotropic cone frame order model."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'parametric_restriction'+sep+'pseudo_ellipse_to_iso_cone_free_rotor.py')

        # The reference chi2 values.
        chi2_ref = []
        chi2_ref.append(0.0177292447567 )
        chi2_ref.append(0.0187585146766 )
        chi2_ref.append(0.0440519894909 )
        chi2_ref.append(0.0225223798489 )
        chi2_ref.append(0.0239979046491 )
        chi2_ref.append(0.0161048633259 )
        chi2_ref.append(0.0267310958091 )
        chi2_ref.append(0.0219820914478 )
        chi2_ref.append(0.0194880630576 )
        chi2_ref.append(0.0348242343833 )
        chi2_ref.append(0.0401631858563 )
        chi2_ref.append(0.0327461783858 )
        chi2_ref.append(0.0391082177884 )
        chi2_ref.append(0.0467056691507 )
        chi2_ref.append(0.0407175857557 )
        chi2_ref.append(0.0441514158832 )
        chi2_ref.append(0.042078718831  )
        chi2_ref.append(0.0403856796359 )

        # Check the calculated chi2 values.
        for i in range(18):
            self.assertAlmostEqual(ds.chi2[i], chi2_ref[i])


    def test_parametric_restriction_pseudo_ellipse_free_rotor_to_iso_cone(self):
        """Parametric restriction of the pseudo-ellipse to the isotropic cone frame order model."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'parametric_restriction'+sep+'pseudo_ellipse_free_rotor_to_iso_cone.py')

        # The reference chi2 values.
        chi2_ref = []
        chi2_ref.append(16957.4964577)
        chi2_ref.append(15727.13869)
        chi2_ref.append(13903.0982799)
        chi2_ref.append(11719.9390681)
        chi2_ref.append(9488.44060873)
        chi2_ref.append(7425.57820642)
        chi2_ref.append(5713.6467735)
        chi2_ref.append(4393.3273949)
        chi2_ref.append(3452.97770868)
        chi2_ref.append(2771.90973598)
        chi2_ref.append(2247.44444894)
        chi2_ref.append(1788.58977266)
        chi2_ref.append(1348.38250916)
        chi2_ref.append(921.060703519)
        chi2_ref.append(539.03217075)
        chi2_ref.append(244.341444558)
        chi2_ref.append(58.4566671195)
        chi2_ref.append(0.148318989268)

        # Check the calculated chi2 values.
        for i in range(18):
            self.assertAlmostEqual(ds.chi2[i], chi2_ref[i])


    def test_parametric_restriction_pseudo_ellipse_free_rotor_to_iso_cone_free_rotor(self):
        """Parametric restriction of the free rotor pseudo-ellipse to the free rotor isotropic cone frame order model."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'parametric_restriction'+sep+'pseudo_ellipse_free_rotor_to_iso_cone_free_rotor.py')

        # The reference chi2 values.
        chi2_ref = []
        chi2_ref.append(0.0177292447567 )
        chi2_ref.append(0.0187585146766 )
        chi2_ref.append(0.0440519894909 )
        chi2_ref.append(0.0225223798489 )
        chi2_ref.append(0.0239979046491 )
        chi2_ref.append(0.0161048633259 )
        chi2_ref.append(0.0267310958091 )
        chi2_ref.append(0.0219820914478 )
        chi2_ref.append(0.0194880630576 )
        chi2_ref.append(0.0348242343833 )
        chi2_ref.append(0.0401631858563 )
        chi2_ref.append(0.0327461783858 )
        chi2_ref.append(0.0391082177884 )
        chi2_ref.append(0.0467056691507 )
        chi2_ref.append(0.0407175857557 )
        chi2_ref.append(0.0441514158832 )
        chi2_ref.append(0.042078718831  )
        chi2_ref.append(0.0403856796359 )

        # Check the calculated chi2 values.
        for i in range(18):
            self.assertAlmostEqual(ds.chi2[i], chi2_ref[i])


    def test_pseudo_ellipse(self):
        """Test the pseudo-ellipse target function."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'pseudo_ellipse.py')

        # The reference chi2 value.
        chi2 = 0.015865464136741975

        # Check the surrounding space.
        self.space_probe(ref_chi2=chi2, params=['ave_pos_alpha', 'ave_pos_beta', 'ave_pos_gamma', 'eigen_alpha', 'eigen_beta', 'eigen_gamma', 'cone_theta_x', 'cone_theta_y', 'cone_sigma_max'])


    def test_pseudo_ellipse_torsionless(self):
        """Test the torsionless pseudo-ellipse target function."""

        # Execute the script.
        self.script_exec(status.install_path + sep+'test_suite'+sep+'system_tests'+sep+'scripts'+sep+'frame_order'+sep+'pseudo_ellipse_torsionless.py')

        # The reference chi2 value.
        chi2 = 2.8393866813588198

        # Check the surrounding space.
        self.space_probe(ref_chi2=chi2, params=['ave_pos_alpha', 'ave_pos_beta', 'ave_pos_gamma', 'eigen_alpha', 'eigen_beta', 'eigen_gamma', 'cone_theta_x', 'cone_theta_y'])
