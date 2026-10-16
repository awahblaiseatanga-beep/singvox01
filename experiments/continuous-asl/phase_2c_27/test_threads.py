import time
import torch
import torch.nn as nn

print(f"Default PyTorch num threads: {torch.get_num_threads()}", flush=True)

x = torch.randn(16, 150, 128)

for threads in [1, 2, 4, 8, torch.get_num_threads()]:
    torch.set_num_threads(threads)
    gru = nn.GRU(128, 64, num_layers=1, batch_first=True, bidirectional=True)
    # Warmup
    _ = gru(x)
    t0 = time.time()
    for _ in range(5):
        _ = gru(x)
    t1 = time.time()
    print(f"Threads={threads}: 5 forward runs took {t1 - t0:.4f}s (avg {(t1 - t0)/5*1000:.1f}ms per run)", flush=True)
