"""Step 1 (EL): download sources and load them into the raw schema."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gridflow.extract_load import run

if __name__ == "__main__":
    for line in run():
        print(line)
