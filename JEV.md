# Jev とは何か：判定モデル（System One モデル）の全体像

調査日: 2026-10-02

## 最初に：このリポジトリで動かしているものは「Jev そのもの」ではない

| 呼び名 | 正体 | どこで動く | 重み |
|---|---|---|---|
| **Jev** | TypeSafe AI 社の判定モデル | TypeSafe のクラウド（API） | 非公開 |
| **Ollaya** | Jev と同じ API で、オープンな判定モデルを手元で動かすツール | 自分の PC | — |
| **clef:flash** | Cloudflare が公開した判定モデル。Ollaya 経由で使っている | 自分の PC（CPU） | 公開（Apache-2.0） |
| このリポジトリの `jev` ツール | clef:flash を Claude Code から呼ぶための自作 MCP サーバー | 自分の PC | — |

このリポジトリでは、本家 Jev は一度も呼んでいない。**本家 Jev と同じ種類の「判定モデル」を、オープンなモデル（clef:flash）を使って手元で動かしている**、というのが正確な説明になる。リポジトリ名の Jev は、この種類のモデルの代表として付けた呼び名である。

## 1. 一言でいうと

Jev は「**文章を書かずに、判断だけを返す AI**」である。

普通の LLM（Claude や GPT）は、質問に文章で答える。Jev は、テキストや JSON と「型の決まった質問」を受け取り、**あらかじめ用意した選択肢のどれに当たるかを確率つきで返す**。トークンを生成しないので、速くて安く、決められた選択肢以外の答えを返すことがない。

```
入力（state）: 「3日前から Stripe 連携が失敗していて売上を失っています。至急助けて」
質問: 担当チームは？ / 苛立ちの度合いは？ / 緊急か？
   ↓
出力: technical（0.85） / 1：苛立っているが丁寧（0〜2 の尺度） / 緊急である確率 1.0
```

