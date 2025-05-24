# from flask import Flask, request, jsonify
# from flask_cors import CORS
# # Assuming IdeaEvaluator and Config are correctly imported from MrAgent or a related module.
# # Based on the demo, IdeaEvaluator must be able to perform sequential analysis if no layer is specified.
# from MrAgent import IdeaEvaluator

# app = Flask(__name__)
# CORS(app)  # Apply CORS after app is created

# # It's good practice to ensure API keys are set in the environment
# # where the Flask app runs, as IdeaEvaluator will rely on them.
# # The demo's Config checks are typically done at the application startup/demo entry point.

# evaluator = IdeaEvaluator()

# @app.route('/start', methods=['POST'])
# def start():
#     """
#     Starts a new analysis session for a given idea.
#     Expects JSON: {"idea": "Your startup idea description"}
#     """
#     try:
#         print("✅ Received request at /start")
#         # print("Request Headers:", request.headers) # For debugging
#         # print("Request Data (raw):", request.data) # For debugging
#         # print("Request JSON:", request.json) # For debugging

#         data = request.json
#         idea = data.get("idea", "")
#         if not idea:
#             print("🔴 Error: No idea provided in /start request.")
#             return jsonify({"error": "No idea provided"}), 400

#         msg = evaluator.start(idea)
#         print("🟢 Successfully started analysis:", msg)

#         # Check if the start was truly successful (e.g., session ID created)
#         if "Error" in msg or not evaluator.current_session_id:
#              print("🔴 Initialization error from evaluator.start().")
#              return jsonify({"error": msg, "details": "Initialization failed"}), 500

#         return jsonify({"message": msg, "session_id": evaluator.current_session_id})
#     except Exception as e:
#         print("🔴 Exception in /start:", str(e))
#         import traceback
#         traceback.print_exc() # Print full traceback for debugging
#         return jsonify({"error": str(e)}), 500

# @app.route('/analyze', methods=['POST'])
# def analyze():
#     """
#     Analyzes an idea. Can perform a single layer analysis or a full sequential analysis.
#     Expects JSON:
#     - For single layer: {"layer": 1, "user_input": "Optional input for this layer"}
#     - For full sequential: {"user_input": "Optional initial input for Layer 1"}
#     """
#     try:
#         print("✅ Received request at /analyze")
#         # print("Request Headers:", request.headers) # For debugging
#         # print("Request Data (raw):", request.data) # For debugging
#         # print("Request JSON:", request.json) # For debugging

#         data = request.json
#         layer = data.get("layer") # This will be None if not provided in the JSON
#         user_input = data.get("user_input", "")

#         if layer is None:
#             # If 'layer' is not provided, trigger the full sequential analysis,
#             # passing the user_input which will typically be used for Layer 1.
#             print(f"🚀 Triggering full sequential analysis for current session. Initial user input length: {len(user_input)}")
#             # The evaluator.analyze() method implicitly handles sequential progression
#             # when the 'layer' argument is absent.
#             result = evaluator.analyze(user_input=user_input)
#         else:
#             # If a specific 'layer' is provided, perform analysis only for that layer.
#             print(f"🔬 Analyzing specific layer: {layer}. User input length: {len(user_input)}")
#             result = evaluator.analyze(layer=layer, user_input=user_input)

#         print("🟢 Analysis request processed. Returning results.")
#         # The 'result' should contain the structure as expected by the demo's summary section,
#         # including 'all_layer_results' for sequential runs or 'analysis' for single layers.
#         return jsonify(result)
#     except Exception as e:
#         print("🔴 Exception in /analyze:", str(e))
#         import traceback
#         traceback.print_exc() # Print full traceback for debugging
#         return jsonify({"error": str(e)}), 500

# @app.route('/summary', methods=['GET'])
# def summary():
#     """
#     Retrieves a summary of the current idea analysis session.
#     """
#     print("✅ Received request at /summary")
#     try:
#         summary_info = evaluator.summary()
#         print("🟢 Returning summary information.")
#         return jsonify(summary_info)
#     except Exception as e:
#         print("🔴 Exception in /summary:", str(e))
#         return jsonify({"error": str(e)}), 500

