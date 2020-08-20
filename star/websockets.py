import logging
from uuid import uuid4

from starlette.websockets import WebSocket

logger = logging.getLogger('uvicorn')


class EnhancedWebscoket(WebSocket):
    """
    Starlette's WebSocket object with additional methods and unique ID
    """
    _uid = None
    _display_name = None

    @property
    def uid(self):
        if not self._uid:
            session_uid = self.session.get('uid', None)
            if session_uid:
                self._uid = session_uid
            else:
                # Attempt to generate new uuid
                logger.info('Generating new uid')
                uid = str(uuid4())
                self.session.update({'uid': uid})
                self._uid = uid
        return self._uid

    @property
    def display_name(self):
        if not self._display_name:
            username = self.session.get('display_name', None)
            self._display_name = username or f'AnonymousUser_{self.uid[-6:]}'
        return self._display_name

    def __hash__(self):
        return hash(self.uid)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __ne__(self, other):
        return hash(self) != hash(other)

    def __str__(self):
        return f'<WebSocketClient {self.display_name or self.uid}>'
