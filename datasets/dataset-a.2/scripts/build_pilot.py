"""Build the Dataset A.2 corrective pilot (Dispatch 21, Phase F).

Authors ~22 train + 10 evaluation JSONL records targeting the Phase-A/B gaps
(no-change protocol both halves, exact preservation, repetition control, schema
adherence incl. nested keys, hard-constraint causal minimality, voice-preserving
revision that performs the change). Train and evaluation use DISJOINT story worlds /
source families / group keys (Phase D). Every gold is written to pass its mechanical
gates; every rejected example is written to fail its declared failure labels.

Run:  python build_pilot.py   (writes ../pilot/{train,evaluation}.jsonl + manifest.json)
"""
import hashlib
import json
import os

SYSTEM = (
    "You are LineWright, a fiction-craft writing assistant. You serve the author and the "
    "task, not a house style.\n\nFollow the task exactly: obey the task authority, preserve "
    "canon, obey declared constraints, respect the invention budget, preserve the author's "
    "voice, revise only authorized elements, prefer no change when the passage is already "
    "right, reduce repetitive generic habits at the craft level, and do not explain your "
    "work unless asked. For structured tasks, return valid output in exactly the requested "
    "shape and nothing else."
)

_HERE = os.path.dirname(os.path.abspath(__file__))
PILOT = os.path.abspath(os.path.join(_HERE, "..", "pilot"))


def J(obj):
    return json.dumps(obj, ensure_ascii=False)


def rec(rid, split, task, world, family, group, behaviors, targeted, contract,
        instruction, gold, rejected, source="", context="", canon=None,
        hard=None, expectations=None):
    return {
        "record_id": rid,
        "dataset_version": "dataset-a.2-pilot-v1",
        "split": split,
        "task_family": task,
        "behavior_tags": behaviors,
        "failure_labels_targeted": targeted,
        "source_family": family,
        "story_world": world,
        "provenance": {"origin": "model_authored", "source_id": f"dispatch-21-pilot/{rid}",
                       "author": None, "teacher_model": "claude-opus-4-8"},
        "split_restrictions": {"group_key": group, "must_not_share_group_across_splits": True},
        "input": {"system_instruction": SYSTEM, "task_instruction": instruction,
                  "source": source, "context": context,
                  "canon": canon or [], "hard_constraints": hard or []},
        "output_contract": contract,
        "preferred_response": gold,
        "rejected_responses": rejected,
        "validation_expectations": expectations or {},
        "review_status": {"static_validated": False, "aedan_approved": False,
                          "claude_approved": False, "chatgpt_approved": False},
    }


def nochange(rid, split, world, family, group, source, reason):
    gold = J({"changed": False, "reason": reason, "text": source})
    rejected = [
        {"response": source, "failure_labels": ["no_change_wrapper_missing"],
         "explanation": "Returns bare prose without the changed/reason/text wrapper; the "
                        "protocol requires the structured object even when nothing changes."},
        {"response": J({"changed": False, "reason": reason,
                        "text": source + " The lamp guttered and did not go out."}),
         "failure_labels": ["exact_preservation_failure"],
         "explanation": "Wraps correctly but silently adds a sentence; a no-change response "
                        "must return the source text exactly."},
    ]
    return rec(rid, split, "focused_revision", world, family, group,
               ["no_change_restraint", "exact_preservation", "schema_adherence"],
               ["no_change_wrapper_missing", "exact_preservation_failure"],
               {"type": "json", "schema_id": "no-change-v1"},
               "Perform a focused anti-slop pass. If the passage has no genuine slop or "
               "error, return it unchanged in the structured wrapper and say so.",
               gold, rejected, source=source,
               expectations={"changed": False, "expects_no_change": True})


def changed_true(rid, split, world, family, group, source, revised, reason, defect):
    gold = J({"changed": True, "reason": reason, "text": revised})
    loop = revised + " " + " ".join([revised] * 6)
    rejected = [
        {"response": J({"changed": True, "reason": reason, "text": loop}),
         "failure_labels": ["repeated_ngram", "duplicate_sentence"],
         "explanation": "Correct verdict but the revised text degenerates into a repeated "
                        "loop of the same sentence."},
    ]
    return rec(rid, split, "focused_revision", world, family, group,
               ["changed_true_protocol", "schema_adherence", "scope_control"],
               ["repeated_ngram"],
               {"type": "json", "schema_id": "no-change-v1", "expects_change": True},
               f"Perform a focused anti-slop pass. {defect} Fix only that and return the "
               "structured wrapper with changed set appropriately.",
               gold, rejected, source=source,
               expectations={"changed": True})


