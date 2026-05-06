import requests
import json

# 使用するモデル名
MODEL_NAME = "gemma3:1b"

# OllamaのAPIエンドポイント
URL = "http://localhost:11434/api/generate"


while True:
    # ユーザーから入力を受け取る
    user_input = input("\nあなた: ")

    # 終了コマンド
    if user_input in ["exit", "quit", "終了"]:
        print("チャットを終了します。")
        break

    # Ollamaへリクエストを送信
    response = requests.post(
        URL,
        json={
            "model": MODEL_NAME,
            "prompt": user_input
        },
        stream=True
    )

    print("AI: ", end="", flush=True)

    # ストリーミングで返ってくる文章を少しずつ表示
    for line in response.iter_lines():
        if line:
            data = json.loads(line)

            # responseキーがある場合だけ表示
            if "response" in data:
                print(data["response"], end="", flush=True)

    print()