# Jev
Jev周りの環境構築や検証，ツール化用

## 構成

| パス | 内容 |
|---|---|
| `NOTES.md` | Ollaya / clef-flash の調査メモ |
| `LOG.md` | 作業ログ（手順・参照リンク・結果） |
| `install.sh` | 実行した Ollaya インストールスクリプトの写し（v0.9.0 時点） |
| `mcp/jev_mcp.py` | clef:flash に固定した MCP サーバー（標準ライブラリのみ） |
| `.mcp.json` | Claude Code から `jev` を MCP ツールとして呼ぶ設定 |
| `.claude/skills/jev/` | どんなときに Jev に委任するかを Claude に伝えるスキル |
| `eval/` | 委任候補タスクの評価セットと結果 |

## 使い方（Claude Code から）

前提: Ollaya と clef:flash を入れておく（`LOG.md` の 2〜7 の項を参照）。

このディレクトリで `claude` を起動すると `.mcp.json` が読まれ、次のツールが使えるようになる（初回は承認が必要）。

| ツール | 内容 |
|---|---|
| `mcp__jev__decide` | 1 件（`state`）または複数（`states`）の項目に、型付きの質問（choice / score / noul）で判定させる |
| `mcp__jev__status` | Ollaya サーバーの状態と、読み込まれているモデルを表示する |

- モデルは clef:flash に固定し、30 分はメモリに残す（`JEV_MODEL`、`JEV_KEEP_ALIVE` で変更できる）。
- 1 件 3〜6 秒（CPU 実行）。アイドル後の初回だけロードに約 20 秒かかる。メモリは約 19GB 使う。
- 判定専用なので、要約や文章生成はできない。
