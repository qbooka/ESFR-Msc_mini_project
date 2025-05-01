import matplotlib.pyplot as plt 
import openmc
import openmc.deplete
import numpy as np 

from structure_esfr import core_r, FA_height, geometry, fuel_outer_d, clad_outer_d, crod_insertion_length, geometry
from matter_esfr import inner_fuel, outer_fuel, sodium, clad_mat, EM10, follower, boron_carbide

# calculating volume
n_iFA = 225
n_oFA = 228
n_iCSD = 6
n_oCSD = 18

n_pins_FA = 270
n_pins_CSD = 198
n_crods_CSD = 73

volume_innerfuel = (n_iFA * n_pins_FA + n_iCSD * n_pins_CSD) * FA_height * np.pi * fuel_outer_d
volume_outerfuel = (n_oFA * n_pins_FA + n_oCSD * n_pins_CSD) * FA_height * np.pi * fuel_outer_d
volume_crods = (n_iCSD + n_oCSD) * n_crods_CSD * crod_insertion_length * np.pi * clad_outer_d

inner_fuel.volume = volume_innerfuel
outer_fuel.volume = volume_outerfuel
boron_carbide.volume = volume_crods

# Export materials and geometry
materials_file = openmc.Materials([inner_fuel, outer_fuel, sodium, clad_mat, EM10, follower, boron_carbide])
materials_file.export_to_xml()
geometry.export_to_xml()

##################################################
################### SETTINGS #####################
##################################################

# Creating initial uniform spatial source distribution over fissionable zones
x1 = core_r
y1 = x1
z1 = FA_height / 2

bounds = [-x1, -y1, -z1, x1, y1, z1]
uniform_dist = openmc.stats.Box(bounds[:3], bounds[3:], only_fissionable=True)

settings = openmc.Settings()
settings.batches = 20 #100
settings.inactive = 5  #10
settings.particles = 5000  #10000
settings.source = openmc.Source(space=uniform_dist)
settings.export_to_xml()

##################################################
################### TALLIES ######################
##################################################

# Create mesh for tallying neutron flux
tallies_file = openmc.Tallies()

# Create mesh which will be used for tally
mesh = openmc.RegularMesh()
mesh.dimension = [1000, 1000]
mesh.lower_left = [-core_r, -core_r]
mesh.upper_right = [core_r, core_r]

mesh_filter = openmc.MeshFilter(mesh)

# Neutron flux tally
tally_nf = openmc.Tally(name="Neutron flux")
tally_nf.filters = [mesh_filter]
tally_nf.scores = ['flux']
tallies_file.append(tally_nf)

# Prompt neutron tally
tally_pn = openmc.Tally(name="prompt n")
tally_pn.filters = [mesh_filter]
tally_pn.scores = ['prompt-nu-fission']
tallies_file.append(tally_pn)

# Export tallies
tallies_file.export_to_xml()
# openmc.run()
##################################################
################### DEPLETION ####################
##################################################

# # Define the depletion model
# themodel = openmc.model.Model()
# themodel.geometry = geometry
# themodel.settings = settings
# themodel.materials = materials_file 

# # ENDF/B-VII.1 Chain (Fast Spectrum)
# path = 'chain_endfb71_sfr.xml'
# chain = openmc.deplete.Chain.from_xml(path)
# operator = openmc.deplete.CoupledOperator(themodel, path)

# # Reactor power (3600 MWth for ESFR)
# power = 3600e6  # W 

# # Define time steps (1 hour per step)
# time_steps = [1 * 60 * 60]  # 1 hour in seconds

# # Set up the integrator for depletion simulation
# integrator = openmc.deplete.PredictorIntegrator(operator, time_steps, power)

# # Run the depletion integration
# if __name__ == '__main__':
#     integrator.integrate()
# import openmc
# import openmc.deplete

# Define the depletion model
themodel = openmc.model.Model()
themodel.geometry = geometry
themodel.settings = settings
themodel.materials = materials_file

# Load depletion chain file
chain_file = 'chain_endfb71_sfr.xml'
chain = openmc.deplete.Chain.from_xml(chain_file)
operator = openmc.deplete.CoupledOperator(themodel, chain_file)

# Reactor power: 3600 MWth for ESFR
power = 3600e6  # in watts

# Time steps: 12 months, 1 per month (~30 days each)
seconds_per_month = 30 * 24 * 60 * 60  # 30 days in seconds
time_steps = [seconds_per_month] * 12  # 12 monthly steps

# Set up the integrator for depletion simulation
integrator = openmc.deplete.PredictorIntegrator(operator, time_steps, power)

# Run the depletion simulation
if __name__ == '__main__':
    integrator.integrate()
