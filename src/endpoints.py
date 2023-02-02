from starlette import status
from starlette.endpoints import WebSocketEndpoint

from src.responses import (
    RESPONSE_CLOSE, RESPONSE_CONNECTED, ResponseEvent, build_chat_message,
    build_game_log, build_response
)
from src.rooms import WebsocketRoom, room_manager
from src.websockets import EnhancedWebscoket


class BaseGameWebSocketEndpoint(WebSocketEndpoint):
    """
    Default Starlette WebSocketEndpoint with additional methods. 
    By default uses EnhancedWebsocket class for dispatching all incoming
    and outcoming requests. Adds client management functionality on connect,
    receive and disconnect events. 

    This class uses dispatch_methods class
    attribute to hold reference to event types and related resolver functions
    through `dispatch_request` method. Resolver function must be async and
    accept websocket and data as first arguments 
    """
    encoding = 'json'
    clients = set()
    dispatch_methods = {}

    def _get_old_connection(self, websocket: EnhancedWebscoket) -> EnhancedWebscoket:
        for client in self.clients:
            if client == websocket:
                return client
        return None

    async def on_chat_message(self, websocket: EnhancedWebscoket, data: dict) -> None:
        await self.broadcast_chat_message(data.get('message'), websocket)

    async def dispatch(self) -> None:
        """
        Overriden `dispatch` method which uses EnhancedWebsocket class instead
        of default WebSocket. Any other functionality stayed intact
        """
        websocket = EnhancedWebscoket(
            self.scope, receive=self.receive, send=self.send)
        await self.on_connect(websocket)

        close_code = status.WS_1000_NORMAL_CLOSURE

        try:
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.receive":
                    data = await self.decode(websocket, message)
                    await self.on_receive(websocket, data)
                elif message["type"] == "websocket.disconnect":
                    close_code = int(message.get(
                        "code", status.WS_1000_NORMAL_CLOSURE))
                    break
        except Exception as exc:
            close_code = status.WS_1011_INTERNAL_ERROR
            raise exc from None
        finally:
            await self.on_disconnect(websocket, close_code)

    async def dispatch_request(self, websocket: EnhancedWebscoket, data: dict):
        """Dispatcher for incoming messages through websocket.

        Args:
            websocket (EnhancedWebscoket): Websocket that sent current data
            data (dict): JSON data from websocket. By default this method
            expects data in format:
            ```
                {
                    "event_type": ResponseEvent,
                    "data": {} dictionary with unstructured data
                }
            ```
        """
        event_type = data.get('event_type', None)
        # Issue a disconnect on empty event
        # TODO: Add strict check for existing events only
        if not event_type:
            await websocket.send_json(RESPONSE_CLOSE)
            await websocket.close()
        method = self.dispatch_methods.get(event_type, None)
        if method:
            await method(websocket=websocket, data=data.get('data', {}))

    async def on_receive(self, websocket: EnhancedWebscoket, data: dict) -> None:
        """Redirects any incoming data to internal request dispatcher

        Args:
            websocket (EnhancedWebscoket): Websocket that sent current data
            data (dict): Raw dictionary with data from websocket
        """
        await self.dispatch_request(websocket, data)

    async def broadcast(self, data: dict) -> None:
        """Helper function to broadcast raw data dictionary to all connected
        clients

        Args:
            data (dict): Raw dictionary with data
        """
        for client in self.clients:
            await client.send_json(data)

    async def broadcast_chat_message(self, message: str, websocket: EnhancedWebscoket = None):
        """Shortcut function to broadcast message of type
        ResponseEvent.CHAT_MESSAGE. If websocket keyword argument is empty,
        chat message sender will be set to `Server`

        Args:
            message (str): Text message
            websocket (EnhancedWebscoket, optional): Sender of message. If None
            then sender will be set to `Server`
        """
        await self.broadcast(build_chat_message(message=message, websocket=websocket))

    async def on_connect(self, websocket: EnhancedWebscoket) -> None:
        await websocket.accept()
        if not websocket.uid:
            await websocket.send_json(RESPONSE_CLOSE)
            await websocket.close()
        if websocket not in self.clients:
            self.clients.add(websocket)
            await websocket.send_json(RESPONSE_CONNECTED)
        else:
            # Close previous connection, open new
            old_connection = self._get_old_connection(websocket)
            await old_connection.close()
            self.clients.add(websocket)

    async def on_disconnect(self, websocket: EnhancedWebscoket, close_code: int):
        if websocket in self.clients:
            self.clients.remove(websocket)


