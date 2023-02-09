""" model.py -> Contains basic framework to simulate an occupant agent for a given set of environment inputs """

# Import packages
import mesa
import tools as om_tools

# Occupant agent class
class Occupant(mesa.Agent):
    """ An occupant agent: Contains information specific to an occupant """
    def __init__(self, unique_id: int, model, home_ID, TM_occupancy , TM_habitual, model_class, model_regres, comfort_temperature, discomfort_theory_name='czt',threshold=4) -> None:
        super().__init__(unique_id, model)
        # Occupant's residence
        self.home_ID = home_ID
        # Place holder variable to contain environment info for each timestep
        self.current_env_features = None 
        # Flag to show if the change in setpoint was implemented by the occupant
        self.recent_stp_change = False
        # Occupancy Model - Transition matrix to simulate occupant's presence
        self.occupancy_tp_matrix = TM_occupancy
        # Occupancy Model - Place holder variable to contain simulated occupancy for a simulation's day
        self.occupancy = []
        # # Comfort model - tracking setpoints
        # self.setpoints = {'current': {'heat':None, 'cool': None},\
        #      'previous':{'heat':None, 'cool': None}}
        # Track comfort temperature
        
        self.T_CT = comfort_temperature
        self.follow_theory = discomfort_theory_name.upper()
        
        self.cz_threshold = 4 # degree F
        self.tf_threshold = 50 # degree F minutes
        
        if self.follow_theory == 'CZT':
            self.cz_threshold = threshold # degree F
        elif self.follow_theory == 'TFT':
            self.tf_threshold = threshold # degree F minutes

        # Initialize thermal frustration tracker        
        self.thermal_frustration =[0]
        
        # Time to override value container
        self.TTO = None

        # Habitual model - Transition matrix 
        self.habitual_tp_matrix = TM_habitual
        self.habitual_schedule = []
        self.discomfort_class_model = model_class
        self.discomfort_regres_model = model_regres

        # Simulation output container
        self.output = {'Motion':None, 'T_stp_cool':None, 'T_stp_heat':None, 'Thermal Frustration': None, 'Comfort delta': None, 'Habitual override':False, 'Discomfort override':False}
        print(f"Occupant created,\nID: {unique_id}\nDiscomfort theory: {self.follow_theory}")

    def step(self) -> None:
        # Initialize the output dictionary to avoid errors
        self.output['Habitual override'] = False
        self.output['Discomfort override'] = False

        T_stp_cool, T_stp_heat = (self.current_env_features['T_stp_cool'], self.current_env_features['T_stp_heat'])

        """ 
        +-------------------+
        | Model predictions |
        +-------------------+
        """

        # Synthesize occupancy data
        if (self.model.current_hour_of_the_day == 0) & (self.model.current_min_of_the_day == 0):
            # Occupancy model: If day is new, simulate occupancy for the day
            self.occupancy.extend(om_tools.Markov_occupancy_model(self.occupancy_tp_matrix, sampling_time = self.model.sampling_frequency))
        
        # Routine based habitual Model:
        if (self.model.current_hour_of_the_day == 0) & (self.model.current_min_of_the_day == 0):
            # Occupancy model: If day is new, simulate occupancy for the day
            self.habitual_schedule.extend(om_tools.Markov_habitual_model(self.habitual_tp_matrix, sampling_time = self.model.sampling_frequency))

        # Discomfort Model:
        if self.TTO is None:
            # Prepare input data for ML
            self.current_env_features['mo'] = self.occupancy[self.model.timestep_day]

            if self.follow_theory == 'CZT':
                discomfort_override = om_tools.comfort_zone_theory(self.current_env_features['T_in'] - self.T_CT, cz_threshold = self.cz_threshold)

            elif self.follow_theory == 'TFT':
                discomfort_override = om_tools.frustration_theory(del_tin_tct=self.current_env_features['T_in'] - self.T_CT, alpha=1, beta=1, thermal_frustration=self.thermal_frustration, tf_threshold=self.tf_threshold)

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
        # If routine based habitual model predicts override and the occupant is present in the home:
        #  then decide the setpoint change
        if self.habitual_schedule[self.model.timestep_day] and self.occupancy[self.model.timestep_day]:
        
            T_stp_cool, T_stp_heat = om_tools.decide_heat_cool_stp(self.T_CT, self.current_env_features['T_in'],\
                 self.current_env_features['T_stp_heat'], self.current_env_features['T_stp_cool'])
            self.output['Habitual override'] = True

        elif discomfort_override and self.occupancy[self.model.timestep_day]:
            
            T_stp_cool, T_stp_heat = om_tools.decide_heat_cool_stp(self.T_CT, self.current_env_features['T_in'],\
                 self.current_env_features['T_stp_heat'], self.current_env_features['T_stp_cool'])
            self.output['Discomfort override'] = True

        # if self.TTO == 0 and self.occupancy[self.model.timestep_day]:
        #     T_stp_cool, T_stp_heat = om_tools.decide_heat_cool_stp(self.occupant.T_CT, self.current_env_features['T_in'],\
        #          self.current_env_features['T_stp_heat'], self.current_env_features['T_stp_cool'])
        #     self.TTO = None
        
        # if self.occupancy[self.model.timestep_day] and is_override:
        #     T_stp_cool, T_stp_heat = om_tools.decide_heat_cool_stp(self.T_CT, self.current_env_features['T_in'],\
        #              self.current_env_features['T_stp_heat'], self.current_env_features['T_stp_cool'])

        if self.model.units == 'F': self.output['T_stp_cool'], self.output['T_stp_heat'] = T_stp_cool, T_stp_heat
        else: self.output['T_stp_cool'], self.output['T_stp_heat'] = om_tools.F_to_C(T_stp_cool), om_tools.F_to_C(T_stp_heat)
        
        self.output['Motion'] = self.occupancy[self.model.timestep_day]
        self.output['Thermal Frustration'] = self.thermal_frustration[-1]
        self.output['Comfort Delta'] = self.current_env_features['T_in'] - self.T_CT
        
        print(f"Occupant idN: {self.unique_id} simulated")

