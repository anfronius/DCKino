import json
from datetime import datetime, timedelta
from pathlib import Path

# Base directory (where this script is located)
base_dir = Path(__file__).resolve().parent.parent

# Input files
afi_path = base_dir / "data/afimovies.json"
miracle_path = base_dir / "data/miraclemovies.json"
suns_path = base_dir / "data/sunsmovies.json"
avalon_path = base_dir / "data/avalonmovies.json"
landmark_path = base_dir / "data/landmarkmovies.json"

# Output file (to site's data folder)
output_dir = base_dir.parent.parent/ "frontend/src/data"
output_path = output_dir / "movies.json"
output_dir.mkdir(parents=True, exist_ok=True)

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

# Function which loads JSON data from a primary path. If the file doesn't exist, is empty, or has fewer than min_entries, it attempts to load from a backup file, then merges
def load_json(path, label, min_entries=5):
    backup_path = base_dir / "data_backup" / f"{path.stem}_backup.json"
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if len(data) >= min_entries:
                print(f"{Colors.GREEN}Loaded {len(data)} entries from {label} ({path.name}) {Styles.default}")
                return data
            else:
                print(f"{Colors.YELLOW}{label} file has {len(data)} entries (minimum {min_entries} required). Trying backup... {Styles.default}")
        except (json.JSONDecodeError, Exception) as e:
            print(f"{Colors.RED}Failed to load or parse {label} from {path.name}: {e}. Trying backup... {Styles.default}")
    if backup_path.exists():
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"{Colors.GREEN}Loaded {len(data)} entries from {label} backup ({backup_path.name}) {Styles.default}")
            return data
        except Exception as e:
            print(f"{Colors.RED}Failed to load {label} from backup {backup_path.name}: {e} {Styles.default}")
            return []
    print(f"{BG_Colors.RED_BG}Could not load sufficient data for {label} from primary or backup paths. {Styles.default}")
    return []

# Function to normalize time format to "HH:MM PM"
def normalize_time(t):
    try:
        return datetime.strptime(t.strip().lower(), "%I:%M %p").strftime("%I:%M %p")
    except Exception as e:
        print(f"[TIME ERROR] '{t}' – {e}")
        return t

# Function to only keep showings within next 60 days and assumes showtimes with a date earlier than today is for next year instead
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

print(f"\n\n{BG_Colors.MAGENTA_BG}{Styles.BOLD}{Styles.UNDERLINE} ///// Beginning Showings Combination Script ///// {Styles.default}\n\n")

# Load all JSON files
afi_data = load_json(afi_path, "AFI")
miracle_data = load_json(miracle_path, "Miracle")
suns_data = load_json(suns_path, "Suns")
avalon_data = load_json(avalon_path, "Avalon")
landmark_data = load_json(landmark_path, "Landmark")

# Combine all data
combined = afi_data + miracle_data + suns_data + avalon_data + landmark_data
print(f"\n{Colors.BLUE}Total combined entries: {len(combined)} {Styles.default}")

# Normalize times
for entry in combined:
    entry["time"] = normalize_time(entry["time"])

# Filter for relevency
filtered = [
    entry for entry in combined
    if (dt := parse_datetime(entry)) and today <= dt <= cutoff
]
print(f"{Colors.BLUE}Entries within 30-day window: {len(filtered)} {Styles.default}")

# Sort chronologically
sorted_combined = sorted(filtered, key=parse_datetime)

# Save result
try:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sorted_combined, f, indent=1, ensure_ascii=False)
    print(f"\n{Colors.GREEN}{Styles.BLINK}Saved {len(sorted_combined)} sorted showings to {output_path.resolve()} {Styles.default}")
except Exception as e:
    print(f"{BG_Colors.RED_BG}Failed to write output file: {e} {Styles.default}")

print(f"\n\n{BG_Colors.GREEN_BG}{Styles.BOLD} ///// Showings Combination Complete ///// {Styles.default}\n\n")