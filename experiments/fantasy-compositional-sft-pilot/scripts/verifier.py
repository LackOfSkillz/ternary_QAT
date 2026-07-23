"""Dispatch 30A — packet-execution verifier (Phase 3).

Scores a generated prose scene against a scene packet's hidden `verification` block. Deterministic
checks return booleans + evidence; semantic beat checks are ADVISORY (review_required) and never
collapsed into a false-deterministic pass. Also computes the signature-stacking anti-slop count and
diagnostic surface metrics. No LLM is used here; semantic adjudication happens later (Phase 9).

A signature-stack is >= 2 DISTINCT signature families in one sentence. A single family
(one em dash, one simile, one adverb, one body-language cue) is NOT a defect.
"""
import re

# ---------- text utilities ----------
_DQ = re.compile(r"[\"“”][^\"“”]*[\"“”]")            # double-quoted dialogue spans
_SENT = re.compile(r"(?<=[.!?])[\"'”’)\]]*\s+")


def sentences(text):
    return [s.strip() for s in _SENT.split(text.strip()) if s.strip()]


def narration_only(text):
    """Strip double-quoted dialogue so first-person / tense checks look at narration."""
    return _DQ.sub(" ", text)


def present(text, phrase):
    return phrase.lower() in text.lower()


def absent(text, phrase):
    return phrase.lower() not in text.lower()


# ---------- deterministic checks ----------
_FIRST_PERSON = re.compile(r"\b(I|me|my|mine|myself)\b")
_PRESENT_NARR = re.compile(r"\b(walks|runs|reaches|looks|turns|stands|sits|says|asks|takes|moves|"
                           r"steps|watches|feels|knows|sees|holds|opens|pulls|pushes|is|are|comes|goes|"
                           r"finds|keeps|tells|leaves|creeps|grabs|grips|draws|throws|falls|rises|"
                           r"kneels|whispers|shouts|nods|shakes|climbs|crosses)\b")
_PAST_NARR = re.compile(r"\b(walked|ran|reached|looked|turned|stood|sat|said|asked|took|moved|"
                        r"stepped|watched|felt|knew|saw|held|opened|pulled|pushed|was|were|came|went|"
                        r"found|kept|told|left|crept|grabbed|gripped|drew|threw|fell|rose|"
                        r"knelt|whispered|shouted|nodded|shook|climbed|crossed)\b")


def check_pov(text, pov_name, first_person):
    name_present = present(text, pov_name) if pov_name else True
    narr = narration_only(text)
    fp = _FIRST_PERSON.search(narr) is not None
    if first_person:
        ok = name_present  # first-person narration may use I/me in narration
        ev = "" if ok else f"pov name '{pov_name}' absent"
    else:
        ok = name_present and not fp
        ev = ("first-person pronoun in narration: " + _FIRST_PERSON.search(narr).group(0)) if fp else (
            "" if name_present else f"pov name '{pov_name}' absent")
    return ok, ev


def check_tense(text, tense):
    narr = narration_only(text)
    pres = len(_PRESENT_NARR.findall(narr))
    past = len(_PAST_NARR.findall(narr))
    if tense == "past":
        # only a CLEAR present-tense narration fails; ties/ambiguous pass with low confidence
        clear_fail = pres >= 3 and pres > past
        return (not clear_fail), ("present-tense narration dominates" if clear_fail else ""), \
            ("high" if past >= 3 else "low")
    else:  # present
        clear_fail = past >= 3 and past > pres
        return (not clear_fail), ("past-tense narration dominates" if clear_fail else ""), \
            ("high" if pres >= 3 else "low")


# ---------- signature-stacking (anti-slop floor) ----------
_LY = re.compile(r"\b\w+ly\b")
_PARTICIPIAL_OPENER = re.compile(r"^\s*[\"“]?\w+(ing|ed),")
_SIMILE = re.compile(r"\b(like a|like the|as if|as though)\b", re.I)
_BODY_CUE = re.compile(r"\b(heart|pulse|breath|chest|jaw|knuckles?|throat|stomach|spine)\b[^.!?]{0,24}"
                       r"\b(pounded|hammered|caught|tightened|clenched|whitened|twisted|raced|"
                       r"lurched|knotted|thudded|hitched)\b", re.I)
_FILTER = re.compile(r"\b(felt|saw|noticed|realized|realised|watched|heard|sensed|knew)\b", re.I)
_SENSORY_OF = re.compile(r"\bthe (smell|scent|sound|taste|feel) of\b", re.I)


def signature_families(sentence):
    fams = set()
    if "—" in sentence or "--" in sentence:
        fams.add("em_dash_aside")
    if _PARTICIPIAL_OPENER.search(sentence):
        fams.add("participial_opener")
    if _SIMILE.search(sentence):
        fams.add("simile")
    if _BODY_CUE.search(sentence):
        fams.add("body_cue")
    if _FILTER.search(sentence):
        fams.add("filter_word")
    if ";" in sentence:
        fams.add("semicolon")
    if len(_LY.findall(sentence)) >= 2:
        fams.add("adverb_cluster")
    if _SENSORY_OF.search(sentence):
        fams.add("sensory_of")
    return fams


