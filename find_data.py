import re
with open(r'd:\Singvox\Singvox\ai\sign-recognition\checkpoints\spoter_v2_model.onnx', 'rb') as f:
    data = f.read()
    match = re.search(b'([a-zA-Z0-9_\-\./\\\\]+\.data)', data)
    if match:
        print("FOUND:", match.group(0).decode('utf-8'))
    else:
        print("NOT FOUND")
