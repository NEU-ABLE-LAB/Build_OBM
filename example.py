
# Import packages
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import os
# sys.path.append(os.path.dirname(__file__)) # Does not work with jupyter notebooks
from src.model import OccupantModel

# Read a local files
df = pd.read_hdf('input_data/sample_data1_stp_processed.h5')
TM_occupancy = pd.read_csv('input_data/transition_matrix.csv')
TM_habitual = pd.read_csv('input_data/TM_habitual.csv')
model_regressor = pickle.load(open('input_data/model_regressor.pkl','rb'))
model_classification = pickle.load(open('input_data/model_classification.pkl','rb'))

## Initiate the occupant model
sim_sampling_frequency = 5 # minutes -> cannot exceed this interval as the TM's are not available for a lower frequency
# TODO: To add raise value error if the value is higher thatn 5 minutes
# Initiate OccupantModel
Occup_model = OccupantModel(units='F', N_homes= 1, N_occupants_in_home=1,
                            sampling_frequency=sim_sampling_frequency,
                            TM_occupancy = TM_occupancy, TM_habitual = TM_habitual,
                            model_class = model_classification,
                            model_regres=model_regressor )

## Simulate the model for a day
t = []
T_stp_heat = []
T_stp_cool = []
# Simulate the occupant model for specific timesteps
for timeStepN in range(0,int((1440)/sim_sampling_frequency)):
    t.append(timeStepN)  # For plotting

    Occup_model.step(ip_data_env= {'T_in':df.loc[timeStepN,'T_ctrl'],
                            'T_stp_cool':df.loc[timeStepN,'T_stp_cool'],
                            'T_stp_heat':df.loc[timeStepN,'T_stp_heat'],
                            'hum':df.loc[timeStepN,'hum'],
                            'T_out':df.loc[timeStepN,'T_out'],
                            'mo':None,
                            'equip_run_heat':df.loc[timeStepN,'equip_run_heat'],
                            'equip_run_cool':df.loc[timeStepN,'equip_run_cool']
                            },T_var_names=['T_in','T_stp_cool','T_stp_heat','T_out'])
    for agents in Occup_model.schedule.agents:
        T_stp_heat.append(agents.output['T_stp_heat'])
        T_stp_cool.append(agents.output['T_stp_cool'])
sns.set()

## Visualize the overrides
fig, axes = plt.subplots(1)
sns.lineplot(x=t,y=T_stp_heat,color='orange',ax=axes)
sns.lineplot(x=t,y=T_stp_cool,color='blue',ax=axes)
sns.lineplot(x=t,y=df.loc[0:287,'T_ctrl'],color='green',ax=axes)

axes.set_xlabel('Time steps')
axes.set_ylabel('Setpoint temperature [°F]')
axes.legend(labels=['$Stp_{heat}$', '$Stp_{cool}$', '$T_{in}$'])
plt.show()
