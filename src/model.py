""" model.py -> Contains basic framework to simulate an occupant agent for a given set of environment inputs """

# Import packages
import mesa
import tools as om_tools

# Occupant agent class
class Occupant(mesa.Agent):
    """ An occupant agent: Contains information specific to an occupant """
    def __init__(self, unique_id: int, model, home_ID,units, init_data, models,
                comfort_temperature, discomfort_theory_name='czt', threshold={'UL':4,'LL':-4},
                TFT_alpha=1, TFT_beta=1, start_datetime=om_tools.datetime.datetime(1996,3,30,0,0),
                tstat_db=0.0) -> None:
        
        super().__init__(unique_id, model)
        self.home_ID = home_ID # Occupant's residence
        self.units = units # Temperature units followed by the occupant
        self.current_env_features = None # Place holder variable to contain environment info for each timestep
        self.recent_stp_change = False # Flag to show if the change in setpoint was implemented by the occupant
        self.init_data = init_data # Initial data dictionary containing TM's and PDFs/PMFs
        self.occupancy = None # Occupancy Model - Place holder variable to contain simulated occupancy for a simulation's day
        self.routine_msc_schedule = None # Routine Model - Place holder variable to contain simulated routine for a simulation's day
        if self.units == 'C':
            self.T_CT = om_tools.C_to_F(comfort_temperature) # Track comfort temperature
        else:
            self.T_CT = comfort_temperature
        self.override_theory = discomfort_theory_name.upper() # Override theory name
        self.last_override_datetime = start_datetime # Time since the last override
        self.tstat_db = tstat_db

        # Discomfort model - Initialize parameters
        if self.override_theory == 'TFT':
            self.TFT_alpha = TFT_alpha
            self.TFT_beta = TFT_beta
            self.tf_threshold = threshold # degree F minutes
            self.thermal_frustration =[0] # Initialize thermal frustration tracker        
        elif self.override_theory == 'CZT':
            self.cz_threshold = threshold # degree F

        self.discomfort_class_model = models['model_classification']
        self.discomfort_regres_model = models['model_regressor']

        # Simulation output container
        self.output = {'Motion':None, 'T_stp_cool':None, 'T_stp_heat':None, 'Thermal Frustration': None, 'Comfort Delta': None, 'Habitual override':False, 'Discomfort override':False}
        print(f"Occupant created,\nID: {unique_id}\nDiscomfort theory: {self.override_theory}")

    def step(self) -> None:
        print(f"Occupant idN: {self.unique_id} simulation started")
        season = om_tools.get_season(self.current_env_features['DateTime'])
        if season == 'heat' or season == 'cool':
            # Initialize the output dictionary to avoid errors
            self.output['Habitual override'] = False
            self.output['Discomfort override'] = False

            # Send simulated indoor env data to the occupant agent
            if self.units == 'C':
                vars_2_convert = [key for key in self.current_env_features.keys() if 'T_' in key]
                for var in vars_2_convert:
                        self.current_env_features[var] = om_tools.C_to_F(self.current_env_features[var])
            """ 
            +-------------------+
            | Model predictions |
            +-------------------+
            """
            # Generate data for the day at midnight
            if (self.current_env_features['DateTime'].hour == 0) & (self.current_env_features['DateTime'].minute == 0):
                # Generate occupancy data at midnight for the next day
                self.occupancy = om_tools.Markov_occupancy_model(
                                                                init_data= self.init_data,
                                                                sampling_time = self.model.sampling_frequency,
                                                                current_datetime=self.current_env_features['DateTime']
                                                                )

                # Generate habitual override data at midnight for the next day
                self.routine_msc_schedule = om_tools.realize_routine_msc(
                                                                        init_data=self.init_data,
                                                                        occupancy_schedule= self.occupancy,
                                                                        current_datetime=self.current_env_features['DateTime']
                                                                        )

            # Get current heating and cooling setpoint
            T_stp_cool, T_stp_heat = (self.current_env_features['T_stp_cool'], self.current_env_features['T_stp_heat'])
            
            # The occupant only feels discomfort if they are present in the home
            if self.occupancy.loc[self.occupancy.datetime.values == self.current_env_features['DateTime'],'occupancy'].values[0]:
            
                # Discomfort Model:
                # Prepare input data for ML
                self.current_env_features['mo'] = self.occupancy.loc[
                                                                    self.occupancy.datetime == self.current_env_features['DateTime'],'occupancy'
                                                                    ].values[0]

                if self.override_theory == 'CZT':
                    discomfort_override = om_tools.comfort_zone_theory(
                                                                        del_tin_tct = self.current_env_features['T_in'] - self.T_CT,
                                                                        cz_threshold = self.cz_threshold
                                                                        )

                elif self.override_theory == 'TFT':
                    discomfort_override = om_tools.frustration_theory(
                                                                        del_tin_tct=self.current_env_features['T_in'] - self.T_CT,
                                                                        alpha=self.TFT_alpha, beta=self.TFT_beta,
                                                                        thermal_frustration=self.thermal_frustration, 
                                                                        tf_threshold=self.tf_threshold
                                                                        )

                # # Decrease the timer per timestep if a TTO value exists
                # if self.TTO == 0:
                #     raise ValueError('Check TTO')
                # if self.TTO:
                #     self.TTO =- 1
                
                # # Classify override using the random forest classification model
                # is_override = self.discomfort_class_model.predict([list(self.current_env_features.values())])[0]
                
                # if is_override:
                #     # Estimate time to override for the classified override using the random forest regressor model
                #     self.TTO = int(om_tools.np.round(self.discomfort_regres_model.predict([list(self.current_env_features.values())])))

                """ 
                +---------------------------+
                | Override decision process |
                +---------------------------+
                """
                            
                # If routine based habitual model predicts override and the occupant is present in the home: then decide the setpoint change
                if self.current_env_features['DateTime'] in self.routine_msc_schedule.datetime.values:

                    DOMSC_cool = self.routine_msc_schedule.loc[
                                                                self.routine_msc_schedule.datetime == self.current_env_features['DateTime'],
                                                                ['delT_cool','delT_heat']
                                                                ].values[0][0]
                    DOMSC_heat = self.routine_msc_schedule.loc[
                                                                self.routine_msc_schedule.datetime == self.current_env_features['DateTime'],
                                                                ['delT_cool','delT_heat']
                                                                ].values[0][1]
                
                    T_stp_cool, T_stp_heat = om_tools.decide_heat_cool_stp(
                                                                            DOMSC_cool,DOMSC_heat,\
                                                                            self.current_env_features['T_stp_heat'],
                                                                            self.current_env_features['T_stp_cool'],
                                                                            current_datetime= self.current_env_features['DateTime'],
                                                                            tstat_db = self.tstat_db,
                                                                            temp_units=self.units                                                                                                                                                    
                                                                            )
                    self.last_override_datetime =  self.current_env_features['DateTime'] # Update the last override time
                    self.output['Habitual override'] = True
                    print('Occupant decides to override: Routine override')

                elif discomfort_override:
                    # Decide the setpoint change
                    if self.T_CT < self.current_env_features['T_in']:
                        # Occupant feels hot, decrease both the setpoints
                        del_T_MSC = self.T_CT - self.current_env_features['T_in']
                        DOMSC_cool = del_T_MSC
                        DOMSC_heat = del_T_MSC
                    else:
                        # Occupant feels cold, increase both the setpoints
                        del_T_MSC = self.T_CT - self.current_env_features['T_in']
                        DOMSC_cool = del_T_MSC
                        DOMSC_heat = del_T_MSC
                    if (self.current_env_features['DateTime'] - self.last_override_datetime).seconds > 300:
                        T_stp_cool, T_stp_heat = om_tools.decide_heat_cool_stp(
                                                                                DOMSC_cool,DOMSC_heat,\
                                                                                self.current_env_features['T_stp_heat'],
                                                                                self.current_env_features['T_stp_cool'],
                                                                                current_datetime= self.current_env_features['DateTime'],
                                                                                tstat_db = self.tstat_db,
                                                                                temp_units=self.units                                                                                                                                                    
                                                                            )
                        self.last_override_datetime =  self.current_env_features['DateTime'] # Update the last override time
                        self.output['Discomfort override'] = True
                        print('Occupant decides to override: Discomfort override')

                    # if self.TTO == 0 and self.occupancy[self.model.timestep_day]:
                    #     T_stp_cool, T_stp_heat = om_tools.decide_heat_cool_stp(self.occupant.T_CT, self.current_env_features['T_in'],\
                    #          self.current_env_features['T_stp_heat'], self.current_env_features['T_stp_cool'])
                    #     self.TTO = None
                    
                    # if self.occupancy[self.model.timestep_day] and is_override:
                    #     T_stp_cool, T_stp_heat = om_tools.decide_heat_cool_stp(self.T_CT, self.current_env_features['T_in'],\
                    #              self.current_env_features['T_stp_heat'], self.current_env_features['T_stp_cool'])
            else:
                self.thermal_frustration =[0] # Reset thermal frustration if the occupant is not present in the home

            if self.units == 'C':
                T_stp_cool, T_stp_heat = om_tools.check_setpoints(om_tools.F_to_C(T_stp_cool), om_tools.F_to_C(T_stp_heat),
                                                          self.current_env_features['DateTime'],tstat_db = self.tstat_db,temp_units=self.units)
                self.output['T_stp_cool'] = T_stp_cool
                self.output['T_stp_heat'] = T_stp_heat
            else: 
                T_stp_cool, T_stp_heat = om_tools.check_setpoints(om_tools.F_to_C(T_stp_cool), om_tools.F_to_C(T_stp_heat),
                                                          self.current_env_features['DateTime'],tstat_db = self.tstat_db,temp_units=self.units)
                self.output['T_stp_cool'] = T_stp_cool
                self.output['T_stp_heat'] = T_stp_heat
            
            self.output['Motion'] = self.occupancy.loc[
                                                        self.occupancy.datetime == self.current_env_features['DateTime'],
                                                        'occupancy'
                                                        ].values[0]
            self.output['Thermal Frustration'] = self.thermal_frustration[-1]
            self.output['Comfort Delta'] = self.current_env_features['T_in'] - self.T_CT
        else:
            self.output = {'Motion':False,
                           'T_stp_cool':self.current_env_features['T_stp_cool'],
                            'T_stp_heat':self.current_env_features['T_stp_heat'],
                            'Thermal Frustration': 0,
                            'Comfort Delta': None,
                            'Habitual override':False,
                            'Discomfort override':False}
            pass
        print(f"Occupant idN: {self.unique_id} simulation completed")

