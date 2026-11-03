"""One no-tools picture question through OpenRouter (generator side, never shipped).

    python3 ask_picture.py <image.png> <out_dir> [model]

Sends the image + the fixed-choice questions, saves request metadata, the raw response and the parsed answer.
The key is read from ~/.config/collinear/openrouter_key and never printed.
"""
import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

PROMPT = """The picture shows many experimental structures of one protein chain, superposed (cartoon representation; colours only distinguish the different structures). The protein's name is withheld.

Answer from the picture and your own knowledge of protein structure. Do not look anything up.

Q1. Where does this protein live in the cell?
  A cytoplasm  B nucleus  C secreted / extracellular  D membrane, single-pass  E membrane, multi-pass  F mitochondrial matrix
Q2. What class of protein is it?
  A enzyme  B G protein-coupled receptor  C transporter / pump  D ion channel  E receptor tyrosine kinase  F structural / scaffold protein  G transcription factor
Q3. How many helices cross the membrane in one chain? Give a whole number (0 if it is not a membrane protein; do not count re-entrant pore loops).
Q4. If it is a channel, what opens it?
  A voltage  B ligand binding  C mechanical force  D not a channel
Q5. Which partners does it bind? Choose all that apply.
  A small single-pass membrane auxiliary subunits  B calmodulin  C heterotrimeric G protein  D beta-arrestin  E DNA  F none of these

End your reply with exactly one line of JSON, for example:
{"Q1": "A", "Q2": "A", "Q3": 0, "Q4": "D", "Q5": ["C"], "protein_guess": "..."}"""


def main(image, out_dir, model="openai/gpt-6-astra"):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    key = (Path.home() / ".config/collinear/openrouter_key").read_text().strip()
    b64 = base64.b64encode(Path(image).read_bytes()).decode()
    body = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "text", "text": PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
        ]}],
        "reasoning": {"effort": "max"},
        "max_tokens": 128000 if "astra" in model else 64000,
        "usage": {"include": True},
    }
    (out / "prompt.txt").write_text(PROMPT)
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=1800) as r:
        resp = json.load(r)
    resp["_elapsed_s"] = round(time.time() - t0, 1)
    (out / "response.json").write_text(json.dumps(resp, indent=1))
    text = resp["choices"][0]["message"]["content"] or ""
    last = [ln for ln in text.strip().splitlines() if ln.strip().startswith("{")]
    answer = json.loads(last[-1]) if last else None
    (out / "answer.json").write_text(json.dumps(answer, indent=1))
    print("elapsed", resp["_elapsed_s"], "s; cost", resp.get("usage", {}).get("cost"),
          "; finish", resp["choices"][0].get("finish_reason"))
    print("ANSWER", json.dumps(answer))
    print("TEXT", text[-1500:])


if __name__ == "__main__":
    main(*sys.argv[1:])
