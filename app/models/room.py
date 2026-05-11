from flask_socketio import SocketIO, emit, join_room
from app.extensions import db
from app.models import Room, RoomPlayer

# When user joins a room
@SocketIO.on('join_game')
def handle_join_game(data):
    room_code = data['room_code']
    user_id = data['user_id']
    
    # Add user to the room in the database
    room = Room.query.filter_by(room_code=room_code).first()
    if room:
        new_player = RoomPlayer(room_id=room.id, user_id=user_id)
        db.session.add(new_player)
        db.session.commit()
        
        # Join the SocketIO room
        join_room(room_code)
        
        # Notify other players in the room
        emit('player_joined', {'user_id': user_id}, room=room_code)
