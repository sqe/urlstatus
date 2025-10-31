from flask import Flask, request, jsonify
import requests
import os
import logging

app = Flask(__name__)
GITHUB_REPO = os.getenv("GITHUB_REPO", "YOUR_ORG/YOUR_REPO")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

AGENT_CARD = {
    "protocolVersion": "0.3.0",
    "name": "GitHub Code Analysis Agent",
    "description": "Finds backend GitHub source for failing endpoints, embeds code, and proposes fixes.",
    "url": "http://localhost:9200/v1",
    "preferredTransport": "HTTP+JSON",
    "skills": [
        {
            "id": "discover_fix",
            "name": "Discover Source for Failing URLs",
            "description": "Map crawl failures to backend code and recommend fixes."
        }
    ]
}

def github_search_code(query):
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.text-match+json"
    }
    # Search term should be endpoint path or fragment
    resp = requests.get(
        f"https://api.github.com/search/code?q={query}+repo:{GITHUB_REPO}", headers=headers)
    if resp.ok:
        return resp.json()
    else:
        logging.error(f"GitHub search failed for {query}: {resp.text}")
        return {}

@app.route("/.well-known/agent-card.json")
def agent_card():
    return jsonify(AGENT_CARD)

@app.route("/v1/message:send", methods=["POST"])
def message_send():
    req = request.json
    params = req.get("params", {})
    skill = params.get("skill")
    if skill == "discover_fix":
        urls = params.get("failing_urls", [])
        analysis = []
        for url in urls:
            endpoint = url.split("/", 3)[-1]  # crude path extraction
            search = github_search_code(endpoint)
            items = search.get("items", [])
            mapped = [{
                "file_path": i["path"],
                "repo_url": i["html_url"],
                "snippet": next((tm["fragment"] for tm in i.get("text_matches", [])), None)
            } for i in items]
            analysis.append({
                "url": url,
                "matches": mapped
            })
        return jsonify({
            "jsonrpc": req.get("jsonrpc", "2.0"),
            "id": req.get("id"),
            "result": {"analysis": analysis}
        })
    return jsonify({
        "jsonrpc": req.get("jsonrpc", "2.0"),
        "id": req.get("id"),
        "error": {"code": -32000, "message": "Unknown skill"}
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9200)
