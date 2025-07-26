import scrapy
from datetime import datetime

class AfiShowtimesSpider(scrapy.Spider):
    name = "afisilver"
    allowed_domains = ["silver.afi.com"]
    start_urls = ["https://silver.afi.com/now-playing/"]

    custom_settings = {
        "FEEDS": {
            "data/afimovies.json": {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True,
                "fields": ["title", "date", "time", "status", "theaterID"]
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
        # Extract movie detail page links from movie_item divs
        movie_links = response.css("div.movie_item a::attr(href)").getall()
        seen = set()
        for link in movie_links:
            if "/movies/detail/" in link and link not in seen:
                seen.add(link)
                yield scrapy.Request(
                    url=response.urljoin(link),
                    headers=self.custom_headers,
                    callback=self.parse_movie_detail
                )

    def parse_movie_detail(self, response):
        # Extract title from h1 in movie_shows div
        title = response.css("div.movie_shows h1::text").get()
        title = title.strip() if title else "Untitled"

        # Extract showtimes from show_wrap divs
        show_wrappers = response.css("div.movie_shows div.show_wrap")
        for wrapper in show_wrappers:
            # Extract date (e.g., "Sunday, August 24, 2025")
            raw_date = wrapper.css("p::text").get()
            if not raw_date:
                continue

            # Parse and format date to "Jul 24"
            try:
                # Remove weekday and year (e.g., "Sunday, August 24, 2025" -> "August 24")
                parts = raw_date.split(", ")
                if len(parts) >= 2:
                    date_str = parts[1].split(",")[0]  # Get "August 24"
                    dt = datetime.strptime(date_str, "%B %d")
                    formatted_date = dt.strftime("%b %d")
                else:
                    # Fallback: attempt to parse raw date directly
                    dt = datetime.strptime(raw_date.strip(), "%B %d")
                    formatted_date = dt.strftime("%b %d")
            except Exception:
                formatted_date = raw_date.strip()

            # Extract time (e.g., "8:15 p.m.")
            raw_time = wrapper.css("a.select_show span::text").get()
            if not raw_time:
                continue

            # Normalize time to "8:15 PM"
            try:
                time_clean = raw_time.replace("p.m.", "PM").replace("a.m.", "AM").strip()
                dt = datetime.strptime(time_clean, "%I:%M %p")
                formatted_time = dt.strftime("%I:%M %p")
            except Exception:
                formatted_time = raw_time.strip()

            yield {
                "title": title,
                "date": formatted_date,
                "time": formatted_time,
                "status": "available",
                "theaterID": "afisilver"
            }