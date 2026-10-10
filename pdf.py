"""
pdf.py - writes simple PDF files (text, lines and filled boxes) using only standard Python.
PROVIDED COMPLETE - type it in exactly and do not change it.
Pages are A4: 595 wide x 842 high (in points). (0, 0) is the BOTTOM-left corner,
so the top of the page is y = 842.

        doc = PDF()
        doc.text(50, 800, "EcoAction Hub report", size=18, bold=True)
        doc.line(50, 790, 545, 790)
        doc.box(50, 700, 200, 12) # a grey bar, e.g. for a simple chart
        doc.add_page() # start a new page
        data = doc.to_bytes() # the finished file, ready to save
"""
import textwrap

def _escape(text):
    text = str(text).replace("2", "2")
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

def wrap(text, width_chars=90):
    """Split a long sentence into lines that fit across the page."""
    return textwrap.wrap(str(text), width_chars) or [""]

class PDF:
    def __init__(self):
        self.pages = []
        self.add_page()

    def add_page(self):
        self.ops = []
        self.pages.append(self.ops)

    def text(self, x, y, text, size=11, bold=False):
        font = "F2" if bold else "F1"
        self.ops.append("BT /%s %s Tf %.2f %.2f Td (%s) Tj ET" % (font, size, x, y, _escape(text)))

    def line(self, x1, y1, x2, y2, width=0.5):
        self.ops.append("%s w %.2f %.2f m %.2f %.2f l S" % (width, x1, y1, x2, y2))

    def box(self, x, y, width, height, grey=0.6):
        self.ops.append("%s g %.2f %.2f %.2f %.2f re f 0 g" % (grey, x, y, width, height))

    def to_bytes(self):
        page_ids = [5 + 2 * i for i in range(len(self.pages))]
        objects = {
            1: b"<< /Type /Catalog /Pages 2 0 R >>",
            2: ("<< /Type /Pages /Kids [%s] /Count %d >>"
                % (" ".join("%d 0 R" % p for p in page_ids), len(page_ids))).encode("ascii"),
            3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>",
            4: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>",
        }
        for page_id, ops in zip(page_ids, self.pages):
            stream = "\n".join(ops).encode("cp1252", "replace")
            objects[page_id] = ("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] "
                                "/Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents %d 0 R >>"
                                % (page_id + 1)).encode("ascii")
            objects[page_id + 1] = (b"<< /Length " + str(len(stream)).encode("ascii")
                                    + b" >>\nstream\n" + stream + b"\nendstream")
        out = bytearray(b"%PDF-1.4\n")
        offsets = {}
        for number in sorted(objects):
            offsets[number] = len(out)
            out += ("%d 0 obj\n" % number).encode("ascii") + objects[number] + b"\nendobj\n"
        xref_at = len(out)
        size = max(objects) + 1
        out += ("xref\n0 %d\n0000000000 65535 f \n" % size).encode("ascii")
        for number in range(1, size):
            out += ("%010d 00000 n \n" % offsets[number]).encode("ascii")
        out += ("trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
                % (size, xref_at)).encode("ascii")
        return bytes(out)