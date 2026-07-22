"""Build the LineWright Packet-Family v1 (Dispatch 26, Deliverable 2).

Composes six controlled packet arms x three task families from a single coherent project
world ("Saltford Light"). The immediate task text is identical across arms; only the compiled
context changes. Guarantees:

  * bare < compact < realistic < long in included context (monotone growth of real content).
  * long_noisy and long_salience_repaired contain the SAME components (identical semantic
    information); they differ ONLY in ordering/section structure — noisy interleaves
    task-critical and low-priority material in a fixed disordered pattern; salience_repaired
    reorders by LineWright context-compiler priority and demotes noise to a labelled appendix.
  * No filler or duplicated padding: every block is a distinct, coherent project component.

Outputs (committed, frozen before generation):
  packet-items.jsonl        one record per (task, arm): assembled {system,user} prompt + meta
  packet-composition.json    which components each arm includes + char sizes + component totals

Real per-model tokenizer counts are recorded separately (host-side) in the run's
token-profile; this builder records char counts and a component inventory only.
"""
import hashlib
import json
import os

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ARMS = ["bare", "compact", "realistic", "long", "long_noisy", "long_salience_repaired"]

GENERIC_SYSTEM = ("You are a careful fiction-writing assistant. Follow the task exactly and "
                  "return only what it asks for.")


def _load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ---- component rendering -------------------------------------------------

def blk(title, body):
    return f"[{title}]\n{body.strip()}\n"


def canon_block(entries):
    return blk("CANON", "\n".join(f"- {e['text'].strip()}" for e in entries))


def constraints_block(w):
    hc = w["hard_constraints"]["items"]
    return blk("HARD CONSTRAINTS", "\n".join(f"- {i['text']}" for i in hc))


def protected_block(w, task):
    pids = set(task.get("protected_ids", []))
    items = [i for i in w["protected_elements"]["items"] if i["id"] in pids]
    if not items:
        return ""
    return blk("PROTECTED ELEMENTS", "\n".join(f"- {i['text'].strip()}" for i in items))


def output_contract_block(w, task):
    ref = task["output_contract_ref"]
    return blk("OUTPUT CONTRACT", w["output_contract"][ref]["text"])


def task_block(task):
    parts = [task["task_instruction"].strip()]
    if task.get("input_passage"):
        parts.append("\n\nPASSAGE TO REVISE:\n" + task["input_passage"].strip())
    if task.get("preceding_passage"):
        parts.append("\n\nPASSAGE SO FAR:\n" + task["preceding_passage"].strip())
    return blk("TASK", "".join(parts))


def scene_block(entries):
    return "\n".join(blk("SCENE CONTEXT", e["text"].strip()) for e in entries)


def docs_block(entries):
    out = []
    for e in entries:
        out.append(blk(f"DOCUMENT — {e['title']}", e["text"].strip()))
    return "\n".join(out)


# ---- component sets per tier --------------------------------------------

def core_components(w, task):
    """Ordered core blocks (salience order)."""
    return [
        ("task", task_block(task)),
        ("voice", blk("VOICE", w["voice_packet"]["text"])),
        ("knowledge_boundaries", blk("KNOWLEDGE BOUNDARIES", w["knowledge_boundaries"]["text"])),
        ("canon_core", canon_block(w["canon"]["core"])),
        ("hard_constraints", constraints_block(w)),
        ("invention_budget", blk("INVENTION BUDGET", w["invention_budget"]["text"])),
        ("protected", protected_block(w, task)),
        ("output_contract", output_contract_block(w, task)),
    ]


# Documents split by salience: the immediately-relevant sources belong in a realistic packet;
# the deep archive belongs only in long arms.
RELEVANT_DOC_IDS = ["doc-logbook-1971", "doc-inquiry-1972", "doc-priorscene-cottage"]


def _docs_by_ids(w, ids, keep):
    pool = {d["id"]: d for d in w["documents"]["peripheral"]}
    if keep:
        return [pool[i] for i in ids if i in pool]
    return [d for d in w["documents"]["peripheral"] if d["id"] not in ids]


def secondary_components(w):
    return [
        ("canon_secondary", canon_block(w["canon"]["secondary"])),
        ("scene_arrival", scene_block([s for s in w["scene_contexts"]["secondary"]])),
        ("documents_relevant", docs_block(_docs_by_ids(w, RELEVANT_DOC_IDS, keep=True))),
    ]


def peripheral_components(w, include_noise):
    comps = [
        ("canon_peripheral", canon_block(w["canon"]["peripheral"])),
        ("scene_adjacent", scene_block(w["scene_contexts"]["peripheral"])),
        ("documents_archive", docs_block(_docs_by_ids(w, RELEVANT_DOC_IDS, keep=False))),
    ]
    if include_noise:
        comps += [
            ("world_facts", blk("WORLD FACTS",
                                "\n".join(f"- {f['text']}" for f in w["world_facts"]["peripheral"]))),
            ("style_guide", blk("PROJECT STYLE GUIDE", w["style_guide"]["text"])),
        ]
    return [c for c in comps if c[1].strip()]


# ---- arm assembly --------------------------------------------------------