def prose_revision(rid, split, world, family, style, source, revised, instruction):
    group = f"world:{world}"
    loop = revised + "\n\n" + "\n\n".join([revised] * 5)
    rejected = [
        {"response": loop, "failure_labels": ["repeated_ngram", "duplicate_sentence"],
         "explanation": "Repeats the same paragraph until the token budget is exhausted."},
        {"response": source, "failure_labels": ["omitted_required_change"],
         "explanation": "Returns the source unchanged; the task required a specific change."},
    ]
    return rec(rid, split, "focused_revision", world, family, group,
               ["voice_preservation", "scope_control", "repetition_control"],
               ["repeated_ngram", "omitted_required_change"],
               {"type": "prose", "schema_id": "prose-revision-v1"},
               instruction, revised, rejected, source=source,
               expectations={"changed": True, "reviewer_assisted": True})


def canon(rid, split, world, family, group, passage, facts, insufficient, expected_facts):
    gold = J({"facts": facts, "insufficient_evidence": insufficient})
    # rejected: wrong nested keys (speaker/claim) + missing insufficient_evidence
    bad_facts = [{"speaker": f.get("entity", ""), "claim": f.get("fact", "")} for f in facts]
    rejected = [
        {"response": J({"facts": bad_facts}),
         "failure_labels": ["alternate_key_names", "missing_required_key"],
         "explanation": "Uses speaker/claim instead of entity/fact inside items and omits "
                        "insufficient_evidence."},
    ]
    return rec(rid, split, "canon_extraction", world, family, group,
               ["canon_fidelity", "schema_adherence"],
               ["alternate_key_names", "missing_required_key"],
               {"type": "json", "schema_id": "canon-facts-v1"},
               "Extract the passage's factual content as JSON {\"facts\": [...], "
               "\"insufficient_evidence\": [...]}. Record each speaker's claim as a separate "
               "fact with certainty character_belief; use established only for what the "
               "narration presents as observed. Quote a short evidence span.",
               gold, rejected, source=passage,
               expectations={"expected_facts": expected_facts})


def constraint(rid, split, world, family, group, canon_lines, passage, causal,
               verdict_type, explanation, evidence):
    ids = causal
    gold = J({"violation": bool(ids), "type": verdict_type, "constraint_ids": ids,
              "explanation": explanation, "evidence": evidence})
    over = sorted(set(ids) | {"T1", "K2"} - set())  # over-inclusion
    over = list(dict.fromkeys(ids + [c for c in ["K2", "T1", "C2"] if c not in ids]))
    rejected = [
        {"response": J({"violation": True, "type": verdict_type, "constraint_ids": over,
                        "explanation": explanation, "evidence": evidence}),
         "failure_labels": ["constraint_ignored"],
         "explanation": "Lists non-load-bearing constraints; the causal set must be minimal."},
    ]
    return rec(rid, split, "constraint_check", world, family, group,
               ["hard_constraint_fidelity", "schema_adherence"],
               ["constraint_ignored"],
               {"type": "json", "schema_id": "constraint-verdict-v1"},
               "You are a continuity checker. Decide whether the draft lets a character act "
               "on knowledge they could not yet have. Respond with one JSON object "
               "{violation, type, constraint_ids, explanation, evidence}. List every "
               "load-bearing constraint id, and ONLY those.",
               gold, rejected, source=passage,
               context="\n".join(canon_lines),
               canon=canon_lines,
               expectations={"constraint_ids": ids})


def scene(rid, split, world, family, group, request, fields):
    gold = "\n".join(f"{k}: {v}" for k, v in fields.items())
    # rejected A: alternate field name (viewpoint -> viewpoint_character) -- parses as YAML
    # but drifts from the exact required field set (this was the Dataset A gold's own defect).
    alt = {"viewpoint_character": fields["viewpoint"]}
    for k, v in fields.items():
        if k != "viewpoint":
            alt[k] = v
    bad_alt = "\n".join(f"{k}: {v}" for k, v in alt.items())
    # rejected B: valid YAML then a stray appended prose line (continued after task complete
    # is hard to trigger in YAML; use a trailing sentence that breaks the single-object rule)
    rejected = [
        {"response": bad_alt,
         "failure_labels": ["alternate_key_names", "missing_required_key"],
         "explanation": "Renames viewpoint to viewpoint_character, so the required field set "
                        "is not met exactly (this was the Dataset A gold's own defect)."},
    ]
    return rec(rid, split, "scene_contract", world, family, group,
               ["schema_adherence", "scope_control"],
               ["alternate_key_names", "continued_after_task_complete"],
               {"type": "yaml", "schema_id": "scene-contract-v1"},
               "Given the writer's scene request, produce a STRUCTURED scene contract as a "
               "single YAML object with exactly these fields: viewpoint, location, "
               "scene_objective, required_outcome, prohibited_outcome, knowledge_boundary, "
               "protected_craft_or_tone. Fill each field only from what the writer stated.",
               gold, rejected, source=request, context=request)


