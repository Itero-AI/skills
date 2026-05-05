---
name: doc-optimizer
description: Use when preparing a single document (PDF, DOCX, TXT) for RAG pipelines, vector store ingestion, OpenAI file search, Pinecone/Weaviate/Chroma, or any LLM retrieval context. Triggers include "optimize for RAG", "prepare for vector store", "clean up docs for AI", "extract and reformat", "process this SOP/training doc". Produces chunk-independent Markdown. Single file in, single optimized Markdown out — for multi-file batch consolidation, use doc-consolidator instead.
last_edited: 2026-05-05
---

# Document Optimizer for LLM Retrieval

## Overview

Turns one PDF, DOCX, or TXT into a clean, chunk-independent Markdown file ready for vector-store ingestion. The goal: when a chunker splits the output automatically, each chunk should be self-contained and immediately useful to an LLM without needing surrounding context.

**This is not summarization.** Every piece of informational content survives. Structure, redundancy, and noise change — substance does not.

## Prerequisites

The bundled script at `${CLAUDE_PLUGIN_ROOT}/skills/doc-optimizer/scripts/extract.py` needs Python 3.11+ and three libraries:

```bash
pip3 install pymupdf pdfplumber python-docx
# or: uv pip install pymupdf pdfplumber python-docx
```

If `extract.py` exits with code `2`, the deps are missing — show the user the install command, ask if they want to run it, and stop if they decline. Don't work around it.

## Core Principles

**Preserve all meaning.** Every informational piece from the source survives the transformation. If you removed content, an LLM retrieving any single chunk must still have what it needs.

**Chunk independence is the prime directive.** A chunk that says "as described above" or "see Section 3" is useless to retrieval. Every section needs enough context to stand alone.

| Bad | Good |
|---|---|
| "Follow the procedure in Section 2.1" | "Follow the equipment calibration procedure (calibrate the sensor using baseline readings, then verify against the reference standard)" |
| "See the table above for thresholds" | "See the temperature thresholds: 40–60°F nominal, 60–80°F warning, >80°F alarm" |

**Remove noise, not signal.** Strip extraction artifacts and repeated boilerplate. When in doubt, keep it.

## Workflow

### Step 1: Extract text

```bash
python3 ${CLAUDE_PLUGIN_ROOT}/skills/doc-optimizer/scripts/extract.py <input-file> --output /tmp/raw.txt
```

Handles PDF (pymupdf + pdfplumber for tables), DOCX (python-docx), TXT. Tables are emitted as GitHub-flavored Markdown.

Exit codes:
- `0` — success
- `1` — extraction failure (unsupported format, scanned PDF with no text layer, etc.) — message on stderr
- `2` — missing deps (see Prerequisites)

If exit `1` on a PDF, the doc is likely scanned. Tell the user to OCR first (e.g., `ocrmypdf in.pdf out.pdf`) and retry.

### Step 2: Classify the document

Read the extracted text and pick a strategy:

- **SOP / Procedure** — numbered steps, safety warnings, prerequisites. Restructure into clear procedural sections with context headers.
- **Training Document** — concepts, examples, assessments. Organize by topic with clear concept boundaries.
- **Transcript** — two modes, pick the right one:
  - *Knowledge-extraction transcripts* (lectures, podcasts, expert interviews, internal training recordings): extract the substance, discard conversational scaffolding (ums, ahs, repetition, off-topic tangents). Preserve speaker attribution only when it adds meaning (expert vs. question).
  - *Performance-evaluation transcripts* (sales calls, customer-service calls, coaching mock calls, QA review samples): preserve EVERY utterance verbatim with timestamps and speaker labels. The filler words, hesitation, interruptions, and exact phrasing ARE the diagnostic data — they are the reason a coach reviews the call. Do not paraphrase, dedupe, or "clean up" repetitions like "yes this is james speaking on yes this is james." Never remove "okay," "yeah," or back-channel acknowledgments. The call IS the artifact. Add a coaching-observations section at the end if useful, but the transcript itself is sacrosanct.
- **Reference Manual** — dense technical content. Normalize structure, ensure each section is self-describing.
- **Mixed** — handle each section per its nature.

### Step 3: Clean extraction artifacts

Strip:
- Page numbers, repeating page headers/footers, "Page X of Y"
- Table of contents (the structure replaces it)
- Watermarks, draft stamps, copyright/disclaimer boilerplate that repeats throughout (keep ONE instance)
- Excessive whitespace, broken line breaks from column extraction
- Orphaned bullets and formatting garbage

Fix:
- Words split across line breaks (`recon-\nstruct` → `reconstruct`)
- Merged columns from PDF extraction (text from adjacent columns interleaved)
- Mangled table data → clean Markdown tables
- Smart quotes and special characters garbled in extraction

