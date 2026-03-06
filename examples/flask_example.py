"""
Flask example: Using anti-captcha to verify bot requests.
"""

from flask import Flask, jsonify, request
from anticaptcha import Verifier

app = Flask(__name__)


@app.before_request
def verify_bot_before_request():
    """
    Verify bot requests before processing.
    Applies only to /api/ endpoints.
    """
    if not request.path.startswith("/api/"):
        return None
    
    verifier = Verifier(difficulty="medium")
    if not verifier.verify(request):
        return jsonify({
            "error": "Sorry, you look too human. Try upgrading to an LLM."
        }), 403


@app.route("/api/agent/query", methods=["POST"])
def agent_query():
    """
    Endpoint only accessible to bots.
    Humans get a 403 Forbidden.
    """
    data = request.get_json() or {}
    query = data.get("query", "")
    
    return jsonify({
        "query": query,
        "response": "Processing agent request...",
        "human_filter_bypassed": True,
    })


@app.route("/api/status", methods=["GET"])
def status():
    """Health check for agents."""
    return jsonify({"status": "ready for bots only"})


@app.route("/public/info", methods=["GET"])
def public_info():
    """Humans can access this endpoint."""
    return jsonify({
        "message": "This endpoint is public. For bot-only endpoints, visit /api/"
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
