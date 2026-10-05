# SignVox Dataset Design Specification

**Project:** SignVox  
**Target language:** American Sign Language (ASL) — initial prototype vocabulary  
**Vocabulary:** ASL-100 candidate vocabulary  
**Primary task:** Isolated sign recognition from short video sequences  
**Primary representation:** Temporal multimodal landmarks  
**Status:** DESIGN COMPLETE — DATA COLLECTION NOT STARTED  
**Document role:** Canonical dataset-design specification

---

## 1. Purpose

This document defines how SignVox will design, collect, label, quality-check, split, and version its ASL recognition dataset.

This is a **dataset design document**, not a data-collection authorization.

No training data should be collected under this specification until:

1. the relevant per-sign specifications have been completed;
2. ASL expert validation has been completed for the vocabulary/specifications;
3. this dataset design has been reviewed;
4. recording and consent procedures have been approved.

The goal is to prevent SignVox from collecting large amounts of data that later prove unsuitable for training or evaluation.

---

# 2. Dataset Objective

The first SignVox recognition model is intended to recognize a controlled vocabulary of approximately 100 ASL signs/concepts from short camera recordings.

The recognition problem is:

```text
Camera video
    ↓
Temporal sequence
    ↓
Holistic landmark extraction
    ↓
Manual + non-manual + pose features
    ↓
Temporal recognition model
    ↓
ASL sign/concept prediction
```

The dataset must therefore preserve:

- handshape
- hand orientation
- hand position
- movement
- movement direction
- hand-to-hand relationship
- body-relative location
- temporal sequence
- facial information
- head movement
- eye/face information where detectable
- upper-body posture
- signer variation
- spatial/directional information

The dataset must not reduce ASL to isolated hand poses.

---

# 3. Primary Dataset Unit

The fundamental dataset sample is a **short labeled video sequence**, not a single image.

Recommended conceptual unit:

```text
one sample
=
one signer
+
one intended sign/concept
+
one performance
+
one short temporal sequence
```

Example:

```text
Sample ID:
GO_S03_R04

GO
→ Signer 03
→ Repetition 04
→ complete temporal performance
```

Each original video should be preserved where permitted.

A derived landmark sequence should then be generated from that video.

```text
RAW VIDEO
    ↓
LANDMARK EXTRACTION
    ↓
NORMALIZATION
    ↓
LANDMARK SEQUENCE
    ↓
MODEL-READY SAMPLE
```

---

# 4. Dataset Modalities

## 4.1 Raw Video

Raw video is the source-of-truth recording when consent and storage permissions allow it.

Purpose:

- future re-processing;
- landmark extraction improvements;
- quality review;
- expert review;
- investigation of model failures.

Raw video should not automatically be uploaded to the production backend.

---

## 4.2 Landmark Sequence

The primary model input should be a temporal landmark representation.

The intended representation includes:

```text
Hands
+
Face
+
Pose / upper body
+
Temporal information
```

MediaPipe HolisticLandmarker provides face landmarks, pose landmarks, left/right hand landmarks, world landmarks, and optional face blendshapes, making it suitable for the planned preprocessing pipeline. citeturn0search0turn0search7

Each hand provides 21 landmarks in the current MediaPipe representation. citeturn0search3

The dataset pipeline should retain enough information to distinguish:

- left hand;
- right hand;
- dominant hand;
- non-dominant hand;
- both-hand interaction;
- hand disappearance/occlusion;
- spatial trajectory.

---

# 5. Model Input Representation

The canonical model-ready representation should conceptually be:

```text
X = [T × F]
```

where:

- `T` = temporal frames/timesteps
- `F` = normalized multimodal features

The exact feature vector should remain configurable until the preprocessing experiment is completed.

Do not hard-code a final feature count into the dataset specification prematurely.

Potential feature groups:

```text
RIGHT_HAND
LEFT_HAND
FACE
POSE
OPTIONAL_FACE_BLENDSHAPES
TEMPORAL_DERIVATIVES
VISIBILITY / PRESENCE MASKS
```

The model should receive missing-data indicators rather than silently treating undetected landmarks as real coordinates.

---

# 6. Recording Format

## 6.1 Camera

Primary collection device:

