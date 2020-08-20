import os
from uuid import uuid4

import uvicorn
from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.middleware.sessions import SessionMiddleware
from starlette.routing import Route, WebSocketRoute
from starlette.templating import Jinja2Templates

from star.endpoints import GameRoomEndpoint, MainServer

templates = Jinja2Templates(directory='templates')
HOST = os.getenv('HOST')


class Homepage(HTTPEndpoint):
    async def get(self, request):
        response = templates.TemplateResponse('index.html', {'request': request, 'host': HOST})
        if not 'uid' in request.session:
            uid = str(uuid4())
            request.session.update({'uid': uid})
        return response


routes = [
    Route("/", Homepage),
    WebSocketRoute("/ws", MainServer),
    WebSocketRoute("/ws/{room:str}", GameRoomEndpoint),
]


app = Starlette(routes=routes)
app.add_middleware(SessionMiddleware, secret_key='secret')  # TODO: wow, so secure


if __name__ == '__main__':
    uvicorn.run(app=app, host='0.0.0.0', port=8000)
