"""Render the five-page provisional report from the saved real-data outputs."""
from pathlib import Path
import csv
import json
from html import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output/pdf"
OUT.mkdir(parents=True, exist_ok=True)
PDF = OUT / "activity_hmm_report_draft.pdf"


def read_csv(name):
    with (ROOT / name).open(newline="") as f:
        return list(csv.DictReader(f))


metrics = read_csv("results/test_metrics.csv")
comparison = read_csv("results/test_comparison.csv")
validation = read_csv("results/validation_selection.csv")[0]
summary = read_csv("results/recording_summary.csv")
manifest = read_csv("data/recordings.csv")
audit = read_csv("results/sampling_audit.csv")
config = json.loads((ROOT / "results/run_config.json").read_text())
accuracy = float(comparison[0]["accuracy"])
macro_f1 = float(comparison[0]["macro_f1"])
stable_accuracy = float(comparison[2]["accuracy"])

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="ReportTitle", fontName="Helvetica-Bold", fontSize=20, leading=24, spaceAfter=12, textColor=colors.HexColor("#17354A")))
styles.add(ParagraphStyle(name="ReportH", fontName="Helvetica-Bold", fontSize=13, leading=17, spaceBefore=10, spaceAfter=7, textColor=colors.HexColor("#17354A")))
styles.add(ParagraphStyle(name="ReportBody", fontName="Helvetica", fontSize=10, leading=14, spaceAfter=8))
styles.add(ParagraphStyle(name="ReportSmall", fontName="Helvetica", fontSize=8.5, leading=11.5, spaceAfter=6, textColor=colors.HexColor("#3E4A54")))
styles.add(ParagraphStyle(name="ReportCell", fontName="Helvetica", fontSize=8.5, leading=11))
styles.add(ParagraphStyle(name="ReportNote", fontName="Helvetica-Bold", fontSize=10, leading=14, spaceAfter=10))
story = []
markdown = []
WIDTH = A4[0] - 88


def p(text, style="ReportBody", md=True):
    story.append(Paragraph(text, styles[style]))
    if md:
        markdown.append(text.replace("<b>", "**").replace("</b>", "**") + "\n")


def heading(text):
    p(text, "ReportH", md=False)
    markdown.append("## " + text + "\n")


def table(rows, widths):
    data = [[Paragraph(escape(str(cell)), styles["ReportCell"]) for cell in row] for row in rows]
    t = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E9EFF3")),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#9CAAB4")),
        ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#D9DFE3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([t, Spacer(1, 9)])
    # Keep the editable report readable without embedding a second metric table.
    markdown.extend(["; ".join(map(str, row)) + "  " for row in rows])
    markdown.append("\n")


def figure(name, width, caption):
    image = Image(str(ROOT / "results" / name))
    image.drawHeight *= width / image.drawWidth
    image.drawWidth = width
    image.hAlign = "CENTER"
    story.append(image)
    p(caption, "ReportSmall", md=False)
    markdown.append(f"![{caption}](results/{name})\n")


def page():
    story.append(PageBreak())


