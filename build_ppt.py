"""
Build Mid-Review PPT: IoT-Based Liver Disease Risk Prediction using Ensemble ML
Clean white theme with muted teal accents (16:9, 14 slides).
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

# ---------------- palette (white & clean, not neon) ----------------
INK    = RGBColor(0x0F, 0x17, 0x2A)   # near-black navy for headings
BODY   = RGBColor(0x33, 0x41, 0x55)   # slate body text
MUTED  = RGBColor(0x64, 0x74, 0x8B)   # secondary text
ACCENT = RGBColor(0x0E, 0x74, 0x90)   # muted teal
ACCENT2= RGBColor(0x15, 0x5E, 0x75)   # darker teal
TINT   = RGBColor(0xF0, 0xF9, 0xFA)   # very light teal card fill
TINT2  = RGBColor(0xF8, 0xFA, 0xFC)   # zebra row fill
LINEC  = RGBColor(0xE2, 0xE8, 0xF0)   # hairline borders
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
RED    = RGBColor(0xB4, 0x3B, 0x3B)
GREEN  = RGBColor(0x1E, 0x7A, 0x46)
AMBER  = RGBColor(0xB7, 0x7A, 0x16)

FONT = "Calibri"

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SLIDE_W, SLIDE_H = 13.333, 7.5

# ---------------- helpers ----------------
def add_slide():
    return prs.slides.add_slide(BLANK)

def _set_text(tf, lines, size=15, color=BODY, bold=False, align=PP_ALIGN.LEFT,
              line_spacing=1.0, space_after=6, anchor=MSO_ANCHOR.TOP):
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    first = True
    for ln in lines:
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.line_spacing = line_spacing
        p.space_after = Pt(space_after)
        # ln can be (text, opts-dict)
        if isinstance(ln, tuple):
            text, opts = ln
        else:
            text, opts = ln, {}
        r = p.add_run(); r.text = text
        r.font.name = FONT
        r.font.size = Pt(opts.get("size", size))
        r.font.bold = opts.get("bold", bold)
        r.font.color.rgb = opts.get("color", color)
        r.font.italic = opts.get("italic", False)

def add_box(slide, x, y, w, h, lines, size=15, color=BODY, bold=False,
            align=PP_ALIGN.LEFT, fill=None, line=None, radius=None,
            anchor=MSO_ANCHOR.TOP, line_spacing=1.0, space_after=6,
            margin=0.12):
    if radius is not None:
        shp = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        try: shp.adjustments[0] = radius
        except Exception: pass
    else:
        shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None:
        shp.fill.background()
    else:
        shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line; shp.line.width = Pt(1.0)
    shp.shadow.inherit = False
    tf = shp.text_frame
    tf.margin_left = Inches(margin); tf.margin_right = Inches(margin)
    tf.margin_top = Inches(margin*0.7); tf.margin_bottom = Inches(margin*0.7)
    _set_text(tf, lines, size=size, color=color, bold=bold, align=align,
              line_spacing=line_spacing, space_after=space_after, anchor=anchor)
    return shp

def add_text(slide, x, y, w, h, lines, size=15, color=BODY, bold=False,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, line_spacing=1.0, space_after=6):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    _set_text(tb.text_frame, lines, size=size, color=color, bold=bold,
              align=align, anchor=anchor, line_spacing=line_spacing, space_after=space_after)
    return tb

PAGE_COUNTER = [0]
def header(slide, kicker, title, page_no):
    """Small accent square + kicker, big title, hairline."""
    sq = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.57), Inches(0.52), Inches(0.16), Inches(0.16))
    sq.fill.solid(); sq.fill.fore_color.rgb = ACCENT; sq.line.fill.background(); sq.shadow.inherit = False
    add_text(slide, 0.82, 0.40, 10.5, 0.32, [(kicker.upper(), {"size": 11, "bold": True, "color": ACCENT})])
    add_text(slide, 0.55, 0.72, 12.2, 0.62, [(title, {"size": 27, "bold": True, "color": INK})])
    ln = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.57), Inches(1.42), Inches(12.2), Pt(1.4))
    ln.fill.solid(); ln.fill.fore_color.rgb = LINEC; ln.line.fill.background(); ln.shadow.inherit = False
    acc = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.57), Inches(1.42), Inches(1.15), Pt(2.6))
    acc.fill.solid(); acc.fill.fore_color.rgb = ACCENT; acc.line.fill.background(); acc.shadow.inherit = False
    footer(slide, page_no)

def footer(slide, page_no):
    add_text(slide, 0.57, 7.08, 9.0, 0.3,
             [("IoT-Based Liver Disease Risk Prediction  •  Mid Review – Individual Project",
               {"size": 9, "color": MUTED})])
    add_text(slide, 12.3, 7.08, 0.55, 0.3, [(str(page_no), {"size": 10, "color": MUTED})],
             align=PP_ALIGN.RIGHT)

def bullet_lines(items, bullet="▪", indent_bullet="–"):
    """items: list of (level, text[, opts])"""
    out = []
    for it in items:
        level, text = it[0], it[1]
        opts = it[2] if len(it) > 2 else {}
        mark = bullet if level == 0 else indent_bullet
        prefix = "" if level == 0 else "      "
        o = {"size": opts.get("size", 15 if level == 0 else 13.5),
             "color": opts.get("color", BODY if level == 0 else BODY),
             "bold": opts.get("bold", False)}
        if level == 0:
            o["color"] = opts.get("color", BODY)
        out.append((f"{prefix}{mark}  {text}", o))
    return out

def make_table(slide, x, y, w, col_widths, headers, rows, font_size=10,
               header_size=10.5, row_h=0.9, header_fill=ACCENT):
    n_r, n_c = len(rows) + 1, len(headers)
    gf = slide.shapes.add_table(n_r, n_c, Inches(x), Inches(y), Inches(w), Inches(row_h * n_r))
    tbl = gf.table
    tbl.first_row = False
    tbl.horz_banding = False
    for i, cw in enumerate(col_widths):
        tbl.columns[i].width = Inches(cw)
    tbl.rows[0].height = Inches(0.42)
    for j, htxt in enumerate(headers):
        c = tbl.cell(0, j)
        c.fill.solid(); c.fill.fore_color.rgb = header_fill
        c.vertical_anchor = MSO_ANCHOR.MIDDLE
        c.margin_left = Inches(0.07); c.margin_right = Inches(0.05)
        c.margin_top = Inches(0.03); c.margin_bottom = Inches(0.03)
        tf = c.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]; r = p.add_run(); r.text = htxt
        r.font.name = FONT; r.font.size = Pt(header_size); r.font.bold = True
        r.font.color.rgb = WHITE
    for i, row in enumerate(rows):
        tbl.rows[i+1].height = Inches(row_h)
        for j, val in enumerate(row):
            c = tbl.cell(i+1, j)
            c.fill.solid()
            c.fill.fore_color.rgb = WHITE if i % 2 == 0 else TINT2
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.margin_left = Inches(0.07); c.margin_right = Inches(0.05)
            c.margin_top = Inches(0.03); c.margin_bottom = Inches(0.03)
            tf = c.text_frame; tf.word_wrap = True
            if isinstance(val, tuple):
                text, opts = val
            else:
                text, opts = val, {}
            p = tf.paragraphs[0]; r = p.add_run(); r.text = text
            r.font.name = FONT; r.font.size = Pt(opts.get("size", font_size))
            r.font.bold = opts.get("bold", False)
            r.font.color.rgb = opts.get("color", BODY)
    return tbl

def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text

# =====================================================================
# SLIDE 1 — TITLE
# =====================================================================
s = add_slide()
# top accent band (subtle)
band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(SLIDE_W), Inches(0.14))
band.fill.solid(); band.fill.fore_color.rgb = ACCENT; band.line.fill.background(); band.shadow.inherit = False
# left vertical accent
vbar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.85), Inches(2.62), Inches(0.09), Inches(2.15))
vbar.fill.solid(); vbar.fill.fore_color.rgb = ACCENT; vbar.line.fill.background(); vbar.shadow.inherit = False

add_text(s, 1.2, 1.72, 11.0, 0.4, [("MID REVIEW  •  INDIVIDUAL PROJECT", {"size": 14, "bold": True, "color": ACCENT})])
add_text(s, 1.2, 2.35, 11.4, 1.9, [
    ("IoT-Based Liver Disease Risk Prediction", {"size": 40, "bold": True, "color": INK}),
    ("using Ensemble Machine Learning", {"size": 40, "bold": True, "color": INK}),
], line_spacing=1.05, space_after=2)
add_text(s, 1.2, 4.35, 11.0, 0.9, [
    ("A sensor-driven point-of-care screening system: biosensor readings → cloud ensemble model → real-time risk assessment",
     {"size": 16, "color": MUTED, "italic": True})], line_spacing=1.1)

# details strip (editable by student)
strip = add_box(s, 1.2, 5.75, 10.9, 1.0, [
    ("Presented by:  ________________________        Roll No:  ____________________", {"size": 13.5, "color": BODY}),
    ("Guide:  ________________________        Department / Class:  ____________________________", {"size": 13.5, "color": BODY}),
], fill=TINT, line=LINEC, radius=0.08, space_after=8, margin=0.22, anchor=MSO_ANCHOR.MIDDLE)

add_text(s, 1.2, 6.95, 11.0, 0.35, [("Dataset: Indian Liver Patient Records (ILPD) — Kaggle / UCI Repository", {"size": 11, "color": MUTED})])
notes(s, "Introduce yourself and the project in one line: an IoT screening system that uses biosensor readings and an ensemble ML model to flag liver disease risk in real time. Dataset is the real Kaggle ILPD dataset (583 records). Fill in your name/roll number/guide/department on this slide before the review.")

# =====================================================================
# SLIDE 2 — INTRODUCTION / BACKGROUND
# =====================================================================
s = add_slide()
header(s, "Introduction", "Introduction & Background", 2)

add_box(s, 0.57, 1.68, 6.0, 2.6, bullet_lines([
    (0, "Domain: Healthcare IoT — point-of-care biosensors combined with Machine Learning for early disease screening", {"size": 14.5}),
    (0, "Liver disease is a “silent killer”: symptoms appear only at advanced stages (cirrhosis, failure)", {"size": 14.5}),
    (0, "≈ 2 million liver-disease deaths worldwide every year (Asrani et al., J. Hepatol., 2019); India carries a high burden", {"size": 14.5}),
    (0, "Screening today = Liver Function Test (LFT) panel from a blood sample at a lab — slow, invasive, costly", {"size": 14.5}),
]), fill=TINT, line=LINEC, radius=0.05, space_after=8, margin=0.18)

add_box(s, 6.85, 1.68, 5.92, 2.6, bullet_lines([
    (0, "Motivation: every LFT biomarker can be measured with compact biosensors:", {"size": 14.5, "bold": True}),
    (1, "Bilirubin → optical sensor (450 nm, like a jaundice meter)", {"size": 13}),
    (1, "ALT / AST / ALP → electrochemical enzyme biosensors", {"size": 13}),
    (1, "Proteins / Albumin → bio-impedance & immuno-sensors", {"size": 13}),
    (0, "Sensor readings + ML risk score = affordable screening for rural / primary healthcare", {"size": 14.5}),
]), fill=TINT, line=LINEC, radius=0.05, space_after=8, margin=0.18)

add_box(s, 0.57, 4.5, 12.2, 2.25, [
    ("Why this problem matters", {"size": 15, "bold": True, "color": ACCENT2}),
    ("Early detection changes outcomes: liver disease caught before cirrhosis is largely manageable, while late diagnosis is often fatal. "
     "A low-cost device that converts a few sensor readings into an instant, reliable risk score can screen populations that never reach a diagnostic lab — "
     "this is the practical motivation for combining IoT sensing with machine learning in this project.", {"size": 14, "color": BODY}),
], fill=WHITE, line=LINEC, radius=0.05, space_after=6, margin=0.2)
notes(s, "Key points: liver disease is asymptomatic early; diagnosis depends on lab-based LFT panels; all LFT parameters are measurable with biosensors, which is why an IoT screening device is feasible. Mention rural/primary-care relevance for India. If asked about the 2M figure: Asrani et al., Journal of Hepatology 2019 — ~1M deaths from cirrhosis complications + ~1M from viral hepatitis & liver cancer.")

# =====================================================================
# SLIDE 3 — PROBLEM STATEMENT
# =====================================================================
s = add_slide()
header(s, "Problem", "Problem Statement", 3)

add_box(s, 0.57, 1.66, 12.2, 1.15, [
    ("Liver disease is detected late because screening depends on lab-based tests and expert interpretation; "
     "there is no affordable, real-time, point-of-care screening that combines multiple liver biomarkers.",
     {"size": 15.5, "bold": True, "color": INK}),
], fill=TINT, line=ACCENT, radius=0.06, anchor=MSO_ANCHOR.MIDDLE, margin=0.22)

add_text(s, 0.57, 3.0, 12.0, 0.35, [("Specific challenges to solve", {"size": 14, "bold": True, "color": ACCENT2})])
cards = [
    ("C1 — Sensing", "Acquire key LFT biomarkers (bilirubin, ALT/AST, ALP, proteins, albumin) outside a laboratory, using sensor modules."),
    ("C2 — Prediction", "Fuse 10 correlated, noisy biomarkers into a reliable risk score on an imbalanced dataset (416 patients vs 167 healthy)."),
    ("C3 — Real-time delivery", "Serve predictions instantly to low-cost hardware (ESP32-class nodes) and a dashboard, not as an offline report."),
]
cx = 0.57
for title, body in cards:
    add_box(s, cx, 3.42, 3.93, 1.95, [
        (title, {"size": 13.5, "bold": True, "color": ACCENT2}),
        (body, {"size": 12.5, "color": BODY}),
    ], fill=WHITE, line=LINEC, radius=0.07, space_after=6, margin=0.17)
    cx += 4.14

add_text(s, 0.57, 5.55, 12.0, 0.35, [("Limitations of the current system", {"size": 14, "bold": True, "color": ACCENT2})])
add_box(s, 0.57, 5.95, 12.2, 1.0, bullet_lines([
    (0, "Lab pathway: hours–days turnaround, per-test cost, invasive venous blood draw, hospital visit required, no repeat/continuous monitoring", {"size": 13.5}),
    (0, "Existing ML studies: offline desktop models — none connected to live sensors; existing IoT devices: single biomarker only, no risk model", {"size": 13.5}),
]), fill=WHITE, line=LINEC, radius=0.05, space_after=4, margin=0.16)
notes(s, "Frame the three challenges clearly: sensing, prediction on noisy imbalanced data, and real-time delivery. The class imbalance numbers (416 vs 167) come straight from the ILPD dataset — examiners like when you know your data. The limitation line sets up the Research Gap slide.")

# =====================================================================
# SLIDE 4 — EXISTING SYSTEM
# =====================================================================
s = add_slide()
header(s, "Existing Work", "Existing System / How It Is Done Today", 4)

make_table(s, 0.57, 1.7, 12.2, [2.6, 4.9, 4.7],
    ["Approach", "How it works", "Advantages / Limitations"],
    [
        [("1. Clinical lab pathway", {"bold": True, "color": INK}),
         "Blood draw → automated analyser → LFT report (bilirubin, ALT/AST, ALP, proteins) → physician interpretation",
         "✔ Gold standard, full panel\n✘ Slow (hours–days), invasive, costly, needs hospital; no continuous monitoring"],
        [("2. Offline ML on ILPD", {"bold": True, "color": INK}),
         "Single classifiers (SVM, Decision Tree, Random Forest, k-NN) trained on the ILPD benchmark dataset",
         "✔ Proves biomarkers are predictive (60–88% accuracy)\n✘ Desktop/offline only, no sensor input, no real-time output, often ignores class imbalance"],
        [("3. Standalone IoT devices", {"bold": True, "color": INK}),
         "Transcutaneous bilirubin meters, neonatal jaundice wearables (color sensor + ESP32), bilirubin test strips",
         "✔ Non-invasive, portable, real-time\n✘ Measure only one biomarker — no multi-parameter risk score, no disease-level prediction"],
    ], font_size=11.5, header_size=12, row_h=1.24)

add_box(s, 0.57, 6.02, 12.2, 0.85, [
    ("Takeaway:  each existing approach solves only one part — accurate labs but slow, ML but offline, IoT but single-biomarker. "
     "None of them connects real sensor data to a multi-biomarker risk model in real time.",
     {"size": 13.5, "bold": True, "color": ACCENT2}),
], fill=TINT, line=LINEC, radius=0.06, anchor=MSO_ANCHOR.MIDDLE, margin=0.2)
notes(s, "Walk through the three rows left→right. The takeaway sentence is the bridge to the literature review: research exists in both ML and IoT, but the two worlds have not been joined. If asked for examples: jaundice meters (JM-105), ESP32 color-sensor wearables (Fatoni 2025).")

# =====================================================================
# SLIDES 5-6 — LITERATURE REVIEW
# =====================================================================
PAPERS_1 = [
    ("1", "Joloudari et al., 2019\nInformatics in Medicine Unlocked",
     "Accurate prediction with optimal feature subset; ELTA data-mining pipeline + PSO-optimized SVM, 10-fold CV on UCI liver data",
     "PSO-SVM best of 5 models — 95.17% avg accuracy",
     "Offline mining; heavy PSO tuning; no deployment or sensing",
     "Baseline for tuned SVM; value of feature weighting"),
    ("2", "Singh, Bagga & Kaur, 2020\nProcedia Computer Science",
     "Software tool for liver risk; 6 classifiers (LR, SMO, RF, NB, J48, k-NN) + feature selection on ILPD; built ILDPS desktop app",
     "Random Forest best — 71.87% accuracy",
     "Low accuracy; class imbalance ignored; desktop-only",
     "Confirms ILPD is noisy → motivates our ensemble"),
    ("3", "Haque et al., 2018\nIC4ME2 (IEEE)",
     "Performance comparison of Random Forest vs Artificial Neural Network for liver disorder classification",
     "RF competitive/superior; ANN limited by small data",
     "Small dataset; limited metrics; no deployment",
     "Justifies Random Forest as ensemble member"),
    ("4", "Tokala et al., 2023\nIJACSA 14(2)",
     "Reduce physician workload; LR, SVM, k-NN, RF on ILPD + correlation analysis of biomarkers",
     "Random Forest best — 88%; bilirubin attributes highly correlated",
     "Imbalance not handled; offline study",
     "Confirms RF strength; supports our derived-ratio features"),
    ("5", "Ahad et al., 2024\nResults in Engineering",
     "Multiclass prediction; adaptive preprocessing + data balancing + ensembles (LR/XGB/RF) + clinician UI",
     "Up to 99.8% accuracy with balancing",
     "Very high values → overfitting risk; UI only, no sensors/IoT",
     "Shows preprocessing power; real-time sensing still missing"),
]
PAPERS_2 = [
    ("6", "El Atifi et al., 2025\nPLOS ONE 20(8)",
     "Optimize ensembles for healthcare; RF / AdaBoost / GB with GridSearchCV & RandomizedSearchCV tuning",
     "RF + GridSearch best — 85.17%, AUC 0.85",
     "Offline benchmark; no deployment or explainability",
     "Validates our hyperparameter-tuning strategy"),
    ("7", "ICDSA Proceedings, 2025\nSpringer",
     "Early prediction (Indian context); 8 models incl. MLP, hard-voting + genetic-algorithm optimization",
     "GA-optimized Random Forest best — 79%",
     "Offline; single dataset; no hardware link",
     "GA-tuning idea; motivation similar to ours"),
    ("8", "Uddin et al., 2026\nNetw. Model. Anal. (Springer)",
     "Early detection on real multi-hospital data (Bangladesh); 5 ML + 5 DL models, Wilcoxon test, sensitivity analysis",
     "RF best — 80.6%; ALP most influential biomarker",
     "Hospital records only; no point-of-care device",
     "Biomarker importance backs our sensor selection"),
    ("9", "LivXAI-Net, 2025\nComput. Methods Programs Biomed.",
     "Explainable AI + IoT monitoring; RF/XGB + SHAP/PFI with simulated wearable biosensors on Mayo PBC data",
     "RF 84% / XGB 82% (20-fold CV)",
     "Simulated sensor data only; no live hardware; PBC-specific",
     "Closest work — still lacks real sensors & low-cost node"),
    ("10", "Fatoni et al., 2025\nAnalytica 6(1)",
     "Non-invasive neonatal jaundice monitoring; TCS34725 color sensor + ESP32-C3 wearable + Blynk app",
     "Bilirubin estimates validated vs blood tests",
     "Single biomarker; no disease-risk prediction model",
     "Proves ESP32 + optical bilirubin sensing → our hardware path"),
]

def lit_slide(page_no, rows, kicker_num):
    s = add_slide()
    header(s, f"Literature Review {kicker_num}", "Literature Review", page_no)
    make_table(s, 0.57, 1.58, 12.2, [0.32, 2.45, 3.95, 1.95, 2.13, 1.4],
        ["#", "Paper (Authors, Venue)", "Problem & Method", "Key Findings", "Limitation", "Relevance"],
        rows, font_size=9.5, header_size=10, row_h=0.96)
    add_text(s, 0.57, 6.8, 12.2, 0.25, [
        ("Each paper was studied in full — problem, technique and limitation summarized above; full citations on slide 14.",
         {"size": 9.5, "italic": True, "color": MUTED})])
    return s

s5 = lit_slide(5, PAPERS_1, "1 / 2  (papers 1–5)")
notes(s5, "Papers 1–5 are the ML-prediction line. Tell the story chronologically: PSO-SVM (2019) → software tools (2020) → RF comparisons (2018/2023) → preprocessing-heavy ensembles claiming 99% (2024, likely overfit). The consistent limitation: everything is offline/desktop, nothing is connected to sensors. Know at least one number from each row — examiners test this.")

s6 = lit_slide(6, PAPERS_2, "2 / 2  (papers 6–10)")
notes(s6, "Papers 6–10: recent tuning studies (85%, 79%), real-world hospital-data study (RF 80.6%, ALP most influential — supports our sensor choice), then the two closest works: LivXAI-Net (IoT + XAI but only SIMULATED sensors on historical data) and Fatoni's ESP32 wearable (real hardware but only bilirubin, no risk model). This directly motivates the research gap on the next slide.")

# =====================================================================
# SLIDE 7 — RESEARCH GAP
# =====================================================================
s = add_slide()
header(s, "Gap Analysis", "Research Gap (derived from the literature)", 7)

gaps = [
    ("G1 — No live sensor pipeline", "All ML studies run offline on stored CSVs. Even the closest IoT work (LivXAI-Net, 2025) simulates sensors with historical data — no real sensor → model pathway exists."),
    ("G2 — Single-biomarker IoT devices", "Existing hardware measures only bilirubin and never fuses a full LFT panel, so no device produces a multi-parameter disease risk score."),
    ("G3 — Recall ignored; imbalance unhandled", "ILPD is 71%/29% imbalanced. Most studies optimize accuracy only and never report recall — exactly the metric a screening device cannot afford to lose."),
    ("G4 — No device–cloud interface", "No published work exposes the liver-risk model as an API that a low-cost ESP32-class node can query with sensor JSON in real time."),
]
pos = [(0.57, 1.68), (6.85, 1.68), (0.57, 3.62), (6.85, 3.62)]
for (gx, gy), (gt, gb) in zip(pos, gaps):
    add_box(s, gx, gy, 5.92, 1.78, [
        (gt, {"size": 14, "bold": True, "color": ACCENT2}),
        (gb, {"size": 12, "color": BODY}),
    ], fill=WHITE, line=LINEC, radius=0.06, space_after=5, margin=0.17)

add_box(s, 0.57, 5.62, 12.2, 1.25, [
    ("Statement of the gap", {"size": 13, "bold": True, "color": ACCENT}),
    ("No existing system performs end-to-end, sensor-driven liver-risk screening — i.e., acquiring the full set of LFT biomarkers "
     "with IoT-compatible sensors and scoring them in real time with a recall-optimized ensemble model exposed as a device-ready API.",
     {"size": 14.5, "bold": True, "color": INK}),
], fill=TINT, line=ACCENT, radius=0.06, space_after=5, margin=0.2)
notes(s, "This is the most-defended slide. Each gap maps to specific papers: G1 → every ML paper + LivXAI-Net's simulated sensors; G2 → Fatoni 2025 & jaundice meters; G3 → accuracy-only evaluation in papers 2, 4, 5; G4 → nobody provides a REST endpoint. End with the boxed statement — that single sentence is the gap.")

# =====================================================================
# SLIDE 8 — OBJECTIVES
# =====================================================================
s = add_slide()
header(s, "Objectives", "Project Objectives", 8)

objs = [
    ("O1", "Map all 10 ILPD parameters to IoT-compatible sensor modules and design the sensing/acquisition architecture.", "addresses G2, G4"),
    ("O2", "Develop a recall-optimized ensemble classifier on the ILPD dataset — target ≥ 72% accuracy with ≥ 90% recall.", "addresses G3"),
    ("O3", "Deploy the model as a real-time REST API + web dashboard that sensor nodes can query instantly.", "addresses G1, G4"),
    ("O4", "Benchmark the ensemble against single-model baselines (LR, SVM, RF, GB, XGB, k-NN) on 5 metrics: accuracy, precision, recall, F1, AUC.", "addresses G3"),
    ("O5", "Validate the pipeline with an ESP32 prototype node using an optical bilirubin sensor.", "addresses G1"),
]
oy = 1.72
for oid, ot, og in objs:
    add_box(s, 0.57, oy, 0.85, 0.78, [(oid, {"size": 19, "bold": True, "color": WHITE})],
            fill=ACCENT, radius=0.12, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, margin=0.05)
    add_box(s, 1.6, oy, 9.6, 0.78, [(ot, {"size": 13.5, "color": BODY})],
            fill=WHITE, line=LINEC, radius=0.1, anchor=MSO_ANCHOR.MIDDLE, margin=0.16)
    add_box(s, 11.35, oy, 1.42, 0.78, [(og, {"size": 9.5, "bold": True, "color": ACCENT2})],
            fill=TINT, line=LINEC, radius=0.1, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, margin=0.06)
    oy += 0.96

add_box(s, 0.57, 6.5, 12.2, 0.45, [
    ("Each objective is specific, measurable and directly traces back to a gap identified in the literature review.",
     {"size": 11.5, "italic": True, "color": MUTED}),
], anchor=MSO_ANCHOR.MIDDLE, margin=0.14)
notes(s, "Emphasize the right-hand tags: every objective closes a named gap. O2's targets (≥72% accuracy, ≥90% recall) were set from literature: ILPD studies report 71–88% accuracy, and screening demands high sensitivity. O5 is the hardware objective for the final phase.")

# =====================================================================
# SLIDE 9 — PROPOSED METHODOLOGY / BLOCK DIAGRAM
# =====================================================================
s = add_slide()
header(s, "Methodology", "Proposed System Architecture", 9)

blocks = [
    ("1 · BIOSENSOR ARRAY", ["Optical bilirubin sensor", "ALT/AST/ALP enzyme", "electrodes · protein/", "albumin sensing"]),
    ("2 · SIGNAL CONDITIONING", ["Amplification &", "filtering · 12-bit ADC", "calibration lookup"]),
    ("3 · ESP32 EDGE NODE", ["Compute A/G ratio,", "AST/ALT ratio ·", "pack sensor JSON"]),
    ("4 · CLOUD ML SERVER", ["Flask REST API ·", "preprocessing ·", "ensemble model"]),
    ("5 · OUTPUT", ["Risk % + level ·", "dashboard · LED/", "buzzer alert"]),
]
bx, bw, bh, by = 0.5, 2.16, 2.72, 1.78
gapx = 0.42
for i, (bt, lines) in enumerate(blocks):
    x = bx + i * (bw + gapx)
    box = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(by), Inches(bw), Inches(bh))
    try: box.adjustments[0] = 0.07
    except Exception: pass
    box.fill.solid(); box.fill.fore_color.rgb = TINT if i % 2 == 0 else WHITE
    box.line.color.rgb = ACCENT; box.line.width = Pt(1.3)
    box.shadow.inherit = False
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = Inches(0.09); tf.margin_right = Inches(0.09); tf.margin_top = Inches(0.1)
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = bt; r.font.name = FONT; r.font.size = Pt(11.5); r.font.bold = True
    r.font.color.rgb = ACCENT2
    p.space_after = Pt(7)
    for lt in lines:
        pp = tf.add_paragraph(); pp.alignment = PP_ALIGN.CENTER; pp.space_after = Pt(3)
        rr = pp.add_run(); rr.text = lt; rr.font.name = FONT; rr.font.size = Pt(10); rr.font.color.rgb = BODY
    if i < 4:
        ax = x + bw + (gapx - 0.34) / 2
        ar = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(ax), Inches(by + bh/2 - 0.13), Inches(0.34), Inches(0.26))
        ar.fill.solid(); ar.fill.fore_color.rgb = ACCENT; ar.line.fill.background(); ar.shadow.inherit = False

add_text(s, 0.5, 4.62, 12.3, 0.3,
         [("Input  →  Processing  →  Model  →  Output        (data flows left→right; risk level flows back to the device)",
           {"size": 11.5, "italic": True, "color": MUTED})], align=PP_ALIGN.CENTER)

ctx = [
    ("DATASET", "ILPD — 583 records (416 patients / 167 healthy), 10 features; Kaggle / UCI #225"),
    ("ALGORITHMS", "Ensemble: XGBoost + Gradient Boosting + Random Forest + SVM (soft voting)"),
    ("SOFTWARE", "Python · scikit-learn · XGBoost · Flask REST API · joblib"),
    ("HARDWARE", "ESP32 (Wi-Fi) · optical & electrochemical sensor modules · OLED/LED alerts"),
]
cx = 0.57
for ct, cb in ctx:
    add_box(s, cx, 5.05, 2.97, 1.62, [
        (ct, {"size": 11, "bold": True, "color": ACCENT2}),
        (cb, {"size": 10.5, "color": BODY}),
    ], fill=TINT2, line=LINEC, radius=0.08, space_after=4, margin=0.15)
    cx += 3.08
notes(s, "Explain left to right: sensors produce the exact 10 ILPD parameters (that is the design rule — every model input must be sensor-measurable). ESP32 computes derived ratios locally and POSTs JSON to the Flask API; the ensemble returns risk probability. The four cards below name dataset, algorithms, software and hardware. If asked why cloud and not on-device: model is small enough for edge later, but cloud-first simplifies updates and logging.")

# =====================================================================
# SLIDE 10 — PROPOSED WORK (existing vs proposed)
# =====================================================================
s = add_slide()
header(s, "Proposed Work", "How the Proposed System Closes the Gap", 10)

make_table(s, 0.57, 1.66, 12.2, [2.2, 4.75, 5.25],
    ["Aspect", "Existing approaches (from literature)", "Proposed approach (this project)"],
    [
        [("Data input", {"bold": True, "color": INK}),
         "Stored CSV records; simulated sensors; single biomarker devices",
         "Sensor-mapped acquisition of all 10 LFT parameters (optical + electrochemical + impedance)"],
        [("Model", {"bold": True, "color": INK}),
         "Single classifiers (RF/SVM/DT) or untuned ensembles",
         "Soft-voting ensemble (XGBoost + GB + RF + SVM) with GridSearch-tuned XGBoost and engineered ratios"],
        [("Imbalance & metrics", {"bold": True, "color": INK}),
         "Accuracy-only evaluation; imbalance mostly ignored",
         "Class-weighted training; evaluated on accuracy, precision, recall, F1 and AUC — recall prioritized for screening"],
        [("Deployment", {"bold": True, "color": INK}),
         "Desktop/offline software; no device interface",
         "Always-on REST API (/api/predict) + live dashboard that an ESP32 node queries in < 1 s"],
        [("Output", {"bold": True, "color": INK}),
         "Static report or single biomarker value",
         "Risk probability + LOW/MODERATE/HIGH level + out-of-range biomarker flags → device alerts"],
    ], font_size=11, header_size=11.5, row_h=0.82)

add_box(s, 0.57, 6.32, 12.2, 0.72, [
    ("Novel component:  an end-to-end sensor-to-cloud screening pipeline in which every model input is sensor-measurable, "
     "derived features are computed at the edge, and a recall-optimized ensemble is served as an open device-ready API.",
     {"size": 13.5, "bold": True, "color": INK}),
], fill=TINT, line=ACCENT, radius=0.06, anchor=MSO_ANCHOR.MIDDLE, margin=0.2)
notes(s, "Read across each row: left = what literature does, right = what we do differently. The novelty box is your one-sentence elevator pitch — memorize it. Note the deliberate recall focus (row 3) which answers 'why not just maximize accuracy'.")

# =====================================================================
# SLIDE 11 — WORK COMPLETED SO FAR
# =====================================================================
s = add_slide()
header(s, "Progress", "Work Completed So Far", 11)

add_text(s, 0.57, 1.6, 6.0, 0.35, [("Software & model — completed", {"size": 14, "bold": True, "color": ACCENT2})])
done1 = bullet_lines([
    (0, "Dataset: real ILPD CSV acquired from Kaggle (583 records); missing A/G ratios repaired by recomputation", {"size": 13}),
    (0, "Feature engineering: bilirubin ratio, AST/ALT ratio, globulin difference (all edge-computable)", {"size": 13}),
    (0, "6 models trained & compared with 5-fold stratified cross-validation", {"size": 13}),
    (0, "XGBoost tuned via GridSearchCV; soft-voting ensemble built and selected", {"size": 13}),
    (0, "Model serialized (joblib) for deployment", {"size": 13}),
], bullet="✔")
add_box(s, 0.57, 2.0, 6.0, 3.3, done1, fill=WHITE, line=LINEC, radius=0.05, space_after=7, margin=0.16)

add_text(s, 6.85, 1.6, 6.0, 0.35, [("Deployment & validation — completed", {"size": 14, "bold": True, "color": ACCENT2})])
done2 = bullet_lines([
    (0, "Flask prediction server + REST API (/api/predict) + web dashboard implemented and running", {"size": 13}),
    (0, "API verified with real records: patient case → 96.6% HIGH risk; healthy case → 44.5% LOW risk", {"size": 13}),
    (0, "Normal-range checker flags out-of-bounds sensor values in the dashboard", {"size": 13}),
    (0, "IoT sensor-mapping table prepared for all 10 parameters (hardware-phase input)", {"size": 13}),
    (0, "Training report (all metrics) exported for documentation", {"size": 13}),
], bullet="✔")
add_box(s, 6.85, 2.0, 5.92, 3.3, done2, fill=WHITE, line=LINEC, radius=0.05, space_after=7, margin=0.16)

add_box(s, 0.57, 5.5, 12.2, 1.35, [
    ("Live demo available", {"size": 13, "bold": True, "color": ACCENT2}),
    ("The dashboard is running now: enter biosensor readings → get risk %, risk level and out-of-range flags instantly. "
     "(Screenshots of the dashboard and API responses are shown in the demo / attached separately.)", {"size": 12.5, "color": BODY}),
], fill=TINT, line=LINEC, radius=0.06, space_after=5, margin=0.18)
notes(s, "Two columns = software/ML vs deployment/validation. Emphasize that the API was tested with a real patient record (96.6% HIGH) and a healthy record (44.5% LOW). Offer to show the live dashboard during the review — this is your strongest impression point. Remaining work = hardware phase + explainability.")

# =====================================================================
# SLIDE 12 — RESULTS / PRELIMINARY ANALYSIS
# =====================================================================
s = add_slide()
header(s, "Results", "Preliminary Results & Analysis", 12)

stats = [("Accuracy", "73.3%"), ("ROC-AUC", "0.81"), ("Recall", "91.3%"), ("Precision", "76.0%"), ("F1 Score", "83.0%")]
sx = 0.57
for name, val in stats:
    add_box(s, sx, 1.62, 2.32, 1.06, [
        (val, {"size": 22, "bold": True, "color": ACCENT2}),
        (name, {"size": 10.5, "color": MUTED}),
    ], fill=TINT, line=LINEC, radius=0.09, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE, space_after=2, margin=0.08)
    sx += 2.47

add_text(s, 0.57, 2.92, 6.4, 0.3, [("Model comparison (5-fold CV on training data)", {"size": 12.5, "bold": True, "color": ACCENT2})])
make_table(s, 0.57, 3.25, 6.4, [3.3, 1.55, 1.55],
    ["Model", "CV Accuracy", "CV AUC"],
    [
        ["Logistic Regression", "62.5%", "0.728"],
        ["Random Forest", "71.2%", "0.682"],
        ["Gradient Boosting", "67.5%", "0.640"],
        ["XGBoost", "68.7%", "0.653"],
        ["SVM (RBF)", "60.9%", "0.706"],
        ["k-NN", "67.7%", "0.643"],
        [("Soft-Voting Ensemble (deployed)", {"bold": True, "color": ACCENT2}),
         ("73.3%*", {"bold": True, "color": ACCENT2}), ("0.813*", {"bold": True, "color": ACCENT2})],
    ], font_size=10.5, header_size=10.5, row_h=0.40)
add_text(s, 0.57, 6.78, 6.4, 0.3, [("* held-out test set (25% of data, stratified)", {"size": 9.5, "italic": True, "color": MUTED})])

add_text(s, 7.35, 2.92, 5.4, 0.3, [("Confusion matrix — test set (146 samples)", {"size": 12.5, "bold": True, "color": ACCENT2})])
make_table(s, 7.35, 3.25, 5.4, [1.8, 1.8, 1.8],
    ["", "Pred. Healthy", "Pred. Patient"],
    [
        [("Actual Healthy", {"bold": True, "color": INK}), "12  (TN)", "30  (FP)"],
        [("Actual Patient", {"bold": True, "color": INK}), "9  (FN)", ("95  (TP)", {"bold": True, "color": GREEN})],
    ], font_size=11, header_size=10.5, row_h=0.62)

add_box(s, 7.35, 5.05, 5.42, 1.85, bullet_lines([
    (0, "Ensemble beats every single model (AUC 0.813 vs best 0.728)", {"size": 12}),
    (0, "91.3% recall → only 9 of 104 patients missed — safe for screening", {"size": 12}),
    (0, "73.3% accuracy sits in the published ILPD range (71–88%) without leakage or over-sampling tricks", {"size": 12}),
], bullet="▪"), fill=TINT2, line=LINEC, radius=0.06, space_after=6, margin=0.16)
notes(s, "Story: single models top out around 0.68–0.71 accuracy on this noisy dataset; the ensemble lifts AUC to 0.813. The key number is RECALL 91.3% — in screening, missing a patient (FN=9) is the dangerous error, and we keep it low. Accuracy 73.3% is honest and in-line with literature (Singh 2020: 71.9%, Tokala 2023: 88% with less strict protocol). The 30 false positives are acceptable: they are simply referred for a confirmatory lab test.")

# =====================================================================
# SLIDE 13 — FUTURE WORK
# =====================================================================
s = add_slide()
header(s, "Plan", "Future Work", 13)

future = [
    ("Hardware phase", "Build ESP32 node: 450 nm optical bilirubin module + enzyme-electrode interface; calibrate readings against lab LFT values."),
    ("Connectivity", "MQTT + cloud logging of patient history, trend charts and threshold alerts; battery-powered portable enclosure."),
    ("Explainability", "Add SHAP values per prediction so the dashboard explains which biomarker drove the risk score (clinician trust)."),
    ("Model upgrades", "Stacking/deep-learning comparison; validation on a second dataset; external validation with collected sensor data."),
    ("Clinical step", "Small pilot study with ethics approval; mobile app for field health workers; Hindi/regional-language UI."),
]
fy = 1.70
for ft, fb in future:
    add_box(s, 0.57, fy, 2.5, 0.82, [(ft, {"size": 13, "bold": True, "color": ACCENT2})],
            fill=TINT, line=LINEC, radius=0.1, anchor=MSO_ANCHOR.MIDDLE, align=PP_ALIGN.CENTER, margin=0.08)
    add_box(s, 3.25, fy, 9.52, 0.82, [(fb, {"size": 12.5, "color": BODY})],
            fill=WHITE, line=LINEC, radius=0.1, anchor=MSO_ANCHOR.MIDDLE, margin=0.16)
    fy += 0.96

add_box(s, 0.57, 6.55, 12.2, 0.5, [
    ("Expected final outcome:  a working IoT screening prototype — sensor readings in, risk report out in < 5 s, recall ≥ 90%.",
     {"size": 12.5, "bold": True, "color": INK}),
], fill=TINT, line=ACCENT, radius=0.08, anchor=MSO_ANCHOR.MIDDLE, margin=0.16)
notes(s, "Sequence matters: hardware first (that is the IoT deliverable), then connectivity/logging, explainability, model validation, and finally a pilot. End with the boxed expected outcome. Timeline if asked: hardware prototype in 3–4 weeks, pilot in the final month.")

# =====================================================================
# SLIDE 14 — REFERENCES
# =====================================================================
s = add_slide()
header(s, "References", "References", 14)

refs_l = [
    "1.  J. H. Joloudari, H. Saadatfar, A. Dehzangi, S. Shamshirband, “Computer-aided decision-making for predicting liver disease using PSO-based optimized SVM with feature selection,” Informatics in Medicine Unlocked, vol. 17, p. 100255, 2019.",
    "2.  J. Singh, S. Bagga, R. Kaur, “Software-based prediction of liver disease with feature selection and classification techniques,” Procedia Computer Science, vol. 167, pp. 1970–1980, 2020.",
    "3.  M. R. Haque, M. M. Islam, H. Iqbal, M. S. Reza, M. K. Hasan, “Performance evaluation of random forests and artificial neural networks for the classification of liver disorder,” in Proc. Int. Conf. on Computer, Communication, Chemical, Material and Electronic Engineering (IC4ME2), IEEE, 2018.",
    "4.  S. Tokala, K. Hajarathaiah, S. R. P. Gunda et al., “Liver disease prediction and classification using machine learning techniques,” Int. J. of Advanced Computer Science and Applications (IJACSA), vol. 14, no. 2, 2023.",
    "5.  A. Ahad, B. Das, M. R. Khan, N. Saha, A. Zahid, M. Ahmad, “Multiclass liver disease prediction with adaptive data preprocessing and ensemble modeling,” Results in Engineering, vol. 22, p. 102059, 2024.",
    "6.  W. El Atifi, O. El Rhazouani, F. M. Khan, H. Sekkat, “Optimizing ensemble machine learning models for accurate liver disease prediction in healthcare,” PLOS ONE, vol. 20, no. 8, p. e0330899, 2025.",
]
refs_r = [
    "7.  “Applying machine learning algorithms for liver disease prediction,” Proc. Int. Conf. on Data Science and Applications (ICDSA), Springer, 2025.",
    "8.  R. Uddin, M. A. R. Khan, J. R. Das, I. Ahammad, S. Debnath, F. Afrin, “Intelligent technique in early liver disease prediction using real data samples from the perspective of Bangladesh,” Network Modeling Analysis in Health Informatics and Bioinformatics, Springer, 2026.",
    "9.  “LivXAI-Net: An explainable AI framework for liver disease diagnosis with IoT-based real-time monitoring support,” Computer Methods and Programs in Biomedicine, 2025.",
    "10. A. Fatoni, M. D. Anggraeni, E. Rahmawati, “Non-invasive wearable sensor for real-time neonatal jaundice monitoring using forehead skin tone analysis,” Analytica, vol. 6, no. 1, p. 6, 2025.",
    "11. N. Anzar et al., “Electrochemical sensor for bilirubin detection using paper-based screen-printed electrodes functionalized with silver nanoparticles,” Micromachines, vol. 13, no. 11, p. 1845, 2022.",
    "12. B. Ramana, N. Venkateswarlu, “ILPD (Indian Liver Patient Dataset),” UCI Machine Learning Repository #225 / Kaggle: uciml/indian-liver-patient-records, 2012. [Dataset]",
    "13. S. K. Asrani, H. Devarbhavi, J. Eaton, P. S. Kamath, “Burden of liver diseases in the world,” Journal of Hepatology, vol. 70, no. 1, pp. 151–171, 2019.",
]
add_box(s, 0.57, 1.62, 6.05, 5.2, [(t, {"size": 11.5, "color": BODY}) for t in refs_l],
        space_after=11, line_spacing=1.05)
add_box(s, 6.75, 1.62, 6.05, 5.2, [(t, {"size": 11.5, "color": BODY}) for t in refs_r],
        space_after=11, line_spacing=1.05)
notes(s, "13 references: 8 ML-prediction papers, 1 IoT+ML framework (LivXAI-Net), 2 sensor-hardware papers, the global disease-burden citation (Asrani 2019) and the dataset citation. Consistent IEEE-style format. If asked 'which papers influenced you most': LivXAI-Net (IoT+ML feasibility), Tokala 2023 (RF strength on ILPD), El Atifi 2025 (tuning strategy).")

prs.save("/home/user/liver_iot/Liver_IoT_Mid_Review_PPT.pptx")
print("Saved /home/user/liver_iot/Liver_IoT_Mid_Review_PPT.pptx")
print("Slides:", len(prs.slides.__iter__.__self__._sldIdLst))
