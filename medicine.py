from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env file
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins

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
    return send_file("medicine.html")  # Serve medicine.html frontend

@app.route("/get_medicine", methods=["POST"])
def get_medicine():
    try:
        data = request.get_json()
        medicine_name = data.get("medicine", "").strip()

        if not medicine_name:
            return jsonify({"error": "Please provide a medicine name"}), 400

        # Query Gemini
        response = model.generate_content(
    f"Provide detailed medical information about the medicine {medicine_name}. "
    f"Include sections on: Uses, Dosage, Side Effects, Contraindications, and Precautions. "
    f"Write the response in clear plain text paragraphs without any markdown, lists, bullet points, numbering, or special characters. "
    f"Keep it structured with short paragraphs for each section. "
    f"Always end with this exact line: This is general advice. Please consult a doctor or pharmacist before use."
)


        return jsonify({"result": response.text})

    except Exception as e:
        print("[ERROR]", e)
        return jsonify({"error": "Failed to fetch medicine info"}), 500

if __name__ == "__main__":
    app.run(port=8001, debug=True)  # Run on 8001 to avoid conflict with disease.py
