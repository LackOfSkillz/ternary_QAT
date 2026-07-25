# Training Serialization - Final (Dispatch 30G)

Two controlled SFT arms from the same 54 targets; identical except packet representation. Metadata only.

| | atomic | compositional |
|---|---|---|
| records | 54 | 54 |
| unique targets | 54 | 54 |
| duplicate record_ids / targets | 0 / 0 | 0 / 0 |
| completion-only loss | true | true |
| records over 8192 | 0 | 0 |
| gold targets truncated | 0 | 0 |
| prompt tokens | 219-405 | 453-1073 |
| completion tokens | 1828-4973 | 1828-4973 |
| total tokens | 2068-5265 | 2476-5766 |

**Contamination:** 0 held-out records in either arm; 0 c01 record_ids; 0 held-out target hashes. Negative self-test raised HeldoutContaminationError (contaminated output not persisted). Dataset hash prefixes recorded privately.
