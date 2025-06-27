import scrapy

class AfiShowtimesSpider(scrapy.Spider):
    name = "afi_showtimes"
    allowed_domains = ["silver.afi.com"]
    start_urls = [
        "https://silver.afi.com/Browsing/QuickTickets/Compare"
    ]

    def parse(self, response):
        # Look at the page structure — for each showing block
        for show in response.css("div.showingItem, li.showingItem"):
            title = show.css(".movieTitle::text").get() or show.css(".title::text").get()
            # Date might be somewhere like data-date attr or in a nested container
            date = show.css("::attr(data-date)").get()
            if not date:
                date = show.css(".showDate::text").get()

            # Multiple showtimes possible – loop times
            times = show.css(".showtime::text").getall()
            # Clean up whitespace
            times = [t.strip() for t in times if t.strip()]

            for t in times:
                yield {
                    "title": title.strip() if title else None,
                    "date": date.strip() if date else None,
                    "time": t
                }

        # If the page uses pagination or “Load more showings” links:
        next_page = response.css("a.nextPage::attr(href)").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
