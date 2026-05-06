# Ollama 起動・確認・停止 手順メモ

## 1. Ollamaを起動する

Windowsでは通常、Ollamaを起動するとバックグラウンドで待機します。

### 方法

- スタートメニューから「Ollama」を起動
- または `ollama run モデル名` を実行

例：

```powershell
ollama run gemma3:1b
````

初回はモデル読込後、そのまま対話モードになります。

終了する場合：

```powershell
/bye
```

---

## 2. Ollamaが起動中か確認する

### Ollamaサーバー確認

```powershell
ollama list
```

正常時：

```powershell
NAME            ID              SIZE
gemma3:1b       xxxxxxxx        815 MB
```

停止時：

```powershell
Error: could not connect to ollama app
```

---

## 3. 現在動作中のモデル確認

```powershell
ollama ps
```

例：

```powershell
NAME         ID         SIZE      PROCESSOR
gemma3:1b    xxxx       1.2 GB    CPU
```

確認できる内容：

* 現在ロード中のモデル
* メモリ使用中モデル
* CPU/GPU利用状況

---

## 4. モデルを停止する

```powershell
ollama stop gemma3:1b
```

これでモデルをメモリから解放できます。

※ Ollama本体は起動したままです。

---

## 5. Ollamaアプリ自体を終了する

Windows右下のタスクトレイから：

* Ollamaアイコン右クリック
* 「Quit Ollama」

これで `localhost:11434` のAPIも停止します。


強制終了（うまくいかなかった）
```
taskkill /IM ollama.exe /F
```
PowerShellで（うまくいかなかった）
```
Stop-Process -Name "ollama"
```

Get-Process ollama

CLIで終了できたらいいのにね。
ってかこれずっと動きっぱなしなんじゃないんですかね？

---

# 補足

## localhost:11434 とは？

OllamaはローカルPC内でHTTPサーバーとして動作しています。

Pythonなどから：

```python
http://localhost:11434/api/generate
```

へアクセスすることでAIと通信できます。

---

## ブラウザで動作確認

ブラウザで：

```text
http://localhost:11434
```

へアクセス。

正常時：

```text
Ollama is running
```

と表示されます。

---

# よく使うコマンドまとめ

```powershell
# モデル一覧
ollama list

# 現在動作中モデル確認
ollama ps

# モデル停止
ollama stop gemma3:1b

# モデル起動
ollama run gemma3:1b

