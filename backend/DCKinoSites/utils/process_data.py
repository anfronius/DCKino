from pathlib import Path
from datetime import datetime
import json
import re

# Define paths
base_dir = Path(__file__).parent.parent
data_dir = base_dir / "data"

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

# Theater names
theaters = ["afisilver", "angelika", "avalon", "greenbelt", "landmark", "miracle", "suns", "lockmart"]

# Process afisilver data: date as 'Sunday, August 24, 2025', time as '8:15 p.m.' or '11:30 a.m.'
def process_afisilver(item):
    try:
        date_str = item["date"].replace(",", "").strip()
        dt = datetime.strptime(date_str, "%A %B %d %Y")
        std_date = dt.strftime("%b %d")
        time_str = item["time"].lower().replace(".", "").strip()
        dt = datetime.strptime(time_str, "%I:%M %p")
        std_time = dt.strftime("%I:%M %p").lstrip("0")
        return {
            "title": item["title"].strip(),
            "date": std_date,
            "time": std_time,
            "status": item["status"].strip(),
            "theaterID": item["theaterID"].strip().lower()
        }
    except Exception as e:
        print(f"{Colors.RED}Error processing afisilver item {item}: {e} {Styles.default}")
        return None

def process_angelika(item):
    try:
        # Standardize date from 'YYYY-MM-DD' to '%b %d'
        date_str = item["date"].strip()
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        std_date = dt.strftime("%b %d")

        # Standardize time: remove timezone (e.g., '-04') and convert to 12-hour format
        time_str = item["time"].split("-")[0].strip()  # Remove timezone (e.g., '21:45:00-04' -> '21:45:00')
        dt = datetime.strptime(time_str, "%H:%M:%S")
        std_time = dt.strftime("%I:%M %p").lstrip("0")

        # Standardize status: convert boolean to string
        status = "sold out" if item["status"] else "available"

        return {
            "title": item["title"].strip(),
            "date": std_date,
            "time": std_time,
            "status": status,
            "theaterID": item["theaterID"].strip().lower()
        }
    except Exception as e:
        print(f"{Colors.RED}Error processing angelika item {item}: {e} {Styles.default}")
        return None
    
# Process avalon data: date as '7/25/25', time as '12:45 P'
def process_avalon(item):
    try:
        date_str = item["date"].strip()
        dt = datetime.strptime(date_str, "%m/%d/%y")
        std_date = dt.strftime("%b %d")
        time_str = item["time"].lower().replace("p", "pm").replace("a", "am").strip()
        dt = datetime.strptime(time_str, "%I:%M %p")
        std_time = dt.strftime("%I:%M %p").lstrip("0")
        return {
            "title": item["title"].strip(),
            "date": std_date,
            "time": std_time,
            "status": item["status"].strip(),
            "theaterID": item["theaterID"].strip().lower()
        }
    except Exception as e:
        print(f"{Colors.RED}Error processing avalon item {item}: {e} {Styles.default}")
        return None

# Process greenbeltcinema data: date as '2025-08-09', time as '13:00:00', available as boolean
def process_greenbelt(item):
    try:
        # Standardize date from 'YYYY-MM-DD' to '%b %d'
        date_str = item["date"].strip()
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        std_date = dt.strftime("%b %d")

        # Standardize time from 'HH:MM:SS' to '%I:%M %p' without leading zero
        time_str = item["time"].strip()
        dt = datetime.strptime(time_str, "%H:%M:%S")
        std_time = dt.strftime("%I:%M %p").lstrip("0")

        # Standardize status: convert boolean to string
        status = "available" if item["available"] else "sold out"

        return {
            "title": item["title"].strip(),
            "date": std_date,
            "time": std_time,
            "status": status,
            "theaterID": item["theaterID"].strip().lower()
        }
    except Exception as e:
        print(f"{Colors.RED}Error processing greenbelt item {item}: {e} {Styles.default}")
        return None

# Process landmark data: date as '2025-08-26', time as '19:00:00'
def process_landmark(item):
    try:
        date_str = item["date"].strip()
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        std_date = dt.strftime("%b %d")
        time_str = item["time"].strip()
        dt = datetime.strptime(time_str, "%H:%M:%S")
        std_time = dt.strftime("%I:%M %p").lstrip("0")
        return {
            "title": item["title"].strip(),
            "date": std_date,
            "time": std_time,
            "status": item["status"].strip(),
            "theaterID": item["theaterID"].strip().lower()
        }
    except Exception as e:
        print(f"{Colors.RED}Error processing landmark item {item}: {e} {Styles.default}")
        return None

