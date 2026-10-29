# Submission checklist — 28 October 2026

The data, notebook, frozen V2 test and five-page report are available.
The new test scored 27/30 windows (90.00%) on four single-activity files. The
remaining work is detailed in rubric_status.md, including missing Baum–Welch,
figures, fuller feature explanations and the ambiguous data-file target.

## Completed locally

- [x] Original timestamped accelerometer and gyroscope CSVs are included and labelled.
- [x] Device, requested/measured sampling rates and 50 Hz analysis grid are documented.
- [x] Training, validation, historical V1 test and fresh V2 test are distinct files.
- [x] Frozen V2 model was evaluated on four new files without refitting or tuning.
- [x] Required four-state sensitivity, specificity and overall-accuracy table is in the V2 report.
- [x] Transition heatmap, decoded new-test sequences and confusion matrix are included.
- [x] Notebook is saved with real execution outputs and project source files.
- [x] Five-page V2 PDF includes background/use case, collection, HMM, results and reflection.
- [x] Synthetic algorithm-test fixtures are not presented as collected data.

## Check and complete before hand-in

- [x] Author Mahamat bakhit is included in the report, notebook and repository.
- [ ] Check all four videos against the rubric: at least five seconds, face and full body visible, adequate lighting, logging phone visible. The sampled still clip crops part of the body at the left edge.
- [x] Four public video links are included in the report and `data/video_links.csv`.
- [x] The public Mahamatbt/human-activity-hmm repository contains this project only; its URL is in the report.
- [ ] Confirm the assignment's ambiguous “approximately 20 samples” wording with your instructor if it means 20 separate recording trials. Current counts are 11 recordings and many two-second windows.
- [ ] Download/clone the repository once to verify that the notebook, data and report are present.

The historical mixed-run change times remain approximate. The new four-file test
has clear whole-file activity labels but does not test real activity transitions.
State that limitation if presenting or answering questions about the project.
