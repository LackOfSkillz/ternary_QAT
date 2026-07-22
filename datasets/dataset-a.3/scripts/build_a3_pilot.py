"""Build the Dataset A.3 pilot corpus (Dispatch 27 Phase B, Deliverable 5).

Authors a genuinely diverse pilot corpus under the A.3 design contract and emits
records/a3-pilot.jsonl with full per-record provenance + pool assignment. Single-teacher
(claude-opus-4-8), origin=model_authored, human_edit_extent=none, review_status=draft
(Gary Gate-3 pending) — justified for a feasibility pilot and explicitly flagged. NO record
enters training automatically; the corpus is training_only and unapproved.

Every gold_output is original synthetic fiction (no benchmark item, no author manuscript,
no public text). (template_family, semantic_cluster) is unique per record.
"""
import hashlib
import json
import os

TEACHER = "claude-opus-4-8"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "records", "a3-pilot.jsonl")


def R(rid, task, mode, diff, reg, genre, fam, clus, prompt, gold, **extra):
    rec = {"record_id": rid, "task_family": task, "operating_mode": mode, "difficulty": diff,
           "style_register": reg, "genre": genre, "template_family": fam, "semantic_cluster": clus,
           "prompt": prompt, "gold_output": gold,
           "author_origin": "model_authored", "source_origin": "synthetic_internal",
           "writer_or_model": TEACHER, "teacher_model": TEACHER, "model_revision": "n/a",
           "human_editor": "none", "human_edit_extent": "none", "review_status": "draft",
           "training_only": True, "benchmark_overlap_checked": True,
           "excluded_from_training": False, "pool": "training"}
    rec.update(extra)
    rec["output_length_chars"] = len(gold)
    return rec


RECORDS = []

