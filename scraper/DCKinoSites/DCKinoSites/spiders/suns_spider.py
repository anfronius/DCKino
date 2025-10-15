import scrapy
import re
from datetime import datetime

class SunsCinemaSpider(scrapy.Spider):
    name = "suns"
    allowed_domains = ["sunscinema.com"]
    start_urls = ["https://sunscinema.com/upcoming-films-3/"]

    custom_settings = {
        "FEEDS": {
            f"data/suns/suns_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json": {
                "format": "json",
                "encoding": "utf-8",
                "fields": ["title", "date", "time", "status", "theaterID"],
                "overwrite": True,
            }
        }
    }

    def parse(self, response):
        movie_blocks = response.css("div.showtimes-description")

        for block in movie_blocks:
            title = block.css("h2.show-title a.title::text").get()
            if not title:
                continue

            date_list = block.css("ul.datelist li")
            if not date_list:
                continue

            for date_item in date_list:
                date = date_item.css("span::text").get()
                if not date:
                    continue

                showtimes = block.css("a.showtime, span.showtime")
                for showtime in showtimes:
                    time = showtime.css("::text").get()
                    if not time:
                        continue

                    cleaned_time = re.sub(r"[\n\t\r]+", "", time) if time else time

                    status = (
                        "sold out"
                        if "sold-out" in showtime.attrib.get("class", "")
                        else "available"
                    )

                    yield {
                        "title": title,
                        "date": date,
                        "time": cleaned_time,
                        "status": status,
                        "theaterID": "suns",
                    }