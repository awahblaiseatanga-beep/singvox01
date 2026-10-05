# SignVox Data Collection Protocol

**Project:** SignVox  
**Target language:** American Sign Language (ASL) — initial prototype  
**Dataset:** ASL-100  
**Protocol version:** v0.1.0  
**Status:** COLLECTION PROTOCOL — PILOT NOT YET STARTED  
**Purpose:** Controlled protocol for collecting provisional ASL video and landmark data for SignVox research

> **Critical status:** This document authorizes the *design of the collection process*, not automatic permission to record people. Human-participant consent and any applicable institutional/ethical review must be completed before participant recordings begin.

---

# 1. Purpose

This protocol defines exactly how SignVox will conduct its first ASL data-collection pilot.

The purpose is to produce consistent, ethically collected, machine-learning-ready recordings while preserving the linguistic information needed for ASL recognition.

The protocol covers:

- participant recruitment;
- participant eligibility;
- consent;
- video-release permission;
- recording setup;
- signer instructions;
- recording sessions;
- repetition strategy;
- metadata;
- file naming;
- quality control;
- landmark extraction;
- rejection/re-recording;
- privacy and storage;
- dataset splitting;
- versioning;
- pilot exit criteria.

This protocol does **not** define the ASL linguistic ground truth. That comes from the per-sign specifications and subsequent ASL-expert validation.

---

# 2. Current Collection Status

```text
ASL-100 vocabulary                 COMPLETE
Per-sign specifications             30/100 COMPLETE
ASL expert validation                PENDING
Dataset design                       COMPLETE
Collection protocol                 COMPLETE
Human-participant approval           REQUIRED/TO BE CHECKED
Pilot collection                    NOT STARTED
Full collection                     NOT AUTHORIZED YET
Training                            NOT STARTED
```

The first collection activity should be a **pilot**, not full ASL-100 production collection.

---

# 3. Non-Negotiable Collection Gates

No participant recording begins until the following have been checked:

```text
[ ] Collection protocol reviewed
[ ] Applicable university/institutional requirements checked
[ ] Applicable ethics/human-subject requirements checked
[ ] Consent process prepared
[ ] Video-release/data-use permission prepared
[ ] Participant information provided in an accessible form
[ ] Secure storage location prepared
[ ] Recording device tested
[ ] Backup procedure tested
[ ] File naming scheme tested
[ ] Metadata schema tested
[ ] Pilot sign list approved
[ ] ASL expert review status documented
```

Do not interpret the absence of an institutional IRB requirement as permission to ignore informed consent or participant privacy.