class OccupantModel(mesa.Model):
    '''
    Occupant Model:

    Using Agent Based Modeling (ABM) framework from Mesa library, this model simulates occupant(s) in home(s).

    To simulate an occupant in a home, the following steps are followed:
    1. Initialize the model: TODO
    2. Run the model: TODO
    3. Return occupant data: TODO

    Uses the Occupant class to simulate occupants in a home
    '''
    def __init__(self, units, N_homes,N_occupants_in_home, sampling_frequency,
                 models, init_data,  comfort_temperature, discomfort_theory_name,
                 threshold, TFT_alpha, TFT_beta, start_datetime, tstat_db) -> None:
        '''
        Intialize the model for occupant(s) in home(s)
        '''
        super().__init__() # Initialize the mesa model

        # Temperature units
        self.units = units.upper()
        # Number of occupants to be simulated in a home
        self.N_occupants_in_home = N_occupants_in_home
        # Number of homes to be simulated
        self.N_homes = N_homes
        # Type of schedule to be used to trigger occupants to react
        self.schedule = mesa.time.BaseScheduler(self)
        # The data/simulated needs to be simulated at the following frequency
        self.sampling_frequency = sampling_frequency

        # Simulation's equivalent of timestep of the day (for 5-min sampling frequency, max value of this var is 288)
        self.timestep_day = 0

        # Create homes
        for home_ID in range(0, N_homes):
            for occup_ID in range(0,self.N_occupants_in_home):
                
                # Create occupant
                occup = Occupant(unique_id=home_ID + occup_ID, model=self, home_ID=home_ID, units=self.units,\
                                models=models, init_data=init_data, comfort_temperature=comfort_temperature,\
                                discomfort_theory_name=discomfort_theory_name, threshold=threshold,\
                                TFT_alpha=TFT_alpha,TFT_beta=TFT_beta, start_datetime=start_datetime, tstat_db = tstat_db)

                # Add occupant to the scheduler
                self.schedule.add(occup)

    def step(self, ip_data_env) -> None:
        print(f"OCcupant simulation started for timestep: {self.schedule.steps}")
        for agent in self.schedule.agents:
            agent.current_env_features = ip_data_env
        
        self.schedule.step()
        
        # Update simulation specific time parameters
        om_tools.update_simulation_timestep(self)
        print(f"Occupant simulation finished for timestep: {self.schedule.steps}")