p("Human Activity States<br/>Using a Hidden Markov Model", "ReportTitle", md=False)
markdown.append("# Human Activity States Using a Hidden Markov Model\n")
p("Individual iPhone study | Participant P01 | Data collected 28 October 2026", "ReportSmall")
p("PROVISIONAL DRAFT: activity-change times were estimated, not independently recorded. Results below are conditional on approximate reference labels.", "ReportNote")
heading("1. Background and motivation")
p("Students alternate between studying, standing pauses, walking and short exercise breaks. A phone-based study-break diary could recognize these movement patterns and identify when the phone is left on a surface. Accelerometer and gyroscope measurements are noisy, so an individual reading does not directly reveal an activity. This project combines motion features with a Hidden Markov Model (HMM) to represent activity persistence and changes. Its specific question is whether one iPhone can distinguish standing while held, walking, jumping and a phone-on-surface still state in a later recording. The final state describes the device, not the person's movement away from it.")
heading("2. Collection and available evidence")
p("One participant used an iPhone 13 Pro, iOS 26.5 and Sensor Logger 1.68. Metadata requests 20 ms intervals (50 Hz). Calibrated acceleration and gyroscope streams are used; uncalibrated exports are preserved but excluded. Both sensors share timestamps within each file. The measured average rates across all seven runs range from 50.1635 to 50.1705 Hz; analysis uses a common 50 Hz grid. No invalid numeric rows or duplicate timestamps were found; the largest gap is about 0.0212 s. Sources: supplied CSV/metadata and sampling_audit.csv; sensor conventions follow [1,2].")
rows = [["Recording", "Split", "Retained seconds", "2 s windows"]]
for row in summary:
    m = next(m for m in manifest if m["recording_id"] == row["recording_id"])
    label = row["activity"].title() if row["activity"] != "mixed" else "Mixed " + row["split"]
    rows.append([label, row["split"], f'{m["trim_start_s"]}-{m["trim_end_s"]}', row["windows"]])
table(rows, [155, 90, 135, WIDTH - 380])
p("Four isolated initial files and one mixed run train the model (282 windows). Distinct later logging runs supply validation (21) and test (24). They were recorded on the same afternoon, by the same person/phone; this is not a cross-day or cross-person study. The source dataset has seven recordings, not 327 independent trials.", "ReportSmall")
p("Video evidence is included locally: standing new video.MP4 (9.77 s), jumping new video.MP4 (11.48 s), still new video.MP4 (10.33 s), and walking video.MP4 (5.23 s). Sampled still frames crop part of the person at the left edge. Accessible online video links, the author's identity and repository URL remain to be added before submission.", "ReportSmall")

page()
heading("3. Preprocessing, features and reference quality")
p("Original CSV bytes and hashes are preserved. Timestamps are sorted, invalid/duplicate rows are audited, and sensors are aligned by time rather than row number. Small jitter is regularized; a fourth-order zero-phase low-pass Butterworth filter uses a cutoff of 0.4 times the lower native/target rate before resampling. Gaps above 0.2 s would be rejected. Offline filtering uses future samples. Isolated files retain seconds 2-120 using one fixed edge rule; the mixed training end is trimmed before its final low-motion tail.")
p("Each non-overlapping 2 s window has 100 aligned rows. Four time-domain features are acceleration-magnitude mean and standard deviation, acceleration signal magnitude area (mean |x|+|y|+|z|), and gyroscope-magnitude RMS. Four frequency features are acceleration/gyroscope dominant magnitude frequencies, acceleration 3-10 Hz power fraction relative to 0.5-10 Hz, and gyroscope AC spectral power with mean-square scaling. Dominant-frequency searches remove the mean, use a Hann taper and exclude DC. FFT bin spacing is 0.5 Hz; quiet-window peaks may represent noise.")
p("The participant confirmed activity orders but did not measure changes. Approximate boundaries were estimated from raw-signal regime changes before new model selection. They are not independent timed ground truth. Source exports' Annotation.csv files are empty. A window uses the reference state at its midpoint. Guarded cores exclude whole windows within 2 s of any estimated interval edge; this chosen buffer is not a statistical confidence interval.")
p("Estimated intervals (seconds since Start): <b>training</b> standing 2-8, walking 8-22, standing 22-30, jumping 30-41, standing 41-54, still 54-68, standing 68-79, walking 79-94; <b>validation</b> walking 2-12, standing 12-20, jumping 20-32, still 32-44; <b>test</b> jumping 2-12, walking 12-24, still 24-40, standing 40-50.", "ReportSmall")
heading("4. HMM setup and algorithms")
p("The hidden states are standing, walking, jumping and still. Observations are eight-dimensional standardized feature vectors. Training-only means/standard deviations define scaling. A is a 4 x 4 transition matrix, pi is the start distribution, and B comprises one diagonal Gaussian density per state. Means/variances use 236 isolated training windows plus 28 guarded mixed-training windows. A and pi use the mixed training sequence only; independent files are never concatenated into artificial transitions.")
p("Supervised parameter estimation is suitable because training activity labels are supplied. Viterbi finds the most likely full state sequence, and Forward computes sequence log likelihood. Baum-Welch is an unlabelled-data alternative and is not executed. Validation macro-F1 selects smoothing and variance floor; unseen sensitivity, specificity and accuracy assess decoded states. Higher likelihood alone does not establish better classification [3].")
p("The fixed grid tests smoothing {0.1, 1.0} and standardized variance floors {0.05, 0.1, 0.2}. All six settings tie at validation accuracy 57.14% and macro-F1 0.569. The first fixed-grid candidate, smoothing 0.1/floor 0.05, is selected; it is not uniquely superior. Test labels do not select model settings. Implementation uses NumPy, pandas, SciPy and matplotlib; six algorithm/pipeline checks pass.", "ReportSmall")

