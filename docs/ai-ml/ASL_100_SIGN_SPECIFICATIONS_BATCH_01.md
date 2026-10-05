# SignVox ASL-100 Sign Specifications — Batch 01

**Status:** Research draft — NOT YET VALIDATED FOR TRAINING  
**Language:** American Sign Language (ASL)  
**Scope:** Core communication and conversation-control concepts *(corresponds to [ASL-100 Master Vocabulary](./ASL_100_VOCABULARY_SPEC.md))*  
**Expert validation required:** Yes

## Annotation principle

For SignVox, a sign is represented as more than a hand pose. The working representation should preserve:

- handshape
- palm/finger orientation
- location
- movement
- two-hand relationship
- directionality/spatial indexing
- timing
- facial expression
- eyebrow position
- eye gaze
- head movement
- body posture/movement
- context/grammatical role

This follows standard ASL descriptions in which sign formation is distinguished by handshape, orientation, location, movement, and non-manual information.

---

## SV-ASL-001 — HELLO

**Gloss:** HELLO / HI  
**Meaning:** Greeting  
**Category:** Communication  
**Difficulty:** 1 — Foundation  
**Priority:** High  
**Manuality:** One-handed  
**Dominant hand:** Dominant hand  
**Non-dominant hand:** Not required

**Handshape:** Open/relaxed hand; natural greeting-wave configuration.  
**Palm orientation:** Generally outward toward the addressee.  
**Finger orientation:** Generally upward/outward.  
**Location:** Upper signing space, near side of head/face.  
**Movement:** Natural wave; typically side-to-side.  
**Movement direction:** Lateral/repeated.  
**Contact:** None.  
**Symmetry:** N/A.

**Non-manual information:** Friendly/neutral greeting expression is natural but not a fixed lexical requirement in the same way as grammatical question markers.  
**Head/body:** Natural engagement toward addressee.

**Static or dynamic:** Dynamic.  
**Temporal complexity:** Low.  
**Visual complexity:** Low.  
**Known variation:** There is no single rigid wave form; natural variation is expected.  
**Potential confusions:** GOODBYE, HEY, generic waving/attention-getting gestures.

**Recognition implications:**  
Do not overfit to one exact wave amplitude or wrist angle. The classifier needs context, position near the upper body, motion trajectory, and likely a short temporal window.

**Dataset instructions:**  
Record natural greeting waves from many signers with different amplitudes, speeds, hand dominance, and distances. Include negative examples of goodbye-type wrist/finger bending and non-linguistic waving.

**Expert validation:** Required.

---

## SV-ASL-002 — GOOD

**Gloss:** GOOD  
**Meaning:** Good / positive evaluation  
**Category:** Communication / Description  
**Difficulty:** 1 — Foundation  
**Priority:** High  
**Manuality:** One- or two-handed variants occur.

**Handshape:** Flat/open dominant hand.  
**Location:** Begins near lips/lower face.  
**Movement:** Dominant hand moves away/downward; a two-handed form can end on the upturned non-dominant palm.  
**Contact:** Possible contact with support hand in the two-handed form.

**Non-manual information:** Neutral-to-positive expression can accompany the sign; expression may strengthen pragmatic meaning but should not be the sole recognition cue.

**Static or dynamic:** Dynamic.  
**Potential confusions:** THANK-YOU is especially important.

**Recognition implications:**  
The key discrimination from THANK-YOU is not handshape alone. Movement direction and endpoint are essential. A frame classifier is insufficient; temporal trajectory should be used.

**Dataset instructions:**  
Collect both one- and two-handed accepted variants. Record GOOD and THANK-YOU in the same sessions so the model learns the distinction rather than signer/background differences.

**Expert validation:** Required.

---

## SV-ASL-003 — BAD

**Gloss:** BAD  
**Meaning:** Bad / negative evaluation  
**Category:** Communication / Description  
**Difficulty:** 1 — Foundation  
**Priority:** High

