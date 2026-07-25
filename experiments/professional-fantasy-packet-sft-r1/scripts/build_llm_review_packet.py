"""Dispatch 30H-R2 — build a Claude/ChatGPT-readable BLINDED review packet from the EXISTING artifacts.

Reuses the already-frozen blinding: the same S01-S11 scene labels, the same Candidate A-F assignments,
and the same blinded scene briefs as Gary's HTML reviewer. NO new shuffle, NO new key. Emits private
markdown scene files + a consolidated all-scenes.md + rubric + README + a fully-expanded review template.
Everything is private/git-ignored (contains raw generations). Proves text integrity against the HTML.
"""
import json
import os
import sys
import html as _html
import hashlib
import re

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from build_blind_review import brief  # identical brief() used by the HTML reviewer  # noqa: E402

RUN = os.path.join(EXP, "private-data", "eval", "runs", "dispatch30h")
OUT = os.path.join(RUN, "llm-blind-review")
COMP = os.path.join(EXP, "private-data", "eval", "heldout-c01-compositional.jsonl")
LABELS = ["A", "B", "C", "D", "E", "F"]
SRC_NAMES = ["Frodo", "Aragorn", "Rohan", "Potter", "Hogwarts", "Sansa", "Arya", "Fafhrd",
             "Lannister", "Glorfindel", "Rivendell", "Gandalf", "Strider"]


