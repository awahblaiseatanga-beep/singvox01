# SignVox

SignVox is an AI-powered two-way sign language communication application designed to bridge the gap between deaf and hard-of-hearing sign-language users and individuals who do not understand sign language. 

## The Problem
Everyday communication between sign-language users and non-signers is difficult without a human translator. SignVox removes this barrier by allowing regular smartphones to act as an immediate, real-time communication bridge.

## Product Vision
To transform an ordinary smartphone into an AI-powered communication bridge that can see sign language, understand spoken language, and communicate through both speech and visual signing without requiring specialized hardware.

## Core Communication Flows
1. **Sign Language → Speech**
   Camera captures signs → AI interprets temporal hand and pose movements → Translates to text/meaning → Text-to-Speech output to hearing user.

2. **Speech → Sign Language**
   Microphone captures speech → Speech-to-Text → Semantic language processing → Sign sequence mapped to avatar → Avatar signs continuously to the deaf/hard-of-hearing user.

## Repository Structure
This repository remains initially technology-agnostic to focus on component boundaries:
- `app/` — Mobile application interface and camera bindings.
- `ai/` — Artificial Intelligence algorithms, logic, processing, and models.
- `backend/` — Server services, APIs, and configuration.
- `avatar/` — 3D/2D Avatar models and animation data.
- `experiments/` — Short-term R&D models not yet integrated.
- `tests/` — Automated core testing suites.
- `docs/` — Core architecture, decisions, and documentation.
- `scripts/` — Scripts mapped to environment preparation.

## Current Project Status
- **Status:** Empty Structure Scaffolding complete; Pending Next Architecture Phase decisions.
- **Technology Stack:** UNDECIDED (Awaiting detailed framework evaluations).

## Development Philosophy
- **Mobile-first Focus:** Target mobile form factors initially. Keep interface straightforward.
- **Measurable Architecture Decisions:** Base technical conclusions on actual limitations (camera response, model bounds).
- **Incremental Expansion:** Build a well-defined domain vocabulary first before attempting to generalize.
- **Data Protection:** Consider video feeds and voice streams as sensitive information unless stated.

## Environment Customization
1. Ensure the repository root matches expectation variables.
2. Form your local `.env` using `.env.example` structure.
3. Detailed setup rules will be placed inside `docs/setup` after final framework choices.

## Development Phases
- **Phase 1:** Mobile Application Foundation (Evaluating tech candidates)
- **Phase 2:** Camera Pipeline construction
- **Phase 3:** Sign Recognition Prototype implementation
- **Phase 4:** Speech-to-Sign Prototype verification
- **Phase 5:** Digital Avatar Integration
- **Phase 6:** Duplex Conversation Loop testing
- **Phase 7:** Field validation
