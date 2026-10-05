# SignVox ASL-100 Per-Sign Specifications — Batch 03

**Batch:** 03  
**Coverage:** GO, COME, GIVE, TAKE, WANT, NEED, HAVE, KNOW, LIKE, SEE  
**Status:** RESEARCH SPECIFICATION COMPLETE — EXPERT VALIDATION PENDING  
**Dataset status:** NOT COLLECTED  
**Training status:** NOT STARTED

> This document specifies candidate recognition properties for SignVox. It is not ASL expert sign-off. Final linguistic decisions, variants, and collection labels must be reviewed by a qualified ASL expert/native Deaf signer before dataset collection is frozen.

---

# 21. GO

## Identification

- **Sign ID:** ASL_GO
- **ASL gloss:** GO / GO-TO
- **English meaning:** go; go to
- **Category:** Actions / movement
- **Difficulty:** Medium
- **Priority:** High

## Manual Parameters

- **Handedness:** Typically two-handed in the commonly taught form; variant forms exist.
- **Dominant/non-dominant relationship:** The hands participate in a coordinated movement; exact articulation should be validated against the selected reference form.
- **Handshape:** Common instructional form uses bent/index-like configurations.
- **Palm orientation:** Directional; preserve orientation throughout the movement.
- **Signing location:** In front of the torso.
- **Movement:** A single quick movement away from the signer.
- **Movement direction:** Away from the signer / toward the destination.
- **Movement type:** Straight or slightly arcing directional movement depending on articulation.
- **Contact:** No required contact.
- **Symmetry:** Two-hand relationship must be preserved; do not reduce to a static hand pose.
- **Hand relationship:** Coordinated hands representing movement toward a destination.

Lifeprint describes GO as a single quick movement and notes that repeating the sign can produce an “attend” interpretation in contexts such as attending a school. citeturn0search0turn0search4

## Spatial / Linguistic Parameters

- **Spatial indexing:** Yes, potentially.
- **Directionality:** Important.
- **Participant encoding:** The movement can point toward a destination or spatial locus.
- **Temporal characteristics:** Short, quick movement with a clear start and endpoint.
- **Context dependence:** High. GO can participate in constructions equivalent to “go to,” and ASL does not require a separate English-style “to” in ordinary uses. citeturn0search4turn3search4

## Non-Manual Parameters

- Facial expression: Context dependent.
- Eye gaze: May track destination/referent.
- Eyebrows: Sentence dependent.
- Head movement: Sentence dependent.
- Mouth movement: Context dependent.
- Body movement: May reinforce direction/destination.

## Recognition Parameters

- **Type:** Dynamic
- **Motion complexity:** Low–medium
- **Visual complexity:** Medium
- **Common confusions:** COME; movement-based classifier constructions; TAKE-OFF/leave variants.
- **Expected landmark characteristics:** Detectable trajectory of the hands; direction relative to torso; start/end spatial relationship.
- **Recognition difficulty:** Medium
- **Occlusion:** Two-hand interaction can become ambiguous if one hand is lost.
- **Camera visibility:** Both hands and upper torso should remain visible.

## Dataset Instructions

Record both natural and deliberately clear performances. Preserve the full preparation-to-completion sequence. Include destination-oriented variations only after expert validation confirms which forms belong under the ASL_GO label.

**Important collection rule:** Do not collapse every English use of “go” into this class. “GO,” “GO-THERE,” “GO-TO,” “ATTEND,” and classifier/deictic constructions may require separate linguistic treatment.

**Source support:** Lifeprint GO and ASL grammar/directionality materials. citeturn0search0turn0search4

**Expert validation:** PENDING

---

# 22. COME

## Identification

- **Sign ID:** ASL_COME
- **ASL gloss:** COME / COME-HERE
- **English meaning:** come; come here
- **Category:** Actions / movement
- **Difficulty:** Medium
- **Priority:** High

## Manual Parameters