- modern smartphone camera;
- front-facing camera for the initial prototype;
- rear camera may be tested later;
- stable camera position;
- no intentional camera movement.

The initial dataset should optimize for the actual SignVox mobile use case rather than studio-only cameras.

---

## 6.2 Orientation

Primary:

```text
Portrait
```

Reason:

The SignVox prototype is mobile-first and the final interaction is expected to occur on a smartphone.

Landscape recordings may be collected as an auxiliary research condition but should not replace the primary portrait dataset.

---

## 6.3 Framing

Recommended framing:

```text
head
+
shoulders
+
upper torso
+
both hands
```

The signer should have enough space for signs that move away from the torso.

Do not crop tightly around the hands.

The face must remain visible.

---

## 6.4 Distance

Use a consistent baseline recording distance sufficient to keep:

- face visible;
- both hands visible;
- upper torso visible;
- movement space available.

The exact physical distance should be finalized during a small recording pilot.

Do not define a single distance as a universal requirement before testing different phone cameras.

---

# 7. Recording Environment

The dataset should deliberately contain controlled variation.

## Baseline conditions

Recordings should include:

- clean background;
- adequate lighting;
- no severe shadows;
- no strong backlighting;
- no distracting objects behind the signer;
- full visibility of face and hands.

## Controlled variation

Later collection rounds should deliberately introduce reasonable variation in:

- indoor lighting;
- outdoor lighting;
- background;
- clothing;
- camera distance;
- signer position.

The purpose is to prevent the model from learning the recording environment instead of the sign.

---

# 8. Signer Diversity

Signer diversity is a first-class dataset requirement.

The dataset should vary:

- signer identity;
- hand dominance;
- signing style;
- body proportions;
- hand size;
- skin tone;
- facial appearance;
- signing speed;
- movement amplitude;
- natural variation in articulation.

Where possible, recruit fluent/native or highly proficient ASL signers and document their language background.

The dataset must not rely on one signer performing every sign.

---

# 9. Signer-Independent Evaluation

This is mandatory.

A signer must not appear in both training and final test sets.

For example:

```text
Signer 01 → TRAIN
Signer 02 → TRAIN
Signer 03 → VALIDATION
Signer 04 → TEST
```

NOT:

```text
Signer 01 clips → TRAIN
Signer 01 other clips → TEST
```

The second arrangement can overestimate generalization because the model has already learned that person's appearance and signing characteristics.

Large ASL datasets such as ASL Citizen and MS-ASL explicitly evaluate generalization to people not present in training data. citeturn0academia24turn0academia26

---

# 10. Recommended Initial Dataset Size

The initial target should be treated as a **pilot target**, not a scientifically guaranteed minimum.

For approximately 100 signs:

### Phase A — pilot

```text
10 signers
×
10 repetitions
×
100 signs

= 10,000 candidate recordings
```

This is enough to expose collection and preprocessing problems before scaling.

### Phase B — expansion

Target approximately:

```text
20–30+ signers
×
10–20 repetitions
×
100 signs
```

This produces approximately:

```text
20,000–60,000 recordings
```

depending on final participation and repetition count.

The exact number should be revised after pilot analysis.

Existing research demonstrates the scale and signer diversity required for robust ASL recognition: ASL Citizen contains 83,399 videos from 52 signers, while MS-ASL contains more than 25,000 annotated videos involving more than 200 signers. These are reference points, not requirements that SignVox must immediately match. citeturn0academia24turn0academia26

---

# 11. Repetition Strategy

Do not record ten identical performances consecutively and assume they represent ten independent examples.

Instead:

```text
Repetition 1
Repetition 2
...
```

should allow natural variation in:

- timing;
- movement amplitude;
- starting position;
- ending position;
- facial expression;
- articulation.

The collection protocol should encourage natural signing rather than robotic repetition.

---

# 12. Temporal Capture

The complete sign movement must be captured.

A sample should include:

```text
PREPARATION
    ↓
SIGNING MOVEMENT
    ↓
COMPLETION
```

Do not crop the video so tightly that the model loses the beginning or end of the sign.

The temporal boundaries should eventually be annotated or automatically proposed and then reviewed.

---

# 13. Frame Rate

