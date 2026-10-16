import torch
import torch.nn as nn
import torch.nn.functional as F

class BahdanauAttention(nn.Module):
    def __init__(self, enc_dim=128, dec_dim=128, attn_dim=64):
        super().__init__()
        self.w_enc = nn.Linear(enc_dim, attn_dim, bias=False)
        self.w_dec = nn.Linear(dec_dim, attn_dim, bias=False)
        self.v = nn.Linear(attn_dim, 1, bias=False)

    def forward(self, dec_hidden, enc_outputs, enc_proj, inv_mask=None):
        dec_proj = self.w_dec(dec_hidden).unsqueeze(1) # [B, 1, attn_dim]
        energy = self.v(torch.tanh(dec_proj + enc_proj)).squeeze(2) # [B, T_src]
        
        if inv_mask is not None:
            energy = energy.masked_fill(inv_mask, -1e9)
            
        attn_weights = F.softmax(energy, dim=1) # [B, T_src]
        context = torch.bmm(attn_weights.unsqueeze(1), enc_outputs).squeeze(1) # [B, enc_dim]
        return context, attn_weights

class LandmarkEncoder(nn.Module):
    def __init__(self, in_features=366, hidden_dim=128, num_layers=1, dropout=0.2):
        super().__init__()
        self.input_proj = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout)
        )
        self.gru = nn.GRU(
            hidden_dim,
            hidden_dim // 2,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True
        )
        self.fc_hidden = nn.Linear(hidden_dim, hidden_dim)

    def forward(self, src, src_lens=None):
        proj = self.input_proj(src)
        if src_lens is not None:
            packed = nn.utils.rnn.pack_padded_sequence(
                proj, src_lens.cpu(), batch_first=True, enforce_sorted=False
            )
            packed_outputs, hidden = self.gru(packed)
            enc_outputs, _ = nn.utils.rnn.pad_packed_sequence(packed_outputs, batch_first=True)
        else:
            enc_outputs, hidden = self.gru(proj)
            
        # hidden: [2, B, hidden_dim // 2]
        forward_final = hidden[-2, :, :]
        backward_final = hidden[-1, :, :]
        cat_hidden = torch.cat([forward_final, backward_final], dim=1)
        init_dec_hidden = torch.tanh(self.fc_hidden(cat_hidden))
        return enc_outputs, init_dec_hidden

class AttentionDecoder(nn.Module):
    def __init__(self, vocab_size, embed_dim=64, enc_dim=128, dec_dim=128, attn_dim=64, pad_id=0, dropout=0.2):
        super().__init__()
        self.vocab_size = vocab_size
        self.pad_id = pad_id
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_id)
        self.attention = BahdanauAttention(enc_dim, dec_dim, attn_dim)
        self.gru_cell = nn.GRUCell(embed_dim + enc_dim, dec_dim)
        self.dropout = nn.Dropout(dropout)
        self.fc_out = nn.Linear(dec_dim + embed_dim + enc_dim, vocab_size)

    def step(self, token_idx, dec_hidden, enc_outputs, enc_proj, inv_mask=None):
        embed = self.dropout(self.embedding(token_idx))
        context, attn_weights = self.attention(dec_hidden, enc_outputs, enc_proj, inv_mask)
        gru_input = torch.cat([embed, context], dim=1)
        next_hidden = self.gru_cell(gru_input, dec_hidden)
        out_cat = torch.cat([next_hidden, embed, context], dim=1)
        logits = self.fc_out(out_cat)
        return logits, next_hidden, attn_weights

class AttentionSeq2Seq(nn.Module):
    def __init__(self, vocab_size, in_features=366, hidden_dim=128, embed_dim=64, attn_dim=64, pad_id=0, sos_id=1, eos_id=2, dropout=0.2):
        super().__init__()
        self.vocab_size = vocab_size
        self.pad_id = pad_id
        self.sos_id = sos_id
        self.eos_id = eos_id
        
        self.encoder = LandmarkEncoder(
            in_features=in_features,
            hidden_dim=hidden_dim,
            num_layers=1,
            dropout=dropout
        )
        self.decoder = AttentionDecoder(
            vocab_size=vocab_size,
            embed_dim=embed_dim,
            enc_dim=hidden_dim,
            dec_dim=hidden_dim,
            attn_dim=attn_dim,
            pad_id=pad_id,
            dropout=dropout
        )

    def forward(self, src, src_mask, tgt, teacher_forcing_ratio=0.5):
        batch_size = src.size(0)
        tgt_len = tgt.size(1)
        
        enc_outputs, dec_hidden = self.encoder(src)
        enc_proj = self.decoder.attention.w_enc(enc_outputs)
        inv_mask = ~src_mask if src_mask is not None else None
        
        output_logits = []
        input_tok = tgt[:, 0]
        
        for t in range(1, tgt_len):
            logits, dec_hidden, _ = self.decoder.step(input_tok, dec_hidden, enc_outputs, enc_proj, inv_mask)
            output_logits.append(logits.unsqueeze(1))
            
            teacher_force = (torch.rand(1).item() < teacher_forcing_ratio) if self.training else False
            if teacher_force:
                input_tok = tgt[:, t]
            else:
                input_tok = logits.argmax(1)
            
        return torch.cat(output_logits, dim=1)

    @torch.no_grad()
    def generate(self, src, src_mask, max_len=50):
        batch_size = src.size(0)
        enc_outputs, dec_hidden = self.encoder(src)
        enc_proj = self.decoder.attention.w_enc(enc_outputs)
        inv_mask = ~src_mask if src_mask is not None else None
        
        curr_tok = torch.full((batch_size,), self.sos_id, dtype=torch.long, device=src.device)
        generated_tokens = []
        
        for _ in range(max_len):
            logits, dec_hidden, _ = self.decoder.step(curr_tok, dec_hidden, enc_outputs, enc_proj, inv_mask)
            top1 = logits.argmax(1)
            generated_tokens.append(top1.unsqueeze(1))
            curr_tok = top1
            
        return torch.cat(generated_tokens, dim=1)
