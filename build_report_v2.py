"""Build the five-page final-results report from frozen v2 outputs."""
from pathlib import Path
import csv
import json
from html import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output/pdf/activity_hmm_report_v2.pdf"
OUT.parent.mkdir(parents=True, exist_ok=True)


def read_csv(path):
    with (ROOT / path).open(newline="") as f:
        return list(csv.DictReader(f))


test = json.loads((ROOT / "results/fresh_test_v2/summary.json").read_text())
selection = json.loads((ROOT / "results/improvement_v2/selection.json").read_text())
metrics = read_csv("results/fresh_test_v2/test_metrics.csv")
fresh = read_csv("data/fresh_test_v2_recordings.csv")
videos = read_csv("data/video_links.csv")
AUTHOR = "Mahamat bakhit"
REPOSITORY = "https://github.com/Mahamatbt/human-activity-hmm"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="TitleV2", fontName="Helvetica-Bold", fontSize=20, leading=24,
                          spaceAfter=12, textColor=colors.HexColor("#17354A")))
styles.add(ParagraphStyle(name="HeadV2", fontName="Helvetica-Bold", fontSize=13, leading=17,
                          spaceBefore=10, spaceAfter=7, textColor=colors.HexColor("#17354A")))
styles.add(ParagraphStyle(name="BodyV2", fontName="Helvetica", fontSize=10, leading=14, spaceAfter=8))
styles.add(ParagraphStyle(name="SmallV2", fontName="Helvetica", fontSize=8.5, leading=11.5,
                          spaceAfter=6, textColor=colors.HexColor("#3E4A54")))
styles.add(ParagraphStyle(name="NoteV2", fontName="Helvetica-Bold", fontSize=10, leading=14, spaceAfter=10))
styles.add(ParagraphStyle(name="CellV2", fontName="Helvetica", fontSize=8.5, leading=11))

story = []
WIDTH = A4[0] - 88


def p(text, style="BodyV2"):
    story.append(Paragraph(text, styles[style]))


def h(text):
    p(text, "HeadV2")


