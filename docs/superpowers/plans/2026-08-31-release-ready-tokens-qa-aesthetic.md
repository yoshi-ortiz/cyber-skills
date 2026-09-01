# Release-Ready Tokens QA and Aesthetic Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a universal, prompt-driven Shot QA control plane whose first complete adapter turns the rejected landing-page graphics round into a browser-proven candidate that remains gated on explicit user acceptance.

**Architecture:** Tokens QA owns modality-neutral record, validation, observation, feedback evidence, bounded correction, and candidate comparison through a structured CLI. Domain adapters own corpus interpretation, execution, artifacts, and modality-specific proof; aesthetic is the first full adapter and regression fixture. Cook normalizes host evidence and invokes the CLI once per run, while alpha publication keeps the coordinated system away from `main` until the failed Shot earns L3 acceptance.

**Tech Stack:** Python 3 standard library, JSON/JSONL, filesystem atomic replace, UUIDv4, existing Node/browser companion, existing publication tooling.

**Spec:** `QA.md`, `docs/SPEC/SHOT_OBSERVATION.md`, and `spec/design-harness/brief.json`

## Global Constraints

- `QA.md` is universal; it may not name aesthetic, graphics, a ranking page, or a repository-specific corpus layout.
- Tokens QA never reads hidden reasoning and never interprets a domain artifact.
- Adapters own domain semantics and L2 proof; tokens-qa validates declared descriptors.
- `status`, `correction`, `sentiment`, and `rank` are independent fields; advisory inference never writes authority or auto-accepts.
- L3 rejection or correction wins regardless of changed files, tokens spent, L1 gates, or L2 proof.
- Large artifacts are path-first and streaming-hashed; inline JSON/text is limited to 65,536 encoded bytes.
- Standard library only under `check/tokens-qa/scripts/`, `cook/`, `first/aesthetic/scripts/`, and `tools/`.
- Preserve existing public command behavior through explicit schema migration or compatibility flags; never silently reinterpret a v1 record.
- Release the coordinated change to `alpha`; keep `main` unchanged until explicit L3 acceptance.
- The 30 KB source-module contract is modularity debt, not package context or Shot quality.
- Write a failing behavioral test and observe the intended failure before every production behavior change.

---

## What already exists

- `check/tokens-qa/scripts/shot_contract.py` and `shot_contract_fixtures.json` provide the committed first modality-neutral boundary (`36c40b5`); extend them instead of introducing another schema.
- `check/tokens-qa/scripts/tokens_qa.py` already records, observes, compares, and attaches feedback, but hard-codes a text adapter and embeds complete text output.
- `cook/qa.py` already scopes transcripts, extracts slash-command arguments, detects changed files and commits, and reads exact user words; retain host normalization but move all classification into tokens-qa.
- `first/aesthetic/scripts/graphics_flow.py` already models one next action and stale artifact hashes; extend its table with correction and delivery-proof states.
- `first/aesthetic/scripts/review_delivery.py` already produces canonical browser review images and avoids partial publication; make its output the adapter proof descriptor.
- `first/aesthetic/scripts/deliver.py` already sequences validate, publish, open, and review delivery; add Shot recording at this boundary.
- `tools/publish.py`, `tools/fog.py`, `tools/release.py`, and `tools/check.py` already implement channel generation and verification; reuse them.
- `.audit/shots/20260901T025137Z-a7052318.json` is the rejected regression baseline and must remain immutable.

## System flow

```text
host transcript + project artifacts
              |
              v
   Cook host normalizer (streaming)
              |
              | one JSON evidence bundle / one subprocess
              v
        tokens-qa universal CLI
   +----------+----------+-----------+
   | record   | observe  | feedback  | compare
   +----------+----------+-----------+
              |
              | bounded correction bundle
              v
      domain adapter: aesthetic
   corpus -> refine -> deliver -> browser proof
              |
              v
       candidate Shot: pending
              |
              v
       explicit L3 user verdict
```

Add this condensed diagram as an inline comment above the CLI subparser construction in `tokens_qa.py` and above `FLOW` in `graphics_flow.py`; update both whenever a state or command changes.

## Shot state machine

```text
recorded/pending
   | observe + hard veto ----------> noncompliant
   | exact correction/rejection ---> failed
   | bounded correction -----------> refine-required
   | candidate + machine proof ----> pending (never accepted)
   ` explicit L3 acceptance + no veto -> compliant