The recording device should use a stable, documented frame rate.

The canonical dataset metadata must record:

```text
fps
resolution
duration_ms
frame_count
```

Do not require a single frame rate across every future recording if the preprocessing pipeline can normalize sequences correctly.

The preprocessing stage should resample sequences to a model-compatible temporal representation while retaining enough information about the original recording.

---

# 14. Label Schema

Every sample requires a stable machine-readable label.

Recommended:

```json
{
  "sample_id": "GO_S03_R04",
  "sign_id": "ASL_GO",
  "gloss": "GO",
  "signer_id": "S03",
  "repetition_id": 4,
  "variant_id": null,
  "validation_status": "pending"
}
```

The exact JSON schema may evolve during implementation.

---

# 15. Required Metadata

Each recording should have metadata for:

### Identity

```text
sample_id
sign_id
gloss
category
```

### Signer

```text
signer_id
dominant_hand
language_background
proficiency_level
```

Avoid storing unnecessary personally identifying information inside the model dataset.

### Recording

```text
recording_id
device_id_or_device_class
camera_type
orientation
resolution
fps
duration
environment_id
```

### Sign

```text
variant_id
signing_style
directionality
one_or_two_handed
temporal_type
```

### Quality

```text
hand_visibility
face_visibility
pose_visibility
occlusion_level
lighting_quality
background_quality
landmark_quality
recording_quality
review_status
```

---

# 16. Privacy and Consent

Before collecting real people:

- obtain informed consent;
- explain the research/product purpose;
- explain where recordings will be stored;
- explain who can access them;
- explain whether recordings may be used for model training;
- define withdrawal procedures;
- avoid collecting unnecessary personal information.

Raw videos should be treated as sensitive research assets.

The production SignVox backend should not be used as the raw dataset repository by default.

---

# 17. Dataset Directory Structure

Recommended:

```text
dataset/
├── README.md
├── VERSION
├── vocabulary/
│   ├── asl_100.csv
│   └── sign_specs/
│
├── raw/
│   ├── signer_S01/
│   ├── signer_S02/
│   └── ...
│
├── metadata/
│   ├── samples.csv
│   ├── signers.csv
│   ├── environments.csv
│   └── collection_sessions.csv
│
├── landmarks/
│   ├── train/
│   ├── validation/
│   └── test/
│
├── splits/
│   ├── train.csv
│   ├── validation.csv
│   └── test.csv
│
├── quality/
│   ├── rejected.csv
│   ├── review_queue.csv
│   └── quality_reports/
│
└── documentation/
    ├── collection_protocol.md
    ├── labeling_protocol.md
    └── consent_protocol.md
```

---

# 18. Train / Validation / Test Split

The split must occur at the **signer level**.

Conceptual target:

```text
TRAIN
~70%

VALIDATION
~15%

TEST
~15%
```

The exact percentages may change depending on the number of available signers.

The important rule is:

```text
NO SIGNER OVERLAP
```

between the final train, validation, and test groups.

A second evaluation set should eventually be considered:

```text
REAL-WORLD / FIELD TEST
```

This set should contain naturally recorded smartphone interactions that differ from the controlled collection environment.

---

# 19. Sign Distribution

Every sign should have approximately comparable representation during the pilot.

Avoid:

```text
GO → 2,000 samples
RARE SIGN → 100 samples
```

unless there is a documented reason.

Class imbalance should be measured before training.

Track:

```text
samples_per_sign
samples_per_signer
samples_per_variant
```

---

# 20. Directional and Spatial Signs

Some signs cannot be represented adequately by a static class label alone.

Examples include signs where movement direction carries participant or spatial information.

For these signs, metadata should preserve:

```text
start_location
end_location
movement_vector
spatial_locus
gaze_direction
participant_role
```

The dataset must not normalize away the information that makes the sign linguistically meaningful.

This is especially important for signs such as:

```text
GIVE
TAKE
HELP
GO
COME
```

---

# 21. Non-Manual Information

The dataset must preserve non-manual information.

Relevant features may include:

```text
facial expression
eyebrow position
eye gaze
head movement
head tilt
mouth movement
body movement
torso orientation
```

These should not automatically be converted into rigid categorical labels during collection.

