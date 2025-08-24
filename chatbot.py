from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Load Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in .env")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Choose a Gemini model
model = genai.GenerativeModel("gemini-2.5-flash")

# System prompt for medical chatbot
MEDICAL_PROMPT = """
You are unoBOT, a medical support chatbot. Mention yourself as unoBOT

Rules:
1. Answer only medical or health-related queries (diseases, symptoms, medicines, treatments, precautions, first aid, diet, wellness).
2. If the question is not medical, reply politely: "I can only answer medical and health-related questions."
3. Format answers in a simple, step-by-step or numbered list. Avoid complex sentences.
4. Keep answers clear, short, and easy to read for elderly users.
5. Use Bullet points and numbering properly. Para Change Wherever needed.
5. Do not use stars, markdown, or decorative symbols.
6. Always include a caution line: "This is general advice. Please consult a doctor for personal medical concerns.
7. Dont use ** anywhere."
"""

def query_gemini(message: str) -> str:
    try:
        response = model.generate_content(f"{MEDICAL_PROMPT}\n\nUser: {message}\n\nChatbot:")
        return response.text.strip()
    except Exception as e:
        print("[ERROR] Gemini request failed:", e)
        return "Sorry, there was a problem talking to the AI."

@app.route("/")
def home():
    return jsonify({"message": "✅ UNOMEDS Medical Chatbot is running."})

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message", "").strip()
    if not user_input:
        return jsonify({"reply": "Please enter a message."}), 400

    reply = query_gemini(user_input)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(port=8000, debug=True)
