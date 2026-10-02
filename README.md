# Jev
Jev周りの環境構築や検証，ツール化用

## 構成

| パス | 内容 |
|---|---|
| `NOTES.md` | Ollaya / clef-flash の調査メモ |
| `LOG.md` | 作業ログ（手順・参照リンク・結果） |
| `install.sh` | 実行した Ollaya インストールスクリプトの写し（v0.9.0 時点） |
| `.mcp.json` | Claude Code から Ollaya を MCP ツール（`decide` など）として呼ぶ設定 |
| `.claude/skills/ollaya-decisions/` | Ollaya 同梱のエージェント用スキル（Apache-2.0） |

## 使い方（Claude Code から）

このディレクトリで `claude` を起動すると `.mcp.json` が読まれ、ローカルの判定モデルを `decide` ツールとして使えるようになる（初回は承認が必要）。
分類・ルーティング・yes/no 判定・スコアリングはローカルで処理できる。要約や文章生成はできない。
