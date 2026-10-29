# Rubric status at publication

Author: Mahamat bakhit. This repository publishes the current experiment and its
90.00% frozen V2 test result. Publication does not mean every Excellent-level rubric
requirement has been completed.

- **Data quantity:** 11 actual recordings are included. The rubric wording asks
  for 50 labelled 5–10-second files for each activity; whether this means 50 total
  or per activity, and whether segments of longer recordings count, needs instructor
  clarification. Original isolated files each exceed 90 seconds. Two-second feature
  windows and separate sensor streams are not counted as independent trials.
- **Implementation:** supervised Gaussian-HMM fitting, Forward and Viterbi are
  implemented. Baum–Welch and its convergence demonstration are still missing.
- **Features:** eight features are extracted, including four time-domain and four
  frequency-domain features; V2 selects four. Each feature's relevance and the
  standardization/window-duration rationale need fuller explanation.
- **Figures:** the notebook includes sample motion plots, but the five-page report
  still needs a sample sensor plot. An emission-distribution figure is also missing.
- **Evaluation:** four fresh test files, sensitivity, specificity, accuracy,
  confusion matrix and transition heatmap are included. The saved model achieves
  27/30 correct windows. This tests steady activities, not true activity transitions.
- **Video evidence:** four public video links are provided. The still clip crops
  part of the participant in sampled frames, so full-body compliance remains a concern.
- **Presentation:** the current report is five pages and includes the author's
  name, repository link and four video links. Its section labels can be aligned more
  closely with the prescribed assignment headings during the rubric revision.

If further model development uses the exposed fresh-test results, a later untouched
test is required for a new unseen-performance claim. The existing 90.00% result
belongs to the frozen V2 model.
