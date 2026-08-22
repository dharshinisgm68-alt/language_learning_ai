from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from google import genai
import sqlite3, os, random

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret-key")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-2.5-flash"
DB = "language_learning.db"

LANGUAGES = ["English", "Tamil", "Hindi", "Malayalam", "Telugu", "Kannada"]
LEVELS = ["Beginner", "Intermediate", "Advanced"]

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        language TEXT DEFAULT 'English',
        level TEXT DEFAULT 'Beginner'
    );
    CREATE TABLE IF NOT EXISTS vocabulary(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        word TEXT,
        meaning TEXT,
        example TEXT,
        learned INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS quiz_scores(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        score INTEGER,
        total INTEGER,
        topic TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS activities(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        feature TEXT,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    con.commit()
    con.close()

def current_user():
    return session.get("user_id")

@app.route("/")
def index():
    return render_template("index.html", user=session.get("username"))

@app.post("/register")
def register():
    data = request.json
    username = data.get("username","").strip()
    password = data.get("password","")
    if not username or not password:
        return jsonify(error="Username and password are required."), 400
    con = db()
    try:
        cur = con.execute(
            "INSERT INTO users(username,password) VALUES(?,?)",
            (username, generate_password_hash(password))
        )
        con.commit()
        session["user_id"] = cur.lastrowid
        session["username"] = username
        return jsonify(ok=True)
    except sqlite3.IntegrityError:
        return jsonify(error="Username already exists."), 409
    finally:
        con.close()

@app.post("/login")
def login():
    data = request.json
    con = db()
    user = con.execute("SELECT * FROM users WHERE username=?", (data.get("username",""),)).fetchone()
    con.close()
    if not user or not check_password_hash(user["password"], data.get("password","")):
        return jsonify(error="Invalid username or password."), 401
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    return jsonify(ok=True)

@app.post("/logout")
def logout():
    session.clear()
    return jsonify(ok=True)

@app.get("/me")
def me():
    if not current_user():
        return jsonify(logged_in=False)
    con = db()
    user = con.execute("SELECT id,username,language,level FROM users WHERE id=?", (current_user(),)).fetchone()
    con.close()
    return jsonify(logged_in=True, **dict(user))

@app.post("/profile")
def profile():
    if not current_user(): return jsonify(error="Login required."), 401
    data = request.json
    language = data.get("language","English")
    level = data.get("level","Beginner")
    if language not in LANGUAGES or level not in LEVELS:
        return jsonify(error="Invalid language or level."), 400
    con = db()
    con.execute("UPDATE users SET language=?, level=? WHERE id=?", (language, level, current_user()))
    con.commit(); con.close()
    return jsonify(ok=True)

def ask_ai(prompt):
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text

@app.post("/chat")
def chat():
    if not current_user(): return jsonify(error="Please login first."), 401
    data = request.json
    message = data.get("message","")
    feature = data.get("feature","Conversation")
    con = db()
    user = con.execute("SELECT language,level FROM users WHERE id=?", (current_user(),)).fetchone()
    con.close()
    prompt = f"""You are a professional AI Language Learning Assistant.
Target language: {user['language']}
Student level: {user['level']}
Feature: {feature}
Student message: {message}

Give a helpful, student-friendly response.
For Grammar: show corrected sentence and short explanation.
For Vocabulary: give word, meaning, pronunciation and example.
For Translation: translate naturally and explain difficult words.
For Conversation: continue the conversation and gently correct important mistakes.
For Pronunciation: provide simple pronunciation guidance.
For Lesson: create a lesson suitable for the student's level.
Do not claim that audio was generated; the browser handles speech output."""
    try:
        answer = ask_ai(prompt)
        con = db()
        con.execute("INSERT INTO activities(user_id,feature,details) VALUES(?,?,?)",
                    (current_user(), feature, message))
        con.commit(); con.close()
        return jsonify(answer=answer)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.post("/quiz")
def quiz():
    if not current_user(): return jsonify(error="Please login first."), 401
    data = request.json
    topic = data.get("topic","Vocabulary")
    con = db()
    user = con.execute("SELECT language,level FROM users WHERE id=?", (current_user(),)).fetchone()
    con.close()
    prompt = f"""Create exactly 5 multiple-choice questions for a language learner.
Target language: {user['language']}; Level: {user['level']}; Topic: {topic}.
Return ONLY valid JSON array. Each item must have:
question, options (array of 4 strings), answer (0-3), explanation."""
    try:
        text = ask_ai(prompt).strip()
        if text.startswith("```"):
            text = text.replace("```json","").replace("```","").strip()
        import json
        questions = json.loads(text)
        return jsonify(questions=questions)
    except Exception as e:
        return jsonify(error="Quiz generation failed: " + str(e)), 500

@app.post("/quiz/score")
def quiz_score():
    if not current_user(): return jsonify(error="Login required."), 401
    data = request.json
    score, total, topic = int(data["score"]), int(data["total"]), data.get("topic","Quiz")
    con = db()
    con.execute("INSERT INTO quiz_scores(user_id,score,total,topic) VALUES(?,?,?,?)",
                (current_user(),score,total,topic))
    con.commit(); con.close()
    return jsonify(ok=True)

@app.post("/vocabulary")
def vocabulary():
    if not current_user(): return jsonify(error="Login required."), 401
    data = request.json
    con = db()
    con.execute("INSERT INTO vocabulary(user_id,word,meaning,example) VALUES(?,?,?,?)",
                (current_user(), data["word"], data["meaning"], data.get("example","")))
    con.commit(); con.close()
    return jsonify(ok=True)

@app.get("/progress")
def progress():
    if not current_user(): return jsonify(error="Login required."), 401
    con = db()
    uid = current_user()
    activities = con.execute("SELECT feature,COUNT(*) n FROM activities WHERE user_id=? GROUP BY feature",(uid,)).fetchall()
    scores = con.execute("SELECT score,total,topic,created_at FROM quiz_scores WHERE user_id=? ORDER BY id DESC LIMIT 10",(uid,)).fetchall()
    words = con.execute("SELECT word,meaning,example,learned FROM vocabulary WHERE user_id=? ORDER BY id DESC LIMIT 20",(uid,)).fetchall()
    con.close()
    return jsonify(activities=[dict(x) for x in activities],
                   scores=[dict(x) for x in scores],
                   vocabulary=[dict(x) for x in words])

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
