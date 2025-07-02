import scrapy
from datetime import datetime

class AvalonSpider(scrapy.Spider):
    name = "avalon"
    allowed_domains = ["theavalon.org", "prod5.agileticketing.net"]
    start_urls = ["https://www.theavalon.org/films/"]

    custom_settings = {
        "FEEDS": {
            "data/avalonmovies.json": {
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

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url, headers=self.custom_headers, callback=self.parse_main)

    def parse_main(self, response):
        movie_links = response.css("div.filmblock a::attr(href)").getall()
        seen = set()
        for link in movie_links:
            if "/films/" in link and link not in seen:
                seen.add(link)
                yield scrapy.Request(
                    url=response.urljoin(link),
                    headers=self.custom_headers,
                    callback=self.parse_movie_detail
                )

    def parse_movie_detail(self, response):
        title = response.css("h1::text").get()
        ticket_url = response.css("a.btn-tix::attr(href)").get()

        if ticket_url:
            yield scrapy.Request(
                url=response.urljoin(ticket_url),
                headers=self.custom_headers,
                callback=self.parse_ticketing_page,
                cb_kwargs={"title": title.strip() if title else "Untitled"},
            )

    def parse_ticketing_page(self, response, title):
        filename = f"debug-ticketing-{title.replace(' ', '_').lower()}.html"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response.text)

        showtimes = response.css("div.ButtonGroup::attr(data-agl_date)").getall()
        for raw in showtimes:
            cleaned = raw.strip().replace(" A", " AM").replace(" P", " PM")
            try:
                dt = datetime.strptime(cleaned, "%m/%d/%y %I:%M %p")
                yield {
                    "title": title,
                    "date": dt.strftime("%b %d"),
                    "time": dt.strftime("%-I:%M %p").lower(),
                    "status": "available",
                    "theaterID": "avalon"
                }
            except Exception as e:
                self.logger.warning(f"Skipping bad date '{raw}' for {title}: {e}")
