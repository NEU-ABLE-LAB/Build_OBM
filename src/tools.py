import numpy as np
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import seaborn as sns
import pathlib
import datetime
import warnings
import math


def comfort_zone_theory(del_tin_tct, cz_threshold = {'UL':4,'LL':-4}):
    """ Comfort zone theory for override prediction
    """
    override = False
    if del_tin_tct > cz_threshold['UL']:
        override = True
    elif del_tin_tct < cz_threshold['LL']:
        override = True
    else:
        override = False
    return override

def check_setpoints(T_stp_cool, T_stp_heat, current_datetime,tstat_db,temp_units):
    """
    Cooling setpoint should always be greater than the heating setpoint. 
    If not, based on the season, the setpoints are adjusted for energy intensive overrides.
    """ 
    if T_stp_cool - tstat_db < T_stp_heat:
        warnings.warn(f"Cooling setpoint({T_stp_cool}) - db({tstat_db}) is less than the heating setpoint({T_stp_heat})")
        season = get_season(current_datetime)
        if season == 'cool':
            T_stp_heat = math.floor(T_stp_cool - (tstat_db + 0.5))
        elif season == 'heat':
            T_stp_cool = math.ceil(T_stp_heat + (tstat_db + 0.5))
    
    if T_stp_cool < 0 | T_stp_heat < 0:
        warnings.warn(f"Cooling setpoint {T_stp_cool} or heating setpoint {T_stp_heat} is less than 0")
        if temp_units == "F":
            T_stp_cool = 60
            T_stp_heat = 50
        else:
            T_stp_cool = 15
            T_stp_heat = 10

    return T_stp_cool, T_stp_heat

def frustration_theory(del_tin_tct, alpha=1, beta=1, thermal_frustration=[0], tf_threshold={'UL':4,'LL':-4}):
    """ Frustration theory for override prediction
    """
    override = False
    thermal_frustration.append(alpha*thermal_frustration[-1]+beta*del_tin_tct)
    
    if thermal_frustration[-1] >= tf_threshold['UL']:
        override = True
    elif thermal_frustration[-1] <= tf_threshold['LL']:
        override = True
    else:
        override = False
    return override

