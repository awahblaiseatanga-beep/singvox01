import sys
import os
import torch
import onnx
import onnxruntime as ort
import numpy as np
import hashlib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models')))
from spoter import Spoter

def main():
    print("--- SPOTER V2 ONNX EXPORT AND NUMERICAL VALIDATION ---")
    
    # Configuration
    model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'checkpoints', 'spoter_v2_groupnorm_best_val_acc.pt'))
    onnx_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'checkpoints', 'spoter_v2_model.onnx'))
    seq_len = 60
    input_dim = 366
    num_classes = 79
    hidden_dim = 512
    nhead = 8
    num_encoder_layers = 6
    num_decoder_layers = 6
    dim_feedforward = 2048
    dropout = 0.1
    opset_version = 17

    # 1. Instantiate exact canonical SPOTER V2 architecture
    model = Spoter(
        num_classes=num_classes,
        hidden_dim=hidden_dim, 
        nhead=nhead, 
        num_encoder_layers=num_encoder_layers, 
        num_decoder_layers=num_decoder_layers, 
        dim_feedforward=dim_feedforward, 
        dropout=dropout
    )
    
    # 2. Load frozen checkpoint
    assert os.path.exists(model_path), f"Checkpoint missing: {model_path}"
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    
    # 3 & 4. Eval and no_grad
    model.eval()

    # Generate deterministic synthetic fixture
    torch.manual_seed(42)
    np.random.seed(42)
    dummy_input = torch.randn(1, seq_len, input_dim, dtype=torch.float32)

    # 5. Export to ONNX
    print("Exporting ONNX...")
    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        export_params=True,
        opset_version=opset_version,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes=None  # Fixed to 1,60,366
    )

    # Validate ONNX model
    onnx_model = onnx.load(onnx_path)
    onnx.checker.check_model(onnx_model)
    print("ONNX model checker passed.")

    # Generate stats
    file_size_mb = os.path.getsize(onnx_path) / (1024 * 1024)
    with open(onnx_path, "rb") as f:
        sha256_hash = hashlib.sha256(f.read()).hexdigest()

    # Numerical Equivalence
    with torch.no_grad():
        pytorch_output = model(dummy_input).numpy()

    ort_session = ort.InferenceSession(onnx_path, providers=['CPUExecutionProvider'])
    ort_inputs = {ort_session.get_inputs()[0].name: dummy_input.numpy()}
    onnx_output = ort_session.run(None, ort_inputs)[0]

    max_abs_diff = np.max(np.abs(pytorch_output - onnx_output))
    mean_abs_diff = np.mean(np.abs(pytorch_output - onnx_output))
    
    # Safe relative difference handling near zero
    zero_mask = np.abs(pytorch_output) < 1e-6
    rel_diff = np.abs(pytorch_output - onnx_output) / (np.abs(pytorch_output) + 1e-8)
    max_rel_diff = np.max(rel_diff[~zero_mask]) if not np.all(zero_mask) else 0.0

    pt_top5_idx = np.argsort(pytorch_output[0])[-5:][::-1]
    onnx_top5_idx = np.argsort(onnx_output[0])[-5:][::-1]
    
    pt_argmax = pt_top5_idx[0]
    onnx_argmax = onnx_top5_idx[0]
    
    top5_match = np.array_equal(pt_top5_idx, onnx_top5_idx)

    # 6-10. Record metrics
    print("\n--- PHASE 2 EXPORT REPORT ---")
    print(f"ONNX Opset Version: {opset_version}")
    print(f"Input Shape: [1, {seq_len}, {input_dim}]")
    print(f"Output Shape: [1, {num_classes}]")
    print(f"ONNX File Size: {file_size_mb:.2f} MB")
    print(f"ONNX SHA-256: {sha256_hash}")
    print("\n--- NUMERICAL EQUIVALENCE ---")
    print(f"Max Absolute Diff: {max_abs_diff:.6e}")
    print(f"Mean Absolute Diff: {mean_abs_diff:.6e}")
    print(f"Max Relative Diff: {max_rel_diff:.6e}")
    print(f"PyTorch Argmax Class: {pt_argmax}")
    print(f"ONNX Argmax Class: {onnx_argmax}")
    print(f"Top-5 Classes Match: {top5_match}")
    print(f"Top-5 PyTorch: {pt_top5_idx}")
    print(f"Top-5 ONNX: {onnx_top5_idx}")

if __name__ == '__main__':
    main()
