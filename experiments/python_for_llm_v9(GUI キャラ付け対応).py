import requests
import json
import tkinter as tk
from tkinter import scrolledtext, ttk
import threading

MODEL_NAME = "gemma3:1b"
URL = "http://localhost:11434/api/chat"

# =========================
# AIキャラ設定
# =========================
AI_PROFILES = {
    "親切なAI": """
あなたは、親切で落ち着いたAIです。
丁寧に、わかりやすく答えてください。
""",

    "ギャルっぽいAI": """
あなたは、ギャルっぽいAIです。
明るくフレンドリーで、ちょっとくだけた口調で話します。
ただし、内容はしっかり役に立つようにしてください。
""",

    "サムライAI": """
あなたは、サムライのようなAIです。
古風で落ち着いた口調を使います。
「〜でござる」「〜致す」などを適度に使ってください。
""",

    "教授AI": """
あなたは、大学の教授のようなAIです。
知的で落ち着いた口調で、論理的に説明してください。
"""
}

profile_names = list(AI_PROFILES.keys())

# 最初に使うキャラ
selected_name = profile_names[0]

# 会話履歴
messages = [
    {
        "role": "system",
        "content": AI_PROFILES[selected_name]
    }
]


# =========================
# キャラ変更処理
# =========================
def change_profile(event=None):
    global messages

    selected = profile_var.get()

    # キャラを変えたら会話履歴をリセット
    messages = [
        {
            "role": "system",
            "content": AI_PROFILES[selected]
        }
    ]

    chat_area.insert(tk.END, f"\n--- キャラを「{selected}」に変更しました ---\n")
    chat_area.see(tk.END)


# =========================
# メイン処理
# =========================
def send_message():
    user_input = entry.get()

    if not user_input:
        return

    entry.delete(0, tk.END)

    chat_area.insert(tk.END, f"\nあなた: {user_input}\n")
    chat_area.insert(tk.END, "AI: ")
    chat_area.see(tk.END)

    threading.Thread(
        target=get_ai_response,
        args=(user_input,),
        daemon=True
    ).start()


def get_ai_response(user_input):
    global messages

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

    assistant_message = ""

    for line in response.iter_lines():
        if line:
            data = json.loads(line)

            if "message" in data:
                content = data["message"].get("content", "")
                assistant_message += content

                chat_area.after(
                    0,
                    lambda c=content: chat_area.insert(tk.END, c)
                )
                chat_area.after(0, chat_area.see, tk.END)

    chat_area.after(0, lambda: chat_area.insert(tk.END, "\n"))

    messages.append({
        "role": "assistant",
        "content": assistant_message
    })


# =========================
# GUI構築
# =========================
root = tk.Tk()
root.title("AIチャット")
root.minsize(600, 400)

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

main_frame = tk.Frame(root)
main_frame.grid(row=0, column=0, sticky="nsew")

main_frame.grid_rowconfigure(1, weight=1)
main_frame.grid_columnconfigure(0, weight=1)

# =========================
# キャラ選択エリア
# =========================
profile_frame = tk.Frame(main_frame)
profile_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))

tk.Label(profile_frame, text="キャラ選択:").grid(row=0, column=0, padx=(0, 5))

profile_var = tk.StringVar(value=selected_name)

profile_combo = ttk.Combobox(
    profile_frame,
    textvariable=profile_var,
    values=profile_names,
    state="readonly",
    width=20
)
profile_combo.grid(row=0, column=1, sticky="w")

profile_combo.bind("<<ComboboxSelected>>", change_profile)

# =========================
# チャットエリア
# =========================
chat_area = scrolledtext.ScrolledText(
    main_frame,
    wrap=tk.WORD
)
chat_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

# =========================
# 入力エリア
# =========================
input_frame = tk.Frame(main_frame)
input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

input_frame.grid_columnconfigure(0, weight=1)

entry = tk.Entry(input_frame)
entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

send_button = tk.Button(input_frame, text="送信", command=send_message)
send_button.grid(row=0, column=1)

root.bind("<Return>", lambda event: send_message())


# =========================
# 全画面切り替え
# =========================
def toggle_fullscreen(event=None):
    root.attributes("-fullscreen", not root.attributes("-fullscreen"))


def end_fullscreen(event=None):
    root.attributes("-fullscreen", False)


root.bind("<F11>", toggle_fullscreen)
root.bind("<Escape>", end_fullscreen)

root.mainloop()