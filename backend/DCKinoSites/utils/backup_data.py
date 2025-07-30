import json
from pathlib import Path
import shutil

# Base directory (where this script is located)
base_dir = Path(__file__).resolve().parent.parent

# Input data directory
data_dir = base_dir / "data"

# Output backup directory
backup_dir = base_dir / "data_backup"
backup_dir.mkdir(parents=True, exist_ok=True)

# ANSI Text Colors and Styles
class Colors:
    BLUE = '\033[34m'
    GREEN = '\033[32m'
    RED = '\033[31m'
    YELLOW = '\033[33m'
class BG_Colors:
    GREEN_BG = '\033[42m'
    RED_BG = '\033[41m'
    MAGENTA_BG = '\033[45m'
class Styles:
    BLINK = '\033[5m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    default = '\033[0m'

# Function to iterate over all .json files in the data directory by reading and validating to ensure valid data to proceed with backup, or to maintain old version if not
def create_json_backups():
    for json_file in data_dir.glob("*.json"):
        if not json_file.is_file():
            continue
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if len(data) >= 5:
                backup_file_name = f"{json_file.stem}_backup{json_file.suffix}"
                backup_file_path = backup_dir / backup_file_name
                shutil.copy2(json_file, backup_file_path)
                print(f"{Colors.GREEN}Backed up {json_file.name} ({len(data)} entries) to {backup_file_path.name}{Styles.default}")
            else:
                print(f"{Colors.YELLOW}Skipping backup for {json_file.name}: Found only {len(data)} entries (minimum 5 required). Previous backup retained.{Styles.default}")
        except json.JSONDecodeError:
            print(f"{BG_Colors.RED_BG}Failed to read {json_file.name}: Invalid JSON format. Backup skipped.{Styles.default}")
        except Exception as e:
            print(f"{BG_Colors.RED_BG}Failed to process {json_file.name}: {e}. Backup skipped.{Styles.default}")

# Create Backups
print(f"\n\n{BG_Colors.MAGENTA_BG}{Styles.BOLD}{Styles.UNDERLINE} ///// Beginning Data Backup Script ///// {Styles.default}\n\n")
create_json_backups()
print(f"\n\n{BG_Colors.GREEN_BG}{Styles.BOLD} ///// Data Backups Complete ///// {Styles.default}\n\n")