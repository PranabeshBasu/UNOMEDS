from flask import Flask, request, jsonify, render_template
import os
import io
from PyPDF2 import PdfReader
import google.generativeai as genai
from flask_cors import CORS
from dotenv import load_dotenv   # <-- NEW

# Load environment variables from .env file
load_dotenv()


app = Flask(__name__)
CORS(app)

# Read key from .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print("Loaded GEMINI_API_KEY:", GEMINI_API_KEY[:8] if GEMINI_API_KEY else "❌ Not Found")


# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")



@app.route('/')
def index():
    return render_template('pdfupload.html')


@app.route('/pdfupload/', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"detail": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"detail": "No file selected"}), 400

    if not file.filename.endswith('.pdf'):
        return jsonify({"detail": "Only PDF files are allowed"}), 400

    try:
        pdf_bytes = file.read()
        reader = PdfReader(io.BytesIO(pdf_bytes))
        extracted_text = " ".join([page.extract_text() or "" for page in reader.pages])

        if not extracted_text.strip():
            return jsonify({"detail": "No readable text found in PDF"}), 400

        prompt = f"""
You are a medical expert tasked with analyzing a medical document, such as test results or a health report. Your goal is to provide a concise and professional summary that extracts key information, identifies potential diseases, and offers recommendations for prevention, treatment, diet, and exercise. Follow these instructions precisely:

1. Summarize the key findings from the provided medical document content in 2-3 short paragraphs. Focus on critical data such as test results, diagnoses, or symptoms mentioned.
2. Identify possible diseases or conditions based on the data, listing them in bullet points if multiple conditions are relevant. Provide a brief explanation for each.
3. Provide recommendations in the following categories, using bullet points for clarity:
   - Prevention: Practical steps to reduce risk or progression of identified conditions.
   - Treatment: Suggested medical interventions, including potential medications (generic names preferred, with dosages if applicable).
   - Diet: Specific dietary advice to support health or manage conditions.
   - Exercise: Tailored physical activities, including frequency and type, if relevant.
4. Ensure the response is professional, concise, and written in plain text without emojis, asterisks, hashtags, or other symbols. Use short paragraphs and bullet points where specified.
5. If the document lacks sufficient data for any section, state this briefly and avoid speculation.
6. Don't Use * in the output, never ever!!
Analyze the following medical document content:

{extracted_text[:5000]}
"""
        response = model.generate_content(prompt)
        summary = response.text

        return jsonify({"summary": summary})
    except Exception as e:
        return jsonify({"detail": str(e)}), 500


if __name__ == '__main__':
    app.run(port=5000,debug=True)