- **Handedness:** Common instructional form uses the dominant hand; variants exist.
- **Dominant/non-dominant relationship:** Primarily dominant-hand movement in the common form.
- **Handshape:** Common form uses index-finger-oriented handshape.
- **Palm orientation:** Preserve the orientation used by the validated reference.
- **Signing location:** In front of the signer.
- **Movement:** Quick movement toward the signer.
- **Movement direction:** Toward the signer / toward the current deictic locus.
- **Movement type:** Directional sweeping/curved movement.
- **Contact:** None required.
- **Symmetry:** Not inherently symmetrical.
- **Hand relationship:** Primarily single-hand.

Lifeprint distinguishes COME and GO primarily by movement direction: COME moves toward the signer while GO moves away. It also notes that COME has variants, including a casual “come on over” form. citeturn0search11turn1search1

## Spatial / Linguistic Parameters

- **Spatial indexing:** Strongly relevant.
- **Directionality:** Essential.
- **Participant encoding:** Destination/locus is encoded by movement.
- **Temporal characteristics:** Single quick movement.
- **Context dependence:** High.

## Non-Manual Parameters

- Eye gaze: May follow the intended destination.
- Eyebrows: Sentence dependent.
- Facial expression: Can distinguish neutral instruction from invitation/urgency.
- Head/body movement: Context dependent.

## Recognition Parameters

- **Type:** Dynamic
- **Motion complexity:** Low
- **Visual complexity:** Low–medium
- **Common confusions:** GO; casual COME-ON gesture; directional pointing.
- **Expected landmark characteristics:** Hand trajectory toward body/locus.
- **Recognition difficulty:** Medium
- **Occlusion:** Moderate.
- **Camera visibility:** Full upper torso recommended.

## Dataset Instructions

Collect COME with natural variation in movement amplitude and speed. Include examples where the movement terminates near the signer and examples directed toward an established spatial locus only if the expert-approved label permits them.

**Critical confusion pair:**

```text
COME → movement toward signer
GO   → movement away/toward destination
```

The model should learn trajectory rather than only handshape.

**Source support:** Lifeprint COME/GO comparison and COME entry. citeturn0search11turn1search1

**Expert validation:** PENDING

---

# 23. GIVE

## Identification

- **Sign ID:** ASL_GIVE
- **ASL gloss:** GIVE / GIVE-TO
- **English meaning:** give
- **Category:** Transfer / directional action
- **Difficulty:** High
- **Priority:** Very High

## Manual Parameters

- **Handedness:** Dominant hand; two-handed variants exist.
- **Dominant/non-dominant relationship:** The dominant hand carries the directional movement; a two-handed form may be used.
- **Handshape:** Multiple documented forms/variants, including a hand-to form and an X-handshape version.
- **Palm orientation:** Depends on the selected GIVE form and direction.
- **Signing location:** In front of the torso.
- **Movement:** Directional movement toward the recipient.
- **Movement direction:** From subject/source locus toward recipient locus.
- **Movement type:** Smooth directional transfer.
- **Contact:** Generally no required body contact.
- **Symmetry:** May be asymmetric or two-handed depending on variant.
- **Hand relationship:** Recipient/source relationship is encoded spatially.

Lifeprint explicitly describes GIVE as a directional/agreement verb in which movement incorporates information about subject and object. It documents forms such as ME-GIVE-YOU, YOU-GIVE-ME, and HE-GIVE-ME. citeturn0search7

## Spatial / Linguistic Parameters

- **Spatial indexing:** Essential.
- **Directionality:** Essential.
- **Participant encoding:** Critical.
- **Temporal characteristics:** Short directional transfer.
- **Context dependence:** Very high.

The same underlying lexical concept can be articulated differently depending on source and recipient loci. This must be preserved in the dataset rather than normalized away.

## Non-Manual Parameters

