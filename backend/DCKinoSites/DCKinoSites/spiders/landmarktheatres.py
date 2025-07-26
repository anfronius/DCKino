import scrapy
import json

import logging

class LandmarkSpider(scrapy.Spider):
    name = "landmark"
    allowed_domains = [
        "cms-assets.webediamovies.pro",
        "www.landmarktheatres.com"
    ]
    start_urls = [
        "https://cms-assets.webediamovies.pro/prod/landmarktheatres/2025-07-03/public/page-data/sq/d/3360083659.json",
        "https://cms-assets.webediamovies.pro/prod/landmarktheatres/2025-07-03/public/page-data/sq/d/3756244030.json",
        "https://www.landmarktheatres.com/api/gatsby-source-boxofficeapi/schedule"
    ]

    custom_settings = {
        "FEEDS": {
            "data/landmarkmovies.json": {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True,
                "fields": ["title", "date", "time", "status", "theaterID"]
            }
        }
    }

    def __init__(self):
        self.movies = []
        self.theaters = {}  # {theater_id: {"theaterName": name, "timeZone": tz}}
        self.allowed_theater_names = [
            "Landmark Atlantic Plumbing Cinema",
            "Landmark Bethesda Row Cinema"
        ]
        self.dates_to_scrape = 30
        self.initial_data_loaded = False

    def start_requests(self):
        # First, get movies and theaters
        yield scrapy.Request(self.start_urls[0], callback=self.parse_movies)
        yield scrapy.Request(self.start_urls[1], callback=self.parse_theaters)

    def try_start_showtimes_requests(self):
        # Only start showtimes requests after both movies and theaters are loaded
        if not self.initial_data_loaded and self.movies and self.theaters:
            self.initial_data_loaded = True
            from datetime import datetime, timedelta
            today = datetime.now()
            # Only use allowed theaters (by name)
            allowed_theaters = [
                {"id": tid, "name": t["theaterName"], "timeZone": t.get("timeZone", "America/New_York")}
                for tid, t in self.theaters.items() if t["theaterName"] in self.allowed_theater_names
            ]
            for theater in allowed_theaters:
                for i in range(self.dates_to_scrape):
                    day = today + timedelta(days=i)
                    next_day = day + timedelta(days=1)
                    body = {
                        "theaters": [{"id": theater["id"], "timeZone": theater["timeZone"]}],
                        "from": day.strftime("%Y-%m-%dT03:00:00"),
                        "to": next_day.strftime("%Y-%m-%dT03:00:00"),
                        "nin": [],
                        "sin": []
                    }
                    headers = {
                        "Content-Type": "text/plain;charset=UTF-8",
                        "Origin": "https://www.landmarktheatres.com",
                        "Referer": "https://www.landmarktheatres.com/showtimes/",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                        "Cookie": f"selectedTheaterId={theater['id']}"
                    }
                    yield scrapy.Request(
                        self.start_urls[2],
                        callback=self.parse_showtimes,
                        method='POST',
                        headers=headers,
                        body=json.dumps(body)
                    )
    def parse_showtimes(self, response):
        data = json.loads(response.text)
        # Handle top-level key as theater ID (e.g., 'X0WLT')
        if isinstance(data, dict) and len(data) == 1:
            theater_id = list(data.keys())[0]
            theater_data = data[theater_id]
            schedule = theater_data.get("schedule", {})
            theater_name = self.theaters.get(theater_id, {}).get("theaterName", "")
            if theater_name not in self.allowed_theater_names:
                return

            # Build a mapping from movie id to title using the movie API data
            movie_id_to_title = {}
            for movie in self.movies:
                movie_id = movie.get("id")
                title = movie.get("title", "")
                if movie_id and title:
                    movie_id_to_title[str(movie_id)] = title

            # schedule: {movie_id: {date: [showtime, ...]}}
            for movie_id, dates in schedule.items():
                title = movie_id_to_title.get(str(movie_id), str(movie_id))
                for date, showtimes in dates.items():
                    for show in showtimes:
                        show_time = show.get("startsAt")
                        time = ""
                        if show_time and "T" in show_time:
                            _, time = show_time.split("T")
                            time = time[:5]
                        # Convert time from 'HH:MM' (24-hour) to 'HH:MM AM/PM' (12-hour)
                        time_12hr = time
                        try:
                            if time:
                                from datetime import datetime
                                time_12hr = datetime.strptime(time, "%H:%M").strftime("%I:%M %p")
                        except Exception:
                            pass
                        # Convert date from 'YYYY-MM-DD' to 'Mon DD' (e.g., 'Jul 27')
                        date_fmt = date
                        try:
                            if date:
                                from datetime import datetime
                                date_fmt = datetime.strptime(date, "%Y-%m-%d").strftime("%b %d")
                        except Exception:
                            pass
                        yield {
                            "title": title,
                            "date": date_fmt,
                            "time": time_12hr,
                            "status": "available",
                            "theaterID": theater_name
                        }
        # else block removed: no debug logging

    def parse_movies(self, response):
        data = json.loads(response.text)
        movie_items = data.get("data", {}).get("allMovie", {}).get("nodes", [])
        for movie in movie_items:
            movie_id = movie.get("id")
            title = movie.get("title")
            if not movie_id or not title:
                continue
            self.movies.append({
                "id": movie_id,
                "title": title
            })
        # Try to start showtimes requests if theaters are loaded
        if self.theaters:
            yield from self.try_start_showtimes_requests()

    def parse_theaters(self, response):
        data = json.loads(response.text)
        theater_items = data.get("data", {}).get("allTheater", {}).get("nodes", [])
        for theater in theater_items:
            theater_id = theater.get("id")
            name = theater.get("name")
            time_zone = theater.get("timeZone", "America/New_York")
            if theater_id:
                self.theaters[theater_id] = {
                    "theaterName": name,
                    "timeZone": time_zone
                }
        # Try to start showtimes requests if movies are loaded
        if self.movies:
            yield from self.try_start_showtimes_requests()

    # build_items_with_times is no longer needed; all showtime items are yielded directly from parse_showtimes
