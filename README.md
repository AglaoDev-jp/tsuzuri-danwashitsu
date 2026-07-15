# すいっとトーク（suitto-talk）v2

**Ollama + VOICEVOX に対応したローカル AI チャットアプリ**

本リポジトリでは、アプリケーションのソースコードを公開しています。  
操作方法については、[利用マニュアル](./README_PLAY.md)をご確認ください。  
>本READMEは、アプリのソースコードおよび仕様をもとに、OpenAIの対話型AI「ChatGPT」の支援を受けて草案を作成し、作者が内容の確認・編集を行っています。  

---

## 主な機能

- Ollama を利用したローカル AI チャット
- キャラクタープロンプトの切り替え
- Ollama にインストールされているモデル一覧の自動取得・更新
- Thinking モードの切り替え（対応モデルのみ）
- AI 応答のストリーミング表示
- VOICEVOX による応答生成中からの順次読み上げ
- VOICEVOX の話者 ID 切り替え
- 読み上げの途中停止
- 一時音声キャッシュの自動管理
- チャットログの保存
- 全キャラクター共通の安全ガイドライン

---

## 動作環境

本アプリでは、以下のソフトウェアを使用します。

- **Python 3.8 以上**
- **Ollama**（必須）
  - AI チャット機能に使用します。
- **VOICEVOX**（任意）
  - AI 応答の音声読み上げに使用します。

VOICEVOX を起動していない場合でも、チャット機能は利用できます。  
その場合、音声読み上げは実行されず、チャット画面に警告メッセージが表示されます。

本アプリは、ローカル環境で動作する **Ollama API** および **VOICEVOX ENGINE** を利用します。

> [!NOTE]
> 本ソフトウェアは、同名または類似名称の既存の商標・製品・サービスとは関係ありません。

---

## 開発について

本プロジェクトの制作にあたり、OpenAI の対話型 AI「ChatGPT」のサポートを受け、アイデア出し、コード設計、実装、検証、文章表現の改善などを行いました。

使用した主なモデル・プランは以下のとおりです。

- GPT-5.5
- GPT-5.6
（ChatGPT Plus）  

開発に携わったすべての研究者、開発者、関係者の皆様に、心より感謝申し上げます。

---

## 制作期間

- **v1:** 2026年5月4日～5月5日、2026年5月7日  
  AI 利用上の注意表示と安全ガイドを追加
- **v2:** 2026年6月19日、2026年7月15日

---

## コントリビューションについて

※ 本リポジトリは個人学習・個人制作を目的としています。  
そのため、Pull Request（PR）はお受けできません。ご了承ください。

---

## 必要なPythonライブラリ

以下の外部ライブラリをインストールしてください。

```bash
pip install requests pygame
```

`tkinter` は Python の標準 GUI ライブラリです。  
環境によっては、Python とは別に Tcl/Tk 関連パッケージの導入が必要になる場合があります。

---

## 起動前の準備

### 1. Ollama のインストール

Ollama 公式サイトからインストールしてください。

