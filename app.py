from uuid import uuid4

import uvicorn
from starlette.applications import Starlette
from starlette.endpoints import HTTPEndpoint
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse
from starlette.routing import Route, WebSocketRoute

from star.endpoints import GameRoomEndpoint, MainServer

# TODO: Create static html file instead
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <form action="" onsubmit="sendCreateRoom(event)">
            <input type="text" id="roomName" autocomplete="off"/>
            <button>Create room</button>
        </form>
        <form action="" onsubmit="sendJoinRoom(event)">
            <input type="text" id="roomNameJoin" autocomplete="off"/>
            <button>Join room</button>
        </form>
            <form action="" onsubmit="sendMakeMove(event)">
            <input type="text" id="sendGameX" autocomplete="off"/>
            <input type="text" id="sendGameY" autocomplete="off"/>
            <button>make move</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                console.log(event.data)
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(JSON.stringify({'event_type': 'chat_message', data: {'message': input.value}}))
                input.value = ''
                event.preventDefault()
            }
            function sendCreateRoom(event) {
                var input = document.getElementById("roomName")
                ws.send(JSON.stringify({'event_type': 'create_room', data: {'name': input.value}}))
                input.value = ''
                event.preventDefault()
            }
            function sendMakeMove(event) {
                var inputX = document.getElementById("sendGameX")
                var inputY = document.getElementById("sendGameY")
                ws.send(JSON.stringify({'event_type': 'make_move', data: {x: inputX.value, y: inputY.value}}))
                inputX.value = ''
                inputY.value = ''
                event.preventDefault()
            }
            function sendJoinRoom(event) {
                var input = document.getElementById("roomNameJoin")
                ws.close()
                ws = new WebSocket(`ws://localhost:8000/ws/${input.value}`)
                ws.onmessage = function(event) {
                    console.log(event.data)
                    var messages = document.getElementById('messages')
                    var message = document.createElement('li')
                    var content = document.createTextNode(event.data)
                    message.appendChild(content)
                    messages.appendChild(message)
                };
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


class Homepage(HTTPEndpoint):
    async def get(self, request):
        response = HTMLResponse(html)
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
