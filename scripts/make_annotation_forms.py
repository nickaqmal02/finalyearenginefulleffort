"""Generate printable annotation forms (PDF) from the blind sample sheets.

Each message = one numbered row with three tick boxes (Positive/Neutral/Negative).
Words, not 0/1/2 — annotators never see the numeric encoding.
Signature block at the foot = the provenance statement on the same sheet.

Usage: venv/bin/python scripts/make_annotation_forms.py
"""
import csv
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

EVAL = Path(__file__).parent.parent / "eval"
OUT_150 = EVAL / "annotation_form_150.pdf"   # classmate + Nik re-label
OUT_100 = EVAL / "annotation_form_100.pdf"   # supervisor

OPTIONS = ["Positive", "Neutral", "Negative"]

STATEMENT = (
    "I confirm that I labelled each message above using only the annotation "
    "guideline provided, without access to any existing labels."
)


def make_form(sample_path: Path, out_path: Path, title: str, rater_line: str):
    with open(sample_path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    c = canvas.Canvas(str(out_path), pagesize=A4)
    w, h = A4
    y = h - 20 * mm
    page = 1

    def header(first=False):
        nonlocal y
        if not first:
            c.showPage()
            page_num[0] += 1
        y = h - 20 * mm  # reset to top of page (was missing -> 1 row/page blowup)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20 * mm, y, title)
        c.setFont("Helvetica", 9)
        c.drawRightString(w - 20 * mm, y - 4 * mm, f"Rater: {rater_line}")
        y -= 11 * mm
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(20 * mm, y, "Tick ONE box per message. Confidential clinic data — do not share.")
        y -= 4 * mm
        c.setFont("Helvetica-Bold", 8)
        c.drawString(20 * mm, y, "Msg")
        c.drawString(34 * mm, y, "Message")
        x_boxes = w - 20 * mm
        for i, opt in enumerate(OPTIONS):
            c.drawRightString(x_boxes - i * 26 * mm, y, opt)
        y -= 2 * mm
        c.setLineWidth(0.5)
        c.line(20 * mm, y, w - 20 * mm, y)
        y -= 6 * mm

    page_num = [1]
    header(first=True)

    box_size = 3.2 * mm
    x_boxes = w - 20 * mm

    for n, row in enumerate(rows, 1):
        if y < 35 * mm:  # leave room for footer/signature on last page
            header()
        # number
        c.setFont("Helvetica", 9)
        c.drawString(20 * mm, y, str(n))
        # message (wrap long text); strip emoji — Helvetica can't render them
        text = row["text"].replace("\n", " ").strip()
        text = "".join(ch for ch in text if ord(ch) <= 0x2FFF)  # drop emoji/CJK-symbol plane
        max_chars = 48  # measured: msg column ~98mm, Helvetica 9pt ~2mm/char
        lines = []
        while text:
            lines.append(text[:max_chars])
            text = text[max_chars:]
        lines = lines[:4]  # cap at 4 lines
        line_h = 4.2 * mm
        ty = y
        c.setFont("Helvetica", 9)
        for line in lines:
            c.drawString(34 * mm, ty, line)
            ty -= line_h
        # boxes (right-aligned under option labels), vertically centered on first line
        for i in range(len(OPTIONS)):
            bx = x_boxes - i * 26 * mm - box_size
            c.rect(bx, y - 0.8 * mm, box_size, box_size, stroke=1, fill=0)
        # advance: lines used + padding (fixes overlap: y already sits on 1st line)
        y -= (len(lines) - 1) * line_h + 6 * mm

    # signature block on final page
    if y < 45 * mm:
        header()
    y -= 8 * mm
    c.setLineWidth(0.8)
    c.line(20 * mm, y, w - 20 * mm, y)
    y -= 7 * mm
    c.setFont("Helvetica-Bold", 10)
    c.drawString(20 * mm, y, "Declaration")
    y -= 6 * mm
    c.setFont("Helvetica", 9)
    words = STATEMENT.split()
    line = ""
    for word in words:
        if len(line) + len(word) > 95:
            c.drawString(20 * mm, y, line)
            y -= 4.5 * mm
            line = ""
        line += word + " "
    c.drawString(20 * mm, y, line)
    y -= 12 * mm
    c.setFont("Helvetica", 9)
    c.drawString(20 * mm, y, "Name: ______________________________")
    c.drawString(110 * mm, y, "Date: ______________")
    y -= 9 * mm
    c.drawString(20 * mm, y, "Signature: __________________________")
    c.setFont("Helvetica", 8)
    c.drawRightString(w - 20 * mm, 12 * mm, f"Page {page_num[0]}")
    c.showPage()
    c.save()
    print(f"Wrote {out_path} ({len(rows)} messages)")


if __name__ == "__main__":
    make_form(EVAL / "sample_150.csv", OUT_150,
              "Sentiri Sentiment Annotation — Sample A (150 messages)",
              "____________________")
    make_form(EVAL / "sample_100.csv", OUT_100,
              "Sentiri Sentiment Annotation — Sample B (100 messages)",
              "____________________")
