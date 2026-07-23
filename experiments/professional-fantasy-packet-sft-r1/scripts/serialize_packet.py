"""Dispatch 30A-R1 — serialize a training packet into the model-visible user message (the exact form
the model receives). Generic renderer; contains no source content. Paired with the frozen system
prompt (freeze/system-prompt.txt) it defines the input the tokenizer measures.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
EXP = os.path.dirname(HERE)
SYSTEM = open(os.path.join(EXP, "freeze", "system-prompt.txt"), encoding="utf-8").read().strip()


def _lines(label, items):
    if not items:
        return []
    return [f"{label}:"] + [f"- {x}" for x in items]


def render_user(tp):
    p = ["Scene packet:",
         f"Viewpoint: {tp.get('viewpoint','')}",
         f"Tense: {tp.get('tense','')}",
         f"Purpose: {tp.get('scene_purpose','')}",
         f"Opening state: {tp.get('opening_state','')}"]
    p += _lines("Required beats", tp.get("required_beats", []))
    p += _lines("Canon", tp.get("canon_facts", []))
    p += _lines("Character goals", tp.get("character_goals", []))
    p += _lines("Knowledge limits", tp.get("knowledge_limits", []))
    p += _lines("Do not", tp.get("forbidden_developments", []))
    p.append(f"Scene boundary: {tp.get('scene_boundary','')}")
    p.append(f"Ending state: {tp.get('ending_state','')}")
    craft = tp.get("craft_profile") or {}
    if craft:
        p.append("Craft profile: " + "; ".join(f"{k}={v}" for k, v in craft.items()))
    p.append("Write the complete scene as prose.")
    return "\n".join(p)


if __name__ == "__main__":
    import sys
    tp = json.load(open(sys.argv[1], encoding="utf-8"))
    print(render_user(tp))
