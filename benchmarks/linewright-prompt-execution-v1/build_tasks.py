"""Dispatch 28A — author the 30 fresh LineWright Prompt-Execution v1 tasks.

Content is ORIGINAL to this instrument (no reuse of the Dispatch-28 Prompt-Effect benchmark, no
reuse of Dataset A/A.2/A.3) so the instrument is uncontaminated for a later generation run. Every
required change, protected element, and unaffected span keys on an exact substring so correctness
is machine-checkable without an LLM grader. compiler_inputs is the ONLY block a future application
compiler may receive; evaluation_ground_truth / machine_checks are held out of it by construction.

Run this module to (a) self-check grounding and (b) emit task-manifest.jsonl/.yaml + tasks/<family>/.
Importing it exposes build_tasks() and TASKS.
"""
import json
import os
import sys
from collections import Counter

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from validators import checks as C  # noqa: E402

# ---- check constructors ----
A = lambda v: {"t": "absent", "v": v}
P = lambda v: {"t": "present", "v": v}
PR = lambda v: {"t": "preserve", "v": v}
AR = lambda v: {"t": "absent_re", "v": v}
PRE = lambda v: {"t": "present_re", "v": v}
OP = lambda o, m: {"t": "max_openers", "o": o, "max": m}
SJ = lambda keys: {"t": "shape_json", "keys": keys}
SL = lambda n: {"t": "shape_list", "min": n}

FAMILIES = {
    "multi_constraint_focused_revision": 12, "protected_text_revision": 5,
    "no_change_judgment": 4, "canon_continuation": 3, "voice_preserving_revision": 3,
    "constraint_bound_scene": 2, "structured_protocol": 1,
}
REVISION_FAMILIES = {"multi_constraint_focused_revision", "protected_text_revision",
                     "voice_preserving_revision"}


def rc(i, defect, chk, desc):
    return {"id": i, "desc": desc, "defect_type": defect, "check": chk}


def T(tid, family, title, source, user_request, ci_extra, req, prot, forb, unaff, authorized,
      req_facts, forb_facts, shape, valid_nc, diag, gold, probe=None, coverage=None,
      shape_keys=None, shape_min=None):
    gt = {
        "required_changes": req,
        "protected_elements": [{"id": p[0], "text": p[1]} for p in prot],
        "forbidden_changes": forb,
        "authorized_spans": [{"id": a[0], "desc": a[1]} for a in authorized],
        "unaffected_spans": [{"id": u[0], "text": u[1]} for u in unaff],
        "required_facts": req_facts, "forbidden_facts": forb_facts,
        "expected_output_shape": shape, "valid_no_change_case": valid_nc,
    }
    shape_checks = []
    if shape == "json":
        shape_checks = [{"id": "sh1", "kind": "schema_valid", "check": SJ(shape_keys or [])}]
    elif shape == "list":
        shape_checks = [{"id": "sh1", "kind": "schema_valid", "check": SL(shape_min or 1)}]
    mc = {
        "required_change_checks": [{"id": r["id"], "kind": r["defect_type"], "check": r["check"]} for r in req],
        "protected_text_checks": [{"id": p[0], "kind": "exact_preservation", "check": PR(p[1])} for p in prot],
        "forbidden_change_checks": [{"id": f["id"], "kind": "forbidden_guard", "check": f["check"]} for f in forb],
        "output_shape_checks": shape_checks,
        "returned_unchanged_check": {
            "normalization": {"trim_outer_whitespace": True, "normalize_line_endings": True},
            "comparison": "exact_after_normalization"},
        "partial_fix_checks": [r["id"] for r in req],
        "unauthorized_edit_checks": [{"id": u[0], "kind": "unaffected_exact", "check": PR(u[1])} for u in unaff],
    }
    d = {"instruction_position": None, "critical_instruction_type": None,
         "critical_instruction_ordinal": None, "defect_count": len(req), "difficulty": "medium",
         "context_length_class": "short", "voice_dependency": False, "canon_dependency": False}
    d.update(diag)
    task = {
        "task_id": tid, "task_family": family, "title": title, "source_passage": source,
        "user_context": user_request,
        "compiler_inputs": {
            "user_request": user_request, "source_passage": source,
            "project_context": ci_extra.get("project_context", ""),
            "scene_context": ci_extra.get("scene_context", ""),
            "canon_records": ci_extra.get("canon_records", []),
            "voice_profile": ci_extra.get("voice_profile", ""),
            "character_state": ci_extra.get("character_state", ""),
            "invention_budget": ci_extra.get("invention_budget", ""),
        },
        "evaluation_ground_truth": gt, "machine_checks": mc, "diagnostics": d,
        "gold_acceptance_requirements": {
            "contract_execution_required": True,
            "manuscript_quality_required": gold.get("mq", True),
            "acceptable_output_properties": gold.get("props", []),
        },
        "benchmark_policy": {
            "benchmark_only": True, "excluded_from_training": True,
            "excluded_from_teacher_examples": True, "excluded_from_dataset_revision_examples": True,
            "excluded_from_preference_data": True, "immutable_after_freeze": True,
        },
    }
    if probe is not None:
        task["comprehension_probe"] = probe
    else:
        task["comprehension_probe"] = {"enabled": False}
    task["_coverage"] = coverage or []
    return task


TASKS = []


def add(*a, **k):
    TASKS.append(T(*a, **k))


# =========================================================================================
# FAMILY 1 — multi_constraint_focused_revision (12)   positions 4 early / 4 middle / 4 late
# critical_instruction_type rotates: required_correction / protected_text_rule /
# unauthorized_rewrite_prohibition / output_shape_requirement (3 each)
# =========================================================================================

add("fr-01", "multi_constraint_focused_revision",
    "Harbor pier — trim the tells",
    "Marla walked to the end of the pier and looked at the water. Marla counted the gulls wheeling "
    "over the masts. Marla felt terrified of what the tide would bring. The lamp at the harbor "
    "office was still lit. The harbor was a wound in the coastline that bled ships into the grey and "
    "hungry infinite. In the end, it all came down to this.",
    "Can you tighten this a little? It feels repetitive and a bit overwritten. Keep the gull line "
    "exactly as it is — I love it.",
    {"voice_profile": "close third, plain declaratives, concrete nouns, dread carried by image not label",
     "character_state": "Marla is waiting for a ship that may not come.",
     "invention_budget": "none: no new events, weather, or characters"},
    [rc("rc1", "repetitive_openers", OP("Marla", 2), "three sentences in a row open with 'Marla'; vary them"),
     rc("rc2", "overwritten_metaphor", A("a wound in the coastline"), "cut the purple 'wound in the coastline' metaphor"),
     rc("rc3", "emotional_explanation", A("felt terrified"), "replace the 'felt terrified' telling with shown dread"),
     rc("rc4", "redundant_summary", A("it all came down to this"), "delete the redundant summary sentence")],
    [("p1", "Marla counted the gulls wheeling over the masts.")],
    [{"id": "f1", "desc": "do not rename Marla", "check": P("Marla")},
     {"id": "f2", "desc": "do not invent a storm or weather event", "check": A("storm")}],
    [("u1", "The lamp at the harbor office was still lit.")],
    [("a1", "the opening, dread, metaphor, and closing sentences may be rewritten")],
    [], [], "prose", False,
    {"instruction_position": "early", "critical_instruction_type": "required_correction",
     "critical_instruction_ordinal": 1, "context_length_class": "medium", "voice_dependency": True},
    {"mq": True, "props": ["varied openings without mechanical rephrasing",
                           "dread shown through image or action, not a 'felt' label",
                           "keeps Marla's plain observational voice", "no new events or weather"]},
    probe={"enabled": True, "expected_required_changes": 4, "expected_protected_elements": 1,
           "expected_forbidden_operations": 2, "expected_output_contract": "prose"},
    coverage=["scattered", "over_edit_trap"])

