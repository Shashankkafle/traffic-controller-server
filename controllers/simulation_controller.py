from starlette.responses import JSONResponse
from universal_generator import UniversalTrafficGenerator
from utils import name_from_param, set_sumo
from model_methods.model import TestModel,TrainModel
from simulation_methods.fixed_duration_calculation import get_durations
from simulation_methods.fixed_time_sim import Simulation as ComparisionSim
from simulation_methods.training_simulation import Simulation as TrainingSim
from visualization import Visualization
import datetime
from shutil import copyfile
import asyncio
from model_methods.memory import Memory


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
    
    Model_Simulation = ComparisionSim(
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
    Cyclic_Simulation = ComparisionSim(
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

async def train_model(Simulation, Model, model_path, total_episodes):
    
    episode = 0
    timestamp_start = datetime.datetime.now()
    
    while episode < total_episodes:
        print('\n----- Episode', str(episode+1), 'of', str(total_episodes))
        epsilon = 1.0 - (episode / total_episodes)  # set the epsilon for this episode according to epsilon-greedy policy
        simulation_time, training_time =await asyncio.to_thread(
            Simulation.run, episode, epsilon
        )  # run the simulation
        print('Simulation time:', simulation_time, 's - Training time:', training_time, 's - Total:', round(simulation_time+training_time, 1), 's')
        episode += 1

    print("\n----- Start time:", timestamp_start)
    print("----- End time:", datetime.datetime.now())
    print("----- Session info saved at:", model_path)

    Model.save_model(model_path)

    # copyfile(src='training_settings.ini', dst=os.path.join(model_path, 'training_settings.ini'))

async def training_simulation(request):
    if request.app.state.isTraining:
        return JSONResponse({"status": "running", "message": "Training is already running"} , status_code=400)
    request.app.state.isTraining = True
    # number of cars running i the simulation
    num_cars = int(request.query_params.get("num_cars"))
    # random seed for reproducibility
    seed = request.query_params.get("seed")
    # model green duration
    model_green_duration = int(request.query_params.get("green_duration"))
    # model green duration
    simulation_duration = int( request.query_params.get("simulation_duration"))
    num_layers =int( request.query_params.get("num_layers"))
    width_layers =int( request.query_params.get("width_layers"))
    batch_size = int(request.query_params.get("batch_size") )
    learning_rate = float(request.query_params.get("learning_rate"))
    num_actions = int(request.query_params.get("num_actions"))
    memory_size_max =  int(request.query_params.get("memory_size_max"))
    memory_size_min = int(request.query_params.get("memory_size_min"))
    gamma = float(request.query_params.get("gamma"))
    max_steps = int(request.query_params.get("max_steps"))
    green_duration = int(request.query_params.get("green_duration"))
    yellow_duration = int(request.query_params.get("yellow_duration"))
    clearence_interval = int(request.query_params.get("clearence_interval"))
    num_states = int(request.query_params.get("num_states"))
    training_epochs = int(request.query_params.get("training_epochs"))
    total_episodes = int(request.query_params.get("total_episodes"))

    model_name = name_from_param(num_cars,model_green_duration)
    model_path = f"./models/{model_name}"

    # SUMO network file and output trips file
    # may need to make dynamic later
    NET_FILE = "./intersection/environment.net.xml"
    OUTPUT_TRIPS_FILE = "./intersection/episode_routes.rou.xml"
    sumocfg_file = "sumo_config.sumocfg"
    Model = TrainModel(
        num_layers, 
        width_layers, 
        batch_size, 
        learning_rate, 
        input_dim=num_states, 
        output_dim=num_actions
    )

    replay_memory = Memory(
        memory_size_max, 
        memory_size_min
    )
    
    TrafficGen = UniversalTrafficGenerator(
        NET_FILE,
        OUTPUT_TRIPS_FILE,
        sim_end=simulation_duration,
        vehicle_count= num_cars 
    )


    sumo_cmd = set_sumo(False, sumocfg_file, simulation_duration)
    
    Simulation = TrainingSim(
        Model,
        replay_memory,
        TrafficGen,
        sumo_cmd,
        gamma,
        max_steps,
        green_duration,
        yellow_duration,
        clearence_interval,
        num_states,
        num_actions,
        training_epochs
    )
    # train_model(Simulation, Model, model_path, total_episodes)
    asyncio.create_task(
    train_model(Simulation, Model, model_path, total_episodes)
    ).add_done_callback(lambda t: setattr(request.app.state, 'isTraining', False))





    return JSONResponse({"status": "started", "message": "Training has been triggered"})
