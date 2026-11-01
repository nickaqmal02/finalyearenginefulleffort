"""Convert corpus .md files to PDF via PyMuPDF (same lib family as the ingest loader).

Usage: python md_to_pdf.py <input.md> <output.pdf>
"""
import sys
from pathlib import Path

import fitz  # PyMuPDF


def md_to_pdf(input_path: str, output_path: str) -> int:
    """Render a markdown file to a clean single-flow PDF. Returns page count."""
    source: Path = Path(input_path)
    text: str = source.read_text(encoding="utf-8")

    doc: fitz.Document = fitz.open()
    width: float = 595  # A4 in points
    height: float = 842
    margin: float = 56
    font: str = "helv"
    font_size: float = 11
    line_height: float = font_size * 1.35

    # Pre-wrap: rely on fitz's insert_textbox flow, page by page
    remaining: str = text
    max_width: float = width - 2 * margin
    max_height: float = height - 2 * margin

    while remaining:
        page: fitz.Page = doc.new_page(width=width, height=height)
        rect: fitz.Rect = fitz.Rect(margin, margin, margin + max_width, margin + max_height)
        # insert_textbox returns unused height; negative means it didn't fit
        leftover: float = page.insert_textbox(rect, remaining, fontname=font,
                                              fontsize=font_size, lineheight=line_height,
                                              align=fitz.TEXT_ALIGN_LEFT)
        if leftover < 0:
            # Binary-search the longest prefix that fits on one page
            lo: int = 0
            hi: int = len(remaining)
            while hi - lo > 1:
                mid: int = (lo + hi) // 2
                probe_doc: fitz.Document = fitz.open()
                probe_page: fitz.Page = probe_doc.new_page(width=width, height=height)
                used: float = probe_page.insert_textbox(rect, remaining[:mid], fontname=font,
                                                        fontsize=font_size, lineheight=line_height)
                probe_doc.close()
                if used >= 0:
                    lo = mid
                else:
                    hi = mid
            # Cut back to a line boundary so we don't split mid-line
            fit_len: int = remaining.rfind("\n", 0, lo + 1)
            if fit_len <= 0:
                fit_len = lo
            page.insert_textbox(rect, remaining[:fit_len], fontname=font,
                                fontsize=font_size, lineheight=line_height)
            remaining = remaining[fit_len:].lstrip("\n")
        else:
            remaining = ""

    doc.save(output_path, deflate=True)
    pages: int = doc.page_count
    doc.close()
    return pages


if __name__ == "__main__":
    pages_built: int = md_to_pdf(sys.argv[1], sys.argv[2])
    print(f"OK {sys.argv[2]} ({pages_built} pages)")
