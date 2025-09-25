from starlette.routing import Route
from controllers.simulation_controller import comparision_simulation, training_simulation
from controllers.route_controller import route_list
from starlette.responses import JSONResponse

async def healthcheck(request):
    return JSONResponse({"status": "ok"})

routes = [
    Route("/compare", endpoint=comparision_simulation, methods=["GET"]),
    Route("/all-routes", endpoint=route_list, methods=["GET"]),
    Route("/train", endpoint=training_simulation, methods=["POST"]),
    Route("/health-check", endpoint=healthcheck, methods=["POST"]),
]
