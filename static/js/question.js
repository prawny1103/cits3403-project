function decodeHtml(str) {
    // This is required to prevent formatting issues with special characters in questions/choices
    const textarea = document.createElement('textarea');
    textarea.innerHTML = str;
    return textarea.value;
}

function setQuestion(text, id) {
    document.getElementById("question-text").textContent = decodeHtml(text);
    document.getElementById("question-text").setAttribute('question-id', id);
}

let correctCount = 0;
let totalQuestions = 1;

function updateScore() {
    document.getElementById("score-display").textContent = `Score: ${correctCount} / ${totalQuestions}`;
}

// Initialize score display
updateScore();

async function loadNextQuestion(currentId) {
    try {
        const response = await fetch(`/get-next-question?current_id=${currentId}`);
        const data = await response.json();

        if (data.finished) {
            // Quiz finished
            document.getElementById("question-block").innerHTML = `<h2>Quiz Complete!</h2><p>Final Score: ${correctCount} / ${totalQuestions}</p>`;
            document.getElementById("answer-multi").style.display = "none";
            document.getElementById("score-display").style.display = "none";
            return;
        }

        totalQuestions++;
        updateScore();

        setQuestion(data.text, data.id);
        
        // Update buttons with new choices
        const answerContainer = document.getElementById("answer-multi");
        answerContainer.innerHTML = "";
        
        for (const [key, value] of Object.entries(data.choices)) {
            const button = document.createElement("button");
            button.className = "choice-btn rounded-pill";
            button.setAttribute("ans-choice", key);
            button.textContent = decodeHtml(value);
            answerContainer.appendChild(button);
        }
        
        // Reset button styles and enable
        document.querySelectorAll('.choice-btn').forEach(btn => {
            btn.classList.remove('btn-correct', 'btn-incorrect');
            btn.disabled = false;
        });
    } catch (err) {
        console.log("Error loading next question:", err);
    }
}

const optionsContainer = document.getElementById('answer-multi');

optionsContainer.addEventListener('click', async (event) => {
    // Was what was clicked a button?
    if (!event.target.classList.contains('choice-btn')) return;

    // Prevent multiple selections
    if (document.querySelector('.choice-btn:disabled')) return;

    const buttonClicked = event.target;
    const choice = buttonClicked.getAttribute('ans-choice');
    const questionId = document.getElementById('question-text').getAttribute('question-id');

    // Disable all buttons
    document.querySelectorAll('.choice-btn').forEach(btn => btn.disabled = true);

    try {
        // POST the choice
        const response = await fetch('/check-answer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_id: questionId,
                user_choice: choice
            })
        });

        const data = await response.json();

        if (data.is_correct) {
            buttonClicked.classList.add('btn-correct');
            correctCount++;
        } else {
            buttonClicked.classList.add('btn-incorrect');
        }

        updateScore();

        // Load next question after a short delay
        setTimeout(() => {
            loadNextQuestion(questionId);
        }, 1500);

    } catch (err) {
        console.log("error contacting server");
        // Re-enable buttons on error
        document.querySelectorAll('.choice-btn').forEach(btn => btn.disabled = false);
    }
});