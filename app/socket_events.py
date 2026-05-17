import time
import json
import threading
from app import socketio
from app.extensions import db
from app.models.quiz import Room, Question, Game, PlayerStats
from app.models.user import User
from flask_socketio import join_room, emit
from flask_login import current_user
from flask import current_app
import random
from datetime import datetime

_app = None

def init_app(app):
    global _app
    _app = app

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
    
    if room.quiz_id:
        questions = Question.query.filter_by(quiz_id=room.quiz_id).all()
        
    else:
        questions = Question.query.filter_by(room_id=room.id).all()

    if not questions:
        emit('error', {'message': 'No questions available for this quiz.'}, to=room_code)
        return
    
    game_state[room_code] = {
        'questions': [q.id for q in questions],
        'time_limit': room.time_limit,
        'current': 0,
        'scores': {player: 0 for player in active_players.get(room_code, [])}, # initialize scores for all players in the room
        'answered': {},
        'question_start_time': 0,
        'advance_timer': None,
    }

    # Notify clients in the room that the game is starting (redirect to quiz page)
    emit('game_starting', to=room_code)

    # small delay for animation


def send_next_question(room_code):
    with _app.app_context():
        state = game_state.get(room_code)
        if not state:
            return
        
        if (state['current'] < len(state['questions'])):
            q_id = state['questions'][state['current']]
            question = db.session.get(Question, q_id)
            
            state['question_start_time'] = time.time()
            state['answered'] = {} # reset answered status for new question
            
            socketio.emit('next_question', {
                'id': question.id,
                'text': question.text,
                'choices': json.loads(question.choices),
                'time_limit': state.get('time_limit'),
                'question_number': state['current'] + 1,
                'total_questions': len(state['questions']),
            }, to=room_code)

            # Auto advance when time runs out (extra second for latency)
            t = threading.Timer(state['time_limit'] + 1, auto_advance, args=[room_code, state['current']])
            t.daemon = True
            t.start()
            state['advance_timer'] = t

        else:
            room = Room.query.filter_by(room_code=room_code, is_active=True).first()
            if room:
                room.is_active=False

            game = Game(
                room_id = room.id,
                ended_at = datetime.utcnow()
            )
            db.session.add(game)
            db.session.flush()

            for username, score in state['scores'].items():
                user=User.query.filter_by(username=username).first()
                if user:
                    db.session.add(PlayerStats(
                        game_id=game.id,
                        user_id=user.id,
                        score=score,
                        correct_answers=None
                    ))
            
            # Delete questions that were received from the api and are tied to this room code
            Question.query.filter_by(room_id=room.id).delete()

            db.session.commit()

            socketio.emit('game_over', {'final_scores': state['scores']}, to=room_code)
            game_state.pop(room_code, None)

# Auto advance if time runs out
def auto_advance(room_code, question_index):
    # Move to the next question if we're still on the same question
    with _app.app_context():
        state = game_state.get(room_code)
        if not state:
            return
        if state['current'] != question_index:
            return # Question was already advanced, do nothing
        
        # Show scores than advance
        socketio.emit('show_scores', {'scores': state['scores']}, to=room_code)
        state['current'] += 1

        t = threading.Timer(3.0, send_next_question, args=[room_code])
        t.daemon = True
        t.start()
        state['advance_timer'] = t

@socketio.on('submit_answer')
def handle_response(data):
    room_code = data.get('room_code')
    choice = data.get('choice')
    q_id = data.get('question_id')
    
    state = game_state.get(room_code)
    if not state:
        return
    # Prevent double answering
    if current_user.username in state['answered']:
        return
    state['answered'][current_user.username] = True

    question = db.session.get(Question, q_id)
    is_correct = (choice == question.correct_answer)
    points = 0

    if is_correct:
        time_taken = time.time() - state['question_start_time']
        multiplier = max(0, 1-(time_taken / state['time_limit'])) # Faster answers get more points
        points = int(1000 * multiplier)
        state['scores'][current_user.username] = state['scores'].get(current_user.username, 0) + points

    # Tell player result
    emit('answer_result', {
        'correct': is_correct,
        'correct_answer': question.correct_answer,
        'points_earned': points,
        'scores': state['scores'],
    })

    players_in_room = active_players.get(room_code, [])
    if len(state['answered']) == len(players_in_room):
        # All players have answered, move to next question immediately
        if state.get('advance_timer'):
            state['advance_timer'].cancel() # Cancel the auto-advance timer
        
        # Show scores than advance

        state['current'] += 1

        def advance():
            with _app.app_context():
                socketio.emit('show_scores', {'scores': state['scores']}, to=room_code)
                t = threading.Timer(3.0, send_next_question, args=[room_code])
                t.daemon = True
                t.start()
                state['advance_timer'] = t

        t = threading.Timer(2.0, advance)
        t.daemon = True
        t.start()


@socketio.on('request_question')
def handle_request_question(data):
    room_code = data.get('room_code')
    send_next_question(room_code)

@socketio.on('disconnect')
def handle_disconnect():
    for room_code, players in active_players.items():
        if current_user.username in players:
            players.remove(current_user.username)
            emit('update_players', {'players': players}, to=room_code)
            break