- [Ollama 公式サイト](https://ollama.com/)

### 2. 使用するモデルのダウンロード

例として、以下のようにモデルをダウンロードできます。

```bash
ollama pull gemma4:e2b
```

```bash
ollama pull qwen3
```

```bash
ollama pull llama3.2
```

上記以外の Ollama 対応モデルも利用できます。

### 3. VOICEVOX のインストール（読み上げ機能を使用する場合）

- [VOICEVOX 公式サイト](https://voicevox.hiroshiba.jp/)
- [VOICEVOX GitHub](https://github.com/VOICEVOX/voicevox)

本アプリに VOICEVOX 本体は含まれていません。  
音声読み上げを使用する場合は、利用者自身で VOICEVOX をインストールし、起動した状態で本アプリをご利用ください。

### 4. 必要なファイルの配置

少なくとも、以下のファイルを同じフォルダに配置してください。

```text
suitto-talk/
├─ main_script_v2.py
└─ profiles.json
```

実行時には、同じフォルダ内に以下のディレクトリが自動作成されます。

```text
logs/         # チャットログの保存先
voice_cache/  # VOICEVOXの一時音声ファイル
```

### 5. アプリの起動

```bash
python main_script_v2.py
```

---

## 使用モデルについて

本アプリは起動時に Ollama の `/api/tags` へ接続し、ローカル環境にインストールされているモデル一覧を取得します。  
取得したモデルは、GUI のモデル選択欄から切り替えられます。

### 初期選択されるモデル

- `gemma4:e2b` がインストールされている場合は、初期モデルとして選択されます。
- `gemma4:e2b` が見つからない場合は、取得できたモデル一覧の先頭が選択されます。

### モデル一覧を取得できなかった場合

Ollama が起動していない場合や、モデル一覧の取得に失敗した場合は、以下の予備モデル一覧（Fallback Models）が表示されます。

- `gemma4:e2b`
- `gemma4`
- `qwen3`
- `llama3.2`

> [!IMPORTANT]
> 予備モデル一覧は、モデル一覧の取得に失敗した場合に表示する候補です。  
> 各モデルが実際にインストールされていることを保証するものではありません。

Ollama の起動後に GUI の「モデル更新」ボタンを押すと、現在インストールされているモデル一覧を再取得できます。

---

## Thinking モードについて

GUI の「Thinking」チェックボックスを切り替えると、Ollama API に `think: true` または `think: false` を送信します。

Thinking モードの対応状況や動作は、使用するモデルおよび Ollama のバージョンによって異なります。  
非対応モデルでは、期待どおりに動作しない可能性があります。

本アプリでは、Thinking の内部内容は表示せず、通常の回答本文のみをチャット画面に表示します。

---

## VOICEVOX について

本アプリは、音声合成ソフトウェア **VOICEVOX** およびローカルで動作する **VOICEVOX ENGINE** を利用して音声を生成します。

AI の回答を全文受信してから読み上げるのではなく、回答生成中の文章を適度な長さに分割し、順次音声を生成・再生します。

### 読み上げ機能

- 読み上げの ON／OFF
- 話者 ID の指定
- 読み上げの途中停止
- 読み上げ開始前の VOICEVOX 接続確認
- 生成済み音声の順次再生
- 一時 WAV ファイルの自動削除

初期設定の話者 ID は `3` です。  
別の音声を使用する場合は、VOICEVOX の話者 ID を確認して変更してください。

> [!IMPORTANT]
> 生成される音声を利用する際は、VOICEVOX 本体および各キャラクター（話者）の利用規約・ライセンスをご確認ください。

---

## 使用モジュール・ライブラリ

### 標準ライブラリ

- `json`  
  AI プロフィール設定（JSON ファイル）の読み込みに使用します。

- `threading`  
  AI 応答の取得、音声生成、音声再生を別スレッドで実行するために使用します。

- `pathlib`  
  設定ファイル、ログ、音声キャッシュなどのパス管理に使用します。

- `datetime`  
  チャットログや一時音声ファイルの日時付きファイル名を生成するために使用します。

- `time`  
  音声再生中の待機処理やタイミング調整に使用します。

- `queue`  
  AI 応答、音声生成、音声再生の各処理間でデータを受け渡すために使用します。

- `re`  
  AI 応答の文章分割や、読み上げ用テキストの整形に使用します。

### GUI 関連

- `tkinter`  
  デスクトップ GUI アプリケーションの構築に使用します。

- `tkinter.scrolledtext`  
  スクロール可能なチャット表示エリアに使用します。

- `tkinter.ttk`  
  モデルやキャラクターを選択するコンボボックスに使用します。

### 外部ライブラリ

- `requests`  
  Ollama API および VOICEVOX ENGINE との通信に使用します。

- `pygame`  
  VOICEVOX で生成した WAV 音声の再生に使用します。

---

## v2 の主な改良点・修正点

### AI チャット機能

- Ollama にインストールされているモデル一覧の自動取得に対応
- GUI からのモデル一覧更新に対応
- モデル切り替えに対応
- Thinking モードの切り替えに対応（対応モデルのみ）

### VOICEVOX 連携

- AI 応答生成中からの順次読み上げに対応
- 話者 ID の切り替えに対応
- 読み上げ停止ボタンを追加
- 音声生成と音声再生を分離したキュー処理を実装
- 生成済み音声の先読み件数を制限
- 一時音声キャッシュの自動管理に対応
- 読み上げ開始前の VOICEVOX 接続確認を追加
- VOICEVOX 未起動時や通信切断時のエラー表示を追加

### 既知の制限事項

- 初回の音声生成時や長い文章を読み上げる場合は、再生開始まで時間がかかることがあります。
- PC の性能、使用する話者、文章の長さなどによって、音声生成や再生が安定しない場合があります。
- 読み上げ停止後も、VOICEVOX ENGINE に送信済みの通信処理はすぐに終了しない場合があります。ただし、停止後に生成された音声は再生されません。
- Thinking モードの対応状況は、モデルおよび Ollama のバージョンによって異なります。
- Ollama や VOICEVOX が起動していない場合、該当する機能は利用できません。

---

## 注意事項

本アプリの AI 応答は、ローカル LLM によって自動生成されます。

キャラクターごとの口調や表現は、会話演出を目的としたものです。  
医療・法律・金融・心理などに関する専門的な助言を行うものではありません。

出力内容の正確性、安全性、完全性は保証されません。  
重要な判断を行う場合は、専門家または公的機関が提供する情報をご確認ください。

---

## 免責事項

本アプリの利用、設定変更、外部ソフトウェアとの連携などによって生じた損害、不具合、データ損失その他の問題について、作者は責任を負いません。  
利用者自身の責任においてご使用ください。

---

## このプロジェクトのライセンス

本プロジェクトは、「コード」と「キャラクタープロンプト集」で
それぞれ異なるライセンスを採用しています。

### ■ アプリケーションコード

* **ライセンス**: MIT License
* 商用利用：可能
* 改変：可能
* 再配布：可能
ただし、以下の条件を満たす必要があります：  

* **著作権表示とライセンス文の同梱**

詳細は [LICENSE-CODE](./licenses/application/LICENSE-CODE.txt) をご確認ください。

#### クレジット例

```plaintext
Code by AglaoDev-jp © 2026, licensed under the MIT License.
```

### ■ キャラクタープロンプト集

本プロジェクトには、AIの応答スタイルを切り替えるための
「キャラクタープロンプト集（Character Prompt Collection）」が含まれています。

各キャラクターは、口調・性格・役割などを定義したプロンプトとして設計されており、
用途に応じてAIの振る舞いを柔軟に変更することができます。

* **ライセンス**: Creative Commons Attribution 4.0 International (CC BY 4.0)
* 商用利用：可能
* 改変：可能
* 再配布：可能

ただし、以下の条件を満たす必要があります：  

* **クレジット表記（著作者の表示）を行うこと**  
詳細は [LICENSE-CODE](./licenses/application/LICENSE-PROMPT.txt) をご確認ください。

#### クレジット例

```plaintext
Character Prompt Collection by AglaoDev-jp
Licensed under CC BY 4.0
```

### ライセンス設定の方針

現在の AI 生成コンテンツを取り巻く状況を踏まえ、本プロジェクトでは、可能な限り利用条件が分かりやすく、自由に活用できるライセンス設定を目指しています。

このライセンス設定は、権利の独占を目的とするものではありません。  
利用条件やクレジット要件を明確にし、安心して利用・改変・再配布できる状態を整えることを目的としています。

今後、法制度や AI 生成コンテンツを取り巻く状況に変化があった場合は、必要に応じてライセンス設定を見直す可能性があります。

---

## 第三者ソフトウェアの著作権・ライセンス

### ライセンスファイル一覧

- [Python License](./licenses/LICENSE-PSF.txt)
- [Tcl/Tk License](./licenses/third_party/LICENSE-TclTk.txt)
- [Pygame LGPL v2.1](./licenses/third_party/LGPL_v2.1.txt)
- [Requests Apache License 2.0](./licenses/third_party/requests_LICENSE.txt)
- [Requests NOTICE](./licenses/third_party/requests_NOTICE.txt)

### Python

- Copyright © 2001 Python Software Foundation. All rights reserved.
- Licensed under the PSF License Version 2.
- [Python 公式ライセンス](https://docs.python.org/3/license.html)

### Tkinter / Tcl/Tk

Tkinter は Python に含まれる GUI ライブラリですが、その動作には Tcl/Tk が使用されています。

- [Tcl/Tk License](https://www.tcl.tk/software/tcltk/license.html)

### Pygame

- License: LGPL v2.1
- [ライセンスファイル](./licenses/third_party/LGPL_v2.1.txt)

### Requests

- License: Apache License 2.0
- [ライセンスファイル](./licenses/third_party/requests_LICENSE.txt)
- [NOTICE](./licenses/third_party/requests_NOTICE.txt)

### 外部ソフトウェア

- [Ollama](https://ollama.com/)
- [VOICEVOX](https://voicevox.hiroshiba.jp/)

これらのプロジェクトの開発者、貢献者、関係者の皆様に、心より感謝申し上げます。

---

© 2026 AglaoDev-jp