def table(rows, widths):
    data = [[Paragraph(escape(str(cell)), styles["CellV2"]) for cell in row] for row in rows]
    obj = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    obj.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E9EFF3")),
        ("LINEBELOW", (0, 0), (-1, 0), .6, colors.HexColor("#9CAAB4")),
        ("LINEBELOW", (0, 1), (-1, -1), .25, colors.HexColor("#D9DFE3")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.extend([obj, Spacer(1, 8)])


def fig(path, width, caption):
    obj = Image(str(ROOT / "results" / path))
    obj.drawHeight *= width / obj.drawWidth
    obj.drawWidth = width
    obj.hAlign = "CENTER"
    story.append(obj)
    p(caption, "SmallV2")


def page():
    story.append(PageBreak())


p("Human Activity States<br/>Using a Hidden Markov Model", "TitleV2")
p(f"{AUTHOR} | Individual iPhone study | Data collected 28 October 2026", "SmallV2")
p("Fresh four-file test: 27 of 30 windows correct (90.00%). This evaluates steady activities for one participant and phone on the same day.", "NoteV2")
h("1. Background and motivation")
p("Students alternate between studying, standing pauses, walking and short exercise breaks. A phone-based study-break diary could recognize movement patterns and identify when the phone is left on a surface. Accelerometer and gyroscope measurements are noisy, so a reading does not directly reveal an activity. A Hidden Markov Model (HMM) combines signal features with activity persistence. This study asks whether one iPhone can distinguish standing while held, walking, jumping and a phone-on-surface still state. Still describes the device, not what its owner does away from it.")
h("2. Collection and available evidence")
p("One participant used an iPhone 13 Pro, iOS 26.5 and Sensor Logger 1.68. The app requested 20 ms intervals (50 Hz). Calibrated acceleration and gyroscope streams were used; uncalibrated exports were preserved. Both sensors share timestamps within each recording. Seven development/historical runs averaged 50.1635-50.1705 Hz; four fresh tests averaged 50.1739-50.1757 Hz. All were aligned to a 50 Hz grid. There were no invalid or duplicate sensor rows and no gap above about 0.0212 s [1,2].")
rows = [["Fresh recording", "Raw duration", "Retained seconds", "2 s windows"]]
for row in fresh:
    rows.append([row["activity"].title(), f'{float(row["raw_duration_s"]):.1f} s',
                 f'{float(row["trim_start_s"]):.0f}-{float(row["trim_end_s"]):.0f}',
                 int((float(row["trim_end_s"]) - float(row["trim_start_s"])) / 2)])
table(rows, [155, 90, 135, WIDTH - 380])
p("Four initial single-activity files and one mixed run trained the model (282 windows). One later mixed run supplied validation (21 windows). A previous mixed test (24 windows) is retained as historical V1 evidence. The four new single-activity files above formed the unseen V2 test (30 windows). All eleven files came from the same participant, device and date. Adjacent windows within a file are correlated.", "SmallV2")
video_links = " | ".join(f'<link href="{escape(row["video_url"], quote=True)}" color="#075e99">{row["activity"].title()} ({float(row["duration_s"]):.2f} s)</link>' for row in videos)
p("Video evidence: " + video_links + ".", "SmallV2")
p(f'<link href="{REPOSITORY}" color="#075e99">GitHub repository: Mahamatbt/human-activity-hmm</link>. Browser-compatible video copies are included under docs/videos. Sampled still-video frames crop part of the person at the left edge; this remains a framing limitation.', "SmallV2")

page()
h("3. Preprocessing, features and reference quality")
p("Original CSV bytes and SHA-256 hashes are preserved. Timestamps are sorted and audited, and sensors are aligned by timestamp. Timing jitter is regularized; a fourth-order zero-phase low-pass Butterworth filter uses a cutoff of 0.4 times the lower native/target rate before resampling. Gaps above 0.2 s would be rejected. Filtering is offline because it uses future samples. Initial isolated training files retain seconds 2-120. Each new test file drops its first 2 s and incomplete last window, a rule fixed from duration without consulting predictions.")
p("Non-overlapping 2 s windows contain 100 aligned samples. The original eight features include acceleration magnitude mean/standard deviation, acceleration signal magnitude area, gyroscope magnitude RMS, acceleration and gyroscope dominant frequencies, acceleration 3-10 Hz spectral-power fraction, and gyroscope AC spectral power. FFT calculations remove the mean, use a Hann taper for the spectral peak and exclude DC. Frequency resolution is 0.5 Hz; peaks in quiet data can reflect noise.")
p("The mixed activity orders were confirmed by the participant, but the exact change times were not measured. Their approximate boundaries were estimated from raw-signal changes before V2 selection. The exported Annotation.csv files are empty. A 2 s guard avoids using windows near these estimated boundaries for emission fitting. It cannot establish true change times. The new four-file test needs no within-file change-time estimates: each new file has one participant-labelled activity.")
p("Historical mixed intervals (seconds since Start): <b>training</b> standing 2-8, walking 8-22, standing 22-30, jumping 30-41, standing 41-54, still 54-68, standing 68-79, walking 79-94; <b>validation</b> walking 2-12, standing 12-20, jumping 20-32, still 32-44; <b>earlier test</b> jumping 2-12, walking 12-24, still 24-40, standing 40-50.", "SmallV2")
h("4. HMM setup and algorithms")
p("Hidden states Z are standing, walking, jumping and still. Observations X are transformed feature vectors. A is the 4 x 4 activity transition matrix, pi the initial state distribution, and B a diagonal Gaussian density for each state. Supervised fitting estimates each Gaussian from labelled training windows and A/pi from the mixed training sequence. It never counts artificial transitions across separate files. Training-only means and standard deviations set the scaler.")
p("Viterbi decodes the most likely complete state path. Forward computes sequence log likelihood. Baum-Welch could learn from unlabelled data but was not run. Validation macro-F1 and accuracy guide model selection; unseen sensitivity, specificity and accuracy assess state recognition. Likelihood alone does not show whether predicted activity labels are correct [3].")
p("V1's six smoothing/variance settings all tied at 57.14% validation accuracy. V2 held smoothing 0.1 and variance floor 0.05 fixed and compared eight development variants: eight versus four features, raw versus log1p values, and per-window versus per-recording emission weighting. The predeclared choice used macro-F1, then accuracy, fewer features and standard weighting. The winner uses acceleration magnitude mean/standard deviation, gyroscope RMS, and acceleration high-band fraction. The three positive magnitude features use log1p before training-only scaling. Validation was 19/21 = 90.48%, macro-F1 0.904. The model was saved before scoring the four fresh test files.", "SmallV2")

page()
h("5. Transition model and unseen test metrics")
fig("transition_matrix.png", WIDTH, "Figure 1. Training transition probabilities and counts at each 2 s step. The change times in this controlled mixed run are approximate.")
p("The scripted mixed training order supplies seven cross-activity changes. Standing leads to walking twice and jumping/still once each; walking, jumping and still each return to standing once. Self-transitions dominate. These probabilities reflect one short script and persistence. Unobserved changes receive smoothing mass rather than measured evidence.")
h("Required four-state test table")
rows = [["State", "Number of samples", "Sensitivity", "Specificity", "Overall accuracy"]]
for row in metrics:
    rows.append([row["Activity"].title(), row["Number of Samples"],
                 f'{float(row["Sensitivity"])*100:.1f}%', f'{float(row["Specificity"])*100:.1f}%',
                 f'{float(row["Overall Accuracy"])*100:.1f}%'])
table(rows, [88, 100, 96, 96, WIDTH - 380])
p("Table 1. Each sample is one non-overlapping, participant-labelled 2 s window in a new single-activity recording. Sensitivity is TP/(TP+FN), specificity is TN/(TN+FP). Overall accuracy is the same four-class score repeated in each row, not a one-versus-rest score. The metrics CSV also includes counts, precision, F1 and one-versus-rest accuracy.", "SmallV2")
p(f"The frozen V2 model correctly labels {test['correct_windows']}/{test['n_windows']} new windows ({test['accuracy']*100:.2f}% accuracy), with macro-F1 {test['macro_f1']:.3f}. Validation was 19/21 (90.48%) on an approximately labelled mixed run. The fresh test gives clearer state labels, but only four short, dependent files. The old 45.83% V1 mixed-test score used a different model and uncertain reference, so it is not a paired measure of improvement.")

page()
h("6. Decoded sequences and interpretation")
fig("fresh_test_v2/decoded_sequences.png", 425, "Figure 2. V2 Viterbi predictions against the activity named by each new file. Lines overlap when the model is correct. These recordings have no true within-file transitions.")
fig("fresh_test_v2/confusion_matrix.png", 220, "Figure 3. Fresh-test confusion matrix. Rows are recorded activities and columns are predicted activities.")
p("Walking (8/8), jumping (8/8) and still (7/7) are correct in every retained window. Standing is correct in 4/7; the middle three standing windows, centred at 9, 11 and 13 s, are predicted as still. Quiet standing while holding a phone can resemble a phone lying flat. Those three false positives reduce still specificity to 87.0%.")
p("The predicted standing-to-still-to-standing change in Figure 2 is an error within a single standing recording. A within-file activity change was never performed in these new test files, so this experiment does not establish whether the HMM detects real transitions. The earlier mixed test remains available in the repository, but its reference times are approximate.", "SmallV2")

page()
h("7. Discussion, limitations and conclusion")
p("The new test agrees with the recorded activities in 27/30 windows. Walking, jumping and still were easiest; standing was hardest because three quiet windows resembled still. This supports recognition of this participant's steady activities in similar same-day conditions. It does not demonstrate reliable recognition for other people, phones, days, environments or activity transitions.")
p("The historical V1 mixed test had 45.83% agreement with approximate activity timings and an unresolved walking/still order-versus-signal mismatch. That motivated the V2 development comparison, which selected a four-feature log-scaled model on validation and then scored the new files without refitting. The old and new test scores use different models and reference designs; their gap cannot be attributed solely to feature reduction. No new test label was used for tuning.")
p("The HMM transition matrix reflects persistence, but its cross-state probabilities rely on only seven observed changes. A strong self-transition can remove isolated noise or preserve a wrong state. Sampling remained near 50 Hz without long gaps, making rate variation unlikely to explain the standing/still errors. Filtering changes spectra; 2 s windows can mix transitions; magnitude features discard direction; and diagonal Gaussians omit correlations. Original long recordings supply many correlated windows, not many independent trials.")
p("A next study should record several continuous runs with activity-change times logged independently of predictions, ideally on different days. More varied phone placement and additional participants/devices would test generalization. More transitions, orientation features or richer state durations can be compared on validation, followed by another untouched test. Any model redesigned after seeing these fresh results needs a new test for an unbiased final score.")
p("The project supplies a reproducible NumPy four-state HMM, real iPhone data, time/frequency observations, a training transition heatmap and decoded test sequences. The fresh result is promising for steady states in this narrow setting. Author details and links to the public repository and four evidence videos appear on page 1. Remaining rubric gaps are documented in the repository's rubric status note.")
h("References and reproducibility")
p('[1] Sensor Logger. <link href="https://www.tszheichoi.com/sensorloggerhelp" color="#17354A">Help and Support</link>.<br/>[2] Choi, K. <link href="https://github.com/tszheichoi/awesome-sensor-logger/blob/main/UNITS.md" color="#17354A">Sensor Logger units reference</link>.<br/>[3] hmmlearn. <link href="https://hmmlearn.readthedocs.io/en/stable/tutorial.html" color="#17354A">HMM tutorial</link>.', "SmallV2")
p("Reproduce with human_activity_hmm.ipynb, activity_hmm.py, improve_model.py and evaluate_fresh_v2.py. Saved V2 parameters, original data hashes, fresh-test manifest, audits, metrics and predictions are included. Runtime: Python 3.13.0, NumPy 2.4.3, pandas 3.0.1. No synthetic study data were substituted.", "SmallV2")


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#CBD4DB"))
    canvas.line(44, 34, A4[0] - 44, 34)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#4E5A63"))
    canvas.drawString(44, 23, "V2 fresh test | four separate recordings | 28 October 2026")
    canvas.drawRightString(A4[0] - 44, 23, f"{doc.page} / 5")
    canvas.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=44, rightMargin=44,
                        topMargin=39, bottomMargin=46,
                        title="Human Activity HMM - Individual V2 Report",
                        author=AUTHOR)
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
