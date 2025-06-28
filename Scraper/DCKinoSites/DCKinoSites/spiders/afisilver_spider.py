import scrapy
import random
import time
from datetime import datetime

class AfiShowtimesSpider(scrapy.Spider):
    name = "afi"
    allowed_domains = ["silver.afi.com"]
    start_urls = [
        "https://silver.afi.com/Browsing/QuickTickets/Compare"
    ]

    custom_settings = {
        "FEEDS": {
            "data/afimovies.json": {
                "format": "json",
                "encoding": "utf-8",
                "fields": ["title", "date", "time", "location"]
            }
        }
    }

    custom_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Referer": "https://google.com",
    }

    def parse(self, response):
        self.logger.info("Loaded URL: %s", response.url)

        film_list = response.css("div.film-list.multi-date")

        for block in film_list:
            current_date = None

            for child in block.xpath("./*"):
                classes = child.xpath("@class").get(default="")

                if "date-group" in classes:
                    raw_date = child.xpath("text()").get(default="").strip()
                    try:
                        # Remove weekday name
                        parts = raw_date.split(" ", 1)
                        if len(parts) == 2:
                            raw_date = parts[1]
                        # Format from "27 June" to "Jun 27"
                        dt = datetime.strptime(raw_date, "%d %B")
                        current_date = dt.strftime("%b %d")
                    except Exception as e:
                        self.logger.warning(f"Date parsing error: {e}")
                        current_date = raw_date  # Fallback to raw text

                    continue

                if "film-item" in classes and current_date:
                    title = child.css("h3.film-title::text").get()
                    times = child.css("time::text").getall()
                    times = [t.strip() for t in times if t.strip()]

                    for t in times:
                        yield {
                            "title": title.strip() if title else None,
                            "date": current_date,
                            "time": t,
                            "location": "AFI Silver Theater"
                        }

        next_page = response.css("a.nextPage::attr(href)").get()
        if next_page:
            time.sleep(random.uniform(1, 2))
            yield response.follow(next_page, callback=self.parse)
