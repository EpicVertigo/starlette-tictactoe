
from starlette.routing import Route, WebSocketRoute

from star.endpoints import GameRoomEndpoint, MainServer
from star.views import Homepage

routes = [
    Route("/", Homepage),
    WebSocketRoute("/ws", MainServer),
    WebSocketRoute("/ws/{room:str}", GameRoomEndpoint),
]