add("fr-02", "multi_constraint_focused_revision",
    "Council eve — remove the anachronism",
    "Bram set the lantern on the oak table and checked his wristwatch. The council would meet at "
    "dawn, and the fate of the whole realm hung upon the abstract weight of his indecision. He "
    "remembered his father's last words: 'Hold the gate, whatever the cost.' At last, everything changed.",
    "Fix the obvious problems here. Do not touch the line with his father's words — that quote has "
    "to stay word for word.",
    {"project_context": "pre-industrial fantasy; no modern technology exists in this world",
     "voice_profile": "grave, formal, close third",
     "invention_budget": "none: fix defects only, add nothing"},
    [rc("rc1", "anachronism", A("wristwatch"), "a wristwatch cannot exist in this world; remove it"),
     rc("rc2", "excessive_abstraction", A("the abstract weight of"), "cut the abstract 'weight of his indecision'"),
     rc("rc3", "cliche_ending", A("everything changed"), "delete the 'everything changed' cliche")],
    [("p1", "He remembered his father's last words: 'Hold the gate, whatever the cost.'")],
    [{"id": "f1", "desc": "do not rename Bram", "check": P("Bram")},
     {"id": "f2", "desc": "do not add magic or a new character", "check": A("wizard")}],
    [("u1", "The council would meet at dawn")],
    [("a1", "the first and last sentences and the abstraction may be rewritten")],
    [], [], "prose", False,
    {"instruction_position": "middle", "critical_instruction_type": "protected_text_rule",
     "critical_instruction_ordinal": 3, "difficulty": "medium"},
    {"mq": True, "props": ["period-consistent detail replaces the watch", "grave formal register intact",
                           "the father's quote is untouched"]},
    coverage=["protected_exact"])

add("fr-03", "multi_constraint_focused_revision",
    "Kitchen argument — no rewriting the clean lines",
    "'You never listen,' she said. 'You never listen to me,' she said again. He nodded slowly, his "
    "knuckles whitening on the counter. He nodded slowly, his knuckles whitening on the counter once "
    "more. I could feel the whole kitchen tighten around us. The kettle began to scream on the stove.",
    "Cut the repetition. Only fix what's actually broken — leave the good sentences alone, "
    "especially the kettle line.",
    {"voice_profile": "third-person limited, past tense, terse",
     "character_state": "two people at the end of a long fight",
     "invention_budget": "none"},
    [rc("rc1", "redundant_dialogue", A("You never listen to me"), "drop the duplicated 'You never listen to me' line"),
     rc("rc2", "repeated_body_language", A("whitening on the counter once more"), "remove the repeated whitened-knuckles cue"),
     rc("rc3", "viewpoint_drift", A("I could feel"), "the stray first-person 'I could feel' breaks the third-person POV")],
    [("p1", "The kettle began to scream on the stove.")],
    [{"id": "f1", "desc": "keep the scene in past tense", "check": A("screams")},
     {"id": "f2", "desc": "do not add a new speaker", "check": A("mother")}],
    [("u1", "He nodded slowly, his knuckles whitening on the counter.")],
    [("a1", "the duplicated dialogue, the repeated cue, and the POV slip may be rewritten")],
    [], [], "prose", False,
    {"instruction_position": "early", "critical_instruction_type": "unauthorized_rewrite_prohibition",
     "critical_instruction_ordinal": 4, "difficulty": "high"},
    {"mq": True, "props": ["one clean instance of each beat remains", "consistent third-person past",
                           "the kettle line and first gesture survive verbatim"]},
    coverage=["over_edit_trap", "protected_exact"])

add("fr-04", "multi_constraint_focused_revision",
    "Storm watch — buried format rule",
    "The rain starts before she reaches the barn. She pulls the door shut behind her. She listens to "
    "the horses shifting in the dark. She was so frightened that she could barely breathe. The barn "
    "smelled of hay and old iron. The wind outside was a great beast throwing itself against the "
    "world. And then, just like that, it was over.",
    "A few things: this drifted into present tense at the top and needs to be past like the rest; "
    "trim the melodrama; and when you're done, return the result as a numbered list of the revised "
    "sentences, one per line.",
    {"voice_profile": "past tense throughout, spare, sensory",
     "invention_budget": "none: revise the given sentences only"},
    [rc("rc1", "tense_drift", A("The rain starts before she reaches"), "opening slipped to present tense; make it past"),
     rc("rc2", "emotional_explanation", A("so frightened that she could barely breathe"), "cut the 'so frightened' telling"),
     rc("rc3", "overwritten_metaphor", A("a great beast throwing itself against the world"), "trim the overwrought wind metaphor"),
     rc("rc4", "cliche_ending", A("just like that, it was over"), "delete the 'just like that, it was over' cliche")],
    [("p1", "The barn smelled of hay and old iron.")],
    [{"id": "f1", "desc": "do not rename or add characters", "check": A("brother")},
     {"id": "f2", "desc": "do not add lightning or thunder", "check": A("thunder")}],
    [("u1", "She listens to the horses shifting in the dark.")],
    [("a1", "the tense slip, the melodrama, the metaphor, and the closing may be rewritten")],
    [], [], "list", False,
    {"instruction_position": "middle", "critical_instruction_type": "output_shape_requirement",
     "critical_instruction_ordinal": 3, "context_length_class": "medium"},
    {"mq": True, "props": ["uniform past tense", "restraint replaces melodrama",
                           "output is a clean numbered list of revised sentences"]},
    probe={"enabled": True, "expected_required_changes": 4, "expected_protected_elements": 1,
           "expected_forbidden_operations": 2, "expected_output_contract": "list"},
    shape_min=3, coverage=["scattered", "buried"])

add("fr-05", "multi_constraint_focused_revision",
    "Interrogation — what the detective can't know",
    "Detective Reyes studied the suspect across the table. The man's alibi was, in the final "
    "analysis, a function of pure contingency. Reyes knew the victim had been poisoned at exactly "
    "9:14, though the coroner's report would not arrive until morning. The fluorescent light hummed "
    "overhead. It was a truth universally acknowledged that the guilty always talk first. The room "
    "held its breath, waiting for the confession that would change all of their lives forever.",
    "Clean this up. One line has the detective knowing something he has no way of knowing yet — "
    "catch that. Trim the philosophy too.",
    {"project_context": "procedural mystery; the detective only knows what he has observed or been told",
     "character_state": "Reyes has not yet seen the coroner's report",
     "invention_budget": "none: fix defects, invent no new facts"},
    [rc("rc1", "character_knowledge_violation", A("poisoned at exactly 9:14"), "Reyes cannot know the exact time before the report arrives"),
     rc("rc2", "excessive_abstraction", A("a function of pure contingency"), "cut the abstract 'function of pure contingency'"),
     rc("rc3", "cliche_ending", A("truth universally acknowledged"), "remove the borrowed 'truth universally acknowledged' cliche"),
     rc("rc4", "redundant_summary", A("change all of their lives forever"), "delete the melodramatic summary tail")],
    [("p1", "The fluorescent light hummed overhead.")],
    [{"id": "f1", "desc": "do not rename Reyes", "check": P("Reyes")},
     {"id": "f2", "desc": "do not name the poison or invent evidence", "check": A("cyanide")}],
    [("u1", "Detective Reyes studied the suspect across the table.")],
    [("a1", "the knowledge slip, the abstraction, the cliche, and the tail may be rewritten")],
    [], [], "prose", False,
    {"instruction_position": "early", "critical_instruction_type": "required_correction",
     "critical_instruction_ordinal": 2, "difficulty": "high", "context_length_class": "medium"},
    {"mq": True, "props": ["Reyes's knowledge stays consistent with what he has seen",
                           "no invented forensic facts", "restrained, procedural register"]},
    coverage=["scattered"])

