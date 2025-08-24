from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)  # <-- allows requests from other origins like your 5500 port

GEMINI_API_KEY = "AIzaSyAi4MVkyGRWw8SgUolH9Mn-XXRojDXVOiM"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}"

def compare_medicines(med1, med2):
    prompt = f"""
    Compare these two medicines:
    1. {med1} (prescribed)
    2. {med2} (available)

    Return ONLY JSON in this format:
    {{
      "confidence": 85,
      "side_effects": ["Nausea", "Headache", "Drowsiness"],
      "symptoms_treated": ["Fever", "Mild Pain"],
      "verdict": "Yes, it can be used as a substitute with caution."
    }}
    """
    headers = {"Content-Type": "application/json"}
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        resp = requests.post(GEMINI_URL, headers=headers, json=data)
        result = resp.json()
        raw_text = result["candidates"][0]["content"]["parts"][0]["text"]
        raw_text = raw_text.strip().strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:].strip()
        return json.loads(raw_text)
    except Exception as e:
        return {"error": f"Parsing failed: {e}", "raw_response": result if 'result' in locals() else None}

@app.route("/api/compare", methods=["POST"])
def api_compare():
    data = request.get_json()
    med1 = data.get("med1", "").strip()
    med2 = data.get("med2", "").strip()

    if not med1 or not med2:
        return jsonify({"error": "Both medicine fields are required."}), 400

    result = compare_medicines(med1, med2)
    return jsonify(result)

if __name__ == "__main__":
    app.run(port=8020, debug=True)
