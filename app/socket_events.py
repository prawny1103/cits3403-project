from app import socketio
from flask_socketio import join_room, emit
from flask_login import current_user

# Dictionary to track active players in each room
active_players = {}

# When user joins a room
@socketio.on('join_room')
def handle_join(data):
    room = data.get('room_code')
    join_room(room)

    # Add player to active players list
    if room not in active_players:
        active_players[room] = []

    if current_user.username not in active_players[room]:
        active_players[room].append(current_user.username)
    
    # Notify clients to update player list
    emit('update_players', {'players': active_players[room]}, to=room)

@socketio.on('start_game')
def handle_start(data):
    room = data.get('room_code')
    # Notify clients in the room that the game is starting (redirect to quiz page)
    emit('game_starting', to=room)
    