"""綴り談話室の簡易チャットアバターを管理します。

このモジュールは、アバター画像の読み込み・表情切り替えと、
ローカルLLMが返した感情タグの安全な解析だけを担当します。
VOICEVOXの話者選択とは意図的に分離しているため、選択した声が変わっても
アバター画像そのものは変わりません。
"""

import json
import re
import tkinter as tk
from pathlib import Path


# 利用できる表情タグです。
# プロンプト、解析、画像ファイル名で同じ値を共有し、表記揺れを防ぎます。
VALID_EMOTIONS = (
    "normal",
    "smile",
    "happy",
    "thinking",
    "surprised",
    "sad",
    "angry",
    "troubled",
    "serious",
)

EMOTION_LABELS = {
    "normal": "通常",
    "smile": "微笑み",
    "happy": "喜び",
    "thinking": "考え中",
    "surprised": "驚き",
    "sad": "悲しみ",
    "angry": "怒り",
    "troubled": "困惑",
    "serious": "真剣",
}

# 旧バージョンの ``neutral`` タグも引き続き受け入れます。
# 画像ファイルについても ``normal.png`` がなければ ``neutral.png`` を探すため、
# 利用者が以前の画像をそのまま残していても問題ありません。
EMOTION_ALIASES = {
    "neutral": "normal",
}

# キャラクター設定にavatar_idがない場合や、不正な値だった場合に使う共通IDです。
DEFAULT_AVATAR_ID = "default"

# avatar_idはフォルダ名として使用します。英数字・ハイフン・アンダースコアだけに
# 制限し、profiles.jsonから意図しない場所を参照できないようにします。
AVATAR_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

# ストリーミング表示を維持するため、通常は返答先頭の短いタグを使います。
# JSON形式が返された場合も、parse_avatar_response() が互換形式として扱います。
EMOTION_TAG_PATTERN = re.compile(
    r"^\s*\[\[\s*emotion\s*:\s*([A-Za-z_]+)\s*\]\][\t ]*(?:\r?\n)?",
    flags=re.IGNORECASE,
)


def normalize_emotion(emotion):
    """未定義の感情タグを安全な ``normal`` に置き換えます。"""
    if not isinstance(emotion, str):
        return "normal"

    normalized = emotion.strip().lower()
    normalized = EMOTION_ALIASES.get(normalized, normalized)
    if normalized in VALID_EMOTIONS:
        return normalized

    return "normal"


def normalize_avatar_id(avatar_id, default_avatar_id=DEFAULT_AVATAR_ID):
    """avatar_idを安全な1階層のフォルダ名へ正規化します。

    avatar_idが未指定・不正・パス形式の場合は、共通のdefaultへ戻します。
    これにより設定ミスがあっても起動を妨げず、上位フォルダの画像を誤って
    読み込むことも防ぎます。
    """
    safe_default = (
        default_avatar_id
        if isinstance(default_avatar_id, str)
        and AVATAR_ID_PATTERN.fullmatch(default_avatar_id)
        else DEFAULT_AVATAR_ID
    )

    if not isinstance(avatar_id, str):
        return safe_default

    normalized = avatar_id.strip()
    if not AVATAR_ID_PATTERN.fullmatch(normalized):
        return safe_default

    return normalized


def _strip_json_code_fence(text):
    """返答全体を囲むMarkdownのJSONコードフェンスだけを取り除きます。"""
    stripped = text.strip()
    match = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        stripped,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1).strip() if match else stripped


def _extract_json_string_field(text, field_names):
    """壊れたJSONからも、文字列フィールドを可能な範囲で救出します。

    ローカルLLMが閉じ括弧を忘れた場合などでも、``text`` の値が完全なら
    チャット本文として利用できます。文字列のエスケープ解除には json.loads を
    使い、独自処理による文字化けを避けています。
    """
    for field_name in field_names:
        pattern = re.compile(
            rf'"{re.escape(field_name)}"\s*:\s*"((?:\\.|[^"\\])*)"',
            flags=re.DOTALL,
        )
        match = pattern.search(text)
        if not match:
            continue

        try:
            return json.loads(f'"{match.group(1)}"')
        except json.JSONDecodeError:
            # エスケープが壊れていても、読める部分は本文として残します。
            return match.group(1)

    return None


