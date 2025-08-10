from flask import Flask, request, jsonify, render_template
import csv
from difflib import SequenceMatcher, get_close_matches
import os

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "knowledge.csv")

def load_knowledge():
    kb = []
    with open(DATA_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            # normalize
            kb.append({
                "id": r.get("id"),
                "keywords": [k.strip().lower() for k in r.get("keywords","").split(",") if k.strip()],
                "answer": r.get("answer","")
            })
    return kb

KB = load_knowledge()

def best_answer(question, kb=KB, top_n=1):
    q = question.lower()
    # Direct keyword match: check overlap
    scores = []
    for item in kb:
        # keyword overlap score
        overlap = 0
        for k in item["keywords"]:
            if k in q:
                overlap += 1
        # fuzzy match between question and joined keywords+answer
        combined = " ".join(item["keywords"]) + " " + item["answer"]
        fuzzy = SequenceMatcher(None, q, combined.lower()).ratio()
        score = overlap * 1.5 + fuzzy  # weight overlap higher
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
    answer, score = best_answer(question)
    if score < 0.15:
        # low confidence fallback
        return jsonify({
            "answer": "I couldn't find an exact match in the knowledge base. Try a different phrasing or ask a supervisor.",
            "confidence": score
        })
    return jsonify({"answer": answer, "confidence": score})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
