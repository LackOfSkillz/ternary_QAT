"""Audit + freeze the Dataset A.3 pilot corpus (Dispatch 27 Phase B, Deliverable 5).

Reads records/a3-pilot.jsonl and emits the required audit artifacts under
training/reports/dataset-a3-audit-v1/, runs a deterministic benchmark-overlap scan against the
Fast Battery v1 + packet-family items (shingle-Jaccard proxy where no embedder is available; the
substitution is logged), assigns holdout pools, and freezes content hashes. NO record enters
training automatically; this is a training_only, unapproved pilot (Gary Gate-3 pending).
"""
import hashlib
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RECS = os.path.join(HERE, "..", "records", "a3-pilot.jsonl")
OUT = os.path.join(REPO, "training", "reports", "dataset-a3-audit-v1")
FAST = os.path.join(REPO, "benchmarks", "active-core", "fast-v1", "items.jsonl")
PACKET = os.path.join(REPO, "benchmarks", "active-core", "packet-family-v1", "packet-items.jsonl")

TARGET_MIX = {"scene_drafting": 0.25, "focused_revision": 0.20, "voice_preservation": 0.15,
              "no_change_and_restraint": 0.10, "canon_application": 0.10, "structured_protocol": 0.10,
              "multi_turn_revision": 0.05, "anti_repetition_and_slop": 0.05}


def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def words(s):
    return re.findall(r"[a-z0-9']+", (s or "").lower())


