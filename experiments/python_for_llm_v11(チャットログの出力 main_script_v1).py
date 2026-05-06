import requests
import json
import tkinter as tk
from tkinter import scrolledtext, ttk
import threading
from pathlib import Path
from datetime import datetime

MODEL_NAME = "gemma3:1b"
URL = "http://localhost:11434/api/chat"

# =========================
# JSON読み込み（pathlib使用）
# =========================
BASE_DIR = Path(__file__).parent  # スクリプトと同じフォルダ
JSON_PATH = BASE_DIR / "profiles.json"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    AI_PROFILES = json.load(f)

profile_names = list(AI_PROFILES.keys())

# =========================
# ログ出力（pathlib使用）
# =========================
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

def save_chat_log():
    # 現在のチャット欄の内容を取得
    chat_text = chat_area.get("1.0", tk.END).strip()

    if not chat_text:
        chat_area.insert(tk.END, "\n--- 保存するチャットログがありません ---\n")
        return

    # 日時つきファイル名を作成
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    selected = profile_var.get()
    log_path = LOG_DIR / f"chat_log_{now}_{selected}.txt"

    # テキストファイルとして保存
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(chat_text)

    chat_area.insert(tk.END, f"\n--- チャットログを保存しました: {log_path.name} ---\n")
    chat_area.see(tk.END)

# --------------------------------------------
# 最初に使うキャラ
selected_name = profile_names[0]

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

    messages = [
        {
            "role": "system",
            "content": AI_PROFILES[selected]
        }
    ]

    chat_area.insert(tk.END, f"\n--- キャラを「{selected}」に変更しました ---\n")
    chat_area.see(tk.END)

# =========================
# チャット内容の消去
# =========================

def clear_chat():
    global messages

    selected = profile_var.get()

    # 会話履歴を、現在選択中のキャラ設定だけに戻す
    messages = [
        {
            "role": "system",
            "content": AI_PROFILES[selected]
        }
    ]

    # チャット表示欄をすべて削除
    chat_area.delete("1.0", tk.END)

    # 任意：クリアしたことを表示
    chat_area.insert(tk.END, f"--- チャット内容をクリアしました（{selected}）---\n")

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

# キャラ選択
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

# チャットエリア
chat_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD)
chat_area.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

# 入力エリア
input_frame = tk.Frame(main_frame)
input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

input_frame.grid_columnconfigure(0, weight=1)

# 入力ボックス
entry = tk.Entry(input_frame)
entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

# 送信ボタン
send_button = tk.Button(input_frame, text="送信", command=send_message)
send_button.grid(row=0, column=1)

# クリアボタン
clear_button = tk.Button(input_frame, text="クリア", command=clear_chat)
clear_button.grid(row=0, column=2, padx=(5, 0))

# 保存ボタン
save_button = tk.Button(input_frame, text="保存", command=save_chat_log)
save_button.grid(row=0, column=3, padx=(5, 0))

root.bind("<Return>", lambda event: send_message())

root.mainloop()