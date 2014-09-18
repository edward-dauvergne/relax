""" Test functions for numdifftools module

"""
import unittest
import numdifftools as nd
import numpy as np


class TestDerivative(unittest.TestCase):
    def test_vec2mat(self):
        mat = nd.core.vec2mat(np.arange(6), n=2, m=3)
        self.assertListEqual(mat.tolist(), [[0, 1, 2], [1, 2, 3]])
        
    def test_derivative_cube(self):
        '''Test for Issue 7'''
        cube = lambda x : x*x*x
        dcube = nd.Derivative(cube)
        shape = (3, 2)
        x = np.ones(shape)*2
        dx = dcube(x)
        self.assertListEqual(list(dx.shape), list(shape), 'Shape mismatch')
        for i, (val, tval) in enumerate(zip(dx.ravel(), (3*x**2).ravel())):
            self.assertAlmostEqual(val, tval,places=12,
                                   msg='First differing element %d\n value = %g, \n true value = %g' % (i, val, tval))

    def test_derivative_exp(self):
        # derivative of exp(x), at x == 0
        dexp = nd.Derivative(np.exp)
        self.assertAlmostEqual(dexp(0), np.exp(0))
        dexp.n = 2
        t = dexp(0)
        self.assertAlmostEqual(t, np.exp(0))

    def test_derivative_sin(self):
        # Evaluate the indicated (default = first)
        # derivative at multiple points
        dsin = nd.Derivative(np.sin)
        x = np.linspace(0, 2. * np.pi, 13)
        y = dsin(x)
        small = np.abs(y - np.cos(x)) < dsin.error_estimate * 10
        # print np.abs(y - np.cos(x))
        # print dsin.error_estimate
        # print small
        self.assertTrue(np.all(small))

    def test_high_order_derivative_sin(self):
        # Higher order derivatives (second derivative)
        # Truth: 0
        d2sin = nd.Derivative(np.sin, n=2, step_max=0.5)

        self.assertAlmostEqual(d2sin(np.pi), 0.0,)

        # Higher order derivatives (up to the fourth derivative)
        # Truth: sqrt(2)/2 = 0.707106781186548
        d2sin.n = 4
        y = d2sin(np.pi / 4)
        small = np.abs(y - np.sqrt(2.) / 2.) < d2sin.error_estimate
        self.assertTrue(small)

    def test_high_order_derivative_cos(self):
        # Higher order derivatives (third derivative)
        # Truth: 1
        d3cos = nd.Derivative(np.cos, n=3)
        y = d3cos(np.pi / 2.0)
        small = np.abs(y - 1.0) < d3cos.error_estimate
        self.assertTrue(small)

    def test_backward_derivative_sinh(self):
        # Compute the derivative of a function using a backward difference scheme
        # And a backward scheme will only look below x0.
        dsinh = nd.Derivative(np.sinh, method='backward')
        small = np.abs(dsinh(0.0) - np.cosh(0.0)) < dsinh.error_estimate
        self.assertTrue(small)

    def test_central_n_forward_derivative_log(self):
        # Although a central rule may put some samples in the wrong places, it
        # may still succeed
        dlog = nd.Derivative(np.log, method='central')
        x = 0.001
        small = np.abs(dlog(x) - 1.0 / x) < dlog.error_estimate
        self.assertTrue(small)

        # But forcing the use of a one-sided rule may be smart anyway
        dlog.method = 'forward'
        small = np.abs(dlog(x) - 1 / x) < dlog.error_estimate
        self.assertTrue(small)

    def test_forward_derivative_tan(self):
        # Control the behavior of Derivative - forward 2nd order method, with only 1 Romberg term
        # Compute the first derivative, also return the final stepsize chosen
        #[deriv,err,fdelta] = derivest(@(x) tan(x),pi,'deriv',1,'Style','for','MethodOrder',2,'RombergTerms',1)
        dtan = nd.Derivative(
            np.tan, n=1, order=2, method='forward', romberg_terms=1)
        y = dtan(np.pi)
        abserr = dtan.error_estimate
        self.assertTrue(np.abs(y - 1) < abserr)

        dtan.finaldelta

        # Control the behavior of DERIVEST - forward 2nd order method, with only 1 Romberg term
        # Compute the first derivative, also return the final stepsize chosen
        dtan = nd.Derivative(
            np.tan, n=1, method='forward', order=2, romberg_terms=1)
        self.assertAlmostEqual(dtan(np.pi), 1.0)

    def test_derivative_poly1d(self):
        # Specify the step size (default stepsize = 0.1)
        p0 = np.poly1d(range(1, 6))
        fd = nd.Derivative(p0, n=4, romberg_terms=0) #, step_max=3, step_num=10)
        p4 = p0.deriv(4)
        self.assertAlmostEqual(fd(1), p4(1), places=5)