def parse_avatar_response(raw_response):
    """LLM返答を ``(本文, 感情タグ)`` に分けます。

    次の順で解析します。

    1. ``{"text": "...", "emotion": "smile"}`` 形式
    2. ``[[emotion:smile]]`` で始まるストリーミング向け形式
    3. 壊れたJSONからの ``text`` / ``emotion`` 救出
    4. 従来どおりの通常テキスト（感情は ``normal``）

    どの形式でも例外を外へ出さず、アバター解析の失敗によって会話処理が
    停止しないことを最優先にしています。
    """
    if not isinstance(raw_response, str):
        return "", "normal"

    candidate = _strip_json_code_fence(raw_response)

    # まず、理想的なJSON形式を通常のJSONパーサーで読み取ります。
    try:
        parsed = json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        parsed = None

    if isinstance(parsed, dict):
        text = parsed.get("text")
        if not isinstance(text, str):
            # 一部モデルが使う可能性のある一般的な本文キーも受け入れます。
            text = parsed.get("content") or parsed.get("message")

        if isinstance(text, str):
            return text.strip(), normalize_emotion(parsed.get("emotion"))

    # 通常利用する先頭タグ形式です。未定義タグでも本文は必ず救出します。
    tag_match = EMOTION_TAG_PATTERN.match(raw_response)
    if tag_match:
        text = raw_response[tag_match.end():].strip()
        return text, normalize_emotion(tag_match.group(1))

    # JSONが少し壊れていても、完全に生成された文字列フィールドは救出します。
    rescued_text = _extract_json_string_field(candidate, ("text", "content", "message"))
    if isinstance(rescued_text, str):
        rescued_emotion = _extract_json_string_field(candidate, ("emotion",))
        return rescued_text.strip(), normalize_emotion(rescued_emotion)

    # 解析できない場合は、返答全体を従来どおり本文として扱います。
    return raw_response.strip(), "normal"


class AvatarResponseStreamParser:
    """先頭の感情タグを除きながら、本文のストリーミングを維持します。

    通常の先頭タグを認識した場合は、その直後から本文だけを逐次返します。
    JSON形式の場合は構造文字を画面やVOICEVOXへ渡さないため、返答完了時に
    parse_avatar_response() でまとめて解析します。
    """

    def __init__(self):
        self.raw_response = ""
        self.mode = "pending"
        self.emotion = None
        self.emitted_text = ""

    def feed(self, content):
        """受信チャンクを追加し、今すぐ表示できる本文と感情を返します。"""
        if not content:
            return "", None

        self.raw_response += content

        if self.mode == "tag" or self.mode == "plain":
            self.emitted_text += content
            return content, None

        stripped = self.raw_response.lstrip()

        # JSONらしい先頭なら、JSONの記号を誤表示しないよう完了まで待ちます。
        if stripped.startswith("{") or stripped.lower().startswith("```json"):
            self.mode = "json"
            return "", None

        tag_match = EMOTION_TAG_PATTERN.match(self.raw_response)
        if tag_match:
            # ストリームが閉じ括弧の直後（またはCRだけ）で分割された場合は、
            # 次のチャンクに来る改行を本文として誤表示しないよう少し待ちます。
            tag_remainder = self.raw_response[tag_match.end():]
            if tag_remainder in ("", "\r"):
                return "", None

            self.mode = "tag"
            self.emotion = normalize_emotion(tag_match.group(1))
            visible_text = tag_remainder
            self.emitted_text += visible_text
            return visible_text, self.emotion

        # 先頭行が完成してもタグでなければ、従来形式の通常本文として扱います。
        # 改行のない長文でも待ち続けないよう、文字数にも上限を設けています。
        if "\n" in self.raw_response or len(self.raw_response) >= 240:
            self.mode = "plain"
            visible_text = self.raw_response
            self.emitted_text += visible_text
            self.emotion = "normal"
            return visible_text, self.emotion

        return "", None

    def finish(self):
        """返答全体を確定し、未表示の本文・最終感情・履歴用本文を返します。"""
        text, emotion = parse_avatar_response(self.raw_response)

        if not self.emitted_text:
            remaining_text = text
        elif text.startswith(self.emitted_text):
            remaining_text = text[len(self.emitted_text):]
        else:
            # すでに通常本文として表示済みなら、差異があっても二重表示しません。
            remaining_text = ""

        return remaining_text, emotion, text


