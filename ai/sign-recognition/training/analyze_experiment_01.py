import os, json, csv, sys, torch, warnings
import numpy as np
from collections import defaultdict

warnings.filterwarnings("ignore")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")
from spoter import Spoter
from dataloaders import get_dataloaders
from run_experiment_01_groupnorm import apply_scaling

def get_masks(seqs):
    m = {}
    m["FULL"] = seqs.clone()
    
    m_h = seqs.clone()
    m_h[:, :, 126:] = 0.0
    m["HANDS_ONLY"] = m_h
    
    m_p = seqs.clone()
    m_p[:, :, :126] = 0.0
    m_p[:, :, 291:] = 0.0
    m["POSE_ONLY"] = m_p
    
    m_f = seqs.clone()
    m_f[:, :, :291] = 0.0
    m["FACE_ONLY"] = m_f
    
    m_hp = seqs.clone()
    m_hp[:, :, 291:] = 0.0
    m["HANDS_POSE"] = m_hp
    
    m_hf = seqs.clone()
    m_hf[:, :, 126:291] = 0.0
    m["HANDS_FACE"] = m_hf
    
    m_pf = seqs.clone()
    m_pf[:, :, :126] = 0.0
    m["POSE_FACE"] = m_pf
    
    return m

def cos_sim(v1, v2):
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 == 0 or n2 == 0: return 0.0
    return np.dot(v1, v2) / (n1 * n2)

def run():
    ckpt_path = r"d:\Singvox\Singvox\ai\sign-recognition\models\spoter_groupnorm_best_val_acc_checkpoint.pt"
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    scalar_path = r"d:\Singvox\Singvox\ai\sign-recognition\models\spoter_groupnorm_scalars.json"
    
    with open(scalar_path, 'r') as f: scalars = json.load(f)
    with open(mapping_path, 'r', encoding='utf-8') as f: mapping_dict = json.load(f)
    idx_to_name = {v['class_index']: v['canonical_name'].upper() for v in mapping_dict.values()}
    name_to_idx = {v['canonical_name'].upper(): v['class_index'] for v in mapping_dict.values()}
    
    # We strictly use the train/val dataloaders. Banning test loader.
    train_loader, val_loader, _ = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    
    device = torch.device("cpu")
    model = Spoter(num_classes=79)
    model.load_state_dict(torch.load(ckpt_path, map_location=device, weights_only=True))
    model.eval()

    intermediates = {}
    def get_act(name):
        def hook(model, input, output): intermediates[name] = output.detach()
        return hook
    model.input_proj.register_forward_hook(get_act('proj'))
    model.transformer_encoder.register_forward_hook(get_act('enc'))
    model.transformer_decoder.register_forward_hook(get_act('dec'))
    
    confusion_pairs = [
        ("NEED", "YES"),
        ("HELLO", "FATHER"),
        ("HOT", "BAD"),
        ("PLEASE", "HAPPY"),
        ("NAME", "FRIEND"),
        ("GIVE", "GOOD"),
        ("LIKE", "PLEASE"),
        ("SIGN", "WHEN"),
        ("NO", "YES"),
        ("SORRY", "ME")
    ]
    
    target_classes = set()
    for p1, p2 in confusion_pairs:
        target_classes.add(name_to_idx[p1])
        target_classes.add(name_to_idx[p2])
    
    rep_names = ["FULL", "HANDS_ONLY", "HANDS_POSE", "HANDS_FACE"]
    out_results = {}
    
    for rep in rep_names:
        class_features = {"366": defaultdict(list), "enc": defaultdict(list), "dec": defaultdict(list)}
        
        with torch.no_grad():
            for batch in val_loader:
                seqs = apply_scaling(batch["padded_sequences"], scalars).to(device)
                mask = batch["attention_mask"].to(device)
                labels = batch["class_indices"].numpy()
                lengths = batch["original_lengths"].to(device)
                
                masked_seqs = get_masks(seqs)[rep]
                model(masked_seqs, attention_mask=mask)
                
                for i in range(seqs.size(0)):
                    l = lengths[i].item()
                    c = labels[i]
                    if c in target_classes:
                        f_366 = masked_seqs[i, :l, :].mean(dim=0).numpy()
                        f_enc = intermediates['enc'][i][:l, :].mean(dim=0).numpy() if intermediates['enc'][i].dim()==2 else np.zeros(512)
                        f_dec = intermediates['dec'][i][0].numpy() if intermediates['dec'][i].dim()==2 else np.zeros(512)
                        
                        class_features["366"][c].append(f_366)
                        class_features["enc"][c].append(f_enc)
                        class_features["dec"][c].append(f_dec)
                        
        # compute centroids
        centroids = {"366": {}, "enc": {}, "dec": {}}
        for layer in class_features:
            for c in class_features[layer]:
                if len(class_features[layer][c]) > 0:
                    centroids[layer][c] = np.mean(class_features[layer][c], axis=0)
                    
        # calculate pair separation = 1 - cosine_similarity(centroid_A, centroid_B)
        pair_seps = []
        for p1, p2 in confusion_pairs:
            idx1, idx2 = name_to_idx.get(p1), name_to_idx.get(p2)
            if idx1 in centroids["dec"] and idx2 in centroids["dec"]:
                sep_366 = 1.0 - cos_sim(centroids["366"][idx1], centroids["366"][idx2])
                sep_enc = 1.0 - cos_sim(centroids["enc"][idx1], centroids["enc"][idx2])
                sep_dec = 1.0 - cos_sim(centroids["dec"][idx1], centroids["dec"][idx2])
                pair_seps.append({
                    "pair": f"{p1}-{p2}",
                    "sep_366": float(sep_366),
                    "sep_enc": float(sep_enc),
                    "sep_dec": float(sep_dec)
                })
        
        rep_avg_dec = float(np.mean([p["sep_dec"] for p in pair_seps])) if len(pair_seps) > 0 else 0.0
        rep_avg_366 = float(np.mean([p["sep_366"] for p in pair_seps])) if len(pair_seps) > 0 else 0.0
        out_results[rep] = {
            "avg_sep_366": rep_avg_366, 
            "avg_sep_dec": rep_avg_dec,
            "pairs": pair_seps
        }
    
    with open(r"d:\Singvox\Singvox\docs\ai-ml\EXPERIMENT_01_REPRESENTATION_SEPARATION.json", "w") as f:
        json.dump(out_results, f, indent=2)
    
    print("SPOTER EXPERIMENT 01 SEPARATION ANALYSIS — COMPLETE")

if __name__ == "__main__":
    run()
