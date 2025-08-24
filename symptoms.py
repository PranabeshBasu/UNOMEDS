from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os, json, re
from dotenv import load_dotenv
import google.generativeai as genai

# Load env and configure Flask
load_dotenv()
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing in .env")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# --- Utilities ---
def extract_json(text: str):
    """Best-effort: pull first {...} JSON block from model text and parse."""
    # direct attempt
    try:
        return json.loads(text)
    except Exception:
        pass
    # strip code fences
    if "```" in text:
        text = re.sub(r"```(?:json)?", "", text).strip("` \n")
    # find JSON object
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    raise ValueError("Could not parse JSON from model output.")

def normalize_percentages(items, key="probability"):
    """Normalize probabilities to sum ~100; clamp to [0,100]."""
    vals = [max(0.0, float(x.get(key, 0))) for x in items]
    total = sum(vals)
    if total <= 0:
        # Assign equal split if model gave zeros
        n = len(items)
        for i in range(n):
            items[i][key] = round(100.0 / n, 1)
        return items
    for i, v in enumerate(vals):
        items[i][key] = round((v / total) * 100.0, 1)
    return items

# --- Prompt builder ---
ANALYSIS_INSTRUCTIONS = """
You are unoBOT, a cautious medical support chatbot. The user will provide free-text symptoms.
Your task:
1) Infer the top 3–6 most likely medical conditions (differential diagnosis) that could explain the symptoms.
2) For each condition, include:
   - condition: short name
   - probability: a number 0–100 (rough estimate; total does not need to sum to 100 exactly)
   - rationale: one or two brief plain-text sentences linking symptoms to the condition
   - severity: "low", "moderate", or "high" (clinical urgency)
3) If there are any immediate red flags in the text that warrant urgent care, add a list under "red_flags" (may be empty).
4) Output STRICT JSON ONLY with this exact schema:
{
  "conditions": [
    { "condition": "...", "probability": 0-100, "rationale": "...", "severity": "low|moderate|high" }
  ],
  "red_flags": ["...", "..."],
  "disclaimer": "This is general advice. Please consult a doctor for personal medical concerns."
}
Rules:
- Plain text only inside the fields. No markdown, no bullets, no hashes, no asterisks.
- Be concise, readable, and non-alarming, but accurate.
"""

@app.route("/")
def serve_html():
    return send_file("symptoms.html")

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(force=True) or {}
    symptoms_text = (data.get("message") or "").strip()
    if not symptoms_text:
        return jsonify({"error": "Please describe your symptoms."}), 400

    prompt = (
        ANALYSIS_INSTRUCTIONS
        + "\nUser symptoms: "
        + symptoms_text
        + "\nReturn JSON only."
    )

    try:
        resp = model.generate_content(prompt)
        raw = resp.text.strip()
        parsed = extract_json(raw)

        # normalize probabilities and clamp fields a bit
        if isinstance(parsed.get("conditions"), list) and parsed["conditions"]:
            parsed["conditions"] = normalize_percentages(parsed["conditions"], "probability")

        # enforce disclaimer line
        parsed["disclaimer"] = "This is general advice. Please consult a doctor for personal medical concerns."

        return jsonify(parsed)
    except Exception as e:
        # Basic safe fallback
        print("[ERROR]", e)
        return jsonify({
            "conditions": [],
            "red_flags": [],
            "disclaimer": "This is general advice. Please consult a doctor for personal medical concerns.",
            "error": "Sorry, we could not analyze your symptoms right now."
        }), 500

if __name__ == "__main__":
    # Use a distinct port so it doesn't clash with your other apps
    app.run(port=8010, debug=True)
