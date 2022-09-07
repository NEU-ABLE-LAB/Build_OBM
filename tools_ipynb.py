def extract_TM_DyD(TM, weekday_df, df_read):
    print("here")
    hours_list = list(range(0,24))*12
    hours_list.sort()
    minutes_list = list(range(0,56,5))*24

    for timestep in range(0,288):
        print(f"timestep: {timestep}")
        
        if timestep == 0:
            cur_min = minutes_list[-1]
            cur_hour = hours_list[-1]
            next_min = minutes_list[0]
            next_hour = hours_list[0]
        else:
            cur_min = next_min
            cur_hour = next_hour
            next_min = minutes_list[timestep]
            next_hour = hours_list[timestep]

        idx_curr_non_override = [index for index,value in weekday_df.loc[(weekday_df.DateTime.dt.minute == cur_min) & (weekday_df.DateTime.dt.hour==cur_hour),'mdsp'].items() if value ==False]
        idx_curr_override = [index for index,value in weekday_df.loc[(weekday_df.DateTime.dt.minute == cur_min) & (weekday_df.DateTime.dt.hour==cur_hour),'mdsp'].items() if value == True]

        for idx in idx_curr_non_override:
            if idx == len(df_read):
                continue
            if df_read.loc[idx+1].mdsp == True:
                TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 0), 'p_2_1'] += 1
            else: 
                TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 0), 'p_2_0'] += 1

        for idx in idx_curr_override:
            if idx == len(df_read):
                continue
            if df_read.loc[idx+1].mdsp == True:
                TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 1),'p_2_1'] += 1
            else: 
                TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 1), 'p_2_0'] += 1

        total_override_events = TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 1),'p_2_1'].values + TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 1),'p_2_0'].values
        total_non_override_events = TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 0),'p_2_1'].values + TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 0),'p_2_0'].values
        if total_override_events == 0:
            TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 1),'p_2_0'] = 1
        else:
            TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 1),'p_2_1'] =  TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 1),'p_2_1'].values/total_override_events
            TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 1),'p_2_0'] = TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 1),'p_2_0'].values/total_override_events

        if total_non_override_events == 0:
            TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 0),'p_2_0'] = 1    
        else:
            TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 0),'p_2_1'] = TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 0),'p_2_1'].values/total_non_override_events
            TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 0),'p_2_0'] = TM.loc[(TM['time']== timestep ) & (TM['cur_state'] == 0),'p_2_0'].values/total_non_override_events
    
    return TM