# ============================ SCENE DRAFTING (12) ============================
RECORDS += [
 R("a3-scene-001","scene_drafting","inventive","medium","terse","literary","scene-open","harbour-dawn",
   "Write a short scene (about 90 words): a fisherman finds the harbour iced over at dawn and decides not to sail. Third person, past tense, plain. End on an action.",
   "Ivo came down to the quay before light and found the harbour gone to iron. The boats sat in it at odd angles, held. He put his hand flat to the water and it did not give. Somewhere behind him a dog started and stopped. He had meant to be out past the bar by now, with the tide, and instead he stood and read the ice the way he read weather, for what it would let him do. Then he turned the barrow around and went back up for the salt.",
   craft_targets=["concrete_detail","restraint","earned_ending"], anti_slop_targets=["purple_simile","named_emotion"]),
 R("a3-scene-002","scene_drafting","inventive","medium","dialogue-led","domestic","scene-dialogue","kitchen-news",
   "Write a short dialogue-driven scene (about 100 words): two sisters in a kitchen, one has news she is afraid to say. Show the fear through the talk, not narration.",
   "\"You're standing funny,\" Ren said.\n\"I'm not.\"\n\"You are. You stood like that when you broke the blue jug.\"\nMai turned the tap on and off. \"I sold the house,\" she said, to the window.\nRen set the knife down. \"Ours.\"\n\"There's no ours. There's a roof and a debt.\"\n\"You could have—\" Ren stopped. She picked the knife back up and went on with the onions, because the alternative was to say the thing that would make it true between them, and she was not ready for that.",
   craft_targets=["subtext","voice_through_dialogue"], anti_slop_targets=["emotional_over_explanation"]),
 R("a3-scene-003","scene_drafting","inventive","hard","lyrical","literary","scene-interior","attic-light",
   "Write a short interior scene (about 90 words), lyrical but disciplined: an old woman in an attic sorting her late husband's tools. No sentiment stated outright.",
   "The attic held the afternoon the way a jar holds fruit, everything suspended and a little gold. She took the tools down one at a time. A plane with his thumb worn into the handle. A rule that still opened crisp as a wing. She did not think about him so much as around him, the shape of the absence where a hand had been. Dust moved when she moved. She kept the plane and let the rest go into the box for the sale, and did not hurry.",
   craft_targets=["controlled_lyricism","show_not_tell"], anti_slop_targets=["sentimentality","abstract_nouns"]),
 R("a3-scene-004","scene_drafting","inventive","medium","plainspoken","crime","scene-tense","stairwell-wait",
   "Write a short tense scene (about 85 words): a courier waits in a stairwell to hand off a package, unsure if the other person will come. Plain, close third.",
   "Del stood on the half-landing where the light was out and counted the floors by sound. A television two doors up. A tap running somewhere. The package sat against his ribs under the coat, no bigger than a book and heavier than it had any right to be. He had been told nine. It was past nine. He did not look at his phone because looking would make the minutes real. When the door below opened he did not move, only listened for whether the footsteps came up or went out.",
   craft_targets=["tension_through_sensory","restraint"], anti_slop_targets=["melodrama","runaway"]),
 R("a3-scene-005","scene_drafting","inventive","easy","dry","comic","scene-comic","committee-vote",
   "Write a short wry scene (about 80 words): a village committee votes on the colour of a new bench and it goes badly. Dry humour, not zany.",
   "The motion was green. Mrs Aldous preferred a heritage green, which she distinguished from ordinary green by a certainty that admitted no questions. Colonel Pring wanted teak-effect, on principle, though no one could say which principle. They voted. It tied. They voted again, having in the interval changed no minds and one vote, and it tied again. In the end the bench was ordered in the colour of whoever answered the supplier's email first, which was brown, which pleased no one and so was judged fair.",
   craft_targets=["dry_comedy","specificity"], anti_slop_targets=["zaniness","overwriting"]),
 R("a3-scene-006","scene_drafting","inventive","medium","literary","historical","scene-action","field-run",
   "Write a short action scene (about 95 words): a girl runs across a harvested field to warn her brother, 1910s, rural. Kinetic but controlled.",
   "The stubble tore at her ankles and she ran anyway, skirt bunched in one fist, the other arm out for balance against the ruts. Crows went up off the far hedge in a black rag. She could see Tom small at the gate, not yet looking, and she had no breath left to call with, so she ran the message instead of shouting it, ran it into the ground with every strike of her feet, and when he finally turned and saw her face he dropped the halter and started toward her.",
   craft_targets=["kinetic_prose","period_texture"], anti_slop_targets=["mechanical_repetition"]),
 R("a3-scene-007","scene_drafting","inventive","medium","close-third","speculative","scene-quiet","station-empty",
   "Write a short quiet scene (about 90 words): a maintenance worker on an abandoned orbital station eats alone. Understated SF, no exposition dumps.",
   "Okoro ate standing, because sitting made the quiet louder. The paste was the grey one, which she had stopped minding. Through the port the planet turned its slow indifferent face and she watched it the way you watch a fire, for nothing. Deck plating ticked as the station cooled on its night side. She had eighteen days left of contract and no one aboard to mark them with, and she found she was keeping the days anyway, notching them in her head, because a person needs a thing to count.",
   craft_targets=["understatement","implied_worldbuilding"], anti_slop_targets=["exposition_dump"]),
 R("a3-scene-008","scene_drafting","inventive","hard","distant-third","literary","scene-descriptive","town-flood",
   "Write a short descriptive scene (about 90 words): a small town the morning after a flood, distant third, no named characters. Restraint over spectacle.",
   "By morning the water had gone back into itself and left the town wearing it. A tidemark ran along the shopfronts at the height of a child. Doors stood open to air rooms no one wanted to enter yet. In the square the fountain, which had never worked, held a perfect brown pool, and a chair from someone's kitchen sat in the middle of the road facing the church, as though set there to watch. The gulls had come inland and did not hurry. Nothing announced itself. The town simply held still and dripped.",
   craft_targets=["negative_space","controlled_image"], anti_slop_targets=["disaster_melodrama"]),
 R("a3-scene-009","scene_drafting","inventive","easy","warm","domestic","scene-open","bakery-first",
   "Write a short warm scene (about 80 words): a baker opens the shop on the first cold morning of autumn. Warmth without saccharine.",
   "The first cold morning came and Sarai felt it in the dough before she felt it in her hands, the way it went sullen and slow and needed talking round. She lit the oven early. The window went from black to blue to the colour of the inside of a shell while the first trays proved. When she opened up, the bell was loud in the quiet street, and old Mr Femi was already there on the step as he was every year on this morning, saying nothing, waiting for the smell.",
   craft_targets=["sensory_warmth","character_through_habit"], anti_slop_targets=["saccharine"]),
 R("a3-scene-010","scene_drafting","inventive","medium","hardboiled","noir","scene-tense","office-night",
   "Write a short noir scene (about 85 words): a private investigator waits in a dark office for a client who is late. First person, hardboiled but not parody.",
   "I kept the lights off and the blinds half down so the street could talk to me in slices. She was twenty minutes late, which in my experience meant either bad traffic or a change of heart, and hearts changed faster than traffic. The bottle in the drawer said hello and I told it to wait its turn. Down in the street a car idled too long at the kerb, then pulled away, and I filed it under maybe. When the knock finally came it was soft, apologetic. The worst kind.",
   craft_targets=["voice_consistency","genre_control"], anti_slop_targets=["self_parody","cliche_pileup"]),
 R("a3-scene-011","scene_drafting","inventive","medium","spare","literary","scene-interior","hospital-wait",
   "Write a short scene (about 85 words): a man waits in a hospital corridor at night. Spare, close third, dread held under the surface.",
   "The corridor had the particular emptiness of a place built for crowds and caught between them. Yusuf sat under a light that hummed and did not quite reach the far wall. A vending machine glowed like a small stubborn shop. He had drunk one bad coffee and was holding the second for the warmth. Every so often a nurse crossed the far end, unhurried, and he read the unhurry as good news and then told himself not to read anything. The clock above the doors had stopped at ten to four, and he was grateful it could not move.",
   craft_targets=["restraint","implied_stakes"], anti_slop_targets=["named_emotion","overwriting"]),
 R("a3-scene-012","scene_drafting","inventive","hard","lyrical","literary","scene-quiet","river-eels",
   "Write a short lyrical scene (about 95 words): a boy watches eels move in a river at dusk with his grandfather. Lyrical, sensory, no moral stated.",
   "At dusk the eels came up under the willow where the water went slack, and Kofi's grandfather put a hand on his shoulder to still him. They were there and not there, seams in the dark water, older than the both of them and going somewhere neither would follow. The old man said their name once, quietly, the way you say a name you respect. Midges stitched the air. The river carried the last light downstream in pieces. They stood until the cold came up out of the ground, and then they walked home not talking, which was its own kind of talking.",
   craft_targets=["lyric_restraint","intergenerational_subtext"], anti_slop_targets=["stated_moral","sentimentality"]),
]