- Eye gaze: May align with recipient/referent.
- Facial expression: Context dependent.
- Eyebrows: Sentence dependent.
- Head/body shift: May help establish participant loci.

## Recognition Parameters

- **Type:** Dynamic
- **Motion complexity:** Medium
- **Visual complexity:** Medium–high
- **Common confusions:** TAKE; directional GIVE variants; hand-to-hand transfer gestures.
- **Expected landmark characteristics:** Clear start/end positions and movement vector.
- **Recognition difficulty:** High
- **Occlusion:** Medium.
- **Camera visibility:** Both hands, face, and torso should remain visible.

## Dataset Instructions

GIVE must not be collected as a single fixed trajectory only.

Collect controlled directional variants after expert validation:

```text
ME → YOU
YOU → ME
HE/SHE → ME
ME → HE/SHE
```

Use stable spatial loci during each recording session and document those loci in metadata.

Do not train a model that learns only “GIVE moves forward.”

**Hard-negative requirement:** Include TAKE-related samples and other transfer actions in evaluation.

**Source support:** Lifeprint GIVE and directionality materials. citeturn0search7turn2search9

**Expert validation:** PENDING

---

# 24. TAKE

## Identification

- **Sign ID:** ASL_TAKE_CANDIDATE
- **ASL gloss:** TAKE-FROM / TAKE-UP / context-specific TAKE
- **English meaning:** take
- **Category:** Transfer / acquisition / action
- **Difficulty:** Very High
- **Priority:** High

## Critical Linguistic Warning

**TAKE is not one visually universal ASL sign.**

Lifeprint documents multiple TAKE forms. “TAKE-from” is used for taking something from someone/place, while “TAKE-up” is used for meanings such as taking a class, adopting, or evaporating. “Take something to” may instead be represented by BRING. citeturn3search0turn3search3

Therefore the English word **TAKE must not automatically become one training class**.

For the initial ASL-100 recognition system, the preferred candidate is:

```text
TAKE-FROM
```

with the generic English gloss “take” retained only as a human-readable meaning.

## Manual Parameters — TAKE-FROM Candidate

- **Handedness:** Variant dependent.
- **Dominant/non-dominant relationship:** Depends on the TAKE-FROM construction.
- **Handshape:** Variant dependent.
- **Palm orientation:** Variant dependent.
- **Signing location:** In front of the body / near source locus.
- **Movement:** Acquisition/removal movement toward the signer or designated endpoint.
- **Movement direction:** Often source → signer.
- **Movement type:** Pulling/acquisition trajectory.
- **Contact:** May be conceptually associated with an object/source but should not be assumed to require physical contact.
- **Symmetry:** Variant dependent.
- **Hand relationship:** Source and recipient/signing-space relationships matter.

Lifeprint describes TAKE-from as the form for taking something from a person/place and distinguishes it from TAKE-up. citeturn3search0

## Spatial / Linguistic Parameters

- **Spatial indexing:** Essential for source-oriented constructions.
- **Directionality:** Essential.
- **Participant encoding:** Source and recipient/actor can be encoded through spatial direction.
- **Temporal characteristics:** Short acquisition movement.
- **Context dependence:** Extremely high.

## Non-Manual Parameters

Context dependent. Eye gaze may track the source or object.

## Recognition Parameters

- **Type:** Dynamic
- **Motion complexity:** Medium
- **Visual complexity:** High because variants have different forms.
- **Common confusions:** GIVE; TAKE-UP; BRING; TAKE-AWAY.
- **Recognition difficulty:** Very High
- **Occlusion:** Medium–high.
- **Camera visibility:** Full hands and upper torso required.

## Dataset Instructions

**Do not collect “TAKE” as a single uncontrolled English category.**

Before collection:

1. Expert must select the intended ASL lexical form.
2. Dataset label must identify the specific ASL construction.
3. Other TAKE meanings must be separate labels or excluded.
4. The model should not be forced to learn English polysemy.

Recommended initial label:

```text
ASL_TAKE_FROM
```

rather than:

```text
ASL_TAKE
```

**Source support:** Lifeprint TAKE and TAKE-UP. citeturn3search0turn3search3

**Expert validation:** REQUIRED BEFORE DATA COLLECTION

---

# 25. WANT

## Identification

- **Sign ID:** ASL_WANT
- **ASL gloss:** WANT
- **English meaning:** want; desire
- **Category:** Needs / intention
- **Difficulty:** Medium
- **Priority:** High

## Manual Parameters

- **Handedness:** Two-handed in the common form.
- **Dominant/non-dominant relationship:** Both hands participate.
- **Handshape:** Commonly begins with open/flat 5-handshapes and transitions toward claw-like shapes.
- **Palm orientation:** Palms generally upward at the start.
- **Signing location:** In front of the torso.
- **Movement:** Hands move back toward the signer while changing handshape.
- **Movement direction:** Toward signer.
- **Movement type:** Pulling motion with handshape change.
- **Contact:** No required contact.
- **Symmetry:** Approximately symmetrical.
- **Hand relationship:** Two hands move together.

Lifeprint describes WANT as starting with 5-handshapes, palms up, then bringing the hands back while changing them into claw shapes. citeturn2search1

## Spatial / Linguistic Parameters

- **Spatial indexing:** Person/reference may be established separately.
- **Directionality:** WANT itself should not be treated as a directional agreement verb; the signer can index who wants what.
- **Participant encoding:** Often separate from the WANT movement.
- **Temporal characteristics:** Short movement.
- **Context dependence:** Medium.

Lifeprint specifically distinguishes WANT from directional verbs: the signer can establish the subject separately and then sign WANT. citeturn2search9

## Non-Manual Parameters

- Facial expression: May communicate intensity/desire.
- Eye gaze: Context dependent.
- Eyebrows: Sentence dependent.
- Head movement: Especially relevant in negative constructions.

## Recognition Parameters

- **Type:** Dynamic
- **Motion complexity:** Medium
- **Visual complexity:** Medium
- **Common confusions:** NEED; HAVE; GIVE/receive gestures.
- **Expected landmark characteristics:** Two-hand inward trajectory + handshape transition.
- **Recognition difficulty:** Medium
- **Occlusion:** Low–medium.
- **Camera visibility:** Both hands required.

## Dataset Instructions

Include natural variation in movement amplitude and speed.

Do not merge WANT and DON'T-WANT into separate unrelated lexical classes if the implementation later models ASL morphological negation compositionally. The negative form should be documented separately for evaluation.

**Source support:** Lifeprint WANT and directionality notes. citeturn2search1turn2search9

**Expert validation:** PENDING

---

# 26. NEED

## Identification

- **Sign ID:** ASL_NEED
- **ASL gloss:** NEED / NEED-TO / MUST / SHOULD (context dependent)
- **English meaning:** need
- **Category:** Needs / obligation
- **Difficulty:** Medium
- **Priority:** High

## Manual Parameters

- **Handedness:** Dominant hand in the standard form.
- **Dominant/non-dominant relationship:** Primarily dominant-hand.
- **Handshape:** X handshape.
- **Palm orientation:** Starts palm-forward and ends palm-down according to Lifeprint's description.
- **Signing location:** In front of the signer, slightly to the dominant side.
- **Movement:** Wrist-driven downward bend.
- **Movement direction:** Downward.
- **Movement type:** Short, sharp wrist movement.
- **Contact:** None required.
- **Symmetry:** Asymmetric / one-handed.
- **Hand relationship:** Dominant hand only in the standard form.

Lifeprint specifies NEED as an X-handshape sign with a downward wrist movement and notes that the standard form is one-handed. It also describes differences in force/repetition associated with related meanings such as MUST versus SHOULD/OUGHT-TO. citeturn0search10turn0search2

## Spatial / Linguistic Parameters