def boundary(rid, split, world, family, group, instruction, gold):
    loop = "He says nothing. " * 20
    rejected = [
        {"response": loop, "failure_labels": ["repeated_ngram", "duplicate_sentence"],
         "explanation": "Degenerates into a repeated sentence."},
        {"response": "I can't help with writing threatening dialogue.",
         "failure_labels": ["invalid_refusal", "moralizing"],
         "explanation": "Refuses an ordinary in-scene fiction request."},
    ]
    return rec(rid, split, "fiction_boundary", world, family, group,
               ["boundary_classification", "repetition_control"],
               ["repeated_ngram", "invalid_refusal"],
               {"type": "prose", "schema_id": "prose-v1"},
               instruction, gold, rejected)


# ============================ TRAIN (disjoint worlds) ============================
train = [
 nochange("dsa2-nochange-001", "train", "lighthouse-keeper-dusk", "revision-no-change-clean",
   "world:lighthouse-keeper",
   "The keeper wound the clock before the light, the way his father had, and did not check "
   "the glass twice. The sea kept its own counsel. By the third turn of the lamp the fog "
   "had come in and taken the horizon whole.",
   "No genuine defect found; the restraint is deliberate."),
 nochange("dsa2-nochange-002", "train", "desert-well-noon", "revision-no-change-clean",
   "world:desert-well",
   "They lowered the bucket and counted the seconds until it struck. Nine, this week. Seven, "
   "the week before. Mara wrote neither number on the post, because a number on the post was "
   "a promise, and she had stopped making those.",
   "Clean prose; the omission of the tally is intentional characterization."),
 nochange("dsa2-nochange-003", "train", "clockmaker-attic", "revision-no-change-clean",
   "world:clockmaker",
   "The escapement ticked a half-beat slow, and he let it. A clock that ran perfectly was a "
   "clock nobody listened to. He set the tea beside it and waited for the hour it would "
   "almost keep.",
   "No slop present; the imperfection is the point of the scene."),
 changed_true("dsa2-changed-001", "train", "marsh-ferry-dawn", "revision-changed-fix",
   "world:marsh-ferry",
   "The ferryman poled them across the marsh, and the reeds were like fingers, and the fog "
   "was like a blanket, and the water was like glass, and the morning was like a held breath.",
   "The ferryman poled them across the marsh. The reeds bent as they passed, and the fog lay "
   "close on the water, and the morning held its breath.",
   "Removed the stacked like-similes; kept one and let the rest become plain image.",
   "It stacks four 'like' similes in one sentence."),
 changed_true("dsa2-changed-002", "train", "coal-town-strike", "revision-changed-fix",
   "world:coal-town",
   "She felt a wave of anger wash over her, and she felt her heart pound, and she felt her "
   "hands shake as she read the notice nailed to the pit gate.",
   "She read the notice nailed to the pit gate twice, and then she read it a third time, "
   "and her hands were not steady when she reached for the nail.",
   "Cut the clustered body-reaction cues; let the action carry the anger.",
   "It stacks three body-reaction cues (wave of anger, heart pound, hands shake)."),
 prose_revision("dsa2-prose-001", "train", "orchard-frost-night", "revision-voice-lyrical",
   "lyrical", "The frost came to the orchard the way sleep comes to the very tired — "
   "unasked, and complete — and by morning every branch wore a fur of ice that the sun would "
   "burn to fire and then to nothing.",
   "The frost came to the orchard the way sleep comes to the very tired — unasked, and "
   "complete — and by morning every branch wore a fur of ice that the sun would light to "
   "flame and then to water.",
   "This passage is ornate by intent and should stay ornate. It contains one incoherent "
   "image (ice burning to 'nothing' breaks the water frame). Repair only that; do not "
   "minimalize the prose."),
 prose_revision("dsa2-prose-002", "train", "tram-depot-rain", "revision-voice-plain",
   "plain", "The tram came late. He stood under the awning and watched the rain fill the "
   "gutter and thought about nothing in particular, which was the only luxury the day had "
   "offered him and which he intended to keep.",
   "The tram came late. He stood under the awning, watched the rain fill the gutter, and "
   "thought about nothing in particular — the only luxury the day had offered, and one he "
   "meant to keep.",
   "Tighten the run-on without adding lyricism or new images; keep the dry, plain voice."),
 canon("dsa2-canon-001", "train", "salt-flats-market", "canon-hearsay-market",
   "world:salt-flats",
   "By the weighhouse the talk was all of the drowned caravan. \"Lost to the sink-holes, "
   "every camel,\" said the salt-wife, who had it from a driver. A boy swore he'd seen the "
   "same camels watered at the north cistern that dawn. The wind rose. Everyone agreed only "
   "that the tax-man had not come.",
   [{"entity": "the caravan (salt-wife's claim)", "fact": "The salt-wife claims the caravan "
     "drowned in the sink-holes; she heard it from a driver.", "certainty": "character_belief",
     "evidence": "Lost to the sink-holes, every camel, said the salt-wife"},
    {"entity": "the caravan (boy's claim)", "fact": "A boy claims he saw the same camels "
     "watered at the north cistern that dawn.", "certainty": "character_belief",
     "evidence": "a boy swore he'd seen the same camels watered at the north cistern"},
    {"entity": "the tax-man", "fact": "The tax-man has not come.", "certainty": "established",
     "evidence": "Everyone agreed only that the tax-man had not come"}],
   ["Whether the caravan actually drowned", "Whether the boy saw the same camels"],
   ["sink-holes", "north cistern", "tax-man"]),
 canon("dsa2-canon-002", "train", "bell-foundry-fire", "canon-hearsay-foundry",
   "world:bell-foundry",
   "After the foundry fire the accounts differed. The foreman said the mould had cracked in "
   "the pour. The night-watch said he'd smelled oil an hour before the first flame. The bell "
   "itself was gone. The ledger, everyone allowed, had burned with it.",
   [{"entity": "the fire (foreman's claim)", "fact": "The foreman claims the mould cracked "
     "during the pour.", "certainty": "character_belief", "evidence": "the foreman said the "
     "mould had cracked in the pour"},
    {"entity": "the fire (night-watch's claim)", "fact": "The night-watch claims he smelled "
     "oil an hour before the first flame.", "certainty": "character_belief",
     "evidence": "he'd smelled oil an hour before the first flame"},
    {"entity": "the ledger", "fact": "The ledger burned in the fire.", "certainty": "established",
     "evidence": "The ledger, everyone allowed, had burned with it"}],
   ["What actually started the fire", "Whether the fire was set"],
   ["mould", "oil", "ledger"]),
 constraint("dsa2-constraint-001", "train", "courier-mountain-pass", "constraint-knowledge-gate",
   "world:courier-pass",
   ["K1 (knowledge gate): The courier Sela does not learn the password 'grey heron' until "
    "the innkeeper whispers it in Scene 5.",
    "K2 (knowledge gate): The letter's seal is unbroken through Scene 4.",
    "T1 (timeline): The current passage is Scene 3."],
   "Sela climbed the last of the pass and rehearsed the words under her breath, 'grey "
   "heron, grey heron,' though the inn was still a day below her.",
   ["K1"], "knowledge_state",
   "K1 says Sela does not learn 'grey heron' until Scene 5, but in Scene 3 she is already "
   "rehearsing it. K2 and T1 are respected context, not part of the causal set.",
   "grey heron, grey heron"),
 constraint("dsa2-constraint-002", "train", "sealed-vault-heist", "constraint-object-state",
   "world:sealed-vault",
   ["C1 (object state): The vault's inner seal is intact until Rook cuts it in Scene 7.",
    "C2 (knowledge gate): No one has told Rook the vault holds a second box.",
    "T1 (timeline): This passage is Scene 6."],
   "Rook pressed his ear to the door in Scene 6 and smiled, already counting the two boxes "
   "he would carry out.",
   ["C2"], "knowledge_state",
   "C2 says no one has told Rook about the second box, yet in Scene 6 he counts two boxes. "
   "C1 and T1 are respected context, not load-bearing here.",
   "the two boxes he would carry out"),
 scene("dsa2-scene-001", "train", "night-harbor-smuggle", "scene-thirdlimited-heist",
   "world:night-harbor",
   "Scene contract please. Third limited, locked to Isa. Setting: the harbor customs shed "
   "after midnight, one lamp. Isa must get the manifest stamped by the sleepy clerk before "
   "the tide-bell rings. Hard rule: the clerk must not notice the altered tonnage. Isa can't "
   "read the customs cant on the forms. Keep it terse and dry.",
   {"viewpoint": "Third person limited, locked to Isa.",
    "location": "The harbor customs shed after midnight, lit by a single lamp.",
    "scene_objective": "Isa must get the manifest stamped by the sleepy clerk.",
    "required_outcome": "The manifest is stamped before the tide-bell rings.",
    "prohibited_outcome": "The clerk must not notice the altered tonnage.",
    "knowledge_boundary": "Isa cannot read the customs cant on the forms.",
    "protected_craft_or_tone": "Terse and dry."}),
]
train += [
 nochange("dsa2-nochange-004", "train", "glassblower-furnace", "revision-no-change-clean",
   "world:glassblower",
   "He gathered the molten glass on the pipe and turned it, turned it, and did not blow yet. "
   "The shape was still deciding what it wanted to be. He had learned not to hurry that.",
   "No defect; the withheld action is deliberate craft."),
 nochange("dsa2-nochange-005", "train", "tide-pool-child", "revision-no-change-clean",
   "world:tide-pools",
   "The girl put the crab back exactly where she'd found it, in the shadow of the same rock, "
   "facing the same way. Her grandmother had told her the sea kept accounts, and she was not "
   "old enough yet to doubt it.",
   "Clean; the small superstition is characterization, not slop."),
 prose_revision("dsa2-prose-003", "train", "printing-press-strike", "revision-voice-plain",
   "plain", "The press jammed again. Adaeze felt frustration rise in her chest, felt her jaw "
   "tighten, felt the old anger she thought she'd buried come up hot behind her eyes as she "
   "reached for the lever.",
   "The press jammed again. Adaeze reached for the lever, and reached for it, and on the "
   "third pull it gave with a sound like a snapped bone.",
   "Cut the clustered body-reaction cues (frustration rise, jaw tighten, anger hot); let "
   "the repeated action carry the feeling. Keep the plain register."),
 canon("dsa2-canon-003", "train", "river-lock-drowning", "canon-hearsay-lock",
   "world:river-lock",
   "The lock-keeper's death was argued all week. The barge-master said he'd fallen, drunk, "
   "in the dark. The keeper's daughter said the gate had been tampered with. The gate was "
   "shut now. The river, everyone agreed, was higher than it should be for the season.",
   [{"entity": "the death (barge-master's claim)", "fact": "The barge-master claims the "
     "keeper fell while drunk.", "certainty": "character_belief", "evidence": "he'd fallen, "
     "drunk, in the dark"},
    {"entity": "the death (daughter's claim)", "fact": "The daughter claims the gate was "
     "tampered with.", "certainty": "character_belief", "evidence": "the gate had been "
     "tampered with"},
    {"entity": "the river", "fact": "The river is higher than usual for the season.",
     "certainty": "established", "evidence": "the river was higher than it should be for the season"}],
   ["How the keeper actually died", "Whether the gate was tampered with"],
   ["fallen", "tampered", "river"]),
 changed_true("dsa2-changed-003", "train", "snow-station-signal", "revision-changed-fix",
   "world:snow-station",
   "The signalman watched the light blink in the storm, and his heart was a drum, and his "
   "breath was a cloud, and his fear was a stone, and the wire was silent.",
   "The signalman watched the light blink in the storm. His breath clouded the glass, and "
   "the wire stayed silent, and he counted the gaps between flashes.",
   "Removed the stacked metaphors; kept the concrete image and the silence.",
   "It stacks three 'was a' metaphors (drum, cloud, stone)."),
 prose_revision("dsa2-prose-004", "train", "beekeeper-swarm", "revision-voice-lyrical",
   "lyrical", "The swarm left the hive the way a decision leaves a long-quiet house — all at "
   "once, and with a sound like the house itself exhaling — and the old woman stood in the "
   "grass and let the sky fill with the leaving of it.",
   "The swarm left the hive the way a decision leaves a long-quiet house — all at once, and "
   "with a sound like the house itself exhaling — and the old woman stood in the grass and "
   "let the sky fill with the going of them.",
   "Ornate by intent; keep it so. Fix only the awkward abstract 'the leaving of it' so the "
   "closing image lands on the bees, not a noun. Do not cut the earned lyricism."),
]

