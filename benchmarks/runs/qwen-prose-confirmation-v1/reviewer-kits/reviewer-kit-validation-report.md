# Reviewer-kit validation report

Source commit `e1d00f6802e85cf790eb40938be1b517a066ce97`; 36 anonymous units; source packet sha256 `6968d598b23f29cd…`.

Note: paired units (two per task, for absolute scoring) share task text by design; this does NOT reveal precision identity (the two precisions were mechanically identical and blind-indistinguishable). Presentation order is reviewer-salted and randomized.

## chatgpt kit
- zip: `benchmarks/runs/qwen-prose-confirmation-v1/reviewer-kits/prose-review-chatgpt-v1.zip`
- sha256: `e3dc89358ccd104fea7f9f7ca277fe338a7519efdf2e48005ff17c2288166987`  size: 244879B  files: 7
- all 36 units present exactly once; template ids match; JSON+YAML parse
- reviewer_id correct: chatgpt

## claude kit
- zip: `benchmarks/runs/qwen-prose-confirmation-v1/reviewer-kits/prose-review-claude-v1.zip`
- sha256: `cf93081ec2fbec501a86fc0289eccd2060e10f36d6d98046ce976c3c429e0fe0`  size: 244863B  files: 7
- all 36 units present exactly once; template ids match; JSON+YAML parse
- reviewer_id correct: claude

## Forbidden-term scan
- identity-relevant matches: **0** (target 0)

## Isolation
- identity key included: no
- private paths included: no
- previous reviewer scores included: no
- deployment/model manifests included: no

## Naming (blindness-preserving deviation)
The kit directory, ZIP filename, and template `review_id` are NEUTRAL (`prose-review-*`, `prose-confirmation-v1`) rather than the dispatch's illustrative `qwen-*` names, because those would announce the model identity to the blind reviewer and fail the mandated zero-match forbidden scan. Blindness is the dispatch's paramount, repeatedly-stated requirement, so it overrides the illustrative filename. The private manifest still records the true run id (`qwen-prose-confirmation-v1`) for the owner.