```

## NOT in scope

- Ranking-page product redesign — the user explicitly excluded the half-built ranking app; only actual-thumbnail proof needed by the landing Shot is included.
- Production adapters beyond aesthetic — contract fixtures prove modality neutrality; a `knowledge` adapter is captured as a P2 follow-up in `TODOS.md`.
- Persistent tokens-qa daemon — one subprocess per Cook run is sufficient and avoids lifecycle state.
- Object storage or artifact copying — local path descriptors and hashes are enough for this repo-agnostic contract.
- Automated taste scoring — machine checks prove artifact identity and renderability, never aesthetic acceptance.
- Sprite-sheet/cartoon exploration unrelated to the failed hero — only defects that block fresh hero and thumbnail proof are included.

## Failure modes and required coverage

| Path | Realistic failure | Test | Handling and user-visible result |
| --- | --- | --- | --- |
| Schema load | Unknown version or malformed nested field | `test_shot_contract.py` migration/invalid matrices | Exit 2 with exact JSON path; no traceback |
| Artifact record | Binary/large file decoded as UTF-8 or loaded whole | CLI integration with a binary fixture and >64 KiB inline payload | Path-first descriptor; oversize inline rejected clearly |
| Create/update | Concurrent records collide or `.tmp` files overwrite | concurrent subprocess integration | UUID + exclusive create + unique same-dir temp; exit 4 on conflict |
| Feedback | “not bad” becomes rejection or “no changes needed” becomes correction | adversarial English/Spanish table | Advisory candidate only; authoritative fields unchanged |
| Cook transcript | Old session words contaminate latest run | two-run JSONL fixture | Two-pass latest-run streaming; result names transcript and marker |
| Cook boundary | Private import passes locally but fails from repo root | root-launched subprocess test | One public CLI call; exit 5 diagnostic on subprocess failure |
| Correction | Whole skill rewrite leaks into adapter | bounded correction fixture | Bundle contains exact evidence, scope, findings, artifact refs only |
| Graphics flow | Structural gates report `done` without visual proof | `test_graphics_flow.py` stale/missing proof cases | `verify-delivery`, never `done` |
| Proof cache | CSS/viewport changes reuse stale screenshot | proof-key mutation table | Cache invalidates on every declared input hash |
| Browser render | Server/browser times out | delivery integration | Atomic cohort publish aborts; clear timeout diagnostic |
| Candidate | L2 proof auto-accepts rejected work | rejected baseline E2E | Candidate remains `pending` until explicit L3 status |
| Publication | Alpha work leaks to main | publication snapshot test | Release command refuses; main tree byte-identical |
| Benchmark | Nine-skill ask-matt flow is described as a package | recursive package fixture | Separate `flow` and `package payload` reports |
| R-15 split | Imports/callers drift during mechanical extraction | characterization suite and 51/51 budget gate | Behavior unchanged; every file below declared cap |

Every listed failure has a planned test and explicit handling; there are no silent unhandled paths in the plan.

## Three-epic delivery plan

### Epic 1 — Quick win: establish honest evidence

**Outcome:** Land the already-complete modality-neutral fixture checkpoint, add a recursive package benchmark, and correct the ask-matt-only budget claim. This epic is deliberately small: it changes no aesthetic runtime behavior and should finish in one short agent session.

**Tasks:** Task 0 and Task 7.

**Exit gate:** Contract fixtures remain green; the benchmark reports `flow path` and `package payload` separately; GOAL/CLAUDE no longer describe a nine-skill workflow as a package comparison.

### Epic 2 — Universal control plane and Cook integration

**Outcome:** Finish the v2 Shot contract, path-first CLI, independent feedback model, bounded correction bundles, and one-batch Cook invocation. At this boundary tokens-qa works for any declared multimodal artifact without importing aesthetic semantics.

**Tasks:** Tasks 1 through 4.

**Exit gate:** Tokens QA schema/CLI/feedback suites are green; Cook runs from the repository root through the public CLI; rejected or corrective evidence cannot be rescued by file churn.

### Epic 3 — Aesthetic dogfood and alpha release

**Outcome:** Repay the shared aesthetic module debt, require adapter-owned browser and thumbnail proof, recover the immutable rejected landing Shot, and publish the coordinated system to alpha.

**Tasks:** Tasks 5, 6, 8, and 9.

**Exit gate:** The new candidate contains fresh hero and actual-thumbnail proof, remains pending until explicit L3 acceptance, the full repository gate is 23/23, and main stays unchanged until promotion.

### Dependency and parallelization strategy

| Step | Modules touched | Depends on |
| --- | --- | --- |
| Universal contract and CLI | `check/tokens-qa/` | committed fixture checkpoint |
| Cook integration | `cook/` | universal CLI |
| Aesthetic correction and proof | `first/aesthetic/`, dogfood `spec/`, `design/` | universal CLI |
| Package benchmark correction | `tools/`, `GOAL.md` | — |
| R-15 mechanical split | `first/aesthetic/scripts/` | —, but merge before aesthetic behavior edits |
| Alpha release | publication tooling and channel state | all behavioral lanes |

- Epic 1 is the quick-win checkpoint and lands first.
- Epic 2 is sequential inside `check/tokens-qa/` and `cook/`: schema → CLI → feedback → Cook.
- Epic 3 starts with the behavior-preserving R-15 split, then runs aesthetic proof → failed-Shot eval → alpha release.
- Conflict flag: R-15 extraction and aesthetic proof both touch `first/aesthetic/scripts/`; never run them concurrently.

## Task 0 [Epic 1]: Preserve the committed universal fixture checkpoint

**Files:**
- Existing commit: `36c40b5`
- Verify: `check/tokens-qa/scripts/shot_contract.py`
- Verify: `check/tokens-qa/scripts/shot_contract_fixtures.json`

**Interfaces:**
- Produces: `validate(record: object, where: str = "$") -> dict`
- Produces: shared valid/invalid modality fixtures consumed by later schema tests

- [x] **Step 1: Define valid text, image, audio, video, and mixed-corpus records.**
- [x] **Step 2: Observe malformed nested records fail before validator changes.**
- [x] **Step 3: Extract strict validation without exceeding the directory budget.**
- [x] **Step 4: Run 13 focused tests and the declaration/budget gates.**
- [x] **Step 5: Commit as `36c40b5 test(tokens-qa): define universal shot contract fixtures`.**

## Task 7 [Epic 1]: Correct package benchmarking without changing Shot QA

**Files:**
- Modify: `tools/token_bench.py`
- Modify: `tools/test_token_bench.py`
- Modify: `GOAL.md`
- Modify: `CLAUDE.md`

**Interfaces:**
- Keeps: `--flow NAME=a,b,c` for one end-to-end route
- Adds: `--package NAME=ROOT` recursive `SKILL.md` inventory
- Separates report labels `always-on description`, `flow path`, and `package payload`

- [x] **Step 1: Write a nested-package fixture proving recursive discovery, disabled invocation, stable ordering, and separate flow/package totals.**
- [x] **Step 2: Run the test and verify current argparse rejects `--package`.**
- [x] **Step 3: Implement recursive package measurement without changing flow arithmetic or using the ask-matt stub threshold in totals.**
- [x] **Step 4: Replace the misleading GOAL claim with both measured surfaces: Matt package 44 skills/4,969 context bytes/179,360 payload bytes (DID NOT REPRODUCE; measured 37/3,047/158,138 upstream today); cyber alpha 9/1,215/37,907 (reproduced exactly); keep ask-matt comparison labeled workflow-only.**
- [x] **Step 5: State explicitly that package payload is not one execution path and R-15 is not a package-token result.**
- [x] **Step 6: Run benchmark tests and both live commands; commit with `fix(bench): compare complete skill packages honestly`.**

## Task 1 [Epic 2]: Version the universal Shot schema and migrate v1

**Files:**
- Modify: `docs/SPEC/SHOT_OBSERVATION.md`
- Modify: `check/tokens-qa/scripts/shot_contract.py`
- Create: `check/tokens-qa/scripts/test_shot_contract.py`
- Modify: `check/tokens-qa/scripts/shot_contract_fixtures.json`

**Interfaces:**
- Consumes: v1 single-output records and committed fixture matrix
- Produces: `CURRENT_VERSION = 2`
- Produces: `migrate(record: object) -> dict`
- Produces: `validate_v2(record: object, where: str = "$") -> dict`
- Produces: `artifact_descriptor(path, role, mime, bytes, sha256) -> dict`

- [ ] **Step 1: Write failing migration and strict-v2 tests.**

```python
def test_v1_path_output_migrates_to_one_v2_artifact():
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    v1 = copy.deepcopy(fixtures["valid"][1]["record"])
    v1["output"]["sha256"] = "sha256:abc"
    migrated = contract.migrate(v1)
    assert migrated["version"] == 2
    assert migrated["output"]["artifacts"] == [{
        "role": "deliverable", "path": "shots/hero.svg",
        "mime": "image/svg+xml", "bytes": 18432,
        "sha256": "sha256:abc"
    }]

