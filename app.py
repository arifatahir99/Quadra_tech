from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv

# Load .env
load_dotenv()

app = Flask(__name__, static_folder=".")
CORS(app)

#  API KEY
API_KEY =" AIzaSyAw7NgCd3A-9rp_agm9iFpsjxKJR-5bFtU"
# if not API_KEY:
#     raise ValueError(" GEMINI_API_KEY not found in .env")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


#  Prompt
def build_prompt(content):
    return f"""
You are a fact-checker.

Return ONLY pure JSON.
Do NOT write anything before or after JSON.
Do NOT use markdown.

TEXT:
{content}

Return format:
{{
  "verdict": "REAL" | "FAKE" | "UNCERTAIN",
  "confidence": 0-100,
  "summary": "short explanation"
}}
"""


#  Home route
@app.route("/")
def index():
    return send_from_directory(".", "index.html")


#  Analyze route
@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    content = data.get("content", "").strip()

    if not content:
        return jsonify({"success": False, "error": "No content provided"})

    try:
        response = model.generate_content(build_prompt(content))
        raw = response.text

        print("RAW RESPONSE:", raw)

        #  Force JSON extraction
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)

        if not match:
            return jsonify({
                "success": True,
                "result": {
                    "verdict": "UNCERTAIN",
                    "confidence": 50,
                    "summary": "AI did not return proper JSON. Showing fallback result."
                }
            })

        raw_json = match.group()

        #  Try parsing
        try:
            result = json.loads(raw_json)
        except:
            #  fallback if parsing fails
            result = {
                "verdict": "UNCERTAIN",
                "confidence": 50,
                "summary": "Invalid JSON from AI, fallback response shown."
            }

        return jsonify({"success": True, "result": result})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({
            "success": True,
            "result": {
                "verdict": "ERROR",
                "confidence": 0,
                "summary": "Server error occurred"
            }
        })
