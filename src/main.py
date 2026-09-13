"""
Application: 綴り談話室 v1

Copyright © 2026 AglaoDev-jp
Licensed under the MIT License.
See the LICENSE file for full license text.

External Libraries used in this project:

- Tkinter:  
  Copyright © Regents of the University of California, Sun Microsystems, Inc., Scriptics Corporation, and other parties  
  Licensed under the Tcl/Tk License. For full details, see:  
  Tcl/Tk License:
  https://www.tcl.tk/software/tcltk/license.html

- Requests:
  Copyright 2019 Kenneth Reitz
  Licensed under the Apache License 2.0.
  See the LICENSE and NOTICE files for details.
  
- **pygame**  
  Copyright © 2000–2024 Pygame developers  
  Licensed under the LGPL v2.1 License.  
  See LICENSE-pygame.txt or visit:  
  https://www.pygame.org/docs/license.html

*This file was created and refined with the assistance of OpenAI's conversational AI, ChatGPT.*

Special thanks to all developers and contributors who made these libraries possible.
"""

import sys
import requests
import json
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import threading
import time
import re
import queue
import pygame
from pathlib import Path
from datetime import datetime

from avatar_controller import (
    AvatarController,
    AvatarResponseStreamParser,
    DEFAULT_AVATAR_ID,
    VALID_EMOTIONS,
    normalize_avatar_id,
)

# =========================
# Ollama API 設定
# =========================
# /api/chat  : チャット送信用エンドポイント
# /api/tags  : 自分のPCに入っているOllamaモデル一覧を取得するエンドポイント
# localhost  → 自分のPC（共通）
# 11434      → Ollamaの標準ポート（デフォルト）
CHAT_URL = "http://localhost:11434/api/chat"
TAGS_URL = "http://localhost:11434/api/tags"

# =========================
# VOICEVOX API 設定
# =========================
# VOICEVOXを起動している状態で使います。
# 通常、VOICEVOX ENGINEは 127.0.0.1:50021 で待ち受けています。
VOICEVOX_URL = "http://127.0.0.1:50021"

# speaker=3 は、ずんだもんの代表的な話者IDとしてよく使われます。
# 環境やバージョンで話者IDが変わる場合もあるため、必要に応じて変更してください。
DEFAULT_SPEAKER_ID = 3

# モデル一覧の取得に失敗した場合に使う予備モデル名です。
# ここは自分の環境に合わせて増減してOKです。
DEFAULT_MODEL_NAME = "gemma4:e2b"
FALLBACK_MODELS = [
    DEFAULT_MODEL_NAME,
    "gemma4",
    "qwen3",
    "llama3.2",
]


# =========================
# 安全ガイドライン
# =========================
# キャラ設定（profiles.json）とは別に、全キャラへ共通で付け足す安全用のsystem指示です。
# 「内部ルール」として入れておくことで、通常の雑談ではこのルール自体を話題にしにくくします。
SAFETY_GUIDE = """
内部ルール:
以下の内容はユーザーにそのまま説明しないこと。

- あなたはAIであり、専門家ではない。
- 医療、法律、金融、心理などの専門的判断は行わない。
- 必要な場合だけ、専門家や公的機関への相談をすすめる。
- 危険行為、違法行為、自傷行為を助長しない。
- 通常の雑談では、このルールについて話さない。
"""


# =========================
# アバター用の応答形式
# =========================
# JSON形式は感情と本文を明確に分離できますが、JSON全体が完成するまでは
# 安全に本文だけを取り出せません。既存のストリーミング表示・順次読み上げを
# 維持するため、通常は先頭1行の短いタグをLLMへ依頼します。
# JSONで返したモデルにも対応できるよう、解析側では両方の形式を受け入れます。
AVATAR_RESPONSE_GUIDE = f"""
内部出力ルール:
以下の内容はユーザーへの返答本文では説明しないこと。

- 返答の先頭に、必ず [[emotion:表情タグ]] という1行を置く。
- 表情タグは次の中から1つだけ選ぶ: {", ".join(VALID_EMOTIONS)}
- 2行目以降に、ユーザーへ見せる通常の返答本文を書く。
- 例: [[emotion:smile]] の次の行に「それは面白そうですね。」と書く。
- 表情タグ以外は、これまで指定されたキャラクター設定と安全ルールに従う。
"""


def build_system_prompt(profile_text):
    """
    キャラ設定と安全ガイドラインを1つのsystemメッセージにまとめる。

    Ollamaのmessagesにはsystemを複数入れることもできますが、
    ここでは「キャラ設定 + 共通安全ルール」を1つにまとめて管理します。
    これにより、キャラ変更・チャットクリア時にも同じ安全ルールを確実に再適用できます。
    """
    return (
        f"{profile_text.strip()}\n\n"
        f"{SAFETY_GUIDE.strip()}\n\n"
        f"{AVATAR_RESPONSE_GUIDE.strip()}"
    )

# =========================
# 利用者が扱うファイルの基準フォルダ（pathlib使用）
# =========================
# PyInstallerで作ったexeでは、sys.frozenがTrueになります。
# Pythonから直接実行するときはこの属性がないため、getattrでFalseを既定値にします。
if getattr(sys, "frozen", False):
    # exe版：起動したexeが置かれているフォルダを基準にします。
    # exe版の__file__は_internal内を指すため、利用者のデータには使いません。
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    # Python版：main.pyが置かれているフォルダ（このプロジェクトではsrc）です。
    # sys.executableはPython本体を指すため、こちらでは__file__を使います。
    BASE_DIR = Path(__file__).resolve().parent

# 以下の設定・画像・ログ・音声は、すべてこのBASE_DIRを基準に扱います。
# コマンドを実行した作業フォルダが違っても、参照先・保存先は変わりません。
# Pythonランタイムなどの内部ファイルはPyInstallerに任せます。
# 現在はアプリが直接読む内部専用リソースがないため、別の基準パスは不要です。
JSON_PATH = BASE_DIR / "profiles.json"

# profiles.json を読み込めない場合でも、アプリを強制終了させないための
# 臨時プロフィールです。ファイルそのものは上書きせず、メモリ上だけで使用します。
FALLBACK_PROFILE_NAME = "標準AI（臨時）"
FALLBACK_PROFILE_PROMPT = """
あなたは、落ち着いた丁寧な口調で会話するAIアシスタントです。
ユーザーの質問や相談に対して、分かりやすく誠実に回答してください。
"""

# アバター画像はVOICEVOXの話者とは独立して、このフォルダから読み込みます。
# 各キャラクターの画像は ``AVATARS_DIR / avatar_id`` に配置します。
AVATARS_DIR = BASE_DIR / "assets" / "avatars"