class AvatarController:
    """キャラクター別PNG画像と現在の表情をTkinter画面へ表示します。

    画像は ``avatars_dir / avatar_id / <emotion>.png`` から読み込みます。
    表情画像がない場合は同じキャラクターの通常画像、共通default画像、
    最後に内蔵プレースホルダーの順で安全にフォールバックします。

    キャラクター選択・表情選択・画像解決をこのクラスへ集約しているため、
    将来の感情判定方法を変えても、GUIやVOICEVOX処理を大きく変更せずに済みます。
    """

    def __init__(
        self,
        parent,
        avatars_dir,
        avatar_id=DEFAULT_AVATAR_ID,
        default_avatar_id=DEFAULT_AVATAR_ID,
        image_size=180,
    ):
        self.avatars_dir = Path(avatars_dir)
        self.default_avatar_id = normalize_avatar_id(default_avatar_id)
        self.current_avatar_id = normalize_avatar_id(
            avatar_id,
            self.default_avatar_id,
        )
        self.image_size = image_size
        self.current_emotion = "normal"
        self._image_cache = {}
        self._broken_image_paths = set()
        self._placeholder_image = None

        self.label = tk.Label(
            parent,
            text="",
            compound=tk.CENTER,
            relief=tk.GROOVE,
            borderwidth=1,
            padx=6,
            pady=6,
        )
        self.label.pack(fill=tk.BOTH, expand=True)

        self._apply_emotion("normal")

    def _create_placeholder_image(self):
        """画像が1枚もない場合に表示する、軽量な内蔵プレースホルダーです。"""
        image = tk.PhotoImage(width=self.image_size, height=self.image_size)
        image.put("#e9eef1", to=(0, 0, self.image_size, self.image_size))

        # 外部描画ライブラリを増やさず、抽象的なAIの窓口を簡単な図形で示します。
        margin = max(12, self.image_size // 12)
        image.put(
            "#a9bbc5",
            to=(margin, margin, self.image_size - margin, self.image_size - margin),
        )
        inner = margin + max(5, self.image_size // 30)
        image.put(
            "#f5f8fa",
            to=(inner, inner, self.image_size - inner, self.image_size - inner),
        )
        return image

    def _emotion_file_names(self, emotion):
        """1つの表情から、互換名を含む画像ファイル名候補を返します。"""
        normalized = normalize_emotion(emotion)

        # 通常表情の正式名はnormal.pngです。旧版のneutral.pngも互換候補として
        # 残しているため、既存素材を急いで変更する必要はありません。
        if normalized == "normal":
            return ("normal.png", "neutral.png")

        return (f"{normalized}.png",)

    def _candidate_image_paths(self, emotion):
        """現在の設定から、安全なフォールバック順で画像候補を作ります。"""
        character_dir = self.avatars_dir / self.current_avatar_id
        default_dir = self.avatars_dir / self.default_avatar_id

        candidates = []

        # 1. 選択キャラクターの指定表情
        for file_name in self._emotion_file_names(emotion):
            candidates.append(character_dir / file_name)

        # 2. 指定表情がなければ、同じキャラクターの通常表情
        if normalize_emotion(emotion) != "normal":
            for file_name in self._emotion_file_names("normal"):
                candidates.append(character_dir / file_name)

        # 3. キャラクター画像がなければ、共通defaultの同じ表情
        for file_name in self._emotion_file_names(emotion):
            candidates.append(default_dir / file_name)

        # 4. 最後に共通defaultの通常表情
        if normalize_emotion(emotion) != "normal":
            for file_name in self._emotion_file_names("normal"):
                candidates.append(default_dir / file_name)

        # avatar_idがdefaultの場合などに生じる重複を、順序を保ったまま除きます。
        return tuple(dict.fromkeys(candidates))

    def _load_photo_image(self, image_path):
        """1枚のPNGを読み込み、表示枠を超える場合だけ整数倍率で縮小します。"""
        image = tk.PhotoImage(file=str(image_path))

        # Tkinter標準機能だけを使うため、新しい画像ライブラリへの依存は増えません。
        width_ratio = max(1, (image.width() + self.image_size - 1) // self.image_size)
        height_ratio = max(1, (image.height() + self.image_size - 1) // self.image_size)
        factor = max(width_ratio, height_ratio)
        if factor > 1:
            image = image.subsample(factor, factor)

        return image

    def _load_image(self, emotion):
        """候補を順に読み込み、すべて失敗した場合だけ内蔵画像を返します。"""
        for image_path in self._candidate_image_paths(emotion):
            cache_key = str(image_path)

            # 一度読み込みに失敗したファイルは、表情更新のたびに再試行しません。
            if cache_key in self._broken_image_paths:
                continue

            try:
                if not image_path.is_file():
                    continue
            except OSError:
                # アクセス権や一時的なファイルシステムエラーも、画像なしとして扱います。
                continue

            if cache_key in self._image_cache:
                return self._image_cache[cache_key], True

            try:
                image = self._load_photo_image(image_path)
            except (tk.TclError, OSError):
                # 壊れたPNGなら次の候補（default等）へ進みます。
                self._broken_image_paths.add(cache_key)
                continue

            self._image_cache[cache_key] = image
            return image, True

        if self._placeholder_image is None:
            self._placeholder_image = self._create_placeholder_image()
        return self._placeholder_image, False

    def set_avatar(self, avatar_id, emotion="normal"):
        """選択キャラクターを変更し、指定表情（既定は通常）へ更新します。"""
        normalized_avatar_id = normalize_avatar_id(
            avatar_id,
            self.default_avatar_id,
        )
        normalized_emotion = normalize_emotion(emotion)
        self.label.after(
            0,
            self._apply_avatar,
            normalized_avatar_id,
            normalized_emotion,
        )

    def _apply_avatar(self, avatar_id, emotion):
        """Tkinterのメインスレッド上でキャラクターと表情を同時に更新します。"""
        self.current_avatar_id = normalize_avatar_id(
            avatar_id,
            self.default_avatar_id,
        )
        self._apply_emotion(emotion)

    def set_emotion(self, emotion):
        """指定した表情へ切り替えます。別スレッドから呼ばれても安全に予約します。"""
        normalized = normalize_emotion(emotion)
        self.label.after(0, self._apply_emotion, normalized)

    def _apply_emotion(self, emotion):
        """Tkinterのメインスレッド上で、実際の画像と表示名を更新します。"""
        self.current_emotion = normalize_emotion(emotion)
        image, image_loaded = self._load_image(self.current_emotion)

        if image_loaded:
            # 実画像がある場合は、表情名を画像の上へ重ねずそのまま表示します。
            label_text = ""
        else:
            label_text = (
                "アバター画像を準備中\n"
                f"表情: {EMOTION_LABELS[self.current_emotion]}"
            )

        self.label.configure(image=image, text=label_text)
        # PhotoImageがガベージコレクションで消えないよう、Labelにも参照を残します。
        self.label.image = image