**Handshape:** Flat/open dominant hand.  
**Location:** Starts near lower face/mouth area.  
**Movement:** Movement away from the face with an orientation change; exact production and accepted variants must be validated.  
**Manuality:** Primarily one-handed in the common form.

**Non-manual information:** Negative facial affect can naturally accompany BAD and can strengthen meaning.  
**Head/body:** Context-dependent.

**Static or dynamic:** Dynamic.  
**Potential confusions:** GOOD at the initial pose; other face-origin flat-hand signs.

**Recognition implications:**  
The model must pay attention to trajectory and palm/orientation change rather than the initial configuration alone. GOOD/BAD should be deliberately treated as a contrast pair during evaluation.

**Dataset instructions:**  
Record neutral, mildly negative, and emphatic natural productions without teaching the model that a frown is mandatory for lexical recognition.

**Expert validation:** Required.

---

## SV-ASL-004 — PLEASE

**Gloss:** PLEASE  
**Meaning:** Please / politeness concept  
**Category:** Communication  
**Difficulty:** 1 — Foundation  
**Priority:** High

**Handshape:** Flat dominant hand.  
**Palm orientation:** Toward/against torso.  
**Location:** Center of chest.  
**Movement:** Circular movement on/near the chest, commonly repeated.  
**Contact:** Typically hand contacts or closely tracks the chest.

**Non-manual information:** Pragmatic politeness can be expressed by facial/body behavior. In actual ASL requests, a hopeful/pleading expression or other constructions may sometimes carry the politeness function instead of lexical PLEASE.

**Static or dynamic:** Dynamic.  
**Potential confusions:** SORRY because both occupy the chest area with circular motion, but they use different handshapes.

**Recognition implications:**  
Excellent test of combined **location + handshape + circular movement**. PLEASE vs SORRY should be included as a deliberate confusion pair.

**Dataset instructions:**  
Record several circle sizes and speeds. Include SORRY negatives captured under identical conditions.

**Expert validation:** Required, particularly for pragmatic usage.

---

## SV-ASL-005 — THANK-YOU

**Gloss:** THANK-YOU / THANKS  
**Meaning:** Expression of gratitude  
**Category:** Communication  
**Difficulty:** 1 — Foundation  
**Priority:** High

**Handshape:** Flat dominant hand.  
**Location:** Fingers begin near the lips.  
**Movement:** Hand moves forward and somewhat downward toward the person being thanked.  
**Directionality:** Meaningfully directed toward addressee.  
**Contact:** Lips need not be touched.

**Non-manual information:** A smile or grateful expression commonly accompanies sincere use, but lexical classification should not depend solely on smiling.

**Static or dynamic:** Dynamic.  
**Potential confusions:** GOOD — critical confusion pair.

**Recognition implications:**  
Spatial direction toward the addressee is important. SignVox should preserve wrist/hand trajectory relative to face and camera, not just normalized finger configuration.

**Dataset instructions:**  
Record different addressee positions and slight camera angles. Record GOOD and THANK-YOU together. Include one- and two-handed emphatic variants only if expert-approved for the target vocabulary.

**Expert validation:** Required.

---

## SV-ASL-006 — SORRY

**Gloss:** SORRY  
**Meaning:** Sorry / apologize / regret  
**Category:** Communication  
**Difficulty:** 1 — Foundation  
**Priority:** High

**Handshape:** Commonly an A-handshape; an S-like variant is also encountered.  
**Location:** Chest.  
**Movement:** Circular motion, commonly a couple of rotations.  
**Contact:** Usually on or very near the chest.

**Non-manual information:** A congruent “sorry” facial expression is explicitly relevant to natural production.  
**Facial expression:** Regretful/apologetic affect.  
**Head/body:** Can contribute to pragmatic force.

**Static or dynamic:** Dynamic.  
**Potential confusions:** PLEASE due to shared chest/circular location and motion.