- **Spatial indexing:** Usually not essential to the lexical sign itself.
- **Directionality:** Not primarily directional.
- **Participant encoding:** Often provided by context/indexing.
- **Temporal characteristics:** Single or repeated movement depending on meaning.
- **Context dependence:** High.

## Non-Manual Parameters

- Facial expression: Important for degree/intensity.
- Head movement: May accompany obligation/force.
- Eye gaze: Context dependent.
- Body posture: Can reinforce urgency.

## Recognition Parameters

- **Type:** Dynamic
- **Motion complexity:** Low
- **Visual complexity:** Low–medium
- **Common confusions:** WANT; HAVE-TO; SHOULD; other X-hand movements.
- **Expected landmark characteristics:** Dominant X-hand + downward wrist trajectory.
- **Recognition difficulty:** Medium
- **Occlusion:** Low.
- **Camera visibility:** Dominant hand and wrist must be visible.

## Dataset Instructions

Record standard NEED separately from strongly inflected forms where possible.

Metadata should capture:

```text
movement_count
movement_strength
facial_intensity
context
```

Do not assume that all English “need,” “must,” and “should” instances are the same ASL form.

**Source support:** Lifeprint NEED and signing notes. citeturn0search10turn0search2

**Expert validation:** PENDING

---

# 27. HAVE

## Identification

- **Sign ID:** ASL_HAVE
- **ASL gloss:** HAVE
- **English meaning:** have; possess; existence
- **Category:** Possession / existence
- **Difficulty:** Medium
- **Priority:** High

## Manual Parameters

- **Handedness:** Two-handed.
- **Dominant/non-dominant relationship:** Symmetric.
- **Handshape:** Bent-B handshapes.
- **Palm orientation:** Toward/against the upper chest.
- **Signing location:** Upper chest.
- **Movement:** Hands move/touch toward the chest.
- **Movement direction:** Inward toward chest.
- **Movement type:** Short contact/touching movement.
- **Contact:** Chest contact is characteristic.
- **Symmetry:** Symmetrical.
- **Hand relationship:** Both hands mirror one another.

Lifeprint's signing notes specify bent-B handshapes touching the chest for HAVE. citeturn3search1

## Spatial / Linguistic Parameters

- **Spatial indexing:** Generally low for the lexical form.
- **Directionality:** Not a directional agreement verb in the same sense as GIVE.
- **Participant encoding:** Possessor may be indexed separately.
- **Temporal characteristics:** Short.
- **Context dependence:** Medium–high.

HAVE is associated with possession/existence and should not automatically be interpreted as an English “request” or “want.” citeturn1search14

## Non-Manual Parameters

- Facial expression: Context dependent.
- Eye gaze: Context dependent.
- Eyebrows: Question structure may affect eyebrows.
- Head movement: Sentence dependent.

## Recognition Parameters

- **Type:** Dynamic/contact
- **Motion complexity:** Low
- **Visual complexity:** Medium
- **Common confusions:** WANT; NEED; chest-pointing/pronominal forms.
- **Expected landmark characteristics:** Two bent-B hands moving/touching upper chest.
- **Recognition difficulty:** Medium
- **Occlusion:** Low.
- **Camera visibility:** Upper torso and both hands required.

## Dataset Instructions

Ensure recordings preserve the chest location. Avoid tight cropping around only the hands.

Include question contexts such as possession only as an evaluation/linguistic context, not as a separate visual class.

**Source support:** Lifeprint signing notes and grammar discussion. citeturn3search1turn1search14

**Expert validation:** PENDING

---

# 28. KNOW

## Identification

- **Sign ID:** ASL_KNOW
- **ASL gloss:** KNOW
- **English meaning:** know; be aware/familiar
- **Category:** Cognition / knowledge
- **Difficulty:** Medium
- **Priority:** High

## Manual Parameters

