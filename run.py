
# Import packages
from model import OccupantModel
import pandas as pd

# Read a local dataframe to simulate the indoor environment conditions
df = pd.read_hdf('sample_data1.h5')

occupant_mdl_smpl_frq = 5  # minutes
in_env_smpl_frq = 5 # minutes


# Initiate OccupantModel
Occup_model = OccupantModel(N_homes= 1, N_occupants_in_home=1, sampling_frequency=occupant_mdl_smpl_frq)

# Simulate the occupant model for specific timesteps
for timeStepN in range(0,int(1440/occupant_mdl_smpl_frq)):
    Occup_model.step(df)
