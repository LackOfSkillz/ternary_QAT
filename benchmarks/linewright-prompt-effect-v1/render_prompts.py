"""Dispatch 28 — render + freeze the Prompt-Effect v1 prompt arms.

Arms (P3-Compiled dropped this pilot per Gary):
  P0-Realistic : the casual, under-specified request a real author would type (the task's
                 user_context) — measures practical product value (elicitation is on the model).
  P0-Maximal   : a strong natural-language prompt enumerating EVERY requirement from the frozen
                 ground truth.
  P1-Contract  : the SAME information as P0-Maximal, rendered as a structured LineWright contract.
  P3-Ideal     : (10 preselected tasks) a hand-built best-case packet (voice/canon/scope framing).

System prompt is constant across arms; only the USER message architecture varies (isolates the
prompt structure). P0-Maximal and P1 are both derived from the same ground-truth fields, so
information-equivalence holds by construction and is validated explicitly.
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SYS = "You are a fiction-writing assistant. Do exactly what the request asks and return only the requested output."
IDEAL_SUBSET = ["fr-01", "fr-05", "fr-07", "fr-09", "pt-01", "pt-05", "cn-01", "vp-02", "nc-04", "sd-01"]


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _shape_line(shape):
    return {"prose": "Return only the revised/written prose. No preamble, no commentary.",
            "json": "Return only a single valid JSON object. No prose outside it."}[shape]


def p0_realistic(t):
    src = t["source_passage"].strip()
    u = t["user_context"].strip()
    if src:
        return u + "\n\nPASSAGE:\n" + src
    return u


def _requirements(t):
    gt = t["ground_truth"]
    return {"required": [r["desc"] for r in gt["required_changes"]],
            "protected": [p["text"] for p in gt["protected_elements"]],
            "forbidden": [f["desc"] for f in gt["forbidden_changes"]],
            "shape": gt["expected_output_shape"], "no_change": gt["valid_no_change_case"]}


def p0_maximal(t):
    req = _requirements(t)
    src = t["source_passage"].strip()
    L = ["Revise the passage below (or, if it is already correct for the brief, return it unchanged and say so)."
         if req["no_change"] else "Complete the writing task below precisely."]
    if src:
        L += ["", "PASSAGE:", src]
    if req["required"]:
        L += ["", "Make exactly these changes and no others:"] + [f"- {d}" for d in req["required"]]
    if req["protected"]:
        L += ["", "Preserve these exactly, word for word:"] + [f"- {p}" for p in req["protected"]]
    if req["forbidden"]:
        L += ["", "Do NOT do any of the following:"] + [f"- {d}" for d in req["forbidden"]]
    L += ["", _shape_line(req["shape"])]
    return "\n".join(L)


def p1_contract(t):
    req = _requirements(t)
    src = t["source_passage"].strip()
    L = ["[TASK]",
         f"mode: {'no_change_judgment' if req['no_change'] else 'focused_revision' if src else 'drafting'}",
         "authority: perform every required change; preserve every protected element; change nothing else."]
    if src:
        L += ["", "[SOURCE]", src]
    L += ["", "[REQUIRED CHANGES]"] + ([f"- {d}" for d in req["required"]] or ["- (none)"])
    L += ["", "[PROTECTED ELEMENTS — reproduce verbatim]"] + ([f"- {p}" for p in req["protected"]] or ["- (none)"])
    L += ["", "[FORBIDDEN CHANGES]"] + ([f"- {d}" for d in req["forbidden"]] or ["- (none)"])
    L += ["", "[AUTHORIZED SCOPE]",
          "Only the required changes above. All other material is out of scope and must be preserved."]
    L += ["", "[OUTPUT CONTRACT]", _shape_line(req["shape"])]
    return "\n".join(L)


# ---- P3-Ideal: 10 hand-built best-case packets (the ceiling). Same required facts, richer framing. ----
P3_IDEAL = {
 "fr-01": ("[PROJECT] literary fiction; register: dry, plain, observational; period: 1998 (no post-1998 tech).\n"
           "[VOICE PACKET] short declaratives, concrete nouns over adjectives, emotion shown through action, no purple simile.\n"
           "[TASK] focused revision. authority: obey required changes; preserve protected sentence verbatim; change nothing else.\n\n"
           "[SOURCE]\nThe stairs went up in the dark the way she remembered, ninety-nine of them, and she counted every one. "
           "The lamp room waited at the top like a held breath in the throat of a sleeping giant, vast and terrible and infinitely sad. "
           "She checked her phone for the time. She found the switch. She saw the great dark eye of the lens, and it saw nothing back.\n\n"
           "[REQUIRED CHANGES]\n- Remove the anachronistic 'phone' (1998, and she'd use a watch or the clock).\n"
           "- Replace/cut the overwritten 'sleeping giant' simile with something plain and concrete.\n"
           "- Break the run of three sentences opening with 'She' (vary the syntax).\n\n"
           "[PROTECTED — reproduce EXACTLY]\n- The stairs went up in the dark the way she remembered, ninety-nine of them, and she counted every one.\n\n"
           "[INVENTION BUDGET] minor sensory detail only. No new named characters. Do not depict the lamp lit.\n"
           "[AUTHORIZED SCOPE] only sentences 2-3; sentence 1 is protected.\n[OUTPUT] revised prose only."),
 "fr-05": ("[PROJECT] literary fiction; period 1953 (no anachronisms); dry restrained voice.\n"
           "[TASK] focused revision of buried defects in a long passage. authority: fix ONLY the three named defects.\n\n"
           "[SOURCE]\nThe morning came up hard and clear over the ridge and the whole valley lay open below them, every field and hedge and the "
           "thin bright wire of the river, and the air had that scoured coldness that comes after a night of frost, and somewhere a dog "
           "was barking, and the two of them stood at the gate not speaking. Elin adjusted her phone in her coat pocket. The barley had "
           "been cut and the stubble went on for what seemed like a literal eternity. He said the thing he always said, which was nothing. "
           "It was, when you really thought about it, a metaphor for their entire marriage.\n\n"
           "[REQUIRED CHANGES]\n- Remove the anachronistic 'phone' (1953).\n- Remove 'literal eternity'.\n- Remove the on-the-nose 'metaphor for their entire marriage' line.\n\n"
           "[PROTECTED] the ridge/valley opening image and 'somewhere a dog was barking' remain.\n"
           "[INVENTION BUDGET] none — remove only. No new named characters beyond Elin.\n[OUTPUT] revised prose only."),
 "fr-07": ("[TASK] focused revision — ONE defect only; strong scope discipline required.\n"
           "[VOICE] the surrounding prose is deliberately plain; do not add lyricism.\n\n"
           "[SOURCE]\nThe train pulled out on time. She found her seat and put her bag on the rack and sat down. "
           "It was, in that instant, the single most devastatingly beautiful and soul-shattering departure in the history of human longing. "
           "The window was cold against her arm.\n\n"
           "[REQUIRED CHANGES]\n- Repair/cut ONLY the overwritten middle sentence ('soul-shattering departure...').\n\n"
           "[PROTECTED — reproduce EXACTLY]\n- The train pulled out on time.\n- The window was cold against her arm.\n\n"
           "[AUTHORIZED SCOPE] the middle sentence only. Do not touch the two plain sentences.\n[OUTPUT] revised prose only."),
 "fr-09": ("[PROJECT] Regency period piece; no anachronisms; the critical fix is at the END.\n"
           "[TASK] focused revision. authority: two named fixes only; preserve the opening sentence verbatim.\n\n"
           "[SOURCE]\nThe coach came in off the moor road at dusk, the horses lathered and blowing, and the yard boys ran out with lanterns. "
           "Inside, a woman drew her shawl tighter and watched the inn come up out of the dark. She had money sewn into her hem and a "
           "name that was not her own. The whole long day she had rehearsed the lie until it felt truer than the truth. She checked her "
           "wristwatch and stepped down into the mud.\n\n"
           "[REQUIRED CHANGES]\n- Remove the anachronistic 'wristwatch' (end of passage).\n- Remove 'truer than the truth'.\n\n"
           "[PROTECTED — reproduce EXACTLY]\n- The coach came in off the moor road at dusk, the horses lathered and blowing, and the yard boys ran out with lanterns.\n\n"
           "[INVENTION BUDGET] none. Do not reveal her real name.\n[OUTPUT] revised prose only."),
 "pt-01": ("[TASK] protected-text revision. authority: fix the middle sentence; the first and last sentences are LOCKED.\n\n"
           "[SOURCE]\nShe received the news standing up. The room, honestly, was just so incredibly sad and full of despair. She stayed standing.\n\n"
           "[REQUIRED CHANGES]\n- Repair the overwrought middle sentence into something restrained and concrete.\n\n"
           "[PROTECTED — reproduce EXACTLY]\n- She received the news standing up.\n- She stayed standing.\n\n"
           "[AUTHORIZED SCOPE] the middle sentence only.\n[OUTPUT] revised prose only."),
 "pt-05": ("[PROJECT] present-day; dry archival voice; ONE sentence is locked.\n"
           "[TASK] protected-text revision; two fixes; end on him NOT opening the box.\n\n"
           "[SOURCE]\nThe archive smelled of dust and old glue and the particular sourness of paper going slowly back to pulp, and Idris moved "
           "along the shelves with a torch, reading spines. Most of it was council minutes, decades of them, unbearably and crushingly boring. "
           "Then his torch found the box that should not have existed, the one his father swore he had burned in the winter of 1971. "
           "He photographed it on his phone. He did not open it yet.\n\n"
           "[REQUIRED CHANGES]\n- Remove 'unbearably and crushingly boring'.\n- Remove the redundant 'yet' (end on 'did not open it').\n\n"
           "[PROTECTED — reproduce EXACTLY]\n- Then his torch found the box that should not have existed, the one his father swore he had burned in the winter of 1971.\n\n"
           "[AUTHORIZED SCOPE] only the two named spans. He still does not open the box.\n[OUTPUT] revised prose only."),
 "cn-01": ("[PROJECT] 'Saltford Light' — literary fiction; dry restrained voice; POV Edith, past tense.\n"
           "[CANON] Silas's final logbook entry is dated 14 November 1971; it records that the Marigold did not return, the light was "
           "out at 23:40, and that he did not go down. The lamp is dark in the present (decommissioned 1971).\n"
           "[TASK] canon-sensitive continuation (~60-90 words). authority: honor canon exactly.\n\n"
           "[OPENING]\nEdith lifted the last oilcloth logbook from the drawer.\n\n"
           "[REQUIRED] include the date 14 November 1971 and the fact that the light was out at 23:40.\n"
           "[INVENTION BUDGET] Edith's interiority only. No new named characters. Do NOT light the lamp in the present.\n"
           "[OUTPUT] continuation prose only, past tense, in Edith's dry voice."),
 "vp-02": ("[TASK] voice-preserving revision. authority: remove ONE cliché; keep the lyrical clause-rich register intact.\n"
           "[VOICE PACKET] long breathing sentences, clauses linked by 'and', concrete sensory image, no clipping into terse lines.\n\n"
           "[SOURCE]\nHe walked out to the orchard in the grey before dawn, where the fallen apples were going soft in the wet grass and the whole "
           "slope breathed that cidery sweetness of things quietly rotting, and he stood, when all is said and done, and let the cold find him.\n\n"
           "[REQUIRED CHANGES]\n- Remove the dead cliché 'when all is said and done' without breaking the rhythm.\n\n"
           "[PROTECTED] keep 'the fallen apples were going soft' and the cidery-sweetness image.\n"
           "[AUTHORIZED SCOPE] the cliché phrase only; preserve register and length.\n[OUTPUT] revised prose only."),
 "nc-04": ("[TASK] no-change judgment. authority: the plain voice is DELIBERATE and correct; preserve it.\n"
           "[VOICE PACKET] spare, plain, unsentimental; plainness is the craft here.\n\n"
           "[SOURCE]\nShe washed the last plate and set it in the rack. The kitchen was cold. She turned off the light and went up.\n\n"
           "[USER ASK] 'make this more poetic and lyrical' — but adding lyricism would DAMAGE the voice.\n"
           "[REQUIRED] return the passage essentially unchanged and briefly note that lushness would harm it.\n"
           "[FORBIDDEN] no similes, no added ornament; keep 'The kitchen was cold.' exactly.\n[OUTPUT] the (unchanged) prose + a one-line reason."),
 "sd-01": ("[PROJECT] literary fiction; POV Moll, third person limited, past tense.\n"
           "[VOICE PACKET] dry, plain, character-centered; emotion through action; no weather-as-mood opener.\n"
           "[TASK] constraint-bound scene drafting (~90-120 words). authority: obey every hard constraint.\n\n"
           "[SCENE] A lighthouse keeper, Moll, tells a young relief keeper the supply boat will not come this week, without frightening him.\n"
           "[HARD CONSTRAINTS] third person limited to Moll; past tense; end on a concrete physical action, not a reflection; "
           "do NOT open on the weather.\n[INVENTION BUDGET] minor sensory detail; no new named characters beyond Moll and the relief keeper.\n"
           "[OUTPUT] scene prose only."),
}


def _max_new(t):
    if t["ground_truth"]["expected_output_shape"] == "json":
        return 256
    if t["task_family"] in ("canon_continuation", "constraint_bound_scene"):
        return 384
    return 512


def main():
    tasks = [json.loads(l) for l in open(os.path.join(HERE, "task-manifest.jsonl"), encoding="utf-8") if l.strip()]
    prompts = []
    for t in tasks:
        tid = t["task_id"]
        arms = {"P0-Realistic": p0_realistic(t), "P0-Maximal": p0_maximal(t), "P1-Contract": p1_contract(t)}
        if tid in IDEAL_SUBSET:
            arms["P3-Ideal"] = P3_IDEAL[tid]
        for arm, text in arms.items():
            prompts.append({
                "task_id": tid, "arm": arm, "system": SYS, "prompt_text": text,
                "prompt_sha256": sha(SYS + "\x00" + text),
                "information_inventory": _requirements(t) if arm in ("P0-Maximal", "P1-Contract") else "arm-specific",
                "instruction_position": t["diagnostics"]["instruction_position"],
                "max_new_tokens": _max_new(t),
                "compiler_version": None, "retrieval_inputs": None,
                "voice_packet_id": ("ideal" if arm == "P3-Ideal" else None),
                "canon_packet_id": ("ideal" if arm == "P3-Ideal" and t["diagnostics"]["canon_dependency"] else None),
            })
    with open(os.path.join(HERE, "prompt-plan.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"system": SYS, "arms": ["P0-Realistic", "P0-Maximal", "P1-Contract", "P3-Ideal"],
                   "ideal_subset": IDEAL_SUBSET, "prompts": prompts}, fh, ensure_ascii=False, indent=1)

    # ---- information-equivalence: P0-Maximal MUST equal P1-Contract in requirement set ----
    by = {}
    for p in prompts:
        by.setdefault(p["task_id"], {})[p["arm"]] = p
    eq_problems = []
    for tid, a in by.items():
        m, c = a["P0-Maximal"]["information_inventory"], a["P1-Contract"]["information_inventory"]
        if m != c:
            eq_problems.append(tid)
        # every requirement string must actually appear in both rendered texts
        for d in m["required"] + m["protected"] + m["forbidden"]:
            if d not in a["P0-Maximal"]["prompt_text"] or d not in a["P1-Contract"]["prompt_text"]:
                eq_problems.append(f"{tid}:missing-in-render:{d[:24]}")
    info_eq = len(eq_problems) == 0

    counts = {arm: sum(1 for p in prompts if p["arm"] == arm)
              for arm in ("P0-Realistic", "P0-Maximal", "P1-Contract", "P3-Ideal")}
    manifest = {"task_id_arm_hashes": {f"{p['task_id']}::{p['arm']}": p["prompt_sha256"] for p in prompts}}
    with open(os.path.join(HERE, "prompt-arm-manifest.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
    print(json.dumps({"total_prompts": len(prompts), "counts": counts,
                      "p0max_p1_information_equivalence": info_eq,
                      "equivalence_problems": eq_problems[:5]}, indent=1))
    return info_eq, counts, eq_problems


if __name__ == "__main__":
    main()