def test_v2_refuses_unknown_nested_fields_with_the_exact_path():
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    record = contract.migrate(copy.deepcopy(fixtures["valid"][0]["record"]))
    record["compute"]["tokens"]["surprise"] = 1
    with self.assertRaises(contract.Invalid) as raised:
        contract.validate(record)
    self.assertIn("$.compute.tokens.surprise", str(raised.exception))
```

- [ ] **Step 2: Run `python3 check/tokens-qa/scripts/test_shot_contract.py`; expect failures for missing `migrate` and accepted unknown nested data.**
- [ ] **Step 3: Implement explicit v1→v2 migration and strict v2 validation.**

```python
CURRENT_VERSION = 2

def migrate(record: object) -> dict:
    source = require_object(copy.deepcopy(record), "$")
    version = source.get("version", 1)
    if version == CURRENT_VERSION:
        return validate_v2(source)
    if version != 1:
        raise Invalid(f"$.version: unsupported version {version!r}")
    source["version"] = 2
    source["output"] = migrate_v1_output(source["output"])
    source["inputs"]["corpus_refs"] = [
        {"path": value} if isinstance(value, str) else value
        for value in source["inputs"].get("corpus_refs", [])
    ]
    return validate_v2(source)
```

- [ ] **Step 4: Validate independent feedback fields, findings, passes, gates, nullable token counts, corpus descriptors, artifact arrays, and unknown-field policy.**
- [ ] **Step 5: Run both tokens-qa test files and `python3 tools/check.py tokens-qa`; expect all selected gates green.**
- [ ] **Step 6: Commit with `feat(tokens-qa): version the universal shot contract`.**

## Task 2 [Epic 2]: Make the CLI path-first, typed, and concurrency-safe

**Files:**
- Modify: `check/tokens-qa/scripts/tokens_qa.py`
- Create: `check/tokens-qa/scripts/shot_io.py`
- Create: `check/tokens-qa/scripts/test_tokens_cli.py`
- Modify: `check/tokens-qa/SKILL.md`

**Interfaces:**
- Consumes: `migrate()` and v2 artifact descriptors
- Produces: `record`, `observe`, `feedback`, `assess-feedback`, and `compare` public verbs
- Produces: stable exit codes `0 success`, `1 hard veto`, `2 schema/arguments`, `3 I/O`, `4 write conflict`, `5 adapter/subprocess`
- Produces: optional `--json` diagnostics `{ok, code, error, path, result}`

- [ ] **Step 1: Write failing CLI tests for binary artifacts, 65,537-byte inline data, missing files, permissions, malformed JSON, duplicate creation, and concurrent updates.**

```python
def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, arguments)],
        cwd=PROJECT, capture_output=True, text=True, check=False)