add("fr-06", "multi_constraint_focused_revision",
    "Forge — keep the maker's line",
    "Old Sena worked the bellows and studied her phone for the time. The forge glowed like the "
    "beating heart of some vast and patient god. 'A blade remembers every hand that holds it,' she "
    "told the boy. She wiped her brow with the back of her hand. She wiped her brow with the back of "
    "her hand again. The apprentice watched the sparks climb.",
    "Please revise. The line she tells the boy is the whole point of the chapter — do not change a "
    "word of it.",
    {"project_context": "low-fantasy village, no electricity or modern devices",
     "voice_profile": "earthy, close third, past tense",
     "invention_budget": "none"},
    [rc("rc1", "anachronism", A("studied her phone"), "there are no phones in this world; remove it"),
     rc("rc2", "overwritten_metaphor", A("the beating heart of some vast and patient god"), "trim the overwrought forge metaphor"),
     rc("rc3", "repeated_body_language", A("wiped her brow with the back of her hand again"), "remove the duplicated brow-wipe cue")],
    [("p1", "'A blade remembers every hand that holds it,' she told the boy.")],
    [{"id": "f1", "desc": "do not rename Sena", "check": P("Sena")},
     {"id": "f2", "desc": "do not add a customer or new character", "check": A("merchant")}],
    [("u1", "The apprentice watched the sparks climb.")],
    [("a1", "the anachronism, the metaphor, and the duplicated cue may be rewritten")],
    [], [], "prose", False,
    {"instruction_position": "middle", "critical_instruction_type": "protected_text_rule",
     "critical_instruction_ordinal": 3},
    {"mq": True, "props": ["period-true detail replaces the phone", "one brow-wipe remains",
                           "the maker's aphorism is untouched"]},
    coverage=["protected_exact"])

add("fr-07", "multi_constraint_focused_revision",
    "Departure platform — do not expand the scene",
    "Nadia stood on the platform and did not cry. Nadia held the ticket in her gloved hand. Nadia "
    "watched the train slide in. She felt an overwhelming sadness wash over her entire body. The "
    "conductor called the final boarding. (Note: keep this the same length — do not add backstory, "
    "new characters, or a flashback.) The whistle blew twice.",
    "Tighten it. Watch the repetition at the start.",
    {"voice_profile": "restrained, close third, past tense",
     "character_state": "Nadia is leaving someone behind",
     "invention_budget": "zero: same length, no backstory, no new characters, no flashback"},
    [rc("rc1", "repetitive_openers", OP("Nadia", 2), "three sentences in a row open with 'Nadia'; vary them"),
     rc("rc2", "emotional_explanation", A("overwhelming sadness wash over her entire body"), "replace the 'overwhelming sadness' telling with restraint"),
     rc("rc3", "unauthorized_expansion", A("(Note: keep this the same length"), "remove the parenthetical author note from the prose")],
    [("p1", "The whistle blew twice.")],
    [{"id": "f1", "desc": "do not add backstory or a flashback", "check": A("years earlier")},
     {"id": "f2", "desc": "do not add a new character", "check": A("her mother")}],
    [("u1", "The conductor called the final boarding.")],
    [("a1", "the repeated openers, the telling line, and the stray note may be revised")],
    [], [], "prose", False,
    {"instruction_position": "middle", "critical_instruction_type": "unauthorized_rewrite_prohibition",
     "critical_instruction_ordinal": 6, "context_length_class": "medium"},
    {"mq": True, "props": ["varied openings", "sorrow shown through restraint",
                           "no added length, backstory, or characters"]},
    probe={"enabled": True, "expected_required_changes": 3, "expected_protected_elements": 1,
           "expected_forbidden_operations": 2, "expected_output_contract": "prose"},
    coverage=["buried", "over_edit_trap"])

add("fr-08", "multi_constraint_focused_revision",
    "Return to the keep — canon says grey eyes",
    "The rain begins as Aldous rides through the gate. The steward met him with a lantern and a bow. "
    "'Your green eyes are your mother's,' the steward said, and Aldous almost smiled. The hall was "
    "cold. And in that moment, he knew he was finally home.",
    "Revise for continuity and register. Return your answer as a JSON object with keys "
    "\"revision\" and \"changes\".",
    {"project_context": "series canon: Aldous has grey eyes, established in book one",
     "canon_records": ["Aldous's eyes are grey.", "Aldous's mother died when he was nine."],
     "voice_profile": "past tense, measured",
     "invention_budget": "none: correct to canon, invent nothing"},
    [rc("rc1", "canon_inconsistency", A("green eyes"), "canon says Aldous has grey eyes, not green"),
     rc("rc2", "tense_drift", A("The rain begins as Aldous rides"), "opening slipped to present tense; make it past"),
     rc("rc3", "cliche_ending", A("he knew he was finally home"), "cut the 'finally home' cliche")],
    [("p1", "The hall was cold.")],
    [{"id": "f1", "desc": "keep the mother reference", "check": P("mother")},
     {"id": "f2", "desc": "do not kill or introduce a character", "check": A("died")}],
    [("u1", "The steward met him with a lantern and a bow.")],
    [("a1", "the eye colour, the tense slip, and the closing may be rewritten")],
    ["grey eyes"], ["green eyes"], "json", False,
    {"instruction_position": "late", "critical_instruction_type": "output_shape_requirement",
     "critical_instruction_ordinal": 2, "canon_dependency": True, "difficulty": "high"},
    {"mq": True, "props": ["eye colour matches canon", "uniform past tense",
                           "valid JSON with revision and changes keys"]},
    shape_keys=["revision", "changes"], coverage=["scattered", "buried"])

