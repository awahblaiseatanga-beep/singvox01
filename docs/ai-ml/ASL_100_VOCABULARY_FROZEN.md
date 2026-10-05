# SignVox Competition Vocabulary â€” FROZEN

1. **Freeze status:** FROZEN
2. **Freeze date:** 2026-10-01
3. **Source file:** docs/ai-ml/ASL_100_VOCABULARY_SPEC.md
4. **Total target classes:** 100
5. **Canonical class list & Stable class IDs:** (See Canonical Class List below)
6. **Dataset coverage status:**
   - 100 target classes
   - 81 classes with source matches
   - 17 classes with no source match
   - 2 ambiguous mappings
   - 2,606 selected videos
   *(Note: Target vocabulary = 100 classes. Current dataset coverage = 81 matched classes. The 19 uncovered/ambiguous classes remain in the frozen vocabulary explicitly.)*
7. **Expert validation:** PENDING
8. **Important limitations:** The target 100 classes are frozen, regardless of current dataset availability mapping. Freezing the vocabulary does NOT mean claiming that all 100 classes currently have training data.
9. **Change-control rules:**
   - After this freeze, changes to the competition vocabulary require an explicit version change (e.g. updating 1.0.0).
   - A future vocabulary change must NOT silently modify version 1.0.0.
   - Any future changes should create a new vocabulary version and document: added classes, removed classes, renamed classes, changed definitions, reason for change, impact on dataset, impact on trained models.
10. **Vocabulary Hash (SHA-256):** 3d27111ddf248247b46c4dc414c6c6977cd4a00b6e8e68ad5bddb4736c09b3ab
    *(Calculated from deterministically ordered <ID>:<Canonical Name>\n string payload derived from the competition list).*

## Canonical Class List

