---
name: doc-consolidator
description: Use when collapsing many related documents (PDF, DOCX, TXT) into fewer topic-grouped Markdown files for vector store / RAG ingestion — dedupes boilerplate and overlapping content across files while preserving all unique meaning. Triggers include "consolidate these docs", "collapse 50 training docs down to 10", "merge these SOPs", "dedupe across these files", "batch RAG prep". Complements doc-optimizer (which handles single files). Many files in, fewer files out.
user-invocable: true
---

# Document Consolidator for LLM Retrieval

## Running the scripts

`<skill-dir>` below means the folder containing this SKILL.md (announced when the
skill loads). Under a Claude Code plugin install this is the `skills/doc-consolidator`
subfolder of the plugin root; under a manual install it is the skill folder
inside your agent's skills directory. All scripts run via `uv run` —
dependencies resolve automatically (PEP 723).

---

## Overview

Takes N related documents and produces M < N consolidated Markdown files for vector-store ingestion. Every piece of informational content from every source survives, but cross-document boilerplate is deduped and topical overlap is collapsed.

**Typical use case**: customer hands over 50 training docs. Many share boilerplate (safety warnings, company intros, disclaimers). Many cover overlapping topics with slightly different wording. Collapse into ~10 denser, topic-grouped files that are cleaner to chunk and index.

**Single document instead?** Use `doc-optimizer` — it covers the per-file restructuring path. This skill handles the multi-file case and is fully self-contained: doc-optimizer does NOT need to be installed for this skill to work.

## Core Principles

**Preserve all meaning.** Every informational piece from every source survives. If you removed content, an LLM retrieving any single chunk must still have what it needs.

**Chunk independence is the prime directive.** A chunk that says "as described above" or "see Section 3" is useless to retrieval. Every section needs enough context to stand alone.

**Top-level provenance by default; inline source attribution only for conflicts.** Every consolidated file lists every source in its metadata block. Inside the body, individual sections do NOT carry source attribution UNLESS the section preserves a genuine conflict between sources — see Step 5.

## Prerequisites

