import json
import math

def pearson_r(x, y):
    n = len(x)
    sum_x = sum(x)
    sum_y = sum(y)
    sum_x_sq = sum(v * v for v in x)
    sum_y_sq = sum(v * v for v in y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    
    num = (n * sum_xy) - (sum_x * sum_y)
    den = math.sqrt((n * sum_x_sq - sum_x**2) * (n * sum_y_sq - sum_y**2))
    return num / den if den != 0 else 0.0

def spearman_rho(x, y):
    def tied_rank(x):
        sorted_x = sorted((v, i) for i, v in enumerate(x))
        ranks = [0] * len(x)
        i = 0
        while i < len(sorted_x):
            j = i
            while j < len(sorted_x) and sorted_x[j][0] == sorted_x[i][0]:
                j += 1
            avg_rank = sum(range(i + 1, j + 1)) / (j - i)
            for k in range(i, j):
                ranks[sorted_x[k][1]] = avg_rank
            i = j
        return ranks
    rank_x = tied_rank(x)
    rank_y = tied_rank(y)
    return pearson_r(rank_x, rank_y)

def run():
    with open(r"d:\Singvox\Singvox\docs\ai-ml\SPOTER_V2_FINAL_TEST_RESULTS.json", "r") as f:
        data = json.load(f)
        
    per_class_acc = data["per_class_accuracy"]
    class_support = data["class_support"]
    
    # 1. Correlations
    r = pearson_r(class_support, per_class_acc)
    rho = spearman_rho(class_support, per_class_acc)
    
    # 2. Concentrations
    # Top confusion pairs
    pairs = data["top_confusion_pairs"]
    top_5_pairs = pairs[:5]
    top_10_pairs = pairs[:10]
    
    top_5_errs = sum(p["count"] for p in top_5_pairs)
    top_10_errs = sum(p["count"] for p in top_10_pairs)
    
    total_incorrect = data["incorrect_predictions"]
    
    # Weakest classes
    # We need to sort by incorrect, then maybe negative accuracy
    incorrect_per_class = [class_support[i] - data["confusion_matrix"][i][i] for i in range(79)]
    cls_stats = [{"idx": i, "incorrect": incorrect_per_class[i], "support": class_support[i], "acc": per_class_acc[i]} for i in range(79)]
    
    cls_stats_by_incorrect = sorted(cls_stats, key=lambda x: (x["acc"], -x["incorrect"]))
    
    top_5_weakest = cls_stats_by_incorrect[:5]
    top_10_weakest = cls_stats_by_incorrect[:10]
    
    top_5_weakest_errs = sum(c["incorrect"] for c in top_5_weakest)
    top_10_weakest_errs = sum(c["incorrect"] for c in top_10_weakest)
    
    print(f"Pearson r: {r:.4f}")
    print(f"Spearman rho: {rho:.4f}")
    print(f"Top 5 pairs errors: {top_5_errs} ({top_5_errs/total_incorrect*100:.2f}%)")
    print(f"Top 10 pairs errors: {top_10_errs} ({top_10_errs/total_incorrect*100:.2f}%)")
    print(f"Top 5 weakest classes errors: {top_5_weakest_errs} ({top_5_weakest_errs/total_incorrect*100:.2f}%)")
    print(f"Top 10 weakest classes errors: {top_10_weakest_errs} ({top_10_weakest_errs/total_incorrect*100:.2f}%)")

if __name__ == "__main__":
    run()
