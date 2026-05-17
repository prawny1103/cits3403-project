import pytest
from app.socket_events import active_players, game_state
from app.models.quiz import Room, Question
from app.extensions import db

# Test join_room event
def test_socket_join_room(socket_client):
    room_code = '1234'
    socket_client.emit('join_room', {'room_code': room_code})
    
    # Get messages received by the client
    received = socket_client.get_received()
    
    # Check if 'update_players' event was emitted
    update_event = next((m for m in received if m['name'] == 'update_players'), None)
    assert update_event is not None
    assert 'tester' in update_event['args'][0]['players']
    assert active_players[room_code] == ['tester']

# If a room is started without questions, an error is expected
def test_socket_start_game_no_questions(app, socket_client):
    room_code = '5678'
    with app.app_context():
        room = Room(room_code=room_code, is_active=True)
        db.session.add(room)
        db.session.commit()

    socket_client.emit('join_room', {'room_code': room_code})
    socket_client.emit('start_game', {'room_code': room_code})
    
    received = socket_client.get_received()
    error_event = next((m for m in received if m['name'] == 'error'), None)
    assert error_event is not None
    assert error_event['args'][0]['message'] == 'No questions available for this quiz.'

# Check that games are started properly
def test_socket_start_game_success(app, socket_client):
    room_code = '9999'
    with app.app_context():
        # Setup room and a question
        room = Room(room_code=room_code, is_active=True)
        db.session.add(room)
        db.session.commit()
        
        q = Question(room_id=room.id, text="Test Q?", correct_answer="A")
        db.session.add(q)
        db.session.commit()

    socket_client.emit('join_room', {'room_code': room_code})
    socket_client.emit('start_game', {'room_code': room_code})
    
    received = socket_client.get_received()
    assert any(m['name'] == 'game_starting' for m in received)
    assert room_code in game_state

# If a user leaves the room, they should be able to rejoin without being added to the list twice
def test_duplicate_player_joins(socket_client):
    room_code = '1111'
    socket_client.emit('join_room', {'room_code': room_code})
    socket_client.emit('join_room', {'room_code': room_code})
    
    assert active_players[room_code].count('tester') == 1