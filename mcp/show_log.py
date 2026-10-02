#!/usr/bin/env python3
"""Jev の呼び出しログ（logs/calls.jsonl）を確認する。

使い方:
  python3 mcp/show_log.py            # 集計と直近 20 件
  python3 mcp/show_log.py -n 50      # 直近 50 件
  python3 mcp/show_log.py --low      # 確信度が低かった判定だけ（0.2 < p < 0.8）
  python3 mcp/show_log.py --full 3   # 直近から 3 番目の呼び出しを全文表示
"""
import argparse
import collections
import json
import os

LOG = os.environ.get("JEV_LOG", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                              "logs", "calls.jsonl"))


def load():
    if not os.path.exists(LOG):
        return []
    with open(LOG, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def answers_of(entry):
    """呼び出し 1 回分の (項目番号, 質問ID, 答え) を並べる。"""
    r = entry.get("result") or {}
    if "answers" in r:
        return [(0, q, a) for q, a in r["answers"].items()]
    return [(item["index"], q, a) for item in r.get("results", []) for q, a in item["answers"].items()]


def confidence(a):
    if a["type"] == "noul":
        return max(a["p_true"], 1 - a["p_true"])
    return a["confidence"]


def fmt(a):
    if a["type"] == "noul":
        return f"p_true={a['p_true']:.2f}"
    if a["type"] == "choice":
        return f"{a['choice']} ({a['confidence']:.2f})"
    return f"score={a['score']:.2f} ({a['confidence']:.2f})"


def short(x, n=70):
    s = x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)
    s = s.replace("\n", " ")
    return s if len(s) <= n else s[:n - 1] + "…"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", type=int, default=20)
    ap.add_argument("--low", action="store_true")
    ap.add_argument("--full", type=int)
    opt = ap.parse_args()
    rows = load()
    if not rows:
        print(f"ログがありません: {LOG}")
        return
    if opt.full:
        print(json.dumps(rows[-opt.full], ensure_ascii=False, indent=2))
        return

    decides = [r for r in rows if r["tool"] == "decide" and not r["error"]]
    items = sum(len((r["args"].get("states") or [None])) for r in decides)
    errors = [r for r in rows if r["error"]]
    print(f"ログ: {LOG}")
    print(f"期間: {rows[0]['ts']} 〜 {rows[-1]['ts']}")
    print(f"decide: {len(decides)} 回（{items} 項目）  エラー: {len(errors)} 回")
    if decides:
        secs = sorted(r["seconds"] for r in decides)
        print(f"所要時間: 中央値 {secs[len(secs) // 2]:.1f} 秒、最大 {secs[-1]:.1f} 秒")
    print("プロジェクト別:", dict(collections.Counter(os.path.basename(r["cwd"]) for r in rows)))
    kinds = collections.Counter(r["args"].get("preset") or "+".join(sorted(r["args"].get("questions") or {}))
                                for r in decides)
    print("質問の種類:", dict(kinds.most_common(10)))
    print()

    for i, r in enumerate(rows[-opt.n:][::-1], 1):
        if r["error"]:
            print(f"[{i}] {r['ts']} {os.path.basename(r['cwd'])} ERROR {r['error']}")
            continue
        if r["tool"] != "decide":
            continue
        states = r["args"].get("states") or [r["args"].get("state")]
        shown = [(idx, q, a) for idx, q, a in answers_of(r) if not opt.low or confidence(a) < 0.8]
        if not shown:
            continue
        print(f"[{i}] {r['ts']} {os.path.basename(r['cwd'])} {r['seconds']}s")
        for idx, q, a in shown:
            print(f"    {short(states[idx])}\n      {q}: {fmt(a)}")


if __name__ == "__main__":
    main()