add("fr-09", "multi_constraint_focused_revision",
    "Rooftop — scattered overwriting",
    "The city sprawled beneath them like an infinite circuit board of longing and regret. Kell "
    "checked the rope. 'We should go,' I said, though it was Kell who had spoken. The night was the "
    "profound and total absence of everything that mattered. 'We should go,' Kell said. Below, a "
    "siren rose and fell.",
    "This is overcooked in places and the point of view slips. Clean it.",
    {"voice_profile": "third-person limited on Kell, past tense, lean",
     "invention_budget": "none"},
    [rc("rc1", "overwritten_metaphor", A("an infinite circuit board of longing and regret"), "cut the overwrought skyline metaphor"),
     rc("rc2", "excessive_abstraction", A("the profound and total absence of everything that mattered"), "trim the abstract night description"),
     rc("rc3", "redundant_dialogue", A("'We should go,' I said, though it was Kell who had spoken"), "the mis-attributed duplicate 'We should go' line must go"),
     rc("rc4", "viewpoint_drift", A("I said"), "remove the first-person slip; the POV is limited to Kell")],
    [("p1", "Below, a siren rose and fell.")],
    [{"id": "f1", "desc": "keep Kell as the viewpoint character", "check": P("Kell")},
     {"id": "f2", "desc": "do not add a fall, jump, or death", "check": A("jumped")}],
    [("u1", "Kell checked the rope.")],
    [("a1", "the two metaphors and the mis-attributed line may be rewritten")],
    [], [], "prose", False,
    {"instruction_position": "early", "critical_instruction_type": "required_correction",
     "critical_instruction_ordinal": 1, "difficulty": "high", "context_length_class": "medium"},
    {"mq": True, "props": ["single clean 'We should go' beat", "consistent limited POV on Kell",
                           "lean imagery replaces the purple lines"]},
    coverage=["scattered"])

add("fr-10", "multi_constraint_focused_revision",
    "Nursery — keep the lullaby line",
    "Iris rocked the cradle in the lamplight. Iris hummed the tune her grandmother taught her. Iris "
    "checked her smartwatch and sighed. She felt a love so deep it hurt to hold. 'Sleep now, little "
    "tide,' she whispered, the way she always did.",
    "Fix this up. The whispered line at the end is a recurring motif in the book, so keep it exactly.",
    {"project_context": "contemporary-set but the room is deliberately timeless; still, no anachronism error should stand",
     "voice_profile": "tender, close third, past tense",
     "invention_budget": "none"},
    [rc("rc1", "repetitive_openers", OP("Iris", 2), "three sentences in a row open with 'Iris'; vary them"),
     rc("rc2", "anachronism", A("smartwatch"), "the smartwatch detail clashes with the timeless framing; remove it"),
     rc("rc3", "emotional_explanation", A("a love so deep it hurt to hold"), "replace the 'love so deep' telling with a shown gesture")],
    [("p1", "'Sleep now, little tide,' she whispered, the way she always did.")],
    [{"id": "f1", "desc": "do not rename Iris", "check": P("Iris")},
     {"id": "f2", "desc": "do not add a second child or partner", "check": A("husband")}],
    [("u1", "Iris hummed the tune her grandmother taught her.")],
    [("a1", "the openers, the device detail, and the telling line may be revised")],
    [], [], "prose", False,
    {"instruction_position": "late", "critical_instruction_type": "protected_text_rule",
     "critical_instruction_ordinal": 4, "voice_dependency": True},
    {"mq": True, "props": ["varied openings", "love shown through gesture",
                           "the lullaby motif line is untouched"]},
    coverage=["protected_exact"])

add("fr-11", "multi_constraint_focused_revision",
    "Duel dawn — resist the tempting cuts",
    "Two swordsmen faced each other in the frost. Ser Cadel saluted with his blade, the steel "
    "catching the first pale light. His opponent said nothing. Ser Cadel saluted with his blade "
    "again, as if the first time had not counted. The whole duel was, ultimately, a meditation on "
    "the impermanence of honour. Their breath smoked in the cold.",
    "Trim the repeats and the overwriting. Be careful not to gut the scene — leave anything that's "
    "already working, particularly the final image.",
    {"voice_profile": "formal, past tense, cinematic restraint",
     "invention_budget": "none"},
    [rc("rc1", "repeated_body_language", A("saluted with his blade again"), "remove the duplicated salute cue"),
     rc("rc2", "excessive_abstraction", A("a meditation on the impermanence of honour"), "cut the abstract 'meditation on impermanence' line"),
     rc("rc3", "overwritten_metaphor", A("the steel catching the first pale light"), "the ornamented salute clause is overwritten; simplify it")],
    [("p1", "Their breath smoked in the cold.")],
    [{"id": "f1", "desc": "do not decide the duel's outcome", "check": A("fell")},
     {"id": "f2", "desc": "do not rename Ser Cadel", "check": P("Cadel")}],
    [("u1", "His opponent said nothing.")],
    [("a1", "the duplicate salute, the abstraction, and the ornament may be revised")],
    [], [], "prose", False,
    {"instruction_position": "late", "critical_instruction_type": "unauthorized_rewrite_prohibition",
     "critical_instruction_ordinal": 5, "difficulty": "high"},
    {"mq": True, "props": ["one salute remains", "no verdict on the duel",
                           "the final breath image and the silent-opponent line survive"]},
    coverage=["over_edit_trap", "protected_exact"])

add("fr-12", "multi_constraint_focused_revision",
    "Field hospital — buried canon and format",
    "Nurse Okonkwo moved between the cots by candlelight. She reached for the antibiotics on the "
    "high shelf. 'We lost three tonight,' she told the surgeon, and her voice did not shake. The "
    "tent breathed with the wind. It was the best of times, it was the worst of times.",
    "Two corrections and a format request are mixed into this note: the setting is 1854 so one "
    "supply detail is wrong for the period; the borrowed opening-of-a-famous-novel line has to go; "
    "and please give the result as a numbered list of the revised sentences.",
    {"project_context": "Crimean-War-era field hospital, 1854; antibiotics did not exist yet",
     "canon_records": ["The story is set in 1854.", "Penicillin was not available until the 20th century."],
     "invention_budget": "none: correct the period error and the borrowed line only"},
    [rc("rc1", "character_knowledge_violation", A("antibiotics"), "antibiotics do not exist in 1854; use a period-true supply"),
     rc("rc2", "canon_inconsistency", A("best of times, it was the worst of times"), "delete the borrowed famous-novel line"),
     rc("rc3", "cliche_ending", A("the tent breathed with the wind"), "the personified 'tent breathed' image is a tired closer; revise it")],
    [("p1", "'We lost three tonight,' she told the surgeon, and her voice did not shake.")],
    [{"id": "f1", "desc": "do not rename Okonkwo", "check": P("Okonkwo")},
     {"id": "f2", "desc": "do not add a named battle or date beyond the setting", "check": A("Balaclava")}],
    [("u1", "Nurse Okonkwo moved between the cots by candlelight.")],
    [("a1", "the supply detail, the borrowed line, and the closer may be revised")],
    [], [], "list", False,
    {"instruction_position": "late", "critical_instruction_type": "output_shape_requirement",
     "critical_instruction_ordinal": 3, "canon_dependency": True, "difficulty": "high"},
    {"mq": True, "props": ["period-true supply detail", "no borrowed famous line",
                           "output is a numbered list of revised sentences"]},
    shape_min=3, coverage=["buried"])

# =========================================================================================
# FAMILY 2 — protected_text_revision (5): a small required fix + strong exact protection
# =========================================================================================

