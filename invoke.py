import requests
payload = {
    "jsonrpc": "2.0",
    "id": "task-001",
    "method": "message/send",
    "params": {
        "skill": "start_periodic_crawl",
        "interval_seconds": 30,
        "target_url": "https://nebius.com/",
        "max_concurrent": 10
    }
}
req = requests.post("http://localhost:9000/v1/message:send", json=payload)
print(req.json())

