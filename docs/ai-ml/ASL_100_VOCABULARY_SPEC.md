# SignVox ASL-100 Vocabulary Specification — Research Draft

**Status:** Research draft / candidate vocabulary  
**Initial language:** American Sign Language (ASL)  
**Purpose:** Define the first 100 ASL lexical concepts to investigate for SignVox's recognition dataset and MVP.

## Research basis

ASL is a complete natural visual-spatial language. Gallaudet describes five core sign parameters: **handshape, palm orientation, location, movement, and non-manual markers**. Non-manual components such as eye gaze, facial expression, and head/body movement can carry grammatical information. citeturn0search30turn0search4

Lifeprint provides a "First 100 Signs" curriculum and extensive sign-by-sign references. It also explicitly notes that ASL signs can have multiple versions and regional variation, so this document is a **candidate vocabulary**, not a final labeling authority. citeturn1search7turn2search10

## Important rule

The labels below are **concepts/glosses**, not English words that can simply be translated one-for-one into ASL. The final SignVox dataset must be validated by a qualified Deaf/native ASL signer or ASL expert before recording/training.

## Difficulty

- **1 — Foundation:** relatively simple visual signature; good early training candidate.
- **2 — Intermediate:** movement, two hands, orientation, or contextual variation matters.
- **3 — Advanced:** strong contextual, spatial, numerical, directional, or non-manual dependence.

## Candidate vocabulary