add("pt-01", "protected_text_revision",
    "Epitaph — one word wrong",
    "They buried the captain beneath the old yew. The stone read: 'She held the line so others could "
    "cross.' The date on the marker said 1817, though every record placed her death in 1819. Rain "
    "filled the carved letters.",
    "There's a factual slip in the date — the records say 1819. Fix only that. The inscription in "
    "quotes must remain exactly as written.",
    {"project_context": "historical fiction; the captain died in 1819 per established records",
     "canon_records": ["The captain died in 1819."],
     "invention_budget": "none: correct the date only"},
    [rc("rc1", "canon_inconsistency", A("1817"), "the marker date should be 1819, not 1817")],
    [("p1", "The stone read: 'She held the line so others could cross.'")],
    [{"id": "f1", "desc": "do not alter the inscription", "check": P("She held the line so others could cross")},
     {"id": "f2", "desc": "do not add a cause of death", "check": A("drowned")}],
    [("u1", "Rain filled the carved letters.")],
    [("a1", "only the date may change")],
    ["1819"], ["1817"], "prose", False,
    {"instruction_position": None, "critical_instruction_type": "protected_text_rule",
     "critical_instruction_ordinal": 2, "canon_dependency": True},
    {"mq": True, "props": ["date corrected to 1819", "inscription preserved verbatim",
                           "nothing else altered"]},
    probe={"enabled": True, "expected_required_changes": 1, "expected_protected_elements": 1,
           "expected_forbidden_operations": 2, "expected_output_contract": "prose"},
    coverage=[])

add("pt-02", "protected_text_revision",
    "Spell text — fix the frame, keep the incantation",
    "The mage lit the candles and, in the final analysis, prepared herself. She spoke the words "
    "carved above the door: 'By root and rain, by iron and name, I bind thee.' The room grew colder.",
    "Trim the abstract phrase in the first sentence. Do not touch the incantation between the quotes.",
    {"voice_profile": "incantatory, close third",
     "invention_budget": "none"},
    [rc("rc1", "excessive_abstraction", A("in the final analysis"), "cut the abstract 'in the final analysis'")],
    [("p1", "She spoke the words carved above the door: 'By root and rain, by iron and name, I bind thee.'")],
    [{"id": "f1", "desc": "do not alter the incantation", "check": P("By root and rain, by iron and name, I bind thee")},
     {"id": "f2", "desc": "do not name the thing being bound", "check": A("demon")}],
    [("u1", "The room grew colder.")],
    [("a1", "only the first sentence's abstraction may change")],
    [], [], "prose", False,
    {"instruction_position": None, "critical_instruction_type": "protected_text_rule",
     "critical_instruction_ordinal": 2},
    {"mq": True, "props": ["abstraction removed", "incantation verbatim", "eerie register intact"]},
    coverage=[])

add("pt-03", "protected_text_revision",
    "Letter home — one anachronism, keep the closing",
    "Dearest Mother, the trenches are quieter tonight. I emailed the lieutenant about my leave, but "
    "I expect nothing will come of it. Whatever happens, know that I remain, as ever, your loving son.",
    "This is a WWI letter. One line has a modern impossibility — fix that. Keep the final sentence, "
    "the sign-off, exactly.",
    {"project_context": "First World War epistolary fiction; no electronic communication exists",
     "invention_budget": "none: correct the anachronism only"},
    [rc("rc1", "anachronism", A("emailed the lieutenant"), "soldiers in WWI could not email; use a period-true means")],
    [("p1", "Whatever happens, know that I remain, as ever, your loving son.")],
    [{"id": "f1", "desc": "keep the sign-off", "check": P("I remain, as ever, your loving son")},
     {"id": "f2", "desc": "do not add the soldier's death", "check": A("killed")}],
    [("u1", "Dearest Mother, the trenches are quieter tonight.")],
    [("a1", "only the anachronistic line may change")],
    [], [], "prose", False,
    {"instruction_position": None, "critical_instruction_type": "protected_text_rule",
     "critical_instruction_ordinal": 2, "canon_dependency": True},
    {"mq": True, "props": ["period-true correspondence replaces email", "sign-off verbatim",
                           "quiet elegiac tone intact"]},
    coverage=[])

add("pt-04", "protected_text_revision",
    "Recipe card — fix the step, keep the warning",
    "Grandmother's honey cake: cream the butter, then fold in the flour, then add the eggs. WARNING: "
    "never open the oven in the first twenty minutes or the cake will fall.",
    "The eggs should go in before the flour, not after — fix the order. Keep the WARNING line word "
    "for word.",
    {"project_context": "domestic fiction; the recipe is a family heirloom object",
     "invention_budget": "none: correct the step order only"},
    [rc("rc1", "required_correction", A("fold in the flour, then add the eggs"), "eggs are added before flour; correct the order")],
    [("p1", "WARNING: never open the oven in the first twenty minutes or the cake will fall.")],
    [{"id": "f1", "desc": "keep the warning", "check": P("never open the oven in the first twenty minutes")},
     {"id": "f2", "desc": "do not add ingredients", "check": A("vanilla")}],
    [("u1", "Grandmother's honey cake:")],
    [("a1", "only the step order may change")],
    ["add the eggs, then fold in the flour"], [], "prose", False,
    {"instruction_position": None, "critical_instruction_type": "required_correction",
     "critical_instruction_ordinal": 1},
    {"mq": True, "props": ["egg/flour order corrected", "warning verbatim", "no new ingredients"]},
    coverage=[])

add("pt-05", "protected_text_revision",
    "Treaty clause — modernise nothing but the typo",
    "Article IV. The signatories hereby aggree to cease all hostilities at the stroke of noon. This "
    "clause shall bind their heirs and successors in perpetuity.",
    "There's a spelling error in Article IV — correct it. Do not modernise or reword the legal "
    "language; leave the perpetuity sentence exactly as it is.",
    {"project_context": "period legal document in an alternate-history novel",
     "invention_budget": "none: fix the spelling only"},
    [rc("rc1", "required_correction", A("aggree"), "'aggree' is misspelled; it should be 'agree'")],
    [("p1", "This clause shall bind their heirs and successors in perpetuity.")],
    [{"id": "f1", "desc": "keep the perpetuity sentence", "check": P("bind their heirs and successors in perpetuity")},
     {"id": "f2", "desc": "do not add a new article", "check": A("Article V")}],
    [("u1", "at the stroke of noon")],
    [("a1", "only the misspelling may change")],
    ["agree to cease all hostilities"], [], "prose", False,
    {"instruction_position": None, "critical_instruction_type": "required_correction",
     "critical_instruction_ordinal": 1},
    {"mq": True, "props": ["spelling corrected to 'agree'", "archaic legal register preserved",
                           "perpetuity clause verbatim"]},
    coverage=[])

# =========================================================================================
# FAMILY 3 — no_change_judgment (4): the correct action is to return unchanged
# =========================================================================================

def nochange(tid, title, source, user_request, ci, forb, protect, unaff, gold):
    add(tid, "no_change_judgment", title, source, user_request, ci,
        [],  # NO required changes — editing is the failure mode
        protect, forb, unaff, [("a1", "no span is authorized for change")],
        [], [], "prose", True,
        {"instruction_position": None, "critical_instruction_type": "no_change_judgment",
         "critical_instruction_ordinal": None},
        gold)


nochange("nc-01", "Already clean — resist the itch",
    "The ferry cut across the still water. Gulls tilted in the wake. On the far shore, the town "
    "lights came up one by one. He did not look back.",
    "Have a look at this and fix anything that needs fixing.",
    {"voice_profile": "spare, past tense, imagistic",
     "invention_budget": "none: the passage is finished; change nothing unless something is actually wrong"},
    [{"id": "f1", "desc": "do not add drama or a twist", "check": A("suddenly")},
     {"id": "f2", "desc": "do not add dialogue", "check": A("he said")}],
    [("p1", "He did not look back.")],
    [("u1", "The ferry cut across the still water.")],
    {"mq": True, "props": ["recognises the passage needs no change",
                           "returns it unchanged (or states no change is needed)",
                           "does not invent problems to fix"]})

