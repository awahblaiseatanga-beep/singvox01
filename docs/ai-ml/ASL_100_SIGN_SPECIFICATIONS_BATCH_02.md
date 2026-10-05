# SignVox ASL-100 Sign Specifications — Batch 02: People & Identity

**Status:** Research draft — NOT YET VALIDATED FOR TRAINING  
**Language:** American Sign Language (ASL)  
**Scope:** People, identity, family and interpersonal reference *(corresponds to [ASL-100 Master Vocabulary](./ASL_100_VOCABULARY_SPEC.md))*  
**Expert validation required:** Yes

## Research basis

Lifeprint's ASL curriculum explicitly treats I/ME, YOU and other pronouns through **indexing**, and distinguishes singular/plural referents using signing-space movement. Its family curriculum includes MOTHER, FATHER, BROTHER, SISTER, CHILD, BABY and FAMILY. Gallaudet's ASL standards likewise describe pronouns and referents as spatially established and manipulated through indexing, eye gaze and other spatial mechanisms. citeturn2search0turn0search24

### Critical SignVox finding

**Pronouns should NOT be treated as ordinary fixed gesture classes.**

In ASL, pointing/indexing can establish a referent in signing space. The same physical index gesture can mean I, YOU, HE/SHE/IT, THIS, THAT, etc., depending on location and discourse context. Plural referents can involve spatial sweeps or established locations. citeturn2search0turn2search1

Therefore, SignVox's eventual representation needs both:

`LEXICAL SIGN`

and

`SPATIAL REFERENT / INDEX`

as separate concepts.

---

## SV-ASL-011 — I / ME

**Gloss:** I / ME / IX-1  
**Meaning:** First-person reference  
**Category:** Identity / Indexing  
**Difficulty:** 2 — Intermediate  
**Priority:** Very High

**Manuality:** One-handed index gesture.  
**Handshape:** Indexing/pointing configuration.  
**Location:** Toward the signer/self.  
**Movement:** Short pointing movement toward the signer's torso/chest area.  
**Directionality:** Toward the first-person locus.

**Non-manual information:** Usually supported by eye gaze and discourse context rather than a special facial expression.

**Static or dynamic:** Low-motion dynamic/static-pointing.  
**Temporal complexity:** Low.  
**Spatial complexity:** High.

**Critical linguistic note:**  
I/ME is an instance of ASL indexing. It should not be interpreted solely from finger configuration.

**Recognition implications:**  
The model needs a coordinate frame relative to the signer. A simple `INDEX_FINGER = ME` classifier would be incorrect.

The representation should eventually resemble:

```json
{
  "type": "INDEX",
  "referent": "SELF",
  "locus": "signer"
}
```

rather than a fixed visual class.

**Dataset instructions:**  
Record I/ME with different torso positions, camera distances and body orientations. Include YOU and HE/SHE/IT indexing as hard negatives.

**Expert validation:** Required.

---

## SV-ASL-012 — YOU

**Gloss:** YOU / IX-2  
**Meaning:** Second-person reference  
**Category:** Identity / Indexing  
**Difficulty:** 2 — Intermediate  
**Priority:** Very High

**Manuality:** One-handed index gesture.  
**Handshape:** Indexing/pointing configuration.  
**Location:** Neutral signing space directed toward addressee.  
**Movement:** Point toward the addressee's established locus.  
**Directionality:** Critical.

**Eye gaze:** Commonly supports the intended referent.  
**Head/body:** May orient toward the addressee.

**Static or dynamic:** Low-motion dynamic/static-pointing.  
**Spatial complexity:** High.

**Recognition implications:**  
The model cannot reliably determine YOU from handshape alone. It must preserve the pointing vector and spatial relationship between signer, camera and intended referent.

**Dataset instructions:**  
Record addressees at multiple positions relative to the signer. Record direct-to-camera and slightly off-axis signing. Label the target locus.

**Hard negatives:** I/ME, HE/SHE/IT, THIS, THAT.

**Expert validation:** Required.

---

## SV-ASL-013 — FAMILY

**Gloss:** FAMILY  
**Meaning:** Family / family group  
**Category:** People / Relationships  
**Difficulty:** 2 — Intermediate  
**Priority:** High

**Manuality:** Two-handed.  
**Hand relationship:** Both hands participate symmetrically/as a paired configuration.  
**Location:** Neutral signing space in front of torso.  
**Movement:** Hands move through a circular/paired spatial pattern characteristic of the sign.

**Non-manual information:** Usually neutral; meaning is primarily manual.

**Static or dynamic:** Dynamic.  
**Temporal complexity:** Moderate.  
**Visual complexity:** Moderate.

**Recognition implications:**  
Both hands must be retained. The model should not discard the non-dominant hand as a secondary feature.

**Dataset instructions:**  
Capture both left- and right-handed signer configurations. Preserve hand identity after mirroring/normalization.

**Potential confusions:** Group/team/class concepts may use related spatial organization; validate against expert-selected negative classes.

