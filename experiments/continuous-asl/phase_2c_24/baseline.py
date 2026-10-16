import csv
import collections
import json
import math
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
PHASE_DIR = BASE_DIR / "experiments" / "continuous-asl" / "phase_2c_24"
TRAIN_CSV = PHASE_DIR / "train.csv"
VAL_CSV = PHASE_DIR / "val.csv"
TEST_CSV = PHASE_DIR / "test.csv"

def compute_bleu(reference_tokens, candidate_tokens, max_n=4):
    """Simple sentence-level BLEU with brevity penalty."""
    if not candidate_tokens:
        return 0.0
    
    precisions = []
    for n in range(1, max_n + 1):
        ref_ngrams = collections.Counter([tuple(reference_tokens[i:i+n]) for i in range(len(reference_tokens) - n + 1)])
        cand_ngrams = collections.Counter([tuple(candidate_tokens[i:i+n]) for i in range(len(candidate_tokens) - n + 1)])
        
        clipped = sum((cand_ngrams & ref_ngrams).values())
        total = max(1, sum(cand_ngrams.values()))
        precisions.append(clipped / total)
        
    if min(precisions) == 0:
        return 0.0
        
    log_prec = sum(math.log(p) for p in precisions) / max_n
    
    # Brevity penalty
    c = len(candidate_tokens)
    r = len(reference_tokens)
    bp = 1.0 if c > r else math.exp(1 - r / max(1, c))
    
    return bp * math.exp(log_prec)

def run_baseline():
    # 1. Find most frequent sentence in train
    train_sentences = []
    with open(TRAIN_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for r in reader:
            s = r.get("SENTENCE", "").strip()
            if s: train_sentences.append(s)
            
    counter = collections.Counter(train_sentences)
    most_common_sentence, freq = counter.most_common(1)[0]
    print(f"Most Frequent Training Sentence: \"{most_common_sentence}\" (occurred {freq}/{len(train_sentences)} times)")
    
    # 2. Evaluate on Val and Test
    results = {}
    for split_name, path in [("train", TRAIN_CSV), ("val", VAL_CSV), ("test", TEST_CSV)]:
        targets = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for r in reader:
                s = r.get("SENTENCE", "").strip()
                if s: targets.append(s)
                
        exact_matches = sum(1 for t in targets if t.lower() == most_common_sentence.lower())
        exact_match_acc = exact_matches / max(1, len(targets))
        
        # Mean BLEU
        pred_tokens = most_common_sentence.lower().split()
        bleu_scores = [compute_bleu(t.lower().split(), pred_tokens) for t in targets]
        avg_bleu = sum(bleu_scores) / max(1, len(bleu_scores))
        
        results[split_name] = {
            "samples": len(targets),
            "exact_match_acc": exact_match_acc,
            "avg_bleu": avg_bleu,
            "prediction": most_common_sentence
        }
        print(f"Split {split_name:5s} | Samples: {len(targets):2d} | Exact-Match: {exact_match_acc:.4f} | BLEU: {avg_bleu:.4f}")
        
    out_path = PHASE_DIR / "baseline_results.json"
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    run_baseline()
