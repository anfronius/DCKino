import scrapy

class MiracleSpider(scrapy.Spider):
    name = "miracle"
    start_urls = ["http://themiracletheater.com/"]

    custom_settings = {
        "FEEDS": {
            "data/miraclemovies.json": {
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

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, headers=self.custom_headers, callback=self.parse)

    def parse(self, response):
        for card in response.css("div.col-md-3.col-sm-3"):
            title = card.css("h4.mec-event-title a.mec-color-hover::text").get()
            month = card.css("div.mec-event-month::text").get()
            day = card.css("div.mec-event-date::text").get()
            time = card.css("div.mec-event-time::text").get()

            date = f"{month.strip()} {day.strip()}" if month and day else ""

            if title:
                yield {
                    "title": title.strip(),
                    "date": date,
                    "time": time.strip() if time else "",
                    "location": "Miracle Theater"
                }