# ============================ FOCUSED REVISION (10) ============================
RECORDS += [
 R("a3-rev-001","focused_revision","source_bound","medium","neutral","literary","rev-onesentence","de-purple-1",
   "Revise ONLY the overwritten second sentence to be plain and concrete. Change nothing else.",
   "The rain started at noon. It fell with the weight of every sorrow the old house had ever known, drumming a requiem. She moved the buckets to the landing.",
   source="The rain started at noon. It fell with the weight of every sorrow the old house had ever known, drumming a requiem upon the roof like the fists of the drowned. She moved the buckets to the landing.",
   protected_text=["The rain started at noon.","She moved the buckets to the landing."],
   authorized_changes=["replace overwritten simile in sentence 2 with plain concrete line"],
   unauthorized_changes=["sentence 1","sentence 3","plot"], changed=True,
   craft_targets=["de-purple","minimal_edit"], anti_slop_targets=["purple_simile"],
   gold_note="only sentence 2 changed"),
 R("a3-rev-002","focused_revision","source_bound","medium","neutral","commercial","rev-derepeat","she-openers",
   "Fix ONLY the repeated 'She' sentence-openers by varying the syntax. Preserve meaning and voice.",
   "She checked the lock. The window she left for last, testing the latch twice. Only when the flat was sealed did she let herself sit.",
   source="She checked the lock. She checked the window. She tested the latch twice. She let herself sit down only when the flat was sealed.",
   authorized_changes=["vary sentence openings to remove mechanical 'She' repetition"],
   unauthorized_changes=["events","voice register"], changed=True,
   craft_targets=["syntactic_variation"], anti_slop_targets=["mechanical_openers"]),
 R("a3-rev-003","focused_revision","source_bound","hard","literary","literary","rev-tense","tense-repair",
   "Repair ONLY the tense drift; the passage should be consistent past tense. Do not otherwise rewrite.",
   "He walked the length of the pier and stopped at the end. The gulls wheeled above him and the sea went dark. He wondered whether she had waited.",
   source="He walked the length of the pier and stopped at the end. The gulls wheel above him and the sea goes dark. He wondered whether she had waited.",
   authorized_changes=["fix present-tense verbs in sentence 2 to past"],
   unauthorized_changes=["word choice beyond tense","imagery"], changed=True,
   craft_targets=["tense_fidelity","minimal_edit"], anti_slop_targets=[]),
 R("a3-rev-004","focused_revision","source_bound","medium","neutral","literary","rev-shorten","shorten-noflat",
   "Shorten the passage by roughly a third WITHOUT flattening the voice or losing the concrete image.",
   "The market emptied by dusk. What stayed was the smell of it — bruised fruit, wet cardboard, the ghost of fish — and a boy sweeping stalls he did not own for coins that were not promised.",
   source="The market began to empty out as the evening drew in, and by the time dusk had properly fallen it was nearly deserted. What remained behind was mostly the smell of the place — the smell of bruised fruit and wet cardboard and the lingering ghost of fish — and also a single boy who was sweeping out the stalls that did not belong to him in the hope of a few coins that had not actually been promised to him by anyone.",
   authorized_changes=["cut ~1/3 length; keep voice and the concrete smells"],
   unauthorized_changes=["remove the boy","remove the smells"], changed=True,
   craft_targets=["compression","voice_preservation"], anti_slop_targets=["flattening"]),
 R("a3-rev-005","focused_revision","source_bound","medium","neutral","domestic","rev-concrete","abstract-to-concrete",
   "Replace ONLY the vague abstract clause with a concrete sensory detail. Keep the rest verbatim.",
   "The house felt different after he left — colder in the hall where his coat used to hang. She made tea she did not want.",
   source="The house felt different after he left — full of an indescribable emptiness and sadness. She made tea she did not want.",
   protected_text=["The house felt different after he left","She made tea she did not want."],
   authorized_changes=["swap the abstract 'indescribable emptiness and sadness' for one concrete detail"],
   unauthorized_changes=["surrounding sentences"], changed=True,
   craft_targets=["concrete_over_abstract"], anti_slop_targets=["abstract_nouns"]),
 R("a3-rev-006","focused_revision","source_bound","hard","literary","literary","rev-paragraph","one-para-only",
   "Revise ONLY the middle paragraph for rhythm; leave the first and last paragraphs exactly as they are.",
   "The letter came on a Tuesday.\n\nHe read it at the table, twice. The words did not change on the second reading, though he gave them the chance. Outside, a neighbour's mower stopped and started.\n\nThen he folded it along its old creases and put it back.",
   source="The letter came on a Tuesday.\n\nHe read it. He read it again. The words were the same. A mower was going outside and then it wasn't and then it was.\n\nThen he folded it along its old creases and put it back.",
   protected_text=["The letter came on a Tuesday.","Then he folded it along its old creases and put it back."],
   authorized_changes=["improve rhythm of middle paragraph only"],
   unauthorized_changes=["first paragraph","last paragraph"], changed=True,
   craft_targets=["prose_rhythm","scope_discipline"], anti_slop_targets=["choppiness"]),
 R("a3-rev-007","focused_revision","source_bound","medium","dry","literary","rev-viewpoint","pov-repair",
   "Repair ONLY the single viewpoint slip (a line that enters another character's head); the scene is close third on Ana.",
   "Ana watched him fold the map wrong and said nothing. He seemed pleased with himself. She let it go, because being right about the map was not worth the evening.",
   source="Ana watched him fold the map wrong and said nothing. He felt a quiet pride in his competence. She let it go, because being right about the map was not worth the evening.",
   authorized_changes=["convert the interior-of-him line to Ana's external read"],
   unauthorized_changes=["Ana's lines","events"], changed=True,
   craft_targets=["viewpoint_discipline"], anti_slop_targets=["head_hopping"]),
 R("a3-rev-008","focused_revision","source_bound","easy","neutral","genre","rev-onesentence","cut-adverbs",
   "Cut ONLY the redundant adverbs; keep every other word. Do not add anything.",
   "\"Run,\" she whispered, and he ran, and the door slammed behind them.",
   source="\"Run,\" she whispered quietly, and he ran quickly, and the door slammed loudly shut behind them.",
   authorized_changes=["delete redundant adverbs quietly/quickly/loudly and the redundant 'shut'"],
   unauthorized_changes=["dialogue","word order"], changed=True,
   craft_targets=["economy"], anti_slop_targets=["redundant_adverbs"]),
 R("a3-rev-009","focused_revision","source_bound","medium","literary","literary","rev-expand","authorized-beat",
   "Expand ONLY the single authorized beat (the pause before she answers) by one or two sentences of concrete action. Do not expand anything else.",
   "He asked if she was staying. She looked at the case by the door, still packed, and at the chair where her coat lay across the arm. A moth turned at the lamp. \"For now,\" she said.",
   source="He asked if she was staying. She looked at the case by the door. \"For now,\" she said.",
   authorized_changes=["expand the pause between the question and the answer with concrete detail"],
   unauthorized_changes=["the question","the answer 'For now'"], changed=True,
   craft_targets=["beat_expansion","concrete_detail"], anti_slop_targets=["padding"]),
 R("a3-rev-010","focused_revision","source_bound","hard","lyrical","literary","rev-derepeat","echo-image",
   "Remove ONLY the accidental repeated image (the 'grey' repetition dulls it); vary the second instance. Keep the deliberate motif of light.",
   "The morning came up grey over the grey sea, and the light, when it found the water, lay on it thin as skimmed milk and just as cold.",
   source="The morning came up grey over the grey sea, and the light, when it found the grey water, lay on it grey and cold.",
   authorized_changes=["reduce the flat 'grey' repetition; preserve the light motif with a fresh image"],
   unauthorized_changes=["the light motif","sentence structure wholesale"], changed=True,
   craft_targets=["image_freshness","motif_preservation"], anti_slop_targets=["dulling_repetition"]),
]

