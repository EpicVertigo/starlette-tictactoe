from starlette.applications import Starlette

from src import settings
from src.routes import routes


def create_app() -> Starlette:
    return Starlette(routes=routes, middleware=settings.middleware)
