import time
import torch
import sys
sys.path.append(r"experiments/continuous-asl/phase_2c_27")
from model import AttentionSeq2Seq

print("Initializing model...")
model = AttentionSeq2Seq(1000, in_features=366, hidden_dim=256)
src = torch.randn(4, 150, 366)
src_mask = torch.ones(4, 150, dtype=torch.bool)
tgt = torch.randint(0, 1000, (4, 25))

t0 = time.time()
logits = model(src, src_mask, tgt)
print(f"Forward time: {time.time() - t0:.3f}s")

t0 = time.time()
loss = logits.sum()
loss.backward()
print(f"Backward time: {time.time() - t0:.3f}s")
print("Done test_speed successfully!")