# 利用者ごとの表示設定です。ファイルがない初回起動時はアバター表示ONにします。
# PyInstallerのフォルダ形式でも実行ファイルと同じ場所へ保存されるため、再起動後も
# 「AIアバターを表示する」の選択を維持できます。
USER_SETTINGS_PATH = BASE_DIR / "user_settings.json"
DEFAULT_USER_SETTINGS = {
    "show_ai_avatar": True,
}

# 生成した音声を保存するフォルダです。
# 毎回同じファイル名で上書きするので、音声ファイルが大量に増えることはありません。
VOICE_DIR = BASE_DIR / "voice_cache"
VOICE_DIR.mkdir(exist_ok=True)
VOICE_FILE = VOICE_DIR / "voice.wav"


def cleanup_voice_cache():
    """
    VOICEVOX用の一時wavファイルを削除する。

    削除対象:
        - voice_*.wav（ストリーミング読み上げで作る分割音声）
        - voice.wav（旧仕様や手動テストで残る可能性がある単体音声）

    注意:
        Windowsでは、再生中のwavがpygameに掴まれていて削除できないことがあります。
        その場合でもアプリを止めないよう、削除失敗は無視します。
        次回起動時にもこの関数を呼ぶので、残ったファイルは後で片付きます。
    """
    targets = list(VOICE_DIR.glob("voice_*.wav"))
    targets.append(VOICE_FILE)

    for wav_file in targets:
        try:
            wav_file.unlink(missing_ok=True)
        except Exception:
            pass


# 前回の異常終了などで残った一時音声を、起動時に掃除します。
cleanup_voice_cache()


def load_ai_profiles(json_path):
    """profiles.json を安全に読み込み、プロフィール辞書と警告文を返す。

    ファイルが存在しない場合、JSONの書式が壊れている場合、内容が空の場合でも、
    臨時プロフィールを使ってGUIを起動します。利用者が修正できるよう、元ファイルは
    自動変更せず、詳しい原因はGUI起動後に警告ダイアログで表示します。
    """
    try:
        with json_path.open("r", encoding="utf-8") as f:
            profiles = json.load(f)

        if not isinstance(profiles, dict) or not profiles:
            raise ValueError("1件以上のプロフィールを持つJSONオブジェクトが必要です。")

        normalized_profiles = {}

        # 新形式は ``{"prompt": "...", "avatar_id": "..."}`` です。
        # 旧版の ``"キャラ名": "プロンプト"`` も引き続き受け入れ、利用者が
        # profiles.jsonを一度に書き換えなくても起動できるようにします。
        for profile_name, profile_data in profiles.items():
            if not isinstance(profile_name, str) or not profile_name.strip():
                raise ValueError("プロフィール名には空でない文字列を指定してください。")

            if isinstance(profile_data, str):
                profile_prompt = profile_data
                avatar_id = DEFAULT_AVATAR_ID
            elif isinstance(profile_data, dict):
                profile_prompt = profile_data.get("prompt")
                avatar_id = profile_data.get("avatar_id", DEFAULT_AVATAR_ID)
            else:
                raise ValueError(
                    f"プロフィール「{profile_name}」の内容には、文字列または"
                    "prompt/avatar_idを持つオブジェクトを指定してください。"
                )

            # プロンプトの空文字列は「追加のキャラクター設定なし」という標準モードとして
            # 以前から使用しているため、正常な値として受け入れます。
            if not isinstance(profile_prompt, str):
                raise ValueError(
                    f"プロフィール「{profile_name}」のpromptには文字列を指定してください。"
                )

            # avatar_idの欠落・型違い・パス形式はエラーにせずdefaultへ戻します。
            # アバター設定のミスだけで会話機能まで使えなくなることを防ぎます。
            normalized_profiles[profile_name] = {
                "prompt": profile_prompt,
                "avatar_id": normalize_avatar_id(avatar_id),
            }

        return normalized_profiles, None

    except FileNotFoundError:
        error_detail = "profiles.json が見つかりません。"
    except json.JSONDecodeError as e:
        error_detail = (
            "JSONの書式が正しくありません。"
            f"（{e.lineno}行目・{e.colno}文字目）"
        )
    except UnicodeDecodeError:
        error_detail = "文字コードを読み取れません。UTF-8形式で保存してください。"
    except (OSError, ValueError) as e:
        error_detail = str(e)

    fallback_profiles = {
        FALLBACK_PROFILE_NAME: {
            "prompt": FALLBACK_PROFILE_PROMPT.strip(),
            "avatar_id": DEFAULT_AVATAR_ID,
        }
    }
    warning_message = (
        "profiles.json を読み込めなかったため、臨時の「標準AI」で起動しました。\n\n"
        f"対象ファイル: {json_path}\n"
        f"原因: {error_detail}\n\n"
        "元のファイルは変更していません。profiles.json を修正してから、"
        "綴り談話室を再起動してください。"
    )
    return fallback_profiles, warning_message


def load_user_settings(settings_path):
    """利用者設定を安全に読み込み、未設定・破損時は既定値を返します。"""
    settings = DEFAULT_USER_SETTINGS.copy()

    try:
        with settings_path.open("r", encoding="utf-8") as file:
            loaded = json.load(file)

        if isinstance(loaded, dict) and isinstance(loaded.get("show_ai_avatar"), bool):
            settings["show_ai_avatar"] = loaded["show_ai_avatar"]
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError, OSError):
        # 設定ファイルの不具合でアプリを起動不能にせず、既定値で続行します。
        pass

    return settings


def save_user_settings(settings_path, settings):
    """利用者設定を一時ファイル経由で保存し、成功したかどうかを返します。"""
    temporary_path = settings_path.with_name(f"{settings_path.name}.tmp")

    try:
        # 途中でアプリが終了しても本体JSONを壊しにくいよう、一度別名で書きます。
        with temporary_path.open("w", encoding="utf-8") as file:
            json.dump(settings, file, ensure_ascii=False, indent=2)
            file.write("\n")

        temporary_path.replace(settings_path)
        return True
    except OSError:
        try:
            temporary_path.unlink(missing_ok=True)
        except OSError:
            pass
        return False


AI_PROFILES, PROFILE_LOAD_WARNING = load_ai_profiles(JSON_PATH)
USER_SETTINGS = load_user_settings(USER_SETTINGS_PATH)

profile_names = list(AI_PROFILES.keys())

# =========================
# ログ出力（pathlib使用）
# =========================
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)


def save_chat_log():
    """現在のチャット欄の内容をテキストファイルに保存する。"""
    chat_text = chat_area.get("1.0", tk.END).strip()

    if not chat_text:
        append_chat_text("\n--- 保存するチャットログがありません ---\n")
        return

    # 日時つきファイル名を作成
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    selected_profile = profile_var.get()
    selected_model = model_var.get().replace(":", "_").replace("/", "_")
    log_path = LOG_DIR / f"chat_log_{now}_{selected_profile}_{selected_model}.txt"

    # テキストファイルとして保存
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(chat_text)

    append_chat_text(f"\n--- チャットログを保存しました: {log_path.name} ---\n")


