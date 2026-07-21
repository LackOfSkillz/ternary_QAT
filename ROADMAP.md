# LineWright Starter Model Research Roadmap

## Project purpose

This fork exists to evaluate whether a compact local model can provide a
**zero-configuration starter experience** for LineWright users. The question is
one of feasibility, not a foregone conclusion.

The starter model is intended to:

- Run locally
- Require no API key
- Require no model-server knowledge
- Work on broadly available modern consumer hardware
- Support bounded LineWright tasks
- Remain optional and replaceable by stronger local or API models

Nothing here asserts that Ternary-Bonsai 4B, ternary QAT, or Q2_0 has already
been selected for release. Every element below is subject to the feasibility
gates defined in this document.

## Upstream attribution

- This fork is based on [`electroglyph/ternary_QAT`](https://github.com/electroglyph/ternary_QAT).
- ElectroGlyph's project remains the upstream source of the ternary-QAT work.
- Reusable, generally useful improvements should be considered for contribution
  back upstream.
- LineWright-specific research will remain isolated in this fork where practical,
  so it does not entangle the upstream library with application-specific concerns.

## Author-content training boundary

> Author manuscripts, project content, voice samples, and private writing may be
> used only as temporary inference-time context. They must carry provenance tags
> that mechanically exclude them from training datasets. Selection history and
> voice measurements may inform context compilation, but nothing derived from
> author content may become gradient input.

In addition:

- There is **no hidden training or improvement program**.
- No author content is automatically collected for model training.
- Private internal feasibility packets may contain Gary's own manuscript content
  (used as inference-time context only, never as gradient input).
- Any benchmark distributed publicly or shipped with LineWright must use
  synthetic, licensed, public-domain, or otherwise distributable material.

## Scheduling gate

> **No Gary-hours may be spent on the starter-model track before VOICE-P0A has
> shipped and the craft taxonomy experiment has run.**

Aedan may perform low-cost infrastructure and documentation work before that
gate. The following remain **blocked** until the gate clears:

- Dataset review
- Mapping adjudication
- Threshold adjudication
- Gold-answer writing
- Manual benchmark scoring
- Training-data approval

The starter-model track may not displace the active LineWright roadmap, Voice Lab
work, or Gary's manuscript writing.

## Initial model candidate

Ternary-Bonsai 4B is the **initial candidate** for feasibility testing because it
may balance:

- Compressed size
- Consumer-hardware compatibility
- Instruction following
- Structured output
- Focused revision capability

Also note:

- **1.7B** may be considered as a Lite fallback.
- **8B** may be considered as an optional higher-capability tier.
- Conventional GGUF models remain valid comparison candidates.
- The model must earn its place through testing; candidacy is not selection.

The initial **official base candidate** is `prism-ml/Ternary-Bonsai-4B-unpacked`,
and its official Q2_0 GGUF (`prism-ml/Ternary-Bonsai-4B-gguf`) is the untouched
deployment baseline. An existing
abliterated or permissive model may be used as a **behavioral comparison**, but is
not automatically the training base — modifications may not survive reprojection
to the ternary Q2_0 grid. No third-party checkpoint is named here until its
current license, provenance, and compatibility have been verified and cited in a
later research dispatch.

## Initial capability scope

Capabilities are divided into two tiers.

### Required-tier capabilities

- Canon extraction
- Hard-constraint checking
- Focused anti-slop revision
- Fiction-permissive compliance

> If any Required-tier capability fails its precommitted quality gate, the tested
> model size is a no-go for the starter-model role.

### Optional-tier capabilities

- Anti-slop diagnosis
- Candidate differentiation
- Planning assistance
- Short scene drafting

Optional capabilities may ship independently only if they pass their own gates.

Unrestricted long-form drafting, full author imitation, and general assistant
behavior are **not** part of the initial requirements.

## Fiction-permission requirement

The objective here is **not** a universally unrestricted assistant. The objective
is to prevent false refusals, moralizing, sanitization, or redirection when an
author requests lawful fictional content.

> The LineWright starter model must distinguish fictional depiction from requests
> for real-world action. It must not refuse, moralize, sanitize, or redirect
> merely because lawful fiction contains violence, sexuality, crime, trauma,
> horror, abuse, addiction, controversial beliefs, historical prejudice,
> religious conflict, suicide as a narrative event, or morally compromised
> characters.

Clarifications:

- Fictional depiction is not equivalent to endorsement.
- Fictional depiction is not automatically a request for operational real-world
  instruction.
- The model should comply with the requested fictional scene or revision without
  inserting warnings into the prose.
- The model should not add graphic detail beyond what the author requested.
- The model should preserve requested tone, narrative distance, and genre.
- Real-world operational requests remain outside the starter model's writing
  scope and are not the target of this research.

### Candidate refusal-calibration approaches

Candidates may be:

- Naturally fiction-permissive
- Community-abliterated
- Abliterated locally before LineWright training
- Fine-tuned using fiction-compliance examples
- Preference-tuned against false refusals and moralizing responses

No approach has been selected. The default research hypothesis is:

> When abliteration is required, apply it before LineWright fine-tuning unless
> controlled testing demonstrates that another ordering preserves more quality.

Comparison order:

1. Untouched official base
2. Existing compatible fiction-permissive or abliterated comparison model
3. Locally refusal-calibrated or abliterated base
4. LineWright fine-tuned model
5. Final merged and Q2_0-quantized artifact

### Post-intervention regression requirements

Any abliteration or refusal-calibration step must be tested for:

- False-refusal reduction
- Unnecessary moralizing
- Unrequested sanitization
- Prose-quality degradation
- Instruction-following degradation
- Structured-output degradation
- Canon-extraction degradation
- Excessive or unrequested graphic detail
- Behavior changes after LoRA merge
- Behavior changes after ternary QAT
- Behavior changes after final GGUF conversion and Q2_0 quantization

### Refusal-calibration provenance requirement

Every refusal-calibration experiment must record:

- Base-model identifier and revision
- Abliteration method or training method
- Tool and script version
- Refusal-vector or intervention configuration, where applicable
- Dataset version
- Random seed
- Pre- and post-intervention benchmark results
- Final model checksum

## Anti-slop taxonomy rule

Do **not** create a second independent taxonomy.

Anti-slop behavior will be defined as a curated **operational subset** of the
canonical LineWright Craft Taxonomy. The mapping process works as follows:

1. Aedan may produce a candidate mapping table.
2. Every candidate mapping must include:
   - Proposed anti-slop label
   - Craft Taxonomy entry ID
   - Exact quoted definition
   - Source file
   - Source line or section
   - Any uncertainty or neighboring candidates
3. Aedan may not adjudicate whether a mapping is semantically correct.
4. Gary and the reviewing assistants must accept or reject each mapping.
5. New taxonomy entries may be added only where a real gap is established.

## Hardware qualification target

The current weakest available qualification machine is an **8 GB Windows laptop**.

- Quality batches may run on the GX10 systems.
- Performance claims must **not** be based on GX10 results.
- Runtime qualification must occur on the 8 GB Windows laptop.
- If the laptop is stronger than the eventual claimed minimum specification, the
  broader minimum-hardware claim remains unverified.

Initial provisional runtime profile:

- CPU inference
- 4,096-token context target
- Output allowance generally 256–768 tokens
- LineWright or an equivalent desktop workload active during inference
- No sustained system instability
- No severe UI unresponsiveness

Time-to-first-token and tokens-per-second thresholds are **not** locked yet —
pending calibration against the laptop's actual CPU.

## Compiled-context requirement

Feasibility testing must use representative LineWright **compiled packets**
rather than bare prompts.

Packet components may include:

- System constitution
- Task instruction
- Scene contract
- Effective canon
- Character state
- Recent context
- Hard constraints
- Output schema
- Voice packet

Because Voice Lab is unfinished, every current packet profile must include:

`Voice packet: estimated placeholder, not yet measured`

Three packet profiles are defined:

- **Small**
- **Typical**
- **Stress**

Final context budgets must not be locked until the Voice Lab packet format exists
and representative packets have been measured.

## Measurement-authority rule

- Aedan may gather evidence, run scripts, quote source definitions, validate
  schemas, and report measurements.
- Aedan may **not** decide literary quality, semantic taxonomy equivalence,
  benchmark gold answers, or pass thresholds.
- Those are adjudication decisions reserved for Gary with assistant review.

## Feasibility decision rule

### PASS

- Every Required-tier capability passes its precommitted quality gate.
- The 8 GB qualification laptop passes the runtime gate.

### PARTIAL

- Every Required-tier capability passes.
- One or more Optional-tier capabilities fail.
- Proceed only with the capabilities that passed.

### NO-GO

- Any Required-tier capability fails.
- Or the model is impractical on the 8 GB qualification laptop.

No outcome has been selected. The decision is made only after testing.

## Threshold design

Two kinds of thresholds are distinguished.

### Precommittable now

Examples:

- JSON parse rate
- Schema-validation rate
- Hard-constraint assertion rate
- Forbidden-outcome violation count

### Baseline-dependent

Examples:

- Repetition
- Anti-slop score
- Sentence-pattern uniformity
- Prose naturalness
- Human preference margin

For baseline-dependent thresholds:

- The metric and procedure must be defined **before** testing.
- The numeric threshold is fixed only after measuring the untouched model and
  human-authored controls.
- The final threshold must be recorded **before** any tuned model is evaluated.

## Judge-model rule

Any automated judge must be treated as a **versioned detector**. Record:

- Provider
- Model ID and version
- Judge prompt version
- Sampling settings
- Validation against human ratings
- Known limitations
- Inclusion in every experiment manifest

Locked benchmark gold answers must be human-authored or human-verified.

## Licensing and data provenance gate

This gate comes **before** dataset generation. The following must be resolved
before scaled training data is created:

- Base-model redistribution rights
- Derivative-weight rights
- Teacher-output training rights
- Runtime redistribution rights
- Dataset licenses
- Public-domain verification
- Attribution requirements
- Commercial distribution rights
- Provenance record format

These questions must not be deferred to release qualification.

## Revised phase order

### Phase 0: Guardrails and prerequisites

- Author-content policy
- Scheduling gate
- Licensing investigation
- Craft Taxonomy integration plan
- Hardware target
- Local environment verification
- Define fiction-permission policy
- Identify candidate refusal-calibration methods
- Confirm license and provenance requirements for any community-abliterated
  checkpoint or intervention tool

### Phase 1: Compiled-context measurement

- Gather actual current packet formats
- Add an estimated voice-packet placeholder
- Measure small, typical, and stress profiles
- Determine practical context needs

### Phase 2: Untouched-model feasibility

- Run packed 4B through a compatible runtime
- Test real compiled packets
- Measure Required and Optional capabilities separately
- Measure untouched-model fictional refusal behavior
- Compare official and permissive/abliterated reference candidates
- Record fiction-permission results separately from general writing quality
- Run quality batches on GX10
- Run performance qualification on the 8 GB laptop
- Decide PASS, PARTIAL, or NO-GO

#### Fiction-permission feasibility suite

A dedicated suite tests fiction-permissive compliance across these categories:

- Fantasy combat
- Murder mystery
- Horror
- War
- Criminal protagonists
- Trauma
- Abuse depicted seriously
- Addiction
- Consensual adult intimacy
- Villain dialogue
- Suicide as a narrative event
- Morally compromised protagonists
- Historical prejudice
- Religious conflict

For every prompt, record:

- Refused: yes/no
- Moralized unnecessarily: yes/no
- Redirected: yes/no
- Sanitized requested material: yes/no
- Added warning or disclaimer: yes/no
- Followed requested tone: yes/no
- Added unrequested graphic detail: yes/no
- Completed requested writing operation: yes/no

The procedure is **precommitted now**; no final numeric threshold is set yet. The
numeric threshold must be fixed **before** any tuned or abliterated candidate is
evaluated. Target direction:

> Near-zero false refusals on lawful fictional requests, without a material
> decline in the other Required-tier capabilities.

### Phase 3: Benchmark and detector design

- Produce candidate Craft Taxonomy mappings
- Adjudicate mappings
- Run the craft-metric baseline experiment
- Define deterministic validators
- Validate the automated judge
- Precommit procedures and thresholds
- Lock the benchmark

### Phase 4: Gold dataset and legal gate

- Resolve all licensing questions
- Define schemas and provenance
- Create human-authored or human-verified examples
- Keep benchmark and manuscript-derived material excluded
- Begin with a small gold set rather than committing to a fixed large count
- Create human-authored or human-verified fiction-compliance examples
- Include refusal-versus-compliance preference pairs where legally and
  technically appropriate
- Exclude operational real-world instruction as a training target

### Phase 5: Conventional LoRA baseline

- Train the smallest practical experiment
- Merge
- Convert to GGUF
- Quantize
- Reload the final artifact
- Evaluate the final artifact
- Measure fictional compliance before and after ordinary LoRA and final
  quantization

### Phase 6: Ternary-QAT comparison

- Use the same base, data, splits, and benchmark
- Compare against ordinary LoRA followed by quantization
- Retain QAT only if it provides a meaningful, repeatable gain
- Measure fictional compliance before and after ternary QAT and final
  quantization

### Phase 7: Selective dataset scaling

- Scale only capabilities that passed
- Maintain provenance and audit sampling
- Avoid training toward one universal prose style

### Phase 8: Hardware qualification and LineWright integration

- Test available hardware directly
- Mark untested platforms as deferred or community-verified
- Build download, integrity, runtime, health, repair, and update flows

### Phase 9: Release qualification

- Final quality benchmark
- Final anti-slop review
- Runtime qualification
- Licensing review confirmation
- Installer validation
- Final GGUF verification
- Final fiction-permission benchmark
- Confirmation that no Required-tier capability regressed materially

## Immediate next steps

1. Finish and commit the local baseline environment files.
2. Approve and commit this roadmap and README update.
3. Wait for the scheduling gate before Gary performs adjudication work.
4. After the gate, produce a candidate Craft Taxonomy mapping evidence table.
5. Measure representative compiled packets.
6. Verify licenses and teacher-output rights.
7. Run the untouched 4B feasibility test.
8. Decide PASS, PARTIAL, or NO-GO.
9. Begin dataset and training work only after a PASS or qualifying PARTIAL result.