# @app.route('/status', methods=['GET'])
# def status():
#     """
#     Retrieves the current status of the idea analysis session.
#     """
#     print("✅ Received request at /status")
#     try:
#         status_info = evaluator.status()
#         print("🟢 Returning status information.")
#         return jsonify(status_info)
#     except Exception as e:
#         print("🔴 Exception in /status:", str(e))
#         return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     print("🚀 Starting Flask API for Idea Evaluator 🚀")
#     print("Ensure ANTHROPIC_API_KEY and SERPER_API_KEY environment variables are set for full functionality.")
#     app.run(host="0.0.0.0", port=8000)






from flask import Flask, request, jsonify
from flask_cors import CORS
import json # Import json for pretty printing in logs
import os # Import os to check environment variables

# Assuming IdeaEvaluator and Config are correctly imported from MrAgent or a related module.
# You might need to adjust this import based on your project structure.
# For example, if Config is in MrAgent.config:
# from MrAgent.config import Config
# Or if Config is a standalone module:
# import config
from MrAgent import IdeaEvaluator

# It's good practice to ensure API keys are set in the environment
# where the Flask app runs, as IdeaEvaluator will rely on them.
# The demo's Config checks are typically done at the application startup/demo entry point.

app = Flask(__name__)
CORS(app)  # Apply CORS after app is created

# Initialize evaluator globally. API keys will be checked by IdeaEvaluator itself.
evaluator = IdeaEvaluator()

