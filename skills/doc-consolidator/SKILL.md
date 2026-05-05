---
name: doc-consolidator
description: Use when collapsing many related documents (PDF, DOCX, TXT) into fewer topic-grouped Markdown files for vector store / RAG ingestion — dedupes boilerplate and overlapping content across files while preserving all unique meaning. Triggers include "consolidate these docs", "collapse 50 training docs down to 10", "merge these SOPs", "dedupe across these files", "batch RAG prep". Complements doc-optimizer (which handles single files). Many files in, fewer files out.
last_edited: 2026-05-05
---

# Document Consolidator for LLM Retrieval

## Overview

Takes N related documents and produces M < N consolidated Markdown files for vector-store ingestion. Same meaning-preservation rules as `doc-optimizer`, plus cross-document deduplication and topical grouping.

**Typical use case**: customer hands over 50 training docs. Many share boilerplate (safety warnings, company intros, disclaimers). Many cover overlapping topics with slightly different wording. Collapse into ~10 denser, topic-grouped files that are cleaner to chunk and index.

## Relationship to doc-optimizer

This skill follows `doc-optimizer`'s per-file rules and bundles its own copy of the same extraction script. The added value is cross-document reasoning: clustering, cross-file dedup, conflict detection, and merged output structure.

If the user has a **single** document, use `doc-optimizer` instead.

## Prerequisites

The bundled script at `${CLAUDE_PLUGIN_ROOT}/skills/doc-consolidator/scripts/extract.py` needs Python 3.11+ and three libraries:

```bash
pip3 install pymupdf pdfplumber python-docx
```

If `extract.py` exits `2`, show the user the install command and stop if they decline.

## Workflow

### Step 1: Inventory inputs

List all input files. Confirm each has a supported extension (`.pdf`, `.docx`, `.txt`, `.md`). Note file count and any unexpected formats.

### Step 2: Extract + optimize each doc (FAIL-CLOSED)

For each input, run:

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-consolidator/scripts/extract.py <file> --output ./optimized/.intermediates/<name>.txt
```

Then apply `doc-optimizer`'s restructuring rules (classify → clean → dedupe → restructure → format) to produce one intermediate optimized Markdown per input at `./optimized/.intermediates/<name>-optimized.md`.

**Fail-closed on per-file errors.** If *any* file fails extraction (unsupported format, scanned PDF with no text layer, corrupt file), STOP. List ALL failed files with reasons. Require an explicit user decision before proceeding:

- OCR the failures and retry
- Exclude the failed files (acknowledge content is missing)
- Abort the whole batch

Never silently drop files. The consolidator's meaning-preservation contract covers every input or none.

**The `.intermediates/` directory matters.** The dot-prefix keeps typical vector-ingestion globs (`./optimized/*.md`) from picking up intermediates alongside final outputs.

### Step 3: Analyze across docs

Read all optimized intermediates and identify:

1. **Thematic clusters** — groups of docs that cover the same subject area.
2. **Cross-file boilerplate** — safety warnings, company intros, disclaimers that repeat across multiple files.
3. **Near-duplicate content** — same information stated in slightly different ways across files.
4. **Conflicts** — same topic, incompatible claims across sources. (These get special handling in Step 5.)

### Step 4: Propose a consolidation plan

Output a structured proposal to the user:

```
N input files → M output files

Cluster A: "Equipment Calibration" (5 sources → 1 output)
  - training-module-3.pdf
  - sop-calibration-v2.docx
  - ...

Cluster B: "Safety Protocols" (8 sources → 1 output)
  ...

Detected conflicts (will carry inline source attribution in merged output):
  - Calibration frequency: training-module-3.pdf says "monthly",
    sop-calibration-v2.docx says "quarterly"
  - ...
```

**Pause for user approval before merging.** The user may want to rebalance clusters, accept or reject the conflict-preservation approach, or adjust the target count.

### Step 5: Merge each cluster

For each approved cluster, produce one Markdown file in `./optimized/` (not `.intermediates/`). Each merged file must:

- **Inherit `doc-optimizer` structure**: metadata block with full source list, context headers per section, chunk-independent sections.
- **Top-level provenance**: list every contributing source file in the metadata block. This is the default attribution level.
- **Per-section attribution ONLY where sources conflict**: when you preserve conflicting claims side by side (rather than resolving one), that section MUST carry inline source attribution so the retrieval system can tell which source supports which version. Without inline attribution in conflict sections, a retrieved chunk showing contradictory statements has no way to signal authority.
- **Dedupe cross-file redundancy**: one canonical version of repeated boilerplate, one clear definition per concept, etc.
- **Preserve every piece of unique meaning** from the sources. This is a hard contract.

Template:

```markdown
# [Theme] — Consolidated

> **Sources**: training-module-3.pdf, sop-calibration-v2.docx, equipment-manual.pdf, ...
> **Type**: Consolidated from [N] source documents | **Processed**: [date]

[2–3 sentence summary of what this consolidated document covers.]

## [Section Title — self-contained]

[Context anchor.]

[Content, deduped across sources...]

## [Conflicting Section — sources disagree]

**Calibration frequency.**

> Source: training-module-3.pdf: "Calibrate monthly under normal operating conditions."
>
> Source: sop-calibration-v2.docx: "Calibrate quarterly; increase to monthly if alarms fire."

[Neutral summary of what's shared, followed by the attributed conflict above.]
```

### Step 6: Verification

For each output file:

1. **No unique content dropped** — spot-check that every source has content reflected somewhere in the merged output (or in another cluster's output).
2. **Chunk-independent sections** — pick 2–3 sections. Could you understand them cold?
3. **Metadata lists every source** — top-level source list is complete.
4. **Conflicts carry inline attribution** — every preserved conflict has per-section source attribution. If a section has no conflict, it should have NO inline attribution (keeps chunks clean).

### Step 7: Intermediate cleanup

Ask the user:

- Keep `./optimized/.intermediates/` for inspection/debugging
- Delete it (recommended once the consolidated outputs pass verification)

Default recommendation: delete. The intermediates served their purpose.

## Output Format

- Final consolidated files: `./optimized/<theme>-consolidated.md`
- Intermediates (until cleanup): `./optimized/.intermediates/<name>-optimized.md`
- Only the consolidated files are intended for vector-store ingestion.

## Edge Cases

- **Docs that don't cluster** — keep as standalone consolidated files (1 source in → 1 output out). Don't force-merge unrelated content.
- **Conflicting info across sources** — preserve both with inline source attribution in that section (per Step 5). Do not silently pick a winner.
- **Mixed languages** — cluster by language as well as topic. Don't mix languages within a single merged file.
- **Mixed success/failure in batch extraction** — see the fail-closed rule in Step 2. Never proceed past extraction failures without explicit user decision.
- **Very small input batch** (2–3 docs) — consolidation may not add value. If the docs are already distinct topics, suggest using `doc-optimizer` on each individually instead.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Silently dropping a file that failed extraction | FAIL-CLOSED — list failures, pause for user decision |
| Resolving conflicts silently (picking one source as "right") | Preserve both with inline source attribution |
| Putting source attribution on every section | Top-level metadata by default; inline ONLY for conflicts |
| Mixing intermediates and final outputs in `./optimized/` | Intermediates go to `./optimized/.intermediates/` |
| Over-consolidating (merging unrelated topics) | Don't force-cluster; standalone outputs are fine |
| Skipping user approval on the merge plan | Always pause in Step 4 for plan approval |
