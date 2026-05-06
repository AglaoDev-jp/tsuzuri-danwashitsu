import requests
import json

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "gemma3:1b",
        "prompt": "こんにちは"
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        data = json.loads(line)
        print(data["response"], end="", flush=True)