The bundled script at `<skill-dir>/scripts/extract.py` runs under [uv](https://docs.astral.sh/uv/). uv reads the script's inline dependency declaration and creates an isolated venv on first run — no separate `pip install` step. If `uv` is missing, the user installs it once per machine (see the repo's INSTALL.md). After that, every `uv run …` invocation is self-contained.

## Workflow

### Step 1: Inventory inputs

List all input files. Confirm each has a supported extension (`.pdf`, `.docx`, `.txt`, `.md`). Note file count and any unexpected formats.

### Step 2: Extract and optimize each input file (FAIL-CLOSED)

For every input file, perform three named substeps in order. Do not move to the next file (or to Step 3) until all three substeps complete successfully.

**(a) Extract** — run the extractor:

```bash
uv run "<skill-dir>/scripts/extract.py" <file> --output ./optimized/.intermediates/<name>-extracted.txt
```

The extractor handles PDF (pymupdf + pdfplumber for tables), DOCX, TXT, and MD. Tables are emitted as GitHub-flavored Markdown.

Exit codes: `0` success, `1` extraction failure (unsupported format, scanned PDF with no text layer, corrupt file). On exit `1`, see fail-closed rule below.

**(b) Optimize** — read the `-extracted.txt` from substep (a), apply the per-file restructuring rules below, then WRITE the result to `./optimized/.intermediates/<name>-optimized.md`. The five sub-rules are:

1. **Classify the document.** Pick the right strategy:
   - **SOP / Procedure** — numbered steps, safety warnings, prerequisites. Restructure into clear procedural sections with context headers.
   - **Training Document** — concepts, examples, assessments. Organize by topic with clear concept boundaries.
   - **Knowledge-extraction transcript** (lecture, podcast, expert interview, internal training recording): extract the substance, discard conversational scaffolding (ums, ahs, repetition, off-topic tangents). Preserve speaker attribution only when it adds meaning.
   - **Performance-evaluation transcript** (sales call, customer-service call, coaching mock call, QA review sample): preserve EVERY utterance verbatim with timestamps and speaker labels. Filler words, hesitation, interruptions, exact phrasing ARE the diagnostic data — never paraphrase, dedupe, or "clean up" repetitions. Add a coaching-observations section at the end if useful, but the transcript itself is sacrosanct.
   - **Reference Manual** — dense technical content. Normalize structure; ensure each section is self-describing.
   - **Mixed** — handle each section per its nature.

2. **Clean extraction artifacts.** Strip page numbers, repeating headers/footers, tables of contents, watermarks, and repeated boilerplate (keep one instance only). Fix words split across line breaks (`recon-\nstruct` → `reconstruct`), merged columns, mangled tables, and garbled smart quotes.

3. **Dedupe within this file.** Keep one canonical version of each repeated safety warning, boilerplate paragraph, or definition. For near-duplicates with different wording, keep the clearest version. After removal, every section must still be retrieval-complete on its own.

4. **Add context headers and normalize hierarchy.** Every major section opens with enough context that a cold reader understands what they're looking at: what the section covers, what system/process/domain it relates to, any critical prerequisites. H1 = document title. H2 = major sections. H3 = subsections. Cap at H4 — flatten deeper nesting. Convert implicit prose steps ("Then you would…") into explicit numbered steps. Keep tables as Markdown tables.

5. **Resolve cross-references.** Every "as described above", "see Section 3", "the table below" gets inlined or replaced with enough context to stand alone — chunkers split arbitrarily, so every chunk must be readable cold.

**(c) Confirm** — verify the `-optimized.md` file exists and is non-empty before moving to the next input. If substep (a) or (b) failed for this file, do NOT continue to the next file — fall into the fail-closed rule below.

**Fail-closed on per-file errors.** If *any* file fails extraction or optimization (unsupported format, scanned PDF with no text layer, corrupt file), STOP. List ALL failed files with reasons. Require an explicit user decision before proceeding:

- OCR the failures and retry
- Exclude the failed files (acknowledge content is missing)
- Abort the whole batch

Never silently drop files. The consolidator's meaning-preservation contract covers every input or none.

**Why two folders.** Intermediate `-extracted.txt` and `-optimized.md` files live under `./optimized/.intermediates/` so they're separated from the final consolidated outputs in `./optimized/`. Configure your vector-ingestion pipeline to scan only `./optimized/*.md` (top level) and skip subdirectories — that's the cleanest way to keep intermediates out of your index. (Don't rely on the `.intermediates` dot-prefix for filtering: glob behavior varies across shells, languages, and ingestion libraries; explicit subdirectory skipping is portable.)

### Step 3: Analyze across docs

Read all `-optimized.md` intermediates and identify:

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

- **Carry a metadata block** at the top with full source list, document type, and processing date — see template below.
- **Top-level provenance only**: list every contributing source file in the metadata block. This is the default attribution level.
- **Per-section attribution ONLY where sources conflict**: when you preserve conflicting claims side by side (rather than resolving one), that section MUST carry inline source attribution so the retrieval system can tell which source supports which version. Without inline attribution in conflict sections, a retrieved chunk showing contradictory statements has no way to signal authority.
- **Dedupe cross-file redundancy**: one canonical version of repeated boilerplate, one clear definition per concept, etc.
- **Use chunk-independent sections**: every section opens with enough context to stand alone, normalized hierarchy (H1 title, H2 sections, H3 subsections, cap at H4), tables preserved as Markdown.
- **Preserve every piece of unique meaning** from the sources. This is a hard contract.

Template:

```markdown
# [Theme] — Consolidated

> **Sources**: training-module-3.pdf, sop-calibration-v2.docx, equipment-manual.pdf, ...
> **Type**: Consolidated from [N] source documents | **Processed**: [date]

[2–3 sentence summary of what this consolidated document covers.]

## [Section Title — self-contained]

[Context anchor — what this section is about and how it fits.]

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

Ask the user whether to keep `./optimized/.intermediates/` for inspection or delete it. Recommend delete once the consolidated outputs pass Step 6 verification — the intermediates have served their purpose.

## Output Format

- Final consolidated files: `./optimized/<theme>-consolidated.md`
- Intermediates (until Step 7 cleanup): `./optimized/.intermediates/<name>-extracted.txt` (raw text from extractor) and `./optimized/.intermediates/<name>-optimized.md` (per-file optimization output).
- Only the consolidated files are intended for vector-store ingestion.

## Edge Cases

- **Docs that don't cluster** — keep as standalone consolidated files (1 source in → 1 output out). Don't force-merge unrelated content.
- **Conflicting info across sources** — preserve both with inline source attribution in that section (per Step 5). Do not silently pick a winner.
- **Mixed languages** — cluster by language as well as topic. Don't mix languages within a single merged file.
- **Mixed success/failure in batch extraction** — see the fail-closed rule in Step 2. Never proceed past extraction failures without explicit user decision.
- **Very small input batch** (2–3 docs) — consolidation may not add value. If the docs are already distinct topics, suggest using `doc-optimizer` on each individually instead.
- **Scanned PDFs** — the extractor exits `1` when there's no text layer. Tell the user to OCR first (e.g., `ocrmypdf in.pdf out.pdf`) and retry. Do not fabricate content.
- **Heavy visuals (images, diagrams)** — extract the surrounding text; mark visuals with placeholders like `[Diagram: Equipment Layout — see original document]` so the LLM knows something visual exists there.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Silently dropping a file that failed extraction | FAIL-CLOSED — list failures, pause for user decision |
| Resolving conflicts silently (picking one source as "right") | Preserve both with inline source attribution |
| Putting source attribution on every section | Top-level metadata by default; inline ONLY for conflicts |
| Mixing intermediates and final outputs in `./optimized/` | Intermediates go to `./optimized/.intermediates/` |
| Over-consolidating (merging unrelated topics) | Don't force-cluster; standalone outputs are fine |
| Skipping user approval on the merge plan | Always pause in Step 4 for plan approval |
| Summarizing a transcript instead of preserving it verbatim | For performance-evaluation transcripts, every utterance survives — filler words and all |