- **Handedness:** Dominant hand.
- **Dominant/non-dominant relationship:** Primarily one-handed.
- **Handshape:** Flat/bent-B-type handshape depending on variant.
- **Palm orientation:** Toward signer.
- **Signing location:** Side of forehead/head in the common citation form; cheek variant also occurs.
- **Movement:** Contact/touch; related variants may include outward twist for DON'T-KNOW.
- **Movement direction:** Minimal for affirmative KNOW.
- **Movement type:** Short contact.
- **Contact:** Finger tips contact the forehead/face.
- **Symmetry:** Asymmetric.
- **Hand relationship:** Dominant hand only.

Lifeprint describes KNOW as touching the side of the forehead with the fingertips of a flat hand and notes a common casual cheek version. citeturn1search2

## Spatial / Linguistic Parameters

- **Spatial indexing:** Usually not required for the lexical sign.
- **Directionality:** Not a directional agreement verb.
- **Participant encoding:** Context/indexing.
- **Temporal characteristics:** Short contact.
- **Context dependence:** Medium.

Lifeprint also notes that KNOW can participate in negation through orientation changes, demonstrating why hand orientation should be retained in the representation. citeturn1search2

## Non-Manual Parameters

- Facial expression: Context dependent.
- Eye gaze: Context dependent.
- Eyebrows: Question structure.
- Head movement: May accompany negative/uncertain meanings.

## Recognition Parameters

- **Type:** Static/contact with possible small movement
- **Motion complexity:** Low
- **Visual complexity:** Medium
- **Common confusions:** THINK; DON'T-KNOW; face-pointing/indexing.
- **Expected landmark characteristics:** Hand-to-face location and handshape.
- **Recognition difficulty:** Medium
- **Occlusion:** Low–medium.
- **Camera visibility:** Face and hand must be clear.

## Dataset Instructions

Collect the validated affirmative KNOW form.

If the expert approves both forehead and cheek forms as variants, metadata must distinguish:

```text
variant_id = KNOW_FOREHEAD
variant_id = KNOW_CHEEK
```

Do not treat a casual/regional variant as an error automatically.

**Source support:** Lifeprint KNOW and signing notes. citeturn1search2turn2search3

**Expert validation:** PENDING

---

# 29. LIKE

## Identification

- **Sign ID:** ASL_LIKE
- **ASL gloss:** LIKE / LIKE-[fondness]
- **English meaning:** like; enjoy; have an affinity for
- **Category:** Emotion / preference
- **Difficulty:** Medium
- **Priority:** High

## Manual Parameters

- **Handedness:** Dominant hand in the common form.
- **Dominant/non-dominant relationship:** Primarily one-handed.
- **Handshape:** Starts as a 5-handshape and changes into an 8-handshape.
- **Palm orientation:** Toward signer/chest at start.
- **Signing location:** Near the chest.
- **Movement:** Short forward movement while the thumb/index relationship changes.
- **Movement direction:** Slightly forward.
- **Movement type:** Forward movement + handshape transition.
- **Contact:** No required chest contact.
- **Symmetry:** Asymmetric.
- **Hand relationship:** Dominant hand only in common form.

Lifeprint describes LIKE as a sign for enjoying/having affinity for something, beginning near the chest and moving forward while changing into an 8-handshape. citeturn2search0turn2search3

## Spatial / Linguistic Parameters

- **Spatial indexing:** Object/person being liked can be established separately.
- **Directionality:** LIKE itself should not be treated as a directional agreement verb.
- **Participant encoding:** Usually contextual/indexical.
- **Temporal characteristics:** Short movement.
- **Context dependence:** Medium.

Important semantic distinction:

```text
LIKE = enjoy / have affinity for
SAME = similar / like
LOOK-LIKE = resemble
```

The English word “like” must not be used as the sole label definition. citeturn2search0turn2search2

## Non-Manual Parameters

- Facial expression: Important for intensity and affect.
- Eye gaze: Context dependent.
- Eyebrows: Question structure.
- Head movement: May contribute to positive/negative affect.

