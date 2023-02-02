
from starlette.routing import Mount, Route, WebSocketRoute
from starlette.staticfiles import StaticFiles

from src.endpoints import GameRoomEndpoint, MainServer
from src.views import Homepage

routes = [
    Route("/", Homepage),
    WebSocketRoute("/ws", MainServer),
    WebSocketRoute("/ws/{room:str}", GameRoomEndpoint),
    Mount('/static', app=StaticFiles(directory='static'), name='static'),
]
