from starlette.responses import JSONResponse
from universal_generator import UniversalTrafficGenerator
from utils import name_from_param, set_sumo
from model import TestModel
from simulation_methods.fixed_duration_calculation import get_durations
from simulation_methods.fixed_time_sim import Simulation
from visualization import Visualization

import os

async def comparision_simulation(request):
    # number of cars running i the simulation
    num_cars = int(request.query_params.get("num_cars"))
    # random seed for reproducibility
    seed = request.query_params.get("seed")
    # model green duration
    model_green_duration = int(request.query_params.get("green_duration"))
    # model green duration
    simulation_duration = int( request.query_params.get("simultion_duration")
)
    model_name = name_from_param(num_cars,model_green_duration)
    model_path = f"./models/{model_name}"

    # SUMO network file and output trips file
    # may need to make dynamic later
    NET_FILE = "./intersection/environment.net.xml"
    OUTPUT_TRIPS_FILE = "./intersection/episode_routes.rou.xml"
    sumocfg_file = "sumo_config.sumocfg"
    print("model_path",model_path)
    if not os.path.exists(model_path):
        return JSONResponse({"error": f"Model with given specs does not exist."}, status_code=404)
    
    comaprision_path = f"{model_path}/test/comparison"

    visualization = Visualization(
       comaprision_path, 
        dpi=96
    )

    Model = TestModel(
        input_dim=80,
        model_path=model_path
    )
    
    TrafficGen = UniversalTrafficGenerator(
        NET_FILE,
        OUTPUT_TRIPS_FILE,
        sim_end=simulation_duration,
        vehicle_count= num_cars 
    )

    fixed_durations, lane_group_counts = get_durations(OUTPUT_TRIPS_FILE, simulation_duration)

    sumo_cmd = set_sumo(False, sumocfg_file, simulation_duration)
    
    Model_Simulation = Simulation(
        Model,
        TrafficGen,
        sumo_cmd,
        simulation_duration,
        model_green_duration,
        3,
        3,
        80,
        4,
        False,
    )
    Cyclic_Simulation = Simulation(
        Model,
        TrafficGen,
        sumo_cmd,
        simulation_duration,
        model_green_duration,
        3,
        3,
        80,
        4,
        True,
        durations=fixed_durations,
        
    )
    Cyclic_Simulation.run(seed)
    Model_Simulation.run(seed)
    response_Data = {}
    response_Data['model_stats'] = {}
    response_Data['fixed_time'] = {}
    response_Data['webster_fixed_timings'] = fixed_durations
    response_Data['vehicles_per_lane_group'] = lane_group_counts
    response_Data['model_stats']['queue_length'] = Model_Simulation.queue_length_episode
    response_Data['fixed_time']['queue_length'] = Cyclic_Simulation.queue_length_episode
    response_Data['model_stats']['average_wait_length'] = Model_Simulation.avg_wait_episode
    response_Data['fixed_time']['average_wait_length'] = Cyclic_Simulation.avg_wait_episode
    response_Data['model_stats']['cum_wait_time_per_vehicle'] = Model_Simulation.cum_wait_time_per_vehicle
    response_Data['fixed_time']['cum_wait_time_per_vehicle'] = Cyclic_Simulation.cum_wait_time_per_vehicle
    response_Data['model_stats']['total_wait'] =sum(Model_Simulation.cum_wait_time_per_vehicle.values())
    response_Data['fixed_time']['total_wait'] = sum(Cyclic_Simulation.cum_wait_time_per_vehicle.values())



    return JSONResponse(response_Data, status_code=200)