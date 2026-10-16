from pathlib import Path

log_path = Path(r"experiments/continuous-asl/phase_2c_27/debug.log")
text = log_path.read_text(encoding="utf-16", errors="replace")
clean_path = Path(r"experiments/continuous-asl/phase_2c_27/debug_utf8.txt")
clean_path.write_text(text, encoding="utf-8")
print(f"Converted to debug_utf8.txt successfully. Chars: {len(text)}")
