"""Dispatch 30A — calibrate the signature-stacking detector against the professional reference
corpus (Section 10 professional prose floor / anti-slop null distribution).

Reads the 11 git-ignored professional files ONLY to compute aggregate per-sentence
signature-family statistics. NO prose, sentences, or spans are stored or printed — output is
counts and percentages only. This establishes the professional null distribution: if published
prose rarely stacks >= 2 families in one sentence, the '0 auto-accepted stacked sentences per
scene' target is well-founded and the detector is not over-firing.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(EXP, "..", ".."))
sys.path.insert(0, HERE)
import verifier as V  # noqa: E402

CORPUS = os.path.join(REPO, "training text")
MANIFEST = json.load(open(os.path.join(EXP, "manifests", "professional-reference-files.json"), encoding="utf-8"))


def calibrate_file(path):
    text = open(path, encoding="utf-8", errors="ignore").read()
    dist = {0: 0, 1: 0, 2: 0, 3: 0}   # families-per-sentence buckets (3 = 3+)
    fam_counts = {}
    n = 0
    for s in V.sentences(text):
        if len(s.split()) < 3:
            continue
        fams = V.signature_families(s)
        k = min(len(fams), 3)
        dist[k] += 1
        n += 1
        for f in fams:
            fam_counts[f] = fam_counts.get(f, 0) + 1
    return n, dist, fam_counts


def main():
    if not os.path.isdir(CORPUS):
        print(json.dumps({"error": "professional corpus not found (training text/)"}))
        return
    per_file, tot = {}, {0: 0, 1: 0, 2: 0, 3: 0}
    tot_fam, tot_n = {}, 0
    for entry in MANIFEST["files"]:
        p = os.path.join(CORPUS, entry["file"])
        if not os.path.exists(p):
            continue
        n, dist, fam = calibrate_file(p)
        tot_n += n
        for k in tot:
            tot[k] += dist[k]
        for f, c in fam.items():
            tot_fam[f] = tot_fam.get(f, 0) + c
        per_file[entry["file"]] = {
            "sentences": n,
            "pct_0_families": round(100 * dist[0] / max(1, n), 2),
            "pct_1_family": round(100 * dist[1] / max(1, n), 2),
            "pct_2plus_stacked": round(100 * (dist[2] + dist[3]) / max(1, n), 2),
        }
    overall = {
        "sentences": tot_n,
        "pct_0_families": round(100 * tot[0] / max(1, tot_n), 2),
        "pct_1_family": round(100 * tot[1] / max(1, tot_n), 2),
        "pct_2_families": round(100 * tot[2] / max(1, tot_n), 2),
        "pct_3plus_families": round(100 * tot[3] / max(1, tot_n), 2),
        "pct_2plus_stacked": round(100 * (tot[2] + tot[3]) / max(1, tot_n), 2),
        "family_prevalence_pct": {f: round(100 * c / max(1, tot_n), 2)
                                  for f, c in sorted(tot_fam.items(), key=lambda x: -x[1])},
    }
    out = {"dispatch": "30A", "phase": 3, "detector": "signature_families v1",
           "corpus_files": len(per_file), "note": "counts/percentages only; no prose stored",
           "overall": overall, "per_file": per_file,
           "interpretation": (
               f"Professional prose stacks >=2 signature families in {overall['pct_2plus_stacked']}% of "
               "sentences. A low rate supports the anti-slop floor (any stacked sentence in a generated "
               "scene is worth inspection); a high rate would mean the detector over-fires and needs "
               "loosening before it gates model output.")}
    json.dump(out, open(os.path.join(EXP, "reports", "signature-stacking-calibration.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(json.dumps({"corpus_files": len(per_file), "total_sentences": tot_n,
                      "overall_pct_2plus_stacked": overall["pct_2plus_stacked"],
                      "top_families": dict(list(overall["family_prevalence_pct"].items())[:5])}, indent=1))


if __name__ == "__main__":
    main()
