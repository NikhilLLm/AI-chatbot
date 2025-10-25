# Chatbot Frontend

A modern Flask-based frontend for the AI chatbot application.

## Features

- **Modern UI**: Clean, responsive design with gradient backgrounds and smooth animations
- **Real-time Chat**: WebSocket-based communication with the backend
- **User Authentication**: Token-based session management
- **Auto-reconnection**: Automatic reconnection on connection loss
- **Typing Indicators**: Visual feedback when AI is responding
- **Message History**: Persistent chat sessions
- **Mobile Responsive**: Works on desktop and mobile devices

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure the backend server is running on `http://localhost:3500`

3. Run the Flask application:
```bash
python app.py
```

4. Open your browser and go to `http://localhost:5000`

## Usage

1. Enter your name to start a chat session
2. Type messages and press Enter or click Send
3. The AI will respond in real-time
4. Use the refresh button to reload the chat
5. Use the logout button to end the session

## API Endpoints

- `GET /` - Main chat interface
- `POST /get_token` - Get a new chat token
- `POST /refresh_token` - Refresh existing token
- `GET /test_backend` - Test backend connection

## WebSocket Connection

The frontend connects to the backend WebSocket at `ws://localhost:3500/chat?token={token}` for real-time messaging.

## File Structure

```
client/
├── app.py                 # Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Main HTML template
└── static/
    ├── css/
    │   └── style.css     # CSS styles
    └── js/
        └── app.js        # JavaScript application
```
