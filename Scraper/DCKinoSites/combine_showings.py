import json
from datetime import datetime, timedelta
from pathlib import Path

# Base directory (where this script is located)
base_dir = Path(__file__).resolve().parent

# Input files
afi_path = base_dir / "data/afimovies.json"
miracle_path = base_dir / "data/miraclemovies.json"

# Output path: ../Site/dc-kino-site/src/data/movies.json
output_dir = base_dir.parent.parent / "Site/dc-kino-site/src/data"
output_path = output_dir / "movies.json"
output_dir.mkdir(parents=True, exist_ok=True)

# Load data
with open(afi_path, "r", encoding="utf-8") as f:
    afi_data = json.load(f)

with open(miracle_path, "r", encoding="utf-8") as f:
    miracle_data = json.load(f)

combined = afi_data + miracle_data

# Define time window
today = datetime.today()
one_month_from_now = today + timedelta(days=30)

# Helper to parse date with assumed current year
def parse_datetime(entry):
    try:
        dt_str = f"{entry['date']} {entry['time']} {today.year}"
        return datetime.strptime(dt_str, "%b %d %I:%M %p %Y")
    except Exception as e:
        print(f"Error parsing entry: {entry} — {e}")
        return None

# Filter and sort
filtered = [
    entry for entry in combined
    if (dt := parse_datetime(entry)) and today <= dt <= one_month_from_now
]

sorted_filtered = sorted(filtered, key=parse_datetime)

# Save output
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(sorted_filtered, f, indent=1, ensure_ascii=False)

print(f"{len(sorted_filtered)} showings written to {output_path.resolve()}")
