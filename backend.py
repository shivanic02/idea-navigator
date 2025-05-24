from flask import Flask, request, jsonify
from flask_cors import CORS
# Assuming IdeaEvaluator and Config are correctly imported from MrAgent or a related module.
# Based on the demo, IdeaEvaluator must be able to perform sequential analysis if no layer is specified.
from MrAgent import IdeaEvaluator

app = Flask(__name__)
CORS(app)  # Apply CORS after app is created

# It's good practice to ensure API keys are set in the environment
# where the Flask app runs, as IdeaEvaluator will rely on them.
# The demo's Config checks are typically done at the application startup/demo entry point.

evaluator = IdeaEvaluator()

@app.route('/start', methods=['POST'])
def start():
    """
    Starts a new analysis session for a given idea.
    Expects JSON: {"idea": "Your startup idea description"}
    """
    try:
        print("✅ Received request at /start")
        # print("Request Headers:", request.headers) # For debugging
        # print("Request Data (raw):", request.data) # For debugging
        # print("Request JSON:", request.json) # For debugging

        data = request.json
        idea = data.get("idea", "")
        if not idea:
            print("🔴 Error: No idea provided in /start request.")
            return jsonify({"error": "No idea provided"}), 400

        msg = evaluator.start(idea)
        print("🟢 Successfully started analysis:", msg)

        # Check if the start was truly successful (e.g., session ID created)
        if "Error" in msg or not evaluator.current_session_id:
             print("🔴 Initialization error from evaluator.start().")
             return jsonify({"error": msg, "details": "Initialization failed"}), 500

        return jsonify({"message": msg, "session_id": evaluator.current_session_id})
    except Exception as e:
        print("🔴 Exception in /start:", str(e))
        import traceback
        traceback.print_exc() # Print full traceback for debugging
        return jsonify({"error": str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyzes an idea. Can perform a single layer analysis or a full sequential analysis.
    Expects JSON:
    - For single layer: {"layer": 1, "user_input": "Optional input for this layer"}
    - For full sequential: {"user_input": "Optional initial input for Layer 1"}
    """
    try:
        print("✅ Received request at /analyze")
        # print("Request Headers:", request.headers) # For debugging
        # print("Request Data (raw):", request.data) # For debugging
        # print("Request JSON:", request.json) # For debugging

        data = request.json
        layer = data.get("layer") # This will be None if not provided in the JSON
        user_input = data.get("user_input", "")

        if layer is None:
            # If 'layer' is not provided, trigger the full sequential analysis,
            # passing the user_input which will typically be used for Layer 1.
            print(f"🚀 Triggering full sequential analysis for current session. Initial user input length: {len(user_input)}")
            # The evaluator.analyze() method implicitly handles sequential progression
            # when the 'layer' argument is absent.
            result = evaluator.analyze(user_input=user_input)
        else:
            # If a specific 'layer' is provided, perform analysis only for that layer.
            print(f"🔬 Analyzing specific layer: {layer}. User input length: {len(user_input)}")
            result = evaluator.analyze(layer=layer, user_input=user_input)

        print("🟢 Analysis request processed. Returning results.")
        # The 'result' should contain the structure as expected by the demo's summary section,
        # including 'all_layer_results' for sequential runs or 'analysis' for single layers.
        return jsonify(result)
    except Exception as e:
        print("🔴 Exception in /analyze:", str(e))
        import traceback
        traceback.print_exc() # Print full traceback for debugging
        return jsonify({"error": str(e)}), 500

@app.route('/summary', methods=['GET'])
def summary():
    """
    Retrieves a summary of the current idea analysis session.
    """
    print("✅ Received request at /summary")
    try:
        summary_info = evaluator.summary()
        print("🟢 Returning summary information.")
        return jsonify(summary_info)
    except Exception as e:
        print("🔴 Exception in /summary:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """
    Retrieves the current status of the idea analysis session.
    """
    print("✅ Received request at /status")
    try:
        status_info = evaluator.status()
        print("🟢 Returning status information.")
        return jsonify(status_info)
    except Exception as e:
        print("🔴 Exception in /status:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Flask API for Idea Evaluator 🚀")
    print("Ensure ANTHROPIC_API_KEY and SERPER_API_KEY environment variables are set for full functionality.")
    app.run(host="0.0.0.0", port=8000)