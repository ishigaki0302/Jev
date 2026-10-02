# 作業ログ: Ollaya / clef-flash

環境: Apple M5 Max / 64GB / macOS 26.7 / 作業ディレクトリ `~/dev/study/Jev`

## 参照したリンク

| URL | 内容 |
|---|---|
| https://ollaya.dev/ | ツール概要・対応環境・モデル一覧（`clef:flash` を含む） |
| https://ollaya.dev/download | インストールコマンド |
| https://ollaya.dev/docs/quickstart | コマンド一覧・API 例（`/api/decide`） |
| https://huggingface.co/Cloudflare/clef-flash | モデルカード（9B、Qwen3.5-9B ベース、BF16、Apache-2.0） |
| https://ollaya.dev/install.sh | インストールスクリプト（`./install.sh` に保存） |

## 2026-10-02

### 1. 調査
- 上記ページを読み、結果を `README.md` にまとめた。

### 2. install.sh の確認
- `curl -fsSL https://ollaya.dev/install.sh -o install.sh` で保存し、全 577 行を読んだ。
- 確認できたこと:
  - バイナリは GitHub Releases（`ollaya-dev/ollaya`）から取得し、`sha256sum.txt` で検証する。
  - macOS では `ollaya-darwin-arm64` 本体と MLX の Metal ライブラリを入れる。
  - インストール先は既定が `/usr/local`（書けなければ sudo）。`OLLAYA_INSTALL_DIR` で変えられる。
  - macOS ではサービス登録をしない（systemd は Linux のみ）。サーバーは CLI がバックグラウンドで起動する。
  - 配置されるもの: `bin/ollaya`、`lib/ollaya/`（MLX）、`share/doc/ollaya/`、`share/ollaya/skills/`
- 判断: sudo を避けるため `OLLAYA_INSTALL_DIR=$HOME/.local` で入れる。

### 3. インストール
```bash
OLLAYA_INSTALL_DIR=$HOME/.local sh install.sh
```
- 結果: Ollaya 0.9.0 を `~/.local/bin/ollaya` に配置（約 59MB）。MLX の Metal ライブラリも入った。
- `~/.local/bin` は PATH に入っていないので、必要なら `~/.zshrc` に `export PATH="$HOME/.local/bin:$PATH"` を追加する。
- モデル保存先: `~/.ollaya/models`（`blobs/`、`manifests/`）

### 4. laya で動作確認
```bash
ollaya run laya --preset triage --verbose "Hi, I cannot log in since this morning and I have a demo at 3pm."
```
- 自動で `laya:en` に振り分けられた。判定時間は 227ms、入力は 334 トークン。
- 初回はモデルのダウンロード（laya:en 853MB ＋ laya:multilingual 683MB）があり、全体で約 4 分半かかった。
- 結果: intent は other 0.53 / technical_help 0.43、is_urgent は yes 0.68、refund_requested は no 1.00。

### 5. Claude Code 連携の調査
- `ollaya mcp` で MCP サーバーとして起動できる（stdio、または `--http` で 127.0.0.1:11436）。
- 提供されるツール: `decide`、`list_models`、`show_model`、`pull_model`
- 同梱スキル: `~/.local/share/ollaya/skills/ollaya-decisions/SKILL.md`
- 注意: Ollaya は判定専用で、文章を生成しない。Claude Code から委任できるのは、分類・ルーティング・yes/no 判定・スコアリングに限られる。
- 同梱スキルによると、clef は「24GB GPU が必要」とされている。Mac のユニファイドメモリで動くかは実測して確かめる。
- 対応: リポジトリに `.mcp.json`（project スコープ）と `.claude/skills/ollaya-decisions/` を置いた。

### 6. GitHub リポジトリ
- `git@github.com:ishigaki0302/Jev.git`。既存の Initial commit（README、LICENSE、.gitignore）の上に積んだ。
- 調査メモは `README.md` から `NOTES.md` に名前を変えた。

### 7. clef:flash の取得（実行中）
```bash
ollaya pull clef:flash
```
- 2026-10-02 16:05 時点で約 2GB。バックグラウンドで続行中。

### 8. MCP サーバーの動作確認（stdio）
JSON-RPC で `initialize` → `tools/list` → `tools/call(decide)` の順に `ollaya mcp` へ直接送った。
```json
{"name":"decide","arguments":{"model":"laya","state":"このPRはREADMEの誤字修正のみです",
 "questions":{"risky":{"type":"noul","instructions":"Is this change risky to merge?"}}}}
```
- 応答: `{"model":"laya:multilingual","answers":{"risky":{"type":"noul","noul":0.0036}},"usage":{"input_tokens":43,"output_tokens":0}}`
- 日本語は自動で `laya:multilingual` に振り分けられた。MCP 経由でも正常に動いている。
- Claude Code が `.mcp.json` を読むのはセッション起動時。`Jev/` で `claude` を起動し直すと `mcp__ollaya__decide` が使えるようになる。