| # | Gloss / concept | Category | Difficulty | Priority | Research note |
|---:|---|---|---:|---|---|
| 1 | **HELLO** | Communication | 1 | High | Core greeting; visually simple |
| 2 | **GOOD** | Communication | 1 | High | Useful but can visually overlap with THANK-YOU |
| 3 | **BAD** | Communication | 1 | High | Basic polarity pair with GOOD |
| 4 | **PLEASE** | Communication | 1 | High | Politeness; validate exact regional production |
| 5 | **THANK-YOU** | Communication | 1 | High | Core politeness; directional nuance |
| 6 | **SORRY** | Communication | 1 | High | Common social repair |
| 7 | **HELP** | Communication | 2 | High | Directional; movement can encode participants |
| 8 | **STOP** | Safety | 1 | High | Strong practical/safety value |
| 9 | **WAIT** | Conversation | 1 | High | Repeated finger movement; easy temporal signature |
| 10 | **UNDERSTAND** | Conversation | 2 | High | Important communication-state concept |
| 11 | **YES** | Conversation | 1 | High | Core confirmation |
| 12 | **NO** | Conversation | 1 | High | Core negation |
| 13 | **AGAIN** | Conversation | 1 | High | Useful repair signal |
| 14 | **SLOW** | Conversation | 1 | High | Useful for communication repair |
| 15 | **DON'T-UNDERSTAND** | Conversation | 2 | High | Critical repair phrase/concept |
| 16 | **NAME** | Identity | 1 | High | Core introduction sign |
| 17 | **ME/PRO1** | Indexing | 1 | High | Usually produced by pointing; spatial indexing |
| 18 | **YOU/PRO2** | Indexing | 1 | High | Spatially directed; context-dependent |
| 19 | **FAMILY** | People | 1 | High | High conversational value |
| 20 | **FRIEND** | People | 1 | High | Common social vocabulary |
| 21 | **MOTHER** | People | 1 | High | Common family term |
| 22 | **FATHER** | People | 1 | High | Common family term |
| 23 | **BROTHER** | People | 2 | High | Two-handed/compound structure; validate |
| 24 | **SISTER** | People | 2 | High | Two-handed/compound structure; validate |
| 25 | **CHILD** | People | 1 | High | Common family/social term |
| 26 | **BABY** | People | 1 | High | Visually distinctive; useful |
| 27 | **TEACHER** | Education | 2 | High | Useful in school/learning contexts |
| 28 | **GO** | Actions | 2 | High | Directional movement; important for continuous signing |
| 29 | **COME** | Actions | 2 | High | Directional counterpart to GO |
| 30 | **GIVE** | Actions | 2 | High | Directional verb; excellent test of spatial meaning |
| 31 | **TAKE** | Actions | 2 | Medium | Context-sensitive movement |
| 32 | **WANT** | Actions | 2 | High | Common functional verb |
| 33 | **NEED** | Actions | 2 | High | High-value request/need concept |
| 34 | **HAVE** | Actions | 1 | High | Core possession/existence concept |
| 35 | **KNOW** | Actions | 1 | High | Common cognitive verb |
| 36 | **LIKE** | Actions | 1 | High | Common preference/emotion concept |
| 37 | **SEE** | Actions | 1 | High | Common perception verb |
| 38 | **THINK** | Actions | 2 | Medium | Important but face/location/context can matter |
| 39 | **LEARN** | Education | 2 | High | Useful for education and SignVox context |
| 40 | **TEACH** | Education | 2 | Medium | Useful counterpart to LEARN |
| 41 | **STUDY** | Education | 2 | High | Practical student vocabulary |
| 42 | **SCHOOL** | Places | 2 | High | Distinctive movement; common context |
| 43 | **WORK** | Places/Activities | 1 | High | Very common concept |
| 44 | **HOME** | Places | 1 | High | High-frequency location |
| 45 | **STORE** | Places | 2 | High | Useful everyday location |
| 46 | **CHURCH** | Places | 2 | Medium | Locally relevant but culturally specific |
| 47 | **HOSPITAL** | Health | 2 | High | Important health/safety context |
| 48 | **DOCTOR** | Health | 2 | High | Important health context |
| 49 | **BATHROOM** | Needs | 2 | High | High practical value |
| 50 | **HERE** | Spatial | 1 | High | Spatial/deictic; useful but context-sensitive |
| 51 | **THERE** | Spatial | 1 | High | Spatial/deictic; context-sensitive |
| 52 | **IN** | Spatial | 2 | Medium | Spatial relation; better as later-stage language feature |
| 53 | **OUT** | Spatial | 2 | Medium | Spatial relation; better as later-stage language feature |
| 54 | **TODAY/NOW** | Time | 1 | High | ASL time concepts can overlap; model as canonical concept with variants |
| 55 | **YESTERDAY** | Time | 2 | High | Temporal movement |
| 56 | **TOMORROW** | Time | 2 | High | Temporal movement |
| 57 | **MORNING** | Time | 2 | High | Useful everyday time |
| 58 | **NIGHT** | Time | 2 | High | Useful everyday time |
| 59 | **DAY** | Time | 1 | High | Broad temporal concept |
| 60 | **WHAT** | Questions | 2 | High | Requires correct WH non-manual marker |
| 61 | **WHO** | Questions | 2 | High | Handshape + facial marker |
| 62 | **WHERE** | Questions | 2 | High | Movement + WH facial marker |
| 63 | **WHEN** | Questions | 2 | High | Movement + WH facial marker |
| 64 | **WHY** | Questions | 2 | High | Handshape/location + WH facial marker |
| 65 | **HOW** | Questions | 2 | High | Two-hand movement; question facial marker |
| 66 | **FOOD** | Needs | 1 | High | High practical value |
| 67 | **EAT** | Needs | 1 | High | High practical value |
| 68 | **DRINK** | Needs | 1 | High | High practical value |
| 69 | **WATER** | Needs | 1 | High | High practical value |
| 70 | **HUNGRY** | Needs | 2 | High | Useful everyday need |
| 71 | **SLEEP** | Needs | 1 | High | Common everyday need |
| 72 | **PAIN/HURT** | Health | 2 | High | Important health communication |
| 73 | **SICK** | Health | 2 | High | Important health communication |
| 74 | **EMERGENCY** | Safety | 3 | Medium | High importance; verify exact ASL production |
| 75 | **DANGER** | Safety | 2 | High | High safety value |
| 76 | **FIRE** | Safety | 2 | High | Useful emergency concept |
| 77 | **CALL/PHONE** | Technology | 2 | High | Useful bridge to spoken communication |
| 78 | **PHONE** | Technology | 1 | High | Very practical |
| 79 | **COMPUTER** | Technology | 2 | High | Useful digital vocabulary |
| 80 | **SIGN/SIGN-LANGUAGE** | Technology/Language | 2 | High | Core SignVox concept |
| 81 | **LANGUAGE** | Technology/Language | 2 | Medium | Useful meta-language concept |
| 82 | **COMMUNICATE** | Technology/Language | 3 | Medium | Conceptually important; exact production needs expert validation |
| 83 | **DEAF** | Identity | 2 | High | Important to SignVox domain |
| 84 | **HEARING** | Identity | 2 | High | Important counterpart to DEAF |
| 85 | **SPEAK** | Communication | 2 | High | Useful for speech↔sign interaction |
| 86 | **MEET** | Communication | 2 | High | Directional/spatial; good test of participant encoding |
| 87 | **FINE/OKAY** | Communication | 1 | High | Common conversational response |
| 88 | **MORE** | Quantity | 1 | High | Common request/quantity concept |
| 89 | **FINISH/DONE** | Conversation | 2 | High | Conversation control and completion |
| 90 | **LOVE** | Emotion | 1 | High | Common emotional/social concept |
| 91 | **HAPPY** | Emotion | 2 | High | Common emotional state |
| 92 | **SAD** | Emotion | 2 | High | Common emotional state |
| 93 | **ANGRY** | Emotion | 2 | High | Common emotional state |
| 94 | **AFRAID/SCARED** | Emotion | 2 | Medium | Useful emotional state; validate exact production |
| 95 | **FEEL** | Emotion | 2 | Medium | Important but context-dependent |
| 96 | **NICE/CLEAN** | Description | 2 | Medium | Useful but potentially ambiguous across meanings |
| 97 | **BIG** | Description | 1 | High | Good early visual adjective |
| 98 | **SMALL** | Description | 1 | High | Good contrast pair with BIG |
| 99 | **HOT** | Description | 2 | High | Everyday/environmental concept |
| 100 | **COLD** | Description | 2 | High | Everyday/environmental concept |