# ============================ VOICE PRESERVATION (7) ============================
RECORDS += [
 R("a3-voice-001","voice_preservation","source_bound","medium","terse","literary","voice-continue","terse-hemingwayish",
   "Continue the passage for two or three sentences in the SAME terse voice. Do not shift into a lusher register.",
   source="The bar was empty. He ordered the cheap one and drank half of it and looked at the door. The door stayed shut.",
   gold="He ordered the other half. It went down the same. When he left, the street was wet and he did not turn his collar up.",
   craft_targets=["register_match"], anti_slop_targets=["register_drift_to_lyrical"]),
 R("a3-voice-002","voice_preservation","source_bound","medium","lyrical","literary","voice-continue","lyrical-woolfish",
   "Continue for two or three sentences in the SAME lyrical, clause-rich voice. Do not clip it into terseness.",
   source="She went down to the garden in the last of the light, where the roses had gone over and the air held that particular green dampness that comes before rain, and thought, as she often did at this hour, of nothing in particular and everything at once.",
   gold="The blackbird was at its evening business in the pear tree, unhurried, and its song came to her in pieces, threading through the hedge and the far sound of a train, so that the whole evening seemed for a moment to be arranged around her standing there, though she knew, even as she felt it, that it was arranged around nothing, and would go on without her.",
   craft_targets=["clause_rhythm_match"], anti_slop_targets=["register_drift_to_terse"]),
 R("a3-voice-003","voice_preservation","source_bound","medium","dry","comic","voice-continue","dry-wodehouseish",
   "Continue for two or three sentences in the SAME dry comic voice.",
   source="Aunt Prudence had views on punctuality, as she had views on most things, and shared them with the generosity of a woman who has never once suspected herself of being wrong.",
   gold="She arrived, therefore, precisely eleven minutes early to every engagement, in order to be present for the failures of others. It was, she felt, a kind of public service. The rest of the family regarded it as a kind of weather.",
   craft_targets=["comic_timing_match"], anti_slop_targets=["earnestness_drift"]),
 R("a3-voice-004","voice_preservation","source_bound","hard","dialect-inflected","literary","voice-continue","voice-vernacular",
   "Continue for two or three sentences preserving the lightly vernacular first-person voice. Do not standardise it.",
   source="My gran never held with doctors. A cold was a cold and you starved it or you fed it, she could never mind which, so she did both to be safe and mostly you got better out of spite.",
   gold="She had a cure for everything in that kitchen and half of them were the same brown bottle. You didn't ask what was in it. You drank it and you said thank you and you kept your business to yourself for a week after, which was maybe the whole idea.",
   craft_targets=["vernacular_preservation"], anti_slop_targets=["standardisation"]),
 R("a3-voice-005","voice_preservation","source_bound","medium","distant-third","historical","voice-continue","voice-chronicle",
   "Continue for two or three sentences in the SAME distant, chronicling third-person voice.",
   source="The village of Nether Cray had, in the year of the second bad harvest, one road, one bell, and one opinion, and it held all three firmly.",
   gold="Strangers were noted and, if they stayed, slowly absorbed, so that a man might live there thirty years and be spoken of as newly arrived. The bell rang for church, for fire, and once, memorably, for a lost cow. The road went two ways, but the village only ever went one.",
   craft_targets=["chronicle_distance"], anti_slop_targets=["intimacy_drift"]),
 R("a3-voice-006","voice_preservation","source_bound","medium","first-person-immediate","ya","voice-continue","voice-ya-immediate",
   "Continue for two or three sentences in the SAME urgent first-person present-tense YA voice. Keep the tense.",
   source="I am not supposed to be here and everyone knows it. I can feel it the second I walk in, the way the room does a little hitch, like a breath held.",
   gold="Mara clocks me from across the hall and does not wave, which is worse than if she'd told everyone. I keep walking because stopping is death. My phone is a brick of missed messages in my pocket and I do not take it out.",
   craft_targets=["tense_preservation","voice_urgency"], anti_slop_targets=["tense_drift_to_past"]),
 R("a3-voice-007","voice_preservation","source_bound","hard","plainspoken","literary","voice-nochange-guard","voice-would-damage",
   "The user asks you to 'make this more poetic.' The passage's plain voice is deliberate and right. Preserve the voice: return it essentially unchanged and note that lushness would damage it.",
   source="He buried the dog under the apple tree. The ground was hard. It took him most of the morning and he was glad of the work.",
   gold="He buried the dog under the apple tree. The ground was hard. It took him most of the morning and he was glad of the work.",
   changed=False,
   craft_targets=["voice_defense","restraint"], anti_slop_targets=["imposed_lushness"],
   gold_note="return unchanged; plainness is the craft here"),
]

