# SignVox ASL Pilot Collection Plan

**Project:** SignVox  
**Dataset:** SignVox-ASL100  
**Pilot version:** P0.1  
**Status:** READY FOR CONTROLLED PILOT — NOT FULL COLLECTION  
**Primary objective:** Validate the end-to-end data-collection and landmark pipeline before scaling.

---

## 1. Pilot Objective

The pilot is not intended to produce the final training dataset.

It is intended to answer five questions:

1. Can SignVox consistently capture complete ASL performances on a smartphone?
2. Can the landmark pipeline reliably capture hands, face, and upper-body pose?
3. Can the team label and organize samples without ambiguity?
4. Can the quality-control process identify bad samples reliably?
5. Does the collected data preserve the information needed for eventual real-time inference?

If any critical answer is no, stop and correct the pipeline before scaling.

---

# 2. Pilot Scope

Recommended initial pilot:

```text
5–10 signers
×
11–13 representative signs
×
5 repetitions per sign
```

This produces approximately:

```text
275–650 attempted recordings
```

depending on signer count and final pilot vocabulary.

Do not treat the target number as a quota that must be filled if the quality is poor.

Quality takes priority over count.

---

# 3. Pilot Sign Set

Use the following stress-test vocabulary.

### Core pipeline

```text
HELLO
WAIT
STOP
MOTHER
FAMILY
GO
COME
GIVE
UNDERSTAND
```

### Confusion-pair testing

```text
GOOD
THANK-YOU
PLEASE
SORRY
```

These signs deliberately stress:

- dynamic movement;
- fine finger motion;
- two-hand interaction;
- body-relative location;
- spatial/directional information;
- non-manual information;
- visually similar signs.

---

# 4. Pilot Sign Status

The pilot vocabulary contains signs from the current per-sign specification work.

Before recording a sign, verify that its current specification is available.

```text
HELLO          Batch 01
WAIT           Batch 01
STOP           Batch 01
MOTHER         Batch 02
FAMILY         Batch 02
GO             Batch 03
COME           Batch 03
GIVE           Batch 03
UNDERSTAND     Batch 01
GOOD           Batch 01
THANK-YOU      Batch 01
PLEASE         Batch 01
SORRY          Batch 01
```

These are **candidate collection labels**, not final ASL ground truth.

Expert validation remains pending.

---

# 5. Participant Gate

Do not record a participant until:

```text
[ ] Participant ID assigned
[ ] Consent completed
[ ] Video/data-use permission completed
[ ] Participant understands the study/use
[ ] Withdrawal procedure explained
[ ] Collection environment ready
```

Participant names must not appear in sample filenames or model metadata.

Use:

```text
S001
S002
S003
...
```

---

# 6. Session ID

Every collection session receives a unique ID.

Example:

```text
SE001
SE002
SE003
```

A participant may have multiple sessions.

Never reuse a session ID.

---

# 7. Recording ID

Every attempted recording receives a unique sample ID.

Recommended:

```text
{SIGN_ID}_{SIGNER_ID}_{REPETITION}_{SESSION_ID}
```

Example:

```text
ASL_GO_S001_R01_SE001
```

Video:

```text
ASL_GO_S001_R01_SE001.mp4
```

Landmarks:

```text
ASL_GO_S001_R01_SE001.landmarks.json
```

Metadata:

```text
ASL_GO_S001_R01_SE001.json
```

---

# 8. Recording Sequence

For every sample:

```text
SELECT SIGN
    ↓
VERIFY SIGN ID
    ↓
VERIFY CAMERA FRAMING
    ↓
START RECORDING
    ↓
NEUTRAL PREPARATION
    ↓
NATURAL SIGN PERFORMANCE
    ↓
COMPLETION
    ↓
STOP RECORDING
    ↓
SAVE SAMPLE
    ↓
IMMEDIATE QC
```

Do not crop the temporal sequence during recording.

---

# 9. Camera Requirements

Initial baseline:

```text
Smartphone
Portrait
Stable camera
Face visible
Upper torso visible
Both hands visible
Adequate lighting
Uncluttered background
```

The camera should not be held by another person during the pilot unless that is specifically being tested.

---

# 10. Framing Check

Before the first sample of every session:

```text
[ ] Head fully visible
[ ] Face visible
[ ] Both shoulders visible
[ ] Upper torso visible
[ ] Both hands fit naturally inside frame
[ ] Signing space available
[ ] No severe shadows
[ ] No strong backlight
[ ] No severe glare
```