Gallaudet's human-subjects guidance emphasizes informed consent, protection of participant rights and welfare, confidentiality, and appropriate consent procedures. It also provides separate informed-consent and video-release resources for recorded research. These are reference practices, not a determination that SignVox itself falls under Gallaudet's procedures. [Gallaudet human-subjects policy](https://gallaudet.edu/operations/administration-and-operation-manual/303-protection-of-human-subjects-in-research-projects/) and [Gallaudet IRB sample documents](https://gallaudet.edu/institutional-review-board/irb-sample-documents/).

---

# 4. Collection Philosophy

The goal is **not** to collect the largest number of videos as quickly as possible.

The goal is to collect data that is:

```text
LINGUISTICALLY VALID
+
VISUALLY CLEAR
+
TEMPORALLY COMPLETE
+
DIVERSE
+
TRACEABLE
+
ETHICALLY COLLECTED
+
REPRODUCIBLE
```

A small high-quality pilot is more valuable than thousands of poorly controlled samples.

---

# 5. Collection Phases

The collection process has four stages.

```text
PHASE 0
Preparation
    ↓
PHASE 1
Pilot collection
    ↓
PHASE 2
Pilot analysis
    ↓
PHASE 3
Full collection authorization
```

Do not jump directly from preparation to full collection.

---

# 6. Phase 0 — Preparation

Before the first participant:

### Technical preparation

- smartphone camera tested;
- storage capacity verified;
- battery/charging plan verified;
- camera resolution documented;
- frame rate documented;
- portrait orientation tested;
- MediaPipe landmark extraction tested;
- raw-video backup tested;
- metadata entry tested.

### Research preparation

- participant information prepared;
- consent form prepared;
- video/data-use permission prepared;
- withdrawal procedure documented;
- participant ID system prepared;
- recording session checklist prepared;
- collection log prepared.

### Linguistic preparation

The collection team must know:

- which exact sign is being requested;
- the approved gloss;
- known variants;
- known confusion pairs;
- whether a sign is directional;
- whether non-manual features matter;
- whether a sign requires a specific spatial setup.

Do not improvise ASL labels during recording.

---

# 7. Participant Recruitment

The pilot should prioritize participants who can provide reliable ASL signing.

Record relevant language-background information without collecting unnecessary personal information.

Potential participant metadata:

```text
signer_id
ASL_proficiency_category
language_background
dominant_hand
age_band
consent_status
video_release_status
```

Avoid storing names, phone numbers, addresses, or other unnecessary identifying information inside the model dataset.

Participant identity records, if needed, should be maintained separately from the machine-learning dataset.

---

# 8. Participant ID

Never use the participant's name as the dataset identifier.

Use:

```text
S001
S002
S003
...
```

The mapping between:

```text
S001 → real participant identity
```

must be stored separately with restricted access.

The model dataset should only see:

```text
signer_id = S001
```

---

# 9. Consent

Before recording, the participant must understand:

- the purpose of SignVox;
- what they will be asked to do;
- that video will be recorded;
- how recordings will be used;
- whether recordings will be used for machine-learning research;
- where recordings will be stored;
- who may access them;
- whether results may be published or demonstrated;
- whether participation is voluntary;
- how withdrawal works;
- whom to contact with questions.

Participation must not depend on the participant agreeing to something they were not informed about.

For video datasets, consent should specifically address the recording and intended use of video. Gallaudet provides separate informed-consent and video-release examples for recorded research. [Gallaudet informed consent/video release](https://gallaudet.edu/schuchman-documentary-center/informed-consent-and-video-release/).

---

# 10. Withdrawal

The project must define a practical withdrawal procedure before collection begins.

At minimum, document:

```text
withdrawal_request_id
participant_id
date
scope_of_withdrawal
action_taken
```

Do not promise deletion beyond what the project's consent/data-retention policy can actually support.

The consent materials must explain the withdrawal rules accurately.

---

# 11. Accessibility of the Collection Process

The collection process must be accessible to sign-language users.

Instructions may be provided through:

- ASL;
- written English;
- captions;
- demonstration video;
- qualified interpreter, where necessary.

Do not rely exclusively on spoken English instructions for Deaf participants.

The goal is informed participation, not merely obtaining a signature.

---

# 12. Pilot Size

Initial pilot target:

```text
5–10 signers
×
10–20 representative signs
×
5–10 repetitions
```

This is a **pilot target**, not the final dataset size.

The pilot exists to determine:

- whether the recording setup works;
- whether landmarks are reliable;
- whether instructions are understandable;
- whether metadata is sufficient;
- whether labels are being applied consistently;
- whether signs are fully captured;
- whether the quality-control system works.

---

# 13. Pilot Sign Selection

The pilot should deliberately cover different recognition challenges.

Recommended pilot set:

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
GOOD
THANK-YOU
PLEASE
SORRY
```

If the pilot must be smaller, prioritize:

```text
GO
COME
GIVE
STOP
WAIT
MOTHER
UNDERSTAND
GOOD
THANK-YOU
PLEASE
SORRY
```

This is intentionally not a random sample.

---

# 14. Why These Pilot Signs

They stress different parts of the system:

| Sign type | Example |
|---|---|
| Simple dynamic | HELLO |
| Fine movement | WAIT |
| Two-hand interaction | STOP |
| Body-relative location | MOTHER |
| Two-hand relationship | FAMILY |
| Directional | GO |
| Opposite directional | COME |
| Transfer/directional | GIVE |
| Non-manual/contextual | UNDERSTAND |
| Confusion pair | GOOD / THANK-YOU |
| Confusion pair | PLEASE / SORRY |

A successful pilot must demonstrate that the pipeline can preserve these differences.

---

# 15. Recording Environment

Primary pilot environment:

- quiet indoor space;
- stable camera;
- sufficient lighting;
- uncluttered background;
- no strong backlighting;
- enough room for full signing movement;
- no unnecessary people moving behind signer.

The environment should be documented.

Do not require a perfectly artificial studio.

SignVox ultimately targets smartphone use, so the pilot should establish a controlled baseline and later introduce realistic variation.

---

# 16. Camera Position

Initial baseline:

```text
smartphone
portrait orientation
stable position
approximately chest/face centered
```

The exact physical camera distance should be established during the pilot rather than guessed permanently.

The framing must include:

```text
head
face
shoulders
upper torso
both hands
```

with enough space for hand movement.

---

# 17. Camera Framing Test

Before each session, perform a framing check.

```text
[ ] Full head visible
[ ] Face visible
[ ] Both shoulders visible
[ ] Upper torso visible
[ ] Both hands can reach signing space without leaving frame
[ ] No severe crop
[ ] No strong glare
[ ] No severe shadows
[ ] Background acceptable
```

If a signer naturally uses a larger signing space, adjust the camera position rather than asking them to artificially shrink the sign.

---

# 18. Recording Orientation

Primary:

```text
PORTRAIT
```

This matches the intended mobile-first SignVox interaction.

Record the orientation in metadata:

```text
orientation = portrait
```

Do not rotate files after recording without preserving the original orientation metadata.

---

# 19. Recording Settings

Record and store:

```text
resolution
fps
duration
orientation
device_class
camera_type
```

Use a stable baseline recording configuration during the pilot.

Do not optimize for maximum resolution at the expense of storage, processing, or mobile realism.

The pilot should determine whether the selected configuration produces sufficiently reliable hand and face landmarks.

---

# 20. Signer Position

The signer should begin from a neutral position.

Recommended:

```text
face toward camera
upper torso visible
hands initially inside frame
```

The signer should then perform the sign naturally.

Do not force an unnatural pose solely to make computer vision easier.

---

# 21. Recording One Sample

The collection operator should use the following sequence:

```text
1. Select sign
2. Confirm participant ID
3. Confirm sign ID
4. Confirm camera framing
5. Start recording
6. Allow neutral preparation
7. Sign naturally
8. Allow completion
9. Stop recording
10. Save sample
11. Enter metadata
12. Perform immediate quality check
```

Do not start and stop recording halfway through a sign.

---

# 22. Temporal Boundaries

Each sample should contain:

```text
PREPARATION
+
SIGN
+
COMPLETION
```

Do not crop away the preparation or ending until the segmentation policy has been finalized.

Later preprocessing may generate a model-ready temporal window.

---

# 23. Repetition Protocol

Each repetition must be a separate sample.

Do not duplicate one video file and call the copies separate repetitions.

Example:

```text
GO_S001_R01.mp4
GO_S001_R02.mp4
GO_S001_R03.mp4
...
```

The signer should perform each repetition naturally.

Avoid:

```text
same exact movement
same exact speed
same exact timing
```

for every repetition.

Natural variation is valuable.

---

# 24. Between-Repetition Procedure

After each repetition:

```text
[ ] sample saved
[ ] file opens
[ ] label correct
[ ] complete sign visible
[ ] hands visible
[ ] face visible
[ ] no major interruption
```

If the sample fails, mark it as rejected/re-record rather than silently replacing it.

---

# 25. Sign Prompting

The collection operator should not demonstrate the sign immediately before every recording.

Demonstrating the exact target repeatedly can cause:

- imitation artifacts;
- unnatural timing;
- reduced variation.

Preferred workflow:

```text
prompt/sign name
    ↓
participant prepares
    ↓
participant produces sign
```

If demonstration is necessary, document that condition in metadata.

---

# 26. Avoiding English-to-ASL Contamination

The collection operator must not tell the participant:

```text
"Make the English word TAKE."
```

Instead use the validated ASL target/gloss.

For ambiguous English concepts:

```text
TAKE
SEE
LIKE
NEED
```

the exact ASL construction must be specified before recording.

Example:

```text
ASL_TAKE_FROM
```

rather than an uncontrolled English “take” category.

---

# 27. Directional Signs

For directional signs such as:

```text
GO
COME
GIVE
HELP
```

the recording protocol must preserve the intended spatial direction.

Do not instruct every participant to perform the sign in one arbitrary direction if direction is linguistically meaningful.

Metadata should capture:

```text
start_locus
end_locus
direction
```

where applicable.

---

# 28. Non-Manual Features

Participants should sign naturally.

Do not tell them:

```text
"Keep your face neutral."
```

unless the target specification specifically requires neutral expression.

Preserve:

- facial expression;
- eyebrow movement;
- head movement;
- eye gaze;
- mouth movement;
- body movement.

These may carry linguistic information.

---

# 29. No Forced Facial Exaggeration

The collection team must not instruct participants to exaggerate facial expressions merely to make the dataset easier.

Record natural signing.

If a non-manual marker is important for a sign, the ASL expert should specify how it should be represented and evaluated.

---

# 30. File Naming Convention

Recommended:

```text
{SIGN_ID}_{SIGNER_ID}_{REPETITION}_{SESSION}.mp4
```

Example:

```text
ASL_GO_S001_R01_SE01.mp4
```

For a variant:

```text
ASL_GO_V01_S001_R01_SE01.mp4
```

The filename must never contain the participant's real name.

---

# 31. Sample ID

Each sample receives a unique immutable ID.

Example:

```text
GO_S001_R01_SE01
```

The sample ID should be referenced by:

- raw video;
- metadata;
- landmark file;
- QC record;
- rejection record;
- dataset split.

---

# 32. Metadata Record

Each accepted or rejected recording must have a metadata record.

Minimum:

```json
{
  "sample_id": "GO_S001_R01_SE01",
  "sign_id": "ASL_GO",
  "gloss": "GO",
  "signer_id": "S001",
  "repetition_id": 1,
  "session_id": "SE01",
  "variant_id": null,
  "orientation": "portrait",
  "resolution": null,
  "fps": null,
  "duration_ms": null,
  "environment_id": "ENV01",
  "dominant_hand": null,
  "quality_status": "pending",
  "expert_validation_status": "pending"
}
```

Fields with unknown values must remain explicitly unknown/null rather than being invented.

---

# 33. Metadata Must Not Become Linguistic Ground Truth

Metadata describes the recording.

It does not replace expert linguistic validation.

For example:

```text
gloss = "TAKE"
```

does not prove that the recording is the correct ASL TAKE construction.

The dataset must distinguish:

```text
candidate label
```

from:

```text
expert-validated label
```

---

# 34. Quality Status

Each sample should have one of:

```text
PENDING
ACCEPTED
REJECTED
RECORD_AGAIN
EXPERT_REVIEW
```

Do not delete rejected samples from the audit trail.

---

# 35. Immediate Rejection Conditions

Reject/re-record if:

- wrong sign performed;
- sign incomplete;
- hands leave frame during important movement;
- face is unavailable when required;
- severe blur;
- severe exposure problem;
- camera moves substantially;
- another person obstructs the signer;
- recording is corrupted;
- label is uncertain;
- landmark extraction is unusable;
- participant did not follow the recording protocol.

---

# 36. Do Not Reject Natural Variation

Do not reject a sample merely because:

- movement is slightly faster;
- movement amplitude differs naturally;
- facial expression differs naturally;
- signer uses a valid variant;
- hand position differs within the validated range.

The goal is not to collect identical performances.

---

# 37. Landmark Extraction

After raw-video QC:

```text
RAW VIDEO
    ↓
MediaPipe Holistic Landmarker
    ↓
face landmarks
left hand
right hand
pose
world landmarks
optional face blendshapes
```

MediaPipe's Holistic Landmarker documentation describes the combined face, pose, and left/right hand outputs used for this type of multimodal tracking.

The original raw video must remain the source artifact.

Landmarks are derived artifacts.

---

# 38. Landmark Quality Metrics

For every sequence, calculate at least:

```text
face_presence_ratio
left_hand_presence_ratio
right_hand_presence_ratio
pose_presence_ratio
```

Also track:

```text
frame_count
frames_with_tracking_failure
sequence_duration
```

A sample should not automatically be accepted simply because landmark extraction completed.

---

# 39. Missing Landmark Policy

Never encode missing landmarks as ordinary coordinates without a mask.

Store:

```text
landmark_coordinates
+
presence/visibility information
```

This allows the model to distinguish:

```text
landmark not detected
```

from:

```text
landmark genuinely at coordinate
```

---

# 40. Raw Video Preservation

Raw recordings are the source-of-truth artifacts.

Do not overwrite them with:

- cropped versions;
- resized versions;
- augmented versions;
- landmark-rendered videos.

Derived versions should have separate filenames/directories.

---

# 41. Storage Architecture

Recommended conceptual structure:

```text
dataset/
├── raw/
├── landmarks/
├── metadata/
├── quality/
├── splits/
└── documentation/
```

Raw videos should not automatically be stored in the SignVox production application database.

The production backend and research dataset should remain separate.

---

# 42. Backup Strategy

At least two independent copies should exist for accepted pilot data before deleting any local working copy.

Example:

```text
PRIMARY STORAGE
        +
BACKUP STORAGE
```

Backups must be access-controlled.

Gallaudet's research guidance also recommends considering multiple backups for recorded research data. citeturn0search2

---

# 43. Access Control

Separate:

```text
Participant identity records
```

from:

```text
Machine-learning dataset
```

Only authorized project personnel should access identifiable information.

The ML dataset should use:

```text
S001
S002
...
```

rather than names.

---

# 44. Dataset Splitting

Never split individual repetitions randomly if doing so causes the same signer to appear in all sets.

Primary rule:

```text
TRAIN signer set
≠
VALIDATION signer set
≠
TEST signer set
```

A signer must not appear in multiple final evaluation splits.

ASL Citizen demonstrated the importance of evaluating on users absent from training and validation. citeturn0academia24

---

# 45. Pilot Split

For the pilot, maintain a provisional signer-level split.

Example:

```text
TRAIN
S001–S006

VALIDATION
S007

TEST
S008
```

The exact allocation depends on actual recruitment.

Do not publish performance numbers from a pilot split as if they represented final model performance.

---

# 46. Collection Session Log

Each session should record:

```text
session_id
date
operator_id
signer_id
environment_id
device_class
camera_configuration
start_time
end_time
number_attempted
number_accepted
number_rejected
notes
```

This makes failures traceable.

---

# 47. Collection Operator Checklist

Before session:

```text
[ ] Consent verified
[ ] Video permission verified
[ ] Signer ID assigned
[ ] Camera tested
[ ] Storage available
[ ] Backup available
[ ] Lighting checked
[ ] Framing checked
[ ] Metadata session created
```

During session:

```text
[ ] Correct sign selected
[ ] Correct prompt given
[ ] Recording started
[ ] Full sign captured
[ ] Sample saved
[ ] Metadata entered
[ ] QC performed
```

After session:

```text
[ ] Files verified
[ ] Backup completed
[ ] Rejected samples logged
[ ] Session closed
[ ] QC summary generated
```

---

# 48. Pilot Quality Review

After the first pilot batch, calculate:

```text
acceptance_rate
rejection_rate
re-record_rate
landmark_failure_rate
hand_visibility_failure_rate
face_visibility_failure_rate
label_uncertainty_rate
```

Also inspect:

```text
samples_per_sign
samples_per_signer
samples_per_environment
```

---

# 49. Pilot Failure Thresholds

The following are **engineering review triggers**, not scientific universal thresholds:

If any of these are high enough to threaten dataset usefulness:

```text
frequent hand loss
frequent face loss
frequent wrong labels
frequent landmark failure
frequent incomplete signs
frequent camera motion
```

stop scaling and fix the collection process.

Do not compensate for a broken collection process by simply collecting more data.

---

# 50. Pilot Review Questions

After the pilot, answer:

### Linguistic

- Are participants performing the intended ASL forms?
- Are variants appearing?
- Are English prompts causing ambiguity?
- Are directional signs being captured correctly?

### Computer vision

- Are both hands reliably detected?
- Is the face reliably detected?
- Are important trajectories preserved?
- Are temporal boundaries usable?

### Dataset

- Are labels consistent?
- Is metadata sufficient?
- Are filenames unique?
- Are rejected samples traceable?

### Human factors

- Are instructions understandable?
- Is the session tiring?
- Is the recording setup intrusive?
- Are participants comfortable?

---

# 51. Full Collection Gate

Full ASL-100 collection should begin only after the pilot review answers:

```text
[ ] Recording setup validated
[ ] Metadata validated
[ ] Storage validated
[ ] Backup validated
[ ] Landmark pipeline validated
[ ] QC process validated
[ ] Participant process validated
[ ] Labeling process validated
[ ] Major linguistic ambiguities resolved
[ ] ASL expert review incorporated where required
```

If any critical item fails:

```text
STOP
→ FIX
→ RE-PILOT
```

Do not scale first and repair later.

---

# 52. Expert Validation Gate

The dataset must maintain a distinction between:

```text
SOURCE-SUPPORTED
```

and:

```text
EXPERT-CONFIRMED
```

A sample should not receive:

```text
expert_confirmed = true
```

simply because it resembles a reference video or dictionary entry.

The actual ASL expert review must determine:

- lexical correctness;
- acceptable variants;
- directional interpretation;
- non-manual requirements;
- label boundaries;
- whether a candidate class should be split or merged.

---

# 53. Dataset Versioning

Pilot release:

```text
SignVox-ASL100-PILOT-v0.1.0
```

Production dataset versions should only be created after the pilot is reviewed.

Every version records:

```text
vocabulary_version
protocol_version
signer_count
sample_count
accepted_count
rejected_count
split_definition
expert_validation_status
known_limitations
```

---

# 54. Never Modify Historical Samples In Place

If a sample is corrected:

```text
old record → preserved
new record → new version
```

Do not silently overwrite historical metadata.

Dataset reproducibility requires knowing what changed.

---

# 55. Data Collection Do-Not-Do List

Do NOT:

- record people without appropriate consent;
- store names inside sample IDs;
- upload raw participant videos to the production app by default;
- invent ASL labels;
- merge English homonyms into one ASL class;
- force participants to exaggerate signs;
- crop out meaningful movement;
- remove facial information;
- mirror all samples automatically;
- split the same signer across final train/test;
- duplicate one recording as multiple samples;
- delete rejected samples without an audit record;
- start full collection before the pilot is reviewed;
- treat pilot accuracy as final model performance.

---

# 56. Pilot Deliverables

The pilot is complete only when the project has:

```text
raw videos
+
metadata
+
landmark sequences
+
quality reports
+
rejection log
+
signer-level split
+
session logs
+
backup
+
pilot review report
```

---

# 57. Final Collection Principle

The SignVox dataset should represent:

```text
REAL SIGNERS
+
REAL TEMPORAL MOVEMENT
+
REAL ASL VARIATION
+
MANUAL FEATURES
+
NON-MANUAL FEATURES
+
SPATIAL INFORMATION
+
MOBILE-CAMERA CONDITIONS
```

while maintaining:

```text
CONSENT
+
PRIVACY
+
TRACEABILITY
+
QUALITY CONTROL
+
SIGNER-INDEPENDENT EVALUATION
```

---

# 58. Current Decision

```text
DATA COLLECTION PROTOCOL       COMPLETE
PILOT COLLECTION               NOT STARTED
FULL COLLECTION                BLOCKED
```

The next action is **not** “record all 100 signs.”

The next action is:

```text
REVIEW PROTOCOL
      ↓
COMPLETE ETHICS/CONSENT CHECK
      ↓
RUN TECHNICAL PILOT
      ↓
REVIEW PILOT
      ↓
AUTHORIZE FULL COLLECTION
```

---

# 59. Canonical Rule

> **Never scale a data-collection process that has not passed a small controlled pilot.**

SignVox should optimize for trustworthy data first and dataset size second.
