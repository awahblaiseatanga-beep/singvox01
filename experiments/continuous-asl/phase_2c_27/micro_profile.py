import time
import torch
import torch.nn as nn
import torch.nn.functional as F

B = 16
H = 128
A = 64
V = 1000

for T in [300, 150, 75]:
    dec_hidden = torch.randn(B, H)
    enc_outputs = torch.randn(B, T, H)
    enc_proj = torch.randn(B, T, A)
    w_dec = nn.Linear(H, A, bias=False)
    v = nn.Linear(A, 1, bias=False)
    gru_cell = nn.GRUCell(64 + H, H)
    fc_out = nn.Linear(H + 64 + H, V)
    embed = torch.randn(B, 64)
    inv_mask = torch.zeros(B, T, dtype=torch.bool)

    t0 = time.time()
    for _ in range(25):
        dec_proj = w_dec(dec_hidden).unsqueeze(1)
        energy = v(torch.tanh(dec_proj + enc_proj)).squeeze(2)
        energy = energy.masked_fill(inv_mask, -1e9)
        attn_weights = F.softmax(energy, dim=1)
        context = torch.bmm(attn_weights.unsqueeze(1), enc_outputs).squeeze(1)
        gru_in = torch.cat([embed, context], dim=1)
        dec_hidden = gru_cell(gru_in, dec_hidden)
        out_cat = torch.cat([dec_hidden, embed, context], dim=1)
        logits = fc_out(out_cat)
    t1 = time.time()
    print(f"T={T}: 25 steps took {t1 - t0:.3f}s (avg {(t1 - t0)/25*1000:.1f}ms per step)")