def Markov_occupancy_model(tp_matrix, sampling_time,current_datetime):
    """ Generate a 1st order markov chain model that synthesizes occupancy schedule for the entire day
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
            start_state = True
            # start_state = np.random.choice([False, True])
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
        occupancy.append([next_state]*int(10/sampling_time))
    sampled_occupancy = []
    sampled_occupancy = [y for x in occupancy for y in x]
    # plt.figure()
    # sns.lineplot(x=range(0,len(sampled_occupancy)),y=sampled_occupancy)
    # plt.show()

    current_datetime_array = pd.to_datetime(np.arange(current_datetime,
                         current_datetime+datetime.timedelta(hours=24),
                         datetime.timedelta(minutes=sampling_time)).astype(datetime.datetime))
    sampled_occupancy = pd.DataFrame({'datetime':current_datetime_array,'occupancy':sampled_occupancy})
    sampled_occupancy.datetime = pd.Series(sampled_occupancy.datetime.dt.to_pydatetime(),dtype='object')

    return sampled_occupancy


def Markov_habitual_model(TM,sampling_time):
    """ Define a schedule for routine based habitual overrides using first order markov chain  """
    # Intitating output variable
    override_schedule = []

    # 5-minutes sampling time used for transition matrices. 
    # Therefore, the data is synthesized for 288 minutes numbers and is later sampled based on input parameter "sampling_time"
    for timestep in range(0, 288):
        
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

# Function to output season for the input date
def get_season(current_datetime):
    """ Get the season based on the current date
    """
    # Get the current date
    current_date = current_datetime.date()
    # Get the current month
    current_month = current_date.month
    
    # Get the current season
    if current_month == 12 or current_month == 1 or current_month == 2:
        season = 'heat'
    elif current_month == 3 or current_month == 4 or current_month == 5:
        season = 'heat2cool'
    elif current_month == 6 or current_month == 7 or current_month == 8:
        season = 'cool'
    elif current_month == 9 or current_month == 10 or current_month == 11:
        season = 'cool2heat'
    return season

# Function to flag weekend for the input date
def is_weekend(current_datetime):
    """ Get the weekday or weekend based on the current date
    """
    # Get the current date
    current_date = current_datetime.date()
    # Get the current weekday
    current_weekday = current_date.weekday()
    
    # Get the current weekday or weekend
    if current_weekday == 5 or current_weekday == 6:
        is_weekend = True
    else:
        is_weekend = False
    return is_weekend

# Determine routine msc schedule
def realize_routine_msc(init_data, occupancy_schedule, current_datetime):
    """ Given the input of Probability density functions, this function computes the next habitual override(s) based on the current season and current weekday/weekend"""
    
    # Initialize output variable
    routine_msc_schedule = pd.DataFrame([], columns=['datetime','delT_cool','delT_heat'])
    true_occupancy_dt = pd.to_datetime(occupancy_schedule.loc[occupancy_schedule['occupancy'] == True,'datetime'].values)
    
    if true_occupancy_dt.size > 10:
        # Get current season
        season = get_season(current_datetime)
        weekend = is_weekend(current_datetime)
        
        # Get the probability density function for the current season and weekday/weekend
        if weekend == True:
            typeofday_label = 'we'
        else:
            typeofday_label = 'wd'
        label = season + '_' + typeofday_label

        # First realize the number of mscs per day i.e. N_mscpd
        N = init_data[label +'_Nmscpd']['N'].values
        probs = init_data[label+'_Nmscpd']['prob'].values
        if np.sum(probs) != 1:
                diff = abs(1 - np.sum(probs))
                probs[0] = probs[0] + diff
        N_mscpd = np.random.choice(N, p = probs)

        if N_mscpd > 2:
            # For now, any larger number of mscs is considered as 2 mscs,
            # TODO: update when PDFs are available for higher number of MSCs
            N_mscpd = 2

        # N_mscpd = 2 # For testing purposes, # TODO: remove this line
        if N_mscpd == 2:
            # Realize the time of first msc i.e. t_msc_1
            t_msc_1 = None
            iterations = 0
            while t_msc_1 not in true_occupancy_dt and true_occupancy_dt[-1] != t_msc_1:
                iterations += 1
                if iterations > 100:
                    warnings.warn('Could not find a valid time for first msc')
                data = init_data[label + '_' + str(N_mscpd) + 'mscpd_tod1']
                tod_1 = data['tod'].values
                prob = data['prob'].values
                if np.sum(prob) != 1:
                    diff = abs(1 - np.sum(prob))
                    prob[0] = prob[0] + diff
                t_msc_1 = datetime.datetime.combine(current_datetime.date(), pd.to_datetime(np.random.choice(tod_1, p = prob), format='%H:%M:%S').time())

            # Realize the type of first msc i.e. type_msc_1
            data = init_data[label + '_' + str(N_mscpd) + 'mscpd_type1']
            types_1 = data['types'].values
            prob = data['prob'].values
            if np.sum(prob) != 1:
                diff = abs(1 - np.sum(prob))
                prob[0] = prob[0] + diff
            type_1 = np.random.choice(types_1, p = prob)

            # Realize the degree of first msc i.e. domsc_1
            data = init_data[label + '_' + str(N_mscpd) + 'mscpd_'+ season + '_DOO1_'+ type_1 +'_type']
            domscs_1 = np.array(data.columns[1:]).astype(int)
            prob = np.array(data.loc[data['tod'] == str(t_msc_1.time())].values[0][1:]).astype(float)
            if np.sum(prob) == 0:
                domsc_1 = np.random.choice(domscs_1)
            elif np.sum(prob) != 1:
                diff = abs(1 - np.sum(prob))
                prob[0] = prob[0] + diff
                domsc_1 = np.random.choice(domscs_1, p = prob)
            else:
                domsc_1 = np.random.choice(domscs_1, p = prob)

            # Realize the time of second msc i.e. t_msc_2 given the time of first msc i.e., t_msc_1
            t_msc_2 = None
            data = init_data[label + '_' + str(N_mscpd) + 'mscpd_tod2_tod1']
            tod_2 = pd.to_datetime([datetime.datetime.combine(current_datetime.date(),pd.to_datetime(item, format='%H:%M:%S').time()) for item in data['tod'].values])
            iterations = 0
            while t_msc_2 not in true_occupancy_dt:
                iterations += 1
                if iterations > 100:
                    warnings.warn('Could not find a valid time for second msc, choosing one from the true occupancy schedule after 1st msc')
                    t_msc_2 = pd.to_datetime(np.random.choice(true_occupancy_dt[true_occupancy_dt> t_msc_1]))
                    break
                prob = np.array(data.loc[data.tod == str(t_msc_1.time())].values[0][1:]).astype(float)
                if np.sum(prob) == 0:
                    t_msc_2 = pd.to_datetime(np.random.choice(tod_2[tod_2 > t_msc_1]))
                elif np.sum(prob) != 1:
                    diff = abs(1 - np.sum(prob))
                    prob[-1] = prob[-1] + diff
                    t_msc_2 = pd.to_datetime(np.random.choice(tod_2,p =prob))
                else:
                    t_msc_2 = pd.to_datetime(np.random.choice(tod_2,p =prob))

            # Realize the type of second msc i.e. type_msc_2 given the type of first msc i.e. type_1
            data = init_data[label + '_' + str(N_mscpd) + 'mscpd_type2_type1_' + type_1]
            types_2 = data['types'].values
            prob = data['prob'].values
            if np.sum(prob) != 1:
                diff = abs(1 - np.sum(prob))
                prob[0] = prob[0] + diff
            type_2 = np.random.choice(types_2, p = prob)
            
            # Realize the degree of second msc i.e. DOO_msc_2 given the type and degree of first msc and type of second msc i.e. type_1, DOMSC_1, type_2
            data = init_data[label + '_' + str(N_mscpd) + 'mscpd_row' + season + '_col' + season + '_DOO2_' + type_1 + '_type1_' + type_2 + '_type2']
            domscs_2 = np.array(data.columns[1:]).astype(int)
            prob = np.array(data.loc[data['doo'] == domsc_1].values[0][1:]).astype(float)
            if np.sum(prob) != 1:
                diff = abs(1 - np.sum(prob))
                prob[0] = prob[0] + diff
            domsc_2 = np.random.choice(domscs_2, p = prob)

            if season == 'cool':
                routine_msc_schedule.datetime = [t_msc_1,t_msc_2]
                routine_msc_schedule.datetime = pd.Series(routine_msc_schedule.datetime.dt.to_pydatetime(),dtype='object')
                routine_msc_schedule.delT_cool = [domsc_1,domsc_2]
                routine_msc_schedule.delT_heat = [0,0]
            elif season == 'heat':
                routine_msc_schedule.datetime = [t_msc_1,t_msc_2]
                routine_msc_schedule.datetime = pd.Series(routine_msc_schedule.datetime.dt.to_pydatetime(),dtype='object')
                routine_msc_schedule.delT_cool = [0,0]
                routine_msc_schedule.delT_heat = [domsc_1,domsc_2]

        elif N_mscpd == 1:
            # Realize the time of first msc i.e. t_msc_1
            t_msc = None
            iterations = 0
            while t_msc not in true_occupancy_dt:
                iterations += 1
                if iterations > 100:
                    warnings.warn('Could not find a valid time for msc')
                data = init_data[label + '_' + str(N_mscpd) + 'mscpd_tod']
                tod = data['tod'].values
                prob = data['prob'].values
                if np.sum(prob) != 1:
                    diff = abs(1 - np.sum(prob))
                    prob[0] = prob[0] + diff
                t_msc = datetime.datetime.combine(current_datetime.date(), pd.to_datetime(np.random.choice(tod, p = prob), format='%H:%M:%S').time())

            # Realize the type of first msc i.e. type_msc_1
            data = init_data[label + '_' + str(N_mscpd) + 'mscpd_type']
            types = data['types'].values
            prob = data['prob'].values
            if np.sum(prob) != 1:
                diff = abs(1 - np.sum(prob))
                prob[0] = prob[0] + diff
            type = np.random.choice(types, p = prob)

            # Realize the degree of first msc i.e. domsc
            data = init_data[label + '_' + str(N_mscpd) + 'mscpd_'+ season + '_DOO_'+ type +'_type']
            domscs = np.round(np.array(data.columns[1:]).astype('float')).astype('int')
            prob = np.array(data.loc[data['tod'] == str(t_msc.time())].values[0][1:]).astype(float)
            if np.sum(prob) != 1:
                diff = abs(1 - np.sum(prob))
                prob[0] = prob[0] + diff
            domsc = np.random.choice(domscs, p = prob)
            
            if season == 'cool':
                routine_msc_schedule.datetime = t_msc
                routine_msc_schedule.datetime = pd.Series(routine_msc_schedule.datetime.dt.to_pydatetime(),dtype='object')
                routine_msc_schedule.delT_cool = domsc
                routine_msc_schedule.delT_heat =0
            elif season == 'heat':
                routine_msc_schedule.datetime = t_msc
                routine_msc_schedule.datetime = pd.Series(routine_msc_schedule.datetime.dt.to_pydatetime(),dtype='object')
                routine_msc_schedule.delT_cool = 0
                routine_msc_schedule.delT_heat = domsc

    return routine_msc_schedule

def Markov_2nd_order_habitual_model(TM,sampling_time,current_datetime):
    """ Generates routine based habitual overrides using second order markov chain for the day based on current season and weekday/weekend"""
    # Intitating output variable
    override_schedule = []

    # Get current season
    season = get_season(current_datetime)
    weekend = is_weekend(current_datetime)

    if season == 'summer' or season == 'fall':
        if weekend == True:
            tm_2_use = TM['cool_we']
        else:
            tm_2_use = TM['cool_wd']
    else:
        if weekend == True:
            tm_2_use = TM['heat_we']
        else:
            tm_2_use = TM['heat_wd']
            
    # 5-minutes sampling time used for transition matrices. 
    # Therefore, the data is synthesized for 288 minutes numbers and is later sampled based on input parameter "sampling_time"
    for timestep in range(0, 288):
        
        # Set state based on current timestep of the day
        if timestep == 0:
            # Start state is randomly selected
            prev_state = np.random.choice([False, True])
            current_state = np.random.choice([False, True])
        elif timestep == 1:
            prev_state = current_state
            current_state = override_schedule[timestep-1][0]
        else:
            prev_state = override_schedule[timestep-2][0]
            current_state = override_schedule[timestep-1][0]
        
        # Get transition state for the period number
        # probs = TM.loc[(TM['time'] == timestep + 1) & (TM['cur_state'] == current_state), 'p_2_0':'p_2_1'].values[0]
        probs = tm_2_use.loc[(tm_2_use['timestep'] == timestep + 1) & 
                             (tm_2_use['prev_state'] == prev_state) & 
                             (tm_2_use['cur_state'] == current_state),
                               'p_2_0':'p_2_1'].values[0]

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

def decide_heat_cool_stp(DOMSC_cool, DOMSC_heat, T_stp_heat, T_stp_cool,current_datetime,tstat_db,temp_units):
    """ Decide the change in setpoint based on indoor temperature difference from comfort temperature """
    print('Occupant decides to override the thermostat setpoint')
    T_stp_cool = T_stp_cool + DOMSC_cool
    T_stp_heat = T_stp_heat + DOMSC_heat 

    T_stp_cool, T_stp_heat = check_setpoints(T_stp_cool, T_stp_heat,current_datetime, tstat_db, temp_units)
    
    return T_stp_cool, T_stp_heat

def update_simulation_timestep(model):
    if model.timestep_day == 1440/model.sampling_frequency:
        model.timestep_day = 0
    else:
        model.timestep_day += 1

def C_to_F(T):
    # Convert temperature from Celsius to Fahrenheit
    return round((T * 9/5) + 32)
def F_to_C(T):
    # Convert temperature from Fahrenheit to Celsius
    return round((T - 32) * 5/9)