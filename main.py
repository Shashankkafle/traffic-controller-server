from starlette.applications import Starlette
from routes import routes


app = Starlette(debug=True, routes=routes)

# Global flag to showing if training is running
app.state.isTraining = False
