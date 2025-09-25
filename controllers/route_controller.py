from starlette.responses import JSONResponse
import os


# move to dotenv later
ROUTES_FOLDER = 'C:/Users/GIS2025/Q-learning/dqn_server/intersection/'

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
        return JSONResponse({"error": "Directory does not exist."}, status_code=404)
    
    files = get_file_list(directory_path)
    return JSONResponse({"files": files})