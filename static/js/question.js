function setQuestion(text, id) {
    document.getElementById("question-text").innerHTML = text;
    document.getElementById("question-text").setAttribute('question-id', id);
}

async function loadNextQuestion(currentId) {
    try {
        const response = await fetch(`/get-next-question?current_id=${currentId}`);
        const data = await response.json();

        if (data.finished) {
            // Quiz finished
            document.getElementById("question-block").innerHTML = "<h2>Quiz Complete!</h2>";
            document.getElementById("answer-multi").style.display = "none";
            return;
        }

        setQuestion(data.text, data.id);
        
        // Update buttons with new choices
        const answerContainer = document.getElementById("answer-multi");
        answerContainer.innerHTML = "";
        
        for (const [key, value] of Object.entries(data.choices)) {
            const button = document.createElement("button");
            button.className = "choice-btn rounded-pill";
            button.setAttribute("ans-choice", key);
            button.textContent = value;
            answerContainer.appendChild(button);
        }
        
        // Reset button styles
        document.querySelectorAll('.choice-btn').forEach(btn => {
            btn.classList.remove('btn-correct', 'btn-incorrect');
        });
    } catch (err) {
        console.log("Error loading next question:", err);
    }
}

const optionsContainer = document.getElementById('answer-multi');

optionsContainer.addEventListener('click', async (event) => {
    // Was what was clicked a button?
    if (!event.target.classList.contains('choice-btn')) return;

    const buttonClicked = event.target;
    const choice = buttonClicked.getAttribute('ans-choice');
    const questionId = document.getElementById('question-text').getAttribute('question-id');

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
        } else {
            buttonClicked.classList.add('btn-incorrect');
        }

        // Load next question after a short delay
        setTimeout(() => {
            loadNextQuestion(questionId);
        }, 1500);

    } catch (err) {
        console.log("error contacting server");
    }
});