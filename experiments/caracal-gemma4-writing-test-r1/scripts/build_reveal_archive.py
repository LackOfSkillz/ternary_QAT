"""Caracal Gemma-4 writing test — build + AES-256 encrypt the two-person reveal archive (DEFERRED).

Do NOT run until candidate mapping is frozen. Produces caracal-gemma4-writing-test-r1-blind-key.7z
(7z AES-256, header encryption on) containing READ-ME-FIRST.txt, candidate-reveal.html/.csv,
blind-key.json, generation-manifest.json, candidate-hashes.txt. Generates a >=256-bit random password
(not derived from any experiment value), splits it 2-of-2, records the public archive SHA-256 in the
safe report, and writes the private emergency-recovery files. See freeze/blind-review-plan.yaml.
"""
raise SystemExit("DEFERRED: awaiting frozen candidate mapping (see freeze/blind-review-plan.yaml)")
