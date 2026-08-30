from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"

DEFAULT_BILLING_FILE = DATA_DIR / "billing_export.csv"
DEFAULT_PROJECT_FILE = DATA_DIR / "project_export.csv"

MATCH_THRESHOLD = 90.0
MATCH_MARGIN = 5.0
RENEWAL_WINDOW_DAYS = 45
