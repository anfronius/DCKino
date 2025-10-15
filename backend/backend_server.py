from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import requests
from PIL import Image
import io
import os
from dotenv import load_dotenv
import re
import logging
import subprocess
from pathlib import Path
import sys

# Add utils directory to path for title_normalizer import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))
import title_normalizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enable CORS for local development and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Local dev
        "http://localhost:4173",  # Local preview
        "https://*.onrender.com",  # All Render sites
        "*"  # Remove this later and add your specific domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

load_dotenv()
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
POSTER_DIR = os.getenv("POSTER_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "public", "posters"))

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

@app.get("/")
async def root():
    return {"message": "Poster Server is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "poster_dir": POSTER_DIR}

# Data processing endpoints
@app.post("/api/process-data")
async def process_data():
    """Process raw scraped data into standardized format"""
    try:
        logger.info("Starting data processing...")
        result = subprocess.run(
            ["python", "/app/utils/process_data.py"],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"Processing failed: {result.stderr}")
            raise HTTPException(status_code=500, detail=f"Processing failed: {result.stderr}")

        logger.info("Data processing completed successfully")
        return {
            "status": "success",
            "message": "Data processed successfully",
            "output": result.stdout[-500:] if len(result.stdout) > 500 else result.stdout  # Last 500 chars
        }
    except subprocess.TimeoutExpired:
        logger.error("Processing timed out")
        raise HTTPException(status_code=500, detail="Processing timed out after 5 minutes")
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/combine-showings")
async def combine_showings():
    """Combine all processed theater data into single movies.json"""
    try:
        logger.info("Starting showings combination...")
        result = subprocess.run(
            ["python", "/app/utils/combine_showings.py"],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"Combination failed: {result.stderr}")
            raise HTTPException(status_code=500, detail=f"Combination failed: {result.stderr}")

        logger.info("Showings combination completed successfully")
        return {
            "status": "success",
            "message": "Showings combined successfully",
            "output": result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
        }
    except subprocess.TimeoutExpired:
        logger.error("Combination timed out")
        raise HTTPException(status_code=500, detail="Combination timed out after 2 minutes")
    except Exception as e:
        logger.error(f"Combination error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/backup-data")
async def backup_data():
    """Create backups of current data"""
    try:
        logger.info("Starting data backup...")
        result = subprocess.run(
            ["python", "/app/utils/backup_data.py"],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"Backup failed: {result.stderr}")
            raise HTTPException(status_code=500, detail=f"Backup failed: {result.stderr}")

        logger.info("Data backup completed successfully")
        return {
            "status": "success",
            "message": "Data backed up successfully",
            "output": result.stdout[-500:] if len(result.stdout) > 500 else result.stdout
        }
    except subprocess.TimeoutExpired:
        logger.error("Backup timed out")
        raise HTTPException(status_code=500, detail="Backup timed out after 2 minutes")
    except Exception as e:
        logger.error(f"Backup error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run-pipeline")
async def run_pipeline():
    """Run the complete data processing pipeline: process → combine → backup"""
    try:
        logger.info("Starting full data pipeline...")
        results = {}

        # Step 1: Process data
        logger.info("Pipeline step 1: Processing data...")
        process_result = subprocess.run(
            ["python", "/app/utils/process_data.py"],
            capture_output=True,
            text=True,
            timeout=300
        )
        results["process"] = {
            "success": process_result.returncode == 0,
            "output": process_result.stdout[-200:] if len(process_result.stdout) > 200 else process_result.stdout
        }

        if process_result.returncode != 0:
            logger.error(f"Pipeline failed at processing: {process_result.stderr}")
            raise HTTPException(status_code=500, detail=f"Processing step failed: {process_result.stderr}")

        # Step 2: Combine showings (skip poster prefetch to avoid circular dependency)
        logger.info("Pipeline step 2: Combining showings...")
        combine_env = os.environ.copy()
        combine_env["SKIP_POSTER_PREFETCH"] = "true"
        combine_result = subprocess.run(
            ["python", "/app/utils/combine_showings.py"],
            capture_output=True,
            text=True,
            timeout=120,
            env=combine_env
        )
        results["combine"] = {
            "success": combine_result.returncode == 0,
            "output": combine_result.stdout[-200:] if len(combine_result.stdout) > 200 else combine_result.stdout
        }

        if combine_result.returncode != 0:
            logger.error(f"Pipeline failed at combination: {combine_result.stderr}")
            raise HTTPException(status_code=500, detail=f"Combination step failed: {combine_result.stderr}")

        # Step 3: Backup data
        logger.info("Pipeline step 3: Backing up data...")
        backup_result = subprocess.run(
            ["python", "/app/utils/backup_data.py"],
            capture_output=True,
            text=True,
            timeout=120
        )
        results["backup"] = {
            "success": backup_result.returncode == 0,
            "output": backup_result.stdout[-200:] if len(backup_result.stdout) > 200 else backup_result.stdout
        }

        if backup_result.returncode != 0:
            logger.warning(f"Pipeline backup failed (non-critical): {backup_result.stderr}")
            # Don't fail the whole pipeline if backup fails

        # Step 4: Pre-fetch posters
        logger.info("Pipeline step 4: Pre-fetching posters...")
        try:
            prefetch_result = await prefetch_posters()
            results["prefetch"] = {
                "success": True,
                "fetched": prefetch_result.get("fetched", 0),
                "cached": prefetch_result.get("cached", 0),
                "failed": prefetch_result.get("failed", 0)
            }
        except Exception as e:
            logger.warning(f"Pipeline poster prefetch failed (non-critical): {str(e)}")
            results["prefetch"] = {
                "success": False,
                "error": str(e)
            }

        logger.info("Full data pipeline completed successfully")
        return {
            "status": "success",
            "message": "Complete pipeline executed successfully",
            "results": results
        }
    except subprocess.TimeoutExpired as e:
        logger.error(f"Pipeline timed out: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline timed out: {str(e)}")
    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/prefetch-posters")
async def prefetch_posters():
    """
    Pre-fetch all posters for movies in movies.json.
    Reads the combined movies.json, extracts unique titles, and fetches posters from TMDb.
    Returns summary of fetched, cached, and failed posters.
    """
    try:
        # Path to movies.json (adjust based on container/local environment)
        # In container: /app/frontend_data/movies.json (via volume mount)
        # Local: ../frontend/src/data/movies.json
        movies_json_path = os.getenv("MOVIES_JSON_PATH", "/app/frontend_data/movies.json")
        if not os.path.exists(movies_json_path):
            # Fallback to local path
            movies_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "src", "data", "movies.json")

        if not os.path.exists(movies_json_path):
            logger.error(f"movies.json not found at {movies_json_path}")
            raise HTTPException(status_code=404, detail="movies.json not found")

        logger.info(f"Reading movies from {movies_json_path}")
        import json
        from datetime import datetime
        with open(movies_json_path, 'r', encoding='utf-8') as f:
            movies_data = json.load(f)

        # Extract unique titles
        unique_titles = set()
        for showing in movies_data:
            title = showing.get('title')
            if title:
                unique_titles.add(title)

        logger.info(f"Found {len(unique_titles)} unique titles to process")

        fetched_count = 0
        cached_count = 0
        failed_count = 0
        failed_details = []  # Changed from failed_titles to track details
        log_file = None  # Initialize log_file variable

        for title in unique_titles:
            try:
                # Extract year if present in title format "Title (YYYY)"
                title_without_year, year = title_normalizer.extract_year_from_title(title)

                # Check for overrides
                override = title_normalizer.get_override(title_without_year)
                if override and 'file' in override:
                    # Verify override file actually exists
                    override_path = os.path.join(POSTER_DIR, override['file'])
                    if os.path.exists(override_path):
                        logger.info(f"Skipping {title}: has file override")
                        cached_count += 1
                        continue
                    else:
                        logger.warning(f"Override file missing for {title}: {override['file']}")
                        failed_count += 1
                        failed_details.append({
                            "title": title,
                            "reason": "override_file_missing",
                            "details": f"File not found: {override['file']}"
                        })
                        continue

                if override and 'year' in override and not year:
                    year = str(override['year'])

                # Generate poster filename (include year if present to avoid conflicts)
                filename_title = title_normalizer.normalize_title(title_without_year)
                poster_filename = title_normalizer.create_poster_filename(filename_title, year)
                webp_path = os.path.join(POSTER_DIR, poster_filename)

                # Check if poster already exists
                if os.path.exists(webp_path):
                    logger.info(f"Poster already cached for {title}")
                    cached_count += 1
                    continue

                # Fetch poster from TMDb
                search_title = title_normalizer.normalize_for_tmdb_search(title_without_year)
                tmdb_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={requests.utils.quote(search_title)}"
                if year:
                    tmdb_url += f"&year={year}"

                logger.info(f"Fetching poster for {title} (search: {search_title})")
                response = requests.get(tmdb_url, timeout=10)
                response.raise_for_status()
                data = response.json()
                results = data.get("results", [])

                if not results:
                    logger.warning(f"⚠️ No TMDb results for {title}")
                    failed_count += 1
                    failed_details.append({
                        "title": title,
                        "reason": "tmdb_no_results",
                        "details": f"Search: '{search_title}'" + (f" Year: {year}" if year else "")
                    })
                    continue

                if not results[0].get("poster_path"):
                    logger.warning(f"⚠️ No poster_path for {title}")
                    failed_count += 1
                    failed_details.append({
                        "title": title,
                        "reason": "tmdb_no_poster",
                        "details": f"Movie found but no poster available"
                    })
                    continue

                poster_path = results[0].get("poster_path")
                image_url = f"https://image.tmdb.org/t/p/w342{poster_path}"

                # Download and convert to WebP
                image_response = requests.get(image_url, timeout=10)
                image_response.raise_for_status()
                image = Image.open(io.BytesIO(image_response.content))
                image.save(webp_path, "WEBP", quality=80)

                logger.info(f"Successfully fetched poster for {title}")
                fetched_count += 1

            except requests.Timeout as e:
                logger.error(f"Timeout fetching poster for {title}")
                failed_count += 1
                failed_details.append({
                    "title": title,
                    "reason": "network_timeout",
                    "details": str(e)
                })
            except requests.RequestException as e:
                logger.error(f"Network error for {title}: {str(e)}")
                failed_count += 1
                failed_details.append({
                    "title": title,
                    "reason": "network_error",
                    "details": str(e)
                })
            except Exception as e:
                logger.error(f"Failed to fetch poster for {title}: {str(e)}")
                failed_count += 1
                failed_details.append({
                    "title": title,
                    "reason": "unknown_error",
                    "details": str(e)
                })

        # Write failure report to log file
        if failed_details:
            log_dir = os.getenv("LOG_DIR", "/app/logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"poster_failures_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"Poster Fetch Failure Report\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"=" * 80 + "\n\n")
                f.write(f"Summary:\n")
                f.write(f"  Total processed: {len(unique_titles)}\n")
                f.write(f"  Fetched: {fetched_count}\n")
                f.write(f"  Cached: {cached_count}\n")
                f.write(f"  Failed: {failed_count}\n\n")
                f.write(f"=" * 80 + "\n\n")

                # Group by failure reason
                from collections import defaultdict
                by_reason = defaultdict(list)
                for failure in failed_details:
                    by_reason[failure['reason']].append(failure)

                for reason, failures in sorted(by_reason.items()):
                    f.write(f"\n{reason.upper().replace('_', ' ')} ({len(failures)} titles):\n")
                    f.write("-" * 80 + "\n")
                    for failure in failures:
                        f.write(f"  • {failure['title']}\n")
                        f.write(f"    {failure['details']}\n")
                    f.write("\n")

            logger.info(f"📝 Failure report written to: {log_file}")
            logger.warning(f"⚠️  {failed_count} posters failed - see {log_file} for details")

        logger.info(f"Poster pre-fetch complete: {fetched_count} fetched, {cached_count} cached, {failed_count} failed")

        # Extract just titles for backwards compatibility
        failed_titles = [f['title'] for f in failed_details]

        return {
            "status": "success",
            "fetched": fetched_count,
            "cached": cached_count,
            "failed": failed_count,
            "failed_titles": failed_titles,  # For backwards compatibility with combine_showings.py
            "failed_details": failed_details,  # Detailed failure info
            "log_file": log_file
        }

    except Exception as e:
        logger.error(f"Poster pre-fetch error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/poster/{title}")
async def get_poster(title: str, year: str = None):
    # Extract year from title if present (e.g., "Title (1952)")
    title_without_year, extracted_year = title_normalizer.extract_year_from_title(title)
    if extracted_year and not year:
        year = extracted_year
        logger.info(f"Extracted year from title: {year}")

    # Check for poster overrides first
    override = title_normalizer.get_override(title_without_year)
    if override:
        # If override has a file, use that directly
        if 'file' in override:
            webp_url = f"/posters/{override['file']}"
            webp_path = os.path.join(POSTER_DIR, override['file'])
            if os.path.exists(webp_path):
                logger.info(f"Using override file for {title}: {override['file']}")
                return {"posterUrl": webp_url}
        # If override has a year, use that for the search
        if 'year' in override and not year:
            year = str(override['year'])
            logger.info(f"Using override year for {title}: {year}")

    # Use title_normalizer for consistent normalization (use title WITHOUT year)
    search_title = title_normalizer.normalize_for_tmdb_search(title_without_year)
    filename_title = title_normalizer.normalize_title(title_without_year)
    poster_filename = title_normalizer.create_poster_filename(filename_title, year)

    webp_path = os.path.join(POSTER_DIR, poster_filename)
    webp_url = f"/posters/{poster_filename}"

    if os.path.exists(webp_path):
        logger.info(f"Serving cached poster for {title}: {webp_url}")
        return {"posterUrl": webp_url}

    try:
        tmdb_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={requests.utils.quote(search_title)}"
        if year:
            tmdb_url += f"&year={year}"
        logger.info(f"Fetching TMDb data for {title} (search: {search_title}, filename: {filename_title}, URL: {tmdb_url})")
        response = requests.get(tmdb_url, timeout=5)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        if not results:
            logger.warning(f"No TMDb search results for {search_title} (year: {year or 'none'})")
            # Fallback only for specific title
            if search_title == "runseokjin ep tour in amsterdam live viewing":
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
            logger.warning(f"No poster_path found for {search_title} in TMDb results")
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