**Recognition implications:**  
Handshape is crucial for PLEASE/SORRY separation. Face features are valuable auxiliary evidence. The system should support accepted handshape variation without collapsing PLEASE and SORRY.

**Dataset instructions:**  
Collect A-hand productions first and separately tag any expert-approved variants. Record facial expression rather than cropping the face out.

**Expert validation:** Required.

---

## SV-ASL-007 — HELP

**Gloss:** HELP / HELP-you / you-HELP-me  
**Meaning:** Help / assist  
**Category:** Communication / Action / Safety  
**Difficulty:** 2 — Intermediate  
**Priority:** Very High

**Manuality:** Two-handed.  
**Dominant hand:** Loose-thumb A-hand or closely related accepted configuration.  
**Non-dominant hand:** Open supporting hand beneath the dominant hand.  
**Location:** Neutral space in front of torso.  
**Movement:** Supporting hand and dominant hand move together upward.  
**Hand relationship:** Dominant fist rests on/supports against open non-dominant hand.

**Directionality:** Critical. The sign can move through space to encode who helps whom.  
**Spatial indexing:** Yes.  
**Participant encoding:** Yes.

**Non-manual information:** Raised eyebrows may convert a directional HELP production into a yes/no request/question depending on context.

**Static or dynamic:** Dynamic.  
**Temporal complexity:** Moderate.  
**Visual complexity:** Moderate.  
**Potential confusions:** Need expert review for visually neighboring two-hand configurations.

**Recognition implications:**  
This should NOT eventually be represented only as class `HELP`. A richer representation should preserve movement start/end positions so SignVox can later distinguish `I-HELP-YOU`, `YOU-HELP-ME`, etc.

**Dataset instructions:**  
For the first isolated model, record neutral HELP. Separately collect directional productions and label **source locus** and **target locus**. Preserve torso coordinates and both hands.

**Expert validation:** Required.

---

## SV-ASL-008 — STOP

**Gloss:** STOP  
**Meaning:** Stop / halt  
**Category:** Safety / Conversation control  
**Difficulty:** 1 — Foundation  
**Priority:** Very High

**Manuality:** Two-handed.  
**Non-dominant hand:** Open, palm upward.  
**Dominant hand:** Open hand.  
**Location:** Neutral space in front of torso.  
**Movement:** Dominant hand comes sharply downward onto the non-dominant palm at roughly a right angle.  
**Contact:** Yes.  
**Timing:** Sharp/decisive impact-like endpoint.

**Non-manual information:** Facial/body urgency can vary with pragmatic force, but the base lexical sign can be produced neutrally.

**Static or dynamic:** Dynamic.  
**Potential confusions:** Other palm-contact signs; STOP-IT/FINISH-type constructions may differ.

**Recognition implications:**  
Good early temporal-classification sign because of its distinctive two-hand geometry and sharp endpoint. Contact itself cannot be measured directly from 2D video, so infer it from hand proximity, trajectory, velocity reduction, and landmark intersection.

**Dataset instructions:**  
Capture normal, gentle, and emphatic productions. Record from angles where palm overlap/occlusion occurs so robustness can be measured.

**Expert validation:** Required.

---

## SV-ASL-009 — WAIT

**Gloss:** WAIT  
**Meaning:** Wait / pause  
**Category:** Conversation control  
**Difficulty:** 1 — Foundation  
**Priority:** High

**Manuality:** Commonly two-handed.  
**Location:** Hands held in front/off to the side of signing space.  
**Movement:** Fingers wiggle/repeat while the hands remain broadly positioned.  
**Fine motion:** Important.

**Non-manual information:** Usually contextual rather than lexically fixed; extended waiting can be expressed with modified duration/manner and corresponding body behavior.

**Static or dynamic:** Dynamic.  
**Temporal complexity:** Moderate because finger articulation must be tracked.  
**Potential confusions:** STAY, PAUSE, EXPECT and non-linguistic finger wiggling require later expert/contrast review.