page()
heading("5. Results: transitions and provisional metrics")
figure("transition_matrix.png", WIDTH, "Figure 1. Training transition probabilities and counts at a 2 s step. Reference times are approximate; counts describe the controlled script.")
p("The training order supplies seven cross-activity changes. Standing leads to walking twice and to jumping/still once each; walking, jumping and still each return to standing once. Self-transitions dominate. This is plausible for activity persistence, but frequencies and pi reflect one scripted run. Probabilities for unobserved changes come from smoothing; they are not evidence that those changes occurred.")
heading("Required four-state table")
rows = [["State", "Number of samples", "Sensitivity", "Specificity", "Overall accuracy"]]
for row in metrics:
    rows.append([row["Activity"].title(), row["Number of Samples"],
                 f'{float(row["Sensitivity"])*100:.1f}%', f'{float(row["Specificity"])*100:.1f}%',
                 f'{float(row["Overall Accuracy"])*100:.1f}%'])
table(rows, [88, 100, 96, 96, WIDTH - 380])
p("Table 1. PROVISIONAL evaluation against participant-confirmed order and estimated timing. A sample is one labelled 2 s test window. Overall accuracy is a single multiclass value repeated in each row, not per-state one-vs-rest accuracy. The CSV additionally exports one-vs-rest accuracy, counts, precision and F1.", "ReportSmall")
p(f"Viterbi obtains {accuracy*100:.2f}% accuracy (11/24 windows) and macro-F1 {macro_f1:.3f}. Independent Gaussian emissions obtain the same accuracy and macro-F1 0.467; the HMM's macro-F1 difference is only about 0.003. On 16 guarded-core windows, accuracy is {stable_accuracy*100:.1f}% and macro-F1 0.431. Removing boundary neighbourhoods does not improve agreement with this reference. No uncertainty interval is claimed from these few dependent windows.")

page()
heading("6. Decoded sequence and interpretation")
figure("decoded_p01_test_mixed_20261028.png", WIDTH, "Figure 2. Viterbi predictions versus the approximate test reference. Dashed reference times are estimates, not independently measured activity boundaries.")
figure("confusion_matrix.png", 305, "Figure 3. Conditional confusion matrix; rows are approximate reference states and columns are predictions.")
p("Jumping agrees best with the supplied reference: all five jumping windows are predicted correctly, with no false jumping predictions. Standing sensitivity is 80%, walking 33.3%, and still 0%. All eight still-reference windows are predicted as standing or walking. These describe agreement with an uncertain reference, not independently established activity accuracy.")
p("A key unresolved mismatch is that the raw test signal is very quiet around 16-23 s, followed by sustained movement around 24-39 s, whereas the participant explicitly confirmed walking before still. That order was retained rather than changed to improve scores. Without a synchronized video/time log, the contributions of model error, phone handling and reference error cannot be separated. A guarded-core score does not resolve an incorrect order or broad timing error.", "ReportSmall")

