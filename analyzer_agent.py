from flask import Flask, request, jsonify
import openai
import os
import logging

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

AGENT_CARD = {
    "protocolVersion": "0.3.0",
    "name": "Analyzer Agent",
    "description": "Analyzes web crawl failures and suggests fixes using an OpenAI-compatible LLM.",
    "url": "http://localhost:9100/v1",
    "preferredTransport": "HTTP+JSON",
    "skills": [
        {
            "id": "analyze_crawl",
            "name": "Analyze Crawl Report",
            "description": "Send a web crawl report (HTTP status codes) and get diagnostic suggestions."
        }
    ]
}

@app.route("/.well-known/agent-card.json")
def agent_card():
    return jsonify(AGENT_CARD)

@app.route("/v1/message:send", methods=["POST"])
def message_send():
    req = request.json
    params = req.get("params", {})
    skill = params.get("skill")
    if skill == "analyze_crawl":
        report = params.get("crawl_report", {})
        prompt = (
            "Given this JSON web crawl result, list root causes for failing URLs. "
            "Suggest specific backend/frontend fixes for each failure. "
            "Respond with a numbered list describing each fix."
            f"\nCrawl Report:\n{report}"
        )
        try:
            llm_resp = openai.ChatCompletion.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512
            )
            analysis = llm_resp['choices'][0]['message']['content']
            return jsonify({
                "jsonrpc": req.get("jsonrpc", "2.0"),
                "id": req.get("id"),
                "result": {"analysis": analysis}
            })
        except Exception as e:
            logging.error(f"LLM error: {e}")
            return jsonify({
                "jsonrpc": req.get("jsonrpc", "2.0"),
                "id": req.get("id"),
                "error": {"code": -32000, "message": str(e)}
            })
    return jsonify({
        "jsonrpc": req.get("jsonrpc", "2.0"),
        "id": req.get("id"),
        "error": {"code": -32000, "message": "Unknown skill"}
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9100)