**Expert validation:** Required.

---

## SV-ASL-014 — FRIEND

**Gloss:** FRIEND  
**Meaning:** Friend  
**Category:** People / Relationships  
**Difficulty:** 2 — Intermediate  
**Priority:** High

**Manuality:** Two-handed.  
**Hand relationship:** Both hands interact/alternate in a linked configuration.  
**Location:** Neutral signing space in front of torso.  
**Movement:** Hands form a repeated interlocking/relationship movement.

**Non-manual information:** Usually neutral; emotional context may modify expression.

**Static or dynamic:** Dynamic.  
**Temporal complexity:** Moderate.  
**Visual complexity:** Moderate.

**Recognition implications:**  
The relationship between the two hands is more important than either hand considered independently.

**Dataset instructions:**  
Capture repetitions at different speeds and with different wrist orientations. Include two-hand non-linguistic movements as negative examples.

**Potential confusions:** Related social/relationship signs should be identified during expert validation.

**Expert validation:** Required.

---

## SV-ASL-015 — MOTHER / MOM

**Gloss:** MOTHER / MOM  
**Meaning:** Mother / mom  
**Category:** Family  
**Difficulty:** 1 — Foundation  
**Priority:** High

**Manuality:** One-handed in the common lexical form.  
**Handshape:** Commonly a flat/open B-like handshape with thumb extended.  
**Location:** Chin/face region.  
**Movement:** Contact/tap at the chin area.

**Non-manual information:** Normally neutral; affectionate/emphatic context can change facial affect.

**Static or dynamic:** Short dynamic sign.  
**Temporal complexity:** Low.  
**Visual complexity:** Low-to-moderate.

**Recognition implications:**  
Face-region location is highly important. The model must distinguish contact/location from visually similar face-region signs.

**Dataset instructions:**  
Capture variation in exact contact position and camera distance. Do not assume that the hand must occupy one exact pixel location.

**Potential confusions:** FATHER differs primarily in location; other face-contact signs need later hard-negative analysis.

**Expert validation:** Required.

---

## SV-ASL-016 — FATHER / DAD

**Gloss:** FATHER / DAD  
**Meaning:** Father / dad  
**Category:** Family  
**Difficulty:** 1 — Foundation  
**Priority:** High

**Manuality:** One-handed in the common lexical form.  
**Handshape:** Commonly the same/similar open hand configuration used in MOTHER.  
**Location:** Forehead/upper face region.  
**Movement:** Contact/tap near forehead.

**Non-manual information:** Normally neutral; context may add affect.

**Static or dynamic:** Short dynamic sign.  
**Temporal complexity:** Low.  
**Visual complexity:** Low-to-moderate.

**Recognition implications:**  
MOTHER ↔ FATHER is a deliberately important contrast pair because the hand configuration is closely related while **location differs**.

The model must therefore preserve body/face-relative coordinates.

**Dataset instructions:**  
Record MOTHER and FATHER under identical lighting, distance and signer conditions. This prevents the model from using background/signer differences as shortcuts.

**Hard negative:** MOTHER.

**Expert validation:** Required.

---

## SV-ASL-017 — BROTHER

**Gloss:** BROTHER  
**Meaning:** Brother  
**Category:** Family  
**Difficulty:** 2 — Intermediate  
**Priority:** High

**Manuality:** Two-handed.  
**Hand relationship:** Both hands use related hand configurations with one hand interacting with the other.  
**Location:** Neutral signing space in front of torso.  
**Movement:** Paired movement associated with the sibling relationship.

**Non-manual information:** Normally neutral.

**Static or dynamic:** Dynamic.  
**Temporal complexity:** Moderate.  
**Visual complexity:** Moderate-to-high.

**Recognition implications:**  
Two-hand geometry and movement order must be retained.

**Dataset instructions:**  
Capture both dominant-hand versions and different signer proportions. Preserve left/right hand identity during landmark normalization.

**Potential confusions:** SISTER and related family signs.

**Expert validation:** Required.

---

## SV-ASL-018 — SISTER

**Gloss:** SISTER  
**Meaning:** Sister  
**Category:** Family  
**Difficulty:** 2 — Intermediate  
**Priority:** High

**Manuality:** Two-handed.  
**Hand relationship:** Both hands participate in a paired movement/configuration.  
**Location:** Neutral signing space in front of torso.  
**Movement:** Sequential/paired movement associated with the lexical sign.

**Non-manual information:** Normally neutral.

**Static or dynamic:** Dynamic.  
**Temporal complexity:** Moderate.  
**Visual complexity:** Moderate-to-high.

**Recognition implications:**  
SISTER should be evaluated directly against BROTHER because both are family signs with related structural patterns.

**Dataset instructions:**  
Record BROTHER and SISTER under matched recording conditions. Include variations in speed and hand dominance.

**Potential confusions:** BROTHER, GIRL/WOMAN-related forms.

**Expert validation:** Required.

---

## SV-ASL-019 — CHILD

