````python
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from google import genai
import sqlite3
import os
import json

load_dotenv()

app = Flask(__name__)

# Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-2.5-flash"

# Database
DB = "language_learning.db"

LANGUAGES = [
    "English",
    "Tamil",
    "Hindi",
    "Malayalam",
    "Telugu",
    "Kannada"
]

LEVELS = [
    "Beginner",
    "Intermediate",
    "Advanced"
]


# ---------------- DATABASE ----------------

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def init_db():
    con = db()

    con.executescript("""
        CREATE TABLE IF NOT EXISTS activities(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT,
            level TEXT,
            feature TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS quiz_scores(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT,
            level TEXT,
            score INTEGER,
            total INTEGER,
            topic TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS vocabulary(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            language TEXT,
            level TEXT,
            word TEXT,
            meaning TEXT,
            example TEXT,
            learned INTEGER DEFAULT 0
        );
    """)

    con.commit()
    con.close()


# ---------------- HOME ----------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------- GEMINI AI ----------------

def ask_ai(prompt):
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    return response.text


# ---------------- CHAT ----------------

@app.post("/chat")
def chat():

    data = request.get_json() or {}

    message = data.get("message", "").strip()
    feature = data.get("feature", "Conversation")
    language = data.get("language", "English")
    level = data.get("level", "Beginner")

    if not message:
        return jsonify(
            error="Please enter a message."
        ), 400

    if language not in LANGUAGES:
        return jsonify(
            error="Invalid language."
        ), 400

    if level not in LEVELS:
        return jsonify(
            error="Invalid level."
        ), 400

    prompt = f"""
You are a professional AI Language Learning Assistant.

Target language: {language}

Student level: {level}

Feature: {feature}

Student message:
{message}

Give a helpful and student-friendly response.

For Grammar:
Correct the sentence and explain the mistake briefly.

For Vocabulary:
Give the word, meaning, pronunciation and example.

For Translation:
Translate naturally and explain difficult words.

For Conversation:
Continue the conversation and gently correct important mistakes.

For Pronunciation:
Give simple pronunciation guidance.

For Lesson:
Create a lesson suitable for the student's level.

Do not claim that audio was generated.
The browser handles speech output.
"""

    try:

        answer = ask_ai(prompt)

        con = db()

        con.execute(
            """
            INSERT INTO activities
            (language, level, feature, details)
            VALUES (?, ?, ?, ?)
            """,
            (
                language,
                level,
                feature,
                message
            )
        )

        con.commit()
        con.close()

        return jsonify(
            answer=answer
        )

    except Exception as e:

        print("CHAT ERROR:", e)

        return jsonify(
            error="AI request failed: " + str(e)
        ), 500


# ---------------- QUIZ ----------------

@app.post("/quiz")
def quiz():

    data = request.get_json() or {}

    topic = data.get(
        "topic",
        "Vocabulary and Grammar"
    )

    language = data.get(
        "language",
        "English"
    )

    level = data.get(
        "level",
        "Beginner"
    )

    prompt = f"""
Create exactly 5 multiple-choice questions
for a language learner.

Target language: {language}

Student level: {level}

Topic: {topic}

Return ONLY valid JSON.

Format:

[
  {{
    "question": "Question",
    "options": [
      "Option 1",
      "Option 2",
      "Option 3",
      "Option 4"
    ],
    "answer": 0,
    "explanation": "Short explanation"
  }}
]

answer must be a number from 0 to 3.
"""

    try:

        text = ask_ai(prompt).strip()

        # Remove markdown JSON code block if Gemini adds it
        if text.startswith("```"):
            text = (
                text
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

        questions = json.loads(text)

        return jsonify(
            questions=questions
        )

    except Exception as e:

        print("QUIZ ERROR:", e)

        return jsonify(
            error="Quiz generation failed: " + str(e)
        ), 500


# ---------------- QUIZ SCORE ----------------

@app.post("/quiz/score")
def quiz_score():

    data = request.get_json() or {}

    score = int(
        data.get("score", 0)
    )

    total = int(
        data.get("total", 0)
    )

    topic = data.get(
        "topic",
        "Vocabulary and Grammar"
    )

    language = data.get(
        "language",
        "English"
    )

    level = data.get(
        "level",
        "Beginner"
    )

    con = db()

    con.execute(
        """
        INSERT INTO quiz_scores
        (language, level, score, total, topic)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            language,
            level,
            score,
            total,
            topic
        )
    )

    con.commit()
    con.close()

    return jsonify(
        ok=True
    )


# ---------------- VOCABULARY ----------------

@app.post("/vocabulary")
def vocabulary():

    data = request.get_json() or {}

    language = data.get(
        "language",
        "English"
    )

    level = data.get(
        "level",
        "Beginner"
    )

    word = data.get(
        "word",
        ""
    )

    meaning = data.get(
        "meaning",
        ""
    )

    example = data.get(
        "example",
        ""
    )

    if not word or not meaning:

        return jsonify(
            error="Word and meaning are required."
        ), 400

    con = db()

    con.execute(
        """
        INSERT INTO vocabulary
        (language, level, word, meaning, example)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            language,
            level,
            word,
            meaning,
            example
        )
    )

    con.commit()
    con.close()

    return jsonify(
        ok=True
    )


# ---------------- PROGRESS ----------------

@app.get("/progress")
def progress():

    con = db()

    activities = con.execute(
        """
        SELECT feature,
               COUNT(*) AS n
        FROM activities
        GROUP BY feature
        ORDER BY n DESC
        """
    ).fetchall()

    scores = con.execute(
        """
        SELECT language,
               level,
               score,
               total,
               topic,
               created_at
        FROM quiz_scores
        ORDER BY id DESC
        LIMIT 10
        """
    ).fetchall()

    words = con.execute(
        """
        SELECT language,
               level,
               word,
               meaning,
               example,
               learned
        FROM vocabulary
        ORDER BY id DESC
        LIMIT 20
        """
    ).fetchall()

    con.close()

    return jsonify(
        activities=[
            dict(x)
            for x in activities
        ],

        scores=[
            dict(x)
            for x in scores
        ],

        vocabulary=[
            dict(x)
            for x in words
        ]
    )


# ---------------- RUN APP ----------------

if __name__ == "__main__":

    init_db()

    app.run(
        debug=True
    )
````
