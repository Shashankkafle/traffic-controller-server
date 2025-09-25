from starlette.applications import Starlette
from routes import routes


app = Starlette(debug=True, routes=routes)

# Global flag to showing if training is running
app.state.isTraining = False
# Global variable storing the active route path for model comparisions and training
app.state.active_route_path = 'episode_routes.rou.xml'
