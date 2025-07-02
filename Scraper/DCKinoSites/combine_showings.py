import json
from datetime import datetime, timedelta
from pathlib import Path

# Base directory (where this script is located)
base_dir = Path(__file__).resolve().parent

# Input files
afi_path = base_dir / "data/afimovies.json"
miracle_path = base_dir / "data/miraclemovies.json"
suns_path = base_dir / "data/sunsmovies.json"
avalon_path = base_dir / "data/avalonmovies.json"

# Output file (to site's data folder)
output_dir = base_dir.parent.parent / "Site/dc-kino-site/src/data"
output_path = output_dir / "movies.json"
output_dir.mkdir(parents=True, exist_ok=True)

print("🔍 Loading JSON data...")

# Load and merge
def load_json(path, label):
    if not path.exists():
        print(f"⚠️  {label} file not found at {path}")
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"✅ Loaded {len(data)} entries from {label}")
            return data
    except Exception as e:
        print(f"❌ Failed to load {label}: {e}")
        return []

afi_data = load_json(afi_path, "AFI")
miracle_data = load_json(miracle_path, "Miracle")
suns_data = load_json(suns_path, "Suns")
avalon_data = load_json(avalon_path, "Avalon")

combined = afi_data + miracle_data + suns_data + avalon_data
print(f"🔗 Total combined entries: {len(combined)}")

# Normalize time format to "HH:MM PM"
def normalize_time(t):
    try:
        return datetime.strptime(t.strip().lower(), "%I:%M %p").strftime("%I:%M %p")
    except Exception as e:
        print(f"[TIME ERROR] '{t}' – {e}")
        return t

for entry in combined:
    entry["time"] = normalize_time(entry["time"])

# Filter: only keep showings within next 60 days
def parse_datetime(entry):
    try:
        now = datetime.today()
        dt = datetime.strptime(f"{entry['date']} {entry['time']}", "%b %d %I:%M %p")
        dt = dt.replace(year=now.year)

        # If this parsed date is earlier than today, assume it's for next year
        if dt < now:
            dt = dt.replace(year=now.year + 1)

        return dt
    except Exception as e:
        print(f"[DATETIME ERROR] {entry} – {e}")
        return None

today = datetime.today()
cutoff = today + timedelta(days=30)

filtered = [
    entry for entry in combined
    if (dt := parse_datetime(entry)) and today <= dt <= cutoff
]

print(f"🧹 Entries within 30-day window: {len(filtered)}")

# Sort chronologically
sorted_combined = sorted(filtered, key=parse_datetime)

# Save result
try:
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sorted_combined, f, indent=1, ensure_ascii=False)
    print(f"✅ Saved {len(sorted_combined)} sorted showings to {output_path.resolve()}")
except Exception as e:
    print(f"❌ Failed to write output file: {e}")
