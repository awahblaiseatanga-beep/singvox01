import csv
import json
import re
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path(r"d:\Singvox\Singvox")
ASL_CITIZEN_DIR = Path(r"D:\ASL_Citizen\ASL_Citizen")
SPLITS_DIR = ASL_CITIZEN_DIR / "splits"
VOCAB_SPEC = REPO_ROOT / "docs" / "ai-ml" / "ASL_100_VOCABULARY_SPEC.md"
OLD_MAPPING_PATH = REPO_ROOT / "ai" / "sign-recognition" / "config" / "asl100_asl_citizen_mapping.json"

def run_deep_audit():
    # 1. Load all ASL Citizen rows
    records_by_gloss = defaultdict(list)
    video_to_records = defaultdict(list)
    all_glosses = set()
    
    for split_name in ["train", "val", "test"]:
        csv_path = SPLITS_DIR / f"{split_name}.csv"
        with open(csv_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                g = row["Gloss"].strip()
                v = row["Video file"].strip()
                pid = row["Participant ID"].strip()
                code = row.get("ASL-LEX Code", "").strip()
                rec = {
                    "participant_id": pid,
                    "video_file": v,
                    "gloss": g,
                    "code": code,
                    "split": split_name
                }
                records_by_gloss[g].append(rec)
                video_to_records[v].append(rec)
                all_glosses.add(g)

    # 2. Parse vocabulary spec
    classes = []
    lines = VOCAB_SPEC.read_text(encoding="utf-8").splitlines()
    table_started = False
    for line in lines:
        if line.strip().startswith("| # | Gloss / concept |"):
            table_started = True
            continue
        if table_started:
            if not line.strip().startswith("|"):
                if classes:
                    break
                continue
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 6 and parts[0].isdigit():
                idx = int(parts[0])
                raw_gloss = parts[1].replace("**", "").strip()
                classes.append({
                    "idx": idx,
                    "asl_id": f"ASL_{idx:03d}",
                    "name": raw_gloss,
                    "category": parts[2],
                    "difficulty": int(parts[3]) if parts[3].isdigit() else parts[3],
                    "priority": parts[4],
                    "research_note": parts[5] if len(parts) > 5 else ""
                })

    # 3. Load historical mapping
    with open(OLD_MAPPING_PATH, "r", encoding="utf-8") as f:
        old_mapping = {item["asl_id"]: item for item in json.load(f)}

    # 4. Map each class with explicit linguistic rationale
    audit_results = []
    
    for c in classes:
        asl_id = c["asl_id"]
        name = c["name"]
        old_item = old_mapping.get(asl_id, {})
        old_glosses = old_item.get("source_glosses", [])
        old_type = old_item.get("mapping_type", "unmapped")
        
        candidates_considered = []
        valid_matched_labels = []
        ambiguity_notes = ""
        missing_reasons = ""
        collection_reqs = ""
        mapping_status = "VERIFIED_MATCH"
        
        # Clean canonical components
        sub_terms = [t.strip() for t in name.split("/")]
        
        # Determine candidate search
        # Standard rules
        clean_terms = [re.sub(r"[^A-Z0-9]", "", t.upper()) for t in sub_terms]
        
        # Candidate labels search in all_glosses
        found_in_asl_citizen = set()
        
        # Specific per-class mappings
        if asl_id == "ASL_005": # THANK-YOU
            candidates_considered = ["THANKYOU", "THANK YOU", "THANKSGIVING"]
            valid_matched_labels = ["THANKYOU"]
            ambiguity_notes = "ASL Citizen formats compound as 'THANKYOU' without hyphen or space."
        elif asl_id == "ASL_015": # DON'T-UNDERSTAND
            candidates_considered = ["NOTUNDERSTAND", "MISUNDERSTAND", "DONTUNDERSTAND"]
            valid_matched_labels = ["NOTUNDERSTAND"]
            ambiguity_notes = "ASL Citizen uses 'NOTUNDERSTAND' for negation of understand. Conceptually identical to DON'T-UNDERSTAND."
        elif asl_id == "ASL_017": # ME/PRO1
            candidates_considered = ["ME", "I", "PRO1"]
            valid_matched_labels = ["ME"]
            ambiguity_notes = "ASL Citizen gloss is 'ME'."
        elif asl_id == "ASL_018": # YOU/PRO2
            candidates_considered = ["YOU", "PRO2"]
            valid_matched_labels = ["YOU"]
            ambiguity_notes = "ASL Citizen gloss is 'YOU'."
        elif asl_id == "ASL_026": # BABY
            candidates_considered = ["BABY", "BABY1", "BABY2", "BABYSITTER"]
            valid_matched_labels = ["BABY1", "BABY2"]
            ambiguity_notes = "Variants BABY1 and BABY2 exist in ASL Citizen representing standard production variants."
        elif asl_id == "ASL_032": # WANT
            candidates_considered = ["WANT", "WANT1", "WANT2", "DONTWANT"]
            valid_matched_labels = ["WANT1", "WANT2"]
            ambiguity_notes = "WANT1 and WANT2 exist; DONTWANT excluded as negative polarity variant."
        elif asl_id == "ASL_040": # TEACH
            candidates_considered = ["TEACH", "TEACH1", "TEACH2", "TEACHER"]
            valid_matched_labels = ["TEACH1", "TEACH2"]
            ambiguity_notes = "TEACH1 and TEACH2 exist. TEACHER excluded to prevent noun/agent confusion with ASL_027 (TEACHER)."
        elif asl_id == "ASL_045": # STORE
            candidates_considered = ["STORE", "SHOP1", "SHOP2", "MARKET", "GROCERY"]
            valid_matched_labels = []
            mapping_status = "MISSING_DATA"
            missing_reasons = "No gloss 'STORE' in ASL Citizen. 'SHOP1'/'SHOP2' exist but lexical equivalence to noun 'STORE' requires Deaf expert validation under constraint 4."
            collection_reqs = "Record native ASL signers performing noun STORE (double downward/forward motion with O-hands)."
        elif asl_id == "ASL_047": # HOSPITAL
            candidates_considered = ["HOSPITAL", "HOSPITAL1", "HOSPITAL2"]
            valid_matched_labels = ["HOSPITAL1", "HOSPITAL2"]
            ambiguity_notes = "HOSPITAL1 and HOSPITAL2 exist as valid production variants."
        elif asl_id == "ASL_048": # DOCTOR
            candidates_considered = ["DOCTOR", "DOCTOR1", "DOCTOR2"]
            valid_matched_labels = ["DOCTOR1", "DOCTOR2"]
            ambiguity_notes = "DOCTOR1 and DOCTOR2 exist as valid production variants."
        elif asl_id == "ASL_054": # TODAY/NOW
            candidates_considered = ["TODAY", "NOW"]
            valid_matched_labels = ["TODAY", "NOW"]
            ambiguity_notes = "Both TODAY and NOW are accepted variants for this canonical time concept."
        elif asl_id == "ASL_058": # NIGHT
            candidates_considered = ["NIGHT", "NIGHT1", "NIGHT2", "EVERYNIGHT", "OVERNIGHT"]
            valid_matched_labels = ["NIGHT1", "NIGHT2"]
            ambiguity_notes = "NIGHT1 and NIGHT2 exist; compound phrases EVERYNIGHT/OVERNIGHT excluded."
        elif asl_id == "ASL_060": # WHAT
            candidates_considered = ["WHAT", "WHAT1", "WHAT2", "WHAT FOR"]
            valid_matched_labels = ["WHAT1", "WHAT2"]
            ambiguity_notes = "WHAT1 and WHAT2 exist as production variants."
        elif asl_id == "ASL_065": # HOW
            candidates_considered = ["HOW", "HOW1", "HOW2"]
            for g in all_glosses:
                if re.match(r"^HOW\d*$", g):
                    candidates_considered.append(g)
                    valid_matched_labels.append(g)
            if not valid_matched_labels:
                mapping_status = "MISSING_DATA"
                missing_reasons = "No 'HOW' gloss found in ASL Citizen."
                collection_reqs = "Record native signers performing HOW (curved hands palms-up rotation)."
        elif asl_id == "ASL_066": # FOOD
            candidates_considered = ["FOOD", "EAT1", "EAT2", "MEAL"]
            valid_matched_labels = []
            mapping_status = "MISSING_DATA"
            missing_reasons = "No 'FOOD' gloss in ASL Citizen. While FOOD/EAT are noun-verb pairs in ASL, merging FOOD into EAT violates constraint 4 (no inventing/merging labels) and collapses ASL_066 into ASL_067."
            collection_reqs = "Record native ASL signers performing noun FOOD (double-tap to mouth with squished-O handshape)."
        elif asl_id == "ASL_067": # EAT
            candidates_considered = ["EAT", "EAT1", "EAT2"]
            valid_matched_labels = ["EAT1", "EAT2"]
            ambiguity_notes = "EAT1 and EAT2 exist as production variants."
        elif asl_id == "ASL_068": # DRINK
            candidates_considered = ["DRINK", "DRINK1", "DRINK2"]
            valid_matched_labels = ["DRINK1", "DRINK2"]
            ambiguity_notes = "DRINK1 and DRINK2 exist as production variants."
        elif asl_id == "ASL_072": # PAIN/HURT
            candidates_considered = ["PAIN", "HURT"]
            valid_matched_labels = ["PAIN", "HURT"]
            ambiguity_notes = "Both PAIN and HURT exist in ASL Citizen; verified as valid lexical variants."
        elif asl_id == "ASL_074": # EMERGENCY
            candidates_considered = ["EMERGENCY", "URGENT", "CRISIS"]
            valid_matched_labels = []
            mapping_status = "MISSING_DATA"
            missing_reasons = "Zero occurrences of EMERGENCY or semantic synonyms in ASL Citizen."
            collection_reqs = "Record native signers performing EMERGENCY (shaking E-handshape)."
        elif asl_id == "ASL_077": # CALL
            candidates_considered = ["CALL", "CALL1", "CALL2", "PHONE", "CALLTTY", "CALLATTENTION"]
            # Check CALL1, CALL2
            valid_matched_labels = [g for g in ["CALL1", "CALL2"] if g in all_glosses]
            if not valid_matched_labels:
                mapping_status = "AMBIGUOUS_COLLISION"
                ambiguity_notes = "CALL shares PHONE alias in vocabulary spec. If only PHONE is used, creates deterministic routing collision with ASL_078."
            else:
                ambiguity_notes = "CALL1 and CALL2 exist in ASL Citizen representing directional verb to call/phone."
        elif asl_id == "ASL_078": # PHONE
            candidates_considered = ["PHONE", "CELLPHONE", "IPHONE"]
            valid_matched_labels = ["PHONE"]
            ambiguity_notes = "PHONE exists as noun sign for telephone."
        elif asl_id == "ASL_082": # COMMUNICATE
            candidates_considered = ["COMMUNICATE", "COMMUNICATION", "CONVERSATION"]
            valid_matched_labels = []
            mapping_status = "MISSING_DATA"
            missing_reasons = "Only nominal 'COMMUNICATION' exists. Mapping nominal form to verb COMMUNICATE requires Deaf validation."
            collection_reqs = "Record native signers performing verb COMMUNICATE (alternating C-hands moving forward/backward)."
        elif asl_id == "ASL_083": # DEAF
            candidates_considered = ["DEAF", "DEAF1", "DEAF2", "DEAFSCHOOL"]
            valid_matched_labels = ["DEAF1", "DEAF2"]
            ambiguity_notes = "DEAF1 and DEAF2 exist as standard ear-to-mouth / mouth-to-ear variants."
        elif asl_id == "ASL_085": # SPEAK
            candidates_considered = ["SPEAK", "TALK1", "TALK2", "VOICE", "SPEAKERS"]
            valid_matched_labels = []
            mapping_status = "MISSING_DATA"
            missing_reasons = "ASL Citizen has no 'SPEAK' gloss (only 'SPEAKERS' which refers to hardware audio speakers, and 'TALK1'/'TALK2')."
            collection_reqs = "Record native signers performing SPEAK/SPOKEN-LANGUAGE (index finger or 4-hand tapping chin/lips)."
        elif asl_id == "ASL_087": # FINE/OKAY
            candidates_considered = ["FINE", "FINE1", "FINE2", "OK", "OKAY"]
            valid_matched_labels = ["FINE1", "FINE2"]
            ambiguity_notes = "FINE1 and FINE2 exist as standard thumb-to-chest 5-hand variants."
        elif asl_id == "ASL_094": # AFRAID/SCARED
            candidates_considered = ["AFRAID", "SCARED"]
            valid_matched_labels = [g for g in ["AFRAID", "SCARED"] if g in all_glosses]
            ambiguity_notes = "SCARED exists in ASL Citizen as standard synonym for AFRAID."
        elif asl_id == "ASL_096": # NICE/CLEAN
            candidates_considered = ["NICE", "CLEAN"]
            valid_matched_labels = [g for g in ["NICE", "CLEAN"] if g in all_glosses]
            ambiguity_notes = "Both NICE and CLEAN exist in ASL Citizen as shared lexical forms."
        else:
            # General class handling
            for t in sub_terms:
                ct = re.sub(r"[^A-Z0-9]", "", t.upper())
                candidates_considered.append(t)
                if t in all_glosses and t not in valid_matched_labels:
                    valid_matched_labels.append(t)
                if ct in all_glosses and ct not in valid_matched_labels:
                    valid_matched_labels.append(ct)
                # numbered variants
                for g in all_glosses:
                    cg = re.sub(r"[^A-Z0-9]", "", g.upper())
                    if re.match(r"^" + re.escape(ct) + r"\d+$", cg):
                        if g not in candidates_considered:
                            candidates_considered.append(g)
                        if g not in valid_matched_labels:
                            valid_matched_labels.append(g)
            
            if not valid_matched_labels:
                mapping_status = "MISSING_DATA"
                missing_reasons = f"No gloss matching {name} found in ASL Citizen."
                collection_reqs = f"Record native signers performing canonical sign for {name}."

        # Compute candidate and valid counts
        candidate_vids = []
        for g in candidates_considered:
            if g in records_by_gloss:
                candidate_vids.extend(records_by_gloss[g])
                
        valid_vids = []
        for g in valid_matched_labels:
            if g in records_by_gloss:
                valid_vids.extend(records_by_gloss[g])

        # Deduplicate video files
        unique_cand_vids = set(r["video_file"] for r in candidate_vids)
        unique_valid_vids = set(r["video_file"] for r in valid_vids)
        distinct_signers = set(r["participant_id"] for r in valid_vids)

        audit_results.append({
            "idx": c["idx"],
            "asl_id": asl_id,
            "canonical_name": name,
            "category": c["category"],
            "difficulty": c["difficulty"],
            "priority": c["priority"],
            "mapping_status": mapping_status,
            "candidates_considered": sorted(list(set(candidates_considered))),
            "valid_matched_labels": sorted(list(set(valid_matched_labels))),
            "num_candidate_videos": len(unique_cand_vids),
            "num_valid_videos": len(unique_valid_vids),
            "num_distinct_signers": len(distinct_signers),
            "ambiguity_notes": ambiguity_notes,
            "missing_reasons": missing_reasons,
            "collection_requirements": collection_reqs,
            "license_cloud_transfer": "BLOCKED (MSR License §2(e), §3 prohibits cloud upload / third-party transfer of personal data)"
        })

    # Summary
    verified_count = sum(1 for r in audit_results if r["num_valid_videos"] > 0)
    zero_count = sum(1 for r in audit_results if r["num_valid_videos"] == 0)
    print(f"\nAudit complete across 100 classes:")
    print(f"  Valid matched classes: {verified_count}/100")
    print(f"  Zero valid videos: {zero_count}/100")
    
    for r in audit_results:
        if r["num_valid_videos"] == 0:
            print(f"  GAP: [{r['asl_id']}] {r['canonical_name']} -> {r['mapping_status']}: {r['missing_reasons']}")

    out_file = REPO_ROOT / "experiments" / "spoter_v3" / "stage_a_100_class_coverage.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(audit_results, f, indent=2)
    print(f"Saved full coverage JSON to {out_file}")
    return audit_results

if __name__ == "__main__":
    run_deep_audit()
