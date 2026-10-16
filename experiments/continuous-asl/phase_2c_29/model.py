import math
import torch
import torch.nn as nn
import torch.nn.functional as F

class LandmarkEncoder(nn.Module):
    def __init__(self, in_features=366, hidden_dim=256, num_layers=2, dropout=0.2):
        super().__init__()
        self.input_proj = nn.Sequential(
            nn.Linear(in_features, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.Dropout(dropout)
        )
        self.rnn = nn.GRU(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            bidirectional=True,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0
        )
        self.fc_bridge = nn.Linear(hidden_dim * 2, hidden_dim)
        self.layer_norm = nn.LayerNorm(hidden_dim)

    def forward(self, src, src_mask, src_lens=None):
        """
        src: [B, T, 366]
        src_mask: [B, T] (True for valid, False for pad)
        """
        x = self.input_proj(src)
        
        if src_lens is not None:
            packed_x = nn.utils.rnn.pack_padded_sequence(
                x, src_lens.cpu(), batch_first=True, enforce_sorted=False
            )
            packed_out, _ = self.rnn(packed_x)
            out, _ = nn.utils.rnn.pad_packed_sequence(packed_out, batch_first=True, total_length=src.size(1))
        else:
            out, _ = self.rnn(x)

        # Bridge bidirectional outputs to hidden_dim
        enc_out = self.layer_norm(self.fc_bridge(out))
        return enc_out

class BahdanauAttention(nn.Module):
    def __init__(self, enc_dim=256, dec_dim=256, attn_dim=128):
        super().__init__()
        self.w_enc = nn.Linear(enc_dim, attn_dim, bias=False)
        self.w_dec = nn.Linear(dec_dim, attn_dim, bias=False)
        self.v = nn.Linear(attn_dim, 1, bias=False)

    def forward(self, dec_state, enc_out, precomputed_enc, inv_mask):
        """
        dec_state: [B, dec_dim]
        enc_out: [B, T, enc_dim]
        precomputed_enc: [B, T, attn_dim]
        inv_mask: [B, T] (True where padded / invalid)
        """
        dec_proj = self.w_dec(dec_state).unsqueeze(1) # [B, 1, attn_dim]
        energy = torch.tanh(precomputed_enc + dec_proj) # [B, T, attn_dim]
        scores = self.v(energy).squeeze(-1) # [B, T]

        scores = scores.masked_fill(inv_mask, -1e9)
        attn_weights = F.softmax(scores, dim=-1) # [B, T]
        context = torch.bmm(attn_weights.unsqueeze(1), enc_out).squeeze(1) # [B, enc_dim]
        return context, attn_weights

class AttentionDecoder(nn.Module):
    def __init__(self, vocab_size, embed_dim=128, enc_dim=256, dec_dim=256, attn_dim=128, pad_id=0, dropout=0.2):
        super().__init__()
        self.vocab_size = vocab_size
        self.pad_id = pad_id
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=pad_id)
        self.attention = BahdanauAttention(enc_dim=enc_dim, dec_dim=dec_dim, attn_dim=attn_dim)
        self.rnn_cell = nn.GRUCell(embed_dim + enc_dim, dec_dim)
        self.fc_out = nn.Linear(dec_dim + enc_dim + embed_dim, vocab_size)
        self.dropout = nn.Dropout(dropout)

    def forward_step(self, token_in, prev_state, enc_out, precomputed_enc, inv_mask):
        embed = self.dropout(self.embedding(token_in))
        context, attn_weights = self.attention(prev_state, enc_out, precomputed_enc, inv_mask)
        cell_input = torch.cat([embed, context], dim=-1)
        next_state = self.rnn_cell(cell_input, prev_state)
        logits = self.fc_out(torch.cat([next_state, context, embed], dim=-1))
        return logits, next_state, attn_weights