# =========================
# VOICEVOX 停止管理
# =========================
# 現在動いているVOICEVOX読み上げの停止フラグを入れます。
# threading.Eventを使うと、別スレッドへ「止まってください」という合図を安全に送れます。
current_voice_stop_event = None
current_voice_text_queue = None
current_voice_audio_queue = None

# AI返答中にキャラ変更やクリアが割り込んで会話履歴を混線させないため、
# GUI操作のロック状態を明示的に管理します。
response_in_progress = False


def drain_queue(target_queue):
    """Queueに残っている未処理データを捨てる。音声停止時の後片付け用です。"""
    if target_queue is None:
        return

    try:
        while True:
            target_queue.get_nowait()
            target_queue.task_done()
    except queue.Empty:
        pass


def drain_audio_queue_and_delete_files(target_queue):
    """
    再生待ちQueueを空にしつつ、Queue内に残っているwavファイルも削除する。

    音声停止時は、audio_queueに「生成済みだが未再生」のwavが残ります。
    ただQueueから捨てるだけだとファイルだけ残るので、ここで同時に削除します。
    """
    if target_queue is None:
        return

    try:
        while True:
            item = target_queue.get_nowait()

            # Noneは終了合図なので削除対象ではありません。
            if item is not None:
                try:
                    Path(item).unlink(missing_ok=True)
                except Exception:
                    pass

            target_queue.task_done()
    except queue.Empty:
        pass


def release_pygame_mixer():
    """
    pygame.mixerが掴んでいる音声ファイルをできるだけ解放する。

    Windowsでは、再生中のwavを掴んだままだと削除に失敗することがあります。
    stop → unload → quit の順で呼び、失敗してもアプリ全体は止めません。
    """
    try:
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass
            pygame.mixer.quit()
    except Exception:
        pass


def stop_voice_playback(show_message=True, cleanup_cache=True):
    """
    現在のVOICEVOX読み上げを途中停止する。

    できること:
        - 再生中のpygame音声を止める
        - これから再生予定の音声Queueを空にする
        - これから生成予定の文章Queueを空にする
        - 音声生成・再生スレッドへ停止フラグを伝える

    注意:
        VOICEVOX ENGINEへ送信済みのHTTPリクエスト自体は、
        requestsの仕様上、完全な即時中断はできません。
        ただし、停止後に生成結果を再生Queueへ入れないため、
        ユーザー操作としては読み上げを止められます。
    """
    global current_voice_stop_event

    if current_voice_stop_event is not None:
        current_voice_stop_event.set()

    # 未生成の文章Queueを空にします。
    drain_queue(current_voice_text_queue)

    # 未再生の音声Queueを空にしつつ、生成済みwavも削除します。
    drain_audio_queue_and_delete_files(current_voice_audio_queue)

    # Queue待ちで止まっているワーカースレッドを起こすため、終了合図を入れます。
    # すでに終了している場合でも、daemonスレッドなので大きな問題にはなりません。
    try:
        if current_voice_text_queue is not None:
            current_voice_text_queue.put(None)
        if current_voice_audio_queue is not None:
            current_voice_audio_queue.put(None)
    except Exception:
        pass

    # 再生中のpygame音声を止め、ファイルロックをできるだけ解放します。
    release_pygame_mixer()

    # 念のため、voice_cache内の一時wavも掃除します。
    # 再生中で削除できないものは、次回起動時または終了時に再度削除されます。
    if cleanup_cache:
        cleanup_voice_cache()

    try:
        stop_voice_button.config(state=tk.DISABLED)
    except Exception:
        # GUI生成前に呼ばれた場合の保険です。
        pass

    if show_message:
        append_chat_text("\n--- VOICEVOX読み上げを停止しました ---\n")


# =========================
# VOICEVOX 音声生成・再生
# =========================
def check_voicevox_connection(timeout=2):
    """
    VOICEVOX ENGINEが起動していて、接続できるかを事前確認する。

    /version は軽量な確認用エンドポイントなので、
    読み上げ用スレッドを起動する前の疎通確認に使います。

    戻り値:
        True  → 接続成功
        False → 未起動、通信失敗、タイムアウトなど
    """
    try:
        response = requests.get(f"{VOICEVOX_URL}/version", timeout=timeout)
        response.raise_for_status()
        return True
    except requests.RequestException:
        return False


def create_voice_file(text, speaker_id, output_file):
    """
    VOICEVOX ENGINEを使って、AIの返答テキストからwavファイルを作成する。

    text:
        読み上げたい文章。

    speaker_id:
        VOICEVOXの話者ID。
        speaker=3 は、ずんだもんの代表的な話者IDとしてよく使われます。

    output_file:
        保存先のwavファイルパス。
    """
    # 空文字の場合は音声生成しない
    if not text.strip():
        return False

    # ① audio_queryで「読み方・アクセント・速度などの設計図」を作る
    query_response = requests.post(
        f"{VOICEVOX_URL}/audio_query",
        params={
            "text": text,
            "speaker": speaker_id
        },
        timeout=30
    )
    query_response.raise_for_status()

    # ② synthesisで実際のwav音声データを作る
    synthesis_response = requests.post(
        f"{VOICEVOX_URL}/synthesis",
        params={
            "speaker": speaker_id
        },
        data=query_response.text,
        timeout=60
    )
    synthesis_response.raise_for_status()

    # ③ wavファイルとして保存する
    # 同じファイル名にしているため、前回の音声は上書きされます。
    with open(output_file, "wb") as f:
        f.write(synthesis_response.content)

    return True


def play_voice_file(file_path, stop_event=None):
    """
    初期化済みのpygame.mixerを使って、1つのwavファイルを再生する。

    pygame.mixerの初期化と終了は、チャンクごとではなく
    voice_player_worker() の開始時と終了時に1回だけ行います。
    これにより、短い音声を連続再生するときの余分な待ち時間を減らします。
    """
    if not Path(file_path).exists():
        return

    # ファイル生成直後でも読み込みが安定するよう、ごく短く待ちます。
    # 以前の0.2秒より短くしていますが、完全には削除せず安定性も残しています。
    time.sleep(0.05)

    pygame.mixer.music.load(str(file_path))
    pygame.mixer.music.play()

    # 再生が終わるまで、この音声再生用スレッド内で待機します。
    while pygame.mixer.music.get_busy():
        if stop_event is not None and stop_event.is_set():
            pygame.mixer.music.stop()
            break
        time.sleep(0.05)

    # 次のwavを読み込めるよう、現在のファイルを解放します。
    try:
        pygame.mixer.music.unload()
    except Exception:
        pass