**Gloss:** CHILD / CHILDREN  
**Meaning:** Child / children; exact plural interpretation depends on construction  
**Category:** People / Family  
**Difficulty:** 1 — Foundation  
**Priority:** High

**Manuality:** Two-handed.  
**Location:** Lower neutral signing space near torso/waist region.  
**Movement:** Hands move downward/along a short vertical path associated with the child's height/body concept.

**Non-manual information:** Generally neutral.

**Static or dynamic:** Dynamic.  
**Temporal complexity:** Low-to-moderate.

**Important linguistic note:**  
The English singular/plural distinction does not automatically mean SignVox should create separate isolated classes. ASL can modify nouns and use context/number marking. Gallaudet explicitly describes pluralization through modification of parameters. citeturn0search24

**Recognition implications:**  
Represent the lexical concept CHILD separately from later number/plural interpretation where possible.

**Dataset instructions:**  
Record canonical isolated CHILD first. Later collect plural/number-modified forms as separate annotated constructions.

**Potential confusions:** BABY, BOY, GIRL, person classifiers.

**Expert validation:** Required.

---

## SV-ASL-020 — BABY

**Gloss:** BABY  
**Meaning:** Baby / infant  
**Category:** People / Family  
**Difficulty:** 1 — Foundation  
**Priority:** High

**Manuality:** Two-handed.  
**Hand relationship:** Hands form a cradling/holding configuration.  
**Location:** In front of torso.  
**Movement:** Small rocking/cradling motion.

**Non-manual information:** Facial affect can naturally be affectionate but is not the sole lexical cue.

**Static or dynamic:** Dynamic.  
**Temporal complexity:** Low-to-moderate.  
**Visual complexity:** Moderate.

**Recognition implications:**  
The model should recognize the characteristic two-arm/hand relationship and rocking motion rather than simply classify an arbitrary two-hand pose.

**Dataset instructions:**  
Record different rocking amplitudes and speeds. Include stationary hand-holding negatives.

**Potential confusions:** CHILD, HOLD, ROCK/comfort gestures.

**Expert validation:** Required.

---

# Batch 02 — Cross-sign recognition findings

## 1. Pronouns are NOT ordinary vocabulary classes

I/ME and YOU are indexing operations.

The future model should eventually represent:

```text
INDEX
├── referent
├── source locus
├── target locus
├── direction
├── gaze
└── discourse context
```

This is supported by Gallaudet's standards, which explicitly describe pronouns and referents through spatial indexing and eye gaze. citeturn0search24

## 2. MOTHER/FATHER is an important location contrast

These signs demonstrate why normalized body-relative coordinates matter.

Conceptually:

```text
same/similar hand configuration
        +
different body location
        ↓
different lexical meaning
```

Therefore the model should retain face/head landmarks and body-relative coordinates.

## 3. BROTHER/SISTER requires two-hand interaction

Do not reduce the sample to the dominant hand.

The relationship between the two hands is part of the sign representation.

## 4. CHILD/CHILDREN should not automatically become separate classes

Number/plural information can be expressed through ASL grammar and modification. The future linguistic layer should be able to represent:

```text
CHILD
+
NUMBER/PLURAL
```

rather than forcing every inflected construction into an independent visual class. citeturn0search24

## 5. Spatial context is now a core SignVox requirement

Lifeprint's instructional material explicitly demonstrates establishing people on locations in signing space and returning to those locations to refer to them later. citeturn0search9turn0search1

Therefore the future SignVox representation needs a persistent **referent/locus layer**.

---

# Recommended future representation

This is an architectural target, NOT an implementation task:

```json
{
  "manual": {
    "lexeme": "INDEX"
  },
  "spatial": {
    "referent": "ADDRESSEE",
    "locus": [0.72, 0.46, 0.31]
  },
  "non_manual": {
    "gaze_target": "ADDRESSEE"
  },
  "temporal": {
    "start": 1.20,
    "end": 1.48
  }
}
```

This gives SignVox a path toward actual language understanding instead of a flat 100-class gesture recognizer.

---

# Deliberate evaluation pairs for Batch 02

The eventual dataset/model evaluation should include:

- I/ME ↔ YOU
- I/ME ↔ HE/SHE/IT indexing
- YOU ↔ HE/SHE/IT indexing
- MOTHER ↔ FATHER
- BROTHER ↔ SISTER
- CHILD ↔ BABY
- FAMILY ↔ FRIEND
- CHILD ↔ person-classifier constructions

These should be tested under matched recording conditions.

---

# Expert validation requirements

Before these signs become training ground truth, an ASL expert should verify:

1. Canonical form
2. Accepted variants
3. Handshape
4. Location
5. Movement
6. Directionality
7. Spatial/indexing behavior
8. Non-manual requirements
9. Singular/plural behavior
10. Contextual usage

**Research status:** Batch 02 complete.  
**Expert validation:** Pending.  
**Training status:** Not approved.  
**Dataset status:** Not created.