class JointCTCAttentionModel(nn.Module):
    def __init__(
        self,
        vocab_size,
        in_features=366,
        hidden_dim=256,
        embed_dim=128,
        attn_dim=128,
        pad_id=0,
        sos_id=1,
        eos_id=2,
        dropout=0.2
    ):
        super().__init__()
        self.vocab_size = vocab_size
        self.pad_id = pad_id
        self.sos_id = sos_id
        self.eos_id = eos_id
        # CTC blank token is index = vocab_size (dedicated extra class)
        self.ctc_blank_id = vocab_size
        self.ctc_num_classes = vocab_size + 1

        self.encoder = LandmarkEncoder(
            in_features=in_features,
            hidden_dim=hidden_dim,
            num_layers=2,
            dropout=dropout
        )
        self.ctc_head = nn.Linear(hidden_dim, self.ctc_num_classes)
        self.decoder = AttentionDecoder(
            vocab_size=vocab_size,
            embed_dim=embed_dim,
            enc_dim=hidden_dim,
            dec_dim=hidden_dim,
            attn_dim=attn_dim,
            pad_id=pad_id,
            dropout=dropout
        )
        self.enc_to_dec = nn.Linear(hidden_dim, hidden_dim)

    def forward(self, src, src_mask, src_lens, tgt, teacher_forcing_ratio=0.5):
        """
        src: [B, T_src, 366]
        src_mask: [B, T_src] (True for valid)
        src_lens: [B]
        tgt: [B, T_tgt] (with <sos> at index 0)
        """
        batch_size = src.size(0)
        enc_out = self.encoder(src, src_mask, src_lens) # [B, T_src, hidden_dim]

        # 1. CTC Log Probs: shape [T_src, B, ctc_num_classes]
        ctc_logits = self.ctc_head(enc_out)
        ctc_log_probs = F.log_softmax(ctc_logits, dim=-1).transpose(0, 1)

        # 2. Attention Decoder
        inv_mask = ~src_mask
        precomputed_enc = self.decoder.attention.w_enc(enc_out)

        # Initial decoder state: mean of valid encoder states
        mask_expanded = src_mask.unsqueeze(-1).float()
        sum_enc = (enc_out * mask_expanded).sum(dim=1)
        mean_enc = sum_enc / mask_expanded.sum(dim=1).clamp(min=1.0)
        dec_state = torch.tanh(self.enc_to_dec(mean_enc))

        max_tgt_len = tgt.size(1)
        outputs = []
        token_in = tgt[:, 0] # <sos>

        for t in range(1, max_tgt_len):
            logits, dec_state, _ = self.decoder.forward_step(
                token_in, dec_state, enc_out, precomputed_enc, inv_mask
            )
            outputs.append(logits)
            teacher_force = (torch.rand(1).item() < teacher_forcing_ratio)
            top1 = logits.argmax(1)
            token_in = tgt[:, t] if teacher_force else top1

        decoder_logits = torch.stack(outputs, dim=1) # [B, T_tgt - 1, vocab_size]
        return decoder_logits, ctc_log_probs

    def generate(self, src, src_mask, max_len=50, repetition_penalty=1.2):
        """
        Greedy autoregressive decoding with repetition penalty
        src: [1, T, 366]
        src_mask: [1, T]
        """
        self.eval()
        with torch.no_grad():
            enc_out = self.encoder(src, src_mask, None)
            inv_mask = ~src_mask
            precomputed_enc = self.decoder.attention.w_enc(enc_out)

            mask_expanded = src_mask.unsqueeze(-1).float()
            sum_enc = (enc_out * mask_expanded).sum(dim=1)
            mean_enc = sum_enc / mask_expanded.sum(dim=1).clamp(min=1.0)
            dec_state = torch.tanh(self.enc_to_dec(mean_enc))

            token_in = torch.tensor([self.sos_id], dtype=torch.long, device=src.device)
            generated_tokens = []
            seen_tokens = set()

            for _ in range(max_len):
                logits, dec_state, attn_weights = self.decoder.forward_step(
                    token_in, dec_state, enc_out, precomputed_enc, inv_mask
                )
                
                # Apply repetition penalty to already-generated tokens
                if repetition_penalty > 1.0 and seen_tokens:
                    for tok in seen_tokens:
                        if logits[0, tok] > 0:
                            logits[0, tok] /= repetition_penalty
                        else:
                            logits[0, tok] *= repetition_penalty

                next_token = logits.argmax(1).item()
                if next_token == self.eos_id:
                    break
                generated_tokens.append(next_token)
                seen_tokens.add(next_token)
                token_in = torch.tensor([next_token], dtype=torch.long, device=src.device)

            return generated_tokens

    def generate_ctc(self, src, src_mask, src_lens=None):
        """
        Greedy CTC decoding (argmax -> collapse consecutive repeats -> remove blank)
        """
        self.eval()
        with torch.no_grad():
            enc_out = self.encoder(src, src_mask, src_lens)
            ctc_logits = self.ctc_head(enc_out) # [B, T, ctc_num_classes]
            preds = ctc_logits.argmax(dim=-1) # [B, T]
            
            results = []
            for b in range(preds.size(0)):
                T = src_lens[b].item() if src_lens is not None else src.size(1)
                seq = preds[b, :T].tolist()
                
                # CTC collapse
                collapsed = []
                prev = None
                for t in seq:
                    if t != prev:
                        if t != self.ctc_blank_id:
                            collapsed.append(t)
                        prev = t
                results.append(collapsed)
            return results
