from starlette.routing import Route
from controllers.simulation_controller import comparision_simulation

routes = [
    Route("/compare", endpoint=comparision_simulation),
]
