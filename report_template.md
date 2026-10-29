# Campus Study-Break and Phone Set-Down Recognition Using an HMM

**WORKING TEMPLATE — NOT A COMPLETED REPORT.** Replace every bracketed field with
your actual work. Add real figures and results, then export and verify 4–5 pages.

Author: [your name and student ID]  
Repository: [GitHub link]  
Collection dates: [actual dates]  
Participant count: 1

## Background and motivation

[One paragraph explaining your individual use case, who benefits, why noisy sensor
data require activity inference, why sequential modelling may help, and the limited
meaning of a phone-on-desk state. Adapt the README's suggested paragraph.]

## Data collection and preprocessing

I recorded [number] sessions and [number] recordings using an [actual iPhone model],
iOS [version], and Sensor Logger [version]. The four operational states were standing
while holding the phone at waist level, walking, repeated jumping, and the phone
stationary on a flat surface. My holding orientation was [description]. Each isolated
activity recording contained [actual] usable seconds. I also collected [number]
continuous recordings to observe real activity changes.

Required video evidence, each at least 5 seconds with my whole body and face clearly
visible, and the phone visible in the activity-appropriate position:

- Standing: [accessible video link]
- Walking: [accessible video link]
- Jumping: [accessible video link]
- Still on flat surface: [accessible video link]

For the sole participant, the requested sensor rate was [actual setting] Hz.
Measured accelerometer rates were [range] Hz and gyroscope rates were [range] Hz;
these were estimated from timestamp differences. Both streams were aligned to
[chosen rate] Hz. [Explain invalid rows, duplicates, timing jitter, observed gaps,
filtering and any rejected recordings using sampling_audit.csv.]

I retained [actual counts] training recordings, [counts] validation recordings and
[counts] test recordings, assigning whole recordings before window extraction.
The test data came from [actual later session/date/environment]. I extracted
non-overlapping [duration]-second windows, obtaining [counts] observations per split.
A “sample” in the evaluation table means one labelled feature window. Mixed windows
were labelled by their midpoint activity; [describe annotation source and uncertainty].

Time features were [list actual features]. Frequency features were [list actual
features, FFT procedure and units]. Feature scaling used training statistics only.
[Insert one compact plot of real sensor signals if space permits.]

## HMM setup and implementation

Z = {standing, walking, jumping, still}. Each observation is an [actual dimension]-
dimensional feature vector. A contains transition probabilities at the window time
step; π contains sequence-start probabilities. Each state's emission is a diagonal
Gaussian with estimated mean and variance; B denotes continuous densities.

I estimated emissions from labelled pure training windows and A/π from continuous
training sequences with additive smoothing. This anchors state names without using
test labels. [State actual smoothing, variance floor, and validation-selection method.]
I used Viterbi for sequence decoding and Forward for log likelihood. Supervised
estimation is appropriate because training activities are labelled; Baum–Welch is an
unlabelled-data alternative and was not run. Validation macro-F1 selected settings;
unseen sensitivity, specificity and accuracy measure whether decoded activity
patterns are correct. Likelihood is an auxiliary diagnostic rather than evidence of
classification accuracy. [If you change the algorithms, rewrite this accurately.]

The code uses NumPy for HMM algorithms. [State final versions and how to reproduce.]
Viterbi and zero-phase filtering are offline methods using future observations.

## Results and interpretation

[Insert results/transition_matrix.png and caption: rows=current activity,
columns=next activity; probabilities estimated at the chosen window duration.
Refer to transition_counts.csv to distinguish observed changes from smoothing.]

[Insert results/confusion_matrix.png with rows=true state, columns=predicted state.]

[Insert the four rows from results/test_metrics.csv using the exact assignment
columns: State (Activity), Number of Samples, Sensitivity, Specificity, Overall
Accuracy. Define sample=window. Report percentages or fractions consistently.
Overall Accuracy is the same multiclass value in all rows. If using the exported
One-vs-Rest Accuracy instead, label and define it explicitly.]

Unseen accuracy was [actual] and macro-F1 was [actual], on [actual number] windows
from [actual number] recordings. Pure-window results were [actual], showing
[evidence-based interpretation of boundary effects]. The emission-only baseline
obtained [actual]; Viterbi obtained [actual]. [Do not claim improvement if there was none.]

[Insert a real decoded mixed-test sequence plot, with true and predicted activities,
time in seconds and the recording ID. Discuss specific observed mistakes.]

## Discussion and conclusion

[Use per-state sensitivity, specificity and the confusion matrix to identify which
activities were easiest/hardest. Explain observed transitions using actual counts,
not assumptions. Discuss noise, measured rates, filtering and window size.]

[Explain whether performance carried over to the later session and how it differed
from validation. Avoid claims about other participants/devices. Note temporal
dependence, small test counts, scripted activity order, few observed transitions,
diagonal Gaussian assumptions and activity-label uncertainty. The phone-on-desk
state does not reveal the participant's movement away from the device.]

[Propose improvements supported by observed errors: more sessions/participants,
more real transitions, revised features, placement checks or duration-aware models.
Finish with one evidence-based conclusion answering your research question.]

## References

- Sensor Logger. Help and Support. https://www.tszheichoi.com/sensorloggerhelp
- Choi, K. Awesome Sensor Logger: export documentation and units.
  https://github.com/tszheichoi/awesome-sensor-logger
- hmmlearn. Tutorial (HMM algorithms).
  https://hmmlearn.readthedocs.io/en/stable/tutorial.html
- [Add any further sources actually used; follow your course's citation rules.]
