"""Script for calculating R2eff values, generating input files for CPMGFit, and executing CPMGFit.

To run:

$ ../../../../../relax sherekhan.py
"""

# Python module imports.
from os import sep

# relax module imports.
from status import Status; status = Status()


# Load the saved state.
data_path = status.install_path + sep+'test_suite'+sep+'shared_data'+sep+'dispersion'+sep+'Hansen'
state.load(data_path+sep+'r2eff_values')

# Generate the input files.
relax_disp.sherekhan_input(force=True)
