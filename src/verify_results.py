"""Read-only public verification; never export or replace a saved model."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.verify_handover import main
if __name__ == '__main__':
    main()
