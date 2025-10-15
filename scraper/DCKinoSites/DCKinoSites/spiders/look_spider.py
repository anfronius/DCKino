import scrapy
from scrapy_playwright.page import PageMethod
from datetime import datetime
import os

class LookCinemasSpider(scrapy.Spider):
    name = "lookcinemas"
    allowed_domains = ["www.lookcinemas.com"]
    start_urls = ["https://www.lookcinemas.com/"]

    async def start(self):
        yield scrapy.Request(
            url=self.start_urls[0],
            meta={
                "playwright": True,
                "playwright_page_methods": [
                    PageMethod("wait_for_load_state", "networkidle", timeout=30000),
                    PageMethod("wait_for_selector", "div.swiperow.splide button[value]", timeout=30000),
                ],
                "playwright_include_page": True,
            },
            callback=self.parse_dates,
        )

    async def parse_dates(self, response):
        page = response.meta.get("playwright_page")
        if not page:
            self.logger.error("No Playwright page available")
            return

        try:
            # Save the full DOM for debugging
            html_content = await page.content()
            debug_file = f"data/lookcinemas/lookcinemas_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            os.makedirs(os.path.dirname(debug_file), exist_ok=True)
            with open(debug_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            self.logger.info(f"Saved page DOM to {debug_file}")

            # Get date buttons with value attribute (e.g., 2025-08-09)
            date_buttons = await page.query_selector_all("div.swiperow.splide button[value]")
            self.logger.info(f"Found {len(date_buttons)} date buttons")

            # Limit to 7 days or available buttons
            for i in range(min(len(date_buttons), 7)):
                # Re-fetch buttons to avoid stale elements
                date_buttons = await page.query_selector_all("div.swiperow.splide button[value]")
                if i >= len(date_buttons):
                    self.logger.warning(f"No button found at index {i}")
                    continue

                button = date_buttons[i]
                date_value = await button.get_attribute("value")
                self.logger.info(f"Processing date: {date_value}")

                # Ensure button is visible and clickable
                await button.scroll_into_view_if_needed()
                await button.wait_for_element_state("visible", timeout=10000)

                # Click the date button
                await button.click()
                await page.wait_for_timeout(3000)  # Wait for showtimes to load

                # Create a new response for Scrapy to parse the updated page
                html = await page.content()
                new_response = response.replace(body=html.encode("utf-8"))

                # Extract showtimes
                showtime_items = new_response.css(".showtime-item")  # Adjust selector
                if not showtime_items:
                    self.logger.warning(f"No showtime items found for date: {date_value}")
                
                for showtime in showtime_items:
                    yield {
                        "title": showtime.css(".movie-title::text").get(default="").strip(),
                        "date": date_value,
                        "time": showtime.css(".showtime-time::text").get(default="").strip(),
                        "status": showtime.css(".showtime-status::text").get(default="available").strip(),
                        "theaterID": "lookcinemas",
                    }

        except Exception as e:
            self.logger.error(f"Error processing page: {str(e)}")
        finally:
            if page:
                await page.close()
                self.logger.info("Playwright page closed")

    def parse(self, response):
        # Fallback for initial page if parse_dates fails
        date_value = response.css("input#swiperow-date::attr(value)").get(default=datetime.now().strftime("%Y-%m-%d"))
        showtime_items = response.css(".showtime-item")
        if not showtime_items:
            self.logger.warning(f"No showtime items found in fallback parse for date: {date_value}")
        
        for showtime in showtime_items:
            yield {
                "title": showtime.css(".movie-title::text").get(default="").strip(),
                "date": date_value,
                "time": showtime.css(".showtime-time::text").get(default="").strip(),
                "status": showtime.css(".showtime-status::text").get(default="available").strip(),
                "theaterID": "lookcinemas",
            }