## Recognition Parameters

- **Type:** Dynamic
- **Motion complexity:** Medium
- **Visual complexity:** Medium
- **Common confusions:** WANT; SAME; LOOK-LIKE; DON'T-LIKE.
- **Expected landmark characteristics:** Start near chest + forward movement + 5→8 handshape transition.
- **Recognition difficulty:** Medium
- **Occlusion:** Low.
- **Camera visibility:** Hand and upper torso visible.

## Dataset Instructions

Include clear examples of LIKE and hard negatives:

```text
LIKE
WANT
SAME
LOOK-LIKE
DON'T-LIKE
```

Do not label LOOK-LIKE or SAME as LIKE merely because the English translation contains “like.”

**Source support:** Lifeprint LIKE and LOOK-LIKE. citeturn2search0turn2search2

**Expert validation:** PENDING

---

# 30. SEE

## Identification

- **Sign ID:** ASL_SEE
- **ASL gloss:** SEE
- **English meaning:** see; perceive visually
- **Category:** Perception
- **Difficulty:** Medium–High
- **Priority:** High

## Critical Linguistic Warning

English “see” maps to multiple ASL forms depending on meaning.

Lifeprint distinguishes:

```text
SEE
LOOK-at
WATCH
```

The citation form SEE is used for meanings such as “Can you see me?” or “I saw you.” LOOK-at is used for actively looking toward something, while WATCH is used for observing an event such as a movie, sports event, or performance. citeturn0search6

The ASL-100 label should therefore mean **SEE**, not every English use of “see.”

## Manual Parameters

- **Handedness:** Dominant hand.
- **Dominant/non-dominant relationship:** Primarily one-handed.
- **Handshape:** V-handshape in the documented SEE form.
- **Palm orientation:** Inward toward signer.
- **Signing location:** In front of/near the face.
- **Movement:** Context-dependent short movement; preserve the validated citation form.
- **Movement direction:** Depends on target/context.
- **Movement type:** Directional visual-attention movement.
- **Contact:** No required contact.
- **Symmetry:** Asymmetric.
- **Hand relationship:** Dominant hand.

Lifeprint identifies SEE with a V-handshape, palm inward, and distinguishes it from LOOK-at and WATCH. citeturn0search6

## Spatial / Linguistic Parameters

- **Spatial indexing:** Important when the visual target is established.
- **Directionality:** Important in target-oriented forms.
- **Participant encoding:** Can involve an indexed visual target.
- **Temporal characteristics:** Short, context-dependent.
- **Context dependence:** Very high.

## Non-Manual Parameters

- Eye gaze: **Critical** for many visual-perception constructions.
- Facial expression: Context dependent.
- Eyebrows: Question/statement dependent.
- Head orientation: May align with visual target.
- Body orientation: May support target direction.

## Recognition Parameters

- **Type:** Dynamic/static hybrid depending on construction.
- **Motion complexity:** Medium.
- **Visual complexity:** Medium–high.
- **Common confusions:** LOOK-at; WATCH; SEE-YOU; face-directed pointing.
- **Expected landmark characteristics:** V-handshape + hand position + movement + eye-gaze direction.
- **Recognition difficulty:** High.
- **Occlusion:** Low–medium.
- **Camera visibility:** Face and hand must both be visible.

## Dataset Instructions

The dataset must not mix SEE, LOOK-at, and WATCH into one class.

Recommended metadata:

```text
semantic_subtype:
  SEE
  LOOK_AT
  WATCH
```

For the ASL-100 initial class, only:

```text
ASL_SEE
```

should be included unless expert validation explicitly expands the class.

Because eye gaze can carry important information, face landmarks and gaze-related features should be preserved where technically reliable.

**Source support:** Lifeprint SEE and its SEE/LOOK/WATCH distinction. citeturn0search6

**Expert validation:** REQUIRED BEFORE DATA COLLECTION

