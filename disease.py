from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Allow frontend fetch calls

# Load Gemini API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in .env")

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Choose Gemini model
model = genai.GenerativeModel("gemini-2.5-flash")

@app.route("/")
def serve_html():
    return send_file("disease.html")

@app.route("/get_disease", methods=["POST"])
def get_disease():
    try:
        data = request.get_json()
        disease_name = data.get("disease", "").strip()

        if not disease_name:
            return jsonify({"error": "Please provide a disease name"}), 400

        # Query Gemini
        response = model.generate_content(
    f"Provide detailed medical information about {disease_name}. "
    f"Include sections on: Causes, Symptoms, Diagnosis, and Treatments. "
    f"Write in plain text only, without markdown, lists, bullet points, numbering, or special characters. "
    f"Use clear short paragraphs under each section label (e.g., 'Causes:', 'Symptoms:'). "
    f"Always end with this exact line: This is general advice. Please consult a doctor for personal concerns."
)


        return jsonify({"result": response.text})

    except Exception as e:
        print("[ERROR]", e)
        return jsonify({"error": "Failed to fetch disease info"}), 500

if __name__ == "__main__":
    app.run(port=8000, debug=True)
