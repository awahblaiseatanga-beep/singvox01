import json

def run():
    with open(r"d:\Singvox\Singvox\docs\ai-ml\SPOTER_V2_FINAL_TEST_RESULTS.json", "r") as f:
        data = json.load(f)
        
    with open(r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json", "r") as f:
        mapping = json.load(f)
        
    idx_to_class = {int(k): v["canonical_name"] for k, v in mapping.items()}
    
    cm = data["confusion_matrix"]
    per_class_acc = data["per_class_accuracy"]
    class_support = data["class_support"]
    
    # Per-Class Analysis
    classes_info = []
    
    for i in range(79):
        name = idx_to_class.get(i, f"Class {i}")
        support = class_support[i]
        correct = int(cm[i][i])
        incorrect = support - correct
        acc = per_class_acc[i]
        
        # Most common predicted class (excluding the correct class 'i')
        top_confusion_idx = -1
        top_confusion_count = -1
        for j in range(79):
            if i != j and cm[i][j] > top_confusion_count:
                top_confusion_count = cm[i][j]
                top_confusion_idx = j
                
        pct_of_errors = 0.0
        top_c_name = "N/A"
        if incorrect > 0 and top_confusion_idx != -1:
            pct_of_errors = (top_confusion_count / incorrect) * 100
            top_c_name = idx_to_class.get(top_confusion_idx, str(top_confusion_idx))
            
        classes_info.append({
            "idx": i,
            "name": name,
            "support": support,
            "correct": correct,
            "incorrect": incorrect,
            "accuracy": acc,
            "top_confusion_name": top_c_name,
            "top_confusion_count": top_confusion_count,
            "pct_of_errors": pct_of_errors
        })
        
    # Sort: 1. lowest accuracy, 2. highest number of errors, 3. highest support
    classes_info.sort(key=lambda x: (x["accuracy"], -x["incorrect"], -x["support"]))
    
    with open("diagnostic_output.md", "w") as out:
        out.write("### Per-Class Table\n")
        out.write("| Index | Class | Support | Correct | Incorrect | Accuracy | Top Confusion | Confused Count | % Class Errors |\n")
        out.write("|---|---|---|---|---|---|---|---|---|\n")
        for c in classes_info:
            out.write(f"| {c['idx']} | {c['name']} | {c['support']} | {c['correct']} | {c['incorrect']} | {c['accuracy']*100:.2f}% | {c['top_confusion_name']} | {c['top_confusion_count']} | {c['pct_of_errors']:.1f}% |\n")
        
        out.write("\n### Top Confusion Pairs\n")
        out.write("| Actual | Predicted | Samples | % All V2 Errors | % Actual-Class Errors |\n")
        out.write("|---|---|---|---|---|\n")
        total_errors = data["incorrect_predictions"]
        for p in data["top_confusion_pairs"][:20]:
            actual_name = idx_to_class.get(p["true_class"], str(p["true_class"]))
            pred_name = idx_to_class.get(p["pred_class"], str(p["pred_class"]))
            
            actual_idx = p["true_class"]
            incorrect = class_support[actual_idx] - cm[actual_idx][actual_idx]
            pct_all = (p["count"] / total_errors) * 100 if total_errors > 0 else 0.0
            pct_actual = (p["count"] / incorrect) * 100 if incorrect > 0 else 0.0
            
            out.write(f"| {actual_name} | {pred_name} | {p['count']} | {pct_all:.2f}% | {pct_actual:.2f}% |\n")
            
        # Support vs Accuracy
        out.write("\n### Support vs Accuracy\n")
        out.write(f"Total Errors: {total_errors}\n")
        
if __name__ == "__main__":
    run()
