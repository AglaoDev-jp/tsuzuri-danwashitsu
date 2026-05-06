import requests
from pathlib import Path

# AIに聞く
response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "gemma3:1b",
        "prompt": "READMEのファイル名だけ答えて",
        "stream": False
    }
)

filename = response.json()["response"].strip()

# 検索
for path in Path.home().rglob(filename):
    print(path)