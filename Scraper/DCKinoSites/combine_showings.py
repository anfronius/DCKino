import json
from datetime import datetime
from pathlib import Path

# Base directory (where this script is located)
base_dir = Path(__file__).resolve().parent

# Input files (relative to this script location)
afi_path = base_dir / "data/afimovies.json"
miracle_path = base_dir / "data/miraclemovies.json"

# Output path: go up two levels, then into Site/dc-kino-site/src/data
output_dir = base_dir.parent.parent / "Site/dc-kino-site/src/data"
output_path = output_dir / "movies.json"

# Ensure output directory exists
output_dir.mkdir(parents=True, exist_ok=True)

# Load input data
with open(afi_path, "r", encoding="utf-8") as f:
    afi_data = json.load(f)

with open(miracle_path, "r", encoding="utf-8") as f:
    miracle_data = json.load(f)

combined = afi_data + miracle_data

# Helper to sort by parsed datetime
def parse_datetime(entry):
    try:
        dt_str = f"{entry['date']} {entry['time']}"
        return datetime.strptime(dt_str, "%b %d %I:%M %p")
    except Exception as e:
        print(f"Error parsing: {entry} – {e}")
        return datetime.max

# Sort by datetime
sorted_combined = sorted(combined, key=parse_datetime)

# Write output
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(sorted_combined, f, indent=1, ensure_ascii=False)

print(f"Sorted output written to {output_path.resolve()}")
