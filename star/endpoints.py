from starlette import status
from starlette.endpoints import WebSocketEndpoint

from star.responses import (RESPONSE_CLOSE, RESPONSE_CONNECTED, ResponseEvent,
                            build_chat_message, build_game_log, build_response)
from star.rooms import WebsocketRoom, room_manager
from star.websockets import EnhancedWebscoket


class BaseGameWebSocketEndpoint(WebSocketEndpoint):
    clients = set()
    encoding = 'json'
    dispatch_methods = {}

    def _get_old_connection(self, websocket):
        for client in self.clients:
            if client == websocket:
                return client
        return None

    async def on_chat_message(self, websocket, data):
        await self.broadcast(build_chat_message(
            message=data.get('message'),
            websocket=websocket
        ))

    async def dispatch(self) -> None:
        """
            Overrided `dispatch` method which uses EnhancedWebsocket class instead
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

    async def dispatch_request(self, websocket, request_data):
        event_type, _ = request_data.get('event_type'), request_data.get('room')
        method = self.dispatch_methods.get(event_type, None)
        if method:
            await method(websocket, request_data.get('data', {}))

    async def on_receive(self, websocket, data):
        await self.dispatch_request(websocket, data)

    async def broadcast(self, data):
        for client in self.clients:
            await client.send_json(data)

    async def broadcast_chat_message(self, message, websocket=None):
        await self.broadcast(build_chat_message(message=message, websocket=websocket))

    async def on_connect(self, websocket: EnhancedWebscoket):
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

    async def on_disconnect(self, websocket, close_code):
        if websocket in self.clients:
            self.clients.remove(websocket)


class MainServer(BaseGameWebSocketEndpoint):
    room_manager = room_manager

    @property
    def dispatch_methods(self):
        return {
            'chat_message': self.on_chat_message,
            'create_room': self.create_room,
        }

    async def create_room(self, websocket, data: dict):
        new_room = WebsocketRoom(data.get('name', None))
        if new_room in self.room_manager:
            await websocket.send_json(build_response(
                event_type=ResponseEvent.CREATE_ROOM_FAILED,
                message=f'Room {new_room.name} already exists'
            ))
        else:
            self.room_manager.create_room(new_room)
            await websocket.send_json(build_response(
                event_type=ResponseEvent.CREATE_ROOM,
                message=f'Room {new_room.name} created'
            ))
            await websocket.send_json(self.room_manager.all_rooms)

    async def on_connect(self, websocket):
        await super().on_connect(websocket)
        await websocket.send_json(self.room_manager.all_rooms)
        await self.broadcast_chat_message(f'{websocket.display_name} connected')


class GameRoomEndpoint(BaseGameWebSocketEndpoint):
    room: WebsocketRoom = None

    @property
    def dispatch_methods(self):
        return {
            'get_clients_count': self.get_room_clients_count,
            'send_game_status': self.send_game_status,
            'chat_message': self.on_chat_message,
            'make_move': self.make_move
        }

    async def make_move(self, websocket, data):
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

    async def broadcast(self, data):
        for client in self.room.clients:
            await client.send_json(data)

    async def get_room_clients_count(self, websocket, _):
        await websocket.send_json(build_response(
            event_type=ResponseEvent.GET_ROOM_CLIENTS_COUNT,
            data={'count': str(self.room.client_count)}
        ))

    async def send_game_status(self):
        await self.broadcast(build_response(
            event_type='game_update',
            data={
                "winner": self.room.game.winner,
                "board": self.room.game.board.tolist()
            }
        ))

    async def on_connect(self, websocket):
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
        await self.get_room_clients_count(websocket, None)

        # Start game here?
        if self.room.is_full and not self.room.game:
            self.room.start_new_game()
            await self.broadcast_chat_message('Game is starting')
            await self.send_game_status()

    async def on_disconnect(self, websocket, close_code):
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