nochange("nc-02", "Correct grammar the reader may 'fix'",
    "None of the sailors was willing to speak. The data were incomplete, and the crew knew it. "
    "Whom the captain blamed, no one could say.",
    "Proofread this and correct any grammar mistakes.",
    {"project_context": "the passage uses correct formal grammar that is often mistaken for errors",
     "invention_budget": "none: only correct genuine errors"},
    [{"id": "f1", "desc": "do not change 'was' to 'were' after None", "check": P("None of the sailors was")},
     {"id": "f2", "desc": "do not change 'data were' to 'data was'", "check": P("The data were incomplete")}],
    [("p1", "Whom the captain blamed, no one could say.")],
    [("u1", "None of the sailors was willing to speak.")],
    {"mq": True, "props": ["recognises the grammar is already correct",
                           "leaves 'None ... was', 'data were', and 'Whom' intact",
                           "returns the passage unchanged"]})

nochange("nc-03", "Deliberate fragment style",
    "Cold. The kind that gets into the teeth. Nobody moving on the platform. Just steam and the smell "
    "of iron and the long wait for a train that might not come.",
    "Tidy this up into complete sentences if it reads awkwardly.",
    {"voice_profile": "intentional sentence fragments for rhythm; a deliberate stylistic choice",
     "invention_budget": "none: the fragments are intentional"},
    [{"id": "f1", "desc": "do not splice the fragments into full sentences", "check": P("Cold. The kind that gets into the teeth.")},
     {"id": "f2", "desc": "do not add a subject to the last fragment", "check": A("There was just steam")}],
    [("p1", "Just steam and the smell of iron and the long wait for a train that might not come.")],
    [("u1", "Nobody moving on the platform.")],
    {"mq": True, "props": ["recognises the fragments are a deliberate style",
                           "preserves the staccato rhythm", "returns the passage unchanged"]})

nochange("nc-04", "Dialect that isn't an error",
    "'I ain't going back down there,' Tam said. 'Not for you, not for nobody.' The lantern guttered "
    "between them.",
    "Clean up the dialogue so it's grammatical.",
    {"project_context": "the dialect and double negative are true to the character's voice",
     "voice_profile": "regional dialect in dialogue; narration is standard",
     "invention_budget": "none: the dialect is intentional character voice"},
    [{"id": "f1", "desc": "do not standardise the dialogue", "check": P("I ain't going back down there")},
     {"id": "f2", "desc": "do not remove the double negative", "check": P("not for nobody")}],
    [("p1", "'Not for you, not for nobody.'")],
    [("u1", "The lantern guttered between them.")],
    {"mq": True, "props": ["recognises the dialect is intentional voice, not error",
                           "leaves the dialogue as written", "returns the passage unchanged"]})

# =========================================================================================
# FAMILY 4 — canon_continuation (3): continue consistently; include required facts, avoid forbidden
# =========================================================================================

def canon(tid, title, source, user_request, ci, req, forb, req_facts, forb_facts, gold, probe=None):
    add(tid, "canon_continuation", title, source, user_request, ci, req, [], forb, [],
        [("a1", "the continuation is authored fresh, consistent with canon")],
        req_facts, forb_facts, "prose", False,
        {"instruction_position": None, "critical_instruction_type": "canon_fidelity",
         "critical_instruction_ordinal": None, "canon_dependency": True},
        gold, probe=probe)


canon("cn-01", "Continue — the sister is dead",
    "Corin pushed open the door to the workshop. Dust hung in the light. He had not been back since "
    "the funeral.",
    "Write the next two or three sentences. Stay consistent with the canon notes.",
    {"project_context": "canon: Corin's sister Vaela died last winter; her workshop is untouched since",
     "canon_records": ["Vaela is Corin's sister.", "Vaela died last winter.",
                       "The workshop has been sealed since her death."],
     "character_state": "grieving, returning for the first time",
     "invention_budget": "low: you may add sensory detail consistent with a sealed, dusty workshop; introduce no living new characters"},
    [rc("rc1", "canon_fact_inclusion", PRE(r"\bVaela\b"), "the continuation must name his late sister Vaela"),
     rc("rc2", "canon_fact_inclusion", PRE(r"her death|the grave|\bgone\b|untouched|her tools|her things|sealed|she left"),
        "the continuation must reflect that she is dead and the room untouched")],
    [{"id": "f1", "desc": "do not resurrect or speak-to a living Vaela", "check": A("Vaela smiled")},
     {"id": "f2", "desc": "do not introduce a living new character", "check": A("a voice called")}],
    ["Vaela", "the room is untouched/sealed since the death"],
    ["Vaela is alive", "a new living character appears"],
    {"mq": True, "props": ["names Vaela consistent with her death", "honours the sealed room",
                           "grief carried by restraint, not exposition"]},
    probe={"enabled": True, "expected_required_changes": 2, "expected_protected_elements": 0,
           "expected_forbidden_operations": 2, "expected_output_contract": "prose"})

canon("cn-02", "Continue — the city has no sun",
    "Mira climbed the last stair to the observation deck. The great lamps of the undercity burned "
    "far below.",
    "Continue for two or three sentences, true to the world.",
    {"project_context": "canon: the city lies underground; there is no sun, sky, or daylight; time is kept by the great lamps",
     "canon_records": ["The city is underground.", "There is no sun or sky.",
                       "Time is measured by the great lamps."],
     "invention_budget": "low: sensory detail consistent with a lamplit underground city only"},
    [rc("rc1", "canon_fact_inclusion", PRE(r"no sky|no sun|no stars|\brock\b|\bstone\b|ceiling|the deep|the dark"),
        "the continuation must reinforce the enclosed, skyless underground world")],
    [{"id": "f1", "desc": "no sun", "check": A("the sun")},
     {"id": "f2", "desc": "no sky or daylight", "check": A("the sky")}],
    ["lamplit underground setting", "Mira"],
    ["the sun", "the sky", "daylight"],
    {"mq": True, "props": ["no sun or sky appears", "detail stays underground and lamplit",
                           "Mira remains the anchor"]})

canon("cn-03", "Continue — magic has a cost",
    "Devi pressed her palm to the ward-stone and felt it wake. The lines of light spread under her "
    "fingers.",
    "Add two or three sentences continuing the moment, consistent with how magic works here.",
    {"project_context": "canon: every use of magic costs the caster memories; Devi has already lost her childhood",
     "canon_records": ["Magic costs the caster memories.", "Devi has already forgotten her childhood."],
     "invention_budget": "low: you may show the cost; do not invent a cost-free spell"},
    [rc("rc1", "canon_fact_inclusion", PRE(r"forgot|forget|memory|memories|\blost\b"), "the continuation must reflect that magic costs memory")],
    [{"id": "f1", "desc": "magic is never free here", "check": A("without cost")},
     {"id": "f2", "desc": "do not restore her lost memories", "check": A("remembered her childhood")}],
    ["the memory-cost of magic", "Devi"],
    ["cost-free magic", "restored childhood memories"],
    {"mq": True, "props": ["the memory cost is honoured", "no cost-free magic",
                           "restraint over exposition"]})

# =========================================================================================
# FAMILY 5 — voice_preserving_revision (3): small fix, preserve a distinctive voice
# =========================================================================================