（TypeSafe 公式の quickstart の例。出典: [TypeSafe Quick start](https://docs.typesafe.ai/introduction/quickstart)、[awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev)）

## 2. 背景：System One モデルという考え方

TypeSafe は Jev を「**System One モデル**」と呼んでいる。これは、心理学者ダニエル・カーネマンの「速い直感（System 1）と遅い熟考（System 2）」の区別から取った名前である（[MarkTechPost](https://www.marktechpost.com/2026/09/19/typesafe-ai-releases-jev/)）。

- **System 2（従来の LLM）**: じっくり考え、文章を生成する。柔軟だが遅く、高く、自信過剰になりやすい。
- **System 1（Jev）**: 状況を読んで、瞬時に判断する。生成しないので速く安い。

TypeSafe は、チャット向けの LLM は RLHF（人間の評価による強化学習）で調整されるため「自信過剰」や「答えの偏り」が起きやすいと指摘している。Jev は代わりに **RLCD（Reinforcement Learning for Calibrated Decisions：較正された判断のための強化学習）** という手法で学習しており、返す確率が実際の正解率と一致するよう調整されている（[TypeSafe AI](https://typesafe.ai/)、[MarkTechPost](https://www.marktechpost.com/2026/09/19/typesafe-ai-releases-jev/)）。

「較正されている（calibrated）」とは、たとえば「確率 0.9」と答えたケースを集めると実際に約 9 割が正解している、という性質のことである。この性質があるので、「確率が高ければ自動で処理し、低ければ人や LLM に回す」という使い方ができる。

## 3. Jev の基本情報

| 項目 | 内容 | 出典 |
|---|---|---|
| 開発元 | TypeSafe AI（創業者: Diogo Almeida、Erik Gafni、Sasha Sheng） | [OpenRouter](https://openrouter.ai/blog/insights/what-is-jev/) |
| 公開 | 2026 年 9 月 15 日にアーリーアクセス開始（報道は 9 月 19 日） | [OpenRouter](https://openrouter.ai/blog/insights/what-is-jev/)、[MarkTechPost](https://www.marktechpost.com/2026/09/19/typesafe-ai-releases-jev/) |
| 提供形態 | クラウド API のみ（ウェイトリスト制）。重みとセルフホストは非公開 | [MarkTechPost](https://www.marktechpost.com/2026/09/19/typesafe-ai-releases-jev/) |
| API | `POST https://api.typesafe.ai/v1/systemone`。モデル名は `jev-latest` など | [LiteLLM docs](https://docs.litellm.ai/docs/pass_through/typesafe) |
| 料金 | 入力 10 億トークンあたり 42 ドル。出力は無料（生成しないため） | [TypeSafe AI](https://typesafe.ai/) |
| 速度 | エンドツーエンドで 70〜500 ms | [MarkTechPost](https://www.marktechpost.com/2026/09/19/typesafe-ai-releases-jev/) |
| アーキテクチャ | 非公開（新しいアーキテクチャ＋並列サンプラー＋RLCD とだけ説明） | [MarkTechPost](https://www.marktechpost.com/2026/09/19/typesafe-ai-releases-jev/) |

TypeSafe は「LLM より 193.6 倍速く、244.6 倍安い」とうたっている（[TypeSafe AI](https://typesafe.ai/)）。ただし、比較に使ったワークフローは TypeSafe 自身が作ったもので、同社も「実際の利用ではこの上限に近い値になるとは限らない」と認めている（[MarkTechPost](https://www.marktechpost.com/2026/09/19/typesafe-ai-releases-jev/)）。「ハルシネーションしない」という主張も、「選択肢の外の答えを返せない」という意味であり、**判断を間違えないという意味ではない**。

## 4. 3 種類の質問

Jev への質問は、次の 3 種類のどれかで書く。1 回のリクエストに複数を混ぜてよく、それぞれ独立に評価される（[TypeSafe docs](https://docs.typesafe.ai/)）。

| 型 | 何を聞くか | 返ってくるもの | 例 |
|---|---|---|---|
| **choice** | 選択肢のどれか（最大 255 個） | 選ばれた選択肢、各選択肢の確率、確信度 | 担当チームは billing / technical / other のどれ？ |
| **score** | 順序のある尺度（2〜10 段階）のどこか | 尺度上の位置、各段階の確率、確信度 | 苛立ちは 0（冷静）〜3（激怒）のどれ？ |
| **noul** | ある文が正しいか（yes/no） | yes である確率（0〜1） | 返金を求めているか？ |

（上限の数値: [awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev)、[datacamp](https://www.datacamp.com/blog/system-one-models-jev)）

「noul」は TypeSafe 独自の用語で、0 に近いほど強い No、1 に近いほど強い Yes、0.5 付近は「どちらとも言えない」を意味する。

## 5. 何に使うか、何に使わないか

TypeSafe の設計方針は、「**ルールはコード、曖昧な判断は Jev、文章は LLM**」と役割を分けることである（[How to build with TypeSafe](https://docs.typesafe.ai/concepts/how-to-build-with-system-one)、[awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev)）。

| その処理に必要なもの | 使うもの | 例 |
|---|---|---|
| 決まったルールの適用 | コード | アカウントのフラグを確認する |
| 曖昧な内容を、決まった選択肢で判断 | **Jev** | 問い合わせを billing / technical に振り分ける |
| 文章を書く、自由な課題を解く | LLM | 振り分けた後に返信文を書く |

公式に挙がっている用途: コマンドの安全性チェック、メールのトリアージ、ブラウザ操作エージェント、電話エージェント、動画の採点、エージェントのガードレール、データベースの行の絞り込み、ゲーム（StarCraft）など（[MarkTechPost](https://www.marktechpost.com/2026/09/19/typesafe-ai-releases-jev/)）。

## 6. Jev を使う経路

| 経路 | 内容 |
|---|---|
| TypeSafe 直接 | 公式 SDK（Python / JavaScript）と API キー。[Console](https://console.typesafe.ai/) でキーを発行 |
| Cloudflare Workers AI | `typesafe/jev` として提供（[Cloudflare docs](https://developers.cloudflare.com/ai/models/typesafe/jev/)） |
| Vercel AI Gateway | `typesafe-ai/jev`（[Vercel changelog](https://vercel.com/changelog/typesafe-ai-jev-now-available-on-ai-gateway)） |
| OpenRouter | decisions API で `typesafe/jev-1.13`（[OpenRouter](https://openrouter.ai/labs/jev/compile)） |
| Netlify AI Gateway | 公式 SDK を Netlify Functions から使う（[Netlify docs](https://docs.netlify.com/build/ai-gateway/overview/)） |

（一覧の出典: [awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev)）

どの経路でも、**入力（state）は外部のサーバーに送られる**。社内のコードや機密情報を扱うなら、次の「ローカルで動かす」選択肢が重要になる。

## 7. ローカルで動かす：Ollaya とオープンな判定モデル

### Ollaya

[Ollaya](https://ollaya.dev/) は「**判定モデル版の Ollama**」である。オープンな判定モデルをダウンロードして手元で動かし、TypeSafe の `/v1/systemone` と同じ形式の API を提供する。環境変数 `TYPESAFE_BASE_URL=http://localhost:11435` を設定すれば、Jev 向けに書いたコードをそのまま手元のモデルに向けられる（[ollaya-dev/ollaya](https://github.com/ollaya-dev/ollaya)）。

- 作者: Mert Cobanov 氏。TypeSafe の公式製品ではない
- 公開: 2026 年 9 月 23 日に GitHub リポジトリ作成。ライセンスは Apache-2.0
- モデルの重みは各作者の Hugging Face リポジトリから、コミットを固定して sha256 で検証しながら取得する

### Ollaya で使える主なモデル

Ollaya 公式の比較表（RTX 4090、5 問のリクエストの中央値）から抜粋した（[ollaya.dev](https://ollaya.dev/)）。

| モデル | 作者・ベース | 正解率 | 遅延 | Mac の GPU |
|---|---|---|---|---|
| TypeSafe Jev（クラウド） | TypeSafe | 0.738 | 236〜276 ms | — |
| winnow:e4b | 4B 級の LLM ベース（GGUF） | 0.722 | 89 ms | ✗ |
| kev:9b | Qwen3.5-9B ＋ポインターヘッド | 0.722 | 498 ms | ✗ |
| **clef:flash** | **Cloudflare**（Qwen3.5-9B ＋ joint schema head） | **0.703** | 532 ms | ✗ |
| decider:4b | Qwen3.5 ベース（AWS Strands Decider 系） | 0.680 | 520 ms | ✗ |
| jeeves:9b | PostHog（Qwen3.5-9B） | 0.680 | 838 ms | ✗ |
| nli | 汎用の自然言語推論モデル | 0.548 | 20 ms | ✓ |
| laya:en | 軽量モデル（421M） | 0.361 | 10 ms | ✓ |

Mac では、GPU（MLX）で動くのは laya と nli だけとされている（公式サイトの記述。実測では nli も CPU だった）。それ以外のモデルは CPU で動く。

### clef:flash

[Cloudflare/clef-flash](https://huggingface.co/Cloudflare/clef-flash) は Cloudflare が公開した 9B の判定モデルである。

- ベースは Qwen3.5-9B（ビジョンエンコーダつき）。テキスト・JSON・画像・動画を入力できる
- 「joint schema head」という出力部で、すべての質問と選択肢をまとめて 1 回で採点する
- ライセンスは Apache-2.0
- 本家の推奨環境は H200 GPU ＋ transformers / vLLM / SGLang
- Ollaya では ONNX 形式・F32 精度・CPU 実行になる（約 19GB、1 件 3〜6 秒）
- 対応言語は英語のみ

## 8. 使う前に知っておくべき限界

コミュニティの独立した検証で、次のような失敗パターンが報告されている（[awesome-typesafe-jev「Before you trust a decision」](https://github.com/AbdelStark/awesome-typesafe-jev)）。いずれも特定のタスクでの結果で、一般化はできない。

| 論点 | 報告された結果 |
|---|---|
| 答えるか、保留するか | 曖昧な問題で「unknown」を選べると 95% がそれを選んだ。選択肢から外すと、79% がステレオタイプ通りの答えを選んだ（[KoBBQ audit](https://github.com/jujumilk3/jev-calibration-audit/blob/main/FINDINGS.md)） |
| LLM へのフォールバック | 確信度が低いときだけ LLM に回す構成は、データセットによって効果があったりなかったりした（[Janus](https://github.com/FirasSX914/Janus/blob/main/RESEARCH.md)） |
| 確率で並べ替え | 分類が得意でも、確率をそのまま並べ替えの基準に使うとうまくいかないことがある（[jev-orderby-bench](https://github.com/yodablocks/jev-orderby-bench/blob/main/README.md)） |
| エージェントの操作の承認 | 111 件中、Jev は 100 件、Claude は 102 件で正解。どちらも危険な操作を 1 件許可した（[agent-action-gate](https://github.com/ghubnab99/jev-enterprise-decision-fabric/blob/main/docs/evaluations/agent-action-gate-v1.md)） |

複数の判定モデルを横並びで比べたベンチマークとして [JevBench](https://github.com/fstandhartinger/jevbench) がある。

教訓は、**自分のタスクで正解率を測り、閾値と「確信度が低いときにどうするか」をコード側で決めること**である。

## 9. このリポジトリでの位置づけと分かったこと

| 項目 | 内容 |
|---|---|
| 目的 | Claude Code が判断の手前で、ローカルの判定モデルに安く判定させてトークンを節約する |
| 使っているもの | Ollaya 0.9.0 ＋ clef:flash（CPU 実行） |
| Claude Code との接続 | 自作の MCP サーバー `mcp/jev_mcp.py`（ユーザー全体に登録） |
| 自前の評価（74 件） | clef:flash 0.99、laya 0.85、nli 0.68（`eval/`、`LOG.md` の 9〜13 の項） |
| 分かった弱点 | 1 件 3〜6 秒と遅い。英語専用で、日本語の依頼文が混ざると判定が甘くなった（`LOG.md` の 16 の項） |

## 10. 用語集

| 用語 | 意味 |
|---|---|
| 判定モデル（decision model） | 文章を生成せず、決まった選択肢について確率を返すモデル |
| System One モデル | TypeSafe による判定モデルの呼び名。カーネマンの「速い直感」から |
| state | 判断の対象（テキスト、JSON、メッセージなど） |
| choice / score / noul | 質問の 3 つの型（選択 / 尺度 / yes・no） |
| 較正（calibration） | 出力された確率が、実際の正解率と一致している性質 |
| RLCD | Reinforcement Learning for Calibrated Decisions。Jev の学習手法 |
| preset | Ollaya に組み込まれた質問セット（triage、agent、guard など） |
| MCP | Model Context Protocol。Claude Code などに外部ツールをつなぐ仕組み |

## 参考リンク

公式（TypeSafe）
- [TypeSafe AI](https://typesafe.ai/)
- [TypeSafe docs](https://docs.typesafe.ai/)（[Quick start](https://docs.typesafe.ai/introduction/quickstart)、[How to build with TypeSafe](https://docs.typesafe.ai/concepts/how-to-build-with-system-one)、[全ページの索引](https://docs.typesafe.ai/llms.txt)）
- [TypeSafe Console](https://console.typesafe.ai/)
- [TypeSafe evals](https://evals.typesafe.ai/)

解説記事
- [MarkTechPost: TypeSafe AI Releases Jev](https://www.marktechpost.com/2026/09/19/typesafe-ai-releases-jev/)
- [MarkTechPost: A Coding Guide to TypeSafe AI Jev](https://www.marktechpost.com/2026/09/23/a-coding-guide-to-typesafe-ai-jev/)
- [OpenRouter: What Is Jev?](https://openrouter.ai/blog/insights/what-is-jev/)
- [DataCamp: Jev: TypeSafe's System One Model Explained](https://www.datacamp.com/blog/system-one-models-jev)
- [Flavio Copes: A deep dive into Jev](https://flaviocopes.com/jev/)

コミュニティ・ローカル実行
- [awesome-typesafe-jev](https://github.com/AbdelStark/awesome-typesafe-jev)（SDK、事例、独立検証のまとめ）
- [Ollaya](https://ollaya.dev/) / [GitHub](https://github.com/ollaya-dev/ollaya)
- [Cloudflare/clef-flash（Hugging Face）](https://huggingface.co/Cloudflare/clef-flash)
- [JevBench](https://github.com/fstandhartinger/jevbench)
- [LiteLLM: TypeSafe AI (Jev)](https://docs.litellm.ai/docs/pass_through/typesafe)
