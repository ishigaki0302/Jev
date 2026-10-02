# Jev
Jev周りの環境構築や検証，ツール化用

## 構成

| パス | 内容 |
|---|---|
| `JEV.md` | **まずここ**: Jev（判定モデル）とは何か、Ollaya・clef:flash との関係 |
| `NOTES.md` | Ollaya / clef-flash の調査メモ |
| `LOG.md` | 作業ログ（手順・参照リンク・結果） |
| `install.sh` | 実行した Ollaya インストールスクリプトの写し（v0.9.0 時点） |
| `mcp/jev_mcp.py` | clef:flash に固定した MCP サーバー（標準ライブラリのみ） |
| `mcp/show_log.py` | 呼び出しログ（`logs/calls.jsonl`）を確認するスクリプト |
| `.claude/skills/jev/` | どんなときに Jev に委任するかを Claude に伝えるスキル |
| `eval/` | 委任候補タスクの評価セットと結果 |

## 使い方（Claude Code から）

前提: Ollaya と clef:flash を入れておく（`LOG.md` の 2〜7 の項を参照）。

ユーザー全体の設定（`~/.claude.json`）に `jev` を登録してあり、どのプロジェクトの Claude Code からでも次のツールが使える。

| ツール | 内容 |
|---|---|
| `mcp__jev__decide` | 1 件（`state`）または複数（`states`）の項目に、型付きの質問（choice / score / noul）で判定させる |
| `mcp__jev__status` | Ollaya サーバーの状態と、読み込まれているモデルを表示する |

- スキル `~/.claude/skills/jev` は、このリポジトリの `.claude/skills/jev` へのシンボリックリンク。
- モデルは clef:flash に固定し、30 分はメモリに残す（`JEV_MODEL`、`JEV_KEEP_ALIVE` で変更できる）。
- 1 件 3〜6 秒（CPU 実行）。アイドル後の初回だけロードに約 20 秒かかる。メモリは約 19GB 使う。
- 判定専用なので、要約や文章生成はできない。

### ログの確認

呼び出しはすべて `logs/calls.jsonl` に 1 行 1 件で記録する（他プロジェクトの内容を含むため git 管理外）。

```bash
python3 mcp/show_log.py            # 集計と直近 20 件
python3 mcp/show_log.py --low      # 確信度が低かった判定だけ
python3 mcp/show_log.py --full 1   # 直近の呼び出しを全文表示
```

### 削除するとき

```bash
claude mcp remove jev -s user
rm ~/.claude/skills/jev
```