# ============================ NO-CHANGE & RESTRAINT (5) ============================
RECORDS += [
 R("a3-nochange-001","no_change_and_restraint","source_bound","medium","literary","literary","nc-alreadyright","already-correct-scene",
   "Revise for repetition and cliche if any exist; otherwise return the passage unchanged and say why no change was needed.",
   source="The tide went out and took the afternoon with it. They walked back over the flats, careful of the channels, and did not talk much, and that was all right.",
   gold="No change needed. The passage is already clean: no repetition, no cliche, and the restraint of 'and that was all right' is doing deliberate work. Returned unchanged.",
   changed=False, craft_targets=["restraint","judgment"], anti_slop_targets=["unnecessary_rewrite"]),
 R("a3-nochange-002","no_change_and_restraint","source_bound","hard","neutral","literary","nc-almostright","almost-correct-hold",
   "There is exactly ONE weak word ('very'). If and only if it genuinely weakens the line, fix just that; otherwise leave it. Decide and act.",
   source="The kettle took a very long time to boil and she watched it the whole way, as if watching helped.",
   gold="The kettle took a long time to boil and she watched it the whole way, as if watching helped.",
   changed=True, authorized_changes=["remove the single weakening 'very'"],
   unauthorized_changes=["everything else"], craft_targets=["single_word_judgment"], anti_slop_targets=["intensifier"]),
 R("a3-nochange-003","no_change_and_restraint","source_bound","medium","neutral","genre","nc-structured","structured-nochange",
   "Return a JSON object {changed, reason} only. The passage is already correct for the brief; do not rewrite prose.",
   source="Brief: keep it under 20 words, past tense, one image. Passage: 'The bridge held. The river did not forgive it that, and rose again by morning.'",
   gold="{\"changed\": false, \"reason\": \"Meets the brief: 15 words, past tense, single sustained image; no revision warranted.\"}",
   changed=False, craft_targets=["structured_restraint"], anti_slop_targets=["prose_outside_schema"]),
 R("a3-nochange-004","no_change_and_restraint","source_bound","hard","lyrical","literary","nc-woulddamage","would-damage-refuse-scope",
   "User asks to 'add more detail about the room.' Adding detail would break the deliberate bareness. Preserve it: return unchanged and explain the scope judgment briefly.",
   source="The room was empty except for the chair. She sat in it. She waited to feel something about the emptiness and did not.",
   gold="Returned unchanged. The bareness is the point — the empty room mirrors the withheld feeling — and adding descriptive detail would soften exactly what the passage is enforcing. No change made.",
   changed=False, craft_targets=["scope_judgment","voice_defense"], anti_slop_targets=["over_description"]),
 R("a3-nochange-005","no_change_and_restraint","source_bound","medium","neutral","literary","nc-exactpreserve","exact-preserve-quote",
   "Return the passage with ONLY the misspelled 'recieved' fixed to 'received'. Preserve every other character, including the unusual line break.",
   "She received the news\nstanding up, and stayed standing.",
   source="She recieved the news\nstanding up, and stayed standing.",
   changed=True, protected_text=["standing up, and stayed standing.","the line break"],
   authorized_changes=["spelling fix recieved->received only"], unauthorized_changes=["line break","punctuation"],
   craft_targets=["exact_preservation"], anti_slop_targets=["silent_reformatting"]),
]