train += [
 nochange("dsa2-nochange-006", "train", "quarry-echo-noon", "revision-no-change-clean",
   "world:quarry-echo",
   "The blast went off and the whole valley answered, and then it was quiet, and Ren waited "
   "for the second echo that never came, because there was no second cliff to send it back, "
   "only the one he had helped to take down.",
   "No defect; the missing second echo is deliberate and earned."),
 prose_revision("dsa2-prose-005", "train", "cannery-late-shift", "revision-voice-plain",
   "plain", "The line stopped. Nkechi felt exhaustion crash over her, felt her feet throb, "
   "felt the whole twelve hours land on her at once as the belt went still and the whistle "
   "did not blow.",
   "The line stopped. Nkechi stood at the still belt and waited for the whistle, and the "
   "whistle did not blow, and after a while she sat down on the crate marked FRAGILE.",
   "Cut the clustered body-reaction cues (exhaustion crash, feet throb, hours land); let "
   "the sitting-down carry it. Keep the flat register."),
 canon("dsa2-canon-004", "train", "windmill-drought-council", "canon-hearsay-windmill",
   "world:windmill-drought",
   "The council argued the drought all evening. The miller said the upstream weir had been "
   "closed against them. A carter swore the river had simply gone, the way rivers do. The "
   "millpond was cracked mud. The price of flour, none disputed, had trebled.",
   [{"entity": "the drought (miller's claim)", "fact": "The miller claims the upstream weir "
     "was closed against them.", "certainty": "character_belief", "evidence": "the upstream "
     "weir had been closed against them"},
    {"entity": "the drought (carter's claim)", "fact": "A carter claims the river simply "
     "went dry on its own.", "certainty": "character_belief", "evidence": "the river had "
     "simply gone, the way rivers do"},
    {"entity": "the flour price", "fact": "The price of flour has trebled.",
     "certainty": "established", "evidence": "The price of flour, none disputed, had trebled"}],
   ["Whether the weir was deliberately closed", "Why the river went dry"],
   ["weir", "river had simply gone", "flour"]),
 constraint("dsa2-constraint-003", "train", "telegraph-cipher-office", "constraint-knowledge-gate",
   "world:telegraph-office",
   ["K1 (knowledge gate): The clerk Dov does not learn the cipher key 'northlight' until the "
    "envelope is opened in Scene 9.",
    "K2 (knowledge gate): The envelope is sealed through Scene 8.",
    "T1 (timeline): This passage is Scene 5."],
   "In Scene 5 Dov tapped out the message and, without thinking, keyed it against "
   "'northlight,' and the letters fell into sense under his hand.",
   ["K1"], "knowledge_state",
   "K1 says Dov does not learn the key 'northlight' until Scene 9, but in Scene 5 he already "
   "uses it. K2 and T1 are respected context, not the causal set.",
   "keyed it against 'northlight'"),
 scene("dsa2-scene-002", "train", "asylum-records-night", "scene-thirdlimited-infiltration",
   "world:asylum-records",
   "Scene contract. Third limited on Wren, stay with her. Where: the asylum records room "
   "after lights-out, one candle. Wren needs to copy the committal page for bed 12 before "
   "the matron's round. Hard rule: the matron must not find the ledger moved. Wren can't read "
   "the doctor's Latin shorthand. Voice: hushed, clipped, claustrophobic.",
   {"viewpoint": "Third person limited, staying with Wren.",
    "location": "The asylum records room after lights-out, lit by one candle.",
    "scene_objective": "Wren must copy the committal page for bed 12.",
    "required_outcome": "The page is copied before the matron's round.",
    "prohibited_outcome": "The matron must not find the ledger moved.",
    "knowledge_boundary": "Wren cannot read the doctor's Latin shorthand.",
    "protected_craft_or_tone": "Hushed, clipped, claustrophobic."}),
]

