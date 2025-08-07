import scrapy
import json
from datetime import datetime, timedelta


class LandmarkSpider(scrapy.Spider):
    name = "landmark"
    allowed_domains = ["cms-assets.webediamovies.pro", "www.landmarktheatres.com"]
    current_date = datetime.now().date().strftime('%Y-%m-%d')
    start_urls = [
        f"https://cms-assets.webediamovies.pro/prod/landmarktheatres/{current_date}/public/page-data/sq/d/3360083659.json",
        f"https://cms-assets.webediamovies.pro/prod/landmarktheatres/{current_date}/public/page-data/sq/d/3756244030.json",
        "https://www.landmarktheatres.com/api/gatsby-source-boxofficeapi/schedule",
    ]

    custom_settings = {
        "FEEDS": {
            f"data/landmark/landmark_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json": {
                "format": "json",
                "encoding": "utf-8",
                "overwrite": True,
                "fields": ["title", "date", "time", "status", "theaterID"],
            }
        }
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.movies = []
        self.theaters = {}
        self.allowed_theater_names = [
            "Landmark Atlantic Plumbing Cinema",
            "Landmark Bethesda Row Cinema",
        ]
        self.dates_to_scrape = 30
        self.initial_data_loaded = False

    def start_requests(self):
        yield scrapy.Request(self.start_urls[0], callback=self.parse_movies)
        yield scrapy.Request(self.start_urls[1], callback=self.parse_theaters)

    def try_start_showtimes_requests(self):
        if not self.initial_data_loaded and self.movies and self.theaters:
            self.initial_data_loaded = True
            allowed_theaters = [
                {"id": tid, "name": t["theaterName"], "timeZone": t.get("timeZone", "America/New_York")}
                for tid, t in self.theaters.items()
                if t["theaterName"] in self.allowed_theater_names
            ]
            for theater in allowed_theaters:
                for i in range(self.dates_to_scrape):
                    day = datetime.now().date() + timedelta(days=i)
                    next_day = day + timedelta(days=1)
                    body = {
                        "theaters": [{"id": theater["id"], "timeZone": theater["timeZone"]}],
                        "from": f"{day}T03:00:00",
                        "to": f"{next_day}T03:00:00",
                        "nin": [],
                        "sin": [],
                    }
                    headers = {
                        "Content-Type": "text/plain;charset=UTF-8",
                        "Origin": "https://www.landmarktheatres.com",
                        "Referer": "https://www.landmarktheatres.com/showtimes/",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
                        "Cookie": f"selectedTheaterId={theater['id']}",
                    }
                    yield scrapy.Request(
                        url=self.start_urls[2],
                        callback=self.parse_showtimes,
                        method="POST",
                        headers=headers,
                        body=json.dumps(body),
                    )

    def parse_movies(self, response):
        data = json.loads(response.text)
        for movie in data.get("data", {}).get("allMovie", {}).get("nodes", []):
            movie_id = movie.get("id")
            title = movie.get("title")
            if movie_id and title:
                self.movies.append({"id": movie_id, "title": title})
        if self.theaters:
            yield from self.try_start_showtimes_requests()

    def parse_theaters(self, response):
        data = json.loads(response.text)
        for theater in data.get("data", {}).get("allTheater", {}).get("nodes", []):
            theater_id = theater.get("id")
            name = theater.get("name")
            time_zone = theater.get("timeZone", "America/New_York")
            if theater_id and name:
                self.theaters[theater_id] = {"theaterName": name, "timeZone": time_zone}
        if self.movies:
            yield from self.try_start_showtimes_requests()

    def parse_showtimes(self, response):
        data = json.loads(response.text)
        if not isinstance(data, dict) or len(data) != 1:
            return
        theater_id = list(data.keys())[0]
        theater_name = self.theaters.get(theater_id, {}).get("theaterName", "")
        if theater_name not in self.allowed_theater_names:
            return
        schedule = data[theater_id].get("schedule", {})
        movie_id_to_title = {str(movie["id"]): movie["title"] for movie in self.movies}
        for movie_id, dates in schedule.items():
            title = movie_id_to_title.get(str(movie_id), str(movie_id))
            for date, showtimes in dates.items():
                for show in showtimes:
                    show_time = show.get("startsAt")
                    if not show_time or "T" not in show_time:
                        continue
                    date, time = show_time.split("T")
                    yield {
                        "title": title,
                        "date": date,
                        "time": time,
                        "status": "available",
                        "theaterID": theater_name,
                    }