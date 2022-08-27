# Import packages
from model import OccupantModel
import pandas as pd

# Read a local dataframe to simulate the indoor environment conditions
df = pd.read_hdf('sample_data1_stp_processed.h5')

sim_sampling_interval = 5 # minutes -> cannot exceed this interval as the TM's are not available for a lower frequency

# Initiate OccupantModel
Occup_model = OccupantModel(N_homes= 1, N_occupants_in_home=1, sampling_frequency=sim_sampling_interval)

# Simulate the occupant model for specific timesteps
for timeStepN in range(0,int(1440/sim_sampling_interval)):
    Occup_model.step(df)
    for agents in Occup_model.schedule.agents:
        del_T_MSC = agents.del_T_MSC
        if del_T_MSC != 0:
            1+1
