# TicTacToe Websocket Backend

Serverside `TicTacToe` based on Starlette's Websockets

Todo list:

- [x] Unique session ID for each Websocket connection
- [x] Main websocket endpoint. Allows all connected users to chat, discover rooms and create new rooms
- [x] GameRoom websocket endpoint. Clients are limited to 2, local chat and TicTacToe game instance
- [x] Awful simple http response to test Main and GameRoom endpoints
- [ ] Cover everything in tests
- [ ] Unity project as a frontend
- [ ] Setup heroku deploy
