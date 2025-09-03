from starlette.responses import JSONResponse

async def comparision_simulation(request):
    return JSONResponse({"hello": "world"})