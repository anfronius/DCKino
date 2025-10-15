import scrapy
from datetime import date, timedelta, datetime

class LockheedMartinSpider(scrapy.Spider):
    name = "lockmart"
    allowed_domains = ["si.edu"]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "FEEDS": {
            f"data/lockmart/lockmart_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json": {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True,
                "fields": ["title", "date", "time", "status", "theaterID"]
            }
        }
    }

    custom_headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }

    def start_requests(self):
        start_date = date.today()
        for i in range(31):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.strftime('%Y-%m-%d')
            url = f"https://www.si.edu/theaters/lockheedmartin?field_day_value={date_str}"
            yield scrapy.Request(url=url, headers=self.custom_headers)

    def parse(self, response):
        date_param = response.url.split('=')[-1]
        for film_block in response.css('ul.listing section.c-film-teaser'):
            title = film_block.css('h2.c-film-teaser__title a span.text::text').get()
            if not title:
                continue
            title = title.strip()

            showtimes = film_block.css('li.c-film-teaser__time--upcoming a::text').getall()
            for showtime in showtimes:
                showtime = showtime.strip()
                if showtime:
                    yield {
                        'title': title,
                        'date': date_param,
                        'time': showtime,
                        'status': 'available',
                        'theaterID': 'lockheedmartin'
                    }