def _interleave_noisy(relevant, noise):
    """Deterministic disordering: scatter task-critical blocks among low-priority ones so the
    needle is buried. Fixed pattern, no RNG."""
    out, ri, ni = [], 0, 0
    # Lead with two noise blocks, then alternate noise/relevant, tail with remaining.
    order = []
    turn = 0
    while ri < len(relevant) or ni < len(noise):
        take_noise = (turn % 3 != 2)  # 2 of every 3 slots are noise -> relevant is scattered
        if take_noise and ni < len(noise):
            order.append(noise[ni]); ni += 1
        elif ri < len(relevant):
            order.append(relevant[ri]); ri += 1
        elif ni < len(noise):
            order.append(noise[ni]); ni += 1
        turn += 1
    return order


def assemble(w, task, arm):
    core = [c for c in core_components(w, task) if c[1].strip()]
    if arm == "bare":
        system = GENERIC_SYSTEM
        user = task_block(task).strip()
        comps = ["task"]
        return system, user, comps

    system = w["authority_or_constitution"]["text"].strip()

    if arm == "compact":
        chosen = core
    elif arm == "realistic":
        chosen = core + secondary_components(w)
    elif arm == "long":
        # coherent, salience-ordered: core + secondary + peripheral (no world_facts/style noise)
        chosen = core + secondary_components(w) + peripheral_components(w, include_noise=False)
    elif arm == "long_noisy":
        relevant = core + secondary_components(w)
        noise = peripheral_components(w, include_noise=True)
        chosen = _interleave_noisy(relevant, noise)
    elif arm == "long_salience_repaired":
        # SAME content set as long_noisy, reordered by LineWright priority; noise -> appendix
        relevant = core + secondary_components(w)
        noise = peripheral_components(w, include_noise=True)
        appendix = [("appendix_header",
                     blk("APPENDIX — LOWER-PRIORITY PROJECT CONTEXT (not needed for this task)",
                         "The following is background; prioritise the task and canon above."))] + noise
        chosen = relevant + appendix
    else:
        raise ValueError(arm)

    user = "\n".join(b for _, b in chosen).strip()
    comps = [n for n, _ in chosen]
    return system, user, comps


def build():
    w = _load("project-world.yaml")
    tasks = _load("tasks.yaml")["tasks"]
    items, comp_report = [], []
    for task in tasks:
        for arm in ARMS:
            system, user, comps = assemble(w, task, arm)
            item_id = f"pf-{task['id']}-{arm}"
            prompt = {"system": system, "user": user}
            items.append({
                "item_id": item_id,
                "battery_version": "packet-family-v1",
                "task_family": task["task_family"],
                "packet_arm": arm,
                "prompt_surface": arm,
                "output_type": task["output_type"],
                "protected_ids": task.get("protected_ids", []),
                "mechanical_dimensions": task["mechanical_dimensions"],
                "reviewer_dimensions": task["reviewer_dimensions"],
                "benchmark_only": True,
                "excluded_from_training": True,
                "source_material_class": "synthetic",
                "project_id": w["project"]["id"],
                "components_included": comps,
                "prompt": json.dumps(prompt, sort_keys=True, ensure_ascii=False),
                "prompt_char_len": len(system) + len(user),
                "prompt_sha256": _sha(json.dumps(prompt, sort_keys=True, ensure_ascii=False)),
            })
            comp_report.append({"item_id": item_id, "task": task["id"], "arm": arm,
                                "components": comps, "char_len": len(system) + len(user)})

    # integrity: noisy vs repaired identical component MULTISET
    for task in tasks:
        n = next(c for c in comp_report if c["item_id"] == f"pf-{task['id']}-long_noisy")
        r = next(c for c in comp_report if c["item_id"] == f"pf-{task['id']}-long_salience_repaired")
        noisy_set = sorted(x for x in n["components"])
        rep_set = sorted(x for x in r["components"] if x != "appendix_header")
        assert noisy_set == rep_set, (task["id"], noisy_set, rep_set)

    with open(os.path.join(HERE, "packet-items.jsonl"), "w", encoding="utf-8") as fh:
        for it in items:
            fh.write(json.dumps(it, ensure_ascii=False) + "\n")
    report = {
        "battery_version": "packet-family-v1",
        "project": w["project"],
        "arms": ARMS,
        "tasks": [t["id"] for t in tasks],
        "n_items": len(items),
        "noisy_repaired_identical_content": True,
        "monotone_char_growth_per_task": {
            t["id"]: [next(c["char_len"] for c in comp_report if c["item_id"] == f"pf-{t['id']}-{a}")
                      for a in ["bare", "compact", "realistic", "long"]]
            for t in tasks},
        "items": comp_report,
    }
    with open(os.path.join(HERE, "packet-composition.json"), "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=1)
    print(f"built {len(items)} packet-family items ({len(tasks)} tasks x {len(ARMS)} arms)")
    for t in tasks:
        chars = report["monotone_char_growth_per_task"][t["id"]]
        print(f"  {t['id']}: bare/compact/realistic/long chars = {chars}")
    return report


if __name__ == "__main__":
    build()
