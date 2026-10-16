import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
SANDBOX_CSV_PATH = BASE_DIR / "data" / "sandbox_continuous" / "how2sign_sample" / "how2sign_val.csv"
FEATURES_DIR = BASE_DIR / "experiments" / "continuous-asl" / "phase_2c_22" / "features"

# Model configurations
FEATURE_DIM = 366
