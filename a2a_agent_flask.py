from flask import Flask, request, jsonify, render_template
import requests
import threading
import time
import os

app = Flask(__name__, template_folder="templates")

AGENT_STATE = {
    "last_crawl": None,
    "last_timestamp": None,
    "suggestions": None,
    "last_target": None,
    "last_interval": None,
    "last_max_concurrent": None
}

RESULTS_DIR = os.path.abspath("results")
ALLOWED_EXTENSIONS = (".json", ".csv", ".md")

MCP_SERVER_URL = "http://localhost:8080/invoke"
MCP_HEALTH_URL = "http://localhost:8080/describe"
MCP_FILE_URL = "http://localhost:8080/files"

AGENT_CARD = {
    "protocolVersion": "0.3.0",
    "name": "Flask Crawler Agent",
    "description": "A2A agent for periodic site crawling and health suggestion using MCP tool.",
    "url": "http://localhost:9000/v1",
    "preferredTransport": "HTTP+JSON",
    "version": "1.0.0",
    "capabilities": {"streaming": False, "pushNotifications": False},
    "defaultInputModes": ["application/json"],
    "defaultOutputModes": ["application/json"],
    "skills": [
        {
            "id": "start_periodic_crawl",
            "name": "Start Periodic Crawl",
            "description": "Schedule periodic crawling",
            "tags": ["crawler", "monitoring"],
            "examples": ["Start crawling every hour for https://example.com"],
        },
        {
            "id": "get_last_report",
            "name": "Get Crawl Report",
            "description": "Fetch the latest crawl and suggestions",
            "tags": ["crawler", "report"],
            "examples": ["Show me the last crawl summary"],
        },
    ],
}

def list_result_files():
    files = []
    if os.path.isdir(RESULTS_DIR):
        for fname in os.listdir(RESULTS_DIR):
            if fname.endswith(ALLOWED_EXTENSIONS):
                files.append(fname)
    return sorted(files)

def call_mcp_crawl(target_url, max_concurrent=10, output_prefix="a2a_mcp", output_format="json"):
    payload = {
        "target_url": target_url,
        "max_concurrent": max_concurrent,
        "output_format": output_format,
        "output_prefix": output_prefix
    }
    try:
        resp = requests.post(MCP_SERVER_URL, json=payload, timeout=180)
        if resp.ok:
            return resp.json()
        else:
            return {
                "http_200": [],
                "http_non200": [],
                "mcp_error": f"Status {resp.status_code}: {resp.text}"
            }
    except Exception as e:
        return {"http_200": [], "http_non200": [], "mcp_error": str(e)}

def mcp_health():
    try:
        r = requests.get(MCP_HEALTH_URL, timeout=3)
        return r.ok
    except Exception:
        return False

def generate_suggestions(non200):
    sugg = []
    for item in non200:
        uri = item.get("uri")
        status = item.get("status")
        if isinstance(status, int) and status == 404:
            sugg.append(f"Check for broken link: {uri}")
        elif isinstance(status, int) and status == 500:
            sugg.append(f"Investigate server error: {uri}")
        else:
            sugg.append(f"Review non-200 status {status}: {uri}")
    return sugg

def periodic_crawl(interval, target_url, max_concurrent):
    while True:
        result = call_mcp_crawl(target_url, max_concurrent)
        AGENT_STATE["last_crawl"] = result
        AGENT_STATE["last_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        AGENT_STATE["suggestions"] = generate_suggestions(result.get("http_non200", []))
        AGENT_STATE["last_target"] = target_url
        AGENT_STATE["last_interval"] = interval
        AGENT_STATE["last_max_concurrent"] = max_concurrent
        print(f"[Agent] Periodic crawl complete at {AGENT_STATE['last_timestamp']}.")
        time.sleep(interval)

@app.route("/")
def dashboard():
    result_files = list_result_files()
    file_links = [
        {"name": fname, "url": f"{MCP_FILE_URL}/{fname}"}
        for fname in result_files
    ]
    return render_template(
        "dashboard.html",
        last_target=AGENT_STATE.get("last_target"),
        last_interval=AGENT_STATE.get("last_interval"),
        last_max_concurrent=AGENT_STATE.get("last_max_concurrent"),
        last_timestamp=AGENT_STATE.get("last_timestamp"),
        crawl=AGENT_STATE.get("last_crawl"),
        suggestions=AGENT_STATE.get("suggestions"),
        mcp_ok=mcp_health(),
        file_links=file_links
    )

@app.route("/.well-known/agent-card.json")
def agent_card():
    return jsonify(AGENT_CARD)

@app.route("/v1/message:send", methods=["POST"])
def message_send():
    req = request.json
    jsonrpc_version = req.get("jsonrpc")
    method = req.get("method")
    params = req.get("params", {})
    req_id = req.get("id")
    try:
        skill = params.get("skill")
        if skill == "start_periodic_crawl":
            interval = int(params.get("interval_seconds", 3600))
            target_url = params.get("target_url")
            max_conc = int(params.get("max_concurrent", 10))
            AGENT_STATE["last_target"] = target_url
            AGENT_STATE["last_interval"] = interval
            AGENT_STATE["last_max_concurrent"] = max_conc
            threading.Thread(target=periodic_crawl, args=(interval, target_url, max_conc), daemon=True).start()
            result = {"message": f"Periodic crawl started for {target_url}"}
        elif skill == "get_last_report":
            result = {
                "timestamp": AGENT_STATE.get("last_timestamp"),
                "last_crawl": AGENT_STATE.get("last_crawl"),
                "suggestions": AGENT_STATE.get("suggestions")
            }
        else:
            raise Exception(f"Unknown skill: {skill}")
        resp = {"jsonrpc": jsonrpc_version, "id": req_id, "result": result}
    except Exception as e:
        resp = {
            "jsonrpc": jsonrpc_version, "id": req_id,
            "error": {"code": -32000, "message": str(e)}
        }
    return jsonify(resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9000)