---

# Batch 03 Cross-Sign Recognition Matrix

| Sign | Main recognition signal | Major confusion | Spatial/directional importance | Non-manual importance |
|---|---|---|---|---|
| GO | directional hand trajectory | COME | Very high | Medium |
| COME | trajectory toward signer | GO | Very high | Medium |
| GIVE | source→recipient trajectory | TAKE | Critical | Medium–high |
| TAKE-FROM | source→signer acquisition trajectory | GIVE | Critical | Medium |
| WANT | two-hand inward pull + handshape change | NEED | Medium | Medium |
| NEED | X-hand downward wrist motion | WANT | Low–medium | High |
| HAVE | two bent-B hands at chest | WANT | Low | Medium |
| KNOW | hand-to-face location | THINK / DON'T-KNOW | Medium | Medium |
| LIKE | 5→8 handshape transition | WANT / SAME | Medium | Medium |
| SEE | V-hand + visual target/gaze | LOOK-at / WATCH | High | High |

---

# Batch 03 High-Risk Dataset Cases

The following should receive additional expert attention before collection:

### 1. GO ↔ COME

The distinction is fundamentally directional.

```text
GO   → away/toward destination
COME → toward signer/current locus
```

Do not train only on static handshape.

### 2. GIVE ↔ TAKE-FROM

These are especially important because transfer direction carries linguistic information.

```text
GIVE
source → recipient

TAKE-FROM
source → receiver/actor
```

The exact ASL construction must be validated before labeling.

### 3. TAKE Polysemy

Do not make:

```text
English TAKE = one ASL class
```

Instead specify the intended ASL construction.

### 4. NEED ↔ WANT

Both express desire/requirement but differ in manual articulation and linguistic function.

### 5. LIKE ↔ WANT

Both can involve forward/inward movement around the torso, so handshape and trajectory must be preserved.

### 6. KNOW ↔ THINK

Handshape and location are important. Lifeprint specifically distinguishes KNOW's bent/flat hand from THINK's index-finger form. citeturn0search2

### 7. SEE ↔ LOOK-at ↔ WATCH

These should not be collapsed simply because English may translate them using “see/look/watch.” citeturn0search6

---

# Batch 03 Dataset Design Consequences

The following features should be preserved for these signs:

```text
handshape
palm_orientation
finger_orientation
hand_position
movement_vector
movement_speed
movement_amplitude
start_location
end_location
left/right hand identity
face landmarks
eye-gaze-related features where reliable
head orientation
upper-body pose
temporal sequence
visibility masks
```

For directional signs, do not normalize away:

```text
start_location
end_location
trajectory
spatial_locus
```

because these may carry linguistic meaning.

---

# Batch 03 Validation Status

| Sign | Specification | Expert validation | Dataset approval |
|---|---|---|---|
| GO | Complete | Pending | Pending |
| COME | Complete | Pending | Pending |
| GIVE | Complete | Pending | Pending |
| TAKE-FROM candidate | Complete | **Required** | Pending |
| WANT | Complete | Pending | Pending |
| NEED | Complete | Pending | Pending |
| HAVE | Complete | Pending | Pending |
| KNOW | Complete | Pending | Pending |
| LIKE | Complete | Pending | Pending |
| SEE | Complete | **Required** | Pending |

**Batch 03 completion:** 10/10 specifications complete.

**Overall per-sign specification progress:** 30/100.

**Expert-confirmed:** 0/30.

**Dataset-approved:** 0/30.

---

# Research References

Primary reference used for individual sign specifications:

- Lifeprint / American Sign Language University — individual ASL sign pages and ASL grammar/signing notes.
- Lifeprint materials on directional/agreement verbs and spatial indexing.
- MediaPipe documentation remains the primary reference for the technical landmark-extraction layer; it does not establish linguistic ground truth.

All individual sign descriptions in this document remain subject to ASL expert validation.