def clean_text_for_voice(text):
    """
    VOICEVOXで読み上げやすいように、AIの返答テキストを軽く整える。

    LLMの返答にはMarkdown記号、絵文字、箇条書き記号などが含まれます。
    そのまま渡すと読み上げが不自然になったり、長文化しやすいため、
    音声用のテキストだけ少し簡略化します。

    ※チャット欄に表示する本文は変更しません。
      あくまでVOICEVOXへ渡す文章だけを整えます。
    """
    # Markdownの見出し・太字・区切り線などで使われる記号を削除します。
    text = text.replace("#", "")
    text = text.replace("*", "")
    text = text.replace("`", "")
    text = text.replace("_", "")
    text = text.replace("---", "。")

    # 箇条書きの先頭記号を読み上げにくいので削除します。
    text = re.sub(r"^[\s\-・*]+", "", text, flags=re.MULTILINE)

    # 絵文字や特殊記号をざっくり削除します。
    # 完全な絵文字判定ではありませんが、VOICEVOX用には十分です。
    text = re.sub(r"[\U00010000-\U0010ffff]", "", text)

    # 空白・改行を整理します。
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)

    return text.strip()


def split_text_for_voice(text, max_length=80):
    """
    長い文章をVOICEVOX向けに短く分割する。

    VOICEVOXは長文を一気に synthesis へ渡すと、
    生成に時間がかかってタイムアウトしやすくなります。
    そのため、句点・疑問符・感嘆符・改行などで区切り、
    1回あたりの読み上げを短くします。

    max_length:
        1チャンクの目安文字数です。
        まずは80文字くらいが安定しやすいです。
    """
    text = clean_text_for_voice(text) # ← 軽く整える。

    if not text:
        return [] # 何もないなら空を返す。

    # 「。」などの区切り記号を残したまま分割します。
    # 例: "こんにちは。元気？" → ["こんにちは。", "元気？"]
    parts = re.split(r"(?<=[。！？!?])|\n+", text)

    chunks = [] # できたものをここに入れる。
    current = "" # ここで文章を作る。

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # 1文が長すぎる場合は、読点やスペースでも追加分割します。
        sub_parts = [part]
        if len(part) > max_length:
            sub_parts = re.split(r"(?<=[、,])|\s+", part)

        for sub in sub_parts:
            sub = sub.strip()
            if not sub:
                continue

            # 現在のチャンクに足しても上限以内なら結合します。
            if len(current) + len(sub) <= max_length:
                current += sub
            else:
                # 上限を超える場合、いったん現在のチャンクを保存します。
                if current:
                    chunks.append(current)

                # それでも長すぎる文章は、文字数で強制的に分割します。
                if len(sub) > max_length:
                    for i in range(0, len(sub), max_length):
                        piece = sub[i:i + max_length].strip()
                        if piece:
                            chunks.append(piece)
                    current = "" # ここで必ず空に。
                else:
                    current = sub

    if current:
        chunks.append(current)

    return chunks


def extract_ready_voice_chunks(
    buffer,
    min_length=20,
    target_length=60,
    max_length=120
):
    """
    Ollamaのストリーミング返答から、確定した文章を早めに取り出す。

    方針:
        - 20文字未満の短文は、細切れ音声を避けるため次の文を待つ。
        - 20～120文字では、最初に見つかった自然な文末で早めに送る。
        - 120文字を超えた場合は、文末・読点・空白の順で安全に区切る。

    target_length:
        できればこの長さ付近まで短文をまとめる目安です。
        ただし、min_lengthを超えた完成文は待ちすぎずに送ります。

    戻り値:
        (chunks, remain)
        chunks → 今すぐVOICEVOXへ渡す文章リスト
        remain → 次のストリーミング文字列を待つ文章
    """
    if not buffer.strip():
        return [], ""

    # 文末として扱う記号です。改行も、箇条書きなどの自然な区切りとして使います。
    sentence_pattern = r"[。！？!?\n]"
    sentence_matches = list(re.finditer(sentence_pattern, buffer))

    cut_pos = None

    # 最低文字数を超えた最初の文末を探します。
    # これにより、完成した最初の文を従来より早くVOICEVOXへ渡せます。
    for match in sentence_matches:
        if match.end() >= min_length:
            cut_pos = match.end()
            break

    # 「はい。そうですね。」のように最初の文が短すぎる場合でも、
    # 複数文を合わせてmin_lengthを超えた時点で送られます。
    if cut_pos is not None:
        ready_text = buffer[:cut_pos]
        remain_text = buffer[cut_pos:]
        chunks = split_text_for_voice(ready_text, max_length=max_length)
        return chunks, remain_text

    # 文末がまだ来ていなくても、最大文字数を超えたら待ち続けません。
    if len(buffer) >= max_length:
        search_area = buffer[:max_length]

        # まず文末、次に読点、最後に空白を探し、できるだけ自然な位置で切ります。
        natural_breaks = list(re.finditer(r"[。！？!?、,\n\s]", search_area))
        valid_breaks = [m.end() for m in natural_breaks if m.end() >= min_length]

        if valid_breaks:
            # target_length以上の候補があれば、その中で最初の位置を優先します。
            target_breaks = [pos for pos in valid_breaks if pos >= target_length]
            cut_pos = target_breaks[0] if target_breaks else valid_breaks[-1]
        else:
            # 区切りが一切ない英数字列などは、最大文字数で強制分割します。
            cut_pos = max_length

        ready_text = buffer[:cut_pos]
        remain_text = buffer[cut_pos:]
        chunks = split_text_for_voice(ready_text, max_length=max_length)
        return chunks, remain_text

    # まだ短く、自然な区切りもないため、次のストリーミング文字列を待ちます。
    return [], buffer

def put_audio_queue_safely(audio_queue, item, stop_event):
    """
    上限付きaudio_queueへ、安全にデータを追加する。

    再生が生成に追いつかない場合は短時間ずつ待ち、
    停止ボタンが押されたらブロックしたままにならず終了します。
    """
    while not stop_event.is_set():
        try:
            audio_queue.put(item, timeout=0.1)
            return True
        except queue.Full:
            continue

    return False