class MainServer(BaseGameWebSocketEndpoint):
    """
    Endpoint that represents entrypoint for all connected users. Holds reference
    to RoomManager instance and manages incoming chat messages and new room
    creation requests
    """
    room_manager = room_manager

    @property
    def dispatch_methods(self) -> dict:
        return {
            'chat_message': self.on_chat_message,
            'create_room': self.create_room,
        }

    async def create_room(self, websocket: EnhancedWebscoket, data: dict) -> None:
        new_room = WebsocketRoom(data.get('name', None))
        if new_room in self.room_manager:
            await websocket.send_json(build_response(
                event_type=ResponseEvent.CREATE_ROOM_FAILED,
                message=f'Room {new_room.name} already exists'
            ))
        else:
            self.room_manager.create_room(new_room)
            await websocket.send_json(build_response(
                event_type=ResponseEvent.CREATE_ROOM_SUCCESS,
                message=f'Room {new_room.name} created'
            ))
            await websocket.send_json(self.room_manager.all_rooms)

    async def on_connect(self, websocket: EnhancedWebscoket) -> None:
        await super().on_connect(websocket)
        await websocket.send_json(self.room_manager.all_rooms)
        await self.broadcast_chat_message(f'{websocket.display_name} connected')


class GameRoomEndpoint(BaseGameWebSocketEndpoint):
    """
    Websocket endpoint that represents game room. Holds reference to
    WebsocketRoom object. Instead of holding references to current clients, all
    clients are located inside `self.room` object. Websocket will initialize
    on first connection and will try to search if current url path (room name)
    is registered in RoomManager instance.
    This endpoint dispatches chat messages, current room status and room.game
    status and data
    """
    room: WebsocketRoom = None

    @property
    def dispatch_methods(self) -> dict:
        return {
            'get_clients_count': self.get_room_clients_count,
            'send_game_status': self.send_game_status,
            'chat_message': self.on_chat_message,
            'make_move': self.make_move
        }

    async def make_move(self, websocket: EnhancedWebscoket, data: dict) -> None:
        """Dispatcher method to process incoming game move data. Will return
        if current game is not available (either didn't start or finished).
        Will broadcast additional game log data upon successfull move and send
        updated game status to both players.

        Args:
            websocket (EnhancedWebscoket): Current player
            data (dict): Data with game move. Keys with coordinates (x and y)
            are expected.
        """
        if not self.room.game:
            await websocket.send_json(build_chat_message(
                message='Game did not start yet'
            ))
            return
        try:
            x, y = int(data.get('x')), int(data.get('y'))
            self.room.game.make_move(x, y, websocket)
            if self.room.game.winner:
                await self.send_game_status()
                await self.broadcast(build_game_log(
                    message=f'Game is finished, the winner is {self.room.game.winner}'
                ))
                self.room.game = None
            else:
                await self.broadcast(build_game_log(
                    message=f'{websocket.display_name} player made a move [{x}:{y}]'
                ))
                await self.send_game_status()
                return
        except Exception as exc:
            await websocket.send_json(build_game_log(message=str(exc)))
            return

    async def broadcast(self, data: dict) -> None:
        """Room specific broadcast function"""
        for client in self.room.clients:
            await client.send_json(data)

    async def get_room_clients_count(self, websocket: EnhancedWebscoket, **kwargs) -> None:
        await websocket.send_json(build_response(
            event_type=ResponseEvent.GET_ROOM_CLIENTS_COUNT,
            data={'count': str(self.room.client_count)}
        ))

    async def send_game_status(self) -> None:
        """Helper method to send updated game data"""
        await self.broadcast(build_response(
            event_type='game_update',
            data={
                "winner": self.room.game.winner,
                "board": self.room.game.board.tolist()
            }
        ))

    async def on_connect(self, websocket: EnhancedWebscoket) -> None:
        await websocket.accept()
        room_name = websocket.path_params['room']
        room = room_manager.get_room(room_name)

        if not room or (websocket not in room and room.is_full):
            await websocket.send_json(build_response(
                event_type=ResponseEvent.CONNECTION_CLOSE,
                message='Room does not exist or this room is full'
            ))
            await websocket.close()
            return

        self.room = room
        response = build_response(
            event_type=ResponseEvent.JOIN_ROOM,
            message=f'Client {websocket.display_name} connected to {self.room.name}'
        )
        if websocket not in self.room.clients:
            self.room.clients.add(websocket)
        else:
            old_connection = self._get_old_connection(websocket)
            await old_connection.close()
            self.room.clients.add(websocket)
        await self.broadcast(response)
        await self.get_room_clients_count(websocket)

        # Start game here?
        if self.room.is_full and not self.room.game:
            self.room.start_new_game()
            await self.broadcast_chat_message('Game is starting')
            await self.send_game_status()

    async def on_disconnect(self, websocket: EnhancedWebscoket, close_code: int):
        if self.room:
            # Cancel current game
            if self.room.game:
                self.room.game = None
            # Remove user from room
            if websocket in self.room:
                self.room.remove_client(websocket)
            # If some people left in the room - announce it
            if self.room.clients:
                await self.broadcast_chat_message(f'{websocket.display_name} disconnected')
