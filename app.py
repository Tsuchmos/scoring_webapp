

# ===== app.py (Flask server) =====
from flask import Flask, render_template, request, jsonify, send_from_directory
import json, os

app = Flask(__name__)

STATIC_DIR = os.path.join(app.root_path, "static")

# --------------------------------------------------
# Helper – load table by gender
# --------------------------------------------------

def load_table(gender: str):
    path = os.path.join(STATIC_DIR, f"score_table_{gender}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

# --------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

# --------------------------------------------------
# record ⇒ score  （最も近いスコア）
# --------------------------------------------------
@app.route("/get_score", methods=["POST"])
def get_score():
    event  = request.form.get("event")
    record_str = request.form.get("record")
    gender = request.form.get("gender", default="men")

    if not event or not record_str:
        return jsonify({"error": "種目・記録を入力してください"})
    try:
        record = parse_record(record_str)
    except:
        return jsonify({"error": "記録の形式が不正です（例: 1:28.58）"})
    try:
        table = load_table(gender)
    except FileNotFoundError:
        return jsonify({"error": f"{gender} データがありません"})

    best, diff = None, float("inf")
    for row in table:
        val_str = row.get(event)
        if not val_str:
            continue
        try:
            val = parse_record(val_str)
        except:
            continue
        d = abs(val - record)
        if d < diff:
            diff, best = d, row
    if best:
        return jsonify({"score": best["score"], "event": event, "record": record_str, "gender": gender})
    return jsonify({"error": "該当記録が見つかりません"})

# --------------------------------------------------
# score ⇒ record  (±5pt 表示)
# --------------------------------------------------
@app.route("/get_record", methods=["POST"])
def get_record():
    score  = request.form.get("score",  type=int)
    gender = request.form.get("gender", default="men")
    if score is None:
        return jsonify({"error": "スコアを入力してください"})
    try:
        table = load_table(gender)
    except FileNotFoundError:
        return jsonify({"error": f"{gender} データがありません"})

    rows = [r for r in table if abs(r["score"]-score) <= 5]
    rows.sort(key=lambda r: r["score"], reverse=True)
    return jsonify(rows)

# --------------------------------------------------
# 記録文字列を秒に変換（1:28.58 → 88.58）
# --------------------------------------------------
def parse_record(s):
    if ":" in s:
        m, s = s.split(":")
        return int(m) * 60 + float(s)
    return float(s)

# --------------------------------------------------
# expose static files even in debug (for fetch)
# --------------------------------------------------
@app.route("/static/<path:fname>")
def _static(fname):
    return send_from_directory(STATIC_DIR, fname)

# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)