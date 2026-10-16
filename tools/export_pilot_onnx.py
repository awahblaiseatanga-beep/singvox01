"""
SignVox Phase 2 — Export Pilot SPOTER Model to ONNX and Run Parity Test
=======================================================================
Exports spoter_pilot_checkpoint.pt to web/public/spoter_pilot.onnx
and verifies numerical parity with PyTorch on CPU.
"""

import sys
import os
import json
import csv
import torch
import numpy as np

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.append(r"d:\Singvox\Singvox\ai\sign-recognition\models")
from spoter import Spoter
import onnxruntime as ort

PILOT_CKPT = r"d:\Singvox\Singvox\ai\sign-recognition\models\spoter_pilot_checkpoint.pt"
PILOT_MAP  = r"d:\Singvox\Singvox\ai\sign-recognition\data\pilot_class_mapping.json"
ONNX_OUT   = r"d:\Singvox\Singvox\web\public\spoter_pilot.onnx"
BASELINE_ONNX = r"d:\Singvox\Singvox\web\public\spoter_v2_model.onnx"
MANIFEST   = r"d:\Singvox\Singvox\ai\sign-recognition\data\asl100_training_manifest.csv"
FEATURES   = r"d:\Singvox\Singvox\ai\sign-recognition\data\dataset_extracted"

def export_and_verify():
    print("=" * 60)
    print("STAGE 2 — EXPORT SPOTER PILOT MODEL TO ONNX & PARITY TEST")
    print("=" * 60)

    # 1. Baseline Preservation Audit
    assert os.path.exists(BASELINE_ONNX), f"Baseline ONNX missing: {BASELINE_ONNX}"
    baseline_size = os.path.getsize(BASELINE_ONNX)
    print(f"[1] Baseline ONNX asset verified: {BASELINE_ONNX} ({baseline_size / (1024*1024):.2f} MB)")

    # 2. Load PyTorch Pilot Model
    with open(PILOT_MAP, 'r') as f:
        mapping = json.load(f)
    idx_to_label = {v["class_index"]: v["canonical_name"] for v in mapping.values()}

    device = torch.device("cpu")
    model = Spoter(num_classes=3, hidden_dim=512, nhead=8, num_encoder_layers=6, num_decoder_layers=6, dim_feedforward=2048, dropout=0.1).to(device)
    model.load_state_dict(torch.load(PILOT_CKPT, map_location=device, weights_only=True))
    model.eval()

    # Create dummy input for ONNX export
    dummy_input = torch.randn(1, 60, 366, dtype=torch.float32)
    dummy_mask  = torch.ones(1, 60, dtype=torch.bool)

    # Wrap model for simple ONNX export (taking single input tensor)
    class SpoterWrapper(torch.nn.Module):
        def __init__(self, spoter_model):
            super().__init__()
            self.spoter = spoter_model

        def forward(self, inputs):
            # inputs: [batch_size, seq_len, 366]
            batch_size, seq_len, _ = inputs.shape
            mask = torch.ones(batch_size, seq_len, dtype=torch.bool, device=inputs.device)
            return self.spoter(inputs, attention_mask=mask)

    wrapper = SpoterWrapper(model)
    wrapper.eval()

    print(f"[2] Exporting ONNX model to {ONNX_OUT} ...")
    torch.onnx.export(
        wrapper,
        dummy_input,
        ONNX_OUT,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["input_features"],
        output_names=["output_logits"],
        dynamic_axes={
            "input_features": {0: "batch_size", 1: "sequence_length"},
            "output_logits": {0: "batch_size"}
        }
    )

    onnx_size_mb = os.path.getsize(ONNX_OUT) / (1024 * 1024)
    print(f"    -> Export successful! ONNX size: {onnx_size_mb:.2f} MB")

    # 3. Numerical Parity Verification
    print("\n[3] Running PyTorch vs ONNX Runtime Numerical Parity Test ...")
    ort_session = ort.InferenceSession(ONNX_OUT, providers=["CPUExecutionProvider"])
    
    # Collect 10 sample feature files
    test_files = []
    with open(MANIFEST, 'r') as f:
        for row in csv.DictReader(f):
            if row['canonical_name'] in idx_to_label.values():
                base = os.path.splitext(row['video_file'])[0]
                fpath = os.path.join(FEATURES, f"{base}_features.npy")
                if os.path.exists(fpath):
                    test_files.append((row['canonical_name'], fpath))
                if len(test_files) >= 10:
                    break

    max_diff = 0.0
    matched_predictions = 0

    for expected_label, fpath in test_files:
        feat = np.load(fpath) # shape [seq_len, 366]
        input_tensor = torch.tensor(feat, dtype=torch.float32).unsqueeze(0) # [1, seq_len, 366]

        # PyTorch forward
        with torch.no_grad():
            pt_logits = wrapper(input_tensor).numpy()[0] # [3]

        # ONNX Runtime forward
        ort_inputs = {"input_features": feat.astype(np.float32)[np.newaxis, :]}
        ort_logits = ort_session.run(None, ort_inputs)[0][0] # [3]

        diff = np.max(np.abs(pt_logits - ort_logits))
        max_diff = max(max_diff, diff)

        pt_pred = idx_to_label[int(np.argmax(pt_logits))]
        ort_pred = idx_to_label[int(np.argmax(ort_logits))]
        
        assert pt_pred == ort_pred, f"Prediction mismatch! PyTorch: {pt_pred}, ONNX: {ort_pred}"
        matched_predictions += 1

        print(f"  Sample {os.path.basename(fpath):35s} | Expected: {expected_label:5s} | PT: {pt_pred:5s} | ONNX: {ort_pred:5s} | Max Logit Diff: {diff:.6e}")

    print(f"\n[4] Parity Test Results:")
    print(f"    - Matched Predictions: {matched_predictions}/{len(test_files)} (100%)")
    print(f"    - Maximum Absolute Logit Difference: {max_diff:.6e}")
    assert max_diff < 1e-4, f"Numerical difference exceeds tolerance! {max_diff} >= 1e-4"
    print("    -> Numerical Parity Check PASSED (tolerance < 1e-4)!")

    # Re-check baseline preservation
    assert os.path.getsize(BASELINE_ONNX) == baseline_size, "CRITICAL ERROR: Baseline ONNX was modified!"
    print(f"    -> Baseline ONNX preserved untouched ({baseline_size / (1024*1024):.2f} MB).")

    print("\n" + "=" * 60)
    print("STAGE 2 ONNX EXPORT & PARITY TEST PASSED 100%")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = export_and_verify()
    sys.exit(0 if success else 1)
