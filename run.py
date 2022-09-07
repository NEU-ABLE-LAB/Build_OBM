# Import packages
from model import OccupantModel
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import seaborn as sns

# Read a local files
df = pd.read_hdf('sample_data1_stp_processed.h5')
TM_occupancy = pd.read_csv('data/transition_matrix.csv')
TM_habitual = pd.read_csv('TM_habitual.csv')
model_regressor = pickle.load(open('model_regressor.pkl','rb'))
model_classification = pickle.load(open('model_classification.pkl','rb'))

t = []
T_stp_heat = []
T_stp_cool = []

sim_sampling_frequency = 5 # minutes -> cannot exceed this interval as the TM's are not available for a lower frequency
# TODO: To add raise value error if the value is higher thatn 5 minutes
# Initiate OccupantModel
Occup_model = OccupantModel(N_homes= 1, N_occupants_in_home=1,
                            sampling_frequency=sim_sampling_frequency,
                            TM_occupancy = TM_occupancy, TM_habitual = TM_habitual,
                            model_class = model_classification,
                            model_regres=model_regressor )

# Simulate the occupant model for specific timesteps
for timeStepN in range(0,int((1440)/sim_sampling_frequency)):
    t.append(timeStepN)  # For plotting

    Occup_model.step(ip_data_env= {'T_in':df.loc[timeStepN,'T_ctrl'],
                            'T_stp_cool':df.loc[timeStepN,'T_stp_cool'],
                            'T_stp_heat':df.loc[timeStepN,'T_stp_heat'],
                            'hum':df.loc[timeStepN,'hum'],
                            'T_out':df.loc[timeStepN,'T_out'],
                            'mo':df.loc[timeStepN,'mo'],
                            'equip_run_heat':df.loc[timeStepN,'equip_run_heat'],
                            'equip_run_cool':df.loc[timeStepN,'equip_run_cool']
                            })
    for agents in Occup_model.schedule.agents:
        T_stp_heat.append(agents.output['T_stp_heat'])
        T_stp_cool.append(agents.output['T_stp_cool'])

# plt.figure()
# sns.lineplot(x=t,y=T_stp_heat)
# sns.lineplot(x=t,y=T_stp_cool)
# plt.show()
