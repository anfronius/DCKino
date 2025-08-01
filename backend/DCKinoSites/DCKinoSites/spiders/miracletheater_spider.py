import scrapy
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser


class MiracleSpider(scrapy.Spider):
    name = "miracle"
    allowed_domains = ["themiracletheatre.com"]
    sitemap_url = "https://themiracletheatre.com/wp-sitemap-posts-mec-events-1.xml"

    custom_settings = {
        "FEEDS": {
            f"data/miracle/miracle_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json": {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True,
                "fields": ["title", "date", "time", "status", "theaterID"]
            }
        }
    }

    custom_headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }

    def start_requests(self):
        yield scrapy.Request(
            url=self.sitemap_url,
            callback=self.parse_sitemap,
            headers=self.custom_headers
        )

    def parse_sitemap(self, response):
        today = datetime.now(timezone.utc).date()
        yesterday = today - timedelta(days=1)
        ns = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        for url_node in response.xpath("//ns:url", namespaces=ns):
            loc = url_node.xpath("ns:loc/text()", namespaces=ns).get()
            lastmod_raw = url_node.xpath("ns:lastmod/text()", namespaces=ns).get()

            if not loc or not lastmod_raw:
                continue

            try:
                lastmod_dt = dateparser.parse(lastmod_raw)
                lastmod_date = lastmod_dt.astimezone(timezone.utc).date()

                if lastmod_date in (today, yesterday):
                    yield scrapy.Request(
                        url=loc,
                        callback=self.parse_event_page,
                        headers=self.custom_headers
                    )
            except Exception:
                continue

    def parse_event_page(self, response):
        title = response.css("h1.mec-single-title::text").get()
        date = response.css("div.mec-single-event-date span::text").get()
        time = response.css("div.mec-single-event-time abbr.mec-events-abbr::text").get()

        yield {
            "title": title.strip() if title else "",
            "date": date.strip() if date else "",
            "time": time.strip() if time else "",
            "status": "available",
            "theaterID": "miracle"
        }