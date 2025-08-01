import scrapy
from datetime import datetime

class AfiShowtimesSpider(scrapy.Spider):
    name = "afisilver"
    allowed_domains = ["silver.afi.com"]
    start_urls = ["https://silver.afi.com/now-playing/"]

    custom_settings = {
        "FEEDS": {
            f"data/afisilver/afi_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json": {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True,
                "fields": ["title", "date", "time", "status", "theaterID"],
            }
        }
    }

    def start_requests(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        }
        yield scrapy.Request(self.start_urls[0], headers=headers, callback=self.parse)

    def parse(self, response):
        seen = set()
        for link in response.css("div.movie_item a::attr(href)").getall():
            if "/movies/detail/" in link and link not in seen:
                seen.add(link)
                yield scrapy.Request(
                    url=response.urljoin(link),
                    headers=response.request.headers,
                    callback=self.parse_movie_detail,
                )

    def parse_movie_detail(self, response):
        title = response.css("div.movie_shows h1::text").get()
        for wrapper in response.css("div.movie_shows div.show_wrap"):
            date = wrapper.css("p::text").get()
            time = wrapper.css("a.select_show span::text").get()
            if title and date and time:
                yield {
                    "title": title,
                    "date": date,
                    "time": time,
                    "status": "available",
                    "theaterID": "afisilver",
                }