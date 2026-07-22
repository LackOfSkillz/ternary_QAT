"""Dispatch-24 controlled-pair diagnostic findings (Dispatch 25, D5).

Reads the live item-level results and emits findings that separate observation / causal
hypothesis / intervention (diagnostic-finding-v1 schema). Observations cite real per-item
values; causes and interventions carry their OWN (lower) confidence and a disambiguating
test / validation plan. Analysis refuses to run unless the threshold lock is valid.
"""
import json
import os
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

from linewright.evaluation.thresholds.freeze import require_locked_before_analysis

RUN = os.path.join(_REPO, "benchmarks", "runs", "lwdb-fast-v1-20260722")


def load_rows():
    rows = json.load(open(os.path.join(RUN, "item-level-results.json"), encoding="utf-8"))
    d = {}
    for r in rows:
        d.setdefault(r["item_id"], {})[r["model_role"]] = r
    return d


def cell(d, iid, role):
    r = d.get(iid, {}).get(role, {})
    return {"pass": r.get("mechanical_pass"), "slop": r.get("slop_severity"),
            "cap": r.get("hit_token_cap")}


def main():
    lock = require_locked_before_analysis()   # gate: thresholds must be frozen first
    d = load_rows()

    def obs(claim, items, metric, val, comp, conf="mechanical"):
        return {"claim": claim, "evidence": "Dispatch-24 live run item-level results",
                "item_ids": items, "metric": metric, "observed_value": val,
                "comparator_value": comp, "observation_confidence": conf}

    findings = []

    # 1. surface pair — rules OUT the context compiler for the candidate
    findings.append({
        "finding_id": "f-surface", "capability": "F_context_robustness / compiler attribution",
        "observation": obs(
            "The candidate fails BOTH surface arms (bare and compiled) with severe slop + token cap; "
            "the base passes BOTH.", ["lwdb-f-surface-bare", "lwdb-f-surface-compiled"],
            "mechanical_pass + slop_severity",
            {"candidate": [cell(d, "lwdb-f-surface-bare", "new_candidate"),
                           cell(d, "lwdb-f-surface-compiled", "new_candidate")]},
            {"base": [cell(d, "lwdb-f-surface-bare", "target_base"),
                      cell(d, "lwdb-f-surface-compiled", "target_base")]}),
        "causal_hypotheses": [{
            "hypothesis": "the candidate's failure is model/training/decoding, NOT the context compiler",
            "confidence": "moderate",
            "supporting_evidence": "same failure on bare and compiled → the compiler is not the differentiator",
            "contradicting_evidence": "only one compiled packet length was tested",
            "competing_explanations": ["long-packet salience effects beyond the tested packet", "decoding"],
            "required_disambiguating_test": "the packet-length controlled family (bare→compact→realistic→long→noisy)"}],
        "proposed_interventions": [{
            "intervention": "do NOT invest in the context compiler on this evidence; investigate the training recipe (steps/LR/overfitting) instead",
            "confidence": "low", "expected_effect": "avoid mis-attributing a model/training failure to the compiler",
            "risk": "the untested long-packet regime could still hide a compiler issue",
            "cost": "low (a reasoning constraint, not a build)",
            "validation_plan": "run the packet-length family before any compiler work",
            "benchmark_items_that_would_be_burned": []}]})

    # 2. length pair — long-horizon degeneration worse for candidate
    findings.append({
        "finding_id": "f-length", "capability": "A_long_form_scene / I_stability",
        "observation": obs(
            "The candidate degenerates (severe, token-capped) at BOTH short and long lengths; the "
            "base degrades only on the long arm.", ["lwdb-a-length-short", "lwdb-a-length-long", "lwdb-i-stability-long"],
            "slop_severity + hit_token_cap",
            {"candidate": [cell(d, "lwdb-a-length-short", "new_candidate"),
                           cell(d, "lwdb-a-length-long", "new_candidate")]},
            {"base": [cell(d, "lwdb-a-length-short", "target_base"),
                      cell(d, "lwdb-a-length-long", "target_base")]}),
        "causal_hypotheses": [{
            "hypothesis": "the candidate overfit (28 records, ~5 epochs) into a repetition attractor that fires even on short generations",
            "confidence": "moderate",
            "supporting_evidence": "consistent with Dispatch-20 evidence (LoRA-20 min-loss 0.08, memorized-style outputs); token-cap 9/20 vs base 3/20",
            "competing_explanations": ["decoding (greedy) interacting with an overfit model", "learning rate too high for the data size"],
            "required_disambiguating_test": "the existing-checkpoint curve (step-10 vs step-20): if step-10 is cleaner, it is over-exposure, not method"}],
        "proposed_interventions": [{
            "intervention": "fewer steps / earlier stopping and/or lower exposure per example",
            "confidence": "low", "expected_effect": "reduce degeneration if the curve is non-monotone",
            "risk": "fewer steps may under-teach", "cost": "one training run",
            "validation_plan": "checkpoint curve + a bounded confirmation run",
            "benchmark_items_that_would_be_burned": []}]})

    # 3. canon pair — separate structured-extraction failure from prose canon-application
    findings.append({
        "finding_id": "f-canon", "capability": "D_canon_continuity_constraint",
        "observation": obs(
            "The base cleanly APPLIES canon in prose (pass/none) but fails to EXTRACT clean JSON "
            "(invalid_json); the candidate degenerates on both.", ["lwdb-d-canon-extract", "lwdb-d-canon-apply"],
            "mechanical_pass + failure_labels",
            {"base_apply": cell(d, "lwdb-d-canon-apply", "target_base"),
             "base_extract": cell(d, "lwdb-d-canon-extract", "target_base")},
            {"candidate_apply": cell(d, "lwdb-d-canon-apply", "new_candidate"),
             "candidate_extract": cell(d, "lwdb-d-canon-extract", "new_candidate")}),
        "causal_hypotheses": [{
            "hypothesis": "the base's canon weakness is a STRUCTURED-OUTPUT (JSON) problem, not a canon-reasoning problem",
            "confidence": "moderate",
            "supporting_evidence": "base applies canon correctly in prose but emits invalid JSON for extraction",
            "competing_explanations": ["prompt format", "tokenizer/JSON handling"],
            "required_disambiguating_test": "a canon-extraction item with a JSON-priming example vs bare"}],
        "proposed_interventions": [{
            "intervention": "do NOT collapse invalid-JSON and invented-canon into one 'canon' problem in the dataset plan",
            "confidence": "moderate", "expected_effect": "targets the real gap (protocol) instead of over-teaching canon",
            "risk": "none material", "cost": "low",
            "validation_plan": "separate structured-protocol coverage in the dataset audit",
            "benchmark_items_that_would_be_burned": []}]})

    # 4. restraint / no-change — shared protocol weakness
    findings.append({
        "finding_id": "f-restraint", "capability": "C_restraint_no_change / E_structured_protocol",
        "observation": obs(
            "BOTH base and candidate fail the structured no-change wrapper (restraint-clean and "
            "revision-wrapper); this is a shared gap, not a candidate regression.",
            ["lwdb-c-restraint-clean", "lwdb-e-revision-wrapper"], "mechanical_pass",
            {"base": cell(d, "lwdb-c-restraint-clean", "target_base"),
             "candidate": cell(d, "lwdb-c-restraint-clean", "new_candidate")}, None),
        "causal_hypotheses": [{
            "hypothesis": "the changed/unchanged JSON wrapper is under-taught in Dataset A (only 2 no-change golds, 0 changed:true)",
            "confidence": "high",
            "supporting_evidence": "matches the Dispatch-21 coverage finding; both models fail identically",
            "competing_explanations": ["prompt clarity"],
            "required_disambiguating_test": "dataset audit no-change coverage count"}],
        "proposed_interventions": [{
            "intervention": "increase no-change / changed:true protocol coverage in the NEXT dataset (not this dispatch)",
            "confidence": "moderate", "expected_effect": "teach the wrapper both models currently miss",
            "risk": "over-representing structure could crowd prose", "cost": "authoring",
            "validation_plan": "the next controlled experiment's protocol pass-rate vs base",
            "benchmark_items_that_would_be_burned": ["lwdb-c-restraint-clean", "lwdb-e-revision-wrapper"]}]})

    # 5. voice pair
    findings.append({
        "finding_id": "f-voice", "capability": "B_focused_revision (voice)",
        "observation": obs(
            "The base handles the terse single-defect revision (pass) but fails the lyrical arm; "
            "the candidate fails both.", ["lwdb-b-voice-terse", "lwdb-b-voice-lyrical"], "mechanical_pass",
            {"base": [cell(d, "lwdb-b-voice-terse", "target_base"), cell(d, "lwdb-b-voice-lyrical", "target_base")]},
            {"candidate": [cell(d, "lwdb-b-voice-terse", "new_candidate"), cell(d, "lwdb-b-voice-lyrical", "new_candidate")]}),
        "causal_hypotheses": [{
            "hypothesis": "lyrical single-defect revision is harder (must preserve ornate register while fixing one image)",
            "confidence": "low",
            "supporting_evidence": "base passes terse, fails lyrical",
            "competing_explanations": ["the lyrical contract's forbidden imposed_minimalism is stricter"],
            "required_disambiguating_test": "reviewer judgement on whether the lyrical output was flattened vs the terse expanded"}],
        "proposed_interventions": [{
            "intervention": "keep voice preservation as a blinded reviewer dimension (mechanical gate under-measures it)",
            "confidence": "moderate", "expected_effect": "captures voice flattening the gates miss",
            "risk": "reviewer variance", "cost": "review time",
            "validation_plan": "blind reviewer voice_preservation scores", "benchmark_items_that_would_be_burned": []}]})

    # 6. constraint pair — shared protocol/constraint weakness under load
    findings.append({
        "finding_id": "f-constraint", "capability": "D_constraint (protocol under load)",
        "observation": obs(
            "BOTH models fail both constraint arms (low and high load) — a shared structured/"
            "constraint weakness, not a load-sensitivity signal that separates them.",
            ["lwdb-d-constraint-low", "lwdb-d-constraint-high"], "mechanical_pass",
            {"base_low": cell(d, "lwdb-d-constraint-low", "target_base"),
             "base_high": cell(d, "lwdb-d-constraint-high", "target_base")}, None),
        "causal_hypotheses": [{
            "hypothesis": "constraint-verdict JSON shape + minimal causal-set discipline is under-taught and hard for the base",
            "confidence": "moderate",
            "supporting_evidence": "both fail regardless of load; base over-includes in Dispatch-20 too",
            "competing_explanations": ["the low-load item is also nontrivial"],
            "required_disambiguating_test": "a JSON-primed constraint item vs bare"}],
        "proposed_interventions": [{
            "intervention": "treat constraint-verdict protocol as a structured-output gap (with canon-extract)",
            "confidence": "low", "expected_effect": "consolidates the real protocol gap",
            "risk": "none", "cost": "low", "validation_plan": "dataset audit protocol coverage",
            "benchmark_items_that_would_be_burned": []}]})

    # 7. turn pair — does the contract measure the intended distinction?
    findings.append({
        "finding_id": "f-turn", "capability": "G_multi_turn",
        "observation": obs(
            "BOTH models PASS the multi-turn arm and FAIL the single-turn arm — the opposite of the "
            "expected cumulative-damage direction; the mechanical contract may not capture the intended distinction.",
            ["lwdb-g-turn-single", "lwdb-g-turn-multi"], "mechanical_pass",
            {"base": [cell(d, "lwdb-g-turn-single", "target_base"), cell(d, "lwdb-g-turn-multi", "target_base")]},
            {"candidate": [cell(d, "lwdb-g-turn-single", "new_candidate"), cell(d, "lwdb-g-turn-multi", "new_candidate")]}),
        "causal_hypotheses": [{
            "hypothesis": "the single-turn contract (keep-last-sentence-exact) is stricter than the multi-turn one; the pair does not isolate cumulative damage mechanically",
            "confidence": "moderate",
            "supporting_evidence": "both pass multi, fail single — inconsistent with a cumulative-damage story",
            "competing_explanations": ["genuine capability quirk"],
            "required_disambiguating_test": "reviewer check of protected-span preservation across turns"}],
        "proposed_interventions": [{
            "intervention": "revise the turn-pair contracts so the mechanical gate measures cumulative damage (equalize strictness)",
            "confidence": "moderate", "expected_effect": "the pair becomes diagnostic",
            "risk": "changes a benchmark item (a NEW battery version, not this frozen one)",
            "cost": "authoring", "validation_plan": "re-run the pair after contract revision",
            "benchmark_items_that_would_be_burned": ["lwdb-g-turn-single", "lwdb-g-turn-multi"]}]})

    out = {"dispatch": 25, "schema": "diagnostic-finding-v1",
           "threshold_lock": {"git_commit": lock["git_commit"],
                              "research_sha256": lock["research_threshold_sha256"]},
           "controlled_pairs_analyzed": 7, "findings": findings}
    with open(os.path.join(RUN, "diagnostic-findings.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(out, fh, ensure_ascii=False, indent=2); fh.write("\n")
    print(f"wrote {len(findings)} pair findings (threshold-locked @ {lock['git_commit'][:12]})")


if __name__ == "__main__":
    main()
