import time
import json
from app import socketio
from app.models.quiz import Room, Question, Game, PlayerStats
from flask_socketio import join_room, emit
from flask_login import current_user

# Dictionary to track active players in each room
active_players = {}
game_state = {}

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
    room_code = data.get('room_code')
    room = Room.query.filter_by(room_code=room_code).first()
    questions = Question.query.limit(room.question_count).all()

    game_state[room_code] = {
        'questions': [i.id for i in questions],
        'time_limit': room.time_limit,
        'current': 0,
        'scores': {},
        'question_start_time': 0
    }

    # Notify clients in the room that the game is starting (redirect to quiz page)
    emit('game_starting', to=room_code)
    send_next_question(room_code)

def send_next_question(room_code):
    state = game_state[room_code]
    
    if (state['current'] < len(state['questions'])):
        q_id = state['questions'][state['current']]
        question = Question.query.get(q_id)
        
        state['question_start_time'] = time.time()
        
        emit('next_question', {
            'id': question.id,
            'text': question.text,
            'choices': json.loads(question.choices),
            'time_limit': state.get('time_limit')
        }, to=room_code)

        print(json.loads(question.choices))
    else:
        emit('game_over', {'final_scores': state['scores']}, to=room_code)

@socketio.on('submit_answer')
def handle_response(data):
    room_code = data.get('room_code')
    choice = data.get('choice')
    q_id = data.get('question_id')
    
    state = game_state[room_code]
    question = Question.query.get(q_id)
    
    if choice == question.correct_answer:
        time_taken = time.time() - state['question_start_time']
        multiplier = max(0, 1 - (time_taken / state.get('time_limit', 15)))
        points = int(1000 * multiplier)
        
        state['scores'][current_user.username] = state['scores'].get(current_user.username, 0) + points