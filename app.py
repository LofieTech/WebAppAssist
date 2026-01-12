from flask import Flask, request, jsonify, render_template
import csv
from difflib import SequenceMatcher
import os
import re

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "knowledge.csv")

def load_knowledge():
    kb = []
    with open(DATA_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            kb.append({
                "id": r.get("id"),
                "keywords": [k.strip().lower() for k in r.get("keywords","").split(",") if k.strip()],
                "answer": r.get("answer","")
            })
    return kb

KB = load_knowledge()

def find_answer(user_input, kb=KB):
    """
    Try numeric/guide code match first. If not found, fallback to keywords/fuzzy.
    Returns (answer, confidence)
    """
    user_input = user_input.lower().strip()

    # 1️⃣ Check for 4-digit numeric code
    match = re.search(r"\b\d{4}\b", user_input)
    code = match.group() if match else None
    guide_code = f"guide_code_{code}" if code else None

    # 2️⃣ Numeric code match
    if guide_code:
        for item in kb:
            if guide_code in item["keywords"]:
                return item["answer"], 0.95  # high confidence

    # 3️⃣ Fallback to fuzzy/keyword matching (original logic)
    answer, score = best_answer(user_input, kb)
    if score < 0.15:
        # low confidence fallback
        return (
            "I couldn't find an exact match in the knowledge base. Try a different phrasing or ask a supervisor.",
            0.04
        )
    return answer, score

def best_answer(question, kb=KB, top_n=1):
    q = question.lower()
    scores = []
    for item in kb:
        overlap = sum(1 for k in item["keywords"] if k in q)
        combined = " ".join(item["keywords"]) + " " + item["answer"]
        fuzzy = SequenceMatcher(None, q, combined.lower()).ratio()
        score = overlap * 1.5 + fuzzy
        scores.append((score, item))
    scores.sort(key=lambda x: x[0], reverse=True)
    if not scores:
        return None, 0.0
    best_score, best_item = scores[0]
    return best_item["answer"], float(best_score)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json or {}
    question = data.get("question","").strip()
    if not question:
        return jsonify({"error":"No question provided"}), 400

    answer, confidence = find_answer(question, KB)
    return jsonify({"answer": answer, "confidence": round(confidence, 2)})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
