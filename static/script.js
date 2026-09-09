```javascript
let currentFeature = "Conversation";
let quizData = [];

const chatbox = document.getElementById("chatbox");
const quizPanel = document.getElementById("quizPanel");
const progressPanel = document.getElementById("progressPanel");
const messageInput = document.getElementById("message");
const language = document.getElementById("language");
const level = document.getElementById("level");


/* =========================
   API FUNCTION
========================= */

async function api(url, body = null) {

    const options = body
        ? {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        }
        : {};

    const response = await fetch(url, options);

    const text = await response.text();

    let data;

    try {
        data = JSON.parse(text);
    }
    catch (error) {

        console.error("Server response:", text);

        throw new Error(
            "Server returned HTML instead of JSON. Check Flask server."
        );
    }

    if (!response.ok) {
        throw new Error(
            data.error || "Request failed"
        );
    }

    return data;
}


/* =========================
   FEATURE
========================= */

function setFeature(feature) {

    currentFeature = feature;

    document.getElementById("feature").innerText =
        feature;

    quizPanel.classList.add("hidden");
    progressPanel.classList.add("hidden");

    addBot(
        feature + " mode selected."
    );
}


/* =========================
   CHAT DISPLAY
========================= */

function addUser(text) {

    const div =
        document.createElement("div");

    div.className = "user";

    div.innerText =
        "👤 " + text;

    chatbox.appendChild(div);

    chatbox.scrollTop =
        chatbox.scrollHeight;
}


function addBot(text) {

    const div =
        document.createElement("div");

    div.className = "bot";

    div.innerText =
        "🤖 " + text;

    chatbox.appendChild(div);

    chatbox.scrollTop =
        chatbox.scrollHeight;
}


/* =========================
   SEND MESSAGE
========================= */

async function sendMessage() {

    const message =
        messageInput.value.trim();

    if (!message) {
        return;
    }

    const selectedLanguage =
        language.value;

    const selectedLevel =
        level.value;

    addUser(message);

    messageInput.value = "";

    addBot("Thinking...");

    try {

        const data = await api(
            "/chat",
            {
                message: message,
                feature: currentFeature,
                language: selectedLanguage,
                level: selectedLevel
            }
        );

        chatbox.lastElementChild.remove();

        addBot(data.answer);

        speak(data.answer);

    }
    catch (error) {

        chatbox.lastElementChild.remove();

        addBot(
            "❌ " + error.message
        );
    }
}


/* =========================
   TEXT TO SPEECH
========================= */

function speak(text) {

    if ("speechSynthesis" in window) {

        const speech =
            new SpeechSynthesisUtterance(text);

        speech.lang = "en-US";

        window.speechSynthesis.cancel();

        window.speechSynthesis.speak(speech);
    }
}


/* =========================
   VOICE INPUT
========================= */

function startVoice() {

    const Recognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;

    if (!Recognition) {

        alert(
            "Voice recognition is not supported. Use Google Chrome."
        );

        return;
    }

    const recognition =
        new Recognition();

    recognition.lang = "en-US";

    recognition.start();

    recognition.onresult =
        function (event) {

            messageInput.value =
                event.results[0][0].transcript;
        };

    recognition.onerror =
        function () {

            alert(
                "Voice recognition failed. Please try again."
            );
        };
}


/* =========================
   SAVE PROFILE
========================= */

function saveProfile() {

    addBot(
        "🎯 Profile selected: " +
        language.value +
        " / " +
        level.value
    );
}


/* =========================
   QUIZ
========================= */

async function loadQuiz() {

    setFeature("Quiz");

    quizPanel.classList.remove("hidden");

    progressPanel.classList.add("hidden");

    quizPanel.innerHTML =
        "<h2>🧠 Quiz</h2>" +
        "<p>Generating 5 questions...</p>";

    try {

        const data = await api(
            "/quiz",
            {
                topic: "Vocabulary and Grammar",
                language: language.value,
                level: level.value
            }
        );

        quizData =
            data.questions;

        renderQuiz();

    }
    catch (error) {

        quizPanel.innerHTML =
            "<p>❌ " +
            error.message +
            "</p>";
    }
}


/* =========================
   RENDER QUIZ
========================= */

function renderQuiz() {

    let html =
        "<h2>🧠 Language Quiz</h2>";

    quizData.forEach(
        function (question, index) {

            html += `
                <div class="quiz-card">

                    <b>
                        ${index + 1}.
                        ${question.question}
                    </b>

                    <br><br>

                    ${question.options
                        .map(
                            function (option, optionIndex) {

                                return `
                                    <label>
                                        <input
                                            type="radio"
                                            name="q${index}"
                                            value="${optionIndex}"
                                        >
                                        ${option}
                                    </label>
                                    <br>
                                `;
                            }
                        )
                        .join("")}

                </div>
            `;
        }
    );

    html += `
        <button onclick="submitQuiz()">
            Submit Quiz
        </button>

        <div id="quizResult"></div>
    `;

    quizPanel.innerHTML =
        html;
}


/* =========================
   SUBMIT QUIZ
========================= */

async function submitQuiz() {

    let score = 0;

    quizData.forEach(
        function (question, index) {

            const selected =
                document.querySelector(
                    `input[name="q${index}"]:checked`
                );

            if (
                selected &&
                Number(selected.value) ===
                Number(question.answer)
            ) {

                score++;
            }
        }
    );

    try {

        await api(
            "/quiz/score",
            {
                score: score,
                total: quizData.length,
                topic: "Vocabulary and Grammar",
                language: language.value,
                level: level.value
            }
        );

        document.getElementById(
            "quizResult"
        ).innerHTML = `
            <div class="score">
                🎯 Score:
                ${score}/${quizData.length}
            </div>
        `;

    }
    catch (error) {

        alert(
            "❌ " + error.message
        );
    }
}


/* =========================
   PROGRESS
========================= */

async function loadProgress() {

    progressPanel.classList.remove(
        "hidden"
    );

    quizPanel.classList.add(
        "hidden"
    );

    try {

        const data =
            await api("/progress");

        let html = `
            <h2>📊 My Progress</h2>

            <h3>Activities</h3>

            <table>

                <tr>
                    <th>Feature</th>
                    <th>Count</th>
                </tr>
        `;

        data.activities.forEach(
            function (item) {

                html += `
                    <tr>
                        <td>${item.feature}</td>
                        <td>${item.n}</td>
                    </tr>
                `;
            }
        );

        html += `
            </table>

            <h3>Quiz Scores</h3>

            <table>

                <tr>
                    <th>Language</th>
                    <th>Level</th>
                    <th>Score</th>
                    <th>Topic</th>
                    <th>Date</th>
                </tr>
        `;

        data.scores.forEach(
            function (item) {

                html += `
                    <tr>
                        <td>${item.language}</td>
                        <td>${item.level}</td>
                        <td>
                            ${item.score}/${item.total}
                        </td>
                        <td>${item.topic}</td>
                        <td>${item.created_at}</td>
                    </tr>
                `;
            }
        );

        html += `
            </table>

            <h3>Vocabulary</h3>

            <table>

                <tr>
                    <th>Language</th>
                    <th>Word</th>
                    <th>Meaning</th>
                    <th>Example</th>
                </tr>
        `;

        data.vocabulary.forEach(
            function (item) {

                html += `
                    <tr>
                        <td>${item.language}</td>
                        <td>${item.word}</td>
                        <td>${item.meaning}</td>
                        <td>${item.example}</td>
                    </tr>
                `;
            }
        );

        html += "</table>";

        progressPanel.innerHTML =
            html;

    }
    catch (error) {

        progressPanel.innerHTML =
            "<p>❌ " +
            error.message +
            "</p>";
    }
}


/* =========================
   ENTER KEY
========================= */

messageInput.addEventListener(
    "keydown",
    function (event) {

        if (event.key === "Enter") {

            sendMessage();
        }
    }
);
```
