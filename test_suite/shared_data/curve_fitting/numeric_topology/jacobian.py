# Script for numerically calculating the exponential curve gradient.

# Python module imports.
from math import exp
from numpy import array
from numdifftools import Jacobian


def func(params):
    """Back-calculate the intensities."""

    global times, I, errors

    # Unpack the parameters.
    R, I0 = params

    # The intensities.
    back_calc = []
    for i in range(len(times)):
        back_calc.append(I0 * exp(-R*times[i]))

    # Return the back-calculated intensities.
    return array(back_calc)


# The real parameters.
R = 1.0
I0 = 1000.0

# The time points.
times = [0.0, 1.0, 2.0, 3.0, 4.0]

# The intensities for the above I0 and R.
I = [1000.0, 367.879441171, 135.335283237, 49.7870683679, 18.3156388887]

# The intensity errors.
errors = [10.0, 10.0, 10.0, 10.0, 10.0]

# Set up the Jacobian function.
jacobian = Jacobian(func)

# The numeric Jacobian at the minimum.
print("\n\nOn-minimum:\n")
matrix = jacobian([R, I0])
print("The Jacobian at %s is:\n%s" % ([R, I0], matrix))

# The numeric Jacobian off the minimum.
print("\n\nOff-minimum:\n")
R = 2.0
I0 = 500.0
matrix = jacobian([R, I0])
print("The Jacobian at %s is:\n%s" % ([R, I0], matrix))
