from starlette.applications import Starlette

from star import settings
from star.routes import routes


def create_app() -> Starlette:
    return Starlette(routes=routes, middleware=settings.middleware)