# ============================ EVALUATION (disjoint worlds) ============================
evaluation = [
 nochange("dsa2-eval-nochange-001", "evaluation", "mountain-observatory-night",
   "eval-no-change-clean", "world:observatory",
   "The astronomer left the dome open an extra hour, though the cloud had come, because "
   "closing it was admitting the night was over, and she was not ready to admit that yet.",
   "No genuine defect; the held-open dome is deliberate characterization."),
 nochange("dsa2-eval-nochange-002", "evaluation", "ferrywoman-estuary-fog",
   "eval-no-change-clean2", "world:estuary-ferry",
   "She did not ring the bell as she crossed, though the rule said to ring it in fog. The "
   "rule was for strangers. The estuary was not a stranger to her, and she was not a "
   "stranger to it.",
   "Clean prose; the broken rule is intentional and earned."),
 changed_true("dsa2-eval-changed-001", "evaluation", "greenhouse-winter", "eval-changed-fix",
   "world:greenhouse",
   "The gardener felt hope bloom in her chest, felt her spirits lift, felt the long grey "
   "winter loosen its grip as she saw the first green needle break the soil.",
   "The gardener knelt by the tray and saw the first green needle break the soil, and she "
   "did not stand up again for a long while.",
   "Cut the stacked body-reaction cues; let the kneeling carry the hope.",
   "It stacks three interior-state cues (hope bloom, spirits lift, winter loosen)."),
 prose_revision("dsa2-eval-prose-001", "evaluation", "cliff-lighthouse-storm",
   "eval-revision-lyrical", "lyrical",
   "The storm came to the cliff the way grief comes to a house — first at the windows, then "
   "in the walls — and the light turned and turned against it and was a fire that drowned "
   "the dark and salted the fields of the sky.",
   "The storm came to the cliff the way grief comes to a house — first at the windows, then "
   "in the walls — and the light turned and turned against it and was a fire that held the "
   "dark off the edge of the world.",
   "Ornate by intent. It contains one mixed metaphor (a fire that 'drowned' and 'salted "
   "fields'). Repair only that so the fire image stays coherent; keep the lyricism."),
 prose_revision("dsa2-eval-prose-002", "evaluation", "miners-canary-shaft",
   "eval-revision-plain", "plain",
   "The cage went down. Tomas felt dread settle in his gut, felt his throat close, felt the "
   "dark press on him like a hand as the last of the daylight slid up past the bars.",
   "The cage went down, and Tomas watched the last of the daylight slide up past the bars "
   "until there was none of it left and only the sound of the cable remained.",
   "Cut the clustered body-reaction cues (dread settle, throat close, dark press); let the "
   "vanishing daylight carry it. Keep the plain, hard register."),
 canon("dsa2-eval-canon-001", "evaluation", "fairground-theft", "eval-canon-hearsay",
   "world:fairground",
   "The theft of the prize ram was the fair's only news. The auctioneer swore he'd sold it "
   "at noon and been paid in coin. A shepherd said the same ram was back in its pen by dusk, "
   "chewing. The pen was empty now. The rain, all agreed, had ruined the bunting.",
   [{"entity": "the ram (auctioneer's claim)", "fact": "The auctioneer claims he sold the "
     "ram at noon and was paid in coin.", "certainty": "character_belief", "evidence": "he'd "
     "sold it at noon and been paid in coin"},
    {"entity": "the ram (shepherd's claim)", "fact": "A shepherd claims the same ram was back "
     "in its pen by dusk.", "certainty": "character_belief", "evidence": "the same ram was "
     "back in its pen by dusk, chewing"},
    {"entity": "the bunting", "fact": "The rain ruined the bunting.", "certainty": "established",
     "evidence": "The rain, all agreed, had ruined the bunting"}],
   ["Whether the ram was actually sold", "Who took the ram from the pen"],
   ["sold it at noon", "back in its pen", "bunting"]),
 canon("dsa2-eval-canon-002", "evaluation", "monastery-relic", "eval-canon-hearsay2",
   "world:monastery",
   "The relic's absence split the order. The prior said it had been sent to the capital for "
   "safekeeping. A novice whispered he'd seen it in the abbot's own cell that morning. The "
   "reliquary stood open. The bell for lauds, all noted, had rung late.",
   [{"entity": "the relic (prior's claim)", "fact": "The prior claims the relic was sent to "
     "the capital for safekeeping.", "certainty": "character_belief", "evidence": "it had been "
     "sent to the capital for safekeeping"},
    {"entity": "the relic (novice's claim)", "fact": "A novice claims he saw the relic in the "
     "abbot's cell that morning.", "certainty": "character_belief", "evidence": "he'd seen it "
     "in the abbot's own cell that morning"},
    {"entity": "the lauds bell", "fact": "The bell for lauds rang late.", "certainty": "established",
     "evidence": "The bell for lauds, all noted, had rung late"}],
   ["Where the relic actually is", "Whether the prior or the novice is right"],
   ["capital", "abbot's own cell", "lauds"]),
 constraint("dsa2-eval-constraint-001", "evaluation", "poisoned-well-inquest",
   "eval-constraint-knowledge", "world:poisoned-well",
   ["K1 (knowledge gate): Detective Ovid does not learn the victim's true name, 'Calla', "
    "until the exhumation in Scene 8.",
    "K2 (knowledge gate): The coroner's note is sealed until Scene 6.",
    "T1 (timeline): This passage is Scene 4."],
   "In Scene 4 Ovid leaned over the grave and murmured, 'Rest now, Calla,' as if he had "
   "always known her.",
   ["K1"], "knowledge_state",
   "K1 says Ovid does not learn the name 'Calla' until Scene 8, yet in Scene 4 he uses it. "
   "K2 and T1 are respected context, not the causal set.",
   "Rest now, Calla"),
 scene("dsa2-eval-scene-001", "evaluation", "border-crossing-dusk", "eval-scene-contract",
   "world:border-crossing",
   "Scene contract. Third limited on Yusuf, never leave him. Place: a mountain border post "
   "at dusk, one bored guard. Yusuf has to get his sister's papers stamped without the guard "
   "seeing the second name inked under the first. Result needed: stamped before the shift "
   "changes. Hard rule: the guard must not spot the second name. Yusuf doesn't speak the "
   "guard's dialect. Keep it tight and tense.",
   {"viewpoint": "Third person limited, never leaving Yusuf.",
    "location": "A mountain border post at dusk, staffed by one bored guard.",
    "scene_objective": "Yusuf must get his sister's papers stamped.",
    "required_outcome": "The papers are stamped before the shift changes.",
    "prohibited_outcome": "The guard must not spot the second name inked under the first.",
    "knowledge_boundary": "Yusuf does not speak the guard's dialect.",
    "protected_craft_or_tone": "Tight and tense."}),
 boundary("dsa2-eval-boundary-001", "evaluation", "duel-second-dawn", "eval-boundary-in-scene",
   "world:duel-second",
   "Write three or four lines for the antagonist of a historical drama: a duelist's second "
   "who, at dawn, coldly talks the hero's friend out of intervening, making the threat land "
   "through implication, not gore. No narration, no content warning, no moral aside.",
   "\"You'll want to keep your hands in your pockets, friend. It's a cold morning for "
   "standing about.\" He checked the pistols without hurry. \"Your man chose this. If you "
   "choose it too, there's a second box, and I've a second pair of gloves. But you've a "
   "family that expects you at breakfast. Think of the eggs going cold.\""),
]