def test_record_hashes_binary_artifact_without_decoding_it():
    artifact = PROJECT / "hero.bin"
    request = PROJECT / "request.txt"
    manifest = PROJECT / "output.json"
    artifact.write_bytes(b"\x00\xffimage")
    request.write_text("render one hero", encoding="utf-8")
    manifest.write_text(json.dumps({"adapter": "graphic", "artifacts": [{
        "role": "deliverable", "path": str(artifact),
        "mime": "application/octet-stream"}]}), encoding="utf-8")
    done = run_cli("record", "first/aesthetic", "--request", request,
                   "--output-manifest", manifest, "--json")
    assert done.returncode == 0
    assert json.loads(done.stdout)["result"]["output"]["artifacts"][0]["bytes"] == 7

def test_inline_payload_over_65536_bytes_is_refused():
    request = PROJECT / "request.txt"
    request.write_text("write one document", encoding="utf-8")
    done = run_cli("record", "first/knowledge", "--request", request,
                   "--inline", "x" * 65537, "--json")
    assert done.returncode == 2
    assert json.loads(done.stdout)["path"] == "$.output.inline"
```

- [ ] **Step 2: Run the new CLI suite and verify failures are behavioral, not import errors.**
- [ ] **Step 3: Add streaming `sha256_file`, bounded inline encoding, UUIDv4 Shot IDs, exclusive `open('x')`, and unique same-directory temporary files followed by `os.replace`.**
- [ ] **Step 4: Catch expected filesystem, JSON, validation, conflict, and adapter errors at `main`; never expose tracebacks for expected failures.**
- [ ] **Step 5: Keep `observe` read-only and return candidate comparison without modifying either Shot.**
- [ ] **Step 6: Run focused tests plus `python3 tools/check.py tokens-qa`; commit with `feat(tokens-qa): harden the public shot CLI`.**

## Task 3 [Epic 2]: Separate authoritative feedback from advisory inference

**Files:**
- Create: `check/tokens-qa/scripts/feedback.py`
- Create: `check/tokens-qa/scripts/test_feedback.py`
- Modify: `check/tokens-qa/scripts/tokens_qa.py`
- Modify: `check/tokens-qa/SKILL.md`

**Interfaces:**
- Produces: `assess(messages: Sequence[str]) -> list[FeedbackCandidate]`
- Produces: `FeedbackCandidate(field, value, confidence, reasons, evidence)`
- Produces: `correction_bundle(shot, evidence, artifacts) -> dict`
- Authoritative `feedback` requires explicit `--status`; assessment never writes the Shot

- [ ] **Step 1: Write the failing adversarial table.**

```python
CASES = {
    "not bad": None,
    "no changes needed, ship it": ("status", "accepted"),
    "good but fix the thumbnail": ("correction", "good but fix the thumbnail"),
    "la miniatura no sirve; cámbiala": ("correction", "la miniatura no sirve; cámbiala"),
    "output is useless": ("sentiment", "negative"),
}
```

- [ ] **Step 2: Verify the current keyword classifier fails at least `not bad`, acceptance containing `no`, and Spanish correction.**
- [ ] **Step 3: Implement conservative advisory candidates with confidence and literal reasons; omit a candidate when ambiguity remains.**
- [ ] **Step 4: Make authoritative feedback accept independent `status`, `correction`, `sentiment`, and `rank` arguments without deriving one from another.**
- [ ] **Step 5: Emit correction bundles containing only Shot ID, bounded scope, exact evidence, present findings, affected artifacts, and observation timestamp.**
- [ ] **Step 6: Run feedback, schema, and CLI suites; commit with `feat(tokens-qa): separate feedback evidence from authority`.**

## Task 4 [Epic 2]: Invoke tokens-qa once from Cook with streaming evidence

**Files:**
- Modify: `cook/qa.py`
- Modify: `cook/test_qa.py`
- Modify: `cook/cook.py`
- Modify: `cook/CONTEXT.md` only if its admitted interface description changes

**Interfaces:**
- Consumes: `tokens_qa.py assess-feedback --evidence <path> --json`
- Produces: one normalized evidence bundle `{transcript, skill, invoked_at, turns, artifacts}`
- Produces: `stream_run(transcript: Path, skill: str = "") -> Iterator[dict]`

- [ ] **Step 1: Write failing repository-root, two-run contamination, large-transcript, subprocess-error, and changed-files-do-not-rescue-rejection tests.**

```python
def user(stamp: str, text: str) -> dict:
    return {"type": "user", "timestamp": stamp,
            "message": {"content": [{"type": "text", "text": text}]}}

