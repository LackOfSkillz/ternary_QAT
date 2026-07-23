"""Dispatch 30A-R1 — Phase 1 fingerprinting. Produce manifests/professional-source-files.json from
the local git-ignored corpus. Emits STATISTICS ONLY (sha256, byte/word/sentence counts, roles) —
no prose, sentences, or spans are ever stored or printed. Friendly author/work labels are kept as
per-entry metadata (the physical filename is never renamed in the manifest).
"""
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(EXP, "..", ".."))
CORPUS = os.path.join(REPO, "training text")

# exact eleven authorized files (actual local names). The dispatch lists HP(1).txt/got(1).txt;
# the real files are HP.txt/got.txt — bound here by name+hash with the mapping recorded.
FILES = [
    ("abercrombe.txt", {"work": "The Blade Itself (First Law)", "author": "Joe Abercrombie"}),
    ("sanderson.txt", {"work": "Brandon Sanderson (short sci-fi work)", "author": "Brandon Sanderson"}),
    ("gord.txt", {"work": "Gord the Rogue (Greyhawk)", "author": "Gary Gygax"}),
    ("mouser.txt", {"work": "Fafhrd and the Gray Mouser", "author": "Fritz Leiber"}),
    ("wot.txt", {"work": "The Wheel of Time", "author": "Robert Jordan"}),
    ("pawn.txt", {"work": "Pawn of Prophecy (Belgariad)", "author": "David Eddings"}),
    ("streams.txt", {"work": "Streams of Silver (Icewind Dale)", "author": "R.A. Salvatore"}),
    ("lies.txt", {"work": "The Lies of Locke Lamora", "author": "Scott Lynch"}),
    ("lor.txt", {"work": "The Lord of the Rings", "author": "J.R.R. Tolkien"}),
    ("HP.txt", {"work": "Harry Potter and the Sorcerer's Stone", "author": "J.K. Rowling",
                "dispatch_alias": "HP(1).txt"}),
    ("got.txt", {"work": "A Game of Thrones", "author": "George R.R. Martin",
                 "dispatch_alias": "got(1).txt"}),
]
_SENT = re.compile(r"[.!?][\"'”’)\]]*\s")


def main():
    entries, missing = [], []
    for i, (fn, meta) in enumerate(FILES, 1):
        p = os.path.join(CORPUS, fn)
        if not os.path.exists(p):
            missing.append(fn)
            continue
        data = open(p, "rb").read()
        text = data.decode("utf-8", "ignore")
        entries.append({
            "source_id": f"src-{i:02d}",
            "filename": fn,
            "absolute_private_path": p.replace("\\", "/"),
            "file_size_bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "word_count": len(text.split()),
            "sentence_count": len(_SENT.findall(text)),
            "encoding": "utf-8",
            "normalization_status": "raw (normalized private copy produced in Phase 1 build step)",
            "source_role": ["gold_training_target_source", "professional_reference_band_source",
                            "memorization_comparison_source"],
            "metadata": meta,
        })
    manifest = {
        "dispatch": "30A-R1",
        "note": "STATISTICS ONLY — no prose stored. The eleven files are gold-target sources AND the "
                "memorization-comparison corpus. Kept locally under 'training text/' (git-ignored).",
        "authorized_file_count": 11,
        "present_file_count": len(entries),
        "missing": missing,
        "filename_mapping": {"HP.txt": "dispatch 'HP(1).txt'", "got.txt": "dispatch 'got(1).txt'"},
        "privacy": {"distribution_scope": "private_local_research", "source_text_commit": "prohibited",
                    "dataset_publication": "prohibited", "adapter_publication": "prohibited_without_separate_review",
                    "model_distribution": "prohibited_without_separate_review"},
        "files": entries,
    }
    out = os.path.join(EXP, "manifests", "professional-source-files.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    json.dump(manifest, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({"present": len(entries), "missing": missing,
                      "total_words": sum(e["word_count"] for e in entries),
                      "total_sentences": sum(e["sentence_count"] for e in entries)}, indent=1))


if __name__ == "__main__":
    main()
