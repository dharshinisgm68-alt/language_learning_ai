LANGUAGE LEARNING AI - SETUP

1. Open this folder in VS Code.
2. Open Terminal.
3. Create virtual environment:
   python -m venv venv

4. Activate:
   Windows:
   venv\Scripts\activate

5. Install packages:
   pip install -r requirements.txt

6. Open .env and replace:
   GEMINI_API_KEY=YOUR_API_KEY_HERE
   with your Gemini API key.

7. Run:
   python app.py

8. Open:
   http://127.0.0.1:5000

FEATURES
- Login / Register
- Language selection
- Beginner / Intermediate / Advanced level
- AI Conversation
- Vocabulary
- Grammar correction
- Translation
- Pronunciation practice
- Browser voice input
- Browser voice output
- AI-generated 5-question MCQ quiz
- Quiz score tracking
- Activity progress tracking
- SQLite database
- Personalized AI responses based on language and level

IMPORTANT
- Never upload .env to GitHub.
- Voice recognition uses the browser Speech Recognition API.
- Pronunciation output uses browser Speech Synthesis.
