"""cases.py の評価セットを Ollaya のローカルサーバーで実行し、正解率と速度を測る。

使い方: python3 eval/run_eval.py laya [clef:flash ...]
結果は eval/results/<model>.json に保存し、要約を標準出力に出す。
"""
import json
import os
import sys
import time
import urllib.request

from cases import TASKS

URL = "http://127.0.0.1:11435/api/decide"
HERE = os.path.dirname(os.path.abspath(__file__))


def decide(model, state, task):
    body = {"model": model, "state": state}
    if "preset" in task:
        body["preset"] = task["preset"]
    else:
        body["questions"] = task["questions"]
    req = urllib.request.Request(URL, json.dumps(body).encode(), {"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as r:
        res = json.load(r)
    return res, time.time() - t0


def judge(answer, expected):
    """(予測, 正解か, 予測の確信度) を返す。noul は 0.5 を閾値にする。"""
    if answer["type"] == "noul":
        p = answer["noul"]
        pred = p >= 0.5
        return pred, pred == expected, max(p, 1 - p)
    return answer["choice"], answer["choice"] == expected, answer["confidence"]


def run(model):
    rows, summary = [], {}
    decide(model, "warm up", TASKS["output_failed"])  # 初回ロードを計測から外す
    for name, task in TASKS.items():
        ok, lat = 0, []
        for state, expected in task["cases"]:
            res, sec = decide(model, state, task)
            pred, correct, conf = judge(res["answers"][task["answer_key"]], expected)
            ok += correct
            lat.append(sec)
            rows.append({"task": name, "state": state, "expected": expected, "pred": pred,
                         "correct": correct, "conf": round(conf, 3), "sec": round(sec, 3),
                         "routed": res.get("model")})
        n = len(task["cases"])
        summary[name] = {"acc": ok / n, "n": n, "avg_sec": sum(lat) / n}
        print(f"{model:12s} {name:18s} {ok:2d}/{n:2d} = {ok / n:.2f}  avg {sum(lat) / n * 1000:6.0f} ms", flush=True)
    total = sum(s["acc"] * s["n"] for s in summary.values()) / sum(s["n"] for s in summary.values())
    print(f"{model:12s} {'TOTAL':18s} {total:.2f}")
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    with open(os.path.join(HERE, "results", model.replace(":", "_") + ".json"), "w") as f:
        json.dump({"model": model, "summary": summary, "total": total, "rows": rows}, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    for m in sys.argv[1:] or ["laya"]:
        run(m)
