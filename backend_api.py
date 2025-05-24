from flask import Flask, request, jsonify
from flask_cors import CORS
from MrAgent import IdeaEvaluator

app = Flask(__name__)
CORS(app)  # Apply CORS after app is created

evaluator = IdeaEvaluator()

@app.route('/start', methods=['POST'])
def start():
    try:
        print("✅ Received request at /start")
        print("Request Headers:", request.headers)
        print("Request Data (raw):", request.data)
        print("Request JSON:", request.json)

        data = request.json
        idea = data.get("idea", "")
        if not idea:
            return jsonify({"error": "No idea provided"}), 400

        msg = evaluator.start(idea)
        print("🟢 Successfully started analysis:", msg)
        return jsonify({"message": msg})
    except Exception as e:
        print("🔴 Exception in /start:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    layer = data.get("layer")
    user_input = data.get("user_input", "")
    result = evaluator.analyze(layer=layer, user_input=user_input)
    return jsonify(result)

@app.route('/summary', methods=['GET'])
def summary():
    return jsonify(evaluator.summary())

@app.route('/status', methods=['GET'])
def status():
    return jsonify(evaluator.status())

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8000)
