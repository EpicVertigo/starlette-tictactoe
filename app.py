from uuid import uuid4

import uvicorn
from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import FileResponse, HTMLResponse
from starlette.routing import Route, WebSocketRoute

from star.endpoints import GameRoomEndpoint, MainServer


class Homepage(HTTPEndpoint):
    async def get(self, request):
        response = FileResponse('templates/index.html')
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
app.add_middleware(SessionMiddleware, secret_key='secret')


if __name__ == '__main__':
    uvicorn.run(app=app, host='0.0.0.0', port=8000)
