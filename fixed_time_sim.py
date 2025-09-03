import traci
import numpy as np
import random
import timeit
import os

# phase codes based on environment.net.xml
PHASE_NS_GREEN = 0  # action 0 code 00
PHASE_NS_YELLOW = 1
PHASE_NSL_GREEN = 2  # action 1 code 01
PHASE_NSL_YELLOW = 3
PHASE_EW_GREEN = 4  # action 2 code 10
PHASE_EW_YELLOW = 5
PHASE_EWL_GREEN = 6  # action 3 code 11
PHASE_EWL_YELLOW = 7


action_number_to_phase_name = {
    0: "PHASE_NS_GREEN",
    1: "PHASE_NSL_GREEN",
    2: "PHASE_EW_GREEN",
    3: "PHASE_EWL_GREEN"
}
action_number_to_phase_number = {
    0: PHASE_NS_GREEN,
    1: PHASE_NSL_GREEN,
    2: PHASE_EW_GREEN,
    3: PHASE_EWL_GREEN
}

class Simulation:
    def __init__(self, Model, TrafficGen, sumo_cmd, max_steps, green_duration, yellow_duration,clearence_duration, num_states, num_actions, fixed_time=False, durations={}):
        self._Model = Model
        self._TrafficGen = TrafficGen
        self._step = 0
        self._sumo_cmd = sumo_cmd
        self._max_steps = max_steps
        self._green_duration = green_duration
        self._yellow_duration = yellow_duration
        self._clearence_duration = clearence_duration
        self._num_states = num_states
        self._num_actions = num_actions
        self._reward_episode = []
        self._avg_wait_episode = []
        self._cum_wait_time_per_vehicle = {}
        self._queue_length_episode = []
        self._fixed_time = fixed_time  # Flag to indicate if fixed time simulation is used
        self._durations = durations  # Dictionary to hold fixed durations for each action if provided


    def run(self, episode):
        """
        Runs the testing simulation
        """
        start_time = timeit.default_timer()
        traci.start(self._sumo_cmd)
        print("Simulating...")

        # inits
        self._step = 0
        self._waiting_times = {}
        old_total_wait = 0
        old_action = -1 # dummy init

        while self._step < self._max_steps:

            # get current state of the intersection
            current_state = self._get_state()

            # calculate reward of previous action: (change in cumulative waiting time between actions)
            # waiting time = seconds waited by a car since the spawn in the environment, cumulated for every car in incoming lanes
            current_total_wait,current_average_wait = self._collect_waiting_times()
            reward = old_total_wait - current_total_wait
            if self._fixed_time:
                action = (old_action + 1) % self._num_actions # cyclical action

            else:
                # choose the light phase to activate, based on the current state of the intersection
                action = self._choose_action(current_state)


            # if the chosen phase is different from the last phase, activate the yellow phase
            if self._step != 0 and old_action != action:
                self._set_yellow_phase(old_action)
                self._simulate(self._yellow_duration)
                self._set_clearence_phase()
                self._simulate(self._clearence_duration)

            # execute the phase selected before
            self._set_green_phase(action)
            if self._fixed_time:
                phase_name = action_number_to_phase_name.get(action)
                green_duration = self._durations.get(phase_name)
                # print("self._durations",self._durations,"action",phase_name,)
                # print(f"Using fixed green duration: {green_duration} seconds for action {action}")
            else:
                # use the configured green duration
                green_duration = self._green_duration
            self._simulate(green_duration)

            # saving variables for later & accumulate reward
            old_action = action
            old_total_wait = current_total_wait

            self._reward_episode.append(reward)
            self._avg_wait_episode.append(current_average_wait)
            
        
        traci.close()
        simulation_time = round(timeit.default_timer() - start_time, 1)

        return simulation_time


    def _simulate(self, steps_todo):
        """
        Proceed with the simulation in sumo
        """
        if (self._step + steps_todo) >= self._max_steps:  # do not do more steps than the maximum allowed number of steps
            steps_todo = self._max_steps - self._step

        while steps_todo > 0:
            traci.simulationStep()  # simulate 1 step in sumo
            self._step += 1 # update the step counter
            steps_todo -= 1
            queue_length = self._get_queue_length() 
            self._queue_length_episode.append(queue_length)
            self._collect_cum_waiting_time()

    def _collect_cum_waiting_time(self):
                car_list = traci.vehicle.getIDList()
                for car_id in car_list:
                    wait_time = traci.vehicle.getAccumulatedWaitingTime(car_id)
                    self._cum_wait_time_per_vehicle[car_id] = wait_time
                # print("total_waiting_time in cum",total_waiting_time)
                # return total_waiting_time
    def _collect_waiting_times(self):
        """
        Retrieve the waiting time of every car in the incoming roads
        """
        incoming_roads = ["E2TL", "N2TL", "W2TL", "S2TL"]
        car_list = traci.vehicle.getIDList()
        for car_id in car_list:
            wait_time = traci.vehicle.getAccumulatedWaitingTime(car_id)
            road_id = traci.vehicle.getRoadID(car_id)  # get the road id where the car is located
            if road_id in incoming_roads:  # consider only the waiting times of cars in incoming roads
                self._waiting_times[car_id] = wait_time
            else:
                if car_id in self._waiting_times: # a car that was tracked has cleared the intersection
                    del self._waiting_times[car_id] 
        total_waiting_time = sum(self._waiting_times.values())
        average_waiting_time = total_waiting_time / len(self._waiting_times) if self._waiting_times else 0
        return total_waiting_time, average_waiting_time


    def _choose_action(self, state):
        """
        Pick the best action known based on the current state of the env
        """
        return np.argmax(self._Model.predict_one(state))



    def _set_yellow_phase(self, old_action):
        """
        Activate the correct yellow light combination in sumo
        """
        yellow_phase_code = old_action * 2 + 1 # obtain the yellow phase code, based on the old action (ref on environment.net.xml)
        traci.trafficlight.setPhase("TL", yellow_phase_code)
        
    def _set_clearence_phase(self):
        """
        Activate the correct yellow light combination in sumo
        """
        clearence_phase_code = 8 # CAUTION: make sure this matches the network file
        traci.trafficlight.setPhase("TL", clearence_phase_code)


    def _set_green_phase(self, action_number):
        """
        Activate the correct green light combination in sumo
        """
        phase = action_number_to_phase_number.get(action_number)
        traci.trafficlight.setPhase("TL", phase)
        # if action_number == 0:
        #     traci.trafficlight.setPhase("TL", PHASE_NS_GREEN)
        # elif action_number == 1:
        #     traci.trafficlight.setPhase("TL", PHASE_NSL_GREEN)
        # elif action_number == 2:
        #     traci.trafficlight.setPhase("TL", PHASE_EW_GREEN)
        # elif action_number == 3:
        #     traci.trafficlight.setPhase("TL", PHASE_EWL_GREEN)


    def _get_queue_length(self):
        """
        Retrieve the number of cars with speed = 0 in every incoming lane
        """
        halt_N = traci.edge.getLastStepHaltingNumber("N2TL")
        halt_S = traci.edge.getLastStepHaltingNumber("S2TL")
        halt_E = traci.edge.getLastStepHaltingNumber("E2TL")
        halt_W = traci.edge.getLastStepHaltingNumber("W2TL")
        queue_length = halt_N + halt_S + halt_E + halt_W
        return queue_length


    def _get_state(self):
        """
        Retrieve the state of the intersection from sumo, in the form of cell occupancy
        """
        state = np.zeros(self._num_states)
        car_list = traci.vehicle.getIDList()

        for car_id in car_list:
            lane_pos = traci.vehicle.getLanePosition(car_id)
            lane_id = traci.vehicle.getLaneID(car_id)
            lane_pos = 750 - lane_pos  # inversion of lane pos, so if the car is close to the traffic light -> lane_pos = 0 --- 750 = max len of a road

            # distance in meters from the traffic light -> mapping into cells
            if lane_pos < 7:
                lane_cell = 0
            elif lane_pos < 14:
                lane_cell = 1
            elif lane_pos < 21:
                lane_cell = 2
            elif lane_pos < 28:
                lane_cell = 3
            elif lane_pos < 40:
                lane_cell = 4
            elif lane_pos < 60:
                lane_cell = 5
            elif lane_pos < 100:
                lane_cell = 6
            elif lane_pos < 160:
                lane_cell = 7
            elif lane_pos < 400:
                lane_cell = 8
            elif lane_pos <= 750:
                lane_cell = 9

            # finding the lane where the car is located 
            # x2TL_3 are the "turn left only" lanes
            if lane_id == "W2TL_0" or lane_id == "W2TL_1" or lane_id == "W2TL_2":
                lane_group = 0
            elif lane_id == "W2TL_3":
                lane_group = 1
            elif lane_id == "N2TL_0" or lane_id == "N2TL_1" or lane_id == "N2TL_2":
                lane_group = 2
            elif lane_id == "N2TL_3":
                lane_group = 3
            elif lane_id == "E2TL_0" or lane_id == "E2TL_1" or lane_id == "E2TL_2":
                lane_group = 4
            elif lane_id == "E2TL_3":
                lane_group = 5
            elif lane_id == "S2TL_0" or lane_id == "S2TL_1" or lane_id == "S2TL_2":
                lane_group = 6
            elif lane_id == "S2TL_3":
                lane_group = 7
            else:
                lane_group = -1

            if lane_group >= 1 and lane_group <= 7:
                car_position = int(str(lane_group) + str(lane_cell))  # composition of the two postion ID to create a number in interval 0-79
                valid_car = True
            elif lane_group == 0:
                car_position = lane_cell
                valid_car = True
            else:
                valid_car = False  # flag for not detecting cars crossing the intersection or driving away from it

            if valid_car:
                state[car_position] = 1  # write the position of the car car_id in the state array in the form of "cell occupied"
        return state


    @property
    def queue_length_episode(self):
        return self._queue_length_episode


    @property
    def reward_episode(self):
        return self._reward_episode

    @property
    def avg_wait_episode(self):
        return self._avg_wait_episode
    
    @property
    def cum_wait_time_per_vehicle(self):
        return self._cum_wait_time_per_vehicle