add("vp-01", "voice_preserving_revision",
    "Hard-boiled narrator — one anachronism",
    "The dame walked in like trouble with a better coat. I'd seen her type before, seen 'em come and "
    "go like cheap cigarettes. She checked her smartphone and asked if I was the guy. Sure I was the "
    "guy. I'm always the guy.",
    "Fix the one detail that doesn't fit a 1940s noir. Keep the narrator's voice exactly as punchy "
    "as it is — don't smooth it out.",
    {"project_context": "1940s hard-boiled detective pastiche; period-accurate world",
     "voice_profile": "first-person, clipped, wisecracking, simile-heavy noir",
     "invention_budget": "none: fix the anachronism, preserve the voice"},
    [rc("rc1", "anachronism", A("smartphone"), "no smartphones in the 1940s; use a period-true detail")],
    [("p1", "The dame walked in like trouble with a better coat."),
     ("p2", "I'm always the guy.")],
    [{"id": "f1", "desc": "do not flatten the noir voice into neutral prose", "check": P("like trouble with a better coat")},
     {"id": "f2", "desc": "keep the first-person narration", "check": PRE(r"\bI(?:'d|'m| )")}],
    [("u1", "Sure I was the guy.")],
    [("a1", "only the anachronistic detail may change")],
    [], [], "prose", False,
    {"instruction_position": None, "critical_instruction_type": "voice_preservation",
     "critical_instruction_ordinal": 2, "voice_dependency": True},
    {"mq": True, "props": ["period-true detail replaces the smartphone",
                           "clipped wisecracking voice fully intact", "signature lines preserved"]})

add("vp-02", "voice_preserving_revision",
    "Whimsical fabulist — trim one abstraction",
    "The clockmaker kept every hour he had ever wasted in a jar on the high shelf, and on Sundays he "
    "let a few of them out to stretch their legs. It was, in a very real sense, a form of temporal "
    "stewardship. The smallest hour liked to hide inside the teapot.",
    "Cut the dry academic sentence in the middle — it breaks the spell. Keep the playful fairy-tale "
    "voice everywhere else.",
    {"project_context": "literary fabulism; whimsical, matter-of-fact-about-the-impossible voice",
     "voice_profile": "whimsical, deadpan-magical, long lyrical sentences",
     "invention_budget": "none: remove the flat line, keep the voice"},
    [rc("rc1", "excessive_abstraction", A("in a very real sense, a form of temporal stewardship"), "cut the dry 'temporal stewardship' sentence")],
    [("p1", "The clockmaker kept every hour he had ever wasted in a jar on the high shelf, and on Sundays he let a few of them out to stretch their legs."),
     ("p2", "The smallest hour liked to hide inside the teapot.")],
    [{"id": "f1", "desc": "do not explain or literalise the magic", "check": A("metaphor for")},
     {"id": "f2", "desc": "keep the whimsical concrete imagery", "check": P("hide inside the teapot")}],
    [("u1", "The smallest hour liked to hide inside the teapot.")],
    [("a1", "only the flat middle sentence may be removed")],
    [], [], "prose", False,
    {"instruction_position": None, "critical_instruction_type": "voice_preservation",
     "critical_instruction_ordinal": 2, "voice_dependency": True},
    {"mq": True, "props": ["the flat academic line is gone",
                           "whimsical voice and imagery preserved", "spell unbroken"]})

add("vp-03", "voice_preserving_revision",
    "Breathless run-on youth — one continuity slip",
    "Okay so we were running, right, we were running down Fenwick and Jonah had the bag and I had "
    "the other bag and my heart was going like a drum solo and then Jonah, who was definitely "
    "wearing his red jacket, ducks into the alley and we just lose him. My blue coat snagged on the "
    "fence but I didn't care.",
    "There's a small continuity error — earlier chapters establish Jonah's jacket is green, not red. "
    "Fix only that. Keep the breathless, run-on teenage voice completely intact.",
    {"project_context": "YA first-person; canon: Jonah's jacket is green",
     "canon_records": ["Jonah wears a green jacket."],
     "voice_profile": "breathless first-person run-ons, present-tense slips are intentional style",
     "invention_budget": "none: fix the jacket colour only"},
    [rc("rc1", "canon_inconsistency", A("red jacket"), "canon says Jonah's jacket is green, not red")],
    [("p1", "my heart was going like a drum solo"),
     ("p2", "My blue coat snagged on the fence but I didn't care.")],
    [{"id": "f1", "desc": "do not tidy the run-on syntax", "check": P("Okay so we were running, right")},
     {"id": "f2", "desc": "keep the narrator's own blue coat", "check": P("My blue coat")}],
    [("u1", "My blue coat snagged on the fence but I didn't care.")],
    [("a1", "only Jonah's jacket colour may change")],
    ["green jacket"], ["red jacket"], "prose", False,
    {"instruction_position": None, "critical_instruction_type": "voice_preservation",
     "critical_instruction_ordinal": 2, "voice_dependency": True, "canon_dependency": True},
    {"mq": True, "props": ["jacket corrected to green", "narrator's blue coat untouched",
                           "breathless run-on voice fully preserved"]})

# =========================================================================================
# FAMILY 6 — constraint_bound_scene (2): draft a short scene under hard constraints
# =========================================================================================

add("sc-01", "constraint_bound_scene",
    "Wordless reunion",
    "",
    "Write a short scene (4-6 sentences) in which two estranged brothers meet again at their "
    "father's grave. Hard constraints: they must NOT speak a single word of dialogue; the season is "
    "winter; and the older brother, Eli, must be the point-of-view character.",
    {"project_context": "quiet literary drama",
     "scene_context": "a churchyard in winter, two estranged brothers, their father's grave",
     "character_state": "years of silence between them; grief and pride",
     "voice_profile": "restrained close third on Eli, past tense",
     "invention_budget": "moderate: you may invent gesture, weather, and setting detail within the constraints"},
    [rc("rc1", "constraint_no_dialogue", AR('["“”]'), "no quoted dialogue is allowed in this scene (no double-quote marks)"),
     rc("rc2", "constraint_season", PRE(r"snow|frost|cold|winter|ice|breath"), "the winter setting must be present in the imagery"),
     rc("rc3", "constraint_pov", PRE(r"\bEli\b"), "Eli must be the named point-of-view character")],
    [], [{"id": "f1", "desc": "no spoken dialogue at all", "check": AR(r"\bsaid\b")},
         {"id": "f2", "desc": "do not resolve the estrangement with a speech", "check": A("forgive me")}],
    [], [("a1", "the whole scene is authored under the stated constraints")],
    ["Eli as POV", "winter imagery", "no dialogue"], ["any spoken dialogue"],
    "prose", False,
    {"instruction_position": None, "critical_instruction_type": "constraint_binding",
     "critical_instruction_ordinal": 1, "voice_dependency": True, "difficulty": "high"},
    {"mq": True, "props": ["no dialogue whatsoever", "winter is felt, not just named",
                           "Eli's interiority carries the estrangement", "gesture does the work"]})