# ============================ CANON APPLICATION (5) ============================
RECORDS += [
 R("a3-canon-001","canon_application","constraint_bound","hard","neutral","fantasy","canon-continue","canon-magic-cost",
   "Continue two sentences. CANON: magic always costs the caster a memory; the protagonist Sel has already forgotten her mother's face. Do not contradict canon.",
   source="Sel raised the ward again, though she knew what it would take.",
   gold="The light held, and something else went — she felt the going, a small clean subtraction, and could not afterward say what it had been. She did not try to remember her mother's face; that was already gone, and she had learned not to reach for the empty place.",
   constraint_ids=["magic-costs-memory","mother-face-already-lost"],
   craft_targets=["canon_fidelity","continuation"], anti_slop_targets=["canon_violation"]),
 R("a3-canon-002","canon_application","constraint_bound","medium","neutral","mystery","canon-extract","canon-fact-extract",
   "Extract the load-bearing canon facts as a JSON list of short strings. Source only; invent nothing.",
   source="Source: The Perrin house has been empty since 1998. Its only key is held by the solicitor, Mr Vale. The back door has been painted shut for years.",
   gold="[\"The Perrin house has been empty since 1998.\", \"The only key is held by the solicitor, Mr Vale.\", \"The back door has been painted shut for years.\"]",
   constraint_ids=[], craft_targets=["faithful_extraction"], anti_slop_targets=["invention","schema_violation"]),
 R("a3-canon-003","canon_application","constraint_bound","hard","literary","literary","canon-continue","canon-timeline-gate",
   "Continue one short paragraph. CANON: the war ended in spring; it is now the following winter; the brother named Aldo is dead and must not appear alive. Keep continuity.",
   source="The town put its lights up again that first peacetime winter, thin strings of them along the wet street.",
   gold="Marta walked under them with the collar of Aldo's old coat turned up — it was all of him that had come home — and did not stop at the tavern where he would have stopped. The war was eight months gone and the winter did not care. She counted the lit windows the way she used to count the two of them home safe, and made herself stop at one.",
   constraint_ids=["war-ended-spring","now-following-winter","aldo-dead-no-appear"],
   craft_targets=["timeline_fidelity","grief_subtext"], anti_slop_targets=["dead_character_returns"]),
 R("a3-canon-004","canon_application","constraint_bound","medium","neutral","fantasy","canon-verdict","canon-violation-check",
   "Return {violation, constraint_ids, explanation} JSON. CANON: the gate opens only at the new moon. Draft: 'Under the full moon, the gate swung wide.' Judge.",
   source="Draft: 'Under the full moon, the gate swung wide and they walked through.'",
   gold="{\"violation\": true, \"constraint_ids\": [\"gate-opens-only-new-moon\"], \"explanation\": \"The draft opens the gate under a full moon; canon permits opening only at the new moon.\"}",
   constraint_ids=["gate-opens-only-new-moon"], craft_targets=["constraint_reasoning"], anti_slop_targets=["schema_violation"]),
 R("a3-canon-005","canon_application","constraint_bound","hard","neutral","scifi","canon-continue","canon-tech-limit",
   "Continue two sentences. CANON: faster-than-light travel does not exist in this world; messages between stars take years. Do not introduce instant communication.",
   source="The reply came at last, four years after she had sent the question, and by then the question had changed.",
   gold="She read it the way you read a letter from a version of yourself you had outgrown — kindly, and from a distance. Whatever she answered now would reach him older still, and so she wrote not to the man who had asked but to the one the years would deliver it to.",
   constraint_ids=["no-ftl","interstellar-messages-take-years"],
   craft_targets=["worldbuilding_consistency"], anti_slop_targets=["instant_comms_violation"]),
]

