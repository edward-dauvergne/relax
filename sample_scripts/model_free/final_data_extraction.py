#####################################################################################
#          Script for Final Data Extraction after Model-free Analysis               #
#                                Michael Bieri                                      #
#                                  16.9.2009                                        #
#####################################################################################


# Extract Data to Table

# relax module imports.
from pipe_control.mol_res_spin import spin_loop



pipe.create('Data_extraction', 'mf')
results.read()

#create file

file = open('Model-free_Results.csv', 'w')

file.write('Data Extraction by Michael Bieri')
file.write("\n")
file.write("\n")
file.write("Residue,Model,S2,Rex\n")
file.write("\n")


for spin, spin_id in spin_loop(return_id=True):
            # The spin ID string.
            spin_no = spin_id[spin_id.index(':')+1:spin_id.index('&')]
            spin_res = spin_id[spin_id.index('&')+2:spin_id.index('@')]
            file.write((spin_res) + " " + (spin_no))
            # The spin is not selected.
            if not spin.select:
                file.write("\n")
                continue
            # Write separator.
            else:
                file.write(",")


            # The model-free model.
            if hasattr(spin, 'model'):
                spin.model = spin.model[1:2]
                file.write(spin.model)
            # Write separator.
            file.write(",")


            # S2.
            if  hasattr(spin, 's2'):
                s2 = str(spin.s2)
                if spin.s2 == None:
                        file.write("")
                else:
                        file.write(s2[0:5])

                        # Try to read the error, skip if no MC simulation was performed
                        try:
                            s2_err = str(spin.s2_err)
                            file.write( " +/- " + s2_err[0:4])
                        except:
                            a = 'No MC'

            # Write separator.
            file.write(",")


            # Rex.
            if hasattr(spin, 'rex'):
                rex = str(spin.rex)
                
                if spin.rex == None:
                        file.write("")
                else:
                        file.write(rex[0:5])

                        # Try to read the error, skip if no MC simulation was performed
                        try:
                            rex_err = str(spin.rex_err)
                            file.write( " +/- " + rex_err[0:4])
                        except:
                            a = 'No MC'

            # Write separator.
            file.write(",")

# Start a new line.
            file.write("\n")

# Close file.
file.close()


##################################################################################################

#Create Single Data Files


value.write(param='rex', file='rex.txt', dir='final_results', force=True)
value.write(param='s2', file='s2.txt', dir='final_results', force=True)
value.write(param='s2f', file='s2f.txt', dir='final_results', force=True)
value.write(param='s2s', file='s2s.txt', dir='final_results', force=True)
value.write(param='te', file='te.txt', dir='final_results', force=True)
value.write(param='tf', file='tf.txt', dir='final_results',  force=True)
value.write(param='ts', file='ts.txt', dir='final_results', force=True)
value.write(param='rex', file='rex.txt', dir='final_results', force=True)
value.write(param='r', file='r.txt', dir='final_results', force=True)
value.write(param='rex', file='rex.txt', dir='final_results', force=True)
value.write(param='csa', file='csa.txt', dir='final_results', force=True)
value.write(param='rex', file='rex.txt', dir='final_results', force=True)
value.write(param='local_tm', file='local_tm.txt', dir='final_results', force=True)

##################################################################################################

#Create Grace Plots

grace.write(x_data_type='res_num', y_data_type='s2', file='s2.agr', force=True)
grace.write(x_data_type='res_num', y_data_type='te', file='te.agr', force=True)
grace.write(x_data_type='res_num', y_data_type='s2f', file='s2f.agr', force=True)
grace.write(x_data_type='res_num', y_data_type='s2s', file='s2s.agr', force=True)
grace.write(x_data_type='res_num', y_data_type='ts', file='ts.agr', force=True)
grace.write(x_data_type='res_num', y_data_type='tf', file='tf.agr', force=True)
grace.write(x_data_type='res_num', y_data_type='csa', file='csa.agr', force=True)
grace.write(x_data_type='te', y_data_type='s2', file='s2-te.agr', force=True)


##################################################################################################

# Create S2 Macro for PyMol 

# relax module imports.
from pipe_control.mol_res_spin import spin_loop

#create file

file = open('s2.pml', 'w')

file.write("bg_color white\n")
file.write("color gray90\n")
file.write("hide all\n")
file.write("show ribbon\n")

for spin, spin_id in spin_loop(return_id=True):

#select residue
            spin_no = spin_id[spin_id.index(':')+1:spin_id.index('&')]


#ribbon color
            if  hasattr(spin, 's2'):
                s2 = str(spin.s2)
                if spin.s2 == None:
                        file.write("")
                else:
                        width = ((1-spin.s2) * 2)
                        green = 1 - ((spin.s2)**3) 
                        green = green * green * green #* green * green
                        green = 1 - green
                        file.write("set_color resicolor" + spin_no + ", [0," + str(green) + ",1]\n")
                        file.write("color resicolor" + spin_no + ", resi " + spin_no + "\n")
                        file.write("set_bond stick_radius, " + str(width) + ", resi " + spin_no + "\n")



file.write("hide all\n")
file.write("show sticks, name C+N+CA\n")
file.write("set stick_quality, 10\n")
file.write("ray\n")
file.close()


##################################################################################################

# Create Rex Macro for PyMol 

#create file

file = open('rex.pml', 'w')

file.write("bg_color white\n")
file.write("color gray90\n")
file.write("hide all\n")
file.write("show ribbon\n")

max_rex = 0

#find max Rex
for spin, spin_id in spin_loop(return_id=True):

            if  hasattr(spin, 'rex'):

                  if not spin.rex == None:
                       if spin.rex > max_rex:
                             max_rex = spin.rex 


for spin, spin_id in spin_loop(return_id=True):

#select residue
            spin_no = spin_id[spin_id.index(':')+1:spin_id.index('&')]
#ribbon color
            if  hasattr(spin, 'rex'):
                rex = str(spin.rex)
                if spin.rex == None:
                        file.write("")
                else:
                        rel_rex = spin.rex / max_rex
                        width = ((rel_rex) * 2)
                        green = ((rel_rex)) 
                        green = green * green * green #* green * green
                        green = 1 - green
                        file.write("set_color resicolor" + spin_no + ", [0," + str(green) + ",1]\n")
                        file.write("color resicolor" + spin_no + ", resi " + spin_no + "\n")
                        file.write("set_bond stick_radius, " + str(width) + ", resi " + spin_no + "\n")



file.write("hide all\n")
file.write("show sticks, name C+N+CA\n")
file.write("set stick_quality, 10\n")
file.write("ray\n")
file.close()


##################################################################################################

#Create Diffusion Tensor

# Try to read the diffusion tensor.
try:
    # Display the diffusion tensor.
    diffusion_tensor.display()

    # Create the tensor PDB file.
    tensor_file = 'tensor.pdb'
    structure.create_diff_tensor_pdb(file=tensor_file, force=True)

# No diffusion in model (local tm model)
except:
    print("No diffusion tensor found.")



##################################################################################################


print("")
print("")
print(" ---------- done ----------------")
print("")
print("")
print("Grace Plots are in Folder /grace/")
print("")
print("Signle Text Files for Relaxation Parameters are in Folder /final_results/")
print("")
print("Diffusion Tensor is in current Folder")
print("")
print("PyMol Macros are in current Folder - execute in PyMol with Command:")
print("@rex.pml and @s2.pml")




