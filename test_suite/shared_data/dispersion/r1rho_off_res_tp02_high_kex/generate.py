"""Simulate relaxation curves for an on resonance R1rho-type experiment using the M61 model.

This is the Meiboom 1961 model for on-resonance 2-site exchange with skewed populations (pA >> pB).  The equation is:

                                                  pA.pB.delta_w^2.kex
    R1rho = R1*cos(theta) + R2*sin(theta) + ---------------------------------*sin(theta) ,
                                            w_aeff^2.w_beff^2/w_eff^2 + kex^2 

where R2 is the R1rho value in the absence of exchange, kex is the chemical exchange rate constant, pA and pB are the populations of states A and B, delta_w is the chemical shift difference between the two states, and omega_1 = omega_e is the effective field in the rotating frame.

To run the script, simply type:

$ ../../../../relax generate.py --tee generate.log
"""

# Python module imports.
from math import atan, cos, exp, pi, sin
from numpy import array, float64

# relax module imports.
from lib.spectrum.sparky import write_list


# Setup for 2 spin systems.
i0 = array([[1e8, 1.5e8], [2e7, 2.5e7]], float64)    # Initial peak intensities per spin and per field.
times = array([0.0, 0.1], float64)    # The relaxation delay times in seconds.
spin_lock = array([1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000], float64)    # The spin-lock field strengths in Hz.
spin_lock_offset = 110.0    # The spin-lock frequency in ppm.
r1rho_prime = array([[10.0, 15.0], [12.0, 18.0]], float64)  # The R1rho' value per spin and per field.
r1 = array([[1.0, 1.2], [1.1, 1.3]], float64)    # The R1 value per spin and per field.
r1_err = 0.1
pA = 0.7654321
kex = 2e5
delta_omega = array([7.0, 9.0], float64)    # The chemical shift difference in ppm.
frqs = array([-50.6985939545, -81.1177503272], float64)
frq_label = ['500MHz', '800MHz']

# Setup for the Sparky peak list.
res_names = ['Trp', 'Lys']
res_nums = [1, 2]
atomN_names = ['N', 'N']
atomH_names = ['HN', 'HN']
wN = array([122.454, 111.978], float64)
wH = array([8.397, 8.720], float64)

# Calculate some parameters.
pB = 1.0 - pA

# Loop over the spectrometer frequencies.
for frq_index in range(len(frqs)):
    # Convert the values from ppm to rad/s.
    frq = 2.0 * pi * frqs[frq_index]
    dw = delta_omega * frq
    omega_rf = spin_lock_offset * frq
    wN_frq = wN * frq

    # Set up the data for the R1 file.
    label = 'R1_%s' % frq_label[frq_index]
    pipe.create(label, 'mf')
    cdp.ri_ids = ['r1']
    for i in range(len(res_names)):
        spin.create(res_name=res_names[i], res_num=res_nums[i], spin_name=atomN_names[i])
        cdp.mol[0].res[i].spin[0].ri_data = {}
        cdp.mol[0].res[i].spin[0].ri_data_err = {}
        cdp.mol[0].res[i].spin[0].ri_data['r1'] = r1[i, frq_index]
        cdp.mol[0].res[i].spin[0].ri_data_err['r1'] = r1_err
    relax_data.write(ri_id='r1', file='%s.out'%label, force=True)

    # Frequency dependent parameters.
    omega_a = wN_frq
    omega_b = wN_frq + dw
    omega_ave = pA*omega_a + pB*omega_b
    delta_a = omega_a - omega_rf 
    delta_b = omega_b - omega_rf 
    delta_ave = omega_ave - omega_rf

    # Loop over the spin-lock fields.
    for spin_lock_index in range(len(spin_lock)):
        # Spin-lock dependent parameters.
        omega1 = spin_lock[spin_lock_index] * 2.0 * pi
        omega_aeff2 = omega1**2 + delta_a**2
        omega_beff2 = omega1**2 + delta_b**2
        omega_eff2 = omega1**2 + delta_ave**2

        # Loop over the relaxation times.
        for time_index in range(len(times)):
            # Loop over the spins.
            intensities = []
            for spin_index in range(len(r1rho_prime)):
                # Spin dependent parameters.
                theta = atan(omega1 / delta_ave[spin_index])
                sin_theta2 = sin(theta)**2
                cos_theta2 = cos(theta)**2

                # The rate.
                nomen = pA * pB * dw[spin_index]**2 * kex
                denom = omega_aeff2[spin_index] * omega_beff2[spin_index] / omega_eff2[spin_index] + kex**2
                rx = r1[spin_index, frq_index] * cos_theta2 + sin_theta2 * (r1rho_prime[spin_index, frq_index] + nomen / denom)
    
                # The peak intensity.
                intensities.append(i0[spin_index, frq_index] * exp(-rx*times[time_index]))

            # Create a Sparky .list file.
            if time_index == 0 and spin_lock_index == 0:
                name = 'ref_%s' % frq_label[frq_index]
            elif time_index == 0:
                name = None
            else:
                name = 'nu_%s_%s' % (spin_lock[spin_lock_index], frq_label[frq_index])
            if name:
                write_list(file_prefix=name, dir=None, res_names=res_names, res_nums=res_nums, atom1_names=atomN_names, atom2_names=atomH_names, w1=wN, w2=wH, data_height=intensities)