**Recognition implications:**  
This is a useful stress test for MediaPipe hand landmarks because the gross hand position changes little while **finger motion carries much of the signal**.

**Dataset instructions:**  
Capture multiple repetition counts and natural speeds. Ensure sufficient image resolution for finger landmarks. Include stationary open-hand negatives.

**Expert validation:** Required.

---

## SV-ASL-010 — UNDERSTAND

**Gloss:** UNDERSTAND  
**Meaning:** Understand / comprehend  
**Category:** Conversation control  
**Difficulty:** 2 — Intermediate  
**Priority:** Very High

**Manuality:** One-handed.  
**Location:** Near forehead.  
**Initial configuration:** Index finger bent with fingertip near/touching thumb pad.  
**Movement:** Index finger flicks/extends upward.  
**Endpoint:** Index points upward.

**Non-manual information:**  
The negative concept **DON'T-UNDERSTAND** can be expressed using UNDERSTAND with a negative headshake rather than requiring a separate lexical `DON'T` sign.

**Head movement:** Critical for the negative construction.  
**Facial expression:** Negative/non-comprehension expression may co-occur.

**Static or dynamic:** Dynamic.  
**Temporal complexity:** Moderate.  
**Potential confusions:** Other forehead/index-flick signs require expert review.

**Recognition implications:**  
This is a strong argument for tracking the head and face alongside the hands. A future representation should allow:

`UNDERSTAND + NMM_NEGATION`

rather than forcing `DON'T-UNDERSTAND` to be a totally independent 101st class.

**Dataset instructions:**  
Collect UNDERSTAND and DON'T-UNDERSTAND in paired recordings from the same signers. Label manual sign and non-manual negation separately.

**Expert validation:** Required.

---

# Batch 01 model-design conclusions

## 1. Non-manual information must be first-class

Do not attach face/head information as an optional afterthought. At minimum preserve:

- eyebrow movement
- head nod/shake
- head tilt
- mouth/affective region
- coarse facial expression features
- torso lean/orientation

## 2. Use compositional labels where possible

Instead of creating separate opaque classes for every grammatical variant, eventually prefer a structure similar to:

```json
{
  "lexeme": "UNDERSTAND",
  "manual_confidence": 0.94,
  "non_manual": {
    "negation_headshake": true
  }
}
```

and for directional signs:

```json
{
  "lexeme": "HELP",
  "source_locus": "self",
  "target_locus": "addressee"
}
```

This is a future representation goal, not something to implement before the recognition baseline works.

## 3. Deliberate confusion pairs for evaluation

Batch 01 already gives us:

- GOOD ↔ THANK-YOU
- PLEASE ↔ SORRY
- HELLO ↔ non-linguistic wave / GOODBYE
- UNDERSTAND ↔ DON'T-UNDERSTAND
- HELP neutral ↔ directional HELP variants

A useful model must be tested on these intentionally difficult pairs rather than only reporting overall accuracy.

## 4. Keep raw temporal information

Do not reduce each sample to one averaged hand pose. Movement trajectory and timing distinguish several signs in this batch.

## 5. Preserve face/body landmarks

The current SignVox architecture should retain selected face/head and pose landmarks in the temporal feature sequence.

---

# Source notes

Research for this batch used:
- Gallaudet University / Gallaudet University Press descriptions of ASL sign parameters and proficiency criteria.
- ASL University / Lifeprint sign reference pages for HELLO, GOOD, PLEASE, THANK-YOU, SORRY, HELP, STOP, WAIT, UNDERSTAND, and non-manual markers.

These sources are research references, not a replacement for final review by a qualified Deaf/native ASL signer or ASL expert.

## Validation status

**Batch 01 research complete.**  
**Expert validation: Pending.**  
**Safe to use for architecture/dataset planning: Yes.**  
**Safe to treat as final training ground truth: No.**
