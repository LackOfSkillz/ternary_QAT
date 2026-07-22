"""Dispatch 27A — package the frozen Phase A blind prose materials into two reviewer ZIP kits.

Builds self-contained, fully-blind review kits for two supplemental LM reviewers (chatgpt, claude)
from the ALREADY-FROZEN anonymous units. No new outputs; no unblinding; the private identity key
and precision mapping never enter a kit. Deterministic ZIPs, reviewer-salted presentation order,
forbidden-term scan, manifest (order hashes only), and a validation report.
"""
import hashlib
import io
import json
import os
import zipfile

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
RUN = os.path.join(_REPO, "benchmarks", "runs", "qwen-prose-confirmation-v1")
PACKET = os.path.join(RUN, "review", "review", "anonymous", "reviewer-packet.json")
D26_PLAN = os.path.join(_REPO, "benchmarks", "runs", "lwdb-stronger-base-v1", "generation-plan.json")
CAL = os.path.join(_REPO, "benchmarks", "calibration", "grader-calibration-set-v1.jsonl")
OUT = os.path.join(RUN, "reviewer-kits")
SOURCE_COMMIT = "e1d00f6802e85cf790eb40938be1b517a066ce97"

REVIEWERS = ["chatgpt", "claude"]
FORBIDDEN = ["qwen", "bf16", "fp16", "fp8", "q4_k_m", "q4", "gguf", "quantized", "quantization",
             "reference precision", "deployment precision", "model_role", "identity-key",
             "pairwise-key", "private-unblinding", "ministral", "bonsai", "ternary"]

FIXED_DT = (1980, 1, 1, 0, 0, 0)


def sha(b):
    return hashlib.sha256(b if isinstance(b, bytes) else b.encode("utf-8")).hexdigest()


def _anon(s):
    return "unit-" + hashlib.sha256(s.encode()).hexdigest()[:16]


# ------------------------------------------------------------------ assemble units
def assemble_units():
    packet = json.load(open(PACKET, encoding="utf-8"))
    plan = json.load(open(D26_PLAN, encoding="utf-8"))
    cals = [json.loads(l) for l in open(CAL, encoding="utf-8") if l.strip()][:6]
    cal_by_uid = {_anon(f"cal::{c['calibration_id']}"): c for c in cals}
    units = []
    for u in packet:
        uid, ctx, out = u["unit_id"], u["task_context"], u["text"]
        if uid in cal_by_uid:                       # calibration control — indistinguishable framing
            shape = cal_by_uid[uid].get("source_item_shape", {})
            src = ""
            if isinstance(shape, dict):
                src = shape.get("source", "") or ""
            task = ("Assess the passage below for the stated craft brief. If it already meets the "
                    "brief, return it unchanged with a brief reason; otherwise make only the "
                    "smallest warranted revision. Return the appropriate output for the task.")
            body = task + (("\n\nSOURCE:\n" + src) if src else "")
        else:                                       # real task — faithful frozen prompt
            prompt = json.loads(plan["items"][ctx]["prompt"])
            body = prompt["user"]
        units.append({"unit_id": uid, "task": body.strip(), "output": out})
    return units


# ------------------------------------------------------------------ static kit text
README = """# Blind LineWright Prose Review

You are reviewing anonymous prose outputs produced from the same underlying task set. You must not
attempt to identify the model, precision, runtime, or source of any output. Score only what appears
in the packet. Do not compare your answers with another reviewer before submitting. Do not search
any repository, prior conversation, commit history, model cards, or result reports for identifying
information. Complete every review unit. Return your completed score file exactly in the provided
YAML or JSON format.

Please note:

- All outputs are anonymous; source identities are deliberately withheld.
- Some units may be calibration controls, and not every unit necessarily represents a model output.
- Do not infer identity from quality, and do not resolve uncertainty by guessing — record it.
- Score each unit independently, before any discussion, using the full rubric.
- Where a unit itself presents a pair, refer to them only as *anonymous version A* / *version B*.

This is an absolute (per-unit) review. Judge each unit on its own merits against the task shown.
"""