page()
heading("7. Discussion, limitations and conclusion")
p("The provisional test accuracy is lower than validation (45.83% versus 57.14%), so this experiment does not demonstrate reliable recognition in the later run. Viterbi changes some window decisions but does not improve overall accuracy over independent emissions. A transition model can suppress isolated errors, but a mismatched emission pattern or strong persistence can also erase short activities. With only one mixed training run, the transition estimates and start distribution have limited support.")
p("Large periodic motion helps explain jumping agreement, while standing/still both have low motion and may overlap under sensor noise and hand movement. The quiet/moving test-order mismatch limits any claim that still is intrinsically the hardest class. Different grip or pace could shift features, but no measured placement-change log was supplied, so this remains a possible explanation rather than an observed cause.")
p("Sampling is consistent near 50 Hz, with no detected long gaps; it is unlikely to be the main technical failure here. Filtering reduces high-frequency noise but changes the spectrum, 2 s windows mix transitions, and magnitude features discard direction. Diagonal Gaussians ignore correlations and may not represent multimodal activities. Long isolated training files contribute many correlated windows, not many independent trials. The short same-day test cannot support claims about other people, devices, environments or long-term behaviour.")
p("The highest-priority improvement is independently timed annotation: record a synchronized full-run video or activity-change log and verify the test intervals without consulting model predictions. If the current test influences redesign, collect another untouched timed test. Add more continuous training transitions and independent sessions, standardize phone placement, then consider feature selection, richer emissions or duration-aware models using validation data only. Additional participants/phones would enable broader generalization assessment.")
p("In conclusion, the project provides a reproducible four-state NumPy HMM pipeline with real iPhone data, both feature domains, a transition heatmap, decoded sequence and conditional metrics. It does not yet establish dependable activity recognition. The approximate reference times must be verified, video framing checked, accessible evidence links added and the repository published before treating this draft as a final submission.")
heading("References and reproducibility")
p('[1] Sensor Logger. <link href="https://www.tszheichoi.com/sensorloggerhelp" color="#17354A">Help and Support</link>. Sensor configuration and sampling-rate guidance.<br/>[2] Choi, K. <link href="https://github.com/tszheichoi/awesome-sensor-logger/blob/main/UNITS.md" color="#17354A">Awesome Sensor Logger: units reference</link>.<br/>[3] hmmlearn. <link href="https://hmmlearn.readthedocs.io/en/stable/tutorial.html" color="#17354A">HMM tutorial</link>. Distinction between estimation, likelihood and decoding.', "ReportSmall", md=False)
markdown.extend(["[Sensor Logger help](https://www.tszheichoi.com/sensorloggerhelp)", "[Units reference](https://github.com/tszheichoi/awesome-sensor-logger/blob/main/UNITS.md)", "[HMM tutorial](https://hmmlearn.readthedocs.io/en/stable/tutorial.html)"])
p("Reproduce with human_activity_hmm.ipynb and activity_hmm.py. Inputs, annotation hashes, sampling audit, run configuration, metrics and predictions are included. Runtime: Python 3.13.0, NumPy 2.4.3, pandas 3.0.1. No external dataset or synthetic study data were substituted.", "ReportSmall")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#CBD4DB"))
    canvas.line(44, 34, A4[0] - 44, 34)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#4E5A63"))
    canvas.drawString(44, 23, "PROVISIONAL | approximate activity timings | 28 October 2026")
    canvas.drawRightString(A4[0] - 44, 23, f"{doc.page} / 5")
    canvas.restoreState()


doc = SimpleDocTemplate(str(PDF), pagesize=A4, leftMargin=44, rightMargin=44,
                        topMargin=39, bottomMargin=46, title="Human Activity HMM - Provisional Report",
                        author="Individual study, participant P01")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
(ROOT / "report_draft.md").write_text("\n".join(markdown) + "\n")
print(PDF)
