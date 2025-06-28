import json
from datetime import datetime
from pathlib import Path

# File paths
afi_path = Path("data/afimovies.json")       # or Path("data/afi_output.json")
miracle_path = Path("data/miraclemovies.json")
output_path = Path("data/combined_sorted_showings.json")

# Load JSON data
with open(afi_path, "r", encoding="utf-8") as f:
    afi_data = json.load(f)

with open(miracle_path, "r", encoding="utf-8") as f:
    miracle_data = json.load(f)

combined = afi_data + miracle_data

def parse_datetime(entry):
    try:
        dt_str = f"{entry['date']} {entry['time']}"
        return datetime.strptime(dt_str, "%b %d %I:%M %p")
    except Exception as e:
        print(f"Error parsing: {entry} – {e}")
        return datetime.max

# Sort by date then time
sorted_combined = sorted(combined, key=parse_datetime)

# Write to output
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(sorted_combined, f, indent=1, ensure_ascii=False)

print(f"Sorted output written to {output_path.resolve()}")
