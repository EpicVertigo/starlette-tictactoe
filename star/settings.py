from starlette.config import Config
from starlette.datastructures import Secret
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.templating import Jinja2Templates

from star.middleware import SessionUIDMiddleware

config = Config('.env')

# Debug mode should be disabled in production
DEBUG = config('DEBUG', cast=bool, default=False)

# Application secret
SECRET_KEY = config('SECRET', cast=Secret, default=None)

# Current host and port
HOST = config('HOST', cast=str, default='localhost')
PORT = config('PORT', cast=int, default='8000')
ADDRESS = f'{HOST}:{PORT}'

# Templates
templates = Jinja2Templates(directory='templates')

# Middleware
middleware = [
    Middleware(SessionMiddleware, secret_key=SECRET_KEY),
    Middleware(SessionUIDMiddleware)
]
