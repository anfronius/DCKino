import json
from datetime import datetime, timedelta
from pathlib import Path
import blacklist_showings  # Import the script directly from the same directory

# Base directory (where the Scrapy project is located)
base_dir = Path(__file__).resolve().parent.parent

# Data directories (where JSONs are located)
data_dir = base_dir / "data"
backup_dir = base_dir / "data_backup/latest"

# Output file (to site's data folder)
output_dir = base_dir.parent.parent / "frontend/src/data"
output_path = output_dir / "movies.json"
output_dir.mkdir(parents=True, exist_ok=True)

# Access the BLACKLIST_SHOWINGS constant from the imported script
BLACKLIST_SHOWINGS = blacklist_showings.BLACKLIST_SHOWINGS

# Setting time limits
today = datetime.today()
cutoff = today + timedelta(days=30)

# ANSI text colors and styles
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

# Theater list
theaters = ["afisilver", "angelika", "avalon", "greenbelt", "landmark", "lockmart", "miracle", "suns"]

# Load the latest processed JSON file for a theater from its data subdirectory or backup
def load_json(theater, min_entries=5):
    theater_dir = data_dir / theater
    backup_theater_dir = backup_dir
    primary_failed = False
    if not theater_dir.exists():
        print(f"{Colors.RED}Directory not found for {theater}: {theater_dir} {Styles.default}")
        primary_failed = True
    else:
        json_files = sorted(theater_dir.glob("*_processed_*.json"), key=lambda x: x.stat().st_mtime, reverse=True)
        if json_files:
            latest_file = json_files[0]
            try:
                with open(latest_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if len(data) >= min_entries:
                    print(f"{Colors.GREEN}Loaded {len(data)} entries from {theater} ({latest_file.name}) {Styles.default}")
                    return data
                else:
                    print(f"{Colors.YELLOW}{theater} file has {len(data)} entries (minimum {min_entries} required). Checking backup... {Styles.default}")
                    primary_failed = True
            except (json.JSONDecodeError, Exception) as e:
                print(f"{Colors.RED}Failed to load or parse {theater} from {latest_file.name}: {e}. Checking backup... {Styles.default}")
                primary_failed = True
        else:
            print(f"{Colors.RED}No processed JSON files found for {theater} in {theater_dir}. Checking backup... {Styles.default}")
            primary_failed = True

    # Check backup directory if primary file is missing or invalid
    if primary_failed and backup_theater_dir.exists():
        print(f"{Colors.YELLOW}Falling back to backup for {theater}... {Styles.default}")
        backup_files = sorted(
            backup_theater_dir.glob(f"{theater}_processed_*_latest_backup.json"),
            key=lambda x: datetime.strptime(x.name.split('_processed_')[1].split('_latest_backup')[0], "%Y%m%d_%H%M%S"),
            reverse=True
        )
        if backup_files:
            latest_backup_file = backup_files[0]
            try:
                with open(latest_backup_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if len(data) >= min_entries:
                    print(f"{Colors.GREEN}Loaded {len(data)} entries from {theater} backup ({latest_backup_file.name}) {Styles.default}")
                    return data
                else:
                    print(f"{Colors.YELLOW}{theater} backup file has {len(data)} entries (minimum {min_entries} required). Skipping... {Styles.default}")
            except (json.JSONDecodeError, Exception) as e:
                print(f"{Colors.RED}Failed to load or parse {theater} backup from {latest_backup_file.name}: {e} {Styles.default}")
        else:
            print(f"{Colors.RED}No backup file found for {theater} in {backup_theater_dir} {Styles.default}")
    elif primary_failed:
        print(f"{Colors.RED}Backup directory not found: {backup_theater_dir} {Styles.default}")
    return []

# Parse date and time from standardized format to datetime for sorting
def parse_datetime(entry):
    try:
        now = datetime.today()
        dt = datetime.strptime(f"{entry['date']} {entry['time']}", "%b %d %I:%M %p")
        dt = dt.replace(year=now.year)
        if dt < now:
            dt = dt.replace(year=now.year + 1)
        return dt
    except Exception as e:
        print(f"[DATETIME ERROR] {entry} – {e}")
        return None

# Main function to combine, filter, sort, and output showtimes to frontend
def main():
    print(f"\n\n{BG_Colors.MAGENTA_BG}{Styles.BOLD}{Styles.UNDERLINE} ///// Beginning Showings Combination Script ///// {Styles.default}\n\n")
    combined = []
    for theater in theaters:
        combined += load_json(theater)
    print(f"\n{Colors.BLUE}Total combined entries: {len(combined)} {Styles.default}")
    # Filter out blacklisted showings using raw titles
    filtered = [
        entry for entry in combined
        if (dt := parse_datetime(entry)) and today <= dt <= cutoff
        and entry['title'] not in BLACKLIST_SHOWINGS
    ]
    print(f"{Colors.BLUE}Entries within 30-day window (after blacklist): {len(filtered)} {Styles.default}")
    sorted_combined = sorted(filtered, key=parse_datetime)
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(sorted_combined, f, indent=1, ensure_ascii=False)
        print(f"\n{Colors.GREEN}{Styles.BLINK}Saved {len(sorted_combined)} sorted showings to {output_path.resolve()} {Styles.default}")
    except Exception as e:
        print(f"{BG_Colors.RED_BG}Failed to write output file: {e} {Styles.default}")
    print(f"\n\n{BG_Colors.GREEN_BG}{Styles.BOLD} ///// Showings Combination Complete ///// {Styles.default}\n\n")

if __name__ == '__main__':
    main()