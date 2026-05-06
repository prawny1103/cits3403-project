function setQuestion(text) {
    document.getElementById("question-text").innerHTML = text;
}

const optionsContainer = document.querySelector('.answer-multi');

optionsContainer.addEventListener('click', async (event) => {
    // Was what was clicked a button?
    if (!event.target.classList.contains('choice-btn')) return;

    const buttonClicked = event.target;
    const choice = buttonClicked.getAttribute('ans-choice');
    const questionId = document.getElementById('question-text').getAttribute('question-id')

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
    } catch (err) {
        console.log("error contacting server");
    }
});