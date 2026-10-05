# SignVox Project Context

This document maintains the high-level perspective of what SignVox is, why it is being built, and where it is going.

## Product Vision
Create a real-time communication bridge between sign language and spoken language that works seamlessly through an ordinary smartphone camera and screen.

## CITX 2026 Context
SignVox won the first stage of the CITX 2026 competition in Buea and will be presented at the finals in Yaoundé. The core objective for CITX is to produce a credible, functioning SignVox prototype demonstrating the underlying core concept rather than attempting to build a fully universal, yet flawed, translator.

## Current Product Concept & Two-Way Communication
We are currently conceptualizing a complete duplex setup:
1. **Sign → Speech Pipeline:** Camera → Vision Processing → Sign Recognition → Translation → Text/Speech.
2. **Speech → Sign Pipeline:** Microphone → Speech Recognition → Translation → Sign Sequence Mapping → Avatar Animation.

## Mobile-First Requirements
The solution must operate primarily via smartphones. Low latency, clear visual feedback, strong camera integration, and reliable offline capabilities (where internet is limited) are strict requirements.

## AI & Avatar Requirements
- **AI Requirements:** The system should not assume sign language is a collection of static hand gestures. It must eventually support temporal and contextual evaluation (movement, face, body pose).
- **Avatar Requirements:** It must accurately perform sign sequences via clear hand and body movements with appropriate facial animation, operating smoothly on mobile devices.

## Known Constraints
- Hardware constraints of typical mobile phones (cannot run massive foundational models directly).
- Real-time video processing latency vs. accuracy tradeoffs. 
- Must ensure that we don't present hallucinated translations (systems should gracefully fail with uncertainty rather than confidently mis-translating).

## Project State
### CONFIRMED
- The goal is a mobile-first duplex sign-language-to-speech translator.
- The repository structure maps domain responsibilities independently (`app/`, `ai/`, `backend/`, `experiments/`, etc.).

### TO BE DECIDED (Architecture Discovery Phase required)
- **Mobile Framework**
- **Camera Pipeline**
- **Computer-Vision Framework**
- **Machine Learning / AI Technologies**
- **Translational Language Representation**
- **Backend & State Architecture**
- **Online vs Offline capabilities for model inference**

### UNKNOWN
- Initial vocabulary size and primary sign language domain for MVP.

## Immediate Objectives
- Create a credible technology foundation.
- Transition into Technical Architecture Discovery to decide the primary tech stack based strictly on verifying camera constraints and mobile inference.

## Long-Term Vision
Establishing a universal, naturally flowing communication layer between the hearing world and deaf or hard-of-hearing signers, acting as a real-time agent built directly into personal devices.