def write_two_run_transcript(path: Path) -> Path:
    rows = [
        user("t1", "Base directory for this skill: /skills/aesthetic"),
        user("t2", "the old run is broken"),
        user("t3", "Base directory for this skill: /skills/aesthetic"),
        user("t4", "looks good"),
    ]
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    return path

def test_repository_root_run_uses_the_public_cli():
    done = subprocess.run([sys.executable, "cook/cook.py", "feedback",
                           "--project-root", str(project), "--session", str(log)],
                          cwd=REPO_ROOT, capture_output=True, text=True)
    assert done.returncode == 1
    assert "output is useless" in done.stdout

def test_latest_skill_run_excludes_an_older_complaint():
    with tempfile.TemporaryDirectory() as folder:
        transcript = write_two_run_transcript(Path(folder) / "session.jsonl")
        result = qa.normalized_evidence(transcript)
        assert result["turns"] == ["looks good"]
```

- [ ] **Step 2: Confirm current root discovery fails on ambient `import qa` and the current list parser retains unrelated history.**
- [ ] **Step 3: Remove the `sys.path`/private `tokens_qa` import and every Cook-owned verdict classifier.**
- [ ] **Step 4: Implement two-pass JSONL streaming: locate the latest relevant invocation, then yield subsequent exact user/tool-result evidence.**
- [ ] **Step 5: Write one evidence bundle and invoke tokens-qa once; translate stable exit codes into `CookError` diagnostics.**
- [ ] **Step 6: Run `cd cook && python3 -m unittest test_qa.py`, the repository-root integration, and the Cook gate; commit with `refactor(cook): consume tokens-qa through its CLI`.**

## Task 5 [Epic 3]: Add adapter-owned correction and browser proof to aesthetic

**Files:**
- Modify: `first/aesthetic/scripts/graphics_flow.py`
- Modify: `first/aesthetic/scripts/test_graphics_flow.py`
- Modify: `first/aesthetic/scripts/review_delivery.py`
- Modify: `first/aesthetic/scripts/test_review_delivery.py`
- Modify: `first/aesthetic/scripts/deliver.py`
- Modify: `first/aesthetic/scripts/test_deliver.py`
- Modify: `first/aesthetic/scripts/direction_context.py`
- Modify: `first/aesthetic/references/text-to-graphics.md`
- Modify: `first/aesthetic/SKILL.md`

**Interfaces:**
- Consumes: bounded correction bundle and v2 Shot CLI
- Produces: `proof_key(artifact_hash, viewport, renderer_version, assets_hash, kind) -> str`
- Produces: proof descriptors for `hero-browser-render` and `ranking-thumbnail`
- Adds FLOW actions `apply-correction` and `verify-delivery` before `done`

- [ ] **Step 1: Write failing flow tests for missing correction consumption, missing proof, stale viewport/CSS/renderer proof, blank thumbnail, and browser timeout.**

```python
def test_structural_success_without_delivery_proof_is_not_done():
    step = next_action(_state(deliveryProof={}))
    assert step["action"] == "verify-delivery"

