import scrapy
from pathlib import Path
from datetime import datetime

class SunsCinemaSpider(scrapy.Spider):
    name = "suns"
    allowed_domains = ["sunscinema.com"]
    start_urls = ["https://sunscinema.com/upcoming-films-3/"]

    custom_settings = {
        "FEEDS": {
            "data/sunsmovies.json": {
                "format": "json",
                "encoding": "utf-8",
                "fields": ["title", "date", "time", "status", "theaterID"],
                "overwrite": True
            }
        }
    }

    def parse(self, response):
        # Save HTML for debugging
        debug_path = Path("data/suns_debug.html")
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        debug_path.write_text(response.text, encoding="utf-8")
        self.logger.info(f"Saved HTML response to {debug_path.resolve()}")

        # Loop through each movie block
        movie_blocks = response.css("div.showtimes-description")

        for block in movie_blocks:
            # Extract title
            title = block.css("h2.show-title a.title::text").get()
            title = title.strip() if title else None

            # Extract date list
            date_list = block.css("ul.datelist li")
            if not date_list:
                continue

            for date_item in date_list:
                raw_date = date_item.css("span::text").get()
                if not raw_date:
                    continue

                try:
                    parts = raw_date.replace(",", "").split()
                    if len(parts) >= 3:
                        dt = datetime.strptime(f"{parts[1]} {parts[2]}", "%b %d")
                        date = dt.strftime("%b %d")
                    else:
                        date = raw_date.strip()
                except Exception as e:
                    self.logger.warning(f"Date parsing issue: {e}")
                    date = raw_date.strip()

                # Get all showtime buttons under the current block
                showtimes = block.css("a.showtime, span.showtime")
                for st in showtimes:
                    time = st.css("::text").get()
                    if not time or not date:
                        continue

                    status = "sold out" if "sold-out" in st.attrib.get("class", "") else "available"

                    yield {
                        "title": title,
                        "date": date,
                        "time": time.strip(),
                        "status": status,
                        "theaterID": "suns"
                    }
