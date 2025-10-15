import json
from pathlib import Path
import shutil
import re
from datetime import datetime, timedelta
from dateutil import parser as dateparser


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
def create_latest_backups():
    for json_file in data_dir.glob("**/*.json"):
        if not json_file.is_file():
            continue
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if len(data) >= 5:
                backup_file_name = f"{json_file.stem}_latest_backup{json_file.suffix}"
                backup_file_path = backup_dir / "latest" / backup_file_name
                shutil.copy2(json_file, backup_file_path)
                print(f"{Colors.GREEN}Backed up {json_file.name} ({len(data)} entries) to {backup_file_path.name}{Styles.default}")
            else:
                print(f"{Colors.YELLOW}Skipping backup for {json_file.name}: Found only {len(data)} entries (minimum 5 required). Previous backup retained.{Styles.default}")
        except json.JSONDecodeError:
            print(f"{BG_Colors.RED_BG}Failed to read {json_file.name}: Invalid JSON format. Backup skipped.{Styles.default}")
        except Exception as e:
            print(f"{BG_Colors.RED_BG}Failed to process {json_file.name}: {e}. Backup skipped.{Styles.default}")

# Function to create weekly backups by copying latest backups if none exist or if existing backups are a week or older
def create_weekly_backups():
    weekly_backup_dir = backup_dir / "weekly"
    weekly_backup_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().date()
    weekly_backups = {}
    for file in weekly_backup_dir.glob("**/*_weekly_backup.json"):
        try:
            type_key = "_raw_" if "_raw_" in file.stem else "_processed_" if "_processed_" in file.stem else None
            if not type_key:
                print(f"{Colors.YELLOW}Skipped {file.name}: invalid type{Styles.default}")
                continue
            theater, date_str = file.stem.split(type_key)
            date_str = date_str.split("_weekly_backup")[0]
            backup_date = datetime.strptime(date_str, "%Y%m%d_%H%M%S").date()
            weekly_backups[f"{theater}_{type_key.strip('_')}"] = {"file": file, "date": backup_date}
        except (IndexError, ValueError) as e:
            print(f"{Colors.YELLOW}Skipped {file.name}: {e}{Styles.default}")
    for file in (backup_dir / "latest").glob("**/*_latest_backup.json"):
        try:
            type_key = "_raw_" if "_raw_" in file.stem else "_processed_" if "_processed_" in file.stem else None
            if not type_key:
                print(f"{Colors.YELLOW}Skipped {file.name}: invalid type{Styles.default}")
                continue
            theater, timestamp = file.stem.split(type_key)
            timestamp = timestamp.split("_latest_backup")[0]
            type_suffix = type_key.strip("_")
            key = f"{theater}_{type_suffix}"
            backup_file = weekly_backup_dir / f"{theater}_{type_suffix}_{timestamp}_weekly_backup.json"
            existing = weekly_backups.get(key)
            if not existing:
                shutil.copy2(file, backup_file)
                print(f"{Colors.GREEN}Created {key} backup: {backup_file.name}{Styles.default}")
            elif (today - existing["date"]).days >= 7:
                shutil.copy2(file, backup_file)
                print(f"{Colors.GREEN}Updated {key} backup: {backup_file.name}{Styles.default}")
            else:
                print(f"{Colors.YELLOW}Skipped {key}: recent ({existing['date']}){Styles.default}")
        except (IndexError, ValueError) as e:
            print(f"{Colors.YELLOW}Skipped {file.name}: {e}{Styles.default}")

# Clean old backups in the specified directory (latest or weekly), keeping only the newest file per theater and type
def clean_old_backups(backup_type):
    print(f"{Colors.BLUE}Cleaning in {backup_dir}...{Styles.default}\n")
    latest_files = {}
    for file in backup_dir.glob(f"**/*_{backup_type}_backup.json"):
        match = re.match(r"(.+)_(raw|processed)_(\d{8}_\d{6})_" + backup_type + r"_backup\.json$", file.name)
        if match:
            theater, file_type, timestamp = match.groups()
            key = f"{theater}_{file_type}"
            if key not in latest_files or timestamp > latest_files[key]["timestamp"]:
                if key in latest_files:
                    old_file = latest_files[key]["file"]
                    print(f"{Colors.YELLOW}Deleting: {old_file}{Styles.default}")
                    old_file.unlink()
                latest_files[key] = {"timestamp": timestamp, "file": file}
            else:
                print(f"{Colors.YELLOW}Deleting: {file}{Styles.default}")
                file.unlink()
        else:
            print(f"{Colors.RED}Skipping invalid filename: {file.name}{Styles.default}")
    for key, info in latest_files.items():
        print(f"{Colors.GREEN}Kept newest file for {key}: {info['file'].name}{Styles.default}")

# Main function to backup latest data and backup weeklydata if parameters met
def main():
    print(f"\n\n{BG_Colors.MAGENTA_BG}{Styles.BOLD}{Styles.UNDERLINE} ///// Beginning Data Backup Script ///// {Styles.default}\n\n")
    print(f"{Colors.BLUE}Creating latest backups... {Styles.default}\n")
    create_latest_backups()
    print(f"\n{Colors.BLUE}Checking weekly backups... {Styles.default}\n")
    create_weekly_backups()
    print(f"\n{Colors.BLUE}Cleaning latest backups... {Styles.default}")
    clean_old_backups("latest")
    print(f"\n{Colors.BLUE}Cleaning weekly backups... {Styles.default}")
    clean_old_backups("weekly")
    print(f"\n\n{BG_Colors.GREEN_BG}{Styles.BOLD} ///// Data Backups Complete ///// {Styles.default}\n\n")

if __name__ == '__main__':
    main()