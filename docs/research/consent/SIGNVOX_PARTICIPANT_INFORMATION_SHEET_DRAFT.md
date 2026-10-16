# Participant Information Sheet (Draft)
**Project Title**: SignVox – Continuous Sign-to-Text Research Pilot
**Lead Researcher / Organization**: [DECISION REQUIRED: Insert Project Owner / Organizational Name]
**Contact Information**: [DECISION REQUIRED: Insert Contact Email/Phone]
**Ethics/Legal Approval Reference**: [DECISION REQUIRED: Insert Review Board / Legal Approval ID]

## 1. What is the purpose of this research?
SignVox is currently in a research and development phase exploring how computer models can recognize continuous sign language (multiple signs strung together). **This is an early feasibility experiment, not a clinical tool or a final production app.** We are testing if our systems can accurately identify the boundaries between signs. 

## 2. What will I be asked to do?
If you agree to participate, you will be asked to perform specific sign language sequences (e.g., signing "HELLO", "YES", or performing natural continuous transitions between signs) while being recorded on video. You may also be recorded during "idle" periods (sitting naturally without signing) to help the system filter out background motion.

## 3. What data will be collected?
- **Video Recording (Muted):** Regular video of your upper body and face. All audio is disabled natively; your voice and background audio will not be recorded.
- **Biometric Landmarks:** The computer extracts points tracking your hands, body posture, and facial expressions (a 366-dimension array). 
- **Pseudonymous Identifiers:** Your actual name will be stored separately from the research data. Recordings will be labeled with a code (e.g., S003).

## 4. Is my data anonymous?
**No.** The video recordings clearly show your face. Furthermore, the numerical "landmark" arrays mapped by the computer contain geometric proportions of your face and body. **This geometric data is biologically unique and can potentially be used to identify you.** We use pseudonymization to separate your name from the data, but the data itself inherently tracks biometric identity.

## 5. Who will have access to my data?
Only authorized researchers [DECISION REQUIRED: Define Exact Custodians] will have access to the raw video and geometric landmarks.

## 6. How is my data stored and when is it deleted?
- **Storage Location:** [DECISION REQUIRED: Insert Secure Server/Local Storage Details].
- **Retention Period:** [DECISION REQUIRED: How long will video limit/JSON arrays be kept before destruction?].
- Note: Your signed consent form and name mapping will be kept entirely separate from the biometric files.

## 7. Can I withdraw from the study?
Participation is purely voluntary. Refusing to participate will not result in any penalty. 
You may ask questions or request withdrawal at any time. However, there are practical limits:
- If you request withdrawal **before** the data is aggregated or models are finalized, we can delete your raw video and landmark files.
- If you request withdrawal **after** your signs have been used to update the shared statistical parameters of the translated model, it is mathematically impossible to untrain the model to remove your data.
- **Withdrawal Cut-Off Date:** [DECISION REQUIRED: Date/Phase after which withdrawal is impossible].

## 8. Risks and Benefits
- **Risks:** The primary risk is a potential data breach exposing your video identity and biometric landmarks. We employ strict access controls to mitigate this.
- **Benefits:** There are no direct personal clinical or financial benefits guaranteed for you by participating. Broadly, this research may advance continuous sign language interpretation software.

## 9. How will findings be reported?
Results will only be reported in aggregate (e.g., statistical accuracy of the model). No individual videos or names will be published without separate, explicit, unambiguous permission.

## 10. Contact Information
If you have any questions or wish to exercise your data rights, please contact:
[DECISION REQUIRED: Placeholder for internal QA/Privacy officer].
