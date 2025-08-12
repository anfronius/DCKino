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

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
POSTER_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "public", "posters")

if not TMDB_API_KEY:
    logger.error("TMDB_API_KEY is not set in .env file")
    raise RuntimeError("TMDB_API_KEY is not set")

try:
    os.makedirs(POSTER_DIR, exist_ok=True)
    logger.info(f"Posters directory created/verified at: {POSTER_DIR}")
except Exception as e:
    logger.error(f"Failed to create posters directory: {str(e)}")
    raise

# Mount static files
app.mount("/posters", StaticFiles(directory=POSTER_DIR, check_dir=False), name="posters")

@app.get("/poster/{title}")
async def get_poster(title: str, year: str = None):
    # Normalize title for search: remove #, :, standardize case and spacing
    normalized_title = title.lower().replace('#', '').replace(':', '').replace('.', ' ').strip()
    # Normalize filename: remove ? and other special chars for compatibility
    safe_title = normalized_title.replace('?', '').replace("'", '').replace("'", '').replace(',', '').replace('!', '').replace('&', 'and').replace(' ', '_')
    webp_path = os.path.join(POSTER_DIR, f"{safe_title}.webp")
    webp_url = f"/posters/{safe_title}.webp"

    if os.path.exists(webp_path):
        logger.info(f"Serving cached poster for {title}: {webp_url}")
        return {"posterUrl": webp_url}

    try:
        tmdb_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={requests.utils.quote(normalized_title)}"
        if year:
            tmdb_url += f"&year={year}"
        logger.info(f"Fetching TMDb data for {title} (normalized: {normalized_title}, URL: {tmdb_url})")
        response = requests.get(tmdb_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            logger.warning(f"No TMDb search results for {normalized_title} (year: {year or 'none'})")
            # Fallback only for specific title
            if normalized_title == "runseokjin ep tour in amsterdam live viewing":
                movie_id = 1513439
                tmdb_url_id = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}"
                logger.info(f"Falling back to ID lookup for {title}: {tmdb_url_id}")
                id_response = requests.get(tmdb_url_id, timeout=5)
                id_response.raise_for_status()
                id_data = id_response.json()
                poster_path = id_data.get("poster_path")
                if poster_path:
                    image_url = f"https://image.tmdb.org/t/p/w342{poster_path}"
                    image_response = requests.get(image_url, timeout=5)
                    image_response.raise_for_status()
                    image = Image.open(io.BytesIO(image_response.content))
                    image.save(webp_path, "WEBP", quality=80)
                    logger.info(f"Saved WebP poster for {title} at {webp_path}")
                    return {"posterUrl": webp_url}
                else:
                    logger.warning(f"No poster_path found for ID {movie_id}")
                    return {"posterUrl": None}
            return {"posterUrl": None}  # No fallback for other titles

        poster_path = results[0].get("poster_path")
        if not poster_path:
            logger.warning(f"No poster_path found for {normalized_title} in TMDb results")
            return {"posterUrl": None}

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
        logger.error(f"TMDb API request failed for {title}: {str(e)}, URL: {tmdb_url}")
        raise HTTPException(status_code=500, detail=f"TMDb API request failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error for {title}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)