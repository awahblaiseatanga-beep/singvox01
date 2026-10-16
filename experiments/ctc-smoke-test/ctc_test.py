import os
import torch
import torch.nn as nn
import torch.optim as optim
import traceback

torch.manual_seed(42)

# VOCAB: 0: <blank>, 1: HELLO, 2: YES, 3: NO
VOCAB = ['<blank>', 'HELLO', 'YES', 'NO']
NUM_CLASSES = len(VOCAB)
FEATURE_DIM = 8  # tiny synthetic feature space

# Synthetic Data Generation
# We create a function to generate a strict deterministic sequence
def generate_synthetic_frame(token_idx):
    vec = torch.zeros(FEATURE_DIM)
    if token_idx > 0:
        vec[token_idx - 1] = 2.0  # signal strength
    vec += torch.randn(FEATURE_DIM) * 0.1 # noise
    return vec

def generate_sequence(tokens, total_frames):
    seq = []
    # e.g., if tokens=[1, 2], and total_frames=10
    # we emit blanks mostly, and emit the tokens for brief windows
    span = total_frames // (len(tokens) + 2)
    tok_ptr = 0
    
    for i in range(total_frames):
        if tok_ptr < len(tokens) and i == span * (tok_ptr + 1):
            seq.append(generate_synthetic_frame(tokens[tok_ptr]))
            tok_ptr += 1
        elif tok_ptr < len(tokens) and i == span * (tok_ptr + 1) + 1:
            seq.append(generate_synthetic_frame(tokens[tok_ptr - 1])) # hold token 2 frames
        else:
            seq.append(generate_synthetic_frame(0)) # blank
            
    return torch.stack(seq)

class TinySequenceModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.lstm = nn.LSTM(input_size=FEATURE_DIM, hidden_size=16, batch_first=True)
        self.fc = nn.Linear(16, NUM_CLASSES)
        
    def forward(self, x):
        out, _ = self.lstm(x)
        logits = self.fc(out)
        return logits

def greedy_decode(logits):
    # logits: (T, NUM_CLASSES)
    # returns list of tokens
    preds = torch.argmax(logits, dim=-1)
    # CTC rules: collapse repeated, remove blanks (0)
    decoded = []
    prev = -1
    for p in preds:
        idx = p.item()
        if idx != prev:
            if idx != 0:
                decoded.append(idx)
        prev = idx
    return decoded

def run_smoke_test():
    print("=== Phase 2A: CTC Smoke Test ===")
    
    # 1. Setup deterministic data
    # Seq A: [HELLO] (1)
    # Seq B: [HELLO, YES] (1, 2)
    # Seq C: [YES, YES] (2, 2) - Must handle repeats with blanks between them natively
    
    # Constructing training loops
    X_train = [
        generate_sequence([1], 15),
        generate_sequence([1, 2], 20),
        generate_sequence([2, 2], 25),
        generate_sequence([2, 3, 1], 30) # Variable length
    ]
    Y_train = [
        torch.tensor([1], dtype=torch.long),
        torch.tensor([1, 2], dtype=torch.long),
        torch.tensor([2, 2], dtype=torch.long),
        torch.tensor([2, 3, 1], dtype=torch.long)
    ]
    
    input_lengths = torch.tensor([len(x) for x in X_train], dtype=torch.long)
    target_lengths = torch.tensor([len(y) for y in Y_train], dtype=torch.long)
    
    # Pad sequences cleanly for batching
    X_padded = nn.utils.rnn.pad_sequence(X_train, batch_first=True)
    Y_concat = torch.cat(Y_train) 
    
    model = TinySequenceModel()
    criterion = nn.CTCLoss(blank=0, zero_infinity=True)
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    
    # Baseline Test (Negative case - before training)
    print("\n[Baseline Negative Check]")
    model.eval()
    with torch.no_grad():
        base_logits = model(X_padded)
        for i in range(len(X_train)):
            decoded = greedy_decode(base_logits[i, :input_lengths[i]])
            print(f"Sample {i} target={Y_train[i].tolist()} -> baseline_decode={decoded}")
    
    # Training Loop
    print("\n[Training Output]")
    model.train()
    for epoch in range(1500):
        optimizer.zero_grad()
        logits = model(X_padded) # (batch, T, classes)
        
        # PyTorch CTCLoss expects (T, batch, classes) and log_softmax
        log_probs = nn.functional.log_softmax(logits, dim=2).transpose(0, 1)
        
        loss = criterion(log_probs, Y_concat, input_lengths, target_lengths)
        
        # Explicit test for valid loss
        if not torch.isfinite(loss):
            print("ERROR: Non-finite loss detected!")
            break
            
        loss.backward()
        
        # Test Gradients
        if epoch == 0:
            grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), float('inf'))
            print(f"Epoch 0 gradient norm: {grad_norm.item():.4f} (Must be > 0)")
            
        optimizer.step()
        
        if (epoch + 1) % 500 == 0:
            print(f"Epoch {epoch+1}/1500, Loss: {loss.item():.4f}")
            
    # Evaluation
    print("\n[Evaluation]")
    model.eval()
    success = True
    with torch.no_grad():
        eval_logits = model(X_padded)
        for i in range(len(X_train)):
            decoded = greedy_decode(eval_logits[i, :input_lengths[i]])
            target_list = Y_train[i].tolist()
            match = decoded == target_list
            print(f"Sample {i} target={target_list} -> decoded={decoded} | Match: {match}")
            if not match: success = False

    # Negative constraints tests
    print("\n[Malformed Input Testing]")
    try:
        # Pass a totally broken 1D tensor to trigger failure
        bad_input = torch.zeros(5)
        model(bad_input)
        print("FAIL: Model accepted malformed 1D input.")
    except Exception as e:
        print(f"PASS: Malformed input gracefully caught dimensionality error -> {type(e).__name__}")
        
    print(f"\nExperiment Result: {'PASS' if success else 'FAIL'}")

if __name__ == "__main__":
    run_smoke_test()
