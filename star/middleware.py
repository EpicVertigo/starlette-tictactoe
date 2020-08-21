import logging
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger('uvicorn')


class SessionUIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if not 'uid' in request.session:
            logger.debug('Generating new session uid from middleware')
            uid = str(uuid4())
            request.session.update({'uid': uid})
        response = await call_next(request)
        return response
