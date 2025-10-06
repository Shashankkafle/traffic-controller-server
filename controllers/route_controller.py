from starlette.responses import JSONResponse
import os


# move to dotenv later
ROUTES_FOLDER = 'C:/Users/GIS2025/Q-learning/dqn_server/intersection'

def get_file_list(directory_path):
    try:
        # Return a list of only the files in the directory
        return [
            f for f in os.listdir(directory_path)
            if os.path.isfile(os.path.join(directory_path, f)) and ".rou" in f
        ]
    except Exception as e:
        raise Exception(f"Error: {e}")
        # return []
async def route_list(request):
    directory_path = ROUTES_FOLDER
    if not os.path.exists(directory_path):
        return JSONResponse({"error": "Directory does not exist.(please correctly set the route directory in the server)"}, status_code=404)
    
    files = get_file_list(directory_path)
    return JSONResponse({"files": files})

async def set_active_route(request):
    directory_path = ROUTES_FOLDER
    print("request.app.state",request.app.state)
    if not os.path.exists(directory_path):
        print("Directory does not exist set")
        return JSONResponse({"error": "Directory does not exist.(please correctly set the route directory in the server)"}, status_code=404)
    form = await request.form()
    route_name =form.get("route_name")
    if not route_name or route_name not in get_file_list(directory_path):
        return JSONResponse({"error": "Route file does not exist."}, status_code=404)
    request.app.state.active_route_path = route_name
    return JSONResponse({f"message": f"The active route is now set to {route_name}"}, status_code=200)

async def get_active_route(request):
    directory_path = ROUTES_FOLDER
    if not os.path.exists(directory_path):
        print("Directory does not exist get")
        return JSONResponse({"error": "Directory does not exist.(please correctly set the route directory in the server)"}, status_code=404)
    route_name =  request.app.state.active_route_path
    return JSONResponse({"message": f"The active route is {route_name}"}, status_code=200)