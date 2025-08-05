from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import requests
from PIL import Image
import io
import os
from dotenv import load_dotenv
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Allow Vite dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
POSTER_DIR = os.path.join(os.path.dirname(__file__), "public", "posters")

if not TMDB_API_KEY:
    logger.error("TMDB_API_KEY is not set in .env file")
    raise RuntimeError("TMDB_API_KEY is not set")

try:
    os.makedirs(POSTER_DIR, exist_ok=True)
    logger.info(f"Posters directory created/verified at: {POSTER_DIR}")
except Exception as e:
    logger.error(f"Failed to create posters directory: {str(e)}")
    raise

app.mount("/posters", StaticFiles(directory=POSTER_DIR), name="posters")

@app.get("/poster/{title}")
async def get_poster(title: str, year: str = None):
    safe_title = re.sub(r'[^\w\s]', '', title).replace(' ', '_').lower()
    webp_path = os.path.join(POSTER_DIR, f"{safe_title}.webp")
    webp_url = f"/posters/{safe_title}.webp"

    if os.path.exists(webp_path):
        logger.info(f"Serving cached poster for {title}: {webp_url}")
        return {"posterUrl": webp_url}

    try:
        tmdb_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
        if year:
            tmdb_url += f"&year={year}"
        logger.info(f"Fetching TMDb data for {title} (year: {year or 'none'})")
        response = requests.get(tmdb_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            logger.warning(f"No results found for {title} (year: {year or 'none'})")
            return {"posterUrl": null}

        poster_path = results[0].get("poster_path")
        if not poster_path:
            logger.warning(f"No poster found for {title}")
            return {"posterUrl": null}

        image_url = f"https://image.tmdb.org/t/p/w342{poster_path}"
        logger.info(f"Fetching image from {image_url}")
        image_response = requests.get(image_url, timeout=5)
        image_response.raise_for_status()

        try:
            image = Image.open(io.BytesIO(image_response.content))
            image.save(webp_path, "WEBP", quality=80)
            logger.info(f"Saved WebP poster for {title} at {webp_path}")
        except Exception as e:
            logger.error(f"Failed to process/save image for {title}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")

        return {"posterUrl": webp_url}
    except requests.RequestException as e:
        logger.error(f"TMDb API request failed for {title}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"TMDb API request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error for {title}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)