# Process lockmart data: date as '2025-08-04', time as '06:00pm'
def process_lockmart(item):
    try:
        date_str = item["date"].strip()
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        std_date = dt.strftime("%b %d")
        time_str = item["time"].lower().replace("am", " am").replace("pm", " pm").strip()
        dt = datetime.strptime(time_str, "%I:%M %p")
        std_time = dt.strftime("%I:%M %p").lstrip("0")
        return {
            "title": item["title"].strip(),
            "date": std_date,
            "time": std_time,
            "status": item["status"].strip(),
            "theaterID": item["theaterID"].strip().lower()
        }
    except Exception as e:
        print(f"{Colors.RED}Error processing lockmart item {item}: {e} {Styles.default}")
        return None

# Process miracle data: date as 'Jul 31 2025', time as '7:00 pm - 9:00 pm'
def process_miracle(item):
    try:
        date_str = item["date"].strip()
        dt = datetime.strptime(date_str, "%b %d %Y")
        std_date = dt.strftime("%b %d")
        time_str = item["time"].split("-")[0].lower().strip()  # Take start time
        dt = datetime.strptime(time_str, "%I:%M %p")
        std_time = dt.strftime("%I:%M %p").lstrip("0")
        return {
            "title": item["title"].strip(),
            "date": std_date,
            "time": std_time,
            "status": item["status"].strip(),
            "theaterID": item["theaterID"].strip().lower()
        }
    except Exception as e:
        print(f"{Colors.RED}Error processing miracle item {item}: {e} {Styles.default}")
        return None

# Process suns data: date as 'Fri, Aug 1', time as '6:00 pm'
def process_suns(item):
    try:
        date_str = item["date"].replace(",", "").strip()
        dt = datetime.strptime(date_str, "%a %b %d")
        std_date = dt.strftime("%b %d")
        time_str = item["time"].lower().strip()
        dt = datetime.strptime(time_str, "%I:%M %p")
        std_time = dt.strftime("%I:%M %p").lstrip("0")
        return {
            "title": item["title"].strip(),
            "date": std_date,
            "time": std_time,
            "status": item["status"].strip(),
            "theaterID": item["theaterID"].strip().lower()
        }
    except Exception as e:
        print(f"{Colors.RED}Error processing suns item {item}: {e} {Styles.default}")
        return None

# Process a single JSON file using theater-specific function
def process_json_file(json_file, theater):
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        processor_map = {
            "afisilver": process_afisilver,
            "angelika": process_angelika,
            "avalon": process_avalon,
            "landmark": process_landmark,
            "miracle": process_miracle,
            "suns": process_suns,
            "lockmart": process_lockmart,
            "greenbelt": process_greenbelt
        }
        processor = processor_map.get(theater)
        if not processor:
            print(f"{Colors.RED}No processor defined for theater {theater} {Styles.default}")
            return
        standardized_data = []
        for item in data if isinstance(data, list) else [data]:
            std_item = processor(item)
            if std_item:
                standardized_data.append(std_item)
        if standardized_data:
            output_filename = json_file.name.replace("_raw_", "_processed_")
            output_path = json_file.parent / output_filename
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(standardized_data, f, indent=2)
            print(f"{Colors.GREEN}Processed {json_file.name} -> {output_filename} {Styles.default}")
        else:
            print(f"{Colors.RED}No valid data to process in {json_file.name} {Styles.default}")
    except json.JSONDecodeError:
        print(f"{Colors.RED}Failed to read {json_file.name}: Invalid JSON format {Styles.default}")
    except Exception as e:
        print(f"{Colors.RED}Failed to process {json_file.name}: {e} {Styles.default}")

# Main function to process theater JSONs from their various formats to uniform format
def main():
    print(f"\n\n{BG_Colors.MAGENTA_BG}{Styles.BOLD}{Styles.UNDERLINE} ///// Beginning Data Processing Script ///// {Styles.default}\n\n")
    for theater in theaters:
        theater_dir = data_dir / theater
        if not theater_dir.exists():
            print(f"{Colors.RED}Directory not found: {theater_dir} {Styles.default}")
            continue
        for json_file in theater_dir.glob("*_raw_*.json"):
            if json_file.is_file():
                process_json_file(json_file, theater)
    print(f"\n\n{BG_Colors.GREEN_BG}{Styles.BOLD} ///// Data Processing Complete ///// {Styles.default}\n\n")

if __name__ == '__main__':
    main()