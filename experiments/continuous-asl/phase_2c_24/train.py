import os
import sys
import json
import torch
import torch.nn as nn
from pathlib import Path
from torch.utils.data import Dataset, DataLoader

# Setup paths
PHASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(PHASE_DIR))
sys.path.append(str(PHASE_DIR.parent / "phase_2c_23"))

from tokenizer import SimpleWordTokenizer
from dataset import ContinuousASLDataset
from model import Seq2Seq
from baseline import compute_bleu

FEATURES_DIR = PHASE_DIR.parent / "phase_2c_22" / "features"
TRAIN_CSV = PHASE_DIR / "train.csv"
VAL_CSV = PHASE_DIR / "val.csv"
TEST_CSV = PHASE_DIR / "test.csv"

class TokenizedContinuousDataset(Dataset):
    def __init__(self, csv_path, tokenizer):
        self.base_dataset = ContinuousASLDataset(csv_path, FEATURES_DIR)
        self.tokenizer = tokenizer
        
    def __len__(self):
        return len(self.base_dataset)
        
    def __getitem__(self, idx):
        item = self.base_dataset[idx]
        tokens = self.tokenizer.encode(item["sentence"])
        return {
            "sentence_name": item["sentence_name"],
            "sentence": item["sentence"],
            "features": item["features"],
            "length": item["length"],
            "tokens": torch.tensor(tokens, dtype=torch.long)
        }

def seq2seq_collate_fn(batch):
    lengths = [item["length"] for item in batch]
    features = [item["features"] for item in batch]
    tokens = [item["tokens"] for item in batch]
    sentences = [item["sentence"] for item in batch]
    sentence_names = [item["sentence_name"] for item in batch]
    
    padded_features = torch.nn.utils.rnn.pad_sequence(features, batch_first=True, padding_value=0.0)
    padded_tokens = torch.nn.utils.rnn.pad_sequence(tokens, batch_first=True, padding_value=0) # 0 is PAD
    
    return {
        "features": padded_features,
        "lengths": torch.tensor(lengths, dtype=torch.long),
        "tokens": padded_tokens,
        "sentences": sentences,
        "sentence_names": sentence_names
    }

def train_and_evaluate():
    # 1. Setup tokenizer
    tokenizer = SimpleWordTokenizer()
    tokenizer.load()
    
    train_dataset = TokenizedContinuousDataset(TRAIN_CSV, tokenizer)
    val_dataset = TokenizedContinuousDataset(VAL_CSV, tokenizer)
    test_dataset = TokenizedContinuousDataset(TEST_CSV, tokenizer)
    
    train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True, collate_fn=seq2seq_collate_fn)
    val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False, collate_fn=seq2seq_collate_fn)
    test_loader = DataLoader(test_dataset, batch_size=8, shuffle=False, collate_fn=seq2seq_collate_fn)
    
    # 2. Model, Loss, Optimizer
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on device: {device}")
    
    model = Seq2Seq(
        input_dim=366,
        enc_hidden=128,
        dec_hidden=256,
        vocab_size=tokenizer.vocab_size,
        embed_dim=128
    ).to(device)
    
    criterion = nn.CrossEntropyLoss(ignore_index=tokenizer.pad_id)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    
    # 3. Training Loop
    epochs = 20
    history = []
    
    for epoch in range(1, epochs + 1):
        model.train()
        total_loss = 0.0
        
        for batch in train_loader:
            features = batch["features"].to(device)
            lengths = batch["lengths"].to(device)
            tokens = batch["tokens"].to(device)
            
            optimizer.zero_grad()
            # targets for forward pass: input tokens [B, T_tok]
            # output logits: [B, T_tok - 1, vocab_size]
            logits = model(features, lengths, tokens, teacher_forcing_ratio=0.5)
            
            # target tokens shifted by 1 (ignoring initial SOS)
            targets = tokens[:, 1:]
            
            loss = criterion(logits.reshape(-1, tokenizer.vocab_size), targets.reshape(-1))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
            
        avg_train_loss = total_loss / len(train_loader)
        
        # Validation Evaluation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                features = batch["features"].to(device)
                lengths = batch["lengths"].to(device)
                tokens = batch["tokens"].to(device)
                
                logits = model(features, lengths, tokens, teacher_forcing_ratio=0.0)
                targets = tokens[:, 1:]
                loss = criterion(logits.reshape(-1, tokenizer.vocab_size), targets.reshape(-1))
                val_loss += loss.item()
                
        avg_val_loss = val_loss / max(1, len(val_loader))
        print(f"Epoch {epoch:2d}/{epochs} | Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
        history.append({"epoch": epoch, "train_loss": avg_train_loss, "val_loss": avg_val_loss})
        
    # Save checkpoint
    torch.save(model.state_dict(), PHASE_DIR / "seq2seq_checkpoint.pt")
    with open(PHASE_DIR / "training_history.json", 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2)
        
    # 4. Evaluation via Greedy Decoding (no reference text provided during inference)
    print("\n=== Evaluating Sequence Generation (Greedy Inference) ===")
    def evaluate_split(loader, name):
        model.eval()
        references = []
        predictions = []
        
        for batch in loader:
            features = batch["features"].to(device)
            lengths = batch["lengths"].to(device)
            sentences = batch["sentences"]
            
            # Greedy generation: zero teacher forcing
            token_ids = model.decode_greedy(features, lengths, max_len=30, sos_id=tokenizer.sos_id, eos_id=tokenizer.eos_id)
            
            for i in range(len(sentences)):
                pred_text = tokenizer.decode(token_ids[i].tolist())
                references.append(sentences[i])
                predictions.append(pred_text)
                
        # Metrics
        exact_matches = sum(1 for r, p in zip(references, predictions) if r.lower().strip() == p.lower().strip())
        exact_match_acc = exact_matches / max(1, len(references))
        
        bleus = [compute_bleu(r.lower().split(), p.lower().split()) for r, p in zip(references, predictions)]
        avg_bleu = sum(bleus) / max(1, len(bleus))
        
        print(f"Split {name:5s} | Exact-Match Acc: {exact_match_acc:.4f} | BLEU: {avg_bleu:.4f}")
        return {
            "exact_match_acc": exact_match_acc,
            "avg_bleu": avg_bleu,
            "examples": [{"ref": r, "pred": p} for r, p in zip(references[:3], predictions[:3])]
        }
        
    eval_results = {
        "train": evaluate_split(train_loader, "Train"),
        "val": evaluate_split(val_loader, "Val"),
        "test": evaluate_split(test_loader, "Test")
    }
    
    with open(PHASE_DIR / "evaluation_results.json", 'w', encoding='utf-8') as f:
        json.dump(eval_results, f, indent=2)
        
    print("\nCompleted Phase 2C.24 Model Training and Evaluation.")

if __name__ == "__main__":
    train_and_evaluate()
