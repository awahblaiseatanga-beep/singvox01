import torch
import torch.nn as nn

class Seq2Seq(nn.Module):
    def __init__(self, input_dim=366, enc_hidden=128, dec_hidden=256, vocab_size=366, embed_dim=128):
        super().__init__()
        self.input_dim = input_dim
        self.enc_hidden = enc_hidden
        self.dec_hidden = dec_hidden
        self.vocab_size = vocab_size
        
        # 1. Encoder
        self.encoder = nn.GRU(
            input_size=input_dim,
            hidden_size=enc_hidden,
            num_layers=1,
            batch_first=True,
            bidirectional=True
        )
        
        # Bridge bidirectional encoder to unidirectional decoder hidden
        self.bridge = nn.Linear(enc_hidden * 2, dec_hidden)
        
        # 2. Decoder
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.decoder = nn.GRU(
            input_size=embed_dim,
            hidden_size=dec_hidden,
            num_layers=1,
            batch_first=True
        )
        self.fc_out = nn.Linear(dec_hidden, vocab_size)

    def encode(self, features, lengths):
        # Pack padded sequence to handle variable lengths natively
        packed = nn.utils.rnn.pack_padded_sequence(
            features, lengths.cpu(), batch_first=True, enforce_sorted=False
        )
        packed_out, hidden = self.encoder(packed)
        # hidden shape: [2, B, enc_hidden]
        
        # Concatenate forward and backward hidden states
        hidden_cat = torch.cat((hidden[0], hidden[1]), dim=1) # [B, enc_hidden * 2]
        dec_hidden = torch.tanh(self.bridge(hidden_cat)).unsqueeze(0) # [1, B, dec_hidden]
        return dec_hidden

    def forward(self, features, lengths, targets, teacher_forcing_ratio=0.5):
        # targets: [B, max_target_len] (starts with SOS, ends with EOS)
        batch_size = features.size(0)
        max_target_len = targets.size(1)
        
        dec_hidden = self.encode(features, lengths)
        
        outputs = []
        # First input is SOS
        dec_input = targets[:, 0].unsqueeze(1) # [B, 1]
        
        for t in range(1, max_target_len):
            embed = self.embedding(dec_input) # [B, 1, embed_dim]
            out, dec_hidden = self.decoder(embed, dec_hidden) # out: [B, 1, dec_hidden]
            logits = self.fc_out(out) # [B, 1, vocab_size]
            outputs.append(logits)
            
            # Teacher forcing
            use_teacher_forcing = (torch.rand(1).item() < teacher_forcing_ratio)
            top1 = logits.argmax(dim=-1) # [B, 1]
            dec_input = targets[:, t].unsqueeze(1) if use_teacher_forcing else top1
            
        outputs = torch.cat(outputs, dim=1) # [B, max_target_len - 1, vocab_size]
        return outputs

    def decode_greedy(self, features, lengths, max_len=40, sos_id=1, eos_id=2):
        self.eval()
        with torch.no_grad():
            dec_hidden = self.encode(features, lengths)
            batch_size = features.size(0)
            
            dec_input = torch.full((batch_size, 1), sos_id, dtype=torch.long, device=features.device)
            generated_tokens = []
            
            for _ in range(max_len):
                embed = self.embedding(dec_input)
                out, dec_hidden = self.decoder(embed, dec_hidden)
                logits = self.fc_out(out)
                top1 = logits.argmax(dim=-1) # [B, 1]
                
                generated_tokens.append(top1)
                dec_input = top1
                
            generated_tokens = torch.cat(generated_tokens, dim=1) # [B, max_len]
            return generated_tokens
