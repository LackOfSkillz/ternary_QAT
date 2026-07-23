"""Dispatch 30A-R1 — Phase 1 normalization. Produce frozen normalized private copies of the eleven
authorized sources. Mechanical normalization ONLY (encoding, line endings, trailing whitespace) so
the gold target text is otherwise unchanged; all downstream offsets index the normalized file.

Inputs: git-ignored `training text/`. Outputs: git-ignored `private-data/normalized-sources/` +
`private-data/normalized-manifest.json` (hashes/lengths only). No prose is printed or committed.
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(EXP, "..", ".."))
CORPUS = os.path.join(REPO, "training text")
OUT = os.path.join(EXP, "private-data", "normalized-sources")
SRC_MANIFEST = os.path.join(EXP, "manifests", "professional-source-files.json")


def normalize(raw_bytes):
    text = raw_bytes.decode("utf-8-sig", "replace")   # strip BOM
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in text.split("\n")]   # strip trailing whitespace per line
    text = "\n".join(lines)
    if not text.endswith("\n"):
        text += "\n"
    return text


def main():
    src = json.load(open(SRC_MANIFEST, encoding="utf-8"))
    os.makedirs(OUT, exist_ok=True)
    entries = []
    for f in src["files"]:
        fn = f["filename"]
        p = os.path.join(CORPUS, fn)
        raw = open(p, "rb").read()
        assert hashlib.sha256(raw).hexdigest() == f["sha256"], f"source hash drift: {fn}"
        norm = normalize(raw)
        data = norm.encode("utf-8")
        np = os.path.join(OUT, fn)
        with open(np, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(norm)
        entries.append({
            "filename": fn, "source_sha256": f["sha256"],
            "normalized_sha256": hashlib.sha256(data).hexdigest(),
            "normalized_char_len": len(norm), "normalized_byte_len": len(data),
            "word_count": len(norm.split()),
            "normalizations_applied": ["encoding_bom", "line_endings", "trailing_whitespace"],
        })
    manifest = {"dispatch": "30A-R1", "phase": 1, "normalized_dir": "private-data/normalized-sources/",
                "note": "hashes/lengths only; normalized copies are private (git-ignored). Offsets index these files.",
                "files": entries, "frozen_at": "2026-07-23"}
    json.dump(manifest, open(os.path.join(EXP, "private-data", "normalized-manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"normalized": len(entries),
                      "total_chars": sum(e["normalized_char_len"] for e in entries)}, indent=1))


if __name__ == "__main__":
    main()
