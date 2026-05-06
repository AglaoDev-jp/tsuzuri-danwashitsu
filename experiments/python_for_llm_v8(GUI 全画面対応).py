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

messages = [
    {"role": "system", "content": AI_PROFILE}
]

# =========================
# メイン処理
# =========================
def send_message():
    user_input = entry.get()
    if not user_input:
        return

    entry.delete(0, tk.END)

    chat_area.insert(tk.END, f"あなた: {user_input}\n")
    chat_area.insert(tk.END, "AI: ")
    chat_area.see(tk.END)

    threading.Thread(target=get_ai_response, args=(user_input,), daemon=True).start()


def get_ai_response(user_input):
    global messages

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

                chat_area.after(0, lambda c=content: chat_area.insert(tk.END, c))
                chat_area.after(0, chat_area.see, tk.END)

    chat_area.after(0, lambda: chat_area.insert(tk.END, "\n"))

    messages.append({"role": "assistant", "content": assistant_message})


# =========================
# GUI構築
# =========================
root = tk.Tk()
root.title("AIチャット")

# 🔑 ウィンドウの最小サイズ設定（崩れ防止）
root.minsize(600, 400)

# 🔑 行・列の伸縮設定（これが超重要）
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# =========================
# メインフレーム
# =========================
main_frame = tk.Frame(root)
main_frame.grid(row=0, column=0, sticky="nsew")

# フレーム内の伸縮設定
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(0, weight=1)

# =========================
# チャットエリア
# =========================
chat_area = scrolledtext.ScrolledText(
    main_frame,
    wrap=tk.WORD
)
chat_area.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

# =========================
# 入力エリアフレーム（下部固定）
# =========================
input_frame = tk.Frame(main_frame)
input_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

# 入力欄の横伸び設定
input_frame.grid_columnconfigure(0, weight=1)

# 入力ボックス
entry = tk.Entry(input_frame)
entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

# 送信ボタン
send_button = tk.Button(input_frame, text="送信", command=send_message)
send_button.grid(row=0, column=1)

# Enterキー送信
root.bind("<Return>", lambda event: send_message())

# =========================
# 全画面切り替え（F11）
# =========================
def toggle_fullscreen(event=None):
    root.attributes("-fullscreen", not root.attributes("-fullscreen"))

def end_fullscreen(event=None):
    root.attributes("-fullscreen", False)

root.bind("<F11>", toggle_fullscreen)
root.bind("<Escape>", end_fullscreen)

root.mainloop()