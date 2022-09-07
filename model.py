""" model.py -> Contains basic framework to simulate an occupant agent for a given set of environment inputs """

# Import packages
import mesa
import pandas as pd
from tools import *

# Occupant agent class
class Occupant(mesa.Agent):
    """ An occupant agent: Contains information specific to an occupant """
    def __init__(self, unique_id: int, model, home_ID, model_class, model_regres) -> None:
        super().__init__(unique_id, model)
        # Occupant's residence
        self.home_ID = home_ID
        # Place holder variable to contain environment info for each timestep
        self.current_env_features = None 
        # Flag to show if the change in setpoint was implemented by the occupant
        self.recent_stp_change = False
        # Occupancy Model - Transition matrix to simulate occupant's presence
        self.occupancy_tp_matrix = pd.read_csv('data/transition_matrix.csv')
        # Occupancy Model - Place holder variable to contain simulated occupancy for a simulation's day
        self.occupancy = []
        # Comfort model - tracking setpoints
        self.setpoints = {'current': {'heat':None, 'cool': None},\
             'previous':{'heat':None, 'cool': None}}
        # Track comfort temperature
        self.T_CT = 72.0 # Static value for now
        # Time to override value container
        self.TTO = None

        # Habitual model - Transition matrix 
        self.habitual_tp_matrix = pd.read_csv('TM_habitual.csv')
        self.habitual_schedule = []
        self.del_T_MSC = 0
        self.discomfort_class_model = model_class
        self.discomfort_regres_model = model_regres

        print(f"Occupant created, ID: {unique_id}")

    def step(self) -> None:

        # Synthesize occupancy data
        if self.model.schedule.steps % 24 == 0:
            # Occupancy model: If day is new, simulate occupancy for the day
            self.occupancy.extend(Markov_occupancy_model(self.occupancy_tp_matrix, sampling_time = self.model.sampling_frequency))
        
        # Routine based habitual Model:
        if self.model.schedule.steps % 24 == 0:
            # Occupancy model: If day is new, simulate occupancy for the day
            self.habitual_schedule.extend(Markov_habitual_model(self.habitual_tp_matrix, sampling_time = self.model.sampling_frequency))
        
        # Comfort Model: Predict comfortable temperature
        if self.model.schedule.steps == 0:
            # No prior data exists, assume previous and current data to be same
            self.setpoints['previous']['heat'] = self.current_env_features['T_stp_heat']
            self.setpoints['previous']['cool'] = self.current_env_features['T_stp_cool']
        else:
            # Update data
            self.setpoints['previous']['heat'] = self.setpoints['current']['heat']
            self.setpoints['previous']['cool'] = self.setpoints['current']['cool']

        self.setpoints['current']['heat'] = self.current_env_features['T_stp_heat']
        self.setpoints['current']['cool'] = self.current_env_features['T_stp_cool']
        
        # Define change in setpoint
        T_stp_heat_change = self.setpoints['current']['heat'] - self.setpoints['previous']['heat']
        T_stp_cool_change = self.setpoints['current']['cool'] - self.setpoints['previous']['cool']

        # Define the comfort temperature if:
        #   1. The previous change was not incurred by the occupant
        #   2. There was setpoint change
        if ( abs(T_stp_cool_change) != 0 or abs(T_stp_heat_change) != 0 ) and not self.recent_stp_change:
            
            # Find the type of setpoint change
            if T_stp_cool_change != 0:
                cooling_stp_change = True
            if T_stp_heat_change != 0:
                heating_stp_change = True
            
            # If both type of setpoints were changed then refer to largest setpoint change as the primary setpoint change
            # TODO: Develop this methodology to find the type of setpoint change. 
            if cooling_stp_change and heating_stp_change:
                if abs(cooling_stp_change) > abs(heating_stp_change):
                    heating_stp_change = False
                else:
                    cooling_stp_change = False
      
            if not self.recent_stp_change:
                self.T_CT = np.mean([self.setpoints['previous']['heat'], self.setpoints['previous']['cool']])
            else:
                self.T_CT = 72 # TODO: If the thermostat schedule was overriden then assign that value

        # Discomfort Model:
        if self.TTO is not None:
            if self.TTO:
                self.TTO =- 1

            ['T_ctrl', 'T_stp_cool', 'T_stp_heat', 'hum', 'T_out', 'fan', 'mo', 'equip_run_heat', 'equip_run_cool']
            df = self.current_env_features
            df_class = df[['T_ctrl', 'T_stp_cool', 'T_stp_heat', 'hum', 'T_out', 'fan', 'mo', 'equip_run_heat', 'equip_run_cool']].copy()
            predictions = self.discomfort_class_model.predict(df_class.values.reshape(1,-1))
            
            if predictions[0]:
                df_regress = df.copy()
                df_regress = df_regress.drop(['DateTime','schedule', 'event'])

                df_regress= df_regress[['T_ctrl','T_stp_cool','T_stp_heat','hum','T_out','fan','mo','equip_run_heat','equip_run_cool','year','day','hour','day_of_week']]
                features = np.array(df_regress)

                self.TTO = np.round(self.discomfort_regres_model.predict(features.reshape(1,-1)))

        # Override decision based on occupancy
        if self.habitual_schedule[self.model.timestep_day] == 1 and self.occupancy[self.model.timestep_day] == 1:
            implement_heat_cool_override(occupant=self,df=df)

        if self.TTO == 0:
            implement_heat_cool_override(occupant=self,df=df)
            self.TTO = None


        print(f"Occupant ID: {self.unique_id} simulated")

class OccupantModel(mesa.Model):
    """ Occupant model: Contains model simulation information required """
    def __init__(self, N_homes,N_occupants_in_home, sampling_frequency, model_class, model_regres) -> None:
        super().__init__()
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
        # 
        self.timestep_day = 0
        #
        self.stp_cool = None
        #
        self.stp_heat = None

        # Create homes
        for home_ID in range(0, N_homes):
            for occup_ID in range(0,self.N_occupants_in_home):
                # Create occupant
                occup = Occupant(unique_id=home_ID + occup_ID, model=self, home_ID=home_ID, model_class = model_class, model_regres=model_regres)
                # Add occupant to the scheduler
                self.schedule.add(occup)

    def step(self, data) -> None:
        print(f"Time step: {self.schedule.steps}")

        # Send simulated indoor env data to the occupant agent
        for agent in self.schedule.agents:
            agent.current_env_features = data.loc[self.schedule.steps].copy()

        self.schedule.step()


        if self.current_min_of_the_day == 55:
            self.current_hour_of_the_day += 1
        if self.current_hour_of_the_day == 24:
            self.current_hour_of_the_day = 0
            if self.current_day_of_the_week == 6:
                self.current_day_of_the_week = 0
            else:
                self.current_day_of_the_week += 1 
        if self.current_min_of_the_day != 55:
            self.current_min_of_the_day += 5
        else:
            self.current_min_of_the_day = 0
        if self.timestep_day == 288:
            self.timestep_day = 0
        else:
            self.timestep_day += 1