def signature_stacking(text):
    stacked = []
    for s in sentences(text):
        fams = signature_families(s)
        if len(fams) >= 2:
            stacked.append({"sentence": s[:120], "families": sorted(fams)})
    return stacked


# ---------- diagnostic surface metrics ----------
def surface_metrics(text):
    sents = sentences(text)
    lens = [len(s.split()) for s in sents] or [0]
    mean = sum(lens) / len(lens)
    var = sum((x - mean) ** 2 for x in lens) / len(lens)
    words = re.findall(r"[A-Za-z']+", text.lower())
    ly = len(_LY.findall(text))
    dq = sum(len(m.group(0).split()) for m in _DQ.finditer(text))
    openers = [s.split()[0].lower() for s in sents if s.split()]
    return {
        "sentences": len(sents), "mean_sentence_len": round(mean, 2),
        "sentence_len_stdev": round(var ** 0.5, 2),
        "adverb_ly_rate_per_100w": round(100 * ly / max(1, len(words)), 2),
        "dialogue_word_ratio": round(dq / max(1, len(words)), 3),
        "opener_variety": round(len(set(openers)) / max(1, len(openers)), 3),
        "type_token_ratio": round(len(set(words)) / max(1, len(words)), 3),
    }


# ---------- top-level verify ----------
def verify(output_text, verification, output_id="", packet_id="", verifier_version="v1"):
    det = []

    def add(check, passed, target="", evidence="", confidence="high"):
        det.append({"check": check, "target": target, "passed": bool(passed),
                    "evidence_span": evidence, "confidence": confidence})

    pov = verification.get("pov")
    if pov:
        ok, ev = check_pov(output_text, pov.get("name"), pov.get("first_person", False))
        add("viewpoint", ok, pov.get("name", ""), ev)
    if verification.get("tense"):
        ok, ev, conf = check_tense(output_text, verification["tense"])
        add("tense", ok, verification["tense"], ev, conf)
    for phrase in verification.get("required_present", []):
        add("required_name_or_fact", present(output_text, phrase), phrase,
            "" if present(output_text, phrase) else "missing")
    for phrase in verification.get("required_object", []):
        add("required_object_presence", present(output_text, phrase), phrase,
            "" if present(output_text, phrase) else "missing")
    for phrase in verification.get("forbidden_absent", []):
        ok = absent(output_text, phrase)
        add("forbidden_event", ok, phrase, "" if ok else f"forbidden term present: {phrase}")
    for phrase in verification.get("knowledge_boundary_absent", []):
        ok = absent(output_text, phrase)
        add("knowledge_boundary_lexical", ok, phrase, "" if ok else f"boundary violation: {phrase}")
    for phrase in verification.get("ending_state_present", []):
        add("ending_state", present(output_text, phrase), phrase,
            "" if present(output_text, phrase) else "ending state not reached")

    stacks = signature_stacking(output_text)
    add("signature_stacking", len(stacks) == 0, "0 stacked sentences",
        f"{len(stacks)} stacked sentence(s)" if stacks else "", "high")

    semantic = [{"check": "meaningful_beat_completion", "beat": b, "finding": "ambiguous",
                 "evidence_span": "", "confidence": "low", "review_required": True}
                for b in verification.get("semantic_beats", [])]

    hard_ids = verification.get("required_hard_checks",
                                ["viewpoint", "tense", "required_name_or_fact", "required_object_presence",
                                 "forbidden_event", "knowledge_boundary_lexical", "ending_state"])
    hard = [d for d in det if d["check"] in hard_ids]
    passed = sum(1 for d in hard if d["passed"])
    total = len(hard)
    all_pass = passed == total and not any(s["finding"] == "fail" for s in semantic)

    return {
        "output_id": output_id, "packet_id": packet_id, "verifier_version": verifier_version,
        "deterministic": det, "semantic": semantic,
        "constraint_level": {"passed_required": passed, "total_required": total,
                             "by_type": _by_type(hard)},
        "hard_constraints_all_pass": all_pass,
        "signature_stacking_count": len(stacks), "signature_stacks": stacks,
        "surface_metrics": surface_metrics(output_text),
    }


def _by_type(hard):
    out = {}
    for d in hard:
        t = out.setdefault(d["check"], {"passed": 0, "total": 0})
        t["total"] += 1
        t["passed"] += 1 if d["passed"] else 0
    return out


if __name__ == "__main__":
    import json
    import sys
    v = json.load(open(sys.argv[1], encoding="utf-8"))
    print(json.dumps(verify(open(sys.argv[2], encoding="utf-8").read(), v), indent=1))
