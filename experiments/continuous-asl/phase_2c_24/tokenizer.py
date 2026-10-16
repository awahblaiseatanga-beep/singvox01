import csv
import json
import collections
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
TRAIN_CSV = BASE_DIR / "experiments" / "continuous-asl" / "phase_2c_24" / "train.csv"
VOCAB_PATH = BASE_DIR / "experiments" / "continuous-asl" / "phase_2c_24" / "vocab.json"

class SimpleWordTokenizer:
    def __init__(self, vocab_path=VOCAB_PATH):
        self.vocab_path = vocab_path
        self.pad_token = "[PAD]"
        self.sos_token = "[SOS]"
        self.eos_token = "[EOS]"
        self.unk_token = "[UNK]"
        
        self.pad_id = 0
        self.sos_id = 1
        self.eos_id = 2
        self.unk_id = 3
        
        self.word2id = {
            self.pad_token: self.pad_id,
            self.sos_token: self.sos_id,
            self.eos_token: self.eos_id,
            self.unk_token: self.unk_id
        }
        self.id2word = {i: w for w, i in self.word2id.items()}

    def _normalize(self, text):
        import re
        text = text.lower().strip()
        # strip basic punctuation
        text = re.sub(r'[^\w\s]', '', text)
        return text.split()

    def fit_and_save(self, csv_file, min_freq=1):
        counter = collections.Counter()
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                words = self._normalize(row.get("SENTENCE", ""))
                counter.update(words)
        
        idx = 4
        for word, count in counter.items():
            if count >= min_freq and word not in self.word2id:
                self.word2id[word] = idx
                self.id2word[idx] = word
                idx += 1
                
        with open(self.vocab_path, 'w', encoding='utf-8') as f:
            json.dump({"word2id": self.word2id}, f, indent=2)
            
        print(f"Tokenizer fitted. Vocab Size: {len(self.word2id)}")

    def load(self):
        with open(self.vocab_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.word2id = data["word2id"]
            self.id2word = {int(i): w for w, i in self.word2id.items()}
            
    def encode(self, text, add_special_tokens=True):
        words = self._normalize(text)
        ids = [self.word2id.get(w, self.unk_id) for w in words]
        if add_special_tokens:
            ids = [self.sos_id] + ids + [self.eos_id]
        return ids

    def decode(self, ids):
        words = []
        for i in ids:
            if i == self.pad_id:
                continue
            if i == self.eos_id:
                break
            if i == self.sos_id:
                continue
            words.append(self.id2word.get(i, self.unk_token))
        return " ".join(words)
        
    @property
    def vocab_size(self):
        return len(self.word2id)

if __name__ == "__main__":
    tokenizer = SimpleWordTokenizer()
    tokenizer.fit_and_save(TRAIN_CSV)