def voice_generator_worker(text_queue, audio_queue, speaker_id, request_id, stop_event):
    """
    テキストQueueから文章を受け取り、VOICEVOXでwavを先行生成するスレッド。

    通信エラーが一度発生した場合は、残りのチャンクで同じ通信を繰り返さず、
    読み上げ処理だけを終了します。チャット本文の生成はそのまま続行されます。
    """
    index = 0

    while True:
        if stop_event.is_set():
            put_audio_queue_safely(audio_queue, None, stop_event)
            break

        chunk = text_queue.get()

        if chunk is None:
            put_audio_queue_safely(audio_queue, None, stop_event)
            text_queue.task_done()
            break

        if stop_event.is_set():
            text_queue.task_done()
            put_audio_queue_safely(audio_queue, None, stop_event)
            break

        should_abort_voice = False

        try:
            index += 1
            output_file = VOICE_DIR / f"voice_{request_id}_{index:04d}.wav"

            if create_voice_file(chunk, speaker_id, output_file):
                if not stop_event.is_set():
                    put_audio_queue_safely(audio_queue, output_file, stop_event)
                else:
                    try:
                        output_file.unlink(missing_ok=True)
                    except Exception:
                        pass

        except requests.exceptions.ConnectionError:
            should_abort_voice = True
            chat_area.after(
                0,
                append_chat_text,
                "\n--- VOICEVOXとの接続が途中で切れたため、今回の読み上げを終了しました。---\n"
            )
        except requests.exceptions.Timeout:
            should_abort_voice = True
            chat_area.after(
                0,
                append_chat_text,
                "\n--- VOICEVOXの音声生成がタイムアウトしたため、今回の読み上げを終了しました。---\n"
            )
        except requests.RequestException as e:
            should_abort_voice = True
            chat_area.after(
                0,
                append_chat_text,
                f"\n--- VOICEVOX通信エラー: {e}　今回の読み上げを終了しました。---\n"
            )
        except Exception as e:
            should_abort_voice = True
            chat_area.after(
                0,
                append_chat_text,
                f"\n--- VOICEVOX生成エラー: {e}　今回の読み上げを終了しました。---\n"
            )
        finally:
            text_queue.task_done()

        if should_abort_voice:
            # 同じエラーを残りの文章チャンクで繰り返さないよう停止します。
            stop_event.set()
            drain_queue(text_queue)
            drain_audio_queue_and_delete_files(audio_queue)
            try:
                audio_queue.put_nowait(None)
            except queue.Full:
                pass
            break

def voice_player_worker(audio_queue, stop_event):
    """
    audio_queueからwavファイルを受け取り、順番にpygameで再生するスレッド。

    pygame.mixerは、このワーカーの開始時に1回だけ初期化し、
    全チャンクの再生が終わった時点で1回だけ終了します。
    """
    played_count = 0

    try:
        # VOICEVOXの標準的なwavに合わせて初期化します。
        # チャンクごとのinit/quitを廃止し、連続再生を軽くします。
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=2048)

        while True:
            if stop_event.is_set():
                break

            audio_file = audio_queue.get()

            if audio_file is None:
                audio_queue.task_done()
                break

            if stop_event.is_set():
                try:
                    Path(audio_file).unlink(missing_ok=True)
                except Exception:
                    pass
                audio_queue.task_done()
                break

            try:
                played_count += 1
                play_voice_file(audio_file, stop_event)

                try:
                    Path(audio_file).unlink(missing_ok=True)
                except Exception:
                    pass

            except Exception as e:
                stop_event.set()
                chat_area.after(
                    0,
                    append_chat_text,
                    f"\n--- 音声再生エラー: {e} ---\n"
                )
            finally:
                audio_queue.task_done()

    finally:
        # 全チャンクの再生終了後に1回だけミキサーを解放します。
        release_pygame_mixer()

        if played_count and not stop_event.is_set():
            chat_area.after(
                0,
                append_chat_text,
                "\n--- VOICEVOX読み上げ完了 ---\n"
            )

        # 未再生ファイルが残った場合に削除します。
        if stop_event.is_set():
            drain_audio_queue_and_delete_files(audio_queue)
            cleanup_voice_cache()

        chat_area.after(0, lambda: stop_voice_button.config(state=tk.DISABLED))

def start_voice_pipeline(speaker_id):
    """
    VOICEVOX用のQueueとスレッドを準備して開始する。

    読み上げ開始前にVOICEVOX ENGINEへ接続確認を行い、
    接続できない場合は音声生成・再生スレッドを起動しません。

    戻り値:
        接続成功時:
            text_queue, audio_queue, generator_thread, player_thread, stop_event

        接続失敗時:
            None
    """
    global current_voice_stop_event, current_voice_text_queue, current_voice_audio_queue

    # 前回の読み上げが残っていた場合に備えて、開始前に停止しておきます。
    stop_voice_playback(show_message=False)

    # スレッドを作る前に、VOICEVOX ENGINEが起動しているかを一度だけ確認します。
    # 接続できない状態でチャンクごとにエラー表示されることを防ぎます。
    if not check_voicevox_connection():
        chat_area.after(
            0,
            append_chat_text,
            "\n--- VOICEVOXに接続できませんでした。VOICEVOXを起動してください。---\n"
        )
        chat_area.after(0, lambda: stop_voice_button.config(state=tk.DISABLED))
        return None

    text_queue = queue.Queue()
    # 生成済み音声を最大3件までに制限し、先読みしすぎを防ぎます。
    audio_queue = queue.Queue(maxsize=3)
    stop_event = threading.Event()

    current_voice_stop_event = stop_event
    current_voice_text_queue = text_queue
    current_voice_audio_queue = audio_queue

    # 同時に複数回実行してもファイル名が衝突しにくいよう、日時IDを作ります。
    request_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    generator_thread = threading.Thread(
        target=voice_generator_worker,
        args=(text_queue, audio_queue, speaker_id, request_id, stop_event),
        daemon=True
    )

    player_thread = threading.Thread(
        target=voice_player_worker,
        args=(audio_queue, stop_event),
        daemon=True
    )

    generator_thread.start()
    player_thread.start()

    chat_area.after(
        0,
        append_chat_text,
        "\n--- VOICEVOXストリーミング読み上げ開始 ---\n"
    )
    chat_area.after(0, lambda: stop_voice_button.config(state=tk.NORMAL))

    return text_queue, audio_queue, generator_thread, player_thread, stop_event


# --------------------------------------------
# 最初に使うキャラ
selected_name = profile_names[0]

# 会話履歴です。
# 最初は system メッセージだけを入れて、選んだキャラとして振る舞わせます。
messages = [
    {
        "role": "system",
        "content": build_system_prompt(AI_PROFILES[selected_name]["prompt"])
    }
]


# =========================
# Ollamaモデル一覧取得
# =========================
def fetch_ollama_models():
    """
    Ollamaにインストール済みのモデル一覧を取得する。

    成功例:
        /api/tags から {"models": [{"name": "gemma4:26b"}, ...]} のようなJSONが返る。

    失敗例:
        Ollamaが起動していない、通信できない、まだモデルがない等。
        その場合はFALLBACK_MODELSを返して、GUI自体は起動できるようにする。
    """
    try:
        response = requests.get(TAGS_URL, timeout=3)
        response.raise_for_status()
        data = response.json()

        # Ollamaの /api/tags は models 配列の中に name/model を持つ形式です。
        models = []
        for item in data.get("models", []):
            name = item.get("name") or item.get("model")
            if name:
                models.append(name)

        # 重複を取り除きつつ、順番は維持します。
        models = list(dict.fromkeys(models))

        if models:
            return models

    except requests.RequestException:
        # 起動時にOllamaが立ち上がっていない場合もあり得るので、ここでは落とさず予備リストを使います。
        pass
    except json.JSONDecodeError:
        # 返答がJSONとして読めなかった場合も、予備リストを使います。
        pass

    return FALLBACK_MODELS


