# Site Crawler A2A Agent

This project provides a fully agentic, **A2A-compliant web crawler agent** using Python, Flask, and modular async crawling logic.  
It exposes both a CLI interface and an A2A HTTP+JSON/JSON-RPC protocol service (per [A2A Protocol](https://a2a-protocol.org/latest/specification/)) for agent-to-agent orchestration.

---

## Features

- **A2A Agent**: Supported via `a2a_agent_flask.py`—responds to any A2A-compliant system with a well-formed AgentCard and JSON-RPC 2.0 methods (`message/send`).
- **Modular CLI**: Run web crawling/joined reporting tasks directly via `cli.py` for interactive/manual use.
- **Skill Structure**: Schedule periodic crawls or fetch the most recent report and suggestions for failed URLs as skills.
- **MCP Tool Optional**: Also includes a modular MCP-style HTTP tool (`mcp_server.py`) for stateless, non-agentic API use.
- **Clean, extensible structure** for large-scale or team-oriented A2A/MCP adoption.

---

## Quickstart

1. **Install dependencies**
    ```
    pip install -r requirements.txt
    ```

2. **Run the A2A agent server (Flask)**
    ```
    python a2a_agent_flask.py
    ```
    This listens on `http://localhost:9000/`

3. **Discover AgentCard**
    ```
    curl http://localhost:9000/.well-known/agent-card.json
    ```

4. **Start periodic crawl with JSON-RPC**
    ```
    import requests
    payload = {
        "jsonrpc": "2.0",
        "id": "task-001",
        "method": "message/send",
        "params": {
            "skill": "start_periodic_crawl",
            "interval_seconds": 600,
            "target_url": "https://example.com/",
            "max_concurrent": 10
        }
    }
    requests.post("http://localhost:9000/v1/message:send", json=payload)
    ```

5. **Fetch latest crawl report and suggestions**
    ```
    payload = {
        "jsonrpc": "2.0",
        "id": "task-002",
        "method": "message/send",
        "params": {"skill": "get_last_report"}
    }
    requests.post("http://localhost:9000/v1/message:send", json=payload)
    ```

6. **Manual (CLI) crawling**
    ```
    python cli.py --target-url https://example.com/ --max-concurrent 10 --output-format json --output-prefix results/manual
    ```

---

## Files

- **a2a_agent_flask.py**: Main A2A agent server (serves agent card, JSON-RPC skill endpoint)
- **cli.py**: Standalone crawler with full CLI interface (runs all crawl/report logic)
- **config.py, crawl.py, report.py**: Modular components for config, network crawling, reporting
- **mcp_server.py**: (Optional) API for tool/server-only mode (not A2A agent)
- **mcp_client.py**: (Optional) test client for direct MCP use
- **requirements.txt**: All dependencies

---

## A2A Specification Conformance

- **AgentCard**: Served at `/.well-known/agent-card.json`
- **JSON-RPC 2.0**: Main endpoint `/v1/message:send` accepts and returns JSON-RPC objects per spec
- **Skills**: `start_periodic_crawl`, `get_last_report`
- **Messages & Tasks**: Responds per standard A2A formats for immediate and schedule-based commands

---

## Extending

- Add more skills by extending the handler in `a2a_agent_flask.py`
- Integrate with larger orchestration tools or LLM agent frameworks
- Use as reference implementation for app-to-agent or agent-to-agent Python systems

---

## MCP Server Instructions (V2 - URL Analysis)

This project includes two advanced agents for analyzing failing URLs and identifying codebase culprits:

### Analyzer Agent (http://localhost:9100)
The `urlstatus/analyzer_agent.py` service analyzes web crawl failures and suggests fixes using an OpenAI-compatible LLM. To run:

1. Install dependencies (if not already done):  
   ```
   pip install -r requirements.txt
   ```

2. Start the analyzer agent:  
   ```
   python urlstatus/analyzer_agent.py
   ```

3. The service will be available at `http://localhost:9100/v1` and serves its AgentCard at `http://localhost:9100/.well-known/agent-card.json`

### GitHub Code Analysis Agent (http://localhost:9200)
The `urlstatus/github_code_agent.py` service finds backend GitHub source for failing endpoints and proposes fixes. To run:

1. Set your GitHub credentials in environment variables:
   ```
   export GITHUB_REPO="YOUR_ORG/YOUR_REPO"
   export GITHUB_TOKEN="your_github_personal_access_token"
   ```

2. Install dependencies (if not already done):  
   ```
   pip install -r requirements.txt
   ```

3. Start the GitHub code analysis agent:  
   ```
   python urlstatus/github_code_agent.py
   ```

4. The service will be available at `http://localhost:9200/v1` and serves its AgentCard at `http://localhost:9200/.well-known/agent-card.json`

These V2 agents extract URLs from crawl reports and pass them to dedicated analysis agents that search for failing URL patterns in the codebase, enabling comprehensive root cause analysis and automated fix recommendations.

## License

MIT License

Copyright (c) 2025 Aziz Kurbanov

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.