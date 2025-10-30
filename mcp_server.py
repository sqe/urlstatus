# mcp_server.py

from flask import Flask, request, send_from_directory, jsonify, abort
import os
import subprocess
import json

app = Flask(__name__)

RESULTS_DIR = os.path.abspath("results")  # Ensure results/ is always used

MCP_DESCRIPTION = {
    "name": "web_crawler_cli",
    "description": "Crawls a website using CLI and returns HTTP 200/non-200 results (excludes redirects)",
    "parameters": {
        "target_url": {"type": "string", "description": "Base URL to crawl"},
        "max_concurrent": {"type": "integer", "description": "Maximum concurrent requests"},
        "output_format": {"type": "string", "enum": ["csv", "json"], "description": "csv or json"},
        "output_prefix": {"type": "string", "description": "Prefix for output files (without folder, e.g. 'a2a_mcp')"}
    },
    "outputs": {
        "http_200": {"type": "list", "description": "List of HTTP 200 records"},
        "http_non200": {"type": "list", "description": "List of HTTP non-200 (not 3xx) records"}
    }
}

@app.route("/describe")
def describe_tool():
    return jsonify(MCP_DESCRIPTION)

@app.route("/invoke", methods=["POST"])
def invoke_mcp():
    body = request.json
    target_url = body.get("target_url")
    max_concurrent = str(body.get("max_concurrent", 10))
    output_format = body.get("output_format", "json")
    output_prefix = body.get("output_prefix", "a2a_mcp")
    # Always store the results in the results/ subdirectory
    full_prefix = os.path.join("results", output_prefix)
    # Ensure results/ directory exists
    os.makedirs("results", exist_ok=True)

    cmd = [
        "python", "cli.py",
        "--target-url", target_url,
        "--max-concurrent", max_concurrent,
        "--output-format", output_format,
        "--output-prefix", full_prefix
    ]
    subprocess.run(cmd, check=True)
    http_200_path = os.path.join("results", f"{output_prefix}_http200.json")
    http_non200_path = os.path.join("results", f"{output_prefix}_http_non200.json")
    with open(http_200_path, "r") as f:
        http_200 = json.load(f)
    with open(http_non200_path, "r") as f:
        http_non200 = json.load(f)
    return jsonify({"http_200": http_200, "http_non200": http_non200})

@app.route("/files/<path:filename>")
def get_file(filename):
    # Only allow .json, .csv, .md files in results/
    allowed_extensions = (".json", ".csv", ".md")
    if not filename.endswith(allowed_extensions):
        abort(403, description="Invalid file type requested")
    safe_path = os.path.abspath(os.path.join(RESULTS_DIR, filename))
    if not safe_path.startswith(RESULTS_DIR):
        abort(400, description="Path traversal attempt detected")
    if not os.path.isfile(safe_path):
        abort(404, description="File not found")
    return send_from_directory(RESULTS_DIR, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
