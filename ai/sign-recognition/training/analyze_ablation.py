import os, json, csv, sys, torch, warnings
import numpy as np
from collections import defaultdict

warnings.filterwarnings("ignore")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")
from spoter import Spoter
from dataloaders import get_dataloaders

def get_ablation_mask(rep_type, seqs):
    masked = seqs.clone()
    if rep_type == "B_Hands_Only":
        masked[:, :, 126:] = 0.0
    elif rep_type == "C_Hands_Pose":
        masked[:, :, 291:] = 0.0
    elif rep_type == "D_Hands_Face":
        masked[:, :, 126:291] = 0.0
    # E is Full (A). F is un-normalized (skipped/impossible).
    return masked

def cos_sim(v1, v2):
    if np.linalg.norm(v1) == 0 or np.linalg.norm(v2) == 0: return 0.0
    return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))

def run_ablation():
    ckpt_path = r"d:\Singvox\Singvox\ai\sign-recognition\models\spoter_baseline_best_val_acc_checkpoint.pt"
    manifest_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
    features_dir = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"
    mapping_path = r"d:\Singvox\Singvox\ai\sign-recognition\data\class_index_mapping.json"
    err_cases_path = r"d:\Singvox\Singvox\ai\sign-recognition\evaluation\targeted_error_audit\selected_error_cases.csv"
    ctrl_cases_path = r"d:\Singvox\Singvox\ai\sign-recognition\evaluation\targeted_error_audit\selected_control_cases.csv"
    
    with open(mapping_path, 'r', encoding='utf-8') as f: mapping_dict = json.load(f)
    idx_to_name = {v['class_index']: v['canonical_name'].upper() for v in mapping_dict.values()}
    
    err_cases = list(csv.DictReader(open(err_cases_path, "r", encoding="utf-8")))
    ctrl_cases = list(csv.DictReader(open(ctrl_cases_path, "r", encoding="utf-8")))
    all_vids = {x["video_file"] for x in err_cases + ctrl_cases}

    _, _, test_loader = get_dataloaders(manifest_path, features_dir, mapping_path, batch_size=32)
    device = torch.device("cpu")
    model = Spoter(num_classes=79)
    model.load_state_dict(torch.load(ckpt_path, map_location=device, weights_only=True))
    model.eval()

    intermediates = {}
    def get_act(name):
        def hook(model, input, output): intermediates[name] = output.detach()
        return hook
    model.input_proj.register_forward_hook(get_act('input_proj'))
    model.transformer_encoder.register_forward_hook(get_act('encoder'))
    model.transformer_decoder.register_forward_hook(get_act('decoder'))
    
    reps = ["A_Full", "B_Hands_Only", "C_Hands_Pose", "D_Hands_Face"]
    out_lines = []
    
    for rep in reps:
        extracted = {}
        with torch.no_grad():
            for batch in test_loader:
                seqs = batch["padded_sequences"].to(device)
                mask = batch["attention_mask"].to(device)
                vids = batch["asl_ids"]
                lengths = batch["original_lengths"].to(device)
                
                masked_seqs = get_ablation_mask(rep, seqs)
                model(masked_seqs, attention_mask=mask)
                
                for i in range(seqs.size(0)):
                    vid = vids[i]
                    if vid in all_vids:
                        l = lengths[i].item()
                        f_366 = masked_seqs[i, :l, :].mean(dim=0).numpy()
                        f_proj = intermediates['input_proj'][i][:l, :].mean(dim=0).numpy() if intermediates['input_proj'][i].dim()==2 else np.zeros(512)
                        f_enc = intermediates['encoder'][i][:l, :].mean(dim=0).numpy() if intermediates['encoder'][i].dim()==2 else np.zeros(512)
                        f_dec = intermediates['decoder'][i][0].numpy() if intermediates['decoder'][i].dim()==2 else np.zeros(512)
                        extracted[vid] = {"366": f_366, "proj": f_proj, "enc": f_enc, "dec": f_dec}
                        
        class_centroids = {"366": defaultdict(list), "enc": defaultdict(list), "dec": defaultdict(list)}
        for c in ctrl_cases:
            v = c["video_file"]
            if v in extracted:
                t = int(c["true_class"])
                class_centroids["366"][t].append(extracted[v]["366"])
                class_centroids["enc"][t].append(extracted[v]["enc"])
                class_centroids["dec"][t].append(extracted[v]["dec"])
        for layer in class_centroids:
            for t in class_centroids[layer]:
                class_centroids[layer][t] = np.mean(class_centroids[layer][t], axis=0)
                
        gap_366, gap_enc, gap_dec = [], [], []
        for e in err_cases:
            v = e["video_file"]
            if v not in extracted: continue
            t, p = int(e["true_class"]), int(e["pred_class"])
            f = extracted[v]
            gap_366.append(cos_sim(f["366"], class_centroids["366"].get(t, f["366"])) - cos_sim(f["366"], class_centroids["366"].get(p, f["366"])))
            gap_enc.append(cos_sim(f["enc"], class_centroids["enc"].get(t, f["enc"])) - cos_sim(f["enc"], class_centroids["enc"].get(p, f["enc"])))
            gap_dec.append(cos_sim(f["dec"], class_centroids["dec"].get(t, f["dec"])) - cos_sim(f["dec"], class_centroids["dec"].get(p, f["dec"])))
        
        out_lines.append(f"[{rep}] Gap 366: {np.mean(gap_366):.4f} | Gap Enc: {np.mean(gap_enc):.4f} | Gap Dec: {np.mean(gap_dec):.4f}")
    
    for line in out_lines:
        print(line)

if __name__ == "__main__":
    run_ablation()