| ID | Canonical Name | Aliases | Description |
|---|---|---|---|
| ASL_001 | HELLO |  | Core greeting; visually simple |
| ASL_002 | GOOD |  | Useful but can visually overlap with THANK-YOU |
| ASL_003 | BAD |  | Basic polarity pair with GOOD |
| ASL_004 | PLEASE |  | Politeness; validate exact regional production |
| ASL_005 | THANK-YOU |  | Core politeness; directional nuance |
| ASL_006 | SORRY |  | Common social repair |
| ASL_007 | HELP |  | Directional; movement can encode participants |
| ASL_008 | STOP |  | Strong practical/safety value |
| ASL_009 | WAIT |  | Repeated finger movement; easy temporal signature |
| ASL_010 | UNDERSTAND |  | Important communication-state concept |
| ASL_011 | YES |  | Core confirmation |
| ASL_012 | NO |  | Core negation |
| ASL_013 | AGAIN |  | Useful repair signal |
| ASL_014 | SLOW |  | Useful for communication repair |
| ASL_015 | DON'T-UNDERSTAND |  | Critical repair phrase/concept |
| ASL_016 | NAME |  | Core introduction sign |
| ASL_017 | ME | PRO1 | Usually produced by pointing; spatial indexing |
| ASL_018 | YOU | PRO2 | Spatially directed; context-dependent |
| ASL_019 | FAMILY |  | High conversational value |
| ASL_020 | FRIEND |  | Common social vocabulary |
| ASL_021 | MOTHER |  | Common family term |
| ASL_022 | FATHER |  | Common family term |
| ASL_023 | BROTHER |  | Two-handed/compound structure; validate |
| ASL_024 | SISTER |  | Two-handed/compound structure; validate |
| ASL_025 | CHILD |  | Common family/social term |
| ASL_026 | BABY |  | Visually distinctive; useful |
| ASL_027 | TEACHER |  | Useful in school/learning contexts |
| ASL_028 | GO |  | Directional movement; important for continuous signing |
| ASL_029 | COME |  | Directional counterpart to GO |
| ASL_030 | GIVE |  | Directional verb; excellent test of spatial meaning |
| ASL_031 | TAKE |  | Context-sensitive movement |
| ASL_032 | WANT |  | Common functional verb |
| ASL_033 | NEED |  | High-value request/need concept |
| ASL_034 | HAVE |  | Core possession/existence concept |
| ASL_035 | KNOW |  | Common cognitive verb |
| ASL_036 | LIKE |  | Common preference/emotion concept |
| ASL_037 | SEE |  | Common perception verb |
| ASL_038 | THINK |  | Important but face/location/context can matter |
| ASL_039 | LEARN |  | Useful for education and SignVox context |
| ASL_040 | TEACH |  | Useful counterpart to LEARN |
| ASL_041 | STUDY |  | Practical student vocabulary |
| ASL_042 | SCHOOL |  | Distinctive movement; common context |
| ASL_043 | WORK |  | Very common concept |
| ASL_044 | HOME |  | High-frequency location |
| ASL_045 | STORE |  | Useful everyday location |
| ASL_046 | CHURCH |  | Locally relevant but culturally specific |
| ASL_047 | HOSPITAL |  | Important health/safety context |
| ASL_048 | DOCTOR |  | Important health context |
| ASL_049 | BATHROOM |  | High practical value |
| ASL_050 | HERE |  | Spatial/deictic; useful but context-sensitive |
| ASL_051 | THERE |  | Spatial/deictic; context-sensitive |
| ASL_052 | IN |  | Spatial relation; better as later-stage language feature |
| ASL_053 | OUT |  | Spatial relation; better as later-stage language feature |
| ASL_054 | TODAY | NOW | ASL time concepts can overlap; model as canonical concept with variants |
| ASL_055 | YESTERDAY |  | Temporal movement |
| ASL_056 | TOMORROW |  | Temporal movement |
| ASL_057 | MORNING |  | Useful everyday time |
| ASL_058 | NIGHT |  | Useful everyday time |
| ASL_059 | DAY |  | Broad temporal concept |
| ASL_060 | WHAT |  | Requires correct WH non-manual marker |
| ASL_061 | WHO |  | Handshape + facial marker |
| ASL_062 | WHERE |  | Movement + WH facial marker |
| ASL_063 | WHEN |  | Movement + WH facial marker |
| ASL_064 | WHY |  | Handshape/location + WH facial marker |
| ASL_065 | HOW |  | Two-hand movement; question facial marker |
| ASL_066 | FOOD |  | High practical value |
| ASL_067 | EAT |  | High practical value |
| ASL_068 | DRINK |  | High practical value |
| ASL_069 | WATER |  | High practical value |
| ASL_070 | HUNGRY |  | Useful everyday need |
| ASL_071 | SLEEP |  | Common everyday need |
| ASL_072 | PAIN | HURT | Important health communication |
| ASL_073 | SICK |  | Important health communication |
| ASL_074 | EMERGENCY |  | High importance; verify exact ASL production |
| ASL_075 | DANGER |  | High safety value |
| ASL_076 | FIRE |  | Useful emergency concept |
| ASL_077 | CALL | PHONE | Useful bridge to spoken communication |
| ASL_078 | PHONE |  | Very practical |
| ASL_079 | COMPUTER |  | Useful digital vocabulary |
| ASL_080 | SIGN | SIGN-LANGUAGE | Core SignVox concept |
| ASL_081 | LANGUAGE |  | Useful meta-language concept |
| ASL_082 | COMMUNICATE |  | Conceptually important; exact production needs expert validation |
| ASL_083 | DEAF |  | Important to SignVox domain |
| ASL_084 | HEARING |  | Important counterpart to DEAF |
| ASL_085 | SPEAK |  | Useful for speechâ†”sign interaction |
| ASL_086 | MEET |  | Directional/spatial; good test of participant encoding |
| ASL_087 | FINE | OKAY | Common conversational response |
| ASL_088 | MORE |  | Common request/quantity concept |
| ASL_089 | FINISH | DONE | Conversation control and completion |
| ASL_090 | LOVE |  | Common emotional/social concept |
| ASL_091 | HAPPY |  | Common emotional state |
| ASL_092 | SAD |  | Common emotional state |
| ASL_093 | ANGRY |  | Common emotional state |
| ASL_094 | AFRAID | SCARED | Useful emotional state; validate exact production |
| ASL_095 | FEEL |  | Important but context-dependent |
| ASL_096 | NICE | CLEAN | Useful but potentially ambiguous across meanings |
| ASL_097 | BIG |  | Good early visual adjective |
| ASL_098 | SMALL |  | Good contrast pair with BIG |
| ASL_099 | HOT |  | Everyday/environmental concept |
| ASL_100 | COLD |  | Everyday/environmental concept |
