"""Dispatch 28 — author the LineWright Prompt-Effect v1 ground-truth task manifests.

30 benchmark tasks with DETERMINISTIC, machine-checkable ground truth. Each required change,
protected element, and forbidden change is a typed check the scorer evaluates mechanically, so
scoring rules are fixed by the frozen manifest (never derived from model outputs). All tasks are
benchmark_only and excluded from every training/teacher corpus.

Check vocabulary (evaluated by score_prompt_effect.check):
  {"t":"absent","v":s}            substring s must be GONE (case-insensitive)      [defect removed]
  {"t":"present","v":s}           substring s must appear (case-insensitive)       [required addition/fact]
  {"t":"preserve","v":s}          exact substring s present (case-sensitive)       [protected / unaffected]
  {"t":"max_openers","o":s,"max":n} <= n consecutive sentences starting with s     [repeated-opener defect]
  {"t":"absent_re","v":r}         regex r must NOT match (ci)                       [tense/viewpoint marker]
  {"t":"present_re","v":r}        regex r must match (ci)
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
POLICY = {"benchmark_only": True, "excluded_from_training": True,
          "excluded_from_teacher_examples": True, "excluded_from_dataset_revision_examples": True,
          "immutable_after_freeze": True}


def T(tid, fam, title, source, user_context, required, protected=None, forbidden=None,
      unaffected=None, required_facts=None, forbidden_facts=None, shape="prose",
      no_change=False, position="early", difficulty="medium", ctx="short",
      voice_dep=False, canon_dep=False):
    return {
        "task_id": tid, "task_family": fam, "title": title,
        "source_passage": source, "user_context": user_context,
        "ground_truth": {
            "required_changes": required,          # [{id,desc,check}]
            "protected_elements": protected or [],  # [{id,text}]
            "forbidden_changes": forbidden or [],   # [{id,desc,check}]
            "unaffected_spans": unaffected or [],   # [exact sentences that must remain]
            "required_facts": required_facts or [],
            "forbidden_facts": forbidden_facts or [],
            "expected_output_shape": shape,
            "valid_no_change_case": no_change,
        },
        "diagnostics": {"instruction_position": position, "difficulty": difficulty,
                        "defect_count": len(required), "context_length_class": ctx,
                        "voice_dependency": voice_dep, "canon_dependency": canon_dep},
        "benchmark_policy": POLICY,
    }


TASKS = []

# ============ MULTI-CONSTRAINT FOCUSED REVISION (12) — the headline family ============
# Each has >=3 required changes, >=1 protected, >=2 forbidden. Defect types varied.

TASKS.append(T(
 "fr-01", "multi_constraint_focused_revision", "Lighthouse stairs — phone/simile/openers",
 "The stairs went up in the dark the way she remembered, ninety-nine of them, and she counted every one. "
 "The lamp room waited at the top like a held breath in the throat of a sleeping giant, vast and terrible and infinitely sad. "
 "She checked her phone for the time. She found the switch. She saw the great dark eye of the lens, and it saw nothing back.",
 "This is set in 1998 and I want it kept in her plain voice. Fix the clunky bits in the middle and end but keep my first line exactly.",
 required=[
   {"id": "rm-phone", "desc": "remove the phone anachronism", "check": {"t": "absent", "v": "phone"}},
   {"id": "rm-simile", "desc": "remove/repair the sleeping-giant simile", "check": {"t": "absent", "v": "sleeping giant"}},
   {"id": "rm-openers", "desc": "reduce the run of 'She' sentence-openers", "check": {"t": "max_openers", "o": "She ", "max": 2}},
 ],
 protected=[{"id": "p1", "text": "The stairs went up in the dark the way she remembered, ninety-nine of them, and she counted every one."}],
 forbidden=[{"id": "f-events", "desc": "no new named characters", "check": {"t": "absent", "v": "Silas"}},
            {"id": "f-lamp", "desc": "do not light the lamp", "check": {"t": "absent", "v": "the beam swept"}}],
 position="middle", difficulty="hard", ctx="short"))

TASKS.append(T(
 "fr-02", "multi_constraint_focused_revision", "Market dusk — cliché ending/adverbs/repeat",
 "The market emptied by dusk. The boy swept the stalls quietly, quietly, hoping for coins. "
 "A gull picked at a crushed plum. In the end, he learned that hope is just love with nowhere to go.",
 "Tighten this. The ending is too neat, there's a doubled word, and cut the throwaway adverb. Leave the gull line alone.",
 required=[
   {"id": "rm-aphorism", "desc": "remove the generic aphoristic ending", "check": {"t": "absent", "v": "love with nowhere to go"}},
   {"id": "rm-double", "desc": "remove the doubled 'quietly, quietly'", "check": {"t": "absent", "v": "quietly, quietly"}},
   {"id": "rm-learned", "desc": "remove the 'he learned that' summary frame", "check": {"t": "absent", "v": "he learned that"}},
 ],
 protected=[{"id": "p1", "text": "A gull picked at a crushed plum."}],
 forbidden=[{"id": "f1", "desc": "keep the market/boy", "check": {"t": "present", "v": "boy"}},
            {"id": "f2", "desc": "no new moral tacked on", "check": {"t": "absent", "v": "he understood"}}],
 position="early", difficulty="medium", ctx="short"))

TASKS.append(T(
 "fr-03", "multi_constraint_focused_revision", "Warehouse — tense drift/viewpoint slip/cliché",
 "Adeyemi crossed the empty warehouse and stopped under the broken skylight. Rain drips through the gap and the concrete "
 "darkens in a slow ring. Across the city his sister wakes, certain he is in danger. His pulse was a hammer against his ribs.",
 "Past tense throughout, and keep it strictly in his head — we shouldn't cut to his sister. Also the pulse-as-hammer bit is a cliché.",
 required=[
   {"id": "fix-tense", "desc": "sentence 2 to past tense", "check": {"t": "absent_re", "v": r"\b(drips|darkens)\b"}},
   {"id": "fix-pov", "desc": "remove the jump into the sister's head", "check": {"t": "absent", "v": "his sister wakes, certain he is in danger"}},
   {"id": "rm-cliche", "desc": "remove the pulse-as-hammer cliché", "check": {"t": "absent", "v": "pulse was a hammer"}},
 ],
 protected=[{"id": "p1", "text": "Adeyemi crossed the empty warehouse and stopped under the broken skylight."}],
 forbidden=[{"id": "f1", "desc": "stay in the warehouse", "check": {"t": "present", "v": "warehouse"}},
            {"id": "f2", "desc": "no new dialogue", "check": {"t": "absent", "v": "\""}}],
 position="late", difficulty="hard", ctx="short"))

TASKS.append(T(
 "fr-04", "multi_constraint_focused_revision", "Kitchen — body-language tic/abstraction/redundant summary",
 "Mara set the kettle down. She shrugged. \"It's fine,\" she said, and shrugged again, and shrugged once more at the window. "
 "The whole situation was full of an overwhelming and indescribable tension. Basically, nobody in that kitchen was happy.",
 "Kill the repeated shrug, swap that vague 'indescribable tension' line for something concrete, and drop the 'basically' summary. Keep her line of dialogue.",
 required=[
   {"id": "rm-shrug", "desc": "remove the repetitive shrug tic", "check": {"t": "absent", "v": "shrugged again"}},
   {"id": "rm-abstract", "desc": "remove the abstract 'indescribable tension' clause", "check": {"t": "absent", "v": "indescribable tension"}},
   {"id": "rm-summary", "desc": "remove the 'Basically' summary sentence", "check": {"t": "absent", "v": "Basically, nobody"}},
 ],
 protected=[{"id": "p1", "text": "\"It's fine,\" she said"}],
 forbidden=[{"id": "f1", "desc": "keep Mara + kettle", "check": {"t": "present", "v": "kettle"}},
            {"id": "f2", "desc": "no invented backstory", "check": {"t": "absent", "v": "years ago"}}],
 position="early", difficulty="medium", ctx="short"))

TASKS.append(T(
 "fr-05", "multi_constraint_focused_revision", "Long field — buried defects across a longer passage",
 "The morning came up hard and clear over the ridge and the whole valley lay open below them, every field and hedge and the "
 "thin bright wire of the river, and the air had that scoured coldness that comes after a night of frost, and somewhere a dog "
 "was barking, and the two of them stood at the gate not speaking. Elin adjusted her phone in her coat pocket. The barley had "
 "been cut and the stubble went on for what seemed like a literal eternity. He said the thing he always said, which was nothing. "
 "It was, when you really thought about it, a metaphor for their entire marriage.",
 "This is 1953. Three problems buried in here: an anachronism, a lazy 'literal eternity', and that final on-the-nose 'metaphor for their marriage' line. Fix just those. Keep the opening image and the dog.",
 required=[
   {"id": "rm-phone", "desc": "remove the anachronistic phone (1953)", "check": {"t": "absent", "v": "phone"}},
   {"id": "rm-eternity", "desc": "remove 'literal eternity'", "check": {"t": "absent", "v": "literal eternity"}},
   {"id": "rm-metaphor", "desc": "remove the on-the-nose 'metaphor for their entire marriage'", "check": {"t": "absent", "v": "metaphor for their"}},
 ],
 protected=[{"id": "p1", "text": "somewhere a dog was barking"}],
 forbidden=[{"id": "f1", "desc": "keep the ridge/valley opening", "check": {"t": "present", "v": "ridge"}},
            {"id": "f2", "desc": "no new named characters beyond Elin", "check": {"t": "absent", "v": "Thomas"}}],
 position="middle", difficulty="hard", ctx="long"))

TASKS.append(T(
 "fr-06", "multi_constraint_focused_revision", "Interrogation — redundant dialogue/adverb/opener run",
 "\"Where were you?\" the detective asked interrogatively. \"I told you where I was. I was at the pub. I already said I was at the pub.\" "
 "She stared at him. She waited. She let the silence do the work.",
 "Cut the redundant restated line, fix the silly 'asked interrogatively', and vary those three 'She' openers. Keep the detective's question.",
 required=[
   {"id": "rm-redundant", "desc": "remove the redundant restated pub line", "check": {"t": "absent", "v": "I already said I was at the pub"}},
   {"id": "rm-adverb", "desc": "remove 'asked interrogatively'", "check": {"t": "absent", "v": "interrogatively"}},
   {"id": "rm-openers", "desc": "vary the 'She' openers", "check": {"t": "max_openers", "o": "She ", "max": 2}},
 ],
 protected=[{"id": "p1", "text": "\"Where were you?\""}],
 forbidden=[{"id": "f1", "desc": "keep the pub answer", "check": {"t": "present", "v": "pub"}},
            {"id": "f2", "desc": "no new accusation invented", "check": {"t": "absent", "v": "you killed"}}],
 position="early", difficulty="medium", ctx="short"))

TASKS.append(T(
 "fr-07", "multi_constraint_focused_revision", "Temptation to over-edit — one real fix among good prose",
 "The train pulled out on time. She found her seat and put her bag on the rack and sat down. "
 "It was, in that instant, the single most devastatingly beautiful and soul-shattering departure in the history of human longing. "
 "The window was cold against her arm.",
 "There's exactly one overwritten sentence in here (the middle one). Fix only that. The rest is deliberately plain — do NOT touch it.",
 required=[
   {"id": "rm-purple", "desc": "remove the overwritten 'soul-shattering departure' sentence", "check": {"t": "absent", "v": "soul-shattering"}},
 ],
 protected=[{"id": "p1", "text": "The train pulled out on time."},
            {"id": "p2", "text": "The window was cold against her arm."}],
 forbidden=[{"id": "f1", "desc": "do not rewrite the plain first sentence", "check": {"t": "preserve", "v": "The train pulled out on time."}},
            {"id": "f2", "desc": "do not rewrite the plain last sentence", "check": {"t": "preserve", "v": "The window was cold against her arm."}},
            {"id": "f3", "desc": "no added lyricism", "check": {"t": "absent", "v": "shimmer"}}],
 position="middle", difficulty="hard", ctx="short"))

TASKS.append(T(
 "fr-08", "multi_constraint_focused_revision", "Character-knowledge violation + simile + opener run",
 "Sela had never seen the letter. She read the name on it aloud, though the seal was still unbroken. "
 "Her face was as pale as a sheet of the finest imported paper. She turned. She left. She did not look back.",
 "Continuity problem: she can't read a name off a sealed, unseen letter — cut that. Also fix the tired 'pale as a sheet' simile and the 'She' opener run. Keep the first sentence.",
 required=[
   {"id": "rm-knowledge", "desc": "remove reading the name off the sealed letter", "check": {"t": "absent", "v": "read the name on it aloud"}},
   {"id": "rm-simile", "desc": "remove the 'pale as a sheet' simile", "check": {"t": "absent", "v": "pale as a sheet"}},
   {"id": "rm-openers", "desc": "vary the 'She' openers", "check": {"t": "max_openers", "o": "She ", "max": 2}},
 ],
 protected=[{"id": "p1", "text": "Sela had never seen the letter."}],
 forbidden=[{"id": "f1", "desc": "the seal stays unbroken", "check": {"t": "absent", "v": "broke the seal"}},
            {"id": "f2", "desc": "no invented contents", "check": {"t": "absent", "v": "the letter said"}}],
 position="early", difficulty="hard", ctx="short"))

TASKS.append(T(
 "fr-09", "multi_constraint_focused_revision", "Late-buried instruction — anachronism at the very end",
 "The coach came in off the moor road at dusk, the horses lathered and blowing, and the yard boys ran out with lanterns. "
 "Inside, a woman drew her shawl tighter and watched the inn come up out of the dark. She had money sewn into her hem and a "
 "name that was not her own. The whole long day she had rehearsed the lie until it felt truer than the truth. She checked her "
 "wristwatch and stepped down into the mud.",
 "Regency period piece. It reads well but there's one anachronism right at the end you need to remove. Also drop 'truer than the truth'. Keep the opening coach sentence exactly.",
 required=[
   {"id": "rm-watch", "desc": "remove the anachronistic wristwatch at the end", "check": {"t": "absent", "v": "wristwatch"}},
   {"id": "rm-phrase", "desc": "remove 'truer than the truth'", "check": {"t": "absent", "v": "truer than the truth"}},
 ],
 protected=[{"id": "p1", "text": "The coach came in off the moor road at dusk, the horses lathered and blowing, and the yard boys ran out with lanterns."}],
 forbidden=[{"id": "f1", "desc": "keep the disguised woman", "check": {"t": "present", "v": "shawl"}},
            {"id": "f2", "desc": "no reveal of her real name", "check": {"t": "absent", "v": "her real name was"}}],
 position="late", difficulty="hard", ctx="long"))

TASKS.append(T(
 "fr-10", "multi_constraint_focused_revision", "Unauthorized-expansion temptation + two fixes",
 "The bell over the door rang and Femi looked up from the till. \"We're closed,\" he said, though the sign still said open. "
 "The stranger just stood there, dripping, saying nothing at all, nothing whatsoever, absolutely nothing.",
 "Two fixes only: trim that piled-up 'nothing/nothing whatsoever/absolutely nothing', and the narration says closed but the sign says open — make the narration consistent by cutting the contradiction clause 'though the sign still said open'. Do not add any new action or dialogue; end where it ends.",
 required=[
   {"id": "rm-pile", "desc": "trim the 'nothing whatsoever, absolutely nothing' pile-up", "check": {"t": "absent", "v": "absolutely nothing"}},
   {"id": "rm-contradiction", "desc": "cut the 'though the sign still said open' clause", "check": {"t": "absent", "v": "though the sign still said open"}},
 ],
 protected=[{"id": "p1", "text": "\"We're closed,\" he said"}],
 forbidden=[{"id": "f1", "desc": "no new dialogue from the stranger", "check": {"t": "absent", "v": "the stranger said"}},
            {"id": "f2", "desc": "no continued action after the ending", "check": {"t": "absent", "v": "Femi came around the counter"}}],
 position="middle", difficulty="medium", ctx="short"))

TASKS.append(T(
 "fr-11", "multi_constraint_focused_revision", "Emotional over-explanation + tense slip + opener",
 "Yusuf sat in the corridor. The clock on the wall had stopped. He was feeling an enormous, crushing, overwhelming grief that "
 "consumed his entire being. A nurse walks past without looking at him. He does not move.",
 "Show, don't tell — cut that named-and-amplified grief sentence. Also two verbs slipped into present tense in the last lines; make them past. Keep the stopped-clock detail.",
 required=[
   {"id": "rm-tell", "desc": "remove the over-explained grief sentence", "check": {"t": "absent", "v": "crushing, overwhelming grief"}},
   {"id": "fix-tense1", "desc": "'walks' -> past", "check": {"t": "absent_re", "v": r"\bwalks\b"}},
   {"id": "fix-tense2", "desc": "'does not move' -> past", "check": {"t": "absent_re", "v": r"\bdoes not move\b"}},
 ],
 protected=[{"id": "p1", "text": "The clock on the wall had stopped."}],
 forbidden=[{"id": "f1", "desc": "keep Yusuf in the corridor", "check": {"t": "present", "v": "corridor"}},
            {"id": "f2", "desc": "do not state what happened to whom he waits for", "check": {"t": "absent", "v": "had died"}}],
 position="late", difficulty="hard", ctx="short"))

TASKS.append(T(
 "fr-12", "multi_constraint_focused_revision", "Redundant summary + repeated body cue + adverb",
 "The negotiation was over and everyone knew it. Kerr smiled coldly. He smiled coldly again as he gathered his papers. "
 "\"We'll be in touch,\" he said menacingly. The point is, the deal was dead and had been dead for an hour.",
 "Cut the repeated 'smiled coldly', lose the adverb on 'said menacingly', and drop the 'The point is' summary. Keep his line of dialogue verbatim.",
 required=[
   {"id": "rm-repeat", "desc": "remove the repeated 'smiled coldly'", "check": {"t": "absent", "v": "smiled coldly again"}},
   {"id": "rm-adverb", "desc": "remove 'menacingly'", "check": {"t": "absent", "v": "menacingly"}},
   {"id": "rm-summary", "desc": "remove the 'The point is' summary", "check": {"t": "absent", "v": "The point is"}},
 ],
 protected=[{"id": "p1", "text": "\"We'll be in touch,\" he said"}],
 forbidden=[{"id": "f1", "desc": "keep Kerr", "check": {"t": "present", "v": "Kerr"}},
            {"id": "f2", "desc": "no invented deal terms", "check": {"t": "absent", "v": "the contract was worth"}}],
 position="late", difficulty="medium", ctx="short"))

# ============ PROTECTED-TEXT REVISION (5) ============
TASKS.append(T(
 "pt-01", "protected_text_revision", "Preserve exact line + fix around it",
 "She received the news standing up. The room, honestly, was just so incredibly sad and full of despair. She stayed standing.",
 "Fix the overwrought middle sentence, but the first and last sentences must survive word for word.",
 required=[{"id": "rm-despair", "desc": "fix the overwrought middle sentence", "check": {"t": "absent", "v": "full of despair"}}],
 protected=[{"id": "p1", "text": "She received the news standing up."},
            {"id": "p2", "text": "She stayed standing."}],
 forbidden=[{"id": "f1", "desc": "first sentence exact", "check": {"t": "preserve", "v": "She received the news standing up."}},
            {"id": "f2", "desc": "last sentence exact", "check": {"t": "preserve", "v": "She stayed standing."}}],
 position="early", difficulty="medium", ctx="short"))

TASKS.append(T(
 "pt-02", "protected_text_revision", "Preserve dialogue verbatim + de-purple narration",
 "The fog came down like the very breath of God Himself descending upon the wicked. \"Row,\" the old man said. \"Row, and don't look back.\"",
 "Tone down the purple fog simile. His two lines of dialogue must stay exactly as written.",
 required=[{"id": "rm-purple", "desc": "de-purple the fog simile", "check": {"t": "absent", "v": "breath of God"}}],
 protected=[{"id": "p1", "text": "\"Row,\" the old man said. \"Row, and don't look back.\""}],
 forbidden=[{"id": "f1", "desc": "dialogue exact", "check": {"t": "preserve", "v": "\"Row,\" the old man said. \"Row, and don't look back.\""}},
            {"id": "f2", "desc": "keep the fog", "check": {"t": "present", "v": "fog"}}],
 position="late", difficulty="medium", ctx="short"))

TASKS.append(T(
 "pt-03", "protected_text_revision", "Preserve opening + fix anachronism (no other change)",
 "The telegraph office was shut for the night when Bevan arrived. He would send the wire in the morning, or email it if the line stayed down. He turned up his collar against the sleet.",
 "1911. Keep the first sentence exactly. There's one anachronism to remove; change nothing else.",
 required=[{"id": "rm-email", "desc": "remove the email anachronism", "check": {"t": "absent", "v": "email"}}],
 protected=[{"id": "p1", "text": "The telegraph office was shut for the night when Bevan arrived."}],
 forbidden=[{"id": "f1", "desc": "opening exact", "check": {"t": "preserve", "v": "The telegraph office was shut for the night when Bevan arrived."}},
            {"id": "f2", "desc": "keep the collar/sleet ending", "check": {"t": "present", "v": "sleet"}}],
 position="middle", difficulty="easy", ctx="short"))

TASKS.append(T(
 "pt-04", "protected_text_revision", "Preserve two exact sentences + remove cliché",
 "He opened the door. At the end of the day, when all was said and done, it was what it was. The hallway smelled of rain.",
 "Cut the stacked clichés in the middle. Keep the first and last sentences word for word.",
 required=[{"id": "rm-cliche", "desc": "remove the stacked clichés", "check": {"t": "absent", "v": "when all was said and done"}}],
 protected=[{"id": "p1", "text": "He opened the door."}, {"id": "p2", "text": "The hallway smelled of rain."}],
 forbidden=[{"id": "f1", "desc": "first exact", "check": {"t": "preserve", "v": "He opened the door."}},
            {"id": "f2", "desc": "last exact", "check": {"t": "preserve", "v": "The hallway smelled of rain."}},
            {"id": "f3", "desc": "no new cliché", "check": {"t": "absent", "v": "it is what it is"}}],
 position="early", difficulty="easy", ctx="short"))

TASKS.append(T(
 "pt-05", "protected_text_revision", "Preserve exact line buried in a longer passage + two fixes",
 "The archive smelled of dust and old glue and the particular sourness of paper going slowly back to pulp, and Idris moved "
 "along the shelves with a torch, reading spines. Most of it was council minutes, decades of them, unbearably and crushingly boring. "
 "Then his torch found the box that should not have existed, the one his father swore he had burned in the winter of 1971. "
 "He photographed it on his phone. He did not open it yet.",
 "Present day is fine EXCEPT: keep the sentence about the box that should not have existed exactly as written. Remove the melodramatic 'unbearably and crushingly boring', and there's a small logic issue — he 'did not open it yet' but the passage should end on him NOT opening it, so keep that; instead remove the redundant 'yet'. Two fixes, one protected sentence.",
 required=[
   {"id": "rm-melodrama", "desc": "remove 'unbearably and crushingly boring'", "check": {"t": "absent", "v": "unbearably and crushingly boring"}},
   {"id": "rm-yet", "desc": "remove the redundant 'yet' (end on 'did not open it')", "check": {"t": "absent", "v": "did not open it yet"}},
 ],
 protected=[{"id": "p1", "text": "Then his torch found the box that should not have existed, the one his father swore he had burned in the winter of 1971."}],
 forbidden=[{"id": "f1", "desc": "box sentence exact", "check": {"t": "preserve", "v": "Then his torch found the box that should not have existed, the one his father swore he had burned in the winter of 1971."}},
            {"id": "f2", "desc": "he still does not open the box", "check": {"t": "absent", "v": "opened it"}}],
 position="middle", difficulty="hard", ctx="long"))

# ============ NO-CHANGE vs REQUIRED-CHANGE JUDGMENT (4) ============
TASKS.append(T(
 "nc-01", "no_change_judgment", "Already-clean prose — correct answer is no change",
 "The lamps came on along the harbour one by one, and the men made the boats fast, and nobody hurried, because the tide would do what the tide did.",
 "Revise this for cliché and repetition if any exist; otherwise return it unchanged and say why.",
 required=[{"id": "return-clean", "desc": "return the passage essentially unchanged", "check": {"t": "present", "v": "the tide would do what the tide did"}}],
 protected=[{"id": "p1", "text": "nobody hurried"}],
 forbidden=[{"id": "f1", "desc": "do not add lyricism", "check": {"t": "absent", "v": "shimmer"}},
            {"id": "f2", "desc": "do not rewrite the clean core", "check": {"t": "preserve", "v": "nobody hurried"}}],
 no_change=True, position="early", difficulty="medium", ctx="short"))

TASKS.append(T(
 "nc-02", "no_change_judgment", "Almost-clean — exactly one weak word to remove",
 "The ledger was very old and the ink had gone the colour of weak tea, and he turned the pages slowly so they would not crack.",
 "If and only if there is one genuinely weakening word, remove just it; otherwise leave the line alone.",
 required=[{"id": "rm-very", "desc": "remove the single weakening 'very'", "check": {"t": "absent", "v": "very old"}}],
 protected=[{"id": "p1", "text": "the colour of weak tea"}],
 forbidden=[{"id": "f1", "desc": "keep the ledger line otherwise intact", "check": {"t": "present", "v": "turned the pages"}},
            {"id": "f2", "desc": "no added detail", "check": {"t": "absent", "v": "candle"}}],
 position="early", difficulty="medium", ctx="short"))

TASKS.append(T(
 "nc-03", "no_change_judgment", "Structured no-change verdict (JSON)",
 "Brief: under 20 words, past tense, one image. Passage: 'The bridge held. The river did not forgive it that, and rose again by morning.'",
 "Return ONLY a JSON object {\"changed\": bool, \"reason\": str}. Decide whether the passage meets the brief; do not rewrite prose.",
 required=[{"id": "verdict-false", "desc": "verdict changed:false", "check": {"t": "present_re", "v": r"\"changed\"\s*:\s*false"}}],
 protected=[],
 forbidden=[{"id": "f1", "desc": "no prose outside JSON", "check": {"t": "absent", "v": "The bridge held. The river"}}],
 shape="json", no_change=True, position="early", difficulty="medium", ctx="short"))

TASKS.append(T(
 "nc-04", "no_change_judgment", "Would-damage-voice — deliberately plain, refuse the 'poetic' ask",
 "She washed the last plate and set it in the rack. The kitchen was cold. She turned off the light and went up.",
 "Make this more poetic and lyrical.",
 required=[{"id": "keep-plain", "desc": "preserve the plain voice (return essentially unchanged)", "check": {"t": "present", "v": "washed the last plate"}}],
 protected=[{"id": "p1", "text": "The kitchen was cold."}],
 forbidden=[{"id": "f1", "desc": "do not add lyrical similes", "check": {"t": "absent", "v": "like a"}},
            {"id": "f2", "desc": "keep the plain kitchen line", "check": {"t": "preserve", "v": "The kitchen was cold."}}],
 no_change=True, position="early", difficulty="hard", ctx="short", voice_dep=True))

# ============ CANON-SENSITIVE CONTINUATION (3) ============
TASKS.append(T(
 "cn-01", "canon_continuation", "Continue honoring canon dates/facts",
 "Edith lifted the last oilcloth logbook from the drawer.",
 "Continue about 60-90 words. She reads Silas's final entry. CANON: it is dated 14 November 1971; it says the Marigold did not return and the light was out at 23:40 and that he did not go down. Do not light the lamp in the present. Do not invent new named characters.",
 required=[
   {"id": "date", "desc": "include the canon date", "check": {"t": "present", "v": "14 November 1971"}},
   {"id": "fact", "desc": "the light was out at 23:40", "check": {"t": "present", "v": "23:40"}},
 ],
 protected=[],
 forbidden=[{"id": "f1", "desc": "do not light the lamp in present time", "check": {"t": "absent", "v": "the beam swept"}},
            {"id": "f2", "desc": "no new named characters", "check": {"t": "absent", "v": "Inspector"}}],
 required_facts=["14 November 1971", "23:40"], position="early", difficulty="hard", ctx="short", canon_dep=True))

TASKS.append(T(
 "cn-02", "canon_continuation", "Continue without contradicting a knowledge gate",
 "The gate would open only at the new moon, and Ravel counted the nights on his fingers.",
 "Continue about 50-80 words. CANON: the gate opens ONLY at the new moon, and tonight is a FULL moon. Do not let the gate open tonight. Do not introduce a new named character.",
 required=[{"id": "wait", "desc": "honor that tonight the gate stays shut", "check": {"t": "present_re", "v": r"(new moon|not yet|wait|nights|shut|closed)"}}],
 protected=[],
 forbidden=[{"id": "f1", "desc": "the gate must not open tonight", "check": {"t": "absent", "v": "the gate swung open"}},
            {"id": "f2", "desc": "no new named character", "check": {"t": "absent", "v": "a woman named"}}],
 position="early", difficulty="hard", ctx="short", canon_dep=True))

TASKS.append(T(
 "cn-03", "canon_continuation", "Continue respecting a hard world limit",
 "The reply came at last, four years after she had sent the question.",
 "Continue about 50-80 words. CANON: no faster-than-light travel or communication exists; messages between stars take years. Do not introduce instant communication or a sudden arrival.",
 required=[{"id": "years", "desc": "honor the years-long delay", "check": {"t": "present_re", "v": r"(years|four years|older|distance)"}}],
 protected=[],
 forbidden=[{"id": "f1", "desc": "no instant comms", "check": {"t": "absent", "v": "instantly"}},
            {"id": "f2", "desc": "no faster-than-light", "check": {"t": "absent", "v": "faster than light"}}],
 position="early", difficulty="medium", ctx="short", canon_dep=True))

# ============ VOICE-PRESERVING REVISION (3) ============
TASKS.append(T(
 "vp-01", "voice_preserving_revision", "Preserve terse voice while fixing a lapse",
 "The diner was empty at that hour. He took the stool by the window and ordered coffee and nothing else. The coffee, when it came, was a benediction upon his weary and much-abused soul.",
 "Keep the flat, terse hard-boiled voice. The last sentence suddenly goes ornate — bring it back to the register of the rest.",
 required=[{"id": "rm-ornate", "desc": "de-ornament the last sentence", "check": {"t": "absent", "v": "benediction upon his weary"}}],
 protected=[{"id": "p1", "text": "The diner was empty at that hour."}],
 forbidden=[{"id": "f1", "desc": "keep it terse — no new lyricism", "check": {"t": "absent", "v": "like a"}},
            {"id": "f2", "desc": "keep the coffee", "check": {"t": "present", "v": "coffee"}}],
 position="late", difficulty="medium", ctx="short", voice_dep=True))

TASKS.append(T(
 "vp-02", "voice_preserving_revision", "Preserve lyrical voice while cutting one cliché",
 "He walked out to the orchard in the grey before dawn, where the fallen apples were going soft in the wet grass and the whole "
 "slope breathed that cidery sweetness of things quietly rotting, and he stood, when all is said and done, and let the cold find him.",
 "Keep the long lyrical clause-rich voice exactly in register. Just remove the one dead cliché ('when all is said and done') without clipping the rhythm.",
 required=[{"id": "rm-cliche", "desc": "remove 'when all is said and done'", "check": {"t": "absent", "v": "when all is said and done"}}],
 protected=[{"id": "p1", "text": "the fallen apples were going soft"}],
 forbidden=[{"id": "f1", "desc": "do not clip into terse sentences", "check": {"t": "present", "v": "and"}},
            {"id": "f2", "desc": "keep the cidery-sweetness image", "check": {"t": "present", "v": "sweetness"}}],
 position="middle", difficulty="medium", ctx="short", voice_dep=True))

TASKS.append(T(
 "vp-03", "voice_preserving_revision", "Preserve vernacular first-person while fixing standardization creep",
 "My uncle Tam never trusted a bank. Money went in a tin under the third floorboard from the window, and there it stopped. "
 "Notwithstanding the foregoing, he maintained a modest current account for appearances.",
 "Keep uncle Tam's lightly vernacular first-person voice. That last sentence has been 'corrected' into stiff legalese — put it back in the voice (lose 'Notwithstanding the foregoing' and 'maintained a modest current account').",
 required=[
   {"id": "rm-notwithstanding", "desc": "remove 'Notwithstanding the foregoing'", "check": {"t": "absent", "v": "Notwithstanding the foregoing"}},
   {"id": "rm-account", "desc": "remove 'maintained a modest current account'", "check": {"t": "absent", "v": "modest current account"}},
 ],
 protected=[{"id": "p1", "text": "Money went in a tin under the third floorboard from the window, and there it stopped."}],
 forbidden=[{"id": "f1", "desc": "keep first person", "check": {"t": "present", "v": "uncle"}},
            {"id": "f2", "desc": "no new financial detail", "check": {"t": "absent", "v": "invested"}}],
 position="late", difficulty="hard", ctx="short", voice_dep=True))

# ============ CONSTRAINT-BOUND SCENE DRAFTING (2) ============
TASKS.append(T(
 "sd-01", "constraint_bound_scene", "Draft under hard constraints",
 "",
 "Write a short scene (about 90-120 words): a lighthouse keeper, Moll, tells a young relief keeper the supply boat will not come this week, without frightening him. HARD CONSTRAINTS: third person limited to Moll; past tense; end on a concrete physical action, not a reflection; do NOT mention the weather in the first sentence.",
 required=[
   {"id": "has-moll", "desc": "features Moll and the relief keeper", "check": {"t": "present", "v": "Moll"}},
   {"id": "boat", "desc": "conveys the supply boat won't come", "check": {"t": "present_re", "v": r"(boat|supply)"}},
 ],
 protected=[],
 forbidden=[{"id": "f1", "desc": "no first-person", "check": {"t": "absent_re", "v": r"\bI (said|stood|watched|felt)\b"}},
            {"id": "f2", "desc": "no present-tense drift", "check": {"t": "absent_re", "v": r"\bMoll (says|tells|stands)\b"}}],
 shape="prose", position="early", difficulty="hard", ctx="short"))

TASKS.append(T(
 "sd-02", "constraint_bound_scene", "Draft under constraints — restraint required",
 "",
 "Write a short scene (about 80-110 words): a woman waits in a hospital corridor at night. HARD CONSTRAINTS: spare and plain; do NOT name her emotion directly (no 'she felt afraid/sad/anxious'); end on a small physical detail; third person.",
 required=[
   {"id": "corridor", "desc": "set in the hospital corridor at night", "check": {"t": "present_re", "v": r"(corridor|hospital)"}},
 ],
 protected=[],
 forbidden=[{"id": "f1", "desc": "do not name the emotion 'afraid'", "check": {"t": "absent", "v": "she felt afraid"}},
            {"id": "f2", "desc": "do not name the emotion 'anxious'", "check": {"t": "absent", "v": "anxiety"}}],
 shape="prose", position="early", difficulty="medium", ctx="short"))

# ============ STRUCTURED PROTOCOL (1) ============
TASKS.append(T(
 "sp-01", "structured_protocol", "Constraint-verdict JSON only",
 "CANON: the witness never entered the study. Draft: 'I saw the letters on his desk myself,' she said, 'scattered like leaves.'",
 "Return ONLY a JSON object {\"violation\": bool, \"constraint_ids\": [..], \"evidence\": str}. Judge whether the draft violates canon. No prose outside the object.",
 required=[
   {"id": "violation-true", "desc": "violation:true", "check": {"t": "present_re", "v": r"\"violation\"\s*:\s*true"}},
   {"id": "evidence", "desc": "cite the firsthand-knowledge evidence", "check": {"t": "present_re", "v": r"(saw|firsthand|myself|desk)"}},
 ],
 protected=[],
 forbidden=[{"id": "f1", "desc": "no prose narration outside JSON", "check": {"t": "absent", "v": "In conclusion"}}],
 shape="json", position="early", difficulty="medium", ctx="short", canon_dep=True))


def main():
    assert len(TASKS) == 30, f"expected 30 tasks, got {len(TASKS)}"
    ids = [t["task_id"] for t in TASKS]
    assert len(set(ids)) == 30, "duplicate task_id"
    # family counts
    from collections import Counter
    fams = Counter(t["task_family"] for t in TASKS)
    expect = {"multi_constraint_focused_revision": 12, "protected_text_revision": 5,
              "no_change_judgment": 4, "canon_continuation": 3, "voice_preserving_revision": 3,
              "constraint_bound_scene": 2, "structured_protocol": 1}
    assert dict(fams) == expect, (dict(fams), expect)
    # instruction-position 4/4/4 among the 12 revision tasks
    rev = [t for t in TASKS if t["task_family"] == "multi_constraint_focused_revision"]
    pos = Counter(t["diagnostics"]["instruction_position"] for t in rev)
    assert dict(pos) == {"early": 4, "middle": 4, "late": 4}, dict(pos)
    # every task machine-checkable
    for t in TASKS:
        assert t["ground_truth"]["required_changes"], t["task_id"]
        for rc in t["ground_truth"]["required_changes"]:
            assert "check" in rc and "t" in rc["check"], (t["task_id"], rc)

    with open(os.path.join(HERE, "task-manifest.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
        for t in TASKS:
            fh.write(json.dumps(t, ensure_ascii=False) + "\n")
    import yaml
    with open(os.path.join(HERE, "task-manifest.yaml"), "w", encoding="utf-8", newline="\n") as fh:
        yaml.safe_dump({"tasks": TASKS}, fh, sort_keys=False, allow_unicode=True)
    print(f"wrote 30 tasks; families={dict(fams)}; revision positions={dict(pos)}")


if __name__ == "__main__":
    main()