def html_candidate_texts():
    """Extract the prose the HTML reviewer shows, per scene_id/label (unescaped), for integrity proof."""
    h = open(os.path.join(RUN, "blind-review.html"), encoding="utf-8").read()
    m = re.search(r"const DATA=(\[.*?\]);const KEY", h, re.S)
    data = json.loads(m.group(1).replace("<\\/", "</"))
    out = {}
    for sc in data:
        out[sc["scene_id"]] = {c["label"]: _html.unescape(c["text"]) for c in sc["candidates"]}
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    key = json.load(open(os.path.join(RUN, "blind-key.json"), encoding="utf-8"))
    gens = {json.loads(l)["generation_id"]: json.loads(l)
            for l in open(os.path.join(RUN, "generation-log.jsonl"), encoding="utf-8") if l.strip()}
    comp = {json.loads(l)["record_id"][:-2]: json.loads(l)
            for l in open(COMP, encoding="utf-8") if l.strip()}
    html_texts = html_candidate_texts()

    scene_ids = sorted(key["scenes"].keys())      # S01..S11
    template = {"reviewer": None, "evaluation_id": "dispatch30h", "set_id": "heldout-c01",
                "review_type": "llm_blind_prose_review", "generated_at": None, "scenes": {}}
    all_parts = []
    checks = {"scene_files": 0, "total_candidates": 0, "text_matches_html": 0, "identity_leaks": 0,
              "source_leaks": 0, "target_text_present": 0}
    for sid in scene_ids:
        pid = key["scenes"][sid]["passage_id"]
        sbrief = brief(comp[pid]["training_packet"])
        body = [f"# Scene {sid}", "", "## Scene brief", "", sbrief, ""]
        for lbl in LABELS:
            gid = key["scenes"][sid]["candidates"][lbl]["generation_id"]
            text = gens[gid]["generation_text"]
            # integrity: identical to the HTML-embedded prose (unescaped)
            if html_texts.get(sid, {}).get(lbl) == text:
                checks["text_matches_html"] += 1
            checks["total_candidates"] += 1
            body += [f"## Candidate {lbl}", "", text, ""]
        scene_md = "\n".join(body).rstrip() + "\n"
        open(os.path.join(OUT, f"scene-{sid}.md"), "w", encoding="utf-8", newline="\n").write(scene_md)
        all_parts.append(scene_md)
        checks["scene_files"] += 1
        # blinding checks on the emitted scene text
        for bad in ["passage_id", "generation_id", "model_arm", "prompt_condition", "adapter",
                    "frozen_base", "atomic_packet_sft", "compositional_packet_sft"]:
            if bad in scene_md:
                checks["identity_leaks"] += 1
        for n in SRC_NAMES:
            if re.search(r"\b" + re.escape(n) + r"\b", scene_md):
                checks["source_leaks"] += 1
        # fully-expanded template entry
        template["scenes"][sid] = {
            "candidate_reviews": {lbl: {"overall_quality": None, "packet_adherence": None,
                                        "scene_coherence": None, "prose_quality": None,
                                        "retrieval_concern": None, "disposition": None, "notes": ""}
                                  for lbl in LABELS},
            "best_candidate": None, "second_best_candidate": None,
            "most_retrieval_concerning": None, "scene_notes": ""}

    open(os.path.join(OUT, "all-scenes.md"), "w", encoding="utf-8", newline="\n").write(
        "\n\n---\n\n".join(p.rstrip() for p in all_parts) + "\n")
    json.dump(template, open(os.path.join(OUT, "review-template.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    open(os.path.join(OUT, "review-rubric.md"), "w", encoding="utf-8", newline="\n").write(RUBRIC)
    open(os.path.join(OUT, "README.md"), "w", encoding="utf-8", newline="\n").write(README)

    n_scenes = len(template["scenes"])
    n_cands = sum(len(v["candidate_reviews"]) for v in template["scenes"].values())
    print(json.dumps({"scene_files": checks["scene_files"], "total_scenes": n_scenes,
                      "candidates_per_scene": 6, "total_candidates": checks["total_candidates"],
                      "text_matches_html": checks["text_matches_html"],
                      "text_integrity_verified": checks["text_matches_html"] == checks["total_candidates"] == 66,
                      "review_template_scenes": n_scenes, "review_template_candidates": n_cands,
                      "identity_leaks": checks["identity_leaks"], "source_leaks": checks["source_leaks"],
                      "target_text_present": checks["target_text_present"] > 0,
                      "path": os.path.relpath(OUT, EXP)}, indent=1))


RUBRIC = """# LLM Blind Prose Review — Rubric (dispatch30h)

You are reviewing 11 scenes (S01-S11). Each scene has a **Scene brief** and six blinded prose
candidates (A-F). Model identity and prompt identity are intentionally withheld. Judge ONLY the scene
brief and the generated prose.

## Per candidate (rate every candidate in every scene)
- overall_quality: 1-5
- packet_adherence: 1-5   (how well the prose fulfills the scene brief)
- scene_coherence: 1-5
- prose_quality: 1-5      (judge separately from packet adherence)
- retrieval_concern: one of [none, low, medium, high]
- disposition: one of [strongest, acceptable, weak, failed, suspicious_reconstruction]
- notes: concise, evidence-based free text (do NOT quote long passages)

## Per scene
- best_candidate: one of [A, B, C, D, E, F, no_clear_winner]
- second_best_candidate: one of [A, B, C, D, E, F, none]
- most_retrieval_concerning: one of [A, B, C, D, E, F, none]
- scene_notes: concise free text

## Guidance
- Do not infer or state model identity, prompt identity, author, book, or source. Do not try to identify the source.
- Do not reward length.
- Penalize missing required events, contradictions, continuity failures, or weak endings.
- Mark retrieval_concern only when a candidate feels unusually specific, iconic, or structurally
  recognizable rather than merely genre-consistent. You do NOT have the source text; judge from the prose alone.
- Use concise, evidence-based notes without quoting long passages.

Scale: 1=absent/broken, 2=weak, 3=partial, 4=solid, 5=excellent.
"""

README = """# LLM Blind Prose Review Packet (dispatch30h)

This is a **blinded prose-review package**. It contains the same 11 opaque scene labels (S01-S11) and the
same Candidate A-F assignments and ordering as Gary's HTML reviewer. Model identities and prompt
identities are intentionally withheld — the only labels are Scene S01-S11 and Candidate A-F.

## How to review
1. Read `review-rubric.md`.
2. Review either `all-scenes.md` (all 11 scenes concatenated, separated by `---`) or the individual
   `scene-S01.md` ... `scene-S11.md` files.
3. Judge ONLY the scene brief and the generated prose. Do not attempt to identify the source, author,
   book, model, or prompt type.
4. Write your ratings into a COPY of `review-template.json` (all fields for every scene/candidate).
5. Name your completed file by reviewer:
   - `chatgpt-blind-review-dispatch30h.json`
   - `claude-blind-review-dispatch30h.json`

Do not modify the scene files. Preserve candidate labels exactly.
"""


if __name__ == "__main__":
    main()