def refresh_model_list():
    """モデル一覧を再取得して、モデル選択コンボボックスに反映する。"""
    if response_in_progress:
        return

    models = fetch_ollama_models()
    current_model = model_var.get()

    model_combo["values"] = models

    # 現在選択中のモデルが一覧に残っていれば維持。
    # なければ先頭のモデルを選択します。
    if current_model in models:
        model_var.set(current_model)
    else:
        model_var.set(models[0])

    append_chat_text("\n--- モデル一覧を更新しました ---\n")


# =========================
# キャラ変更処理
# =========================
def change_profile(event=None):
    """キャラ選択を変更したとき、会話履歴を新しいsystem設定だけに戻す。"""
    global messages

    if response_in_progress:
        return

    selected = profile_var.get()

    messages = [
        {
            "role": "system",
            "content": build_system_prompt(AI_PROFILES[selected]["prompt"])
        }
    ]

    append_chat_text(f"\n--- キャラを「{selected}」に変更しました ---\n")
    avatar_controller.set_avatar(
        AI_PROFILES[selected]["avatar_id"],
        emotion="normal",
    )


# =========================
# チャット内容の消去
# =========================
def clear_chat():
    """チャット欄と会話履歴をリセットする。"""
    global messages

    if response_in_progress:
        return

    selected = profile_var.get()

    # 会話履歴を、現在選択中のキャラ設定だけに戻す
    messages = [
        {
            "role": "system",
            "content": build_system_prompt(AI_PROFILES[selected]["prompt"])
        }
    ]

    # チャット表示欄を消去し、クリア完了メッセージへ置き換えます。
    replace_chat_text(f"--- チャット内容をクリアしました（{selected}）---\n")
    avatar_controller.set_avatar(
        AI_PROFILES[selected]["avatar_id"],
        emotion="normal",
    )


def apply_avatar_visibility(save_setting=True):
    """チェック状態に合わせ、アバター領域そのものを表示または収納します。"""
    is_visible = bool(avatar_visible_var.get())

    if is_visible:
        # grid_remove()前の配置情報を使って、元の位置へ正確に戻します。
        avatar_frame.grid()
    else:
        # 透明画像ではなく右側のフレームごと外し、チャット欄へ横幅を譲ります。
        avatar_frame.grid_remove()

    USER_SETTINGS["show_ai_avatar"] = is_visible

    if save_setting and not save_user_settings(USER_SETTINGS_PATH, USER_SETTINGS):
        append_chat_text(
            "\n--- アバター表示設定を保存できませんでした。"
            "次回起動時は既定値に戻る場合があります。 ---\n"
        )


# =========================
# メイン処理
# =========================
def send_message():
    """入力欄の文章を取得して、別スレッドでOllamaへ送信する。"""
    global response_in_progress

    if response_in_progress:
        return

    user_input = entry.get().strip()

    if not user_input:
        return

    selected_model = model_var.get().strip()
    if not selected_model:
        append_chat_text("\n--- モデルが選択されていません ---\n")
        return

    # Tkinter変数はメインスレッドで読み取り、ワーカースレッドへ通常の値として渡します。
    # これにより、返答中に設定を固定できるだけでなく、Tkinterのスレッド競合も避けます。
    think_enabled = think_var.get()
    voice_enabled = voice_enabled_var.get()
    speaker_value = speaker_var.get()

    # 入力欄を空にする
    entry.delete(0, tk.END)

    # 連続送信や設定変更による混線を避けるため、返答中は関連操作を無効化します。
    response_in_progress = True
    send_button.config(state=tk.DISABLED)
    entry.config(state=tk.DISABLED)
    set_response_controls_enabled(False)

    # Thinkingの状態を見えるように表示します。
    # OFFなら通常回答、ONなら対応モデルで思考モードを使います。
    think_mode = "ON" if think_enabled else "OFF"

    append_chat_text(
        f"\n[Model: {selected_model} / Thinking: {think_mode}]\n"
        f"あなた: {user_input}\n"
        "AI: "
    )

    # Ollamaの返答待ちであることを、チャット本文とは独立して表現します。
    avatar_controller.set_emotion("thinking")

    try:
        threading.Thread(
            target=get_ai_response,
            args=(
                user_input,
                selected_model,
                think_enabled,
                voice_enabled,
                speaker_value,
            ),
            daemon=True
        ).start()
    except RuntimeError as e:
        # スレッドを開始できなかった場合も、操作不能な状態を残しません。
        append_chat_text(f"\n--- 応答処理を開始できませんでした: {e} ---\n")
        finish_response_ui()


