
# Import packages
import src.tools as om_tools
import sys
import os
# sys.path.append(os.path.dirname(__file__)) # Does not work with jupyter notebooks
from src.model import OccupantModel


# Read a local files
df = om_tools.pd.read_hdf('input_data/sample_data1_stp_processed.h5')

# Read the transition matrices and PDFs
init_data_dir = om_tools.pathlib.Path("input_data\csv").resolve()
models_dir = om_tools.pathlib.Path("input_data\models").resolve()
data_files = list(init_data_dir.iterdir())
model_files = list(models_dir.iterdir())
init_data = {}
for file in data_files:
    init_data[file.stem] = om_tools.pd.read_csv(file)
models = {}
for model_file in model_files:
    models[model_file.stem] = om_tools.pickle.load(open(model_file,'rb'))

start_datetime = om_tools.datetime.datetime(2019, 1, 1, 0, 0, 0)
## Initiate the occupant model
sim_sampling_frequency = 5 # minutes -> cannot exceed this interval as the TM's are not available for a lower frequency
# TODO: To add raise value error if the value is higher than 5 minutes
# Initiate OccupantModel
Occup_model = OccupantModel(units='F', N_homes= 1, N_occupants_in_home=1,
                            sampling_frequency=sim_sampling_frequency, models = models,
                            init_data = init_data, comfort_temperature=68,
                             discomfort_theory_name='tft', threshold={'UL': 50, 'LL': -50},TFT_alpha=1,TFT_beta=1,start_datetime=start_datetime)

## Simulate the model for a day
t = []
T_stp_heat = []
T_stp_cool = []
mo = []
del_t = []
tf =[]
current_datetime = start_datetime
total_timesteps = int((1440*20)/sim_sampling_frequency)
# Simulate the occupant model for specific timesteps
for timeStepN in range(0,total_timesteps):
    t.append(timeStepN)  # For plotting
    if timeStepN > 0:
        current_datetime = current_datetime + om_tools.datetime.timedelta(minutes=sim_sampling_frequency)

    Occup_model.step(ip_data_env= {'DateTime':current_datetime, 'T_in':df.loc[timeStepN,'T_ctrl'],
                            'T_stp_cool':df.loc[timeStepN,'T_stp_cool'],
                            'T_stp_heat':df.loc[timeStepN,'T_stp_heat'],
                            'hum':df.loc[timeStepN,'hum'],
                            'T_out':df.loc[timeStepN,'T_out'],
                            'mo':None,
                            'equip_run_heat':df.loc[timeStepN,'equip_run_heat'],
                            'equip_run_cool':df.loc[timeStepN,'equip_run_cool']
                            })
    for agents in Occup_model.schedule.agents:
        T_stp_heat.append(agents.output['T_stp_heat'])
        T_stp_cool.append(agents.output['T_stp_cool'])
        mo.append(agents.output['Motion'])
        del_t.append(agents.output['Comfort delta'])
        tf.append(agents.output['Thermal Frustration'])

om_tools.sns.set()
## Visualize the overrides
fig, axes = om_tools.plt.subplots(3)
om_tools.sns.lineplot(x=t,y=T_stp_heat,color='orange',ax=axes[0])
om_tools.sns.lineplot(x=t,y=T_stp_cool,color='blue',ax=axes[0])
om_tools.sns.lineplot(x=t,y=df.loc[0:total_timesteps-1,'T_ctrl'],color='green',ax=axes[0])
om_tools.sns.lineplot(x=t,y=mo,color='blue',ax=axes[1])
om_tools.sns.lineplot(x=t,y=tf,color='blue',ax=axes[2])

axes[1].set_xlabel('Time steps')
axes[0].set_ylabel('Setpoint temperature [°F]')
axes[0].legend(labels=['$Stp_{heat}$', '$Stp_{cool}$', '$T_{in}$'])
om_tools.plt.show()

print('Finished')