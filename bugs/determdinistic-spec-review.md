# deterMDinistic spec review

Reviewed 2026-09-05. No file named deterMDinistic exists in either workspace.
This review covers the closest contract, [Deterministic inference context
compiler](../docs/SPEC/INFERENCE_CONTEXT_COMPILER.md), not an assumed new module.

## Findings

1. **High: deterministic input is undefined.** Step 1 parses informal user intent
   while promising byte-for-byte reproducibility. Separate reviewed structured
   constraints from language interpretation. The compiler must consume the former;
   identical prose alone cannot guarantee identical interpretation.
2. **High: mandatory context overflow has no failure contract.** Step 6 permits
   truncation without defining what happens when corrections, acceptance criteria
   and required evidence exceed budget. Fail explicitly with required/available
   counts; never silently truncate these fields.
3. **Medium: chunk identity is underspecified.** Heading and declaration chunks
   lack rules for duplicate headings, fenced Markdown, Unicode, newline handling,
   source offsets and tie ordering. Define versioned parser/profile identifiers,
   exact input hashes and stable source-relative spans before implementation.
4. **Medium: acceptance conflates independent modules.** Requiring every indexed
   skill and held-out learning improvements makes a minimal compiler inseparable
   from catalog migration and experiments. Split a Markdown chunking slice, a
   deterministic admission slice, then optional learning evaluation.
5. **Medium: outcome accounting can reward survivorship.** Median cost per
   accepted result must include all failed attempts for the same item, distinguish
   unknown telemetry and report unresolved items separately. Shipping is not
   evidence of explicit end-user acceptance.

## Recommended first slice

An optional, standalone Markdown-to-chunks command: text and parser version in;
ordered source spans, hashes and diagnostics out. Fixtures cover duplicate
headings, code fences, CRLF, Unicode, empty input and reproducible serialization.
No network, tokenizer, neural package, Aesthetic import or Genesis dependency.

Genesis remains usable as one prompt. Tokens QA observes item outcomes without
requiring this compiler. These are review findings, not a claim that R-50 or a
separate deterMDinistic product has been implemented or its promoted spec changed.
