"""Slop reviewer checklist (Dispatch 23, slop Layer 3).

Decomposed binary questions instead of one vague slop rating (CheckEval-style — see the
research review). Each positive finding must carry evidence spans, an explanation, a
severity, and a confidence. This module provides the checklist definition, a blank template,
and validation that a filled result is well-formed. Reviewers answer these blind.
"""
VERSION = "slop-reviewer-checklist-v1"

CHECKLIST = [
    {"id": "restates_previous_sentence",
     "question": "Does a sentence merely restate the preceding sentence?"},
    {"id": "explains_already_demonstrated_emotion",
     "question": "Does narration explain an emotion already demonstrated through action, dialogue, or imagery?"},
    {"id": "repeated_paragraph_function",
     "question": "Do multiple paragraphs perform the same narrative function without meaningful progression?"},
    {"id": "generic_setting_language",
     "question": "Could the description fit many unrelated settings with little alteration?"},
    {"id": "repetitive_sentence_structure",
     "question": "Does sentence structure become noticeably repetitive?"},
    {"id": "stock_transition_concentration",
     "question": "Does the passage rely on clustered stock transitions or contrast formulas?"},
    {"id": "voice_flattening",
     "question": "Does the prose flatten or replace the requested voice?"},
    {"id": "removable_without_loss",
     "question": "Could substantial text be removed without losing information, tension, characterization, or effect?"},
    {"id": "character_voice_homogenization",
     "question": "Do distinct characters sound implausibly alike?"},
    {"id": "progression_failure",
     "question": "Does each paragraph advance action, understanding, tension, setting, or character?"},
    {"id": "generic_explanatory_ending",
     "question": "Does the ending summarize or moralize what the scene already conveyed?"},
    {"id": "vague_abstraction",
     "question": "Does abstract or generic language replace concrete action, objects, or observation?"},
]
CHECKLIST_IDS = [c["id"] for c in CHECKLIST]
_SEVERITY = {"none", "low", "moderate", "high", "severe"}
_CONFIDENCE = {"high", "moderate", "low"}


def blank_checklist():
    """A blank per-item result template for a reviewer to fill."""
    return [{"id": c["id"], "question": c["question"], "positive": None,
             "evidence_spans": [], "explanation": "", "severity": None, "confidence": None}
            for c in CHECKLIST]


def validate_result(result):
    """Return a list of problems with a filled checklist result (empty == valid).

    A POSITIVE finding must carry >=1 evidence span, an explanation, a severity, and a
    confidence — no bald 'yes' without evidence.
    """
    problems = []
    ids = {r.get("id") for r in result}
    for cid in CHECKLIST_IDS:
        if cid not in ids:
            problems.append(f"missing checklist id {cid}")
    for r in result:
        if r.get("positive"):
            if not r.get("evidence_spans"):
                problems.append(f"{r.get('id')}: positive finding needs evidence_spans")
            if not r.get("explanation"):
                problems.append(f"{r.get('id')}: positive finding needs an explanation")
            if r.get("severity") not in _SEVERITY:
                problems.append(f"{r.get('id')}: invalid/missing severity")
            if r.get("confidence") not in _CONFIDENCE:
                problems.append(f"{r.get('id')}: invalid/missing confidence")
    return problems
