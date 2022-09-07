# Import packages
from model import OccupantModel
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import seaborn as sns

# Read a local dataframe to simulate the indoor environment conditions
df = pd.read_hdf('sample_data1_stp_processed.h5')
df.rename({'T_ctrl':'T_in'}, axis = 1)
model_regressor = pickle.load(open('model_regressor.pkl','rb'))
model_classification = pickle.load(open('model_classification.pkl','rb'))
t = []
T_SP = []

sim_sampling_interval = 5 # minutes -> cannot exceed this interval as the TM's are not available for a lower frequency
# TODO: To add raise value error if the value is higher thatn 5 minutes
# Initiate OccupantModel
Occup_model = OccupantModel(N_homes= 1, N_occupants_in_home=1,
                            sampling_frequency=sim_sampling_interval,
                            model_class = model_classification,
                            model_regres=model_regressor )

# Simulate the occupant model for specific timesteps
for timeStepN in range(0,int(1440/sim_sampling_interval)):
    t.append(timeStepN)
    Occup_model.step(df)
    for agents in Occup_model.schedule.agents:
        if agents.del_T_MSC != 0:
            T_SP.append(agents.agents.del_T_MSC)

# plt.figure()
# sns.lineplot(x=t,y=del_T_MSC)
# plt.show()
1+1