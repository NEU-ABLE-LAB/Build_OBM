""" model.py -> Contains basic framework to simulate an occupant agent for a given set of environment inputs """

# Import packages
from turtle import home
import mesa
import pandas as pd
from tools import *

# Occupant agent class
class Occupant(mesa.Agent):
    """ An occupant agent: Contains information specific to an occupant """
    def __init__(self, unique_id: int, model, home_ID) -> None:
        super().__init__(unique_id, model)
        # Occupant's residence
        self.home_ID = home_ID
        # Place holder variable to contain environment info for each timestep
        self.current_env_features = None 
        # Transition matrix to simulate occupant's presence
        self.occupancy_tp_matrix = pd.read_csv('data/transition_matrix.csv')
        # Place holder variable to contain simulated occupancy for a simulation's day
        self.occupancy = []

        print(f"Occupant created, ID: {unique_id}")

    def step(self) -> None:

        # Synthesize occupancy data
        if self.model.schedule.steps % 24 == 0:
            # Occupancy model: If day is new, simulate occupancy for the day
            self.occupancy.extend(Markov_occupancy_model(self.occupancy_tp_matrix, sampling_time = self.model.sampling_frequency))
        
        # Comfort Model: Predict comfortable temperature

        # Habitual Model:

        # Discomfort Model:

        # Override decision based on occupancy

        print(f"Occupant ID: {self.unique_id} simulated")

class OccupantModel(mesa.Model):
    """ Occupant model: Contains model simulation information required """
    def __init__(self, N_homes,N_occupants_in_home, sampling_frequency) -> None:
        super().__init__()
        # Number of occupants to be simulated in a home
        self.N_occupants_in_home = N_occupants_in_home
        # Number of homes to be simulated
        self.N_homes = N_homes
        # Type of schedule to be used to trigger occupants to react
        self.schedule = mesa.time.SimultaneousActivation(self)
        # The data/simulated needs to be simulated at the following frequency
        self.sampling_frequency = sampling_frequency

        # Create homes
        for home_ID in range(0, N_homes):
            for occup_ID in range(0,self.N_occupants_in_home):
                # Create occupant
                occup = Occupant(unique_id=home_ID + occup_ID, model=self, home_ID=home_ID)
                # Add occupant to the scheduler
                self.schedule.add(occup)

    def step(self, data) -> None:
        print(f"Time step: {self.schedule.steps}")

        # Send simulated indoor env data to the occupant agent
        for agent in self.schedule.agents:
            agent.env_features = data.loc[self.schedule.steps].copy()

        self.schedule.step()