#    fun = lambda x: x**3 + x**4
#    fd3 = Derivative(fun,n=3)
# fd3([0,1])          #  True derivatives: [6,30]
#
# fd = Derivative(np.exp)              # 1'st derivative
# fdd = Derivative(np.exp,n=2)  # 2'nd derivative
#    d = fd(1)
#    d2 = fdd(1)
#
#    fun = lambda x : x[0] + x[1]**2 + x[2]**3
#    fd = Hessdiag(fun)
# hd = fd([1,2,3]) # HD = [ 0,2,18]
#    fd.error_estimate
#
#    rosen = lambda x : (1-x[0])**2 + 105*(x[1]-x[0]**2)**2
#    rd = Hessian(rosen)
# h = rd([1, 1])  #%  h =[ 842 -420; -420, 210];
#    rd.error_estimate
#
#%% Provide other parameters via an anonymous function
#% At a minimizer of a function, its derivative should be
#% essentially zero. So, first, find a local minima of a
#% first kind bessel function of order nu.
#nu = 0;
# fun = @(t) besselj(nu,t);
# fplot(fun,[0,10])
#x0 = fminbnd(fun,0,10,optimset('TolX',1.e-15))
# hold on
# plot(x0,fun(x0),'ro')
# hold off
#
#deriv = derivest(fun,x0,'d',1)
#
#%% The second derivative should be positive at a minimizer.
#deriv = derivest(fun,x0,'d',2)
#
#%% Compute the numerical gradient vector of a 2-d function
#% Note: the gradient at this point should be [4 6]
# fun = @(x,y) x.^2 + y.^2;
# xy = [2 3];
# gradvec = [derivest(@(x) fun(x,xy(2)),xy(1),'d',1), ...
#           derivest(@(y) fun(xy(1),y),xy(2),'d',1)]
#
#%% Compute the numerical Laplacian function of a 2-d function
#% Note: The Laplacian of this function should be everywhere == 4
# fun = @(x,y) x.^2 + y.^2;
# xy = [2 3];
# lapval = derivest(@(x) fun(x,xy(2)),xy(1),'d',2) + ...
#           derivest(@(y) fun(xy(1),y),xy(2),'d',2)
#
#%% Compute the derivative of a function using a central difference scheme
#% Sometimes you may not want your function to be evaluated
#% above or below a given point. A 'central' difference scheme will
#% look in both directions equally.
#[deriv,err] = derivest(@(x) sinh(x),0,'Style','central')
#
#%% Compute the derivative of a function using a forward difference scheme
#% But a forward scheme will only look above x0.
#[deriv,err] = derivest(@(x) sinh(x),0,'Style','forward')
#
#%% Compute the derivative of a function using a backward difference scheme
#% And a backward scheme will only look below x0.
#[deriv,err] = derivest(@(x) sinh(x),0,'Style','backward')
#
#%% Although a central rule may put some samples in the wrong places, it may still succeed
#[d,e,del]=derivest(@(x) log(x),.001,'style','central')
#
#%% But forcing the use of a one-sided rule may be smart anyway
#[d,e,del]=derivest(@(x) log(x),.001,'style','forward')
#
#%% Control the behavior of DERIVEST - forward 2nd order method, with only 1 Romberg term
#% Compute the first derivative, also return the final stepsize chosen
#[deriv,err,fdelta] = derivest(@(x) tan(x),pi,'deriv',1,'Style','for','MethodOrder',2,'RombergTerms',1)
#
#%% Functions should be vectorized for speed, but its not always easy to do.
#[deriv,err] = derivest(@(x) x.^2,0:5,'deriv',1)
#[deriv,err] = derivest(@(x) x^2,0:5,'deriv',1,'vectorized','no')
class TestJacobian(unittest.TestCase):

    def testjacobian(self):
        xdata = np.reshape(np.arange(0, 1, 0.1), (-1, 1))
        ydata = 1 + 2 * np.exp(0.75 * xdata)
        fun = lambda c: (c[0] + c[1] * np.exp(c[2] * xdata) - ydata) ** 2
        Jfun = nd.Jacobian(fun)
        J = Jfun([1, 2, 0.75])  # should be numerically zero
        for ji in J.ravel():
            self.assertAlmostEqual(ji, 0.0)


class TestGradient(unittest.TestCase):
    def testgradient(self):
        fun = lambda x: np.sum(x ** 2)
        dfun = nd.Gradient(fun)
        d = dfun([1, 2, 3])
        dtrue = [2., 4., 6.]
        for (di, dit) in zip(d, dtrue):
            self.assertAlmostEqual(di, dit)


class TestHessian(unittest.TestCase):

    def testhessian(self):
        #cos(x-y), at (0,0)
        cos = np.cos
        fun = lambda xy: cos(xy[0] - xy[1])
        Hfun2 = nd.Hessian(fun)
        h2 = Hfun2([0, 0])  # h2 = [-1 1; 1 -1];
        htrue = [-1., 1., 1., -1.]
        for (hi, hit) in zip(h2.ravel(), htrue):
            self.assertAlmostEqual(hi, hit)


class TestHessdiag(unittest.TestCase):

    def testhessdiag(self):
        fun = lambda x: x[0] + x[1] ** 2 + x[2] ** 3
        Hfun = nd.Hessdiag(fun)
        hd = Hfun([1, 2, 3])
        htrue = [0., 2., 18.]
        for (hi, hit) in zip(hd, htrue):
            self.assertAlmostEqual(hi, hit)


class TestGlobalFunctions(unittest.TestCase):

    def testvec2mat(self):
        mat = nd.core.vec2mat(np.arange(12), 3, 4)
        self.assertListEqual(mat.tolist(), [[0, 1, 2, 3],
                                            [1, 2, 3, 4],
                                            [2, 3, 4, 5]])

    def testdea3(self):
        Ei = np.zeros(3)
        linfun = lambda k: np.linspace(0, np.pi / 2., 2. ** (k + 5) + 1)
        for k in np.arange(3):
            x = linfun(k)
            Ei[k] = np.trapz(np.sin(x), x)
        [En, err] = nd.dea3(Ei[0], Ei[1], Ei[2])
        self.assertTrue(np.abs(En - 1) < err)
        self.assertAlmostEqual(En, 1.0)

if __name__ == '__main__':
    unittest.main()
