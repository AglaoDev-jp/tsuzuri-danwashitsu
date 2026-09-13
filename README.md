# 綴り談話室 v1

**Ollama + VOICEVOX に対応したローカル AI チャットアプリ**

[実行ファイル版を GitHub Releases からダウンロード](https://github.com/AglaoDev-jp/tsuzuri-danwashitsu/releases/tag/v1.0.0)

本作は、これまで制作していたアプリの内容と方向性を引き継ぎ、**「綴り談話室（つづりだんわしつ）」** へ名称を変更したものです。
名称変更後、最初に公開するバージョンを **v1** としています。


本リポジトリでは、ソースコードと開発者向け情報を公開しています。  
実行ファイル版の詳しい使い方は、[利用マニュアル](./README_PLAY.md)をご確認ください。

> [!NOTE]
> 本 README は、アプリのソースコードおよび仕様をもとに、OpenAI の対話型 AI「ChatGPT」の支援を受けて草案を作成し、作者が内容の確認・編集を行っています。

---

## 目次

- [主な機能](#主な機能)
- [動作環境](#動作環境)
- [実行ファイル版から起動する](#実行ファイル版から起動する)
- [ソースコードから起動する](#ソースコードから起動する)
- [PyInstaller によるビルド](#pyinstaller-によるビルド)
- [プロジェクト構成](#プロジェクト構成)
- [技術情報](#技術情報)
- [既知の制限事項](#既知の制限事項)
- [開発について](#開発について)
- [ライセンス](#ライセンス)

---

## 主な機能

- Ollama を利用したローカル AI チャット
- キャラクタープロンプトの切り替え
- Ollama にインストールされているモデル一覧の自動取得・更新
- Thinking モードの切り替え（対応モデルのみ）
- AI 応答のストリーミング表示
- ユーザーが誤入力できない表示専用のチャット欄
- AI 返答中の設定変更・クリア・保存をロックし、会話履歴の混線を防止
- `profiles.json` の読込失敗時に、原因を警告して臨時プロフィールで起動
- キャラクターごとのアバター切り替えと、安全なデフォルト画像へのフォールバック
- AI アバター表示／非表示の切り替えと設定保存
- AI の待機状態と返答の感情に応じた表情切り替え
- VOICEVOX による応答生成中からの順次読み上げ
- VOICEVOX の話者 ID 切り替え
- 読み上げの途中停止
- 一時音声キャッシュの自動管理
- チャットログの保存
- 全キャラクター共通の安全ガイドライン

---

## 動作環境

### 実行時に必要なソフトウェア

- **Ollama**（必須）
  - AI チャット機能に使用します。
- **Ollama 対応モデル**（必須）
  - 使用するモデルを事前にダウンロードしてください。
- **VOICEVOX**（任意）
  - AI 応答の音声読み上げに使用します。

VOICEVOX を起動していない場合でも、チャット機能は利用できます。  
本アプリは、ローカル環境で動作する **Ollama API** および **VOICEVOX ENGINE** を利用します。

### ソースコードから起動・ビルドする場合

- Windows
- Python 3.8 以上
- `requests`
- `pygame`
- PyInstaller（実行ファイルを作成する場合のみ）

`tkinter` は通常、Windows 版 Python に同梱されています。

> [!NOTE]
> 本ソフトウェアは、同名または類似名称の既存の商標・製品・サービスとは関係ありません。

---

## 実行ファイル版から起動する

1. [GitHub Releases](https://github.com/AglaoDev-jp/suitto-talk/releases) から配布 ZIP をダウンロードします。
2. ZIP を任意のフォルダへ展開します。
3. Ollama を起動し、使用するモデルがインストールされていることを確認します。
4. 音声読み上げを使用する場合は、VOICEVOX も起動します。
5. 展開したフォルダ内の `綴り談話室.exe` をダブルクリックします。

実行ファイル版では、Python や Python ライブラリを別途インストールする必要はありません。  
ただし、Ollama、使用するモデル、必要に応じて VOICEVOX は利用者自身で用意してください。

> [!IMPORTANT]
> ZIP 内から直接起動せず、必ず展開してから使用してください。  
> また、`綴り談話室.exe` だけを別の場所へ移動せず、配布フォルダの構成を保ってください。

詳しい準備、操作方法、トラブル対処は [README_PLAY.md](./README_PLAY.md) に記載しています。

---

## ソースコードから起動する

### 1. Ollama をインストールする

- [Ollama 公式サイト](https://ollama.com/)

使用するモデルをダウンロードします。

```bash
ollama pull gemma4:e2b
```

上記以外の Ollama 対応モデルも利用できます。

### 2. VOICEVOX をインストールする（任意）

- [VOICEVOX 公式サイト](https://voicevox.hiroshiba.jp/)
- [VOICEVOX GitHub](https://github.com/VOICEVOX/voicevox)

本アプリに VOICEVOX 本体は含まれていません。

### 3. Python ライブラリをインストールする

```bash
py -m pip install requests pygame
```

### 4. アプリを起動する

コマンドプロンプトで `src` フォルダへ移動し、次を実行します。

```bash
py main.py
```

`py` コマンドを使用できない環境では、`python` に置き換えてください。

Pythonから直接実行した場合は、`main.py` のある `src` フォルダが基準です。
`profiles.json` と `assets` をここから読み込み、設定・ログ・一時音声もここへ保存します。
別の作業フォルダから `main.py` のパスを指定して起動しても、この基準は変わりません。

---

## PyInstaller によるビルド

以下は、Windows 上で配布用の実行ファイル一式を作成する手順です。  
`profiles.json` の編集、アバター画像の差し替え、チャットログの保存を維持するため、本プロジェクトでは **1ファイル化ではなくフォルダ形式（`--onedir`）** を使用します。

### 1. PyInstaller をインストールする

```bash
py -m pip install "pyinstaller>=6,<7"
```
※ こちらは、"PyInstaller 6.x 系の最新版をインストールする。ただし将来の PyInstaller 7.x には上げない。"というコマンドです。  
**「このビルド手順はPyInstaller 6系を前提にしています」**  


### 2. `src` フォルダへ移動する

```bat
cd src
```

### 3. ビルドする

Windows のコマンドプロンプトで、次を実行します。  
再ビルドする場合は、既存の `dist\綴り談話室` を先に別の場所へ退避してください。  
編集したキャラクター設定・画像や、動作確認中に保存した設定・ログを残せます。  

```bat
py -m PyInstaller ^
  --clean ^
  --windowed ^
  --onedir ^
  --name "綴り談話室" ^
  --icon "icon.ico" ^
  main.py ^
&& copy /Y "profiles.json" "dist\綴り談話室\profiles.json" ^
&& xcopy /E /I /Y "assets" "dist\綴り談話室\assets"
```

ビルドに成功すると、次のフォルダが作成されます。  

```text
src\dist\綴り談話室\
```

ビルドに成功すると、`綴り談話室.exe` と、Pythonランタイム・DLLなどをまとめた
`_internal` フォルダが作成され、続けて `profiles.json` と `assets` がexeの隣へ自動でコピーされます。

`&&` でコマンドをつないでいるため、PyInstaller のビルドに失敗した場合はコピー処理へ進みません。  
`profiles.json` と `assets` は利用者が編集・差し替えできるよう、`--add-data` で `_internal` に取り込まず、exeの隣へ配置します。specファイルの編集は不要です。  

### 4. マニュアル・ライセンスを配置する

**ビルドが正常に完了したことを確認してから**、`src` フォルダにいる状態で次を実行します。

```bat
copy /Y "..\README_PLAY.md" "dist\綴り談話室\README_PLAY.md"
xcopy /E /I /Y "..\licenses" "dist\綴り談話室\licenses"
```

ソース側の `user_settings.json`・`logs`・`voice_cache` はコピーしません。これらは実行時に必要に応じて作成されます。

```text
dist\綴り談話室\
├─ 綴り談話室.exe
├─ profiles.json
├─ assets/
├─ README_PLAY.md
├─ licenses/
├─ _internal/          # Pythonランタイム・DLLなど（削除しない）
├─ user_settings.json  # 設定保存時に自動作成
├─ logs/               # 起動時に自動作成
└─ voice_cache/        # 起動時に自動作成
```

exe版では **exeのあるフォルダ** が利用者向けファイルの基準です。
`_internal` の中に設定・画像・ログ・音声を置く必要はありません。
書き込み可能な場所へフォルダごと展開し、exeと `_internal` は一緒に保管してください。

| 起動方法 | 基準フォルダ | 読み込み・保存先 |
| --- | --- | --- |
| `py main.py` | `Path(__file__).resolve().parent`（`src`） | その直下の設定・画像・ログ・音声 |
| `綴り談話室.exe` | `Path(sys.executable).resolve().parent` | exeの隣の設定・画像・ログ・音声 |

参考：[PyInstaller公式の実行時パスの説明](https://pyinstaller.org/en/stable/runtime-information.html)、
[ビルドオプション](https://pyinstaller.org/en/stable/usage.html)。

### 5. 配布 ZIP を作成する

`dist\綴り談話室` フォルダを、そのフォルダごと ZIP にします。  
配布版には、2つの README のうち **`README_PLAY.md` のみ同梱**します。

配布前に、少なくとも次を確認してください。

- `綴り談話室.exe` が起動する
- Ollama のモデル一覧を取得できる
- AI の返答を表示できる
- チャット表示欄へ文字を入力できない
- AI 返答中にキャラ・モデル・各種設定・クリア・保存を変更できない
- `profiles.json` を読み込める
- 壊れた `profiles.json` では、警告後に臨時プロフィールで起動する
- キャラ変更時に対応する `avatar_id` へ切り替わる
- アバター表示ONで画像、OFFで広いチャット欄を利用できる
- アバター表示設定が再起動後も維持される
- キャラクター画像や表情画像がなくてもdefault画像で動作する
- exeの隣の `logs` フォルダへチャットログを保存できる
- exeの隣の `user_settings.json` に設定が保存され、再起動で反映される
- 音声生成中はexeの隣の `voice_cache` に一時音声が作られる（再生後は削除される）
- `_internal` に利用者向けの設定・画像・ログ・音声が作られていない
- VOICEVOX 使用時に音声を再生できる
- `README_PLAY.md` と `licenses` フォルダが含まれている

---

## プロジェクト構成

```text
綴り談話室/
├─ .gitignore
├─ README.md
├─ README_PLAY.md
├─ licenses/
│  ├─ application/
│  └─ third_party/
└─ src/
   ├─ main.py
   ├─ avatar_controller.py
   ├─ profiles.json
   └─ assets/
      └─ avatars/
         ├─ default/
         │  ├─ normal.png
         │  ├─ smile.png
         │  ├─ happy.png
         │  ├─ thinking.png
         │  ├─ surprised.png
         │  ├─ sad.png
         │  └─ serious.png
         │  
            ets...
```

実行時には、Python版では `main.py` の隣、exe版ではexeの隣に次のファイル・フォルダが必要に応じて作成されます。

```text
logs/         # 保存したチャットログ
voice_cache/  # VOICEVOXの一時音声ファイル
user_settings.json  # アバター表示／非表示の保存設定
```

`.gitignore` では、`__pycache__`、`.mypy_cache`、実行ログ、一時音声、
PyInstaller の `build`・`dist` など、リポジトリへ含めない生成物を除外しています。

### キャラクター設定とアバター画像

`profiles.json` の各キャラクターは、AIへ渡す `prompt` と画像フォルダ名を表す
`avatar_id` を持ちます。

```json
{
  "優しいAI": {
    "prompt": "あなたは丁寧で優しいアシスタントです。",
    "avatar_id": "kind"
  }
}
```

この例の本番画像は `src/assets/avatars/kind/normal.png` へ置きます。表情差分は
同じフォルダへ `smile.png`、`sad.png`、`angry.png`、`surprised.png`、
`troubled.png`、`thinking.png` などの名前で追加します。

指定画像がない場合は、同じキャラクターの `normal.png`、
`assets/avatars/default/` 内の画像、内蔵プレースホルダーの順で切り替わります。

---

## 技術情報

### Ollama API

- チャット送信: `http://localhost:11434/api/chat`
- モデル一覧取得: `http://localhost:11434/api/tags`

アプリは起動時にモデル一覧を取得し、取得できなかった場合は予備モデル一覧を表示します。  
「モデル更新」ボタンを押すと、現在インストールされているモデル一覧を再取得します。

### Thinking モード

GUI の「Thinking」チェックボックスに応じて、Ollama API へ `think: true` または `think: false` を送信します。  
対応状況や動作は、モデルおよび Ollama のバージョンによって異なります。

### ストリーミング応答とアバター

Ollama API へ `stream: true` を送信し、回答本文を少しずつ表示します。  
通常は返答先頭の短い感情タグを解析し、本文には表示せず、アバターの表情切り替えに使用します。
画像の解決とフォールバックは `avatar_controller.py` に集約しています。

### VOICEVOX ENGINE API

- 接続確認: `http://127.0.0.1:50021/version`
- 音声クエリ生成: `http://127.0.0.1:50021/audio_query`
- 音声合成: `http://127.0.0.1:50021/synthesis`

回答を適度な長さに分割し、生成中から順次音声を作成・再生します。

---

## 既知の制限事項

- Thinking モードの対応状況は、使用するモデルと Ollama のバージョンによって異なります。
- PC の性能や使用モデルによって、AI の応答速度が大きく異なります。
- 初回の音声生成や長文読み上げでは、再生開始まで時間がかかる場合があります。
- 読み上げ停止後も、VOICEVOX ENGINE へ送信済みの処理が一時的に継続する場合があります。
- Ollama または VOICEVOX のポート番号を変更している場合は、スクリプト側の設定変更が必要です。
- ローカル LLM が感情形式を守らない場合は、表情を `neutral` にして本文を優先します。
- アバターの口パクとまばたきには対応していません。

---

## 開発について

本プロジェクトの制作にあたり、OpenAI の対話型 AI「ChatGPT」のサポートを受け、アイデア出し、コード設計、実装、検証、文章表現の改善などを行いました。  

使用した主なモデルは以下のとおりです。  

* GPT-5.5
* GPT-5.6
* GPT-6 Astra

利用プラン：ChatGPT Plus  

開発に携わったすべての研究者、開発者、関係者の皆様に、心より感謝申し上げます。  


### コントリビューションについて

本リポジトリは個人学習・個人制作を目的としています。  
そのため、Pull Request（PR）はお受けできません。ご了承ください。  

---

## 注意事項・免責事項

本アプリの AI 応答は、ローカル LLM によって自動生成されます。  
医療、法律、金融、心理などに関する専門的な助言を行うものではありません。

出力内容の正確性、安全性、完全性は保証されません。  
重要な判断を行う場合は、専門家または公的機関が提供する情報をご確認ください。

本アプリの利用、設定変更、外部ソフトウェアとの連携などによって生じた損害、不具合、データ損失その他の問題について、作者は責任を負いません。  
利用者自身の責任においてご使用ください。

---

## ライセンス

本プロジェクトでは、収録内容に応じて異なるライセンスを適用しています。  

### アプリケーションコード・アプリアイコン

**MIT License**

* 商用利用：可能
* 改変：可能
* 再配布：可能

MIT Licenseは、著作権表示とライセンス文を残すことで、個人・商用を問わず、比較的自由に利用・改変・再配布できるライセンスです。  

* [LICENSE-CODE](./licenses/application/LICENSE-CODE.txt)

```
Code and App Icon by AglaoDev-jp © 2026
Licensed under the MIT License.
```

### キャラクタープロンプト集

**Creative Commons Attribution 4.0 International（CC BY 4.0）**

* 商用利用：可能
* 改変：可能
* 再配布：可能
* クレジット表記：必要

CC BY 4.0は、作者への適切なクレジットを表示することで、個人・商用を問わず、作品の利用・改変・再配布ができるライセンスです。  

* [LICENSE-PROMPT](./licenses/application/LICENSE-PROMPT.txt)
* [CC BY 4.0 公式ライセンス](https://creativecommons.org/licenses/by/4.0/)

```
Character Prompt Collection by AglaoDev-jp
Licensed under CC BY 4.0
```

### 画像素材

本プロジェクトに含まれる画像素材には、**Creative Commons Attribution 4.0 International（CC BY 4.0）**を適用します。  

クレジットを表示し、CC BY 4.0の条件を守ることで、画像の利用・加工・再配布が可能です。  

* [LICENSE-IMAGE](./licenses/application/LICENSE-IMAGE.txt)
* [CC BY 4.0 公式ライセンス](https://creativecommons.org/licenses/by/4.0/)

```
Image Collection by AglaoDev-jp
Licensed under CC BY 4.0
```

---

## 第三者ソフトウェアの著作権・ライセンス

本プロジェクトでは、以下の第三者ソフトウェアやライブラリを使用しています。  

それぞれ本プロジェクトとは別の著作権・ライセンスが適用されます。詳しい条件については、各ライセンスファイルおよび公式サイトをご確認ください。  

* **Python** — PSF License Version 2
  Copyright © 2001 Python Software Foundation. All rights reserved.
  [ライセンスファイル](./licenses/LICENSE-PSF.txt) / [Python公式ライセンス](https://docs.python.org/3/license.html)

* **Tcl/Tk** — Tcl/Tk License
  [ライセンスファイル](./licenses/third_party/LICENSE-TclTk.txt) / [Tcl/Tk公式ライセンス](https://www.tcl.tk/software/tcltk/license.html)

* **Pygame** — LGPL v2.1
  [ライセンスファイル](./licenses/third_party/LGPL_v2.1.txt)

* **Requests** — Apache License 2.0
  [ライセンスファイル](./licenses/third_party/requests_LICENSE.txt) / [NOTICE](./licenses/third_party/requests_NOTICE.txt)

### 外部ソフトウェア・生成ツール

* [Ollama](https://ollama.com/)
* [VOICEVOX](https://voicevox.hiroshiba.jp/)
* [ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5)

VOICEVOXで生成した音声を利用する場合は、VOICEVOX本体および使用するキャラクター（話者）の利用規約・ライセンスをご確認ください。  

Ollamaで使用する各AIモデルにも、それぞれモデル提供元が定めたライセンスがあります。モデルを利用・配布する際は、各モデルのライセンスをご確認ください。  

これらのプロジェクトの開発者、貢献者、関係者の皆様に感謝申し上げます。  

---


© 2026 AglaoDev-jp
