# すいっとトーク（suitto-talk）v1  

**Ollamaを使った軽量GUIチャットアプリ**  
本リポジトリでは、アプリの **ソースコード** を公開しています。  
マニュアルは[こちら](./README_PLAY.md)  
※ 本アプリはローカル環境で動作する [Ollama API](http://localhost:11434) を前提としています。  
※ 本ソフトウェアは、既存の商標・サービスとは関係ありません。  

---

## 開発について  

本プロジェクトの制作にあたり、OpenAI の対話型AI「ChatGPT」のサポートを受けて、  
アイデア出し、コード設計、実装、文章表現の改善などを効率的に行いました。  

- **GPT-5.5**  
（ChatGPT Plus）  

開発に携わったすべての研究者・開発者・関係者の皆様に、心より感謝申し上げます。  

---

## 免責事項
本アプリの利用や環境設定に起因するいかなる損害や不具合について、  
作者は一切の責任を負いません。

## 注意事項

本アプリのAI応答は、ローカルLLMによって自動生成されるものです。  

キャラクターごとの口調や表現は会話演出を目的としたものであり、
医療・法律・金融・心理などの専門的助言を行うものではありません。

出力内容の正確性・安全性・完全性は保証されません。  
重要な判断を行う場合は、必ず専門家または公的機関の情報をご確認ください。  

---

**製作期間**

- **v1**: 2026年5月4日 ~ 2026年5月5日, 2026年5月7日（AI注意表示と安全ガイドを追加）  

---

※ 本リポジトリは個人学習・個人制作を目的としています。  
そのため、Pull Request（PR）はお受けできません。ご了承ください。

---

## 使用言語とライブラリ

### 使用言語
- **Python 3.12.5**

---

### 使用モジュール・ライブラリ

#### 標準ライブラリ
- `json`  
  → AIプロフィール設定（JSONファイル）の読み込みに使用

- `threading`  
  → UIを停止させずに非同期でAI応答を取得するために使用

- `pathlib`  
  → ファイルパスの管理（設定ファイル・ログ保存）に使用

- `datetime`  
  → チャットログ保存時の日時付きファイル名の生成に使用

---

#### GUI関連
- `tkinter`  
  → デスクトップGUIアプリケーションの構築に使用

- `tkinter.scrolledtext`  
  → スクロール可能なチャット表示エリアの実装

- `tkinter.ttk`  
  → コンボボックスなどの拡張UI部品に使用

---

#### 外部ライブラリ
- `requests`  
  → Ollama APIとの通信に使用

Ollama は Ollama, Inc. の提供するソフトウェアです。  

## 使用モデル

- gemma3:1b (via Ollama)

---

## Ollamaについて

本アプリは、ローカルLLM実行環境である「Ollama」を利用しています。

Ollamaは、PC上で軽量な大規模言語モデル（LLM）を動作させるためのツールです。

### インストール
以下の公式サイトよりインストールしてください：
https://ollama.com/

### モデルのダウンロード

```bash
ollama pull gemma3:1b
````
## 使用モデルについて

本アプリでは以下のモデルを使用しています：

- gemma3:1b（Google Gemma）

### 特徴
- 軽量（低スペックPCでも動作可能）
- 応答速度が速い
- シンプルな対話用途に適している

GemmaはGoogleが提供する軽量LLMであり「Gemma Terms of Use」に基づいて利用されています。

詳細：
https://ai.google.dev/gemma/terms

※ Gemma3 1B はオープンウェイトモデルですが、
完全なオープンソースではなく独自ライセンスが適用されます。

※ 今話題の Gemma4 E2B の使用も検討しましたが、本開発環境ではメモリ不足により動作が困難であったため、
本モデルを採用しています。  

### モデルの変更について

`MODEL_NAME` を変更することで、他のモデルにも対応可能です：

```python
MODEL_NAME = "llama3"
````

※ 使用するモデルは、事前にOllamaでダウンロードしておく必要があります

---

### APIについて

本アプリは以下のエンドポイントに接続します：

```
http://localhost:11434/api/chat
```

※ `localhost` はユーザー自身のPCを指します
※ ポート `11434` はOllamaのデフォルト設定です

---

### 使用エディター
- Visual Studio Code (VS Code)

---

### 著作権表示とライセンス

## 📂 ライセンスファイルまとめ[licenses](./licenses/)
- Python [LICENSE-PSF.txt](./licenses/LICENSE-PSF.txt)
- Tkinter [Tcl/Tk License](./licenses/third_party/LICENSE-TclTk.txt)
- Requests License [Apache License 2.0](./licenses/third_party/requests_LICENSE.txt) 
- Requests NOTICE [NOTICE](./licenses/third_party/requests_NOTICE.txt) 

---

### **Python**  
- Copyright © 2001 Python Software Foundation. All rights reserved.
Licensed under the PSF License Version 2.  
[Python license](https://docs.python.org/3/license.html)  
※ 通常の利用においては追加のライセンス同梱は不要ですが、配布形態によっては別途対応が必要となる場合があります。  

#### **Tkinter**  
- © Regents of the University of California, Sun Microsystems, Inc., Scriptics Corporation, and other parties  
TkinterはPythonに含まれるGUIライブラリですが、その動作にはTcl/Tkが使用されています。  
- [Tcl/Tk License](https://www.tcl.tk/software/tcltk/license.html)  

#### **Requests**

- Copyright: Copyright 2019 Kenneth Reitz  
- License: Apache License 2.0  

This product includes software developed by Kenneth Reitz.  
- [Apache License 2.0](./licenses/third_party/requests_LICENSE.txt) 
- [NOTICE](./licenses/third_party/requests_NOTICE.txt) 

---

これらのプロジェクトの開発者の皆様、貢献者の皆様に、心より感謝申し上げます。  

---

## ライセンス

本プロジェクトは、「コード」と「キャラクタープロンプト集」で
それぞれ異なるライセンスを採用しています。

---

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

---

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

---

#### ライセンスの理由
現在のAI生成コンテンツの状況を踏まえ、私は本作品を可能な限りオープンなライセンス設定になるように心がけました。  
問題がある場合、状況に応じてライセンスを適切に見直す予定です。  

このライセンス設定は、権利の独占を目的とするものではありません。  
明確なライセンスを設定することにより、パブリックドメイン化するリスクを避けつつ、自由な利用ができるように期待するものです。  
  
© 2026 AglaoDev-jp  