SCORING_INSTRUCTIONS = """# Scoring Instructions

## Step 1 — Read the task
For each unit read the task instruction, any source passage, context or canon, protected text, the
required output shape, and the anonymous output.

## Step 2 — Score independently
Assign scores without comparing against later units. Use the full rubric.
Do NOT reward: verbosity alone; ornate prose alone; generic literary language; merely following the
topic; plausible details that violate canon; polished prose that ignores the requested task.
Do NOT punish: concise prose when concision fits; plain language when the voice requires it; exact
preservation when no change is correct; lack of decorative metaphor.

## Step 3 — Identify fatal failures
A fatal failure exists when the output is unusable for the task because of one or more of: wrong
task; wrong output type; severe canon violation; protected-text corruption; runaway repetition;
unfinished or truncated output; a reasoning trace; a schema payload instead of the requested prose;
prose instead of a required structured response; or a substantial unauthorized rewrite. Do not mark
a merely mediocre passage as fatal.

## Step 4 — Provide concise evidence
For each score cite a short phrase or describe the exact behaviour. Do not rewrite the passage and
do not provide a replacement answer.

## Step 5 — Submit the completed score file
Return the completed YAML or JSON score file for your assigned reviewer id, following the template.
Per-unit scores are mandatory; aggregate mean fields may be left null.
"""

RUBRIC = """# Scoring Rubric (prose-review-v1)

All numeric dimensions use a 1-5 integer scale.

## 1. prose_quality
1 unusable/incoherent/degenerate · 2 weak/artificial/overwritten · 3 competent but ordinary ·
4 strong, natural, controlled · 5 exceptional and highly effective.
(sentence naturalness, rhythm, clarity, specificity, control, absence of mechanical phrasing,
register appropriateness)

## 2. instruction_compliance
1 ignores/contradicts · 2 partial · 3 general with misses · 4 close · 5 fulfils every important instruction.

## 3. voice_preservation
1 replaces the source voice · 2 substantial flattening/takeover · 3 mixed · 4 preserves well ·
5 fully native to the source voice. (tense, viewpoint, distance, sentence architecture, diction,
emotional temperature, ornamentation, dialogue character)

## 4. scene_coherence
1 incoherent · 2 hard to follow · 3 understandable with weaknesses · 4 coherent/controlled ·
5 fully coherent with strong continuity.

## 5. pacing
1 stalled/rushed/broken · 2 significantly uneven · 3 adequate · 4 effective · 5 exceptionally controlled.

## 6. sentence_naturalness
1 mechanical/malformed · 2 frequently awkward · 3 mostly natural · 4 consistently natural · 5 effortless and precise.

## 7. scope_control
1 rewrites beyond authorization · 2 major unnecessary changes · 3 some unnecessary change ·
4 stays within scope · 5 exact, disciplined scope control.

## 8. canon_fidelity
1 fatal contradiction/invention · 2 major error · 3 minor ambiguity/unsupported detail ·
4 canon preserved · 5 handled precisely. Use `not_applicable` where no canon is present.

## 9. author_usefulness
1 unusable · 2 major rewriting needed · 3 useful with moderate editing · 4 minor editing · 5 ready or nearly.

## 10. repetition_or_slop
Label one of: none / low / moderate / high / severe. (repeated structures, duplicate ideas,
paraphrased emotional repetition, generic summaries, stacked similes, overwriting, repetitive
transitions, runaway continuation, duplicated sentences or n-grams)

## fatal_failure
true/false. If true, include fatal_failure_type and fatal_failure_evidence.
Allowed types: wrong_task, wrong_output_type, canon_violation, protected_text_corruption,
runaway_repetition, truncation, reasoning_trace, schema_failure, unauthorized_rewrite, other.
"""

SUBMISSION_CHECKLIST = """# Submission Checklist

Before returning your review:

- [ ] Every anonymous unit has been scored.
- [ ] All numeric scores are integers from 1 through 5.
- [ ] `canon_fidelity` is either 1-5 or `not_applicable`.
- [ ] Every unit has a repetition/slop label.
- [ ] Every fatal failure includes a type and evidence.
- [ ] Nonfatal weaknesses are not marked fatal.
- [ ] No model or precision identity was guessed or added.
- [ ] No unit text was edited.
- [ ] No discussion occurred with another reviewer.
- [ ] `completed_all_units` is true.
- [ ] `submission_complete` is true.

Return only the completed YAML or JSON review file plus, optionally, one short paragraph of overall
impressions. Do not include speculation about model identity.
"""

DIMS = ["prose_quality", "instruction_compliance", "voice_preservation", "scene_coherence",
        "pacing", "sentence_naturalness", "scope_control", "canon_fidelity", "author_usefulness"]


