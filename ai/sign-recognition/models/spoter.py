import torch
import torch.nn as nn
import math

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        self.pe = nn.Parameter(torch.empty(1, max_len, d_model))
        nn.init.uniform_(self.pe, -0.1, 0.1)

    def forward(self, x):
        # x is (batch_size, seq_len, d_model)
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)

class Spoter(nn.Module):
    def __init__(self, num_classes=79, hidden_dim=512, nhead=8, num_encoder_layers=6, num_decoder_layers=6, dim_feedforward=2048, dropout=0.1):
        super(Spoter, self).__init__()
        
        # 1. SignVox 366-D specific adaptation
        # The reference model evaluates dynamic subsets; we project the fixed frozen 366-D directly.
        self.input_proj = nn.Linear(366, hidden_dim)
        
        # 2. Positional Encoding
        self.pos_encoder = PositionalEncoding(hidden_dim, dropout)
        
        # 3. Transformer Encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_dim, 
            nhead=nhead, 
            dim_feedforward=dim_feedforward, 
            dropout=dropout, 
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_encoder_layers)
        
        # 4. Transformer Decoder
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=hidden_dim, 
            nhead=nhead, 
            dim_feedforward=dim_feedforward, 
            dropout=dropout, 
            batch_first=True
        )
        self.transformer_decoder = nn.TransformerDecoder(decoder_layer, num_layers=num_decoder_layers)
        
        # 5. Decoder Query Mechanism
        # Reference SPOTER utilizes a fixed learnable class query token representing global output sequence queries natively
        self.class_query = nn.Parameter(torch.rand(1, 1, hidden_dim))
        
        # 6. Classification Mechanism
        # Linearly mapping explicitly down to canonical 79 classes
        self.classifier = nn.Linear(hidden_dim, num_classes)
        
    def forward(self, x, attention_mask=None):
        """
        x: (batch_size, seq_len, 366)
        attention_mask: (batch_size, seq_len) -> Boolean explicitly True=Real, False=Padding
        """
        x = self.input_proj(x)
        x = self.pos_encoder(x)
        
        # PyTorch attention mask semantics inversion
        # PyTorch expects True = ignore (pad), False = attend (real)
        # SignVox Dataloader exposes True = real, False = pad
        if attention_mask is not None:
            pytorch_pad_mask = ~attention_mask
        else:
            pytorch_pad_mask = None
            
        memory = self.transformer_encoder(x, src_key_padding_mask=pytorch_pad_mask)
        
        batch_size = x.size(0)
        query = self.class_query.expand(batch_size, -1, -1)
        
        # The query vector attends to the computed memory keys securely
        out = self.transformer_decoder(tgt=query, memory=memory, memory_key_padding_mask=pytorch_pad_mask)
        
        # Output classification step natively tracking exactly 79 states natively
        out = out.squeeze(1) # shape: (batch_size, hidden_dim)
        logits = self.classifier(out) # shape: (batch_size, num_classes)
        
        return logits