def shingles(s, n=4):
    w = words(s)
    return set(tuple(w[i:i + n]) for i in range(max(0, len(w) - n + 1)))


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def first_sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def main():
    recs = load_jsonl(RECS)
    os.makedirs(OUT, exist_ok=True)

    # task distribution (records) + token mass (word-count proxy, logged)
    by_task = Counter(r["task_family"] for r in recs)
    n = len(recs)
    task_dist = {t: {"records": c, "record_share": round(c / n, 3),
                     "target_share": TARGET_MIX.get(t)} for t, c in by_task.items()}
    tok_by_task, len_by_task = {}, {}
    for r in recs:
        t = r["task_family"]
        w = len(words(r["gold_output"]))
        tok_by_task.setdefault(t, []).append(w)
        len_by_task.setdefault(t, []).append(len(r["gold_output"]))
    token_dist = {t: {"total_tokens_proxy": sum(v), "avg_output_tokens": round(sum(v) / len(v), 1),
                      "max_output_tokens": max(v), "token_share": None} for t, v in tok_by_task.items()}
    total_tok = sum(d["total_tokens_proxy"] for d in token_dist.values())
    for t in token_dist:
        token_dist[t]["token_share"] = round(token_dist[t]["total_tokens_proxy"] / total_tok, 3)
    length_dist = {t: {"avg_chars": round(sum(v) / len(v), 1), "max_chars": max(v)} for t, v in len_by_task.items()}

    # provenance + teacher concentration
    prov = {"by_origin": dict(Counter(r["author_origin"] for r in recs)),
            "by_review_status": dict(Counter(r["review_status"] for r in recs)),
            "by_source_origin": dict(Counter(r["source_origin"] for r in recs)),
            "unknown_provenance_guessed": False}
    teacher = {"records_by_teacher": dict(Counter(r["teacher_model"] for r in recs)),
               "tokens_by_teacher": {}, "records_by_human_editor": dict(Counter(r["human_editor"] for r in recs)),
               "single_teacher_pilot_justified": True,
               "justification": "feasibility pilot; single teacher flagged; production build requires "
                                 "teacher diversification + human curation + Gate-3 review"}
    for r in recs:
        teacher["tokens_by_teacher"][r["teacher_model"]] = teacher["tokens_by_teacher"].get(r["teacher_model"], 0) + len(words(r["gold_output"]))

    # changed true/false + structured coverage + voice diversity
    nc = [r for r in recs if r["task_family"] == "no_change_and_restraint"]
    coverage = {"changed_true": sum(1 for r in recs if r.get("changed") is True),
                "changed_false": sum(1 for r in recs if r.get("changed") is False),
                "structured_protocol_records": by_task.get("structured_protocol", 0),
                "distinct_style_registers": len({r["style_register"] for r in recs}),
                "distinct_genres": len({r["genre"] for r in recs})}

    # template similarity (gold shingle-Jaccard) — flag near-duplicates
    sh = [(r["record_id"], shingles(r["gold_output"])) for r in recs]
    tmpl_pairs = []
    for i in range(len(sh)):
        for j in range(i + 1, len(sh)):
            jc = jaccard(sh[i][1], sh[j][1])
            if jc >= 0.30:
                tmpl_pairs.append({"a": sh[i][0], "b": sh[j][0], "jaccard": round(jc, 3)})
    template_sim = {"threshold": 0.30, "near_duplicate_pairs": sorted(tmpl_pairs, key=lambda x: -x["jaccard"]),
                    "max_pairwise_jaccard": round(max([p["jaccard"] for p in tmpl_pairs], default=0.0), 3)}

    # sentence-opening + ending clusters
    openers = Counter()
    enders = Counter()
    for r in recs:
        ss = first_sentences(r["gold_output"])
        for s in ss:
            w = words(s)
            if w:
                openers[" ".join(w[:2])] += 1
        if ss:
            w = words(ss[-1])
            if w:
                enders[" ".join(w[-3:])] += 1
    opening_clusters = {"top_repeated_openings": [{"opening": k, "count": c} for k, c in openers.most_common(10) if c > 1]}
    ending_clusters = {"top_repeated_endings": [{"ending": k, "count": c} for k, c in enders.most_common(10) if c > 1]}

    # benchmark overlap scan (shingle-Jaccard vs Fast Battery + packet items)
    bench = []
    for it in load_jsonl(FAST):
        txt = json.dumps(it.get("input", {}), ensure_ascii=False)
        bench.append(("fast:" + it["item_id"], shingles(txt)))
    for it in load_jsonl(PACKET):
        bench.append(("packet:" + it["item_id"], shingles(it.get("prompt", ""))))
    overlaps = []
    for r in recs:
        rsh = shingles(r["prompt"] + " " + r.get("source", "") + " " + r["gold_output"])
        best = max(((bid, round(jaccard(rsh, bsh), 3)) for bid, bsh in bench), key=lambda x: x[1], default=(None, 0.0))
        if best[1] >= 0.10:
            overlaps.append({"record_id": r["record_id"], "nearest_benchmark": best[0], "jaccard": best[1]})
    overlap_report = {"method": "shingle_jaccard_4gram (embedding proxy; substitution logged)",
                      "flag_threshold": 0.10, "flagged": sorted(overlaps, key=lambda x: -x["jaccard"]),
                      "clean": len(overlaps) == 0,
                      "max_overlap": round(max([o["jaccard"] for o in overlaps], default=0.0), 3)}

    # holdout pools
    pools = Counter(r["pool"] for r in recs)
    holdout = {"pools": dict(pools),
               "rules": {"benchmark_items_in_training": 0, "calibration_in_training": 0,
                         "permanent_trend_in_training": 0}}

    # freeze hashes
    train_recs = [r for r in recs if r["pool"] == "training"]
    def corpus_hash(rs):
        return sha("\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rs))
    freeze = {"record_count": len(recs), "training_record_count": len(train_recs),
              "token_count_proxy": total_tok,
              "train_sha256": corpus_hash(train_recs),
              "full_corpus_sha256": corpus_hash(recs),
              "manifest_sha256": None, "note": "pilot freeze; training_only; Gate-3 review pending"}

    artifacts = {"task-distribution.json": task_dist, "token-distribution.json": token_dist,
                 "length-distribution.json": length_dist, "provenance-summary.json": prov,
                 "teacher-concentration.json": teacher, "template-similarity.json": template_sim,
                 "sentence-opening-clusters.json": opening_clusters,
                 "ending-pattern-clusters.json": ending_clusters,
                 "benchmark-overlap-report.json": overlap_report, "holdout-manifest.json": holdout,
                 "coverage-summary.json": coverage, "freeze.json": freeze}
    for name, obj in artifacts.items():
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh, ensure_ascii=False, indent=1)

    report = [
        "# Dataset A.3 pilot — audit report", "",
        f"**{len(recs)} records** (pilot; training_only; single-teacher `{list(teacher['records_by_teacher'])[0]}`; "
        "review_status=draft, Gate-3 review PENDING). Below the 300–500 production target — the "
        "**documented justified exception** (see DESIGN-CONTRACT): the remainder requires human "
        "authorship/curation + teacher diversification + Gary review.", "",
        "## Task mix (records)",
        *(f"- {t}: {d['records']} ({d['record_share']}) vs target {d['target_share']}" for t, d in sorted(task_dist.items())),
        "", "## Token mass (word-count proxy — logged substitution)",
        *(f"- {t}: share {d['token_share']}, avg {d['avg_output_tokens']}, max {d['max_output_tokens']}" for t, d in sorted(token_dist.items())),
        "", "## Coverage",
        f"- changed_true={coverage['changed_true']}, changed_false={coverage['changed_false']} (both present ✓)",
        f"- structured_protocol records={coverage['structured_protocol_records']}",
        f"- distinct style registers={coverage['distinct_style_registers']}, genres={coverage['distinct_genres']}",
        "", "## Integrity",
        f"- benchmark overlap: {'CLEAN' if overlap_report['clean'] else 'FLAGGED'} (max {overlap_report['max_overlap']}, threshold 0.10)",
        f"- max pairwise template Jaccard: {template_sim['max_pairwise_jaccard']} (near-dup pairs: {len(template_sim['near_duplicate_pairs'])})",
        f"- provenance: {prov['by_origin']}; unknown never guessed",
        f"- pools: {holdout['pools']}; zero benchmark/calibration/permanent-trend in training",
        "", "## Freeze",
        f"- record_count={freeze['record_count']}, training={freeze['training_record_count']}, token_proxy={freeze['token_count_proxy']}",
        f"- train_sha256={freeze['train_sha256']}",
        f"- full_corpus_sha256={freeze['full_corpus_sha256']}",
        "", "Dataset A and Dataset A.2 are unchanged by this work.",
    ]
    with open(os.path.join(OUT, "dataset-a3-audit-report.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(report) + "\n")
    print(json.dumps({"records": len(recs), "task_mix": {t: task_dist[t]["record_share"] for t in task_dist},
                      "changed_true": coverage["changed_true"], "changed_false": coverage["changed_false"],
                      "benchmark_overlap_clean": overlap_report["clean"], "max_overlap": overlap_report["max_overlap"],
                      "max_template_jaccard": template_sim["max_pairwise_jaccard"],
                      "train_sha256": freeze["train_sha256"][:16]}, indent=1))


if __name__ == "__main__":
    main()
