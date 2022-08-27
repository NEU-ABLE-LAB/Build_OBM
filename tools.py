import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def Markov_occupancy_model(tp_matrix, sampling_time):
    """ Create a 1st order markov chain model that synthesizes occupancy schedule for the entire day
    Created using transition matrices discussed in the paper: https://doi.org/10.1016/j.enbuild.2008.02.006
    """
    # Temp. variable
    occupancy = []

    # Synthesize data for the day, 10-minutes sampling time used for transition matrices. 
    # Therefore, the data is synthesized for 144 minutes numbers and later sampled based on input parameter "sampling_time"
    for timestep in range(0, 144):
        
        # Set state based on current timestep of the day
        if timestep == 0:
            # Start state is randomly selected
            start_state = np.random.choice([1,0])
            current_state = start_state
        else:
            current_state = occupancy[timestep-1]
        
        # Get transition state for the period number
        probs = tp_matrix[(tp_matrix['Ten minute period number'] == timestep+1) & (
                tp_matrix['Current state'] == current_state)][['Unoccup_prob','Occupied_prob']].values[0]

        # Probability should add up to 1.
        if probs[0] + probs[1] != 1:
            # If the probabilities were rounded up, remove the thousandnth decimal.
            probs[0] = probs[0] - 0.001
        
        # Estimate the next state
        next_state = np.random.choice([0,1], p = probs)

        # Add the next state based on the sampling time
        occupancy.extend([next_state]*int(10/sampling_time))
    
    # plt.figure()
    # sns.lineplot(x=range(0,len(occupancy)),y=occupancy)
    # plt.show()
    return occupancy


def Markov_habitual_model(TM,sampling_time):
    override_schedule = []
    # Synthesize data for the day, 10-minutes sampling time used for transition matrices. 
    # Therefore, the data is synthesized for 144 minutes numbers and later sampled based on input parameter "sampling_time"
    for timestep in range(0, 287):
        
        # Set state based on current timestep of the day
        if timestep == 0:
            # Start state is randomly selected
            start_state = np.random.choice([1,0])
            current_state = start_state
        else:
            current_state = override_schedule[timestep-1]
        
        # Get transition state for the period number
        probs = TM.loc[(TM['time'] == timestep+1) & (TM['cur_state'] == current_state), 'p_2_0':'p_2_1'].values[0]

        # Probability should add up to 1.
        if probs[0] + probs[1] != 1:
            dif = abs(1 - probs[0] - probs[1])
            probs[0] = probs[0]+dif
            # raise warning('Total probability does not add up to 1')
        
        # Estimate the next state
        next_state = np.random.choice([0,1], p = probs)

        # Add the next state based on the sampling time
        override_schedule.extend([next_state]*int(5/sampling_time))
    return override_schedule