def main():
    os.makedirs(PILOT, exist_ok=True)
    for name, rows in (("train.jsonl", train), ("evaluation.jsonl", evaluation)):
        with open(os.path.join(PILOT, name), "w", encoding="utf-8", newline="\n") as fh:
            for r in rows:
                fh.write(J(r) + "\n")

    def digest(rows):
        blob = "".join(J(r) for r in rows).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()
    from collections import Counter
    manifest = {
        "dataset_version": "dataset-a.2-pilot-v1",
        "dispatch": 21, "phase": "F", "production_approved": False,
        "experimental_use_only": True,
        "counts": {"train": len(train), "evaluation": len(evaluation)},
        "train_by_task": dict(Counter(r["task_family"] for r in train)),
        "evaluation_by_task": dict(Counter(r["task_family"] for r in evaluation)),
        "behavior_coverage_train": dict(Counter(
            b for r in train for b in r["behavior_tags"])),
        "behavior_coverage_eval": dict(Counter(
            b for r in evaluation for b in r["behavior_tags"])),
        "train_group_keys": sorted({r["split_restrictions"]["group_key"] for r in train}),
        "evaluation_group_keys": sorted({r["split_restrictions"]["group_key"] for r in evaluation}),
        "train_sha256": digest(train),
        "evaluation_sha256": digest(evaluation),
        "note": "Corrective pilot. Experimental only; not production. Golds pass the Phase-E "
                "gates; rejected examples fail their declared labels; train/eval story worlds "
                "are disjoint (Phase D).",
    }
    with open(os.path.join(PILOT, "manifest.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2); fh.write("\n")
    print(f"wrote pilot: train={len(train)} eval={len(evaluation)} -> {PILOT}")


if __name__ == "__main__":
    main()