First preserve the underlying visual/landmark information.

The model can learn which dimensions matter.

---

# 22. Confusion-Pair Design

The collection protocol must deliberately include signs that can be confused visually.

Examples from our sign specifications:

```text
GOOD ↔ THANK-YOU
PLEASE ↔ SORRY
MOTHER ↔ FATHER
BROTHER ↔ SISTER
CHILD ↔ BABY
I/ME ↔ YOU
```

These should receive explicit evaluation attention.

For every major confusion pair:

```text
collect both classes
+
ensure signer diversity
+
test similar recording conditions
+
evaluate confusion matrix
```

---

# 23. Hard Negatives

A hard negative is a sample whose visual characteristics resemble another class but whose correct label is different.

The dataset should eventually contain:

```text
easy examples
+
normal examples
+
hard examples
```

This is more useful than collecting only perfectly clean textbook performances.

---

# 24. Quality-Control Pipeline

Every recording should pass:

```text
RAW RECORDING
    ↓
FILE VALIDATION
    ↓
VIDEO QUALITY CHECK
    ↓
LANDMARK EXTRACTION
    ↓
LANDMARK QUALITY CHECK
    ↓
LABEL CHECK
    ↓
DUPLICATE CHECK
    ↓
SIGNER/SPLIT CHECK
    ↓
ACCEPT / REJECT
```

---

# 25. Recording Rejection Conditions

Reject or flag recordings when:

- the sign is not completed;
- hands leave the frame;
- face is severely occluded;
- important movement is missing;
- recording is corrupted;
- severe blur occurs;
- severe lighting prevents landmark detection;
- camera moves excessively;
- wrong sign is performed;
- label is uncertain;
- another person interferes with the frame;
- landmark extraction fails for a substantial portion of the sequence.

Do not silently delete rejected recordings.

Record:

```text
sample_id
rejection_reason
reviewer
timestamp
```

---

# 26. Landmark Quality

The preprocessing system should calculate landmark presence/quality statistics.

At minimum:

```text
right_hand_presence_ratio
left_hand_presence_ratio
face_presence_ratio
pose_presence_ratio
```

For each sequence.

A sample with poor landmark coverage should be flagged before entering training.

---

# 27. Missing Landmarks

Missing landmarks are expected in real-world computer vision.

Do not automatically convert:

```text
missing = [0,0,0]
```

without a mask.

Instead maintain:

```text
landmark_coordinates
+
visibility/presence mask
```

This allows the model to distinguish:

```text
landmark genuinely near coordinate 0
```

from:

```text
landmark not detected
```

---

# 28. Normalization

Landmarks should eventually be normalized to reduce irrelevant variation.

Potential normalization references:

```text
body center
shoulder center
shoulder width
torso orientation
hand-relative-to-body position
```

However, normalization must not destroy linguistically meaningful spatial information.

Therefore:

```text
INVARIANT FEATURES
+
PRESERVED SPATIAL FEATURES
```

should coexist.

This is especially important for directional signs and spatial indexing.

---

# 29. Data Augmentation

Augmentation should be introduced only after baseline data quality is established.

Possible later augmentations:

- small temporal speed changes;
- small spatial translations;
- limited scale changes;
- controlled landmark noise;
- frame dropout;
- limited camera noise simulation.

Avoid augmentations that change the linguistic meaning of the sign.

Do not mirror every sample blindly.

For directional or asymmetric signs, horizontal mirroring can change or distort the intended linguistic representation.

---

# 30. Dataset Leakage Controls

The pipeline must detect:

### Signer leakage

Same signer across train/test.

### Recording-session leakage

Nearly identical recordings from the same session across splits.

### Duplicate leakage

The same or near-identical clip appearing in multiple splits.

### Environment leakage

If all examples of a sign are recorded in one environment while another sign is recorded elsewhere, the model may learn the environment.

### Temporal leakage

Do not split adjacent frames from the same performance into different datasets.

The **entire performance** belongs to exactly one split.

---

# 31. Versioning

Every dataset release should have a version.

Example:

```text
SignVox-ASL100-v0.1.0
```

Version semantics:

```text
MAJOR → vocabulary/schema breaking change
MINOR → additional validated data/signers
PATCH → metadata/quality correction
```

