import scrapy
from datetime import datetime

class AvalonSpider(scrapy.Spider):
    name = "avalon"
    allowed_domains = ["theavalon.org", "prod5.agileticketing.net"]
    start_urls = ["https://www.theavalon.org/films/"]

    custom_settings = {
        "FEEDS": {
            f"data/avalon/avalon_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json": {
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
        yield scrapy.Request(self.start_urls[0], headers=headers, callback=self.parse_main)

    def parse_main(self, response):
        seen = set()
        for link in response.css("div.filmblock a::attr(href)").getall():
            if "/films/" in link and link not in seen:
                seen.add(link)
                yield scrapy.Request(
                    url=response.urljoin(link),
                    headers=response.request.headers,
                    callback=self.parse_movie_detail,
                )

    def parse_movie_detail(self, response):
        title = response.css("h1::text").get()
        ticket_url = response.css("a.btn-tix::attr(href)").get()
        if title and ticket_url:
            yield scrapy.Request(
                url=response.urljoin(ticket_url),
                headers=response.request.headers,
                callback=self.parse_ticketing_page,
                cb_kwargs={"title": title},
            )

    def parse_ticketing_page(self, response, title):
        for show in response.css("div.ButtonGroup::attr(data-agl_date)").getall():
            if show:
                try:
                    date, time = show.split(" ", 1)
                    yield {
                        "title": title,
                        "date": date,
                        "time": time,
                        "status": "available",
                        "theaterID": "avalon",
                    }
                except ValueError:
                    continue