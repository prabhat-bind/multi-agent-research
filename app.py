
import html
import io
import os
import re
import textwrap
import time
from datetime import datetime

import streamlit as st
from agents import build_reader_agent, build_search_agent, writer_chain, critic_chain

st.set_page_config(
    page_title="ResearchMind · AI Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═════════════════════════════════════════════════════════════════════
# STYLE  (change --a / --b below to re-colour the whole app)
# ═════════════════════════════════════════════════════════════════════
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;600;800&family=Inter:wght@300;400;500&family=JetBrains+Mono:wght@400;500&display=swap');

:root{ --bg:#07060f; --a:#7c5cff; --b:#22d3ee; --ok:#34d399; --err:#f87171;
       --text:#e9e7f5; --muted:#9a97b5; }

html, body, [class*="css"]{ font-family:'Inter',sans-serif; color:var(--text); }
.stApp{
  color-scheme:dark; background:var(--bg);
  background-image:
    radial-gradient(ellipse 70% 45% at 15% -5%, rgba(124,92,255,.22), transparent 60%),
    radial-gradient(ellipse 60% 40% at 90% 105%, rgba(34,211,238,.14), transparent 55%);
  overflow-x:hidden;
}
#MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stDecoration"]{ display:none !important; }
.block-container{ padding:1rem 3rem 4rem; max-width:1180px; position:relative; z-index:2; }

/* ── 3D perspective grid floor (moves toward you) ── */
.stApp::before{
  content:""; position:fixed; left:-50%; right:-50%; bottom:-8%; height:60vh; z-index:0; pointer-events:none;
  background-image:
    linear-gradient(rgba(124,92,255,.35) 1px, transparent 1px),
    linear-gradient(90deg, rgba(124,92,255,.35) 1px, transparent 1px);
  background-size:60px 60px;
  transform:perspective(500px) rotateX(62deg); transform-origin:center bottom;
  animation:gridmove 5s linear infinite;
  -webkit-mask-image:linear-gradient(to top, rgba(0,0,0,.9), transparent 85%);
          mask-image:linear-gradient(to top, rgba(0,0,0,.9), transparent 85%);
}
@keyframes gridmove{ from{background-position:0 0} to{background-position:0 60px} }

/* ── Hero ── */
.hero{ text-align:center; padding:1.5rem 0 1rem; }
.scene{ width:110px; height:110px; margin:0 auto 1.8rem; perspective:600px; animation:bob 4s ease-in-out infinite; }
.cube{ width:110px; height:110px; position:relative; transform-style:preserve-3d; animation:spin 14s linear infinite; }
.face{ position:absolute; width:110px; height:110px; border:1px solid rgba(34,211,238,.65);
  background:linear-gradient(135deg, rgba(124,92,255,.28), rgba(34,211,238,.10));
  box-shadow:inset 0 0 25px rgba(124,92,255,.40), 0 0 18px rgba(124,92,255,.25); }
.f1{ transform:rotateY(0deg)   translateZ(55px); }
.f2{ transform:rotateY(90deg)  translateZ(55px); }
.f3{ transform:rotateY(180deg) translateZ(55px); }
.f4{ transform:rotateY(270deg) translateZ(55px); }
.f5{ transform:rotateX(90deg)  translateZ(55px); }
.f6{ transform:rotateX(-90deg) translateZ(55px); }
.core{ position:absolute; inset:33px; border-radius:50%;
  background:radial-gradient(circle, #fff, var(--b) 40%, transparent 72%); animation:pulse 2.4s ease-in-out infinite; }
@keyframes spin{ from{transform:rotateX(-22deg) rotateY(0)} to{transform:rotateX(-22deg) rotateY(360deg)} }
@keyframes bob{ 50%{ transform:translateY(-10px) } }
@keyframes pulse{ 50%{ transform:scale(1.3); opacity:.75 } }

.eyebrow{ font-family:'JetBrains Mono',monospace; font-size:.72rem; letter-spacing:.3em; color:var(--b); margin-bottom:.9rem; }
.hero-title{
  font-family:'Sora',sans-serif; font-weight:800; letter-spacing:-.03em; line-height:1.05;
  font-size:clamp(2.6rem, 6vw, 4.6rem); margin-bottom:.9rem;
  background:linear-gradient(90deg, #fff, #b8a8ff, #22d3ee, #fff); background-size:300% 100%;
  -webkit-background-clip:text; background-clip:text; color:transparent; animation:shine 6s linear infinite;
}
@keyframes shine{ to{ background-position:-300% 0 } }
.hero-sub{ color:var(--muted); font-size:1.02rem; font-weight:300; max-width:540px; margin:0 auto; line-height:1.65; }

/* ── Glass containers (keyed containers) ── */
.st-key-exportcard .stDownloadButton>button{ padding:.65rem .3rem; font-size:.85rem; }
.stDownloadButton>button:disabled{ opacity:.35; box-shadow:none; transform:none; cursor:not-allowed; }
.st-key-inputcard, .st-key-exportcard, .st-key-reportcard{
  background:rgba(255,255,255,.035); border:1px solid rgba(255,255,255,.09);
  border-radius:18px; padding:1.4rem 1.6rem; backdrop-filter:blur(10px);
}
.st-key-reportcard{ border-color:rgba(124,92,255,.35); box-shadow:0 0 40px rgba(124,92,255,.12); }

/* ── Inputs & buttons ── */
.stTextInput label p{ font-family:'JetBrains Mono',monospace !important; font-size:.72rem !important;
  letter-spacing:.15em; text-transform:uppercase; color:var(--b) !important; }
.stTextInput input{ background:rgba(255,255,255,.06) !important; border:1px solid rgba(124,92,255,.35) !important;
  border-radius:12px !important; color:var(--text) !important; padding:.75rem 1rem !important; }
.stTextInput input:focus{ border-color:var(--b) !important; box-shadow:0 0 0 3px rgba(34,211,238,.15) !important; }
.stTextInput input::placeholder{ color:#6b6890 !important; }

.stButton>button, .stDownloadButton>button{
  background:linear-gradient(135deg, var(--a), var(--b)); color:#fff; border:none; border-radius:12px;
  font-family:'Sora',sans-serif; font-weight:600; padding:.7rem 1.4rem;
  box-shadow:0 8px 30px rgba(124,92,255,.35); transition:transform .2s, box-shadow .2s;
}
.stButton>button p, .stDownloadButton>button p{ color:inherit !important; }
.stButton>button:hover, .stDownloadButton>button:hover{
  transform:translateY(-3px) scale(1.01); box-shadow:0 14px 38px rgba(34,211,238,.35); color:#fff; border:none; }
.st-key-chips .stButton>button{
  background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.10); box-shadow:none;
  font-family:'Inter',sans-serif; font-weight:400; font-size:.78rem; padding:.35rem .6rem; color:var(--muted); }
.st-key-chips .stButton>button:hover{ color:#fff; border:1px solid var(--b); box-shadow:none; transform:translateY(-2px); }

/* ── Pipeline step cards (3D tilt) ── */
.section-heading{ font-family:'Sora',sans-serif; font-size:1.2rem; font-weight:700; margin:.2rem 0 1rem; }
.steps{ perspective:900px; }
.step{
  position:relative; overflow:hidden; display:flex; align-items:center; gap:1rem;
  padding:1.05rem 1.3rem; margin-bottom:.85rem; border-radius:16px;
  background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.08); backdrop-filter:blur(10px);
  transform:rotateY(-7deg); transition:transform .35s, border-color .35s, box-shadow .35s;
}
.step:hover{ transform:rotateY(0deg) translateX(6px) translateZ(20px); }
.step.running{ border-color:rgba(34,211,238,.6); animation:glow 1.5s ease-in-out infinite alternate; }
.step.done{ border-color:rgba(52,211,153,.45); background:rgba(52,211,153,.04); }
.step.error{ border-color:rgba(248,113,113,.55); }
@keyframes glow{ from{box-shadow:0 0 8px rgba(34,211,238,.15)} to{box-shadow:0 0 30px rgba(34,211,238,.40)} }
.badge{ flex:none; width:44px; height:44px; border-radius:12px; display:grid; place-items:center; font-size:1.3rem;
  background:linear-gradient(135deg, rgba(124,92,255,.35), rgba(34,211,238,.20)); }
.step.running .badge{ animation:jump 1s ease-in-out infinite; }
@keyframes jump{ 50%{ transform:translateY(-5px) } }
.step-title{ font-family:'Sora',sans-serif; font-weight:600; font-size:.95rem; }
.step-desc{ color:var(--muted); font-size:.78rem; margin-top:.15rem; }
.tag{ margin-left:auto; font-family:'JetBrains Mono',monospace; font-size:.65rem; letter-spacing:.12em; }
.tag.waiting{ color:#6b6890; } .tag.running{ color:var(--b); } .tag.done{ color:var(--ok); } .tag.error{ color:var(--err); }
.bar{ position:absolute; left:0; bottom:0; width:100%; height:2px; background-repeat:no-repeat; background-size:40% 100%;
  background-image:linear-gradient(90deg, transparent, var(--b), transparent); animation:sweep 1.1s linear infinite; }
@keyframes sweep{ from{background-position:-50% 0} to{background-position:150% 0} }

/* ── Stats ── */
.stats{ display:grid; grid-template-columns:repeat(3,1fr); gap:1rem; margin:.5rem 0 1.5rem; perspective:900px; }
.stat{ text-align:center; padding:1.1rem; border-radius:16px; background:rgba(255,255,255,.04);
  border:1px solid rgba(255,255,255,.08); transition:transform .35s; animation:rise .7s both; }
.stat:nth-child(2){ animation-delay:.1s } .stat:nth-child(3){ animation-delay:.2s }
.stat:hover{ transform:rotateX(10deg) translateY(-4px); }
.num{ font-family:'Sora',sans-serif; font-size:1.9rem; font-weight:800;
  background:linear-gradient(90deg, var(--a), var(--b)); -webkit-background-clip:text; background-clip:text; color:transparent; }
.lbl{ font-family:'JetBrains Mono',monospace; font-size:.62rem; letter-spacing:.15em; color:var(--muted); margin-top:.2rem; }
@keyframes rise{ from{ opacity:0; transform:translateY(20px) } to{ opacity:1; transform:none } }

/* ── Tabs & markdown text ── */
.stTabs [data-baseweb="tab"] p{ color:var(--muted); font-family:'Sora',sans-serif; font-weight:600; }
.stTabs [aria-selected="true"] p{ color:#fff; }
.stTabs [data-baseweb="tab-highlight"]{ background:var(--b) !important; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] td, [data-testid="stMarkdownContainer"] th{ color:#d9d6ec; line-height:1.75; }
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] strong{ color:#fff; font-family:'Sora',sans-serif; }
[data-testid="stMarkdownContainer"] a{ color:var(--b); }

.footer{ text-align:center; margin-top:3rem; font-family:'JetBrains Mono',monospace; font-size:.68rem; letter-spacing:.1em; color:#5f5c80; }
@media (prefers-reduced-motion: reduce){ *, *::before, *::after{ animation:none !important; } }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════
# EXPORT ENGINE  (PDF / Word / Excel / PowerPoint / HTML / Markdown)
# Needs: pip install reportlab python-docx openpyxl python-pptx markdown
# ═════════════════════════════════════════════════════════════════════
# Tiny markdown parser (shared by PDF / Word / Excel / PowerPoint)
# ═════════════════════════════════════════════════════════════════════
INLINE = re.compile(r"(\*\*[^*]+\*\*|__[^_]+__|`[^`]+`|\[[^\]]+\]\([^)]+\)|\*[^*\s][^*]*\*)")


def inline_tokens(text):
    """Split a line into (text, kind, url). kind: '' | b | i | c (code) | a (link)."""
    out = []
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            out.append((part[2:-2], "b", None))
        elif part.startswith("__") and part.endswith("__") and len(part) > 4:
            out.append((part[2:-2], "b", None))
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            out.append((part[1:-1], "c", None))
        elif part.startswith("[") and "](" in part:
            m = re.match(r"\[(.+?)\]\((.+?)\)$", part)
            out.append((m.group(1), "a", m.group(2)) if m else (part, "", None))
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            out.append((part[1:-1], "i", None))
        else:
            out.append((part, "", None))
    return out


def plain(text):
    return "".join(t for t, _, _ in inline_tokens(text))


def parse_md(md):
    """Markdown -> blocks: h, p, ul, ol, code, quote, hr, table."""
    blocks, para = [], []
    lines = md.replace("\r\n", "\n").split("\n")
    i = 0

    def flush():
        if para:
            blocks.append(("p", " ".join(s.strip() for s in para)))
            para.clear()

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if s.startswith("```"):
            flush()
            i += 1
            code = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            blocks.append(("code", "\n".join(code)))
            i += 1
            continue
        if not s:
            flush()
            i += 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            flush()
            blocks.append(("h", len(m.group(1)), m.group(2).strip()))
            i += 1
            continue
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            flush()
            blocks.append(("hr",))
            i += 1
            continue
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|?\s*:?-{2,}", lines[i + 1].strip()):
            flush()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                row = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.match(r"^:?-{2,}:?$", c) for c in row):
                    rows.append(row)
                i += 1
            blocks.append(("table", rows))
            continue
        m = re.match(r"^(\s*)([-*+•])\s+(.*)$", ln)
        if m:
            flush()
            blocks.append(("ul", len(m.group(1)) // 2, m.group(3)))
            i += 1
            continue
        m = re.match(r"^(\s*)(\d+)[.)]\s+(.*)$", ln)
        if m:
            flush()
            blocks.append(("ol", len(m.group(1)) // 2, m.group(3), m.group(2)))
            i += 1
            continue
        if s.startswith(">"):
            flush()
            blocks.append(("quote", s.lstrip("> ").strip()))
            i += 1
            continue
        para.append(s)
        i += 1
    flush()
    return blocks


def block_plain(b):
    k = b[0]
    if k == "h":
        return plain(b[2])
    if k in ("p", "quote"):
        return plain(b[1])
    if k == "ul":
        return "• " + plain(b[2])
    if k == "ol":
        return f"{b[3]}. " + plain(b[2])
    if k == "code":
        return b[1]
    if k == "table":
        return "\n".join(" | ".join(plain(c) for c in r) for r in b[1])
    return ""


def sections(md):
    """[(heading, [blocks])] split at every heading."""
    secs, title, cur = [], "", []
    for b in parse_md(md):
        if b[0] == "h":
            if title or cur:
                secs.append((title, cur))
            title, cur = plain(b[2]), []
        else:
            cur.append(b)
    if title or cur:
        secs.append((title, cur))
    return secs


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "research-report"


# ═════════════════════════════════════════════════════════════════════
# PDF  (reportlab)
# ═════════════════════════════════════════════════════════════════════
def _pdf_fonts():
    """Use DejaVu (ships with matplotlib) for wide Unicode support; fall back to Helvetica."""
    try:
        import matplotlib
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        d = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
        for name, f in [("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"),
                        ("DV-I", "DejaVuSans-Oblique.ttf"), ("DV-BI", "DejaVuSans-BoldOblique.ttf"),
                        ("DV-M", "DejaVuSansMono.ttf")]:
            pdfmetrics.registerFont(TTFont(name, os.path.join(d, f)))
        pdfmetrics.registerFontFamily("DV", normal="DV", bold="DV-B", italic="DV-I", boldItalic="DV-BI")
        return "DV", "DV-B", "DV-M", True
    except Exception:
        return "Helvetica", "Helvetica-Bold", "Courier", False


_SWAPS = {"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"', "\u2013": "-",
          "\u2014": "-", "\u2026": "...", "\u00a0": " ", "\u2705": "\u2713", "\u274c": "\u2717"}
_EMOJI = re.compile("[\U00010000-\U0010ffff\ufe0f\u200d\u2600-\u26ff]")


def build_pdf(d):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (HRFlowable, PageBreak, Paragraph, Preformatted,
                                    SimpleDocTemplate, Spacer, Table, TableStyle)

    F, FB, FM, unicode_ok = _pdf_fonts()
    ink, accent, soft = colors.HexColor("#1f1d33"), colors.HexColor("#5b3df5"), colors.HexColor("#6b6890")
    margin = 2.2 * cm
    avail = A4[0] - 2 * margin

    def clean(t):
        t = _EMOJI.sub("", t)
        for a, b in _SWAPS.items():
            t = t.replace(a, b)
        return t if unicode_ok else t.encode("cp1252", "ignore").decode("cp1252")

    def xml(text):
        out = []
        for t, kind, url in inline_tokens(clean(text)):
            t = html.escape(t, quote=False)
            if kind == "b":
                t = f"<b>{t}</b>"
            elif kind == "i":
                t = f"<i>{t}</i>"
            elif kind == "c":
                t = f'<font name="{FM}" size="9" color="#b4235a">{t}</font>'
            elif kind == "a":
                t = f'<a href="{html.escape(url)}" color="#1a56db"><u>{t}</u></a>'
            out.append(t)
        return "".join(out)

    body = ParagraphStyle("body", fontName=F, fontSize=10.5, leading=15.5, textColor=ink, spaceAfter=6)
    sizes = {1: 20, 2: 15, 3: 12.5, 4: 11.5}
    heads = {n: ParagraphStyle(f"h{n}", parent=body, fontName=FB, fontSize=s, leading=s * 1.25,
                               textColor=accent if n <= 2 else ink, spaceBefore=14 if n <= 2 else 10,
                               spaceAfter=6, keepWithNext=1) for n, s in sizes.items()}
    code_st = ParagraphStyle("code", fontName=FM, fontSize=8.5, leading=11, textColor=ink,
                             backColor=colors.HexColor("#f2f1fa"), borderPadding=6, leftIndent=6,
                             spaceAfter=10, spaceBefore=4)
    quote_st = ParagraphStyle("quote", parent=body, leftIndent=14, textColor=soft)
    cell = ParagraphStyle("cell", parent=body, fontSize=9, leading=12, spaceAfter=0)
    cell_head = ParagraphStyle("cellh", parent=cell, fontName=FB, textColor=colors.white)

    def story_for(blocks):
        out = []
        for b in blocks:
            k = b[0]
            if k == "h":
                out.append(Paragraph(xml(b[2]), heads[min(b[1], 4)]))
            elif k == "p":
                out.append(Paragraph(xml(b[1]), body))
            elif k == "ul":
                ind = min(b[1], 3)
                st = ParagraphStyle("ul", parent=body, leftIndent=16 + 14 * ind, bulletIndent=4 + 14 * ind, spaceAfter=3)
                out.append(Paragraph(xml(b[2]), st, bulletText="\u2022"))
            elif k == "ol":
                ind = min(b[1], 3)
                st = ParagraphStyle("ol", parent=body, leftIndent=20 + 14 * ind, bulletIndent=2 + 14 * ind, spaceAfter=3)
                out.append(Paragraph(xml(b[2]), st, bulletText=f"{b[3]}."))
            elif k == "code":
                wrapped = "\n".join(textwrap.fill(ln, 95, replace_whitespace=False, drop_whitespace=False)
                                    for ln in clean(b[1]).split("\n"))
                out.append(Preformatted(wrapped, code_st))
            elif k == "quote":
                out.append(Paragraph("<i>" + xml(b[1]) + "</i>", quote_st))
            elif k == "hr":
                out.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#d5d3e6"),
                                      spaceBefore=6, spaceAfter=10))
            elif k == "table" and b[1]:
                n = max(len(r) for r in b[1])
                data = [[Paragraph(xml(r[c]) if c < len(r) else "", cell_head if ri == 0 else cell)
                         for c in range(n)] for ri, r in enumerate(b[1])]
                t = Table(data, colWidths=[avail / n] * n, repeatRows=1)
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), accent),
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cfcde0")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]))
                out += [t, Spacer(1, 10)]
        return out

    def footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont(F, 8)
        canvas.setFillColor(soft)
        canvas.drawString(margin, 1.2 * cm, clean(f"ResearchMind  |  {d['topic']}")[:90])
        canvas.drawRightString(A4[0] - margin, 1.2 * cm, f"Page {doc_.page}")
        canvas.restoreState()

    title_st = ParagraphStyle("title", parent=body, fontName=FB, fontSize=26, leading=31, textColor=ink, spaceAfter=6)
    sub_st = ParagraphStyle("sub", parent=body, fontSize=10, textColor=soft, spaceAfter=10)

    story = [Paragraph(xml(d["topic"]), title_st),
             Paragraph(clean(f"AI Research Report  |  {d['date']}  |  generated by ResearchMind"), sub_st),
             HRFlowable(width="100%", thickness=2, color=accent, spaceAfter=12)]
    story += story_for(parse_md(d["report"]))
    story += [PageBreak(), Paragraph("Critic Review", heads[1])]
    story += story_for(parse_md(d["critic"]))

    buf = io.BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, leftMargin=margin, rightMargin=margin, topMargin=2 * cm,
                      bottomMargin=2 * cm, title=clean(d["topic"]), author="ResearchMind"
                      ).build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()


# ═════════════════════════════════════════════════════════════════════
# Word  (python-docx)
# ═════════════════════════════════════════════════════════════════════
def build_docx(d):
    from docx import Document
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Cm, Pt, RGBColor

    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)
    for s in doc.sections:
        s.left_margin = s.right_margin = Cm(2.3)

    def runs(par, text, bold=False):
        for t, kind, url in inline_tokens(text):
            if kind == "a" and t != url:
                t = f"{t} ({url})"
            r = par.add_run(t)
            if bold or kind == "b":
                r.bold = True
            if kind == "i":
                r.italic = True
            if kind == "c":
                r.font.name = "Consolas"
                r.font.size = Pt(10)
            if kind == "a":
                r.font.color.rgb = RGBColor(0x1A, 0x56, 0xDB)
                r.underline = True

    def render(blocks):
        for b in blocks:
            k = b[0]
            if k == "h":
                runs(doc.add_heading("", level=min(b[1], 4)), b[2])
            elif k == "p":
                runs(doc.add_paragraph(), b[1])
            elif k == "ul":
                style = "List Bullet" if b[1] == 0 else "List Bullet 2"
                runs(doc.add_paragraph(style=style), b[2])
            elif k == "ol":
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.9 + 0.7 * b[1])
                p.paragraph_format.first_line_indent = Cm(-0.6)
                p.add_run(f"{b[3]}.  ")
                runs(p, b[2])
            elif k == "code":
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.6)
                r = p.add_run(b[1])
                r.font.name = "Consolas"
                r.font.size = Pt(9)
            elif k == "quote":
                runs(doc.add_paragraph(style="Quote"), b[1])
            elif k == "hr":
                p = doc.add_paragraph()
                bd, line = OxmlElement("w:pBdr"), OxmlElement("w:bottom")
                for a, v in (("w:val", "single"), ("w:sz", "6"), ("w:space", "1"), ("w:color", "999999")):
                    line.set(qn(a), v)
                bd.append(line)
                p._p.get_or_add_pPr().append(bd)
            elif k == "table" and b[1]:
                n = max(len(r) for r in b[1])
                t = doc.add_table(rows=len(b[1]), cols=n)
                try:
                    t.style = "Light Grid Accent 1"
                except Exception:
                    t.style = "Table Grid"
                for ri, row in enumerate(b[1]):
                    for ci in range(n):
                        c = t.cell(ri, ci)
                        c.text = ""
                        runs(c.paragraphs[0], row[ci] if ci < len(row) else "", bold=(ri == 0))
                doc.add_paragraph()

    doc.add_heading(d["topic"], 0)
    sub = doc.add_paragraph()
    r = sub.add_run(f"AI Research Report  |  {d['date']}  |  generated by ResearchMind")
    r.italic = True
    r.font.color.rgb = RGBColor(0x6B, 0x68, 0x90)
    render(parse_md(d["report"]))
    doc.add_page_break()
    doc.add_heading("Critic Review", 1)
    render(parse_md(d["critic"]))

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


# ═════════════════════════════════════════════════════════════════════
# Excel  (openpyxl)
# ═════════════════════════════════════════════════════════════════════
def build_xlsx(d):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    wb = Workbook()
    head_fill, head_font = PatternFill("solid", fgColor="5B3DF5"), Font(bold=True, color="FFFFFF")
    wrap = Alignment(wrap_text=True, vertical="top")

    def xl(v):
        if not isinstance(v, str):
            return v
        v = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", v)[:32000]
        return " " + v if v.startswith("=") else v

    def sheet(title, header, rows, widths, first=False):
        ws = wb.active if first else wb.create_sheet(title)
        ws.title = title
        ws.append(header)
        for c in ws[1]:
            c.fill, c.font = head_fill, head_font
        for r in rows:
            ws.append([xl(v) for v in r])
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment = wrap
        for i, w in enumerate(widths):
            ws.column_dimensions[chr(65 + i)].width = w
        ws.freeze_panes = "A2"

    def section_rows(md):
        rows = []
        for title, blocks in sections(md):
            text = "\n".join(t for t in (block_plain(b) for b in blocks) if t)
            if text:
                rows.append((title or "Overview", text))
        return rows or [("Content", plain(md))]

    urls = []
    for u in re.findall(r"https?://[^\s)\]>\"'<]+", d["search"] + "\n" + d["reader"]):
        u = u.rstrip(".,;")
        if u not in urls:
            urls.append(u)

    sheet("Summary", ["Item", "Value"], [
        ("Topic", d["topic"]), ("Generated", d["date"]), ("Duration (seconds)", d["seconds"]),
        ("Report words", len(d["report"].split())), ("Sources found", len(urls)),
        ("Agents", "Search, Reader, Writer, Critic"),
    ], [24, 70], first=True)
    sheet("Report", ["Section", "Content"], section_rows(d["report"]), [32, 110])
    sheet("Critic Feedback", ["Section", "Content"], section_rows(d["critic"]), [32, 110])
    sheet("Sources", ["#", "URL"], [(i + 1, u) for i, u in enumerate(urls)] or [("", "No URLs found")], [6, 110])
    sheet("Raw Research", ["Stage", "Content"],
          [("Search agent output", d["search"]), ("Reader agent output", d["reader"])], [26, 120])

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ═════════════════════════════════════════════════════════════════════
# PowerPoint  (python-pptx) - one slide per report section
# ═════════════════════════════════════════════════════════════════════
def _short(t, n=190):
    t = t.strip()
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"


def _points(blocks, limit=6):
    pts = []
    for b in blocks:
        if b[0] in ("ul", "ol"):
            pts.append(plain(b[2]))
        elif b[0] == "p":
            pts.append(re.split(r"(?<=[.!?])\s", plain(b[1]))[0])
    return [_short(p) for p in pts if p][:limit]


def build_pptx(d):
    from pptx import Presentation
    from pptx.dml.color import RGBColor
    from pptx.enum.shapes import MSO_SHAPE
    from pptx.util import Inches, Pt

    BG, CYAN = RGBColor(0x0B, 0x0A, 0x1A), RGBColor(0x22, 0xD3, 0xEE)
    WHITE, MUTE = RGBColor(0xFF, 0xFF, 0xFF), RGBColor(0xA9, 0xA6, 0xC8)

    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)

    def new_slide():
        s = prs.slides.add_slide(prs.slide_layouts[6])
        s.background.fill.solid()
        s.background.fill.fore_color.rgb = BG
        return s

    def text(s, x, y, w, h, txt, size, color=WHITE, bold=False):
        tf = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)).text_frame
        tf.word_wrap = True
        r = tf.paragraphs[0].add_run()
        r.text, r.font.size, r.font.bold, r.font.name = txt, Pt(size), bold, "Calibri"
        r.font.color.rgb = color

    def accent(s, x, y):
        shp = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(1.3), Inches(0.07))
        shp.fill.solid()
        shp.fill.fore_color.rgb = CYAN
        shp.line.fill.background()

    def content_slide(title, pts, n):
        s = new_slide()
        text(s, 0.7, 0.55, 12, 0.9, _short(title, 70), 32, bold=True)
        accent(s, 0.75, 1.5)
        tf = s.shapes.add_textbox(Inches(0.7), Inches(1.95), Inches(11.9), Inches(4.8)).text_frame
        tf.word_wrap = True
        for i, pt in enumerate(pts):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_after = Pt(12)
            r = p.add_run()
            r.text, r.font.size, r.font.name = "•  " + pt, Pt(20 if len(pts) <= 5 else 18), "Calibri"
            r.font.color.rgb = WHITE
        text(s, 0.7, 6.9, 12, 0.4, f"ResearchMind  |  {n}", 11, MUTE)

    s = new_slide()
    text(s, 0.9, 2.3, 11.5, 2.2, _short(d["topic"], 80), 46, bold=True)
    accent(s, 0.95, 4.35)
    text(s, 0.9, 4.6, 11.5, 0.6, f"AI Research Report  |  {d['date']}", 20, CYAN)
    text(s, 0.9, 6.9, 11.5, 0.4, "Generated by ResearchMind multi-agent system", 11, MUTE)

    n = 2
    for title, blocks in sections(d["report"])[:10]:
        pts = _points(blocks)
        if pts:
            content_slide(title or "Overview", pts, n)
            n += 1
    pts = _points([b for _, bl in sections(d["critic"]) for b in bl], 5)
    if pts:
        content_slide("Critic review", pts, n)

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()


# ═════════════════════════════════════════════════════════════════════
# HTML + Markdown
# ═════════════════════════════════════════════════════════════════════
_HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>__TITLE__</title>
<style>
body{margin:0;background:#f6f5fb;color:#1f1d33;font:16px/1.75 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
header{background:linear-gradient(135deg,#7c5cff,#22d3ee);color:#fff;padding:3rem 1.5rem}
header div,main{max-width:820px;margin:0 auto}
header small{letter-spacing:.2em;opacity:.85}
header h1{margin:.4rem 0 0;font-size:2.2rem;line-height:1.2}
main{background:#fff;margin-top:-1.5rem;margin-bottom:3rem;padding:2rem 2.4rem;border-radius:16px;box-shadow:0 10px 40px rgba(60,40,160,.12)}
h1,h2,h3{color:#3b2bb8;line-height:1.3} a{color:#1a56db}
code{background:#f2f1fa;padding:.1em .35em;border-radius:4px} pre{background:#f2f1fa;padding:1rem;border-radius:8px;overflow:auto}
table{border-collapse:collapse;width:100%} th,td{border:1px solid #d9d7ea;padding:.45rem .7rem;text-align:left} th{background:#5b3df5;color:#fff}
blockquote{border-left:4px solid #22d3ee;margin-left:0;padding-left:1rem;color:#6b6890}
.review{border-top:3px solid #7c5cff;margin-top:2.5rem;padding-top:1rem}
footer{text-align:center;color:#8a87a8;font-size:.8rem;padding-bottom:2rem}
@media print{body{background:#fff} main{box-shadow:none;margin:0}}
</style></head><body>
<header><div><small>AI RESEARCH REPORT  |  __DATE__</small><h1>__TITLE__</h1></div></header>
<main>__REPORT__<div class="review"><h1>Critic Review</h1>__CRITIC__</div></main>
<footer>Generated by ResearchMind</footer></body></html>"""


def build_html(d):
    try:
        import markdown

        def conv(t):
            return markdown.markdown(t, extensions=["tables", "fenced_code", "sane_lists"])
    except ImportError:
        def conv(t):
            return "<pre style='white-space:pre-wrap'>" + html.escape(t) + "</pre>"

    page = (_HTML.replace("__TITLE__", html.escape(d["topic"])).replace("__DATE__", d["date"])
            .replace("__REPORT__", conv(d["report"])).replace("__CRITIC__", conv(d["critic"])))
    return page.encode("utf-8")


def build_md(d):
    return (f"# {d['topic']}\n\n*AI Research Report | {d['date']}*\n\n{d['report']}\n\n---\n\n"
            f"## Critic Review\n\n{d['critic']}\n").encode("utf-8")


# ═════════════════════════════════════════════════════════════════════
# Registry used by app.py
# ═════════════════════════════════════════════════════════════════════
FORMATS = [  # key, button label, extension, mime, builder, pip package
    ("pdf", "📕 PDF", "pdf", "application/pdf", build_pdf, "reportlab"),
    ("docx", "📘 Word", "docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", build_docx, "python-docx"),
    ("xlsx", "📗 Excel", "xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", build_xlsx, "openpyxl"),
    ("pptx", "📙 PowerPoint", "pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation", build_pptx, "python-pptx"),
    ("html", "🌐 HTML", "html", "text/html", build_html, "markdown"),
    ("md", "📝 Markdown", "md", "text/markdown", build_md, ""),
]


def build_all(d):
    """-> {key: (bytes | None, error_message)}. One failing format never breaks the others."""
    d = {**d, "date": datetime.now().strftime("%d %b %Y")}
    out = {}
    for key, _label, _ext, _mime, fn, pip in FORMATS:
        try:
            out[key] = (fn(d), "")
        except ImportError:
            out[key] = (None, f"Missing package. Run: pip install {pip}")
        except Exception as e:
            out[key] = (None, f"{type(e).__name__}: {e}")
    return out


# ═════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════
STEPS = [
    ("search", "🔍", "Search Agent", "Finds recent, reliable sources"),
    ("reader", "📄", "Reader Agent", "Scrapes the best source in depth"),
    ("writer", "✍️", "Writer", "Drafts the full research report"),
    ("critic", "🧐", "Critic", "Reviews and scores the report"),
]
LABELS = {"waiting": "WAITING", "running": "● RUNNING", "done": "✓ DONE", "error": "✕ FAILED"}
EXAMPLES = ["LLM agents 2026", "CRISPR gene editing", "Fusion energy progress"]


def steps_html(states: dict) -> str:
    html = '<div class="steps">'
    for key, icon, title, desc in STEPS:
        s = states.get(key, "waiting")
        bar = '<div class="bar"></div>' if s == "running" else ""
        html += (
            f'<div class="step {s}"><div class="badge">{icon}</div>'
            f'<div><div class="step-title">{title}</div><div class="step-desc">{desc}</div></div>'
            f'<div class="tag {s}">{LABELS[s]}</div>{bar}</div>'
        )
    return html + "</div>"


def to_text(value) -> str:
    return value.content if hasattr(value, "content") else str(value)


def run_pipeline(topic: str, slot) -> dict:
    """Same logic as pipeline.py, but updates the animated cards live."""
    states, out = {}, {}

    def update(step, status):
        states[step] = status
        slot.markdown(steps_html(states), unsafe_allow_html=True)

    t0, current = time.time(), None
    try:
        current = "search"; update(current, "running")
        sr = build_search_agent().invoke({"messages": [
            ("user", f"Find recent, reliable and detailed information about: {topic}")]})
        out["search"] = to_text(sr["messages"][-1].content)
        update(current, "done")

        current = "reader"; update(current, "running")
        rr = build_reader_agent().invoke({"messages": [("user",
            f"Based on the following search results about '{topic}', "
            f"pick the most relevant URL and scrape it for deeper content.\n\n"
            f"Search Results:\n{out['search'][:800]}")]})
        out["reader"] = to_text(rr["messages"][-1].content)
        update(current, "done")

        current = "writer"; update(current, "running")
        combined = (f"SEARCH RESULTS : \n {out['search']} \n\n"
                    f"DETAILED SCRAPED CONTENT : \n {out['reader']}")
        out["writer"] = to_text(writer_chain.invoke({"topic": topic, "research": combined}))
        update(current, "done")

        current = "critic"; update(current, "running")
        out["critic"] = to_text(critic_chain.invoke({"report": out["writer"]}))
        update(current, "done")
    except Exception:
        if current:
            update(current, "error")
        raise

    out["seconds"] = round(time.time() - t0)
    out["topic"] = topic
    return out


@st.cache_data(show_spinner="Preparing downloads…")
def cached_exports(topic, report, critic, search, reader, seconds):
    """Builds every file format once per result (cached, so reruns are instant)."""
    return build_all(dict(topic=topic, report=report, critic=critic,
                          search=search, reader=reader, seconds=seconds))


def use_example(text: str):
    st.session_state.topic = text


st.session_state.setdefault("topic", "")
st.session_state.setdefault("results", None)

# ═════════════════════════════════════════════════════════════════════
# HERO
# ═════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="hero">
<div class="scene"><div class="cube">
<div class="face f1"></div><div class="face f2"></div><div class="face f3"></div>
<div class="face f4"></div><div class="face f5"></div><div class="face f6"></div>
<div class="core"></div>
</div></div>
<div class="eyebrow">MULTI-AGENT AI SYSTEM</div>
<div class="hero-title">ResearchMind</div>
<div class="hero-sub">Four specialised AI agents search, read, write and critique, delivering a polished research report on any topic.</div>
</div>
""", unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════
# INPUT (left)  +  PIPELINE (right)
# ═════════════════════════════════════════════════════════════════════
col_in, _, col_pipe = st.columns([5, 0.4, 4])

with col_in:
    st.markdown('<div class="section-heading">Start a research</div>', unsafe_allow_html=True)
    with st.container(key="inputcard"):
        st.text_input("Research topic", key="topic",
                      placeholder="e.g. Quantum computing breakthroughs in 2026")
        run_clicked = st.button("⚡  Run research pipeline", use_container_width=True)
    with st.container(key="chips"):
        for col, ex in zip(st.columns(len(EXAMPLES)), EXAMPLES):
            col.button(ex, key=f"ex_{ex}", on_click=use_example, args=(ex,), use_container_width=True)

with col_pipe:
    st.markdown('<div class="section-heading">Pipeline</div>', unsafe_allow_html=True)
    pipeline_slot = st.empty()
    done_now = {k: "done" for k, *_ in STEPS} if st.session_state.results else {}
    pipeline_slot.markdown(steps_html(done_now), unsafe_allow_html=True)

# ═════════════════════════════════════════════════════════════════════
# RUN
# ═════════════════════════════════════════════════════════════════════
if run_clicked:
    topic = st.session_state.topic.strip()
    if not topic:
        st.warning("Please enter a research topic first.")
    else:
        st.session_state.results = None
        try:
            st.session_state.results = run_pipeline(topic, pipeline_slot)
        except Exception as e:
            st.error(f"The pipeline stopped with an error: {e}")

# ═════════════════════════════════════════════════════════════════════
# RESULTS
# ═════════════════════════════════════════════════════════════════════
res = st.session_state.results
if res:
    st.markdown('<div class="section-heading" style="margin-top:2rem">Results</div>', unsafe_allow_html=True)
    words = len(res["writer"].split())
    st.markdown(
        f'<div class="stats">'
        f'<div class="stat"><div class="num">4/4</div><div class="lbl">AGENTS COMPLETED</div></div>'
        f'<div class="stat"><div class="num">{words:,}</div><div class="lbl">WORDS IN REPORT</div></div>'
        f'<div class="stat"><div class="num">{res["seconds"]}s</div><div class="lbl">TOTAL TIME</div></div>'
        f'</div>', unsafe_allow_html=True)

    # ── Download panel: PDF · Word · Excel · PowerPoint · HTML · Markdown ──
    st.markdown('<div class="section-heading">Download</div>', unsafe_allow_html=True)
    files = cached_exports(res["topic"], res["writer"], res["critic"],
                           res["search"], res["reader"], res["seconds"])
    slug = slugify(res["topic"])
    with st.container(key="exportcard"):
        for col, (key, label, ext, mime, _fn, _pip) in zip(st.columns(len(FORMATS)), FORMATS):
            data, err = files[key]
            col.download_button(label, data=data or b"", file_name=f"{slug}.{ext}", mime=mime,
                                key=f"dl_{key}", disabled=data is None, help=err or None,
                                use_container_width=True)
    failed = [f"{label}: {files[key][1]}" for key, label, *_ in FORMATS if files[key][0] is None]
    if failed:
        st.caption("Some formats are unavailable.  " + "  ·  ".join(failed))

    tab_report, tab_feedback, tab_sources = st.tabs(["📝 Report", "🧐 Critic feedback", "🔎 Sources"])

    with tab_report:
        with st.container(key="reportcard"):
            st.markdown(res["writer"])
    with tab_feedback:
        st.markdown(res["critic"])
    with tab_sources:
        st.markdown("#### Search results")
        st.markdown(res["search"])
        st.markdown("#### Scraped content")
        st.markdown(res["reader"])

st.markdown('<div class="footer">ResearchMind · LangChain multi-agent pipeline · Built with Streamlit</div>',
            unsafe_allow_html=True)