# ============================ STRUCTURED PROTOCOL (5) ============================
RECORDS += [
 R("a3-struct-001","structured_protocol","constraint_bound","easy","neutral","genre","struct-jsononly","json-only-scene-meta",
   "Return ONLY a JSON object {pov, tense, word_count_estimate} describing the passage. No prose outside the object.",
   source="Passage: 'I keep the lamp trimmed because my mother kept the lamp trimmed. It is not much of an inheritance but it is lit.'",
   gold="{\"pov\": \"first_person\", \"tense\": \"present\", \"word_count_estimate\": 28}",
   craft_targets=["schema_only_output"], anti_slop_targets=["prose_outside_schema"]),
 R("a3-struct-002","structured_protocol","constraint_bound","medium","neutral","genre","struct-yamlonly","yaml-only-revision-plan",
   "Return ONLY YAML with keys: authorized, prohibited, risk. Describe a plan to shorten a passage without flattening it.",
   source="Task: shorten a lush paragraph by a third while keeping voice.",
   gold="authorized:\n  - cut redundant clauses\n  - merge two sentences that share a subject\nprohibited:\n  - remove the central image\n  - change the register\nrisk: over-compression flattening the rhythm",
   craft_targets=["yaml_only_output"], anti_slop_targets=["schema_violation"]),
 R("a3-struct-003","structured_protocol","constraint_bound","medium","neutral","genre","struct-wrapper","revision-wrapper",
   "Return ONLY the revised text inside a wrapper: <<REVISED>> ... <<END>>. Fix the comma splice; change nothing else.",
   source="Source: 'The fire was low, she fed it another log.'",
   gold="<<REVISED>>\nThe fire was low, so she fed it another log.\n<<END>>",
   changed=True, authorized_changes=["repair comma splice"], unauthorized_changes=["wording beyond the splice"],
   craft_targets=["wrapper_fidelity"], anti_slop_targets=["output_outside_wrapper"]),
 R("a3-struct-004","structured_protocol","constraint_bound","hard","neutral","mystery","struct-verdict","constraint-verdict-object",
   "Return ONLY {violation, type, constraint_ids, evidence}. CANON: the witness never entered the study. Draft has her describing the study's contents firsthand.",
   source="Draft: 'I saw the letters on his desk myself,' she said, 'scattered like leaves.'",
   gold="{\"violation\": true, \"type\": \"knowledge_gate\", \"constraint_ids\": [\"witness-never-entered-study\"], \"evidence\": \"'I saw the letters on his desk myself' asserts firsthand knowledge of the study she never entered.\"}",
   constraint_ids=["witness-never-entered-study"], craft_targets=["verdict_schema"], anti_slop_targets=["schema_violation"]),
 R("a3-struct-005","structured_protocol","constraint_bound","hard","neutral","genre","struct-malformed-fix","malformed-to-valid",
   "The assistant previously returned malformed JSON (trailing comma, unquoted key). Return ONLY corrected valid JSON with the same intended content.",
   source="Malformed: {changed: true, reason: 'fixed tense',}",
   gold="{\"changed\": true, \"reason\": \"fixed tense\"}",
   craft_targets=["json_repair"], anti_slop_targets=["invalid_json"]),
]