### Step 4: Deduplicate

- **Repeated safety warnings** — keep one canonical version at the top; add "Safety protocols apply throughout" in relevant sections
- **Boilerplate paragraphs** — keep first occurrence, remove copies
- **Repeated definitions** — consolidate into one clear definition
- **Near-duplicates** (same info, different wording) — keep the clearest version

Test: if you removed something, does an LLM retrieving any single chunk still have what it needs? If a safety warning is critical to a specific procedure, keep a brief contextual reference even after deduplication.

### Step 5: Restructure for retrieval

**Add context headers.** Every major section opens with enough context that a cold reader understands what they're looking at: what the section covers, what system/process/domain it relates to, any critical prerequisites.

Example:
```markdown
## Sensor Calibration Procedure — Model X200 Temperature Monitoring System

This procedure covers the monthly calibration of temperature sensors in the X200 monitoring system. Calibration must be performed by certified technicians with access to the reference standard kit (Part #RS-4401).
```

**Normalize hierarchy.** H1 = document title. H2 = major sections. H3 = subsections. Don't go deeper than H4 — flatten if needed.

**Make procedures explicit.** Implicit steps buried in prose ("Then you would…") get extracted into numbered steps.

**Preserve tables.** Keep tabular data as Markdown tables — most chunkers handle them well.

**Group related content.** If the same topic is scattered across the source, consolidate it.

### Step 6: Format output

Write to `./optimized/<descriptive-slug>.md` (create the `optimized/` subfolder alongside the input if missing).

**The filename matters for retrieval.** It ends up as vector-store metadata. When a retrieval agent surfaces a chunk, the filename alone needs to disambiguate it from sibling docs in the index. A name like `EasyHealth_Day1_Training-optimized.md` adds nothing — it just echoes the input. A name like `easyhealth-new-hire-training-day-1-role-kpis-hipaa-tools.md` tells the agent what the chunk is about before it reads a word of content.

**Slug rules:**

- Lowercase, hyphenated, 4–10 meaningful words.
- Lead with the source/owner if it disambiguates (`easyhealth-`, `acme-`).
- Then the doc type (`training-deck`, `call-transcript`, `coaching-reference`, `agent-guide`, `sop`, `script`, `playbook`).
- Then the specific topic/scope (`day-1-onboarding`, `awv-decline-recovery`, `objection-handling`, `mock-call-exercises`).
- For call transcripts, include speakers and outcome: `call-transcript-villa-adams-elevance-declined`.
- Never include `optimized`, `processed`, `final`, `cleaned`, or other process verbs — the `optimized/` folder name conveys that. Wasted token budget on the filename.
- Don't echo the original filename — derive the slug from what the document IS.

**Output template:**

```markdown
# [Document Title — natural-language version of the slug]

> **Source**: [original filename] | **Type**: [SOP/Training/Transcript/Reference] | **Processed**: [date]

[2–3 sentence summary of what the document covers and who it's for — helps the LLM anchor any chunk retrieved from it.]

## [Section Title — descriptive and self-contained]

[Context anchor — what this section is about and how it fits]

[Content...]
```

### Step 7: Quality check

Before delivering:

1. **No lost meaning** — spot-check that substantive source content survived.
2. **Self-contained sections** — pick 2–3 sections at random. Could you understand them without reading anything else?
3. **No orphaned references** — grep for "above", "below", "as mentioned", "see section" in the output. Each hit is a flag to resolve.
4. **Clean Markdown** — no double blank lines, no broken formatting, no extraction artifacts that slipped through.
5. **Tables intact** — any source tables render as Markdown tables.

## Edge Cases

- **Scanned PDFs** — `extract.py` detects an empty text layer and exits `1`. Flag to the user; suggest OCR (`ocrmypdf`). Do not fabricate content.
- **Very short documents (<1 page)** — light cleanup only. Don't over-restructure something already concise.
- **Heavy visuals (images, diagrams)** — extract the text; mark visuals with placeholders like `[Diagram: Equipment Layout — see original document]` so the LLM knows something visual exists there.
- **Other languages** — process in the source language. Don't translate unless asked.
- **Multiple files** — this skill processes one file at a time. For batch consolidation (e.g., 50 docs → 10), use `doc-consolidator`.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Summarizing instead of restructuring | Every informational sentence survives in some form |
| Leaving cross-references intact | Inline the referenced context or add a brief anchor |
| Over-nesting headings (H5, H6) | Cap at H4; flatten deeper nesting |
| Converting tables to prose | Keep tables as Markdown tables |
| Stripping all safety boilerplate | Keep one canonical version; reference it where critical |
