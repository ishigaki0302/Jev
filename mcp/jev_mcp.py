#!/usr/bin/env python3
"""Jev: ローカルの判定モデル（Ollaya の clef:flash）を Claude Code のツールにする MCP サーバー。

標準ライブラリだけで書いた stdio の MCP サーバー。Ollaya の HTTP API（/api/decide）を呼ぶ。
- モデルは clef:flash に固定する（ollaya mcp はモデル省略時に laya を使うため）
- keep_alive を付けて、モデルをメモリに残す（初回ロードに約 17 秒かかる）
- 複数の state を 1 回の呼び出しでまとめて判定できる
- Ollaya のサーバーが止まっていれば `ollaya serve` を起動する

環境変数:
  JEV_MODEL       使うモデル（既定: clef:flash）
  JEV_KEEP_ALIVE  モデルを残す時間（既定: 30m）
  JEV_OLLAYA      ollaya の実行ファイル（既定: ~/.local/bin/ollaya）
  OLLAYA_HOST     Ollaya のアドレス（既定: 127.0.0.1:11435）
"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

MODEL = os.environ.get("JEV_MODEL", "clef:flash")
KEEP_ALIVE = os.environ.get("JEV_KEEP_ALIVE", "30m")
OLLAYA = os.environ.get("JEV_OLLAYA", os.path.expanduser("~/.local/bin/ollaya"))
BASE = "http://" + os.environ.get("OLLAYA_HOST", "127.0.0.1:11435")
PROTOCOL = "2025-06-18"

INSTRUCTIONS = f"""Jev runs a local decision model ({MODEL}) on this machine. It never generates text: it
answers typed questions about a text or JSON state with calibrated probabilities, at no token cost.
Delegate to `decide` whenever the answer is one of a known set of outcomes: classify (choice),
rate (score) or check a yes/no statement (noul). Good fits: is this command destructive, did this
build/test output fail, is this snippet relevant to the query, what commit type is this change,
how severe is this review comment, label/triage many items. Pass many items at once via `states`.
Keep open-ended work (writing, summarizing, explaining, coding) for yourself.
Each item takes about 3-6 s (the first call after idle loads the model, about 20 s).
Act on confident answers; look yourself when confidence is low. Do not rely on it alone as a
security gate (prompt-injection detection missed 1 of 10 in evaluation)."""

DECIDE_SCHEMA = {
    "type": "object",
    "properties": {
        "state": {
            "description": "One item to decide about: a string, or a JSON object/array. Give this or `states`.",
        },
        "states": {
            "type": "array",
            "description": "Several items to decide about with the same questions, in one call. Give this or `state`.",
        },
        "questions": {
            "type": "object",
            "description": (
                "Questions keyed by an id you choose. Each: {\"type\": \"choice\"|\"score\"|\"noul\", "
                "\"instructions\": the question (may refer to fields of the state), \"criteria\": "
                "for choice an object option -> description, for score a list of levels from lowest "
                "to highest, for noul optional}. Describe options concretely: answers depend on it. "
                "Omit when giving `preset`."
            ),
        },
        "preset": {
            "type": "string",
            "description": (
                "A built-in question set instead of `questions`: triage, email, guard, moderation, "
                "router, agent (reviews a command an agent is about to run; state {request, command})."
            ),
        },
    },
}

TOOLS = [
    {
        "name": "decide",
        "description": (
            f"Ask typed questions (choice / score / noul) about one or more text or JSON states and get "
            f"calibrated answers from the local model {MODEL}. Costs no tokens beyond the call. "
            "Returns per item and question: choice -> chosen option, confidence and probabilities; "
            "score -> expected level and probabilities; noul -> probability the statement is true."
        ),
        "inputSchema": DECIDE_SCHEMA,
    },
    {
        "name": "status",
        "description": "Show whether the Ollaya server is running and which models are loaded.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]


def http(path, body=None, timeout=900):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data, {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read().decode()
    try:
        return json.loads(raw)
    except ValueError:
        return raw


def ensure_server():
    try:
        http("/", timeout=3)
        return
    except (urllib.error.URLError, OSError):
        pass
    subprocess.Popen([OLLAYA, "serve"], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)
    for _ in range(60):
        time.sleep(0.5)
        try:
            http("/", timeout=3)
            return
        except (urllib.error.URLError, OSError):
            pass
    raise RuntimeError(f"Ollaya server did not start ({OLLAYA} serve)")


def compact(answers):
    """Claude に返す量を減らすため、必要なフィールドだけ残す。"""
    out = {}
    for qid, a in answers.items():
        if a["type"] == "noul":
            out[qid] = {"type": "noul", "p_true": a["noul"]}
        elif a["type"] == "choice":
            out[qid] = {"type": "choice", "choice": a["choice"], "confidence": a["confidence"],
                        "probabilities": a["probabilities"]}
        else:
            out[qid] = {"type": "score", "score": a["score"], "confidence": a["confidence"],
                        "probabilities": a["probabilities"], "legend": a.get("legend")}
    return out


def decide(args):
    if ("state" in args) == ("states" in args):
        raise ValueError("give exactly one of `state` or `states`")
    if ("questions" in args) == ("preset" in args):
        raise ValueError("give exactly one of `questions` or `preset`")
    ensure_server()
    items = [args["state"]] if "state" in args else args["states"]
    results, t0 = [], time.time()
    for state in items:
        body = {"model": MODEL, "keep_alive": KEEP_ALIVE, "state": state}
        if "preset" in args:
            body["preset"] = args["preset"]
        else:
            body["questions"] = args["questions"]
        res = http("/api/decide", body)
        results.append(compact(res["answers"]))
    out = {"model": MODEL, "seconds": round(time.time() - t0, 2)}
    if "state" in args:
        out["answers"] = results[0]
    else:
        out["results"] = [{"index": i, "answers": r} for i, r in enumerate(results)]
    return out


def status(_args):
    try:
        http("/", timeout=3)
    except (urllib.error.URLError, OSError):
        return {"server": "stopped", "model": MODEL}
    ps = subprocess.run([OLLAYA, "ps"], capture_output=True, text=True, timeout=30).stdout
    return {"server": "running", "model": MODEL, "keep_alive": KEEP_ALIVE, "ps": ps.strip()}


HANDLERS = {"decide": decide, "status": status}


def reply(msg_id, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": msg_id}
    if error is None:
        msg["result"] = result
    else:
        msg["error"] = error
    sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def handle(msg):
    method, msg_id = msg.get("method"), msg.get("id")
    if msg_id is None:
        return  # notification
    if method == "initialize":
        reply(msg_id, {
            "protocolVersion": msg.get("params", {}).get("protocolVersion", PROTOCOL),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "jev", "version": "0.1.0"},
            "instructions": INSTRUCTIONS,
        })
    elif method == "ping":
        reply(msg_id, {})
    elif method == "tools/list":
        reply(msg_id, {"tools": TOOLS})
    elif method == "tools/call":
        params = msg.get("params", {})
        fn = HANDLERS.get(params.get("name"))
        if fn is None:
            reply(msg_id, error={"code": -32602, "message": f"unknown tool {params.get('name')}"})
            return
        try:
            result = fn(params.get("arguments") or {})
            text = json.dumps(result, ensure_ascii=False)
            reply(msg_id, {"content": [{"type": "text", "text": text}], "structuredContent": result,
                           "isError": False})
        except Exception as e:  # ツールのエラーとして Claude に返す
            reply(msg_id, {"content": [{"type": "text", "text": f"{type(e).__name__}: {e}"}],
                           "isError": True})
    else:
        reply(msg_id, error={"code": -32601, "message": f"method not found: {method}"})


def main():
    for line in sys.stdin:
        line = line.strip()
        if line:
            handle(json.loads(line))


if __name__ == "__main__":
    main()
