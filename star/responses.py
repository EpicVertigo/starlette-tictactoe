from datetime import datetime
from enum import Enum
from functools import partial

from star.websockets import EnhancedWebscoket


class ResponseEvent(Enum):
    # TODO: Clean this up
    CONNECTION_OPEN = 'connection_open'
    CONNECTION_CLOSE = 'connection_close'
    GET_ALL_ROOMS = 'get_all_rooms'
    CREATE_ROOM_SUCCESS = 'create_room'
    CREATE_ROOM_FAILED = 'create_room_failed'
    JOIN_ROOM = 'join_room'
    LEAVE_ROOM = 'leave_room'
    CHAT_MESSAGE = 'chat_message'
    GET_ROOM_CLIENTS_COUNT = 'get_cleints_count'
    GAME_FINISHED = 'game_finished'

    GAME_UPDATE = 'game_update'
    GAME_LOG = 'game_log'


def build_response(event_type: str, data: dict = None, message: str = None,
                   websocket: EnhancedWebscoket = None) -> dict:
    event_value = event_type.value if isinstance(
        event_type, ResponseEvent) else event_type
    if not data:
        data = {'sender': 'Server',
                'timestamp': datetime.now().strftime('%H:%M:%S')}
    if message:
        data.update({'message': message})
    if websocket:
        data.update({'sender': websocket.display_name or websocket.uid})
    return {
        'event_type': event_value,
        'data': data
    }


build_chat_message = partial(
    build_response, event_type=ResponseEvent.CHAT_MESSAGE)
build_game_log = partial(build_response, event_type=ResponseEvent.GAME_LOG)

RESPONSE_CONNECTED = build_response(
    event_type=ResponseEvent.CONNECTION_OPEN,
    message='Client connected'
)

RESPONSE_CLOSE = build_response(
    event_type=ResponseEvent.CONNECTION_CLOSE,
    message='Client disconnected'
)
