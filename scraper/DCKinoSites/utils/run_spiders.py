import sys
from pathlib import Path
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
import requests
import os


# Add parent directory to Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

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

# Spider list
SPIDERS = ['afisilver', 'angelika', 'avalon', 'greenbelt', 'landmark', 'lockmart', 'miracle', 'suns']

# Main function to run spiders
def main():
    print(f"\n\n{BG_Colors.MAGENTA_BG}{Styles.BOLD}{Styles.UNDERLINE} ///// Beginning Spider Crawl Script ///// {Styles.default}{Colors.YELLOW}\n\n")
    print(f"{Colors.BLUE}Initializing crawler settings... {Colors.YELLOW}\n")
    settings = get_project_settings()
    process = CrawlerProcess(settings)
    print(f"\n")
    for spider_name in SPIDERS:
        print(f"{Colors.BLUE}Priming {spider_name} spider... {Colors.YELLOW}\n")
        process.crawl(spider_name)
        print(f"\n{Colors.GREEN}{Styles.BLINK}{spider_name}Spider primed {Styles.default}")
    print(f"{Colors.BLUE}Initializing crawl... {Colors.YELLOW}\n")
    process.start()
    print(f"{Styles.default}")
    print(f"\n\n{BG_Colors.GREEN_BG}{Styles.BOLD} ///// Spider Crawl Complete ///// {Styles.default}\n\n")

    # Trigger backend data processing pipeline
    backend_url = os.getenv("BACKEND_API_URL", "http://backend:3001")
    print(f"{Colors.BLUE}Triggering backend data processing pipeline at {backend_url}/api/run-pipeline...{Colors.YELLOW}\n")

    try:
        response = requests.post(f"{backend_url}/api/run-pipeline", timeout=600)  # 10 minute timeout
        if response.status_code == 200:
            result = response.json()
            print(f"{Colors.GREEN}Backend pipeline completed successfully!{Styles.default}")
            print(f"{Colors.BLUE}Pipeline results:{Styles.default}")
            if "results" in result:
                for step, step_result in result["results"].items():
                    status = "✓" if step_result.get("success") else "✗"
                    print(f"  {status} {step.capitalize()}: {'Success' if step_result.get('success') else 'Failed'}")
            print(f"\n{BG_Colors.GREEN_BG}{Styles.BOLD} ///// Full Pipeline Complete ///// {Styles.default}\n\n")
        else:
            print(f"{Colors.RED}Backend pipeline failed with status {response.status_code}: {response.text}{Styles.default}")
            print(f"{Colors.YELLOW}You may need to run backend processing manually.{Styles.default}\n")
    except requests.exceptions.ConnectionError:
        print(f"{Colors.YELLOW}Could not connect to backend at {backend_url}{Styles.default}")
        print(f"{Colors.YELLOW}Backend may not be running. Run processing manually if needed.{Styles.default}\n")
    except requests.exceptions.Timeout:
        print(f"{Colors.YELLOW}Backend pipeline timed out after 10 minutes{Styles.default}")
        print(f"{Colors.YELLOW}Processing may still be running on backend. Check backend logs.{Styles.default}\n")
    except Exception as e:
        print(f"{Colors.RED}Error triggering backend pipeline: {str(e)}{Styles.default}")
        print(f"{Colors.YELLOW}You may need to run backend processing manually.{Styles.default}\n")

if __name__ == '__main__':
    main()