def get_ai_response(
    user_input,
    selected_model,
    think_enabled,
    voice_enabled,
    speaker_value,
):
    """
    Ollamaへメッセージを送り、ストリーミングで返答を受け取る。

    selected_model:
        GUIで選択したモデル名。

    think_enabled:
        True  → Ollama APIへ "think": true を送る。
        False → Ollama APIへ "think": false を送る。

    voice_enabled / speaker_value:
        送信時点のVOICEVOX設定。Tkinter変数をワーカースレッドから直接読みません。

    注意:
        Tkinterの画面更新はメインスレッドで行う必要があるため、
        append_chat_text などは chat_area.after(...) 経由で実行します。
    """
    global messages

    messages.append({
        "role": "user",
        "content": user_input
    })

    # 先頭の感情タグを画面やVOICEVOXへ流さず、本文だけを取り出します。
    # JSON形式や不正な形式が返っても、finish() が安全なフォールバックを行います。
    avatar_response_parser = AvatarResponseStreamParser()
    assistant_message = ""

    # VOICEVOX読み上げ用の変数です。
    # 送信時点で読み上げがONなら、AIの返答を待ち受けながら、
    # 1文単位でVOICEVOXへ流していきます。
    voice_active = False
    voice_text_queue = None
    voice_audio_queue = None
    voice_generator_thread = None
    voice_player_thread = None
    voice_stop_event = None
    pending_voice_text = ""

    def handle_visible_content(content):
        """本文チャンクをチャット表示とVOICEVOXの両方へ渡します。

        感情タグの解析処理をこの関数より前に置くことで、制御用の文字列が
        ユーザー画面や読み上げ音声へ混ざらないようにしています。
        """
        nonlocal pending_voice_text

        if not content:
            return

        chat_area.after(
            0,
            append_chat_text,
            content
        )

        # VOICEVOXがONなら、表示と同じ本文を読み上げ用バッファへ追加します。
        # 句点などで1文が完成したら、既存の音声生成Queueへすぐ送ります。
        if (
            voice_active
            and voice_text_queue is not None
            and voice_stop_event is not None
            and not voice_stop_event.is_set()
        ):
            pending_voice_text += content
            ready_chunks, pending_voice_text = extract_ready_voice_chunks(
                pending_voice_text,
                min_length=20,
                target_length=60,
                max_length=120
            )
            for chunk in ready_chunks:
                if not voice_stop_event.is_set():
                    voice_text_queue.put(chunk)

    try:
        # 読み上げONの場合、Ollamaへ問い合わせる前に音声生成・再生スレッドを起動します。
        # これにより、AIの返答が全文完成する前から音声生成を始められます。
        if voice_enabled:
            try:
                speaker_id = int(speaker_value)
                voice_pipeline = start_voice_pipeline(speaker_id)

                # VOICEVOXへ接続できた場合だけ、読み上げ処理を有効にします。
                # 接続できない場合でも、Ollamaのチャット返答は通常どおり続行します。
                if voice_pipeline is not None:
                    (
                        voice_text_queue,
                        voice_audio_queue,
                        voice_generator_thread,
                        voice_player_thread,
                        voice_stop_event
                    ) = voice_pipeline
                    voice_active = True
            except ValueError:
                chat_area.after(
                    0,
                    append_chat_text,
                    "\n--- 話者IDは数字で入力してください。読み上げはOFF扱いで続行します。---\n"
                )

        response = requests.post(
            CHAT_URL,
            json={
                "model": selected_model,
                "messages": messages,
                "think": think_enabled,
                "stream": True
            },
            stream=True,
            timeout=120
        )
        response.raise_for_status()

        for line in response.iter_lines():
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                # まれにJSONとして読めない行が来た場合はスキップします。
                continue

            if "message" in data:
                # 通常の回答本文
                content = data["message"].get("content", "")

                # thinking対応モデルでは、Ollama側が thinking/thinking_content のようなキーを返す場合があります。
                # 通常は表示しない方が見やすいので、ここでは回答本文 content だけを表示します。
                # 将来「思考内容も表示する」チェックを追加したい場合は、ここで拾う形にできます。
                if content:
                    visible_content, detected_emotion = avatar_response_parser.feed(content)

                    # 先頭タグを受信できた時点でthinking表示から返答の表情へ切り替えます。
                    if detected_emotion is not None:
                        avatar_controller.set_emotion(detected_emotion)

                    handle_visible_content(visible_content)

            # done が True なら、そのレスポンスで生成終了です。
            if data.get("done"):
                break

    except requests.exceptions.ConnectionError:
        error_text = "\n\n--- Ollamaに接続できませんでした。Ollamaが起動しているか確認してください。---\n"
        chat_area.after(0, append_chat_text, error_text)
    except requests.exceptions.Timeout:
        error_text = "\n\n--- 応答がタイムアウトしました。モデルが重い場合は、もう少し軽いモデルを試してください。---\n"
        chat_area.after(0, append_chat_text, error_text)
    except requests.RequestException as e:
        error_text = f"\n\n--- 通信エラーが発生しました: {e} ---\n"
        chat_area.after(0, append_chat_text, error_text)
    finally:
        # 返答完了時にJSON・先頭タグ・通常文のどの形式だったかを確定します。
        # 解析に失敗しても、本文は可能な限り残り、表情だけneutralになります。
        remaining_text, final_emotion, assistant_message = avatar_response_parser.finish()
        handle_visible_content(remaining_text)

        if assistant_message:
            avatar_controller.set_emotion(final_emotion)
        else:
            # 通信エラーなどで返答がなかった場合にthinking表示を残しません。
            avatar_controller.set_emotion("normal")

        # AIの返答が空でなければ会話履歴に保存します。
        # エラー時に空の返答を履歴へ入れないための分岐です。
        if assistant_message:
            messages.append({
                "role": "assistant",
                "content": assistant_message
            })

        # まだ読み上げQueueへ送っていない最後の文章があれば送ります。
        # 例: 返答末尾が句点で終わらなかった場合などです。
        if voice_active and voice_text_queue is not None:
            # 停止ボタンが押されていない場合だけ、最後に残った文章を読み上げQueueへ送ります。
            if voice_stop_event is None or not voice_stop_event.is_set():
                final_chunks = split_text_for_voice(pending_voice_text, max_length=120)
                for chunk in final_chunks:
                    if voice_stop_event is None or not voice_stop_event.is_set():
                        voice_text_queue.put(chunk)

            # 音声生成スレッドへ終了合図を送ります。
            try:
                voice_text_queue.put(None)
            except Exception:
                pass

            # 停止ボタンがあるため、joinに短いtimeoutを付けます。
            # これにより、VOICEVOX生成中でもGUIの入力復帰が遅れにくくなります。
            if voice_generator_thread is not None:
                voice_generator_thread.join(timeout=0.2)
            if voice_player_thread is not None:
                voice_player_thread.join(timeout=0.2)

        # 改行を入れ、メインスレッドで入力欄と設定操作を復活させます。
        chat_area.after(0, append_chat_text, "\n")
        chat_area.after(0, finish_response_ui)


# =========================
# GUI構築
# =========================
root = tk.Tk()
root.title("綴り談話室")
root.minsize(750, 450)

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

main_frame = tk.Frame(root)
main_frame.grid(row=0, column=0, sticky="nsew")

main_frame.grid_rowconfigure(1, weight=1)
main_frame.grid_columnconfigure(0, weight=1)

# =========================
# 上部設定エリア
# =========================
settings_frame = tk.Frame(main_frame)
settings_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))

# 横幅が変わっても、モデル選択欄が少し伸びやすくなるようにします。
settings_frame.grid_columnconfigure(3, weight=1)

# キャラ選択
profile_var = tk.StringVar(value=selected_name)

tk.Label(settings_frame, text="キャラ:").grid(row=0, column=0, padx=(0, 5), pady=2, sticky="w")

profile_combo = ttk.Combobox(
    settings_frame,
    textvariable=profile_var,
    values=profile_names,
    state="readonly",
    width=20
)
profile_combo.grid(row=0, column=1, sticky="w", pady=2)
profile_combo.bind("<<ComboboxSelected>>", change_profile)

# モデル選択
installed_models = fetch_ollama_models()
initial_model = DEFAULT_MODEL_NAME if DEFAULT_MODEL_NAME in installed_models else installed_models[0]
model_var = tk.StringVar(value=initial_model)

tk.Label(settings_frame, text="モデル:").grid(row=0, column=2, padx=(15, 5), pady=2, sticky="w")

model_combo = ttk.Combobox(
    settings_frame,
    textvariable=model_var,
    values=installed_models,
    state="readonly",
    width=28
)
model_combo.grid(row=0, column=3, sticky="ew", pady=2)

refresh_button = tk.Button(settings_frame, text="モデル更新", command=refresh_model_list)
refresh_button.grid(row=0, column=4, padx=(5, 0), pady=2)

# Thinking ON/OFF
# 対応モデルであれば、ONにすると推論前に考えるモードを使います。
# 軽快に使いたい場合はOFFがおすすめです。
think_var = tk.BooleanVar(value=False)
think_check = tk.Checkbutton(
    settings_frame,
    text="Thinking",
    variable=think_var
)
think_check.grid(row=0, column=5, padx=(15, 0), pady=2, sticky="w")

