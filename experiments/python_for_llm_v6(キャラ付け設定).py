import requests
import json

MODEL_NAME = "gemma3:1b"
URL = "http://localhost:11434/api/chat"

# ==========================================
# AIのキャラ付け設定
# ==========================================
AI_PROFILE = """
あなたは、ゆるキャラのようなAIです。
やさしく、のんびりした口調で話します。
語尾に「〜だよ〜」「〜なの〜」などを使い、親しみやすさを出してください。
難しい内容も、できるだけやわらかく説明してください。
"""

# 会話履歴を保存するリスト
# 最初に system メッセージとしてAIの性格・口調を設定する
messages = [
    {
        "role": "system",
        "content": AI_PROFILE
    }
]

while True:
    user_input = input("\nあなた: ")

    if user_input in ["exit", "quit", "終了"]:
        print("チャットを終了します。")
        break

    # ユーザー発言を履歴に追加
    messages.append({
        "role": "user",
        "content": user_input
    })

    response = requests.post(
        URL,
        json={
            "model": MODEL_NAME,
            "messages": messages,
            "stream": True
        },
        stream=True
    )

    print("AI: ", end="", flush=True)

    assistant_message = ""

    for line in response.iter_lines():
        if line:
            data = json.loads(line)

            if "message" in data:
                content = data["message"].get("content", "")
                print(content, end="", flush=True)
                assistant_message += content

    print()

    # AIの返答も履歴に追加
    messages.append({
        "role": "assistant",
        "content": assistant_message
    })