Each version must document:

```text
number of signs
number of signers
number of recordings
number of accepted samples
number of rejected samples
split composition
known limitations
```

---

# 32. Dataset Manifest

Every release should have a machine-readable manifest.

Example:

```json
{
  "dataset_name": "SignVox-ASL100",
  "version": "0.1.0",
  "language": "ASL",
  "sign_count": 100,
  "signer_count": 0,
  "sample_count": 0,
  "status": "design_only",
  "collection_started": false,
  "expert_validation_complete": false
}
```

The initial repository version should explicitly show:

```text
collection_started = false
```

until collection actually begins.

---

# 33. Dataset Stages

The dataset itself should move through controlled stages.

```text
DESIGN
  ↓
PILOT
  ↓
QUALITY REVIEW
  ↓
COLLECTION
  ↓
LABEL VALIDATION
  ↓
LANDMARK EXTRACTION
  ↓
DATASET FREEZE
  ↓
TRAINING
```

Do not train from an uncontrolled working directory.

---

# 34. Dataset Freeze

Before the first serious model-training run, create a frozen dataset version.

Example:

```text
SignVox-ASL100-v0.1.0
```

The training experiment must record exactly which dataset version it used.

This makes experiments reproducible.

---

# 35. Recommended Pilot

Before collecting tens of thousands of recordings, conduct a small pilot.

Recommended:

```text
5–10 signers
×
10–20 representative signs
×
5–10 repetitions
```

The pilot should test:

- framing;
- lighting;
- landmark extraction;
- temporal segmentation;
- metadata;
- file sizes;
- storage;
- signer variation;
- hand visibility;
- face visibility;
- model preprocessing;
- recording instructions.

Only after the pilot passes should full ASL-100 collection begin.

---

# 36. Representative Pilot Signs

The pilot should deliberately include different technical classes.

### Static / low-motion

```text
MOTHER
FATHER
```

### Fine hand movement

```text
WAIT
```

### Two-handed interaction

```text
STOP
FAMILY
```

### Directional

```text
HELP
GIVE
GO
```

### Face/body dependent

```text
UNDERSTAND
DON'T-UNDERSTAND
```

### Similar/confusable

```text
GOOD
THANK-YOU
PLEASE
SORRY
```

This gives much more information than randomly choosing 10 signs.

---

# 37. Dataset Success Criteria

The dataset design is considered ready for collection when:

- all 100 sign specifications are complete;
- expert validation has been completed or explicitly marked pending according to project governance;
- collection protocol is approved;
- consent procedure exists;
- metadata schema is finalized;
- split strategy is finalized;
- quality-control pipeline is defined;
- pilot protocol is ready;
- repository structure is ready.

Dataset design completion does **not** mean the model is ready.

---

# 38. Current SignVox Status

```text
Research                         COMPLETE
ASL-100 candidate vocabulary    COMPLETE
Per-sign specification           IN PROGRESS
ASL expert validation            PENDING EXPERT REVIEW
Dataset design                   COMPLETE
Dataset collection               NOT STARTED
Dataset labeling                 NOT STARTED
Landmark extraction              NOT STARTED
Model training                   NOT STARTED
Model evaluation                 NOT STARTED
Mobile integration               NOT STARTED
```

---

# 39. Immediate Next Step

The next implementation-independent step is:

```text
COMPLETE PER-SIGN SPECIFICATIONS
            ↓
EXPERT VALIDATION
            ↓
REVIEW THIS DATASET DESIGN
            ↓
RUN SMALL DATA-COLLECTION PILOT
            ↓
FREEZE DATASET PROTOCOL
            ↓
FULL DATA COLLECTION
```

No model-training implementation should begin merely because the dataset design is complete.

---

# 40. Canonical Principle

> **Collect data for the model we actually intend to deploy, not merely data that is easy to collect.**

For SignVox, that means designing around:

```text
mobile camera
+
temporal video
+
hands
+
face
+
upper-body pose
+
signer variation
+
spatial information
+
non-manual information
+
signer-independent evaluation
```

The dataset should therefore be treated as a linguistic and machine-learning asset, not simply a folder of videos.