@app.route('/start', methods=['POST'])
def start():
    """
    Starts a new analysis session for a given idea.
    Expects JSON: {"idea": "Your startup idea description"}
    """
    try:
        print("\n--- Received request at /start ---")
        # For detailed debugging of incoming requests:
        # print("Request Headers:", request.headers)
        # print("Request Data (raw):", request.data)
        # print("Request JSON:", request.json)

        data = request.json
        idea = data.get("idea", "")
        if not idea:
            print("🔴 Error: No idea provided in /start request.")
            return jsonify({"error": "No idea provided"}), 400

        print(f"💡 Attempting to start analysis for idea: '{idea[:80]}...'")
        start_message = evaluator.start(idea)

        # The demo prints a start_message and checks for errors or missing session ID
        if "Error" in start_message or not evaluator.current_session_id:
            print(f"🔴 Initialization error from evaluator.start(): {start_message}")
            return jsonify({"error": start_message, "details": "Initialization failed"}), 500

        print(f"🟢 Analysis session successfully started. Session ID: {evaluator.current_session_id}")
        return jsonify({"message": start_message, "session_id": evaluator.current_session_id})

    except Exception as e:
        print(f"🔴 Exception in /start: {str(e)}")
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
        print("\n--- Received request at /analyze ---")
        # print("Request Headers:", request.headers)
        # print("Request Data (raw):", request.data)
        # print("Request JSON:", request.json)

        if not evaluator.current_session_id:
            print("🔴 Error: No active analysis session. Please call /start first.")
            return jsonify({"error": "No active analysis session. Please call /start first."}), 400

        data = request.json
        layer = data.get("layer") # This will be None if not provided in the JSON
        user_input = data.get("user_input", "")

        if user_input:
            print(f"ℹ️ User input provided for analysis: '{user_input[:80]}...'")

        if layer is None:
            # If 'layer' is not provided, trigger the full sequential analysis.
            print("🚀 Triggering full sequential analysis for the current idea.")
            print("This may take several minutes as all 5 layers are processed sequentially.")
            # The evaluator.analyze() method implicitly handles sequential progression
            # when the 'layer' argument is absent.
            full_analysis_results = evaluator.analyze(user_input=user_input)
        else:
            # If a specific 'layer' is provided, perform analysis only for that layer.
            print(f"🔬 Analyzing specific layer: {layer}")
            full_analysis_results = evaluator.analyze(layer=layer, user_input=user_input)

        print("🟢 Analysis request processed. Preparing response.")

        # Create the response payload
        response_payload = full_analysis_results.copy() if full_analysis_results else {}

        # If it was a full sequential run, or if the result structure contains
        # all_layer_results, format a detailed summary for the client.
        if full_analysis_results and "all_layer_results" in full_analysis_results:
            detailed_layer_summary = []
            print("\n--- Server-Side Detailed Layer Summary (from sequential run) ---")
            for layer_num_key in sorted(full_analysis_results["all_layer_results"].keys()):
                result = full_analysis_results["all_layer_results"][layer_num_key]
                layer_num_actual = result.get("layer", layer_num_key)
                layer_name = result.get("layer_name", f"Layer {layer_num_actual}")
                status = result.get("status", "unknown")
                confidence = result.get('confidence', 'N/A')
                error = result.get('error', '')
                reason = result.get('reason', '')
                analysis_text = result.get('analysis', '') # Get the full analysis text

                # Removed truncation: now `analysis_text` contains the full content
                # The frontend will be responsible for handling how it displays long texts.

                layer_detail_for_summary = {
                    "layer": layer_num_actual,
                    "name": layer_name,
                    "status": status.upper(),
                    "confidence": confidence,
                }
                if error:
                    layer_detail_for_summary["error"] = error
                if reason:
                    layer_detail_for_summary["reason"] = reason
                if analysis_text: # Include the full text if it's not empty
                    layer_detail_for_summary["analysis_text"] = analysis_text # Changed key for clarity

                detailed_layer_summary.append(layer_detail_for_summary)

                # Print to server console for immediate visibility during execution
                print(f"\n  Layer {layer_num_actual} ({layer_name}) - Status: {status.upper()}")
                if status == "completed":
                    print(f"    Confidence: {confidence}")
                    # Print full text to console, or a snippet if you still want brevity there
                    # For console, you might still want a snippet to avoid overwhelming the terminal
                    console_display_text = analysis_text[:500] + ('...' if len(analysis_text) > 500 else '')
                    if console_display_text:
                        print(f"    Analysis Text: {console_display_text}")
                elif status in ["skipped_completed", "skipped_previous_issue"]:
                    print(f"    Skipped: {reason if reason else status}")
                elif status in ["rate_limited", "failed"]:
                    print(f"    Error: {error}")
                    if "retry_suggestion" in result:
                        print(f"    Suggestion: {result['retry_suggestion']}")
                print("-" * 40)

            response_payload["detailed_layer_summary"] = detailed_layer_summary
            print("--- End of Server-Side Detailed Layer Summary ---")

        return jsonify(response_payload)

    except Exception as e:
        print(f"🔴 Exception in /analyze: {str(e)}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging
        return jsonify({"error": str(e)}), 500

@app.route('/summary', methods=['GET'])
def summary():
    """
    Retrieves a summary of the current idea analysis session.
    """
    print("\n--- Received request at /summary ---")
    try:
        if not evaluator.current_session_id:
            print("🔴 Error: No active analysis session for summary. Please call /start first.")
            return jsonify({"error": "No active analysis session. Please call /start first."}), 400

        summary_info = evaluator.summary()
        print("🟢 Returning summary information:")
        print(json.dumps(summary_info, indent=2))
        return jsonify(summary_info)
    except Exception as e:
        print(f"🔴 Exception in /summary: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    """
    Retrieves the current status of the idea analysis session.
    """
    print("\n--- Received request at /status ---")
    try:
        if not evaluator.current_session_id:
            print("🔴 Error: No active analysis session for status. Please call /start first.")
            return jsonify({"error": "No active analysis session. Please call /start first."}), 400

        status_info = evaluator.status()
        print("🟢 Returning status information:")
        print(json.dumps(status_info, indent=2))
        return jsonify(status_info)
    except Exception as e:
        print(f"🔴 Exception in /status: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Flask API for Idea Evaluator 🚀")
    print("===========================================")

    # --- API Key Check on startup for better visibility ---
    # Assuming Config is available or we check environment variables directly
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    SERPER_API_KEY = os.getenv("SERPER_API_KEY")

    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == 'your-anthropic-api-key-here':
        print("🔴 CRITICAL: ANTHROPIC_API_KEY is not set or is default. LLM calls will fail.")
        print("Please set it as an environment variable (e.g., export ANTHROPIC_API_KEY='your_key').")
    else:
        print("✅ ANTHROPIC_API_KEY is set.")

    if not SERPER_API_KEY or SERPER_API_KEY == 'your-serper-api-key-here':
        print("🟡 WARNING: SERPER_API_KEY is not set or is default. Internet search functionality will be limited or unavailable.")
        print("Please set it as an environment variable for full functionality.")
    else:
        print("✅ SERPER_API_KEY is set.")

    print("\n💡 Ready to receive requests...")
    app.run(host="0.0.0.0", port=8000)