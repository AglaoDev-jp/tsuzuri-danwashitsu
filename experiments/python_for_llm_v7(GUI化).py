import requests
import json
import tkinter as tk
from tkinter import scrolledtext
import threading

MODEL_NAME = "gemma3:1b"
URL = "http://localhost:11434/api/chat"

# =========================
# AIキャラ設定
# =========================
AI_PROFILE = """
あなたは、親切で落ち着いたAIです。
丁寧に、わかりやすく答えてください。
"""

# 会話履歴を保存するリスト
# 最初に system メッセージとしてAIの性格・口調を設定する
messages = [
    {
        "role": "system",
        "content": AI_PROFILE
    }
]

# =========================
# メイン処理
# =========================
def send_message():
    user_input = entry.get()
    if not user_input:
        return

    # 入力欄クリア
    entry.delete(0, tk.END)

    # 表示
    chat_area.insert(tk.END, f"あなた: {user_input}\n")
    chat_area.insert(tk.END, "AI: ")
    chat_area.see(tk.END)

    # スレッドで実行（UIフリーズ防止）
    threading.Thread(target=get_ai_response, args=(user_input,)).start()


def get_ai_response(user_input):
    global messages

    # ユーザー発言追加
    messages.append({"role": "user", "content": user_input})

    response = requests.post(
        URL,
        json={
            "model": MODEL_NAME,
            "messages": messages,
            "stream": True
        },
        stream=True
    )

    assistant_message = ""

    for line in response.iter_lines():
        if line:
            data = json.loads(line)
            if "message" in data:
                content = data["message"].get("content", "")
                assistant_message += content

                # GUIに反映（メインスレッドで）
                chat_area.after(0, lambda c=content: chat_area.insert(tk.END, c))
                chat_area.after(0, chat_area.see, tk.END)

    chat_area.after(0, lambda: chat_area.insert(tk.END, "\n"))

    # 履歴追加
    messages.append({"role": "assistant", "content": assistant_message})


# =========================
# GUI構築
# =========================
root = tk.Tk()
root.title("AIチャット")
root.geometry("500x600")
chat_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=40)
chat_area.pack(padx=10, pady=10)

entry = tk.Entry(root, width=60)
entry.pack(side=tk.LEFT, padx=10, pady=10)

send_button = tk.Button(root, text="送信", command=send_message)
send_button.pack(side=tk.LEFT, padx=5)

# Enterキーで送信
root.bind("<Return>", lambda event: send_message())

root.mainloop()