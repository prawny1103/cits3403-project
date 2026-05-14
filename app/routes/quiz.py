from flask import Blueprint, render_template, request, jsonify, url_for, redirect, flash
from flask_login import login_required, current_user
import json
from app.extensions import db
from app.models.quiz import Question, Room
import random
import requests

quiz_bp = Blueprint('quiz', __name__)

@quiz_bp.route('/multichoice')
def multichoice():
    question_id = request.args.get('question_id', 1, type=int)
    question = db.session.get(Question, question_id)
    if not question:
        return "Question not found", 404
    
    choices = json.loads(question.choices) if question.choices else {}
    return render_template('multichoice.html', question=question.text, question_id=question.id, choices=choices)

@quiz_bp.route('/get-next-question')
def get_next_question():
    current_id = request.args.get('current_id', 0, type=int)
    next_question = Question.query.filter(Question.id > current_id).first()
    if next_question:
        choices = json.loads(next_question.choices) if next_question.choices else {}
        return jsonify({
            'id': next_question.id,
            'text': next_question.text,
            'choices': choices,
            'has_next': Question.query.filter(Question.id > next_question.id).first() is not None
        })
    else:
        return jsonify({'finished': True})

@quiz_bp.route('/check-answer', methods=['POST'])
def check_answer():
    data = request.get_json()
    q_id = data.get('question_id')
    user_choice = data.get('user_choice')

    question = db.session.get(Question, q_id)
    if not question:
        return jsonify({"error": "Question not found"}), 404

    is_correct = user_choice == question.correct_answer
    return jsonify({
        "is_correct": is_correct
    })

@quiz_bp.route('/create-game', methods=['GET', 'POST'])
@login_required
def create_game():
    question_count = request.form.get('question-count')
    time_limit = request.form.get('time-limit')
    difficulty = request.form.get('difficulty')
    quiz_type = request.form.get('quizType') # Random or Preset
    preset_category = request.form.get('preset-select') # e.g. "Science", "History" (only used if quiz_type is Preset)

    print("Button clicked, creating game...") # Debug log
    code = Room.generate_code()
    if not code:
        return jsonify({"error": "Server is full, please try again later."}), 503
    
    new_room = Room(
        room_code=code, 
        host_id=current_user.id,
        question_count=int(question_count) if question_count else 10,
        time_limit=int(time_limit) if time_limit else 15,
        difficulty=str(difficulty) if difficulty else 'Any',
        quiz_type = quiz_type or 'random',
        preset_category = preset_category if quiz_type == 'preset' else None,
    )
    
    db.session.add(new_room)
    db.session.flush() # Get the ID of the new room before commit

    if quiz_type == "random":
        params = {
            'amount': int(question_count) if question_count else 10,
            'type': 'multiple'
        }
        if difficulty:
            params['difficulty'] = difficulty

        try:
            response = requests.get('https://opentdb.com/api.php', params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['response_code'] != 0:
                raise ValueError(f"OpenTDB response code: {data['response_code']}")
            
            for q in data['results']:
                all_choices = q['incorrect_answers'] + [q['correct_answer']]
                random.shuffle(all_choices)

                labels = ['A', 'B', 'C', 'D'][:len(all_choices)]
                choices_dict = {labels[i]: all_choices[i] for i in range(len(all_choices))}
                correct_label = next(k for k, v in choices_dict.items() if v == q['correct_answer'])

                db.session.add(Question(
                    room_id=new_room.id,
                    category = None,
                    text=q['question'],
                    correct_answer=correct_label,
                    question_type="multiple_choice",
                    choices=json.dumps(choices_dict)
                ))
                
        except (requests.RequestException, ValueError, KeyError) as e:
            print(f"OpenTDB fetch failed: {e}")
            db.session.rollback()
            flash("Could not load questions from external API. Please try again.")
            return redirect(url_for('main.home'))
    
 
    db.session.commit()
  
    return redirect(url_for('quiz.game_room', room_code=code))

@quiz_bp.route('/join-game', methods=['POST'])
@login_required
def join_game():
    code = request.form.get('room_code')

    room = Room.query.filter_by(room_code=code).first()
    if not room:   
        flash("Room not found. Please check the code and try again.")
        return redirect(url_for('main.home'))
    else:
        return redirect(url_for('quiz.game_room', room_code=code))

@quiz_bp.route('/game/<room_code>')
@login_required
def game_room(room_code):
    room = Room.query.filter_by(room_code=room_code).first()
    if not room:
        flash("Room not found.")
        return redirect(url_for('main.index'))
    
    is_host = (room.host_id == current_user.id)
    
    return render_template('game.html', room_code=room_code, is_host=is_host)

@quiz_bp.route('/test')
def test():
    return "Test route is working!"