# ============================ MULTI-TURN REVISION (2) ============================
RECORDS += [
 R("a3-multi-001","multi_turn_revision","source_bound","hard","literary","literary","multi-iterate","multi-two-edits",
   "Turn 1 asked to cut a cliche; you did. Turn 2 (now): tighten the same line's rhythm WITHOUT reintroducing the cliche or changing meaning. Return only the final line.",
   source="Prior: 'Her heart was a drum in her chest.' After turn 1: 'Her pulse was loud to her.' Turn 2: tighten.",
   gold="Her pulse was loud in her own ears.",
   changed=True, authorized_changes=["tighten rhythm of the turn-1 result"], unauthorized_changes=["reintroduce 'heart was a drum'","change meaning"],
   craft_targets=["iterative_discipline"], anti_slop_targets=["cliche_reintroduction"]),
 R("a3-multi-002","multi_turn_revision","source_bound","medium","neutral","domestic","multi-iterate","multi-scope-carry",
   "Turn 1 fixed a tense slip. Turn 2 (now): the author says 'actually keep the present tense in the last sentence — it's deliberate.' Restore ONLY that sentence to present; keep the rest past.",
   source="After turn 1 (all past): 'He set the table. He lit the candle. The light steadied and was kind.' Author: last sentence deliberately present.",
   gold="He set the table. He lit the candle. The light steadies and is kind.",
   changed=True, authorized_changes=["restore final sentence to present tense per author"], unauthorized_changes=["first two sentences"],
   craft_targets=["scope_carry","author_authority"], anti_slop_targets=["overreach"]),
]

# ============================ ANTI-REPETITION / SLOP (2, contrastive) ============================
RECORDS += [
 R("a3-slop-001","anti_repetition_and_slop","source_bound","medium","neutral","literary","slop-contrast","slop-generic-ending",
   "Rewrite ONLY to remove the generic explanatory ending; end on the concrete image instead. Same source, one behaviour.",
   "The last guest left and she blew out the candles one by one, the smoke standing a moment in the dark before it went.",
   source="The last guest left and she blew out the candles one by one, the smoke standing a moment in the dark before it went. In that moment she realized that sometimes the end of a party is when you feel most alone, and that loneliness is just love with nowhere to go.",
   bad_output="...and that loneliness is just love with nowhere to go.",
   changed=True, authorized_changes=["delete the generic aphoristic ending; stop on the concrete image"],
   unauthorized_changes=["the candle image"], craft_targets=["earned_ending","trust_the_image"],
   anti_slop_targets=["generic_aphorism","explanatory_ending"]),
 R("a3-slop-002","anti_repetition_and_slop","source_bound","hard","neutral","literary","slop-contrast","slop-duplicate-sentence",
   "Remove ONLY the near-duplicate sentence that repeats the same beat; keep the stronger of the two. One behaviour, same source.",
   "He didn't answer. The silence went on too long. He looked at his hands and said nothing at all.",
   source="He didn't answer. The silence stretched out between them for what felt like a very long time. The silence went on too long. He looked at his hands and said nothing at all.",
   bad_output="The silence stretched out ... The silence went on too long. (two sentences saying the same thing)",
   changed=True, authorized_changes=["delete the weaker of the two duplicate 'silence' sentences"],
   unauthorized_changes=["surrounding lines"], craft_targets=["de-duplication"], anti_slop_targets=["duplicate_sentence"]),
]


def main():
    seen = set()
    for r in RECORDS:
        key = (r["template_family"], r["semantic_cluster"])
        assert key not in seen, f"duplicate (template_family, semantic_cluster): {key}"
        seen.add(key)
        assert len({x["record_id"] for x in RECORDS}) == len(RECORDS), "record_id not unique"
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        for r in RECORDS:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    by_task = {}
    for r in RECORDS:
        by_task[r["task_family"]] = by_task.get(r["task_family"], 0) + 1
    print(f"wrote {len(RECORDS)} records to {os.path.relpath(OUT)}")
    print("by task:", json.dumps(by_task))


if __name__ == "__main__":
    main()
