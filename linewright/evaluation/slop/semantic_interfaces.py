"""Semantic slop-detector INTERFACES (Dispatch 23, slop Layer 2).

Interface-only in this dispatch (research_review: interface_only). Semantic detectors may use
frozen embeddings, pinned classifiers, rule-assisted candidate generation, and calibrated
reviewer confirmation — but no embedding dependency is required to import this module, and no
threshold is validated. Every semantic finding MUST retain evidence spans; a scalar without
the implicated passages is insufficient. The default implementation is a NULL detector that
returns no findings with ``detector_confidence: unvalidated`` so the pipeline runs offline.
"""
import re

VERSION = "semantic-interfaces-v1"

SEMANTIC_DETECTORS = [
    "semantic_redundant_span_pairs", "paraphrased_repetition",
    "explanation_after_demonstration", "repeated_paragraph_function",
    "local_coherence_anomaly", "scene_progression_stall", "voice_profile_distance",
    "character_voice_similarity", "cross_output_template_similarity", "semantic_diversity",
]


class SemanticDetector:
    """Interface a concrete (pinned-embedding) detector implements later.

    Contract: ``analyze(output, context)`` returns a dict with, per detector, a list of
    findings, each carrying ``evidence_spans`` (verbatim) and never a bare scalar.
    """
    detector_id = "abstract"
    model_name = None
    model_revision = None
    thresholds_status = "unvalidated"

    def analyze(self, output, context=None):
        raise NotImplementedError


class NullSemanticDetector(SemanticDetector):
    """Offline default: emits the interface shape with no findings, confidence unvalidated.

    A concrete detector will replace this once frozen embeddings are pinned. Until then the
    slop report's semantic block is structurally present but empty and clearly unvalidated —
    never a fabricated similarity number.
    """
    detector_id = "null-semantic-v1"

    def analyze(self, output, context=None):
        block = {d: [] for d in SEMANTIC_DETECTORS if d not in
                 ("voice_profile_distance", "character_voice_similarity",
                  "cross_output_template_similarity")}
        block.update({
            "voice_profile_distance": None,
            "character_voice_similarity": None,
            "cross_output_template_similarity": None,
            "evidence_spans": [],
            "detector_confidence": "unvalidated",
            "detector_id": self.detector_id,
        })
        return block


def manifest_entry(detector):
    """The pinned manifest entry for a semantic detector (thresholds unvalidated)."""
    return {
        "detector_id": detector.detector_id,
        "model_name": detector.model_name,
        "model_revision": detector.model_revision,
        "tokenizer_revision": getattr(detector, "tokenizer_revision", None),
        "library_versions": getattr(detector, "library_versions", {}),
        "pooling_method": getattr(detector, "pooling_method", None),
        "normalization": getattr(detector, "normalization", None),
        "segmentation_method": getattr(detector, "segmentation_method", "sentence"),
        "thresholds_status": detector.thresholds_status,
    }
