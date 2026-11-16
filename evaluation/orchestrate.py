"""Direct OpenRouter orchestration for the blind eval (gemma vs nemotron, ±skill).

Why direct API instead of subagent dispatch: the agent harness reserves ~225k
max_tokens per subagent call, which exceeds the account's OpenRouter credit for
paid models. Direct calls set max_tokens to what the JSON reply actually needs.

Usage:
  python orchestrate.py run   [--model M] [--cond skill|noskill]   # call models
  python orchestrate.py parse                                    # parse raw -> decisions_*.json

The API key is read from opencode's auth.json and NEVER printed.
"""
import argparse
import base64
import glob
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
KEY_PATH = os.path.join(os.path.expanduser("~"), ".local", "share", "opencode", "auth.json")

MODELS = {
    "gemma": "google/gemma-4-31b-it",
    "nemotron": "nvidia/nemotron-3.5-lightning",
}
URL = "https://openrouter.ai/api/v1/chat/completions"


def get_key() -> str:
    with open(KEY_PATH) as f:
        auth = json.load(f)

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, str) and v.startswith("sk-or-"):
                    yield v
                else:
                    yield from walk(v)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v)

    keys = list(walk(auth))
    if not keys:
        sys.exit("no openrouter key found in auth.json")
    return keys[0]


def call(model_id: str, prompt: str, max_tokens: int = 8000) -> dict:
    body = json.dumps({
        "model": model_id,
        "messages": [
            {"role": "system",
             "content": "You output only valid JSON. No markdown, no prose."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Authorization": f"Bearer {get_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/lowf49/evidence-first-trading",
        "X-Title": "blind-eval",
    })
    with urllib.request.urlopen(req, timeout=300) as r:
        return json.load(r)


def run(model: str | None, cond: str | None) -> int:
    payloads = sorted(glob.glob(os.path.join(HERE, "prompts", "payload_*.txt")))
    if not payloads:
        sys.exit("no payloads found - run: python blind_eval.py prompt")
    for m in ([model] if model else list(MODELS)):
        for path in payloads:
            stem = os.path.basename(path)[len("payload_"):-4]  # skill_1
            c, part = stem.rsplit("_", 1)
            if cond and c != cond:
                continue
            out = os.path.join(HERE, f"raw_{m}_{c}_{part}.json")
            if os.path.exists(out):
                print(f"skip {m}/{c} part {part} (exists)")
                continue
            payload = open(path).read()
            print(f"calling {MODELS[m]} cond={c} part {part} "
                  f"(prompt {len(payload)} chars)...", flush=True)
            try:
                resp = call(MODELS[m], payload, max_tokens=9000)
            except Exception as e:
                detail = e.read().decode()[:500] if hasattr(e, "read") else str(e)
                print(f"  FAILED: {detail}")
                continue
            choice = (resp.get("choices") or [{}])[0]
            content = choice.get("message", {}).get("content", "")
            usage = resp.get("usage", {})
            print(f"  done: {len(content)} chars, usage={usage}, "
                  f"finish={choice.get('finish_reason')}")
            json.dump({"model": MODELS[m], "cond": c, "part": part,
                       "usage": usage, "content": content},
                      open(out, "w"), indent=1)
    return 0


def parse() -> int:
    groups = {}
    for path in sorted(glob.glob(os.path.join(HERE, "raw_*.json"))):
        m = re.match(r"raw_(\w+)_(skill|noskill)_(\d+)\.json$",
                     os.path.basename(path))
        if not m:
            print(f"skip unrecognized raw file: {os.path.basename(path)}")
            continue
        groups.setdefault((m.group(1), m.group(2)), []).append(
            (int(m.group(3)), path))
    if not groups:
        sys.exit("no raw files found - run: python orchestrate.py run")
    cases = json.load(open(os.path.join(HERE, "cases.json")))
    valid = {c["id"] for c in cases}
    for (model, cond), parts in sorted(groups.items()):
        obj = {}
        for _, path in sorted(parts):
            content = json.load(open(path))["content"]
            mm = re.search(r"\{.*\}", content, re.S)
            if not mm:
                print(f"{model}/{cond}: NO JSON in {os.path.basename(path)}")
                continue
            try:
                obj.update(json.loads(mm.group(0)))
            except json.JSONDecodeError as e:
                print(f"{model}/{cond}: decode failed on "
                      f"{os.path.basename(path)}: {e}")
        preds = {}
        for k, v in obj.items():
            if k in valid and isinstance(v, str):
                v = v.strip().upper()
                preds[k] = v if v in ("LONG", "SHORT", "FLAT") else "FLAT"
        missing = valid - set(preds)
        for cid in missing:
            preds[cid] = "FLAT"  # abstain on anything not answered
        outp = os.path.join(HERE, f"decisions_{model}_{cond}.json")
        json.dump(preds, open(outp, "w"), indent=1)
        print(f"{model}_{cond}: {len(preds)} decisions from {len(parts)} part(s) "
              f"({len(missing)} defaulted FLAT) -> decisions_{model}_{cond}.json")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["run", "parse"])
    p.add_argument("--model", choices=list(MODELS), default=None)
    p.add_argument("--cond", choices=["skill", "noskill"], default=None)
    a = p.parse_args()
    sys.exit(run(a.model, a.cond) if a.cmd == "run" else parse())
