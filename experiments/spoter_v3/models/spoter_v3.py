"""
SignVox SPOTER V3 Architecture Specification
Target: 100-Class Canonical ASL Vocabulary
Input Dimension: 366-D (SignVox canonical landmark features)
Output Dimension: 100 (Classes 0-99 mapped from ASL_100_VOCABULARY_SPEC.md)
"""

import math
import torch
import torch.nn as nn

class PositionalEncoding(nn.Module):
    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)
        self.pe = nn.Parameter(torch.empty(1, max_len, d_model))
        nn.init.uniform_(self.pe, -0.1, 0.1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch_size, seq_len, d_model)
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)

class SpoterV3(nn.Module):
    def __init__(
        self,
        num_classes: int = 100,
        input_dim: int = 366,
        hidden_dim: int = 512,
        nhead: int = 8,
        num_encoder_layers: int = 6,
        num_decoder_layers: int = 6,
        dim_feedforward: int = 2048,
        dropout: float = 0.1
    ):
        super(SpoterV3, self).__init__()
        
        self.num_classes = num_classes
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        
        # 1. Input Linear Projection from 366-D to hidden_dim
        self.input_proj = nn.Linear(input_dim, hidden_dim)
        
        # 2. Positional Encoding
        self.pos_encoder = PositionalEncoding(hidden_dim, dropout=dropout)
        
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
        
        # 5. Fixed Learnable Class Query Token
        self.class_query = nn.Parameter(torch.rand(1, 1, hidden_dim))
        
        # 6. Classifier Projection to 100 Canonical Classes
        self.classifier = nn.Linear(hidden_dim, num_classes)
        
    def forward(self, x: torch.Tensor, attention_mask: torch.Tensor = None) -> torch.Tensor:
        """
        Forward pass for SPOTER V3.
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, 366)
            attention_mask: Optional boolean tensor of shape (batch_size, seq_len)
                            True = valid frame, False = padding frame.
        Returns:
            Logits tensor of shape (batch_size, num_classes)
        """
        # Project input features
        x = self.input_proj(x)
        x = self.pos_encoder(x)
        
        # Invert mask for PyTorch Transformer (True = masked/ignored, False = attended)
        if attention_mask is not None:
            pytorch_pad_mask = ~attention_mask
        else:
            pytorch_pad_mask = None
            
        # Encoder pass
        memory = self.transformer_encoder(x, src_key_padding_mask=pytorch_pad_mask)
        
        # Decoder pass with learnable class query token
        batch_size = x.size(0)
        query = self.class_query.expand(batch_size, -1, -1)
        out = self.transformer_decoder(tgt=query, memory=memory, memory_key_padding_mask=pytorch_pad_mask)
        
        # Final classification logits: (batch_size, 100)
        out = out.squeeze(1)
        logits = self.classifier(out)
        
        return logits