add("sc-02", "constraint_bound_scene",
    "The letter she can't send",
    "",
    "Write a short scene (4-6 sentences): a woman drafts and destroys a letter. Hard constraints: "
    "the entire scene takes place in ONE room; no other character appears or is spoken to; and you "
    "must NOT state what the letter is about — the reader should only infer its weight.",
    {"project_context": "interior character study",
     "scene_context": "a single room at night, one woman, an unfinished letter",
     "character_state": "she has something she cannot say and cannot keep",
     "voice_profile": "close third, past tense, oblique",
     "invention_budget": "moderate: room detail and gesture only, within the constraints"},
    [rc("rc1", "constraint_single_room", A("she went outside"), "the scene may not leave the room"),
     rc("rc2", "constraint_no_second_character", AR(r"\bhe said\b|\bthey said\b"), "no other character speaks or appears"),
     rc("rc3", "constraint_withhold_subject", PRE(r"letter|page|paper|words|ink"), "keep the focus on the act of writing/destroying, not a stated subject")],
    [], [{"id": "f1", "desc": "do not name what the letter concerns", "check": A("the affair")},
         {"id": "f2", "desc": "no second character enters", "check": A("the door opened and")}],
    [], [("a1", "the whole scene is authored under the stated constraints")],
    ["one room", "no second character", "subject withheld"],
    ["an explicit statement of the letter's subject"],
    "prose", False,
    {"instruction_position": None, "critical_instruction_type": "constraint_binding",
     "critical_instruction_ordinal": 3, "difficulty": "high"},
    {"mq": True, "props": ["confined to one room", "no second character", "subject stays implied",
                           "weight carried by gesture and restraint"]})

# =========================================================================================
# FAMILY 7 — structured_protocol (1): output must be a valid JSON object
# =========================================================================================

add("sp-01", "structured_protocol",
    "Scene-card extraction",
    "The heist went wrong the moment the lights came back on. Dain froze in the vault doorway while "
    "the alarm climbed. Behind him, Sera was already gone.",
    "Read the passage and return ONLY a JSON object with exactly these keys: \"pov_character\" (the "
    "point-of-view character's name), \"setting\" (one short phrase), and \"tension\" (one sentence "
    "naming the central tension). Do not include any prose outside the JSON.",
    {"project_context": "tooling task: convert a passage into a structured scene card",
     "invention_budget": "none: extract only what the passage states"},
    [rc("rc1", "schema_valid", SJ(["pov_character", "setting", "tension"]), "output must be a JSON object with the three required keys"),
     rc("rc2", "required_fact_present", P("Dain"), "the pov_character is Dain")],
    [], [{"id": "f1", "desc": "do not invent a character not in the passage", "check": A("guard")},
         {"id": "f2", "desc": "do not add keys beyond the three requested", "check": A("summary")}],
    [], [("a1", "the whole output is authored as the requested JSON")],
    ["Dain as pov_character"], ["a fourth key"], "json", False,
    {"instruction_position": None, "critical_instruction_type": "output_shape_requirement",
     "critical_instruction_ordinal": 1, "difficulty": "medium"},
    {"mq": False, "props": ["valid JSON, exactly three keys", "pov_character is Dain",
                            "no prose outside the JSON", "no invented content"]},
    probe={"enabled": True, "expected_required_changes": 2, "expected_protected_elements": 0,
           "expected_forbidden_operations": 2, "expected_output_contract": "json"},
    shape_keys=["pov_character", "setting", "tension"])


# =========================================================================================
# emit
# =========================================================================================

def _self_check():
    problems = []
    fams = Counter(t["task_family"] for t in TASKS)
    if dict(fams) != FAMILIES:
        problems.append(f"family distribution {dict(fams)} != {FAMILIES}")
    if len(TASKS) != 30:
        problems.append(f"task count {len(TASKS)} != 30")
    # instruction positions among focused-revision
    rev = [t for t in TASKS if t["task_family"] == "multi_constraint_focused_revision"]
    pos = Counter(t["diagnostics"]["instruction_position"] for t in rev)
    if dict(pos) != {"early": 4, "middle": 4, "late": 4}:
        problems.append(f"focused-revision instruction positions {dict(pos)} != 4/4/4")
    # focused-revision structural rules
    for t in rev:
        n = len(t["evaluation_ground_truth"]["required_changes"])
        if not (3 <= n <= 5):
            problems.append(f"{t['task_id']}: focused-revision has {n} required changes (need 3-5)")
        if not t["evaluation_ground_truth"]["protected_elements"]:
            problems.append(f"{t['task_id']}: focused-revision needs >=1 protected element")
        if len(t["evaluation_ground_truth"]["forbidden_changes"]) < 2:
            problems.append(f"{t['task_id']}: focused-revision needs >=2 forbidden changes")
    # coverage buckets
    cov = Counter()
    for t in rev:
        for c in t["_coverage"]:
            cov[c] += 1
    for bucket in ("scattered", "protected_exact", "buried", "over_edit_trap"):
        if cov[bucket] < 4:
            problems.append(f"focused-revision coverage '{bucket}' = {cov[bucket]} (< 4)")
    # comprehension probes <= 6
    probes = [t["task_id"] for t in TASKS if t.get("comprehension_probe", {}).get("enabled")]
    if len(probes) > 6:
        problems.append(f"{len(probes)} comprehension probes (> 6): {probes}")
    # revision families define authorized + unaffected scope
    for t in TASKS:
        if t["task_family"] in REVISION_FAMILIES:
            if not t["evaluation_ground_truth"]["authorized_spans"]:
                problems.append(f"{t['task_id']}: revision task missing authorized_spans")
            if not t["evaluation_ground_truth"]["unaffected_spans"]:
                problems.append(f"{t['task_id']}: revision task missing unaffected_spans")
    # leakage separation: compiler_inputs must not carry ground truth
    for t in TASKS:
        ci = json.dumps(t["compiler_inputs"])
        for banned in ("evaluation_ground_truth", "machine_checks", "required_change_checks"):
            if banned in ci:
                problems.append(f"{t['task_id']}: compiler_inputs leaks '{banned}'")
    # grounding: defects real, protected/unaffected present
    for t in TASKS:
        problems += C.ground_task(t)
    # duplicate ids
    ids = [t["task_id"] for t in TASKS]
    if len(ids) != len(set(ids)):
        problems.append("duplicate task ids")
    return problems


def _strip(t):
    t = dict(t)
    t.pop("_coverage", None)
    return t


def build_tasks(write=True):
    problems = _self_check()
    if problems:
        raise SystemExit("TASK BUILD BLOCKED — grounding/structure problems:\n  - " + "\n  - ".join(problems))
    out = [_strip(t) for t in TASKS]
    if write:
        with open(os.path.join(HERE, "task-manifest.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
            for t in out:
                fh.write(json.dumps(t, ensure_ascii=False) + "\n")
        with open(os.path.join(HERE, "task-manifest.yaml"), "w", encoding="utf-8", newline="\n") as fh:
            yaml.safe_dump({"tasks": out}, fh, sort_keys=False, allow_unicode=True)
        for t in out:
            fam_dir = os.path.join(HERE, "tasks", t["task_family"].replace("_", "-"))
            os.makedirs(fam_dir, exist_ok=True)
            with open(os.path.join(fam_dir, t["task_id"] + ".json"), "w", encoding="utf-8", newline="\n") as fh:
                json.dump(t, fh, ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    tasks = build_tasks(write=True)
    fams = Counter(t["task_family"] for t in tasks)
    print(json.dumps({"tasks": len(tasks), "families": dict(fams),
                      "probes": [t["task_id"] for t in tasks if t.get("comprehension_probe", {}).get("enabled")],
                      "grounding": "OK"}, ensure_ascii=False, indent=1))