## Concepts intentionally held for the next expansion

The following concepts were researched but held outside the first 100 so the MVP vocabulary remains focused:

**REPEAT, WE, THEY, WEEK, MONTH, YEAR, LATER, WHICH, HOW-MANY, HOW-MUCH, QUESTION/ASK, THIRSTY, MEDICINE, SAFE, INTERNET, VIDEO.**

These should not be forgotten; they are **Expansion-101+ candidates**.

## What must be recorded for every final sign

Before a sign enters the training dataset, add:

1. Canonical ASL gloss
2. Meaning / usage
3. Handshape
4. One-handed / two-handed
5. Dominant vs non-dominant hand
6. Palm/finger orientation
7. Signing location
8. Movement trajectory
9. Contact points
10. Symmetry / hand relationship
11. Non-manual markers
12. Directionality / spatial indexing
13. Common variants
14. Commonly confused signs
15. Recognition difficulty
16. Dataset recording instructions
17. Expert validation status
18. Source/reference video

## Important linguistic findings

- **Do not model ASL as English word substitution.** Lifeprint explicitly describes vocabulary items as sign concepts that can have several meanings depending on context and inflection. citeturn2search10
- **Directional verbs matter.** HELP and MEET can encode participants through movement direction, so the model eventually needs spatial information rather than only classifying static gestures. citeturn0search0turn0search12
- **Questions require non-manual information.** Yes/no questions generally use raised eyebrows, while WH-type questions use a different facial pattern; this means face/head features should not be discarded from the recognition pipeline. citeturn1search0turn0search31
- **Temporal context matters.** ASL can establish a time frame and then use the same verb form rather than English-style verb conjugation. citeturn1search9
- **Signs can overlap visually.** GOOD and THANK-YOU, for example, share substantial form similarity and are distinguished partly by movement/direction/context. citeturn0search1turn0search10
- **Regional/production variation exists.** The dataset should record approved variants rather than treating every variation as an error. citeturn1search7

## Recommended dataset progression

### Stage 1 — 20 signs
Use the highest-priority, visually tractable concepts from the list to validate the camera → landmark → temporal model pipeline.

### Stage 2 — 50 signs
Add two-handed signs, directional signs, question signs, and moderate movement complexity.

### Stage 3 — 100 signs
Add contextual, spatial, emotional, health, safety, and technology concepts.

### Stage 4 — continuous signing
Do not simply train a 100-class classifier and assume it can translate conversation. Add temporal segmentation, sign sequencing, ASL grammar representation, and eventually continuous-signing datasets.

## Expert validation gate

**Required before dataset collection:**
- A Deaf/native ASL signer or qualified ASL expert reviews every selected concept.
- Confirm canonical sign and acceptable variants.
- Confirm whether the English label maps cleanly to an ASL lexical concept.
- Mark signs that require non-manual markers or spatial context.
- Record a reference demonstration for each accepted sign.

**Current status:** Candidate vocabulary researched. Detailed evaluations for the first 20 core signs are available in [Batch 01](./ASL_100_SIGN_SPECIFICATIONS_BATCH_01.md) and [Batch 02](./ASL_100_SIGN_SPECIFICATIONS_BATCH_02.md). Exact per-sign parameter sheets and dataset recording protocol remain as active research paths.
