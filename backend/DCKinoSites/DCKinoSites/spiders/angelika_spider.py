import scrapy
from datetime import datetime
from scrapy_playwright.page import PageMethod

class AngelikaSpider(scrapy.Spider):
    name = "angelika"
    allowed_domains = ["angelikafilmcenter.com", "production-api.readingcinemas.com"]
    start_urls = ["https://angelikafilmcenter.com"]
    api_urls = {
        "https://production-api.readingcinemas.com/films?brandId=US&countryId=6&cinemaId=0000000007&status=getShows&flag=nowshowing&unique=popup",
        "https://production-api.readingcinemas.com/films?brandId=US&countryId=6&cinemaId=0000000006&status=getShows&flag=nowshowing&unique=mosaic"
    }
    theater_mapping = {
        "0000000007": "Angelika Popup",
        "0000000006": "Angelika Mosaic"
    }

    custom_settings = {
        'HTTPCACHE_ENABLED': False,
        "FEEDS": {
            f"data/angelika/angelika_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json": {"format": "json", "encoding": "utf-8", "overwrite": True}
        },
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 30000,
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
            "args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"]
        }
    }

    custom_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Origin": "https://angelikafilmcenter.com",
        "Referer": "https://angelikafilmcenter.com/",
    }

    async def start(self):
        self.logger.debug("Starting requests with Playwright enabled")
        yield scrapy.Request(
            url=self.start_urls[0],
            meta={
                "playwright": True,
                "playwright_include_page": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "domcontentloaded", timeout=10000),
                    PageMethod("wait_for_timeout", 5000),
                ],
            },
            callback=self.parse_page,
            errback=self.errback,
            dont_filter=True
        )

    async def parse_page(self, response):
        self.logger.debug(f"Response meta: {response.meta}")
        if "playwright_page" not in response.meta:
            self.logger.error("Playwright page not found in response.meta")
            return

        page = response.meta["playwright_page"]
        auth_token = None

        async def log_and_extract(route, request):
            nonlocal auth_token
            headers = request.headers
            auth_header = headers.get("authorization")
            if auth_header and "Bearer" in auth_header:
                auth_token = auth_header
            await route.continue_()

        await page.route("**/*", log_and_extract)
        await page.goto("https://angelikafilmcenter.com", wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        await page.close()

        api_headers = self.custom_headers.copy()
        if auth_token:
            api_headers["Authorization"] = auth_token
        else:
            self.logger.warning("No authorization token captured")

        for url in self.api_urls:
            theater_id = self.theater_mapping[url.split("cinemaId=")[1][:10]]
            yield scrapy.Request(
                url=url,
                headers=api_headers,
                callback=self.parse_api,
                meta={"theaterID": theater_id},
                dont_filter=True
            )

    async def errback(self, failure):
        self.logger.error(f"Request failed: {failure}")
        if "playwright_page" in failure.request.meta:
            page = failure.request.meta["playwright_page"]
            await page.close()

    def parse_api(self, response):
        data = response.json()
        theater_id = response.meta["theaterID"]
        movies = data["nowShowing"]["data"]["movies"]

        for film in movies:
            title = film["name"]
            for showdate in film["showdates"]:
                date_str = showdate["date"]
                for showtype in showdate["showtypes"]:
                    for showtime in showtype["showtimes"]:
                        dt = showtime["date_time"]
                        time_str = dt.split("T")[1]  # Extract time portion after 'T'
                        status = showtime["soldout"]
                        yield {
                            "title": title,
                            "date": date_str,
                            "time": time_str,
                            "status": status,
                            "theaterID": theater_id
                        }