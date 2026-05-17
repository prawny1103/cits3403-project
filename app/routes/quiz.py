from flask import Blueprint, render_template, request, jsonify, url_for, redirect, flash
from flask_login import login_required, current_user
import json
from app.extensions import db
from app.models.quiz import Quiz, Question, Room
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

# Blueprint for creating a game room
@quiz_bp.route('/create-game', methods=['GET', 'POST'])
@login_required
def create_game():
    # Get parameters from the form
    question_count = request.form.get('question-count')
    time_limit = request.form.get('time-limit')
    difficulty = request.form.get('difficulty')
    quiz_type = request.form.get('quizType') 
    preset_quiz_id = request.form.get('preset-quiz-id')

    # Generate unused room code
    code = Room.generate_code()
    if not code:
        return jsonify({"error": "Server is full, please try again later."}), 503
    
    # Add room to the database
    new_room = Room(
        room_code=code, 
        host_id=current_user.id,
        question_count=int(question_count) if question_count else 10,
        time_limit=int(time_limit) if time_limit else 15,
        difficulty=str(difficulty) if difficulty else 'Any',
        quiz_type=quiz_type or 'random',
        quiz_id=int(preset_quiz_id) if quiz_type == 'preset' and preset_quiz_id else None,
    )
    
    db.session.add(new_room)
    db.session.flush() # Get the ID of the new room before commit

    # If the quiz is random type:
    if quiz_type == "random":
        # Get the information we will send with the api request
        params = {
            'amount': int(question_count) if question_count else 10,
            'type': 'multiple'
        }
        if difficulty and difficulty != "any":
            params['difficulty'] = difficulty

        try:
            # Send api request to opentdb
            response = requests.get('https://opentdb.com/api.php', params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # If opentdb sends back an error:
            if data['response_code'] != 0:
                raise ValueError(f"OpenTDB response code: {data['response_code']}")
            
            # Iterate through the questions sent by the api and store them in db
            for q in data['results']:
                all_choices = q['incorrect_answers'] + [q['correct_answer']]
                random.shuffle(all_choices)

                labels = ['A', 'B', 'C', 'D'][:len(all_choices)]
                choices_dict = {labels[i]: all_choices[i] for i in range(len(all_choices))}
                # Find the label that corresponds to the correct answer
                correct_label = next(k for k, v in choices_dict.items() if v == q['correct_answer'])

                # Add to db
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
  
    # Redirect to the game room with the room code
    return redirect(url_for('quiz.game_room', room_code=code))

# Join game using the room code from the joinRoom page
@quiz_bp.route('/join-game', methods=['POST'])
@login_required
def join_game():
    # Get the room code from the form
    code = request.form.get('room_code')

    # Check to see if room code corresponds to a currently active room
    room = Room.query.filter_by(room_code=code, is_active=True).first()
    if not room:   
        return render_template('joinRoom.html', error="Room not found. Please check the code and try again.")
    else:
        # Redirect to the game room if the room code is valid
        return redirect(url_for('quiz.game_room', room_code=code))

# The url for a game. A user is sent here when they input a valid room code
@quiz_bp.route('/game/<room_code>')
@login_required
def game_room(room_code):
    # Fetch room from the database
    room = Room.query.filter_by(room_code=room_code, is_active=True).first()
    if not room:
        flash("Room not found.")
        return redirect(url_for('main.index'))
    
    # Is the user the same user who created the room?
    is_host = (room.host_id == current_user.id)
    
    # Render the template with some arguments. If the user is the host then they have the ability to start the game. Room code is displayed on the page.
    return render_template('game.html', room_code=room_code, is_host=is_host)

# Page that displays all the user's quizzes that they created
@quiz_bp.route('/my-quizzes')
@login_required
def my_quizzes():
    # Get all the quizzes from the db
    user_quizzes = Quiz.query.filter_by(creator_id=current_user.id).all()
    public_quizzes = Quiz.query.filter_by(is_published=True).filter(Quiz.creator_id != current_user.id).all()

    # Render the page template with the quizzes we just fetched
    return render_template('myQuizzes.html', user_quizzes=user_quizzes, public_quizzes=public_quizzes)

# Page for creating a new quiz
@quiz_bp.route('/quiz/new', methods=['GET', 'POST'])
@login_required
def create_quiz():
    # Get the form from the client
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        
        # Add quiz to the database
        new_quiz = Quiz(title=title, description=description, creator_id=current_user.id)
        db.session.add(new_quiz)
        db.session.commit()
        
        # Redirect to the page where you can add questions to the quiz.
        flash("Quiz created! Now add some questions.")
        return redirect(url_for('quiz.edit_quiz', quiz_id=new_quiz.id))
    
    return render_template('editQuiz.html', quiz=None)

# Page for editing a quiz (adding questions)
@quiz_bp.route('/quiz/<int:quiz_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_quiz(quiz_id):
    # Fetch the quiz from the db
    quiz = db.session.get(Quiz, quiz_id)
    # Check if the quiz exists and the current is the creator
    if not quiz or quiz.creator_id != current_user.id:
        flash("Unauthorized or Quiz not found.")
        return redirect(url_for('quiz.my_quizzes'))

    # Get the form from the client
    if request.method == 'POST':
        # The question text (aka the actual question being asked)
        question_text = request.form.get('question_text')
        # The correct answer for the question
        correct_answer = request.form.get('correct_answer')

        # Will include 1 correct answer and 3 incorrect answers
        choices = {
            'A': request.form.get('choice_a'),
            'B': request.form.get('choice_b'),
            'C': request.form.get('choice_c'),
            'D': request.form.get('choice_d')
        }
        
        # Add the question to the database and relate it to its corresponding quiz
        new_q = Question(
            quiz_id=quiz.id,
            text=question_text,
            correct_answer=correct_answer,
            choices=json.dumps(choices)
        )
        db.session.add(new_q)
        db.session.commit()
        flash("Question added!")

    return render_template('editQuiz.html', quiz=quiz)

# Set the quiz to be published. It can now be used in games
@quiz_bp.route('/quiz/<int:quiz_id>/publish', methods=['POST'])
@login_required
def publish_quiz(quiz_id):
    quiz = db.session.get(Quiz, quiz_id)
    # If the quiz exists and the current user is the creator:
    if quiz and quiz.creator_id == current_user.id:
        # Set it to published = True
        quiz.is_published = True
        db.session.commit()
        flash("Quiz published successfully!")
        
    return redirect(url_for('quiz.my_quizzes'))