import re
import json
from collections import Counter, defaultdict
from pathlib import Path

class BPETokenizer:
    PAD_TOKEN = "<pad>"
    SOS_TOKEN = "<sos>"
    EOS_TOKEN = "<eos>"
    UNK_TOKEN = "<unk>"
    
    SPECIAL_TOKENS = [PAD_TOKEN, SOS_TOKEN, EOS_TOKEN, UNK_TOKEN]
    
    def __init__(self, target_vocab_size=1000):
        self.target_vocab_size = target_vocab_size
        self.token2id = {}
        self.id2token = {}
        self.merges = []
        
        for idx, tok in enumerate(self.SPECIAL_TOKENS):
            self.token2id[tok] = idx
            self.id2token[idx] = tok
            
        self.pad_id = self.token2id[self.PAD_TOKEN]
        self.sos_id = self.token2id[self.SOS_TOKEN]
        self.eos_id = self.token2id[self.EOS_TOKEN]
        self.unk_id = self.token2id[self.UNK_TOKEN]

    def _normalize(self, text):
        text = text.lower().strip()
        text = re.sub(r"[^\w\s']", " ", text)
        return text

    def _get_stats(self, vocab):
        pairs = defaultdict(int)
        for word, freq in vocab.items():
            symbols = word.split()
            for i in range(len(symbols) - 1):
                pairs[(symbols[i], symbols[i + 1])] += freq
        return pairs

    def _merge_vocab(self, pair, v_in):
        v_out = {}
        bigram = re.escape(" ".join(pair))
        p = re.compile(r"(?<!\S)" + bigram + r"(?!\S)")
        replacement = "".join(pair)
        for word in v_in:
            w_out = p.sub(replacement, word)
            v_out[w_out] = v_in[word]
        return v_out

    def fit(self, texts):
        # 1. Build initial character vocabulary with end-of-word markers
        word_freqs = Counter()
        for t in texts:
            cleaned = self._normalize(t)
            for w in cleaned.split():
                if w:
                    # Space-separated characters with '</w>' suffix
                    word_repr = " ".join(list(w)) + " </w>"
                    word_freqs[word_repr] += 1
                    
        # Collect base characters
        base_chars = set()
        for w in word_freqs:
            for ch in w.split():
                base_chars.add(ch)
                
        # Register base characters
        for ch in sorted(list(base_chars)):
            if ch not in self.token2id:
                idx = len(self.token2id)
                self.token2id[ch] = idx
                self.id2token[idx] = ch

        # 2. Learn merges
        vocab = dict(word_freqs)
        num_merges = self.target_vocab_size - len(self.token2id)
        
        self.merges = []
        for i in range(num_merges):
            pairs = self._get_stats(vocab)
            if not pairs:
                break
            best_pair = max(pairs, key=pairs.get)
            vocab = self._merge_vocab(best_pair, vocab)
            self.merges.append(best_pair)
            merged_tok = "".join(best_pair)
            if merged_tok not in self.token2id:
                idx = len(self.token2id)
                self.token2id[merged_tok] = idx
                self.id2token[idx] = merged_tok
                
        print(f"BPE Tokenizer fit completed. Final vocab size: {len(self.token2id)} (merges: {len(self.merges)})")

    def _encode_word(self, word):
        symbols = list(word) + ["</w>"]
        for pair in self.merges:
            p0, p1 = pair
            i = 0
            new_symbols = []
            while i < len(symbols):
                if i < len(symbols) - 1 and symbols[i] == p0 and symbols[i + 1] == p1:
                    new_symbols.append(p0 + p1)
                    i += 2
                else:
                    new_symbols.append(symbols[i])
                    i += 1
            symbols = new_symbols
        return symbols

    def encode(self, text, add_special_tokens=True):
        cleaned = self._normalize(text)
        tokens = []
        if add_special_tokens:
            tokens.append(self.sos_id)
            
        for w in cleaned.split():
            subwords = self._encode_word(w)
            for sw in subwords:
                token_id = self.token2id.get(sw, self.unk_id)
                tokens.append(token_id)
                
        if add_special_tokens:
            tokens.append(self.eos_id)
        return tokens

    def decode(self, token_ids, skip_special_tokens=True):
        subwords = []
        for tid in token_ids:
            if tid in [self.pad_id, self.sos_id, self.eos_id, self.unk_id]:
                if not skip_special_tokens:
                    subwords.append(self.id2token.get(tid, self.UNK_TOKEN))
                continue
            subwords.append(self.id2token.get(tid, self.UNK_TOKEN))
            
        text = "".join(subwords).replace("</w>", " ").strip()
        return text

    def save(self, filepath):
        data = {
            "target_vocab_size": self.target_vocab_size,
            "token2id": self.token2id,
            "merges": self.merges
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        tok = cls(target_vocab_size=data["target_vocab_size"])
        tok.token2id = data["token2id"]
        tok.id2token = {int(v): k for k, v in tok.token2id.items()}
        tok.merges = [tuple(m) for m in data["merges"]]
        tok.pad_id = tok.token2id[cls.PAD_TOKEN]
        tok.sos_id = tok.token2id[cls.SOS_TOKEN]
        tok.eos_id = tok.token2id[cls.EOS_TOKEN]
        tok.unk_id = tok.token2id[cls.UNK_TOKEN]
        return tok
