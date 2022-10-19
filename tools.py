import numpy as np
# import matplotlib.pyplot as plt
# import seaborn as sns


def Markov_occupancy_model(tp_matrix, sampling_time):
    """ Create a 1st order markov chain model that synthesizes occupancy schedule for the entire day
    Created using transition matrices discussed in the paper: https://doi.org/10.1016/j.enbuild.2008.02.006
    """
    # Intitating output variable
    occupancy = []

    # Synthesize data for the day, 10-minutes sampling time used for transition matrices. 
    # Therefore, the data is synthesized for 144 minutes numbers and later sampled based on input parameter "sampling_time"
    for timestep in range(0, 144):
        
        # Set state based on current timestep of the day
        if timestep == 0:
            # Start state is randomly selected
            start_state = np.random.choice([False, True])
            current_state = start_state
        else:
            current_state = occupancy[timestep-1][0]
        
        # Get transition state for the period number
        probs = tp_matrix[(tp_matrix['Ten minute period number'] == timestep+1) & (
                tp_matrix['Current state'] == current_state)][['Unoccup_prob','Occupied_prob']].values[0]

        # Probability should add up to 1.
        if probs[0] + probs[1] != 1:
            # If the probabilities were rounded up, remove the thousandnth decimal.
            probs[0] = probs[0] - 0.001
        
        # Estimate the next state
        next_state = np.random.choice([False, True], p = probs)

        # Add the next state based on the sampling time
        # occupancy.extend([next_state]*int(10/sampling_time))
        occupancy.append([next_state]*int(10/sampling_time))
    sampled_occupancy = []
    sampled_occupancy = [y for x in occupancy for y in x]
    # plt.figure()
    # sns.lineplot(x=range(0,len(sampled_occupancy)),y=sampled_occupancy)
    # plt.show()
    return sampled_occupancy


def Markov_habitual_model(TM,sampling_time):
    """ Define a schedule for routine based habitual overrides using first order markov chain  """
    # Intitating output variable
    override_schedule = []

    # 5-minutes sampling time used for transition matrices. 
    # Therefore, the data is synthesized for 288 minutes numbers and is later sampled based on input parameter "sampling_time"
    for timestep in range(0, 287):
        
        # Set state based on current timestep of the day
        if timestep == 0:
            # Start state is randomly selected
            start_state = np.random.choice([False, True])
            current_state = start_state
        else:
            current_state = override_schedule[timestep-1][0]
        
        # Get transition state for the period number
        probs = TM.loc[(TM['time'] == timestep + 1) & (TM['cur_state'] == current_state), 'p_2_0':'p_2_1'].values[0]

        # Probability should add up to 1 (Rounding off leads to thousandth of difference from 1)
        if probs[0] + probs[1] != 1:
            dif = abs(1 - probs[0] - probs[1])
            probs[0] = probs[0] + dif
        
        # Estimate the next state
        next_state = np.random.choice([False,True], p = probs)

        # Add the next state based on the sampling time
        override_schedule.append([next_state]*int(5/sampling_time))
        
    sampled_override_schedule = []
    sampled_override_schedule = [y for x in override_schedule for y in x]
    return sampled_override_schedule

def decide_heat_cool_stp(T_CT, T_in, T_stp_heat, T_stp_cool):
    """ Decide the change in setpoint based on indoor temperature difference from comfort temperature """
    print('Occupant decides to override.')
    print(f"Current heating setpoint: {T_stp_heat}")
    print(f"Current cooling setpoint: {T_stp_cool}")

    if T_in < T_CT:
        # The occupant feels cold, increase heating and cooling stp
        del_T_MSC = abs(T_stp_heat - T_CT)
        T_stp_heat = T_stp_heat + del_T_MSC
        T_stp_cool = T_stp_cool + del_T_MSC
    else:
        # The occupant feels hot, decrease heating and cooling stp
        del_T_MSC = abs(T_stp_cool - T_CT)
        T_stp_heat = T_stp_heat - del_T_MSC
        T_stp_cool = T_stp_cool - del_T_MSC
    
    print(f"New heating setpoint: {T_stp_heat}")
    print(f"New cooling setpoint: {T_stp_cool}")
    return T_stp_cool, T_stp_heat

def update_simulation_timestep(model):
    if model.timestep_day == 1440/model.sampling_frequency:
        model.timestep_day = 0
    else:
        model.timestep_day += 1
    if model.current_min_of_the_day == 60 - model.sampling_frequency:
        model.current_hour_of_the_day += 1
    if model.current_min_of_the_day != 60 - model.sampling_frequency:
        model.current_min_of_the_day += model.sampling_frequency
    else:
        model.current_min_of_the_day = 0
    if model.current_hour_of_the_day == 24:
        model.current_hour_of_the_day = 0
        if model.current_day_of_the_week == 6:
            model.current_day_of_the_week = 0
        else:
            model.current_day_of_the_week += 1 

def convert_F_to_C(ip_data_env, T_var_names):
    for var in T_var_names:
        ip_data_env[var] = (ip_data_env[var] - 32) * 5/9
    return ip_data_env