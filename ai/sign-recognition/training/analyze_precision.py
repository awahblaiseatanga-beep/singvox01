import os, json, csv, sys, torch, warnings
import numpy as np
from collections import defaultdict

warnings.filterwarnings("ignore")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\training")
from spoter import Spoter
from dataloaders import get_dataloaders

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
    
    rep_names = ["FULL", "HANDS_ONLY", "POSE_ONLY", "FACE_ONLY", "HANDS_POSE", "HANDS_FACE", "POSE_FACE"]
    
    # Store aggregated magnitude stats
    stats = {"hands": {"l2": [], "var": [], "zeros": []},
             "pose":  {"l2": [], "var": [], "zeros": []},
             "face":  {"l2": [], "var": [], "zeros": []}}

    out_lines = []
    for rep in rep_names:
        extracted = {}
        with torch.no_grad():
            for batch in test_loader:
                seqs = batch["padded_sequences"].to(device)
                mask = batch["attention_mask"].to(device)
                vids = batch["asl_ids"]
                lengths = batch["original_lengths"].to(device)
                
                # if rep is FULL, collect stats for magnitude exactly once per video.
                if rep == "FULL":
                    for i in range(seqs.size(0)):
                        vid = vids[i]
                        if vid in all_vids:
                            l = lengths[i].item()
                            s_h = seqs[i, :l, :126].numpy()
                            s_p = seqs[i, :l, 126:291].numpy()
                            s_f = seqs[i, :l, 291:].numpy()
                            
                            stats["hands"]["l2"].append(np.linalg.norm(s_h))
                            stats["hands"]["var"].append(np.var(s_h))
                            stats["hands"]["zeros"].append(np.sum(s_h == 0.0) / s_h.size)
                            
                            stats["pose"]["l2"].append(np.linalg.norm(s_p))
                            stats["pose"]["var"].append(np.var(s_p))
                            stats["pose"]["zeros"].append(np.sum(s_p == 0.0) / s_p.size)
                            
                            stats["face"]["l2"].append(np.linalg.norm(s_f))
                            stats["face"]["var"].append(np.var(s_f))
                            stats["face"]["zeros"].append(np.sum(s_f == 0.0) / s_f.size)

                masked_seqs = get_masks(seqs)[rep]
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
                if len(class_centroids[layer][t]) > 0:
                    class_centroids[layer][t] = np.mean(class_centroids[layer][t], axis=0)
                
        gap_366, gap_enc, gap_dec = [], [], []
        for e in err_cases:
            v = e["video_file"]
            if v not in extracted: continue
            t, p = int(e["true_class"]), int(e["pred_class"])
            f = extracted[v]
            
            c_t_366 = class_centroids["366"].get(t, f["366"])
            c_p_366 = class_centroids["366"].get(p, f["366"])
            c_t_enc = class_centroids["enc"].get(t, f["enc"])
            c_p_enc = class_centroids["enc"].get(p, f["enc"])
            c_t_dec = class_centroids["dec"].get(t, f["dec"])
            c_p_dec = class_centroids["dec"].get(p, f["dec"])
            
            gap_366.append(cos_sim(f["366"], c_t_366) - cos_sim(f["366"], c_p_366))
            gap_enc.append(cos_sim(f["enc"], c_t_enc) - cos_sim(f["enc"], c_p_enc))
            gap_dec.append(cos_sim(f["dec"], c_t_dec) - cos_sim(f["dec"], c_p_dec))
        
        out_lines.append(f"[{rep}] Gap 366: {np.mean(gap_366):.4f} | Gap Enc: {np.mean(gap_enc):.4f} | Gap Dec: {np.mean(gap_dec):.4f}")
    
    print("--- GAP METRICS ---")
    for line in out_lines:
        print(line)
        
    print("\n--- MAGNITUDE / VARIANCE STATS (Over evaluated samples) ---")
    for grp in ["hands", "pose", "face"]:
        m_l2 = np.mean(stats[grp]["l2"])
        m_var = np.mean(stats[grp]["var"])
        m_zer = np.mean(stats[grp]["zeros"])
        print(f"[{grp.upper()}] L2 Norm: {m_l2:.4f} | Variance: {m_var:.4f} | Zeros: {m_zer:.1%}")

if __name__ == "__main__":
    run()
