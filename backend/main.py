import uvicorn as uvicorn

import fastapi as _fastapi
from backend.api import analytic

app = _fastapi.FastAPI()


def configure():
    configure_routing()


def configure_routing():
    app.include_router(analytic.router)

if __name__ == "__main__":
    configure()
    uvicorn.run(app, port=8000, host='127.0.0.1')
else:
    configure()