import sys
from pathlib import Path
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings


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
SPIDERS = ['afisilver', 'angelika', 'avalon', 'landmark', 'miracle', 'suns']

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

if __name__ == '__main__':
    main()