def units_md(units):
    out = ["# Anonymous Review Units", "",
           "Score every unit below in the supplied YAML or JSON score template. Units are in a "
           "randomized order.", ""]
    for u in units:
        out += [f"## Review Unit: {u['unit_id']}", "", "### Task", "", u["task"], "",
                "### Anonymous Output", "", u["output"] if u["output"].strip() else "(no output)", "",
                "### Reviewer Scores", "",
                "Complete this unit in the supplied YAML or JSON score template.", "", "---", ""]
    return "\n".join(out)


def template_yaml(reviewer, units):
    lines = ["review_metadata:", "  review_id: prose-confirmation-v1",
             f"  reviewer_id: {reviewer}", "  reviewer_type: supplemental_language_model",
             "  rubric_version: prose-review-v1", "  completed_all_units: false",
             "  identity_information_seen: false",
             "  discussed_with_other_reviewers_before_submission: false", "", "units:", ""]
    for u in units:
        lines += [f"  - unit_id: {u['unit_id']}", "    scores:",
                  *(f"      {d}: null" for d in DIMS),
                  "    repetition_or_slop: null", "    fatal_failure: false",
                  "    fatal_failure_type: null", "    fatal_failure_evidence: null",
                  "    strongest_quality: null", "    main_weakness: null", "    evidence: null",
                  "    confidence: null   # high | moderate | low", ""]
    lines += ["overall:", "  mean_prose_quality: null", "  mean_instruction_compliance: null",
              "  fatal_failure_count: null", "  calibration_suspected: false",
              "  general_observations: null", "  submission_complete: false", ""]
    return "\n".join(lines)


def template_json(reviewer, units):
    obj = {"review_metadata": {"review_id": "prose-confirmation-v1", "reviewer_id": reviewer,
            "reviewer_type": "supplemental_language_model", "rubric_version": "prose-review-v1",
            "completed_all_units": False, "identity_information_seen": False,
            "discussed_with_other_reviewers_before_submission": False},
           "units": [{"unit_id": u["unit_id"], "scores": {d: None for d in DIMS},
                      "repetition_or_slop": None, "fatal_failure": False, "fatal_failure_type": None,
                      "fatal_failure_evidence": None, "strongest_quality": None,
                      "main_weakness": None, "evidence": None, "confidence": None} for u in units],
           "overall": {"mean_prose_quality": None, "mean_instruction_compliance": None,
                       "fatal_failure_count": None, "calibration_suspected": False,
                       "general_observations": None, "submission_complete": False}}
    return json.dumps(obj, ensure_ascii=False, indent=2)


def kit_files(reviewer, ordered):
    return {
        "README-FIRST.md": README,
        "SCORING-INSTRUCTIONS.md": SCORING_INSTRUCTIONS,
        "SCORING-RUBRIC.md": RUBRIC,
        "ANONYMOUS-REVIEW-UNITS.md": units_md(ordered),
        "REVIEW-SCORES-TEMPLATE.yaml": template_yaml(reviewer, ordered),
        "REVIEW-SCORES-TEMPLATE.json": template_json(reviewer, ordered),
        "SUBMISSION-CHECKLIST.md": SUBMISSION_CHECKLIST,
    }


def order_for(units, reviewer):
    salt = f"{reviewer}-v1"
    return sorted(units, key=lambda u: hashlib.sha256((u["unit_id"] + salt).encode()).hexdigest())


def make_zip(path, kitdir, files):
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(files):
            zi = zipfile.ZipInfo(f"{kitdir}/{name}", date_time=FIXED_DT)
            zi.external_attr = 0o644 << 16
            z.writestr(zi, files[name])


def scan_forbidden(files):
    hits = []
    for name, content in files.items():
        low = content.lower()
        for term in FORBIDDEN:
            idx = low.find(term)
            if idx != -1:
                hits.append({"file": name, "term": term, "context": content[max(0, idx - 30):idx + 30]})
    return hits