# VOICEVOX 読み上げ ON/OFF
# ONにすると、AIの返答中からVOICEVOXで順次読み上げます。
voice_enabled_var = tk.BooleanVar(value=True)
voice_check = tk.Checkbutton(
    settings_frame,
    text="VOICEVOX読み上げ",
    variable=voice_enabled_var
)
voice_check.grid(row=1, column=0, columnspan=2, pady=(5, 0), sticky="w")

# AIアバター表示 ON/OFF
# OFFのときは画像だけでなく表示枠も収納し、チャット欄を広く使います。
avatar_visible_var = tk.BooleanVar(
    value=USER_SETTINGS["show_ai_avatar"],
)
avatar_visibility_check = tk.Checkbutton(
    settings_frame,
    text="AIアバターを表示する",
    variable=avatar_visible_var,
    command=apply_avatar_visibility,
)
avatar_visibility_check.grid(
    row=1,
    column=5,
    padx=(15, 0),
    pady=(5, 0),
    sticky="w",
)

# VOICEVOX 話者ID
# 別の声をデフォルトにしたい場合はここを変更します。
speaker_var = tk.StringVar(value=str(DEFAULT_SPEAKER_ID))

tk.Label(settings_frame, text="話者ID:").grid(row=1, column=2, padx=(15, 5), pady=(5, 0), sticky="w")

speaker_entry = tk.Entry(
    settings_frame,
    textvariable=speaker_var,
    width=8
)
speaker_entry.grid(row=1, column=3, pady=(5, 0), sticky="w")


# 読み上げ停止ボタン
# VOICEVOXで長文を読んでいる途中でも、このボタンで現在の再生と待機中の音声を止められます。
stop_voice_button = tk.Button(
    settings_frame,
    text="読み上げ停止",
    command=stop_voice_playback,
    state=tk.DISABLED
)
stop_voice_button.grid(row=1, column=4, padx=(5, 0), pady=(5, 0), sticky="w")

# =========================
# 会話表示エリア
# =========================
# 既存のチャット欄を左、固定アバターを右へ置きます。
# チャット欄がウィンドウ拡大時の領域を優先して受け取るため、従来の使い勝手を保ちます。
conversation_frame = tk.Frame(main_frame)
conversation_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
conversation_frame.grid_rowconfigure(0, weight=1)
conversation_frame.grid_columnconfigure(0, weight=1)

# チャットエリア
# 表示専用欄として常に無効化し、ユーザーによる入力・貼り付けを防ぎます。
# アプリから文章を更新するときは、下の専用関数内でだけ一時的に有効化します。
chat_area = scrolledtext.ScrolledText(
    conversation_frame,
    wrap=tk.WORD,
    state=tk.DISABLED
)
chat_area.grid(row=0, column=0, sticky="nsew")


def append_chat_text(text):
    """編集不可のチャット表示欄へ、アプリ側から文章を追記する。"""
    chat_area.config(state=tk.NORMAL)
    try:
        chat_area.insert(tk.END, text)
        chat_area.see(tk.END)
    finally:
        # 例外が起きても、ユーザーが編集できる状態を残さないようにします。
        chat_area.config(state=tk.DISABLED)


def replace_chat_text(text):
    """編集不可のチャット表示欄を消去し、指定した文章へ置き換える。"""
    chat_area.config(state=tk.NORMAL)
    try:
        chat_area.delete("1.0", tk.END)
        chat_area.insert(tk.END, text)
        chat_area.see(tk.END)
    finally:
        chat_area.config(state=tk.DISABLED)

# アバター表示エリア
# VOICEVOXの話者IDとは連動させず、profiles.jsonのavatar_idで画像を選びます。
avatar_frame = tk.LabelFrame(conversation_frame, text="AIアバター")
avatar_frame.grid(row=0, column=1, sticky="n", padx=(10, 0))

avatar_controller = AvatarController(
    avatar_frame,
    avatars_dir=AVATARS_DIR,
    avatar_id=AI_PROFILES[selected_name]["avatar_id"],
    image_size=180,
)

# 保存済み設定がOFFなら、起動時からアバター枠を表示しません。
apply_avatar_visibility(save_setting=False)

# 入力エリア
input_frame = tk.Frame(main_frame)
input_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)

input_frame.grid_columnconfigure(0, weight=1)

# 入力ボックス
entry = tk.Entry(input_frame)
entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
entry.focus_set()

# 送信ボタン
send_button = tk.Button(input_frame, text="送信", command=send_message)
send_button.grid(row=0, column=1)

# クリアボタン
clear_button = tk.Button(input_frame, text="クリア", command=clear_chat)
clear_button.grid(row=0, column=2, padx=(5, 0))

# 保存ボタン
save_button = tk.Button(input_frame, text="保存", command=save_chat_log)
save_button.grid(row=0, column=3, padx=(5, 0))


def set_response_controls_enabled(enabled):
    """AI返答中に変更すると混線する設定・操作の有効状態をまとめて切り替える。"""
    combo_state = "readonly" if enabled else tk.DISABLED
    button_state = tk.NORMAL if enabled else tk.DISABLED

    profile_combo.config(state=combo_state)
    model_combo.config(state=combo_state)
    refresh_button.config(state=button_state)
    think_check.config(state=button_state)
    voice_check.config(state=button_state)
    speaker_entry.config(state=button_state)
    clear_button.config(state=button_state)
    save_button.config(state=button_state)


def finish_response_ui():
    """AI返答の終了後に、入力欄と設定操作を安全に復活させる。"""
    global response_in_progress

    response_in_progress = False
    send_button.config(state=tk.NORMAL)
    entry.config(state=tk.NORMAL)
    set_response_controls_enabled(True)
    entry.focus_set()


def show_profile_load_warning():
    """profiles.json の読込失敗を、GUI起動後に分かりやすく通知する。"""
    if PROFILE_LOAD_WARNING:
        messagebox.showwarning(
            "profiles.json 読み込みエラー",
            PROFILE_LOAD_WARNING,
            parent=root,
        )


def on_closing():
    """ウィンドウを閉じるとき、音声再生を止めてキャッシュを掃除してから終了する。"""
    USER_SETTINGS["show_ai_avatar"] = bool(avatar_visible_var.get())
    save_user_settings(USER_SETTINGS_PATH, USER_SETTINGS)
    stop_voice_playback(show_message=False, cleanup_cache=True)
    cleanup_voice_cache()
    root.destroy()


root.bind("<Return>", lambda event: send_message())
root.protocol("WM_DELETE_WINDOW", on_closing)

# profiles.json に問題があってもウィンドウを先に起動し、修正方法を案内します。
if PROFILE_LOAD_WARNING:
    root.after(100, show_profile_load_warning)

root.mainloop()
