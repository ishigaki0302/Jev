# Ollaya / clef-flash ローカル実行メモ

調査日: 2026-10-02
環境: Apple M5 Max / メモリ 64GB / macOS 26.7

## 1. Ollaya とは

- 公式: https://ollaya.dev/
- 判定（decision）モデルをローカルで動かすオープンソースの CLI。
- テキストや JSON（= state）と型付きの質問（= schema）を渡すと、選択肢ごとの確率が返ってくる。文章を生成する LLM ではない。
- 外部 API を呼ばないので、データは手元から出ない。

### 対応環境

| OS | 条件 |
|---|---|
| macOS | Apple silicon、macOS 14 以上（一部モデルは MLX で GPU を使う） |
| Windows | 10 / 11（x64） |
| Linux | x86-64 / ARM64 |
| その他 | WSL 2、Docker（amd64 / arm64） |

NVIDIA GPU は CUDA 12 / 13 に対応。

### 利用できるモデル（公式サイトの一覧より）

| 系列 | タグ |
|---|---|
| winnow | 7.5b, 12b, e4b |
| laya | multilingual, en（322m / 421m） |
| decider | 0.8b, 2b, 4b |
| kev | 0.8b, 4b, 9b |
| nli | 396m, 435m |
| gliclass | 439m |
| qwen3guard | 0.6b |
| decision | 0.75b |
| nimble | 9b |
| clef | flash ほか |

モデルは Hugging Face 上のオープンウェイトで、コミット固定・SHA256 検証つきで取得される。

## 2. インストール

```bash
curl -fsSL https://ollaya.dev/install.sh | sh
```

- 実行前にスクリプトの中身を確認しておくと安全（`curl -fsSL https://ollaya.dev/install.sh | less`）。
- 社用 Mac では Defender for Endpoint が反応する可能性がある。必要なら情シスに事前に相談する。
- バイナリの配置先・モデル保存先・アンインストール手順は、公式ドキュメントに記載がなかった（要確認）。

## 3. 使い方

```bash
# まず軽いモデルで動作確認
ollaya run winnow:e4b

# サーバーを起動（http://localhost:11435）
ollaya serve
```

その他のコマンド: `ollaya pull` / `ollaya list` / `ollaya rm` / `ollaya create`（Modelfile から独自モデルを作る）

### API 呼び出し例

```bash
curl http://localhost:11435/api/decide -d '{
  "model": "winnow:e4b",
  "state": "Hi, I cannot log in since this morning and I have a demo at 3pm.",
  "questions": {
    "angry": {"type": "noul", "instructions": "Is the customer angry?"}
  }
}'
```

- TypeSafe API と互換（`/v1/systemone`）。TypeSafe Python SDK 0.7.1 以上で、接続先を `http://localhost:11435` に向ければそのまま使える。
- レスポンス JSON の完全な例は公式ページに載っていない。CLI では選択肢ごとの確率がバーで表示される。

## 4. Cloudflare/clef-flash

- モデルページ: https://huggingface.co/Cloudflare/clef-flash

| 項目 | 内容 |
|---|---|
| 用途 | state と質問の schema から判定を返す（文章は生成しない） |
| ベース | Qwen/Qwen3.5-9B ＋ ビジョンエンコーダ |
| パラメータ数 | 9B |
| 入力 | テキスト / JSON / 画像 / 動画 |
| 特徴 | joint schema head が全質問・全選択肢をまとめてスコアリング |
| 精度 | BF16（重みは約 18GB） |
| 形式 | safetensors（`model-*.safetensors`、`joint_head.safetensors`）＋ 独自コード `joint_schema_model.py` |
| ライセンス | Apache-2.0 |
| 公式の検証環境 | H200 1 枚、torch 2.11 以上、transformers 5.10.2 |
| 推論基盤 | transformers / vLLM / SGLang / Docker |

### ローカルで使えるか

**使える見込み。** ollaya のモデル一覧に `clef:flash` がある。

```bash
ollaya run clef:flash
```

- BF16 で約 18GB なので、メモリ 64GB の Mac なら収まる。
- vLLM / SGLang は Mac では実用的でないため、Mac では ollaya 経由が手軽。
- ollaya 上の clef:flash が MLX（GPU）に対応しているかは未確認。CPU 実行になると遅い可能性がある。

## 5. 進め方

1. install.sh の中身を確認してからインストール
2. `ollaya run winnow:e4b` で動作確認
3. `ollaya run clef:flash` を試す
4. `ollaya serve` を起動して API から呼ぶ
5. 未確認点（保存先、アンインストール、MLX 対応、レスポンス形式）を実際に確かめてこのメモに追記する
