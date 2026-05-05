#!/usr/bin/env python3
# Last Edited: 2026-04-15
"""Extract text and tables from PDF, DOCX, or TXT files for LLM processing.

Exit codes:
  0  success
  1  extraction failure (unsupported format, scanned PDF with no text layer, etc.)
  2  missing Python dependency — message on stderr describes install command
"""

import argparse
import sys
from pathlib import Path

try:
    import fitz  # pymupdf
    import pdfplumber
    from docx import Document
except ImportError as e:
    sys.stderr.write(
        f"Missing dependency: {e.name}\n"
        f"Install with:\n"
        f"  pip install pymupdf pdfplumber python-docx\n"
        f"  # or: uv pip install pymupdf pdfplumber python-docx\n"
    )
    sys.exit(2)


def _rows_to_markdown(rows):
    """Render a 2D list of cells as a GitHub-flavored Markdown table.

    Rows with mismatched column counts are padded/truncated to the max width.
    """
    cleaned = []
    for row in rows:
        cleaned.append(["" if cell is None else str(cell).replace("\n", " ").strip() for cell in row])
    if not cleaned:
        return ""
    width = max(len(r) for r in cleaned)
    cleaned = [r + [""] * (width - len(r)) for r in cleaned]
    header = cleaned[0]
    body = cleaned[1:] if len(cleaned) > 1 else []
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in header) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def extract_pdf(path: Path) -> str:
    """Extract text + tables from a PDF, preserving reading order.

    Body text comes from pymupdf. Tables detected by pdfplumber are appended
    to their page's output so they stay near their surrounding context.
    Raises RuntimeError if the PDF appears to be scanned (no text layer).
    """
    doc = fitz.open(str(path))
    try:
        pages_out = []
        total_text = 0
        for i, page in enumerate(doc):
            text = page.get_text("text") or ""
            total_text += len(text.strip())
            pages_out.append((i, text))
        if total_text == 0:
            raise RuntimeError(
                "PDF has no extractable text layer — likely scanned. "
                "OCR the document first (e.g., `ocrmypdf in.pdf out.pdf`), then retry."
            )
    finally:
        doc.close()

    tables_by_page: dict[int, list[str]] = {}
    try:
        with pdfplumber.open(str(path)) as pdf:
            for i, page in enumerate(pdf.pages):
                try:
                    tables = page.extract_tables() or []
                except Exception:
                    tables = []
                rendered = [_rows_to_markdown(t) for t in tables if t]
                rendered = [r for r in rendered if r]
                if rendered:
                    tables_by_page[i] = rendered
    except Exception as e:
        sys.stderr.write(f"Warning: pdfplumber table extraction failed ({e}); continuing without tables.\n")

    parts = []
    for i, text in pages_out:
        if text.strip():
            parts.append(text.strip())
        for table_md in tables_by_page.get(i, []):
            parts.append(table_md)
    return "\n\n".join(parts)


def extract_docx(path: Path) -> str:
    """Extract paragraphs and tables from a DOCX file in document order."""
    doc = Document(str(path))
    parts = []
    body = doc.element.body
    for child in body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            text = "".join(node.text or "" for node in child.iter() if node.tag.endswith("}t")).strip()
            if text:
                parts.append(text)
        elif tag == "tbl":
            rows = []
            for tr in child.iter():
                if not tr.tag.endswith("}tr"):
                    continue
                row = []
                for tc in tr.iter():
                    if not tc.tag.endswith("}tc"):
                        continue
                    cell_text = "".join(
                        node.text or "" for node in tc.iter() if node.tag.endswith("}t")
                    ).strip()
                    row.append(cell_text)
                if row:
                    rows.append(row)
            if rows:
                parts.append(_rows_to_markdown(rows))
    return "\n\n".join(parts)


def extract_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract text from PDF/DOCX/TXT.")
    parser.add_argument("input", type=Path, help="Path to input file")
    parser.add_argument("--output", type=Path, default=None, help="Output file (default: stdout)")
    args = parser.parse_args()

    if not args.input.exists():
        sys.stderr.write(f"Input file not found: {args.input}\n")
        return 1

    suffix = args.input.suffix.lower()
    try:
        if suffix == ".pdf":
            text = extract_pdf(args.input)
        elif suffix == ".docx":
            text = extract_docx(args.input)
        elif suffix in (".txt", ".md"):
            text = extract_txt(args.input)
        else:
            sys.stderr.write(
                f"Unsupported format: {suffix}. Supported: .pdf, .docx, .txt, .md\n"
            )
            return 1
    except RuntimeError as e:
        sys.stderr.write(f"Extraction failed: {e}\n")
        return 1
    except Exception as e:
        sys.stderr.write(f"Extraction failed ({type(e).__name__}): {e}\n")
        return 1

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