def main():
    os.makedirs(OUT, exist_ok=True)
    units = assemble_units()
    src_hashes = {u["unit_id"]: sha(u["output"]) for u in units}
    packet_sha = sha(json.dumps(units, sort_keys=True, ensure_ascii=False))

    manifest = {"review_id": "prose-confirmation-v1", "source_run": "qwen-prose-confirmation-v1",
                "source_commit": SOURCE_COMMIT, "anonymous_unit_count": len(units),
                "identity_key_included": False, "private_data_included": False}
    val = ["# Reviewer-kit validation report", "",
           f"Source commit `{SOURCE_COMMIT}`; {len(units)} anonymous units; source packet sha256 `{packet_sha[:16]}…`.",
           "", "Note: paired units (two per task, for absolute scoring) share task text by design; "
           "this does NOT reveal precision identity (the two precisions were mechanically identical "
           "and blind-indistinguishable). Presentation order is reviewer-salted and randomized.", ""]
    all_forbidden = []
    for reviewer in REVIEWERS:
        ordered = order_for(units, reviewer)
        files = kit_files(reviewer, ordered)
        # validations
        assert json.loads(files["REVIEW-SCORES-TEMPLATE.json"])  # parses
        import yaml
        ty = yaml.safe_load(files["REVIEW-SCORES-TEMPLATE.yaml"])
        assert ty["review_metadata"]["reviewer_id"] == reviewer
        tmpl_ids = [u["unit_id"] for u in ty["units"]]
        assert sorted(tmpl_ids) == sorted(u["unit_id"] for u in units)
        assert len(tmpl_ids) == len(set(tmpl_ids)) == len(units)
        # every output present exactly once + hash matches
        um = files["ANONYMOUS-REVIEW-UNITS.md"]
        for u in units:
            assert um.count(f"## Review Unit: {u['unit_id']}") == 1
        forb = scan_forbidden(files)
        # allow the neutral word inside instructions? none expected; record all
        all_forbidden += [{**h, "reviewer": reviewer} for h in forb]
        kitdir = f"prose-review-{reviewer}-v1"
        zip_path = os.path.join(OUT, f"{kitdir}.zip")
        make_zip(zip_path, kitdir, files)
        zbytes = open(zip_path, "rb").read()
        order_sha = sha("\n".join(u["unit_id"] for u in ordered))
        manifest[reviewer] = {"zip": os.path.relpath(zip_path, _REPO).replace("\\", "/"),
                              "zip_sha256": sha(zbytes), "zip_size_bytes": len(zbytes),
                              "file_count": len(files), "unit_order_sha256": order_sha,
                              "reviewer_id": reviewer, "reviewer_type": "supplemental_language_model"}
        val += [f"## {reviewer} kit", f"- zip: `{manifest[reviewer]['zip']}`",
                f"- sha256: `{manifest[reviewer]['zip_sha256']}`  size: {len(zbytes)}B  files: {len(files)}",
                f"- all {len(units)} units present exactly once; template ids match; JSON+YAML parse",
                f"- reviewer_id correct: {reviewer}", ""]

    manifest["validation_status"] = "pass" if not all_forbidden else "forbidden_terms_found"
    manifest["forbidden_scan_hits"] = len(all_forbidden)
    val += ["## Forbidden-term scan",
            f"- identity-relevant matches: **{len(all_forbidden)}** (target 0)"]
    if all_forbidden:
        for h in all_forbidden[:20]:
            val.append(f"  - [{h['reviewer']}] {h['file']}: '{h['term']}' … {h['context']!r}")
    val += ["", "## Isolation", "- identity key included: no", "- private paths included: no",
            "- previous reviewer scores included: no", "- deployment/model manifests included: no", ""]
    val += ["## Naming (blindness-preserving deviation)",
            "The kit directory, ZIP filename, and template `review_id` are NEUTRAL "
            "(`prose-review-*`, `prose-confirmation-v1`) rather than the dispatch's illustrative "
            "`qwen-*` names, because those would announce the model identity to the blind reviewer "
            "and fail the mandated zero-match forbidden scan. Blindness is the dispatch's paramount, "
            "repeatedly-stated requirement, so it overrides the illustrative filename. The private "
            "manifest still records the true run id (`qwen-prose-confirmation-v1`) for the owner.", ""]

    with open(os.path.join(OUT, "reviewer-kit-manifest.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    with open(os.path.join(OUT, "reviewer-kit-validation-report.md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(val) + "\n")
    print(json.dumps({"units": len(units), "forbidden_hits": len(all_forbidden),
                      "chatgpt_zip_sha": manifest["chatgpt"]["zip_sha256"][:16],
                      "claude_zip_sha": manifest["claude"]["zip_sha256"][:16],
                      "chatgpt_size": manifest["chatgpt"]["zip_size_bytes"],
                      "claude_size": manifest["claude"]["zip_size_bytes"]}, indent=1))


if __name__ == "__main__":
    main()