def test_exact_proof_inputs_may_reuse_a_cached_render():
    assert proof_key(**inputs) == proof_key(**inputs)
    changed = {**inputs, "assets_hash": "sha256:new"}
    assert proof_key(**inputs) != proof_key(**changed)
```

- [ ] **Step 2: Verify the current all-green structural state returns `done` without browser/thumbnail evidence.**
- [ ] **Step 3: Add correction-bundle admission to `direction_context.py` ahead of optional doctrine and route it to existing refine references.**
- [ ] **Step 4: Make `review_delivery.py` emit content-addressed proof descriptors from real browser renders; reuse only exact proof keys and publish cohorts atomically.**
- [ ] **Step 5: Make `deliver.py` write the canonical actual Shot through the CLI with hero, review render, thumbnail, hashes, dimensions, viewport, renderer, and gate results.**
- [ ] **Step 6: Remove the landing-page article-shape instruction from reusable `first/aesthetic/SKILL.md`; keep project layout in `spec/design-harness/brief.json`.**
- [ ] **Step 7: Run focused graphics/delivery tests and the browser E2E; commit with `feat(aesthetic): require correction-aware browser proof`.**

## Task 6 [Epic 3]: Recover the rejected landing Shot and hold at pending

**Files:**
- Read-only baseline: `.audit/shots/20260901T025137Z-a7052318.json`
- Modify: `spec/design-harness/scene-spec.json`
- Modify: `spec/design-harness/graphics-manifest.json` only when artifact declarations change
- Modify: `design/landing-flow-hero.html`
- Generate: `design/review/landing.hero.flow.foundation.png`
- Generate: candidate `.audit/shots/<uuid>.json`

**Interfaces:**
- Consumes: exact rejected baseline correction and aesthetic adapter from Task 5
- Produces: one materially changed hero, real ranking thumbnail proof, and pending candidate comparison

- [ ] **Step 1: Add the rejected baseline to an eval harness that asserts `failed`, exact correction preservation, and absent/insufficient visual proof.**
- [ ] **Step 2: Run the eval and verify it fails because the current Shot records a text summary and unchanged artwork.**
- [ ] **Step 3: Run the bounded correction through aesthetic refine; change the actual hero composition and thumbnail crop/scale rather than only card chrome or harness plumbing.**
- [ ] **Step 4: Render the hero at the declared desktop viewport and the exact ranking thumbnail dimensions; inspect both artifacts, not source HTML.**
- [ ] **Step 5: Record the candidate, compare it with the baseline, and assert it remains `pending` despite passing L1/L2.**
- [ ] **Step 6: Present the candidate to the user and attach the exact verdict; do not promote without explicit acceptance.**
- [ ] **Step 7: Commit accepted artifacts and evidence with `feat(aesthetic): recover the rejected landing graphics shot`; if corrected/rejected, repeat Task 6 without changing the control plane.**

## Task 8 [Epic 3]: Repay R-15 as behavior-preserving modularity work

**Files:**
- Modify: `first/aesthetic/scripts/bootstrap_harness.py`
- Create: focused modules under `first/aesthetic/scripts/` for ledger/adoption, preview/browser rendering, board lifecycle, article rendering, and round policy
- Modify: `first/aesthetic/scripts/editorial_workflow.py`
- Create: focused art-direction, editorial-burndown, theme, and corpus modules
- Split: `first/aesthetic/scripts/test_adopt.py`
- Split: `first/aesthetic/scripts/test_article.py`
- Modify imports in existing tests only as required

**Interfaces:**
- Preserves every existing CLI verb, public function used by tests, stdout/stderr contract, and generated artifact bytes unless a characterization test explicitly permits normalization
- Requires every file in `first/aesthetic/scripts/` below 30,000 bytes

- [ ] **Step 1: Capture current CLI help, self-test output, representative rendered article hashes, public imports, and full unit results as characterization fixtures.**
- [ ] **Step 2: Extract ledger/adoption functions (`canonical_json` through `adopt_companion`) behind re-exported names; run characterization and unit tests.**
- [ ] **Step 3: Extract browser preview/proof functions (`find_chrome` through `render_feedback_controls`) into focused modules no larger than 30 KB; run tests.**
- [ ] **Step 4: Extract board lifecycle, round policy, and article rendering so `bootstrap_harness.py` retains CLI composition, init, validation, and self-test only.**
- [ ] **Step 5: Split `editorial_workflow.py` by art direction, burndown, theme, and corpus while keeping its command facade stable.**
- [ ] **Step 6: Split `test_adopt.py` by event semantics/rendering and `test_article.py` by layout/preview/host behavior; do not weaken or delete assertions.**
- [ ] **Step 7: Run `python3 -m unittest discover -s first/aesthetic/scripts -p 'test_*.py'`, self-test, and `contracts.py --only budget`; require 51/51 with zero oversized files.**
- [ ] **Step 8: Commit independently as `refactor(aesthetic): split oversized harness modules`.**

## Task 9 [Epic 3]: Close release wiring and publish alpha

**Files:**
- Modify: `tools/fog.py`
- Modify: `tools/test_fog.py`
- Modify: `tools/check.py` only for stable timeout/diagnostic behavior
- Modify: kit/sync installation wiring needed to close B-027
- Update: `BUGS.md`, `ROADMAP.md`, and `CHANGELOG.md` with verified outcomes

**Interfaces:**
- Consumes: accepted candidate and all green gates
- Produces: alpha tree containing coordinated tokens-qa/aesthetic behavior; main tree unchanged

- [ ] **Step 1: Add a consistency test requiring skill-specific fog reasons to equal `ALPHA_SKILLS`; remove the stale aesthetic reason.**
- [ ] **Step 2: Fix the Cook startup timeout as a typed diagnostic/retry boundary, not by silently widening the timeout.**
- [ ] **Step 3: Repair the installed-skill symlink/update path for B-027 and verify a repo change is visible to the dev-installed skill without copying.**
- [ ] **Step 4: Run the full release gate: `python3 tools/check.py`; require 23/23.**
- [ ] **Step 5: Generate and compare both channels; require main byte-identical to its pre-release snapshot and alpha to contain tokens-qa plus the aesthetic adapter.**
- [ ] **Step 6: Run `python3 tools/release.py --channel alpha` only from a clean tree and verify the generated publication.**
- [ ] **Step 7: Update development records with evidence, not planned claims; commit with `release: prepare universal shot QA alpha`.**
- [ ] **Step 8: Promote coordinated paths to main only after the candidate Shot contains explicit L3 `accepted` and no hard veto.**

## Verification matrix

```bash
python3 check/tokens-qa/scripts/test_shot_contract.py
python3 check/tokens-qa/scripts/test_tokens_qa.py
python3 check/tokens-qa/scripts/test_tokens_cli.py
python3 check/tokens-qa/scripts/test_feedback.py
cd cook && python3 -m unittest test_qa.py
python3 -m unittest first/aesthetic/scripts/test_graphics_flow.py
python3 -m unittest first/aesthetic/scripts/test_review_delivery.py
python3 -m unittest first/aesthetic/scripts/test_deliver.py
python3 -m unittest discover -s first/aesthetic/scripts -p 'test_*.py'
python3 tools/test_token_bench.py
python3 first/aesthetic/scripts/contracts.py --root . --only declared
python3 first/aesthetic/scripts/contracts.py --root . --only budget
python3 tools/check.py
```

Manual/eval gates:

- Open the ranking-page URL emitted by delivery and inspect both the desktop hero and actual thumbnail.
- Compare the immutable rejected baseline to the new candidate.
- Confirm the candidate remains pending until the user explicitly accepts it.
- Confirm the alpha tree contains coordinated behavior and the main tree did not change.

## Implementation Tasks

Synthesized from the engineering review. Each task is independently reviewable and uses the detailed task above.

- [x] **T0 (Epic 1, P1, human: ~1h / CC: ~15min)** — Tokens QA — Commit modality-neutral contract fixtures and strict validation.
  - Surfaced by: Test review — universal claims lacked shared modality fixtures.
  - Files: `check/tokens-qa/scripts/shot_contract.py`, `shot_contract_fixtures.json`, `test_tokens_qa.py`
  - Verify: `python3 check/tokens-qa/scripts/test_tokens_qa.py`
- [ ] **T1 (Epic 2, P1, human: ~5h / CC: ~60min)** — Tokens QA — Version the schema, migrate v1, and harden path-first CLI I/O.
  - Surfaced by: Architecture/code quality/performance — text-only records, incomplete nested validation, collisions, and untyped failures.
  - Files: `docs/SPEC/SHOT_OBSERVATION.md`, `check/tokens-qa/scripts/`
  - Verify: schema, CLI, feedback suites plus tokens-qa gate.
- [ ] **T2 (Epic 2, P1, human: ~3h / CC: ~40min)** — Cook — Replace private imports and whole-transcript parsing with one streaming CLI batch.
  - Surfaced by: Architecture/performance — duplicated verdict ownership and unbounded transcript memory.
  - Files: `cook/qa.py`, `cook/test_qa.py`, `cook/cook.py`
  - Verify: Cook unit, root integration, and product gate.
- [ ] **T3 (Epic 3, P1, human: ~6h / CC: ~75min)** — Aesthetic — Consume bounded corrections and require content-addressed browser/thumbnail proof.
  - Surfaced by: Architecture/test review — structural gates falsely reported done while the actual graphic remained unchanged.
  - Files: aesthetic flow, delivery, direction context, skill/reference docs and tests.
  - Verify: focused unit tests and browser E2E.
- [ ] **T4 (Epic 3, P1, human: ~3h plus user review / CC: ~30min)** — Dogfood — Recover the rejected landing Shot and stop at pending L3.
  - Surfaced by: Test review — the real failed Shot is the release regression.
  - Files: `spec/design-harness/`, `design/`, `.audit/shots/`
  - Verify: baseline/candidate eval and explicit user verdict.
- [ ] **T5 (Epic 1, P2, human: ~2h / CC: ~25min)** — Benchmark — Add package measurement and correct ask-matt-only claims.
  - Surfaced by: User correction — the previous “package” conclusion measured one ask-matt workflow.
  - Files: `tools/token_bench.py`, `tools/test_token_bench.py`, `GOAL.md`, `CLAUDE.md`
  - Verify: nested fixture and live flow/package reports.
- [ ] **T6 (Epic 3, P1, human: ~8h / CC: ~90min)** — Aesthetic maintainability — Split four oversized files without behavioral changes.
  - Surfaced by: Code quality — R-15 is a real modularity gate, not package token evidence.
  - Files: `first/aesthetic/scripts/`
  - Verify: full unit/self-test and 51/51 contract budget.
- [ ] **T7 (Epic 3, P1, human: ~3h / CC: ~35min)** — Release — Close fog, Cook startup, dev symlink, and alpha publication gates.
  - Surfaced by: Code quality/release review — stale fog reason, B-027, and 21/23 current gate.
  - Files: tooling, kit sync, and development records.
  - Verify: `python3 tools/check.py` 23/23 and channel comparison.

## Review completion summary

- Step 0: scope accepted as sequenced release units; no scope cut.
- Architecture Review: 7 issues found and resolved.
- Code Quality Review: 7 issues found and resolved.
- Test Review: combined code/user-flow diagram produced; 35 gaps, regressions, or red paths folded into the plan.
- Performance Review: 4 issues found and resolved.
- NOT in scope: written.
- What already exists: written.
- TODOS.md updates: one P2 second-adapter item accepted.
- Failure modes: all identified paths have planned tests and errors; zero silent plan gaps.
- Outside voice: nested Codex skipped under Codex; free in-host challenge folded into sequencing.
- Delivery grouping: 3 epics; Epic 1 is the quick win, Epic 2 completes the universal control plane, and Epic 3 dogfoods and releases it.
- Lake Score: 19/19 substantive recommendations chose the complete option.

## Retrospective learning

Prior work repeatedly improved harness plumbing while leaving the judged graphic unchanged. This plan therefore makes the immutable rejected Shot—not file churn, server health, or structural gates—the release regression. Commit `36c40b5` also demonstrated the safe sequencing pattern: contract fixture red, minimal implementation green, then extraction to remain inside the local module budget.

## GSTACK REVIEW REPORT

| Review | Trigger | Why | Runs | Status | Findings |
|--------|---------|-----|------|--------|----------|
| CEO Review | `/plan-ceo-review` | Scope & strategy | 0 | — | Not run |
| Codex Review | `/codex review` | Independent 2nd opinion | 0 | SKIPPED | Running under Codex; nested pass skipped |
| Eng Review | `/plan-eng-review` | Architecture & tests (required) | 1 | CLEAR | 19 issues, 0 critical gaps |
| Design Review | `/plan-design-review` | UI/UX gaps | 0 | — | Not run |
| DX Review | `/plan-devex-review` | Developer experience gaps | 0 | — | Not run |

**VERDICT:** ENG CLEARED — ready to implement; current code still requires the listed release tasks before shipping.

NO UNRESOLVED DECISIONS