class OccupantModel(mesa.Model):
    """ Occupant model: Contains model simulation information required """
    def __init__(self, units, N_homes,N_occupants_in_home, sampling_frequency, TM_occupancy, TM_habitual, model_class, model_regres, comfort_temperature, discomfort_theory_name, threshold) -> None:
        super().__init__()
        # Temperature units
        self.units = units.upper()
        # Number of occupants to be simulated in a home
        self.N_occupants_in_home = N_occupants_in_home
        # Number of homes to be simulated
        self.N_homes = N_homes
        # Type of schedule to be used to trigger occupants to react
        self.schedule = mesa.time.SimultaneousActivation(self)
        # The data/simulated needs to be simulated at the following frequency
        self.sampling_frequency = sampling_frequency
        # Simulation's timestep equivalent hour of the day
        self.current_hour_of_the_day = 0
        # Simulation's timestep equivalent minute of the day
        self.current_min_of_the_day = 0
        # Simulation's timestep equivalent day of the week
        self.current_day_of_the_week = 0
        # Simulation's equivalent of timestep of the day (for 5-min sampling frequency, max value of this var is 288)
        self.timestep_day = 0

        # Create homes
        for home_ID in range(0, N_homes):
            for occup_ID in range(0,self.N_occupants_in_home):
                
                # Create occupant
                occup = Occupant(unique_id=home_ID + occup_ID, model=self, home_ID=home_ID, \
                    TM_occupancy = TM_occupancy, TM_habitual = TM_habitual, \
                    model_class = model_class, model_regres=model_regres,\
                    comfort_temperature=comfort_temperature, discomfort_theory_name=discomfort_theory_name,threshold=threshold)
                # Add occupant to the scheduler
                self.schedule.add(occup)

    def step(self, ip_data_env,T_var_names) -> None:
        print(f"Time step: {self.schedule.steps}")

        # Send simulated indoor env data to the occupant agent
        for agent in self.schedule.agents:
            if self.units == 'F':
                agent.current_env_features = ip_data_env
            else:
                for var in T_var_names:
                    ip_data_env[var] = om_tools.C_to_F(ip_data_env[var])

                agent.current_env_features = ip_data_env

        self.schedule.step()
        
        # Update simulation specific time parameters
        om_tools.update_simulation_timestep(self)