If the signer naturally requires more space, move the camera.

Do not force unnatural signing.

---

# 11. Recording Repetitions

Each sign:

```text
5 repetitions
```

per signer during the initial pilot.

The repetitions must be independent performances.

Do not copy or duplicate video files.

The signer should vary naturally in:

- speed;
- movement amplitude;
- timing;
- facial expression;
- articulation.

Do not deliberately distort the sign.

---

# 12. Operator Prompting

The operator should identify the intended ASL target without unnecessarily demonstrating the exact movement.

Preferred:

```text
SIGN ID → participant performs sign
```

Avoid repeatedly demonstrating the sign immediately before recording.

This reduces imitation artifacts.

For ambiguous concepts, use the exact validated candidate specification rather than an uncontrolled English instruction.

---

# 13. Directional Signs

Special handling is required for:

```text
GO
COME
GIVE
```

The operator must not arbitrarily force every participant to use the same direction if the intended construction is directional.

Record the intended spatial context in metadata when applicable.

Preserve:

```text
start locus
end locus
movement direction
```

---

# 14. Non-Manual Features

Participants should sign naturally.

Do not instruct them to:

- freeze their face;
- exaggerate facial expressions;
- artificially move their eyebrows;
- deliberately change eye gaze.

Capture natural performance.

For UNDERSTAND and other signs where non-manual information may matter, the face must remain visible.

---

# 15. Immediate Sample QC

Immediately after every recording, check:

```text
[ ] Correct sign performed
[ ] Complete sign captured
[ ] Hands visible
[ ] Face visible where required
[ ] No severe blur
[ ] No camera movement
[ ] No obstruction
[ ] File saved correctly
[ ] Correct sample ID
```

Possible result:

```text
ACCEPTED
RECORD_AGAIN
REJECTED
EXPERT_REVIEW
```

---

# 16. Do Not Delete Failed Samples

If a recording fails:

```text
sample → REJECTED
```

rather than silently deleting it.

Record:

```text
rejection_reason
reviewer
timestamp
```

This allows later analysis of why the collection process is failing.

---

# 17. Rejection Reasons

Use controlled reasons:

```text
WRONG_SIGN
INCOMPLETE_SIGN
HAND_OUT_OF_FRAME
FACE_OUT_OF_FRAME
SEVERE_BLUR
SEVERE_LIGHTING
CAMERA_MOVEMENT
OCCLUSION
CORRUPTED_FILE
LABEL_UNCERTAIN
LANDMARK_FAILURE
OTHER
```

---

# 18. Metadata

Minimum pilot metadata:

```json
{
  "sample_id": "ASL_GO_S001_R01_SE001",
  "sign_id": "ASL_GO",
  "gloss": "GO",
  "signer_id": "S001",
  "session_id": "SE001",
  "repetition_id": 1,
  "variant_id": null,
  "orientation": "portrait",
  "resolution": null,
  "fps": null,
  "duration_ms": null,
  "environment_id": "ENV001",
  "dominant_hand": null,
  "quality_status": "pending",
  "expert_validation_status": "pending"
}
```

Unknown information must remain `null`.

Never invent metadata.

---

# 19. Landmark Extraction

After raw-video QC:

```text
RAW VIDEO
    ↓
MediaPipe Holistic Landmarker
    ↓
FACE
LEFT HAND
RIGHT HAND
POSE
WORLD LANDMARKS
OPTIONAL FACE BLENDSHAPES
```

The raw video remains the source artifact.

Landmarks are derived data.

Do not delete the raw video merely because landmarks were extracted.

---

# 20. Landmark QC

For every sample calculate:

```text
face_presence_ratio
left_hand_presence_ratio
right_hand_presence_ratio
pose_presence_ratio
frame_count
frames_with_tracking_failure
duration
```

Flag samples with unusually poor tracking.

Do not automatically accept a sample just because the extractor produced a file.

---

# 21. Pilot Storage

Recommended structure:

```text
dataset/
├── pilot/
│   ├── raw/
│   ├── landmarks/
│   ├── metadata/
│   ├── quality/
│   ├── sessions/
│   └── reports/
```

Keep research data separate from the production SignVox application database.

---

# 22. Signer-Level Split

The pilot should already respect signer separation.

Example:

```text
TRAIN
S001
S002
S003
S004
S005

VALIDATION
S006

TEST
S007
```

The actual allocation depends on the number of recruited participants.

Do not place the same signer into multiple final evaluation groups.

---

# 23. Pilot Metrics

After collection, calculate:

```text
total_attempted
total_accepted
total_rejected
total_record_again
acceptance_rate
rejection_rate
landmark_failure_rate
hand_visibility_failure_rate
face_visibility_failure_rate
label_uncertainty_rate
```

Also calculate per sign:

```text
samples_per_sign
acceptance_rate_per_sign
tracking_failure_rate_per_sign
```

And per signer:

```text
samples_per_signer
acceptance_rate_per_signer
```

---

# 24. Technical Success Criteria

The pilot is technically successful if:

```text
[ ] Recording process is repeatable
[ ] Sample IDs remain unique
[ ] Metadata is complete
[ ] Raw files are recoverable
[ ] Landmark extraction works reliably
[ ] Hands remain trackable
[ ] Face remains trackable
[ ] Temporal sequences are complete
[ ] Directional movement is preserved
[ ] QC catches obvious failures
[ ] Backup procedure works
```

Do not define an arbitrary model-accuracy threshold for the pilot.

The pilot's primary goal is **pipeline validation**, not final recognition performance.

---

# 25. Linguistic Success Criteria

The pilot should also be reviewed for:

```text
[ ] Correct ASL form being performed
[ ] Variants documented
[ ] Directionality preserved
[ ] Non-manual features preserved
[ ] Confusion pairs represented
[ ] No accidental English-pantomime labeling
```

Any uncertain sign should be flagged for expert review.

---

# 26. Pilot Exit Review

After the pilot, produce:

```text
SIGNVOX_PILOT_REVIEW_REPORT.md
```

The report must answer:

### Collection

- Did the recording procedure work?
- Were instructions clear?
- How many recordings were accepted?

### Computer vision

- How reliable were hand landmarks?
- How reliable were face landmarks?
- Were important trajectories preserved?

### Data quality

- Which signs generated the most rejection?
- Which recording conditions caused problems?
- Were labels consistent?

### Human factors

- Was the session practical?
- Were participants comfortable?
- Did the procedure take too long?

---

# 27. Full Collection Authorization

Full ASL-100 collection remains blocked until the pilot review passes.

Gate:

```text
PILOT
  ↓
ANALYZE
  ↓
FIX PROBLEMS
  ↓
RE-PILOT IF NECESSARY
  ↓
ASL EXPERT REVIEW
  ↓
FULL COLLECTION AUTHORIZATION
```

Do not scale simply because the first recordings look good.

---

# 28. Important Product Architecture Rule

The dataset is being collected from recorded samples for **training and evaluation**.

The eventual SignVox application should support:

```text
LIVE CAMERA
    ↓
LIVE FRAMES
    ↓
LANDMARK EXTRACTION
    ↓
STREAMING TEMPORAL MODEL
    ↓
RECOGNITION
    ↓
LANGUAGE PROCESSING
    ↓
REAL-TIME OUTPUT
```

The research collection process must therefore preserve temporal information suitable for streaming inference.

Do not design the dataset around a batch-only assumption such as:

```text
upload 10-second video
→ wait
→ translate
```

That is not the intended SignVox product architecture.

---

# 29. Pilot Completion Definition

The pilot is complete only when:

```text
[ ] Planned participants recruited
[ ] Consent completed
[ ] Pilot recordings completed
[ ] Raw data verified
[ ] Metadata verified
[ ] Landmark extraction completed
[ ] QC completed
[ ] Rejections documented
[ ] Signer-level split created
[ ] Backup verified
[ ] Pilot metrics generated
[ ] Pilot review report completed
```

At that point the project makes a decision:

```text
PASS → authorize scaled collection
```

or:

```text
FAIL → fix → repeat pilot
```

---

# 30. Current Status

```text
DATA COLLECTION PROTOCOL       COMPLETE
PILOT PLAN                     COMPLETE
PILOT RECORDING                NOT STARTED
FULL COLLECTION                BLOCKED
TRAINING                       NOT STARTED
```

---

# 31. Core Rule

> **The pilot exists to discover problems before the problems are multiplied across the full dataset.**

Do not optimize for the number of videos collected.

Optimize for trustworthy, reproducible, linguistically meaningful data.
