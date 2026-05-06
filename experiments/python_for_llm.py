import requests

response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "gemma3:1b",
        "prompt": "",
        "stream": False  # ← これが重要
    }
)

print(response.json()["response"])