import scrapy
from scrapy_playwright.page import PageMethod
from scrapy.selector import Selector
from datetime import datetime
import asyncio

class GreenbeltCinemaSpider(scrapy.Spider):
    name = "greenbelt"
    allowed_domains = ["greenbeltcinema.org"]
    start_urls = ["https://www.greenbeltcinema.org/home/"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.processed_dates = {"4", "5", "6", "7"}  # Track first four days as processed

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "HTTPCACHE_ENABLED": False,
        "FEEDS": {
            f"data/greenbelt/greenbelt_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json": {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True
            }
        },
        "PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT": 120000,
        "PLAYWRIGHT_BROWSER_TYPE": "chromium",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {
            "headless": True,
            "args": ["--no-sandbox", "--disable-setuid-sandbox", "--disable-blink-features=AutomationControlled"]
        }
    }

    custom_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }

    async def start(self):
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                headers=self.custom_headers,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "playwright_page_methods": [
                        PageMethod("wait_for_load_state", "networkidle"),
                        PageMethod("wait_for_selector", "div[data-test-id='showtimes-by-film-movie-container']", state="attached", timeout=30000),
                    ],
                },
                callback=self.parse
            )

    async def parse(self, response):
        if "playwright_page" not in response.meta:
            self.logger.error("Playwright page not found in response.meta")
            return

        page = response.meta["playwright_page"]
        
        # Capture browser console errors and network requests for debugging
        page.on("console", lambda msg: self.logger.warning(f"Browser console: {msg.text}"))
        page.on("request", lambda req: self.logger.debug(f"Request: {req.method} {req.url}"))
        page.on("response", lambda res: self.logger.debug(f"Response: {res.status} {res.url}"))
        
        try:
            # Wait for the calendar filter to be loaded
            await page.wait_for_selector('.calendar-filter ul li', timeout=30000)
            
            # Process initial visible dates (Today, Tue, Wed, Thu)
            initial_calendar_items = await page.query_selector_all('.calendar-filter ul li:not(.calendar)')
            self.logger.info(f"Found {len(initial_calendar_items)} initial calendar items")
            
            for i, calendar_item in enumerate(initial_calendar_items):
                try:
                    date_text = await calendar_item.text_content()
                    self.logger.info(f"Processing initial calendar item {i+1}: {date_text}")
                    
                    # Click on the calendar date
                    self.logger.debug(f"Attempting to click initial calendar item: {date_text}")
                    await calendar_item.click()
                    self.logger.debug(f"Successfully clicked initial calendar item: {date_text}")
                    
                    # Wait for content to update
                    await page.wait_for_timeout(3000)
                    await page.wait_for_selector('div[data-test-id="showtimes-by-film-movie-container"]', timeout=15000)
                    
                    # Parse showings for this date
                    html_content = await page.content()
                    async for item in self.parse_showings(html_content, date_text):
                        yield item
                        
                except Exception as e:
                    self.logger.error(f"Error processing initial calendar item {i+1} ({date_text}): {e}")
                    continue
            
            # Click on the "Other Date" calendar button to open the full calendar
            calendar_button = await page.query_selector('.calendar-filter ul li.calendar')
            if calendar_button:
                self.logger.info("Found 'Other Date' calendar button")
                self.logger.debug("Attempting to click 'Other Date' calendar button")
                await calendar_button.click()
                self.logger.debug("Successfully clicked 'Other Date' calendar button")
                
                # Wait for the calendar popup to appear
                await page.wait_for_timeout(5000)
                await page.wait_for_selector('.q-date__calendar-item--in button', timeout=15000, state="visible")
                
                # Process dates one at a time, re-querying buttons each time
                while True:
                    # Get fresh list of clickable date buttons
                    calendar_date_buttons = await page.query_selector_all('.q-date__calendar-item--in button:not([disabled])')
                    if not calendar_date_buttons:
                        self.logger.info("No more clickable calendar date buttons found")
                        break
                        
                    self.logger.info(f"Found {len(calendar_date_buttons)} clickable calendar date buttons")
                    
                    # Process the first unprocessed date button
                    for date_button in calendar_date_buttons:
                        try:
                            # Check if button is visible and enabled
                            is_visible = await date_button.is_visible()
                            is_enabled = await date_button.is_enabled()
                            
                            if not (is_visible and is_enabled):
                                self.logger.debug(f"Skipping date button: visible={is_visible}, enabled={is_enabled}")
                                continue
                            
                            # Get date text
                            date_text = None
                            try:
                                block_element = await date_button.query_selector('.block')
                                if block_element:
                                    date_text = await block_element.text_content()
                                else:
                                    date_text = await date_button.text_content()
                                date_text = date_text.strip()
                            except:
                                self.logger.warning(f"Could not extract date text for button")
                                continue
                            
                            if not date_text:
                                self.logger.warning(f"Empty date text for button, skipping")
                                continue
                            
                            # Skip if date was already processed
                            if date_text in self.processed_dates:
                                self.logger.debug(f"Skipping already processed date: {date_text}")
                                continue
                            
                            self.logger.debug(f"Attempting to click calendar date button: {date_text}")
                            await date_button.click(force=True)
                            self.logger.debug(f"Successfully clicked calendar date button: {date_text}")
                            self.processed_dates.add(date_text)
                            
                            # Wait for the calendar to close and content to update
                            await page.wait_for_timeout(5000)
                            await page.wait_for_selector('div[data-test-id="showtimes-by-film-movie-container"]', timeout=15000)
                            
                            # Parse showings for this date
                            html_content = await page.content()
                            async for item in self.parse_showings(html_content, f"Calendar_{date_text}"):
                                yield item
                            
                            # Re-open calendar for next date
                            calendar_button = await page.query_selector('.calendar-filter ul li.calendar')
                            if calendar_button:
                                self.logger.debug("Attempting to re-open 'Other Date' calendar button")
                                is_calendar_visible = await calendar_button.is_visible()
                                self.logger.debug(f"Calendar button visibility: {is_calendar_visible}")
                                await calendar_button.click(force=True)
                                self.logger.debug("Successfully re-opened 'Other Date' calendar button")
                                await page.wait_for_timeout(5000)
                                await page.wait_for_selector('.q-date__calendar-item--in button', timeout=15000, state="visible")
                            else:
                                self.logger.warning("Could not find 'Other Date' calendar button to re-open")
                                break
                            
                            break  # Exit inner loop after processing one date
                            
                        except Exception as e:
                            self.logger.error(f"Error processing calendar date button ({date_text}): {e}")
                            continue
                    else:
                        self.logger.info("No unprocessed date buttons found in current calendar view")
                        break
                    
            else:
                self.logger.warning("Could not find 'Other Date' calendar button")
                
        except Exception as e:
            self.logger.error(f"Error in calendar navigation: {e}")
            # Fallback to parsing current page
            html_content = await page.content()
            async for item in self.parse_showings(html_content, "Current"):
                yield item
        
        finally:
            await page.close()

    async def parse_showings(self, html_content, date_context=""):
        """Parse movie showings from HTML content"""
        selector = Selector(text=html_content)
        movies = selector.xpath('//div[@data-test-id="showtimes-by-film-movie-container"]')

        if not movies:
            self.logger.warning(f"No movie containers found for {date_context}")
            return

        self.logger.info(f"Found {len(movies)} movies for {date_context}")

        for movie in movies:
            # Title from aria-label
            title = movie.xpath('.//div[@role="img"]/@aria-label').get(default="").strip()
            
            if not title:
                self.logger.warning("No title found for movie, skipping")
                continue

            # Date string like "Mon, Aug 4, 2025"
            date_str = movie.xpath(
                './/div[contains(@class,"text-uppercase")]/span/following-sibling::text()[1]'
            ).get(default="").strip()
            
            if not date_str:
                self.logger.warning(f"No date found for movie {title}")
                continue
                
            try:
                date_obj = datetime.strptime(date_str, "%a, %b %d, %Y").date()
                date_iso = date_obj.strftime("%Y-%m-%d")
            except Exception as e:
                self.logger.warning(f"Could not parse date '{date_str}' for movie {title}: {e}")
                continue

            showings = movie.xpath('.//div[@data-test-id="showing-for-date-container"]')
            
            if not showings:
                self.logger.warning(f"No showings found for movie {title} on {date_str}")
                continue
                
            for show in showings:
                raw_time = show.xpath('.//div[contains(@class,"text-primary")]/text()').get()
                if not raw_time:
                    continue
                    
                try:
                    time_obj = datetime.strptime(raw_time.strip(), "%I:%M %p").time()
                    time_str = time_obj.strftime("%H:%M:%S")
                except Exception as e:
                    self.logger.warning(f"Could not parse time '{raw_time}' for {title}: {e}")
                    continue

                yield {
                    "title": title,
                    "date": date_iso,
                    "time": time_str,
                    "available": True,
                    "theaterID": "greenbeltcinema"
                }