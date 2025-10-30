from fastapi import FastAPI, Request
import requests
import threading
import time

app = FastAPI()

AGENT_STATE = {
    "last_crawl": None,
    "last_timestamp": None,
    "suggestions": None
}
MCP_SERVER_URL = "http://localhost:8080"

def call_mcp_crawler(target_url, max_concurrent=10, output_prefix="agent_result"):
    payload = {
        "target_url": target_url,
        "max_concurrent": max_concurrent,
        "output_format": "json",
        "output_prefix": output_prefix
    }
    resp = requests.post(f"{MCP_SERVER_URL}/invoke", json=payload)
    if resp.ok:
        return resp.json()
    return None

def generate_suggestions(non200):
    suggestions = []
    for item in non200:
        uri = item.get("uri")
        status = item.get("status")
        if isinstance(status, int) and status == 404:
            suggestions.append(f"Check for broken link: {uri}")
        elif isinstance(status, int) and status == 500:
            suggestions.append(f"Investigate server error: {uri}")
        else:
            suggestions.append(f"Review non-200 status {status}: {uri}")
    return suggestions

def periodic_crawl(interval, target_url, max_concurrent):
    while True:
        result = call_mcp_crawler(target_url, max_concurrent)
        if result:
            AGENT_STATE["last_crawl"] = result
            AGENT_STATE["last_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            AGENT_STATE["suggestions"] = generate_suggestions(result.get("http_non200", []))
            print(f"[Agent] Periodic crawl complete at {AGENT_STATE['last_timestamp']}.")
        else:
            print("[Agent] MCP crawl failed!")
        time.sleep(interval)

AGENT_CARD = {
    "agent_name": "SiteCrawlerA2A",
    "skills": [
        {"name": "start_periodic_crawl", "description": "Start periodic crawl", "parameters": ["interval_seconds", "target_url", "max_concurrent"]},
        {"name": "get_last_report", "description": "Get report and suggestions", "parameters": []}
    ]
}

@app.get("/agent_card")
def get_agent_card():
    return AGENT_CARD

@app.post("/act")
async def act(request: Request):
    body = await request.json()
    skill = body.get("skill")
    params = body.get("parameters", {})
    if skill == "start_periodic_crawl":
        interval = int(params.get("interval_seconds", 3600))
        target_url = params.get("target_url")
        maxc = int(params.get("max_concurrent", 10))
        threading.Thread(target=periodic_crawl, args=(interval, target_url, maxc), daemon=True).start()
        return {"status": "Started periodic crawl"}
    elif skill == "get_last_report":
        return {
            "timestamp": AGENT_STATE["last_timestamp"],
            "summary": AGENT_STATE["last_crawl"],
            "suggestions": AGENT_STATE["suggestions"]
        }
    return {"error": "Unknown skill"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
