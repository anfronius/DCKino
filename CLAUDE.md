# DCKino - DC Area Independent Theater Showtimes Aggregator

**Status:** Production-Ready Containerized Application
**Last Updated:** 2025-10-14
**Architecture:** Microservices (Docker Containers)
**Deployment:** Hybrid (Local Development + Cloud Production Target)

---

## 🎯 CRITICAL DIRECTIVES

- **ALWAYS ASK QUESTIONS**: Never assume implementation details
- **MAINTAIN PORTABILITY**: Ensure OS and system compatibility
- **EXPLAIN ALL CHANGES**: Thoroughly document any code modifications with reasoning
- **GET APPROVAL FIRST**: Ask permission before major architectural changes
- **FOLLOW EFFICIENT PATTERNS**: Maintain best practice coding styles and conventions
- **BE EXPERIMENTAL BUT SAFE**: Use complex solutions but always ask first

---

## 📋 TABLE OF CONTENTS

1. [Project Overview](#project-overview)
2. [Current Architecture](#current-architecture)
3. [Tech Stack](#tech-stack)
4. [Data Flow Pipeline](#data-flow-pipeline)
5. [Container Services](#container-services)
6. [Development Setup](#development-setup)
7. [Production Deployment](#production-deployment)
8. [Current Tasks & Issues](#current-tasks--issues)
9. [Theater Coverage](#theater-coverage)
10. [Data Management](#data-management)
11. [Title Normalization System](#title-normalization-system)
12. [Poster Management](#poster-management)
13. [Future Roadmap](#future-roadmap)
14. [Common Operations](#common-operations)
15. [Troubleshooting](#troubleshooting)

---

## 🎬 PROJECT OVERVIEW

DCKino aggregates and displays movie showtimes from independent theaters in the DC metro area. The system scrapes theater websites, processes the data into a standardized format, fetches movie posters from TMDb, and presents everything through a responsive React web interface.

### Key Features
- **Automated Scraping**: Scrapy + Playwright for JavaScript-heavy theater sites
- **Smart Poster Matching**: Intelligent title normalization with TMDb integration
- **Responsive UI**: Mobile-first design with dark/light mode support
- **Movie Stacking**: Multiple theater showings grouped visually
- **Date Navigation**: Calendar picker for browsing future dates
- **Offline Theater Tracking**: Monitors which theaters are currently scrapable

### Migration Status
**✅ Container Migration: 100% Complete**
The project has successfully migrated from a monolithic local architecture to a fully containerized microservices system using Docker.

---

## 🏗️ CURRENT ARCHITECTURE

### Three-Tier Containerized System

```
┌─────────────────────────────────────────────────────────────────┐
│                     SCRAPER CONTAINER                            │
│  Scrapy + Playwright → Theater Websites → Raw JSON              │
│  Microsoft Playwright Python Image (v1.54.0-noble)              │
│  Runs: On-demand or scheduled                                    │
└────────────────────┬────────────────────────────────────────────┘
                     │ Writes to dckino-data volume
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     BACKEND CONTAINER                            │
│  FastAPI Server + Data Processing Utilities                     │
│  - API Endpoints: /poster, /api/process-data, /api/run-pipeline │
│  - TMDb Integration: Poster fetching & caching                  │
│  - Python Utilities: process_data.py, combine_showings.py       │
│  Python 3.12-slim + Uvicorn                                     │
└────────────────────┬────────────────────────────────────────────┘
                     │ Writes movies.json + posters
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND CONTAINER                           │
│  React 19.1 + Vite 7.0 Static Site                              │
│  Served by: Nginx (Production) or Vite Dev Server (Dev)         │
│  Features: Movie timeline, date picker, theater filtering       │
│  Node 20-alpine + Nginx Alpine                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Scraper: Websites → Raw JSON → Shared Volume (dckino-data)
            ↓
Backend: Raw JSON → process_data.py → Processed JSON
            ↓
Backend: Processed JSON → combine_showings.py → movies.json
            ↓
Backend: movies.json → /api/prefetch-posters → Poster images
            ↓
Frontend: movies.json (build-time) + Posters (volume) → Static Site
            ↓
Users: Browse showtimes at http://localhost or production domain
```

### Automation

**Fully Automated Pipeline:**
1. Scraper completes → Triggers backend API `/api/run-pipeline`
2. Backend processes data automatically
3. Backend combines showings into movies.json
4. Backend pre-fetches posters from TMDb
5. Backend creates backups
6. Frontend serves updated data (rebuild required for prod)

**No manual intervention needed** between scraping and data availability.

---

## 💻 TECH STACK

### Core Technologies

**Backend:**
- **Python**: 3.12
- **Scrapy**: 2.13.2 (web scraping framework)
- **Playwright**: 1.54.0 (headless browser automation)
- **FastAPI**: 0.116.1 (REST API server)
- **Uvicorn**: 0.35.0 (ASGI server)
- **Pillow**: 11.3.0 (image processing for WebP conversion)

**Frontend:**
- **React**: 19.1.0
- **Vite**: 7.0.0 (build tool)
- **Tailwind CSS**: 3.4.17 (styling)
- **React DatePicker**: 8.4.0 (calendar UI)
- **date-fns**: 4.1.0 (date manipulation)

**Infrastructure:**
- **Docker**: Containerization platform
- **Docker Compose**: Multi-container orchestration
- **Nginx**: Production web server (Alpine-based)
- **Microsoft Playwright Image**: Chromium automation base

### Version Management

**Host Environment:**
- **OS**: Windows 11 Pro
- **WSL2**: Ubuntu 24.04
- **Node**: 20.19.4
- **npm**: 10.8.2
- **Python**: 3.12.3 (in venv)

---

## 🔄 DATA FLOW PIPELINE

### Complete Pipeline (Automated)

```bash
# Triggered via: docker-compose run scraper
# OR: docker-compose up scraper

1. SCRAPING PHASE
   └─ scraper/DCKinoSites/utils/run_spiders.py
      ├─ Runs 10 theater spiders in parallel
      ├─ Playwright launches headless Chromium per spider
      ├─ Scrapes showtimes from theater websites
      ├─ Outputs: /app/data/{theater}/{theater}_raw_{timestamp}.json
      └─ Triggers: HTTP POST to http://backend:3001/api/run-pipeline

2. PROCESSING PHASE (Backend API Triggered)
   └─ /api/run-pipeline
      ├─ Step 1: process_data.py
      │  ├─ Reads raw JSONs from all theaters
      │  ├─ Standardizes date format: "Mmm DD"
      │  ├─ Standardizes time format: "H:MM AM/PM"
      │  ├─ Standardizes theaterID: lowercase
      │  ├─ Cleans old files (keeps only newest)
      │  └─ Outputs: /app/data/{theater}/{theater}_processed_{timestamp}.json
      │
      ├─ Step 2: combine_showings.py
      │  ├─ Reads all processed JSONs
      │  ├─ Filters by date range (30 days from today)
      │  ├─ Applies showing blacklist (removes events like comedy shows)
      │  ├─ Sorts chronologically
      │  └─ Outputs: /app/frontend_data/movies.json (997 showings example)
      │
      ├─ Step 3: backup_data.py
      │  ├─ Creates "latest" backups (overwrites previous)
      │  ├─ Creates "weekly" backups (if >7 days old)
      │  └─ Validates data (minimum 5 entries per file)
      │
      └─ Step 4: /api/prefetch-posters (async)
         ├─ Reads movies.json
         ├─ Extracts unique titles
         ├─ For each title:
         │  ├─ Normalize title for TMDb search
         │  ├─ Check poster overrides (year or file)
         │  ├─ Check if poster cached
         │  ├─ Query TMDb API if not cached
         │  ├─ Download poster image
         │  ├─ Convert to WebP (quality=80)
         │  └─ Save to /app/posters/{normalized_title}.webp
         └─ Returns: {fetched: N, cached: M, failed: K}

3. FRONTEND SERVING
   └─ Production Build (npm run build)
      ├─ Reads movies.json (baked into build)
      ├─ Reads posters from /public/posters (copied to /dist)
      ├─ Vite bundles React app
      └─ Nginx serves static files on port 80
```

### Data Standard Format

**Raw JSON (from scraper):**
```json
{
  "title": "THE ROOM - 40th ANNIVERSARY Q&A",
  "date": "Various per theater",
  "time": "Various per theater",
  "status": "available",
  "theaterID": "theater_name"
}
```

**Processed JSON (after process_data.py):**
```json
{
  "title": "THE ROOM - 40th ANNIVERSARY Q&A",
  "date": "Jan 15",
  "time": "7:30 PM",
  "status": "available",
  "theaterID": "angelika"
}
```

**Frontend Display:**
- **Raw title** shown to user: `"THE ROOM - 40th ANNIVERSARY Q&A"`
- **Normalized title** for grouping: `"the_room"` (invisible to user)
- **Poster filename**: `"the_room.webp"`

---

## 🐳 CONTAINER SERVICES

### 1. Scraper Container

**Base Image:** `mcr.microsoft.com/playwright/python:v1.54.0-noble`

**Purpose:** Web scraping with headless browser automation

**Key Configuration:**
```yaml
scraper:
  build: ./scraper/Dockerfile
  init: true  # Prevents zombie processes
  ipc: host   # Chromium memory optimization
  user: pwuser  # Security: runs as non-root (UID 1000)
  security_opt:
    - seccomp:unconfined  # Required for Chromium sandbox
  volumes:
    - dckino-data:/app/data
  restart: "no"  # One-time execution
```

**Why Microsoft Playwright Image?**
- Pre-configured Chromium with all system dependencies
- Eliminates browser installation issues
- Security: includes 'pwuser' for safe browser execution
- Zero configuration needed for Playwright

**Files:**
- `/scraper/Dockerfile`
- `/scraper/requirements.txt` (57 dependencies)
- `/scraper/DCKinoSites/` (Scrapy project)
- `/scraper/DCKinoSites/utils/run_spiders.py` (entry point)

**Theaters Scraped:** 10 active spiders (see [Theater Coverage](#theater-coverage))

---

### 2. Backend Container

**Base Image:** `python:3.12-slim`

**Purpose:** FastAPI server + data processing utilities

**Key Configuration:**
```yaml
backend:
  build: ./backend/Dockerfile
  ports: ["3001:3001"]
  user: "1000:1000"  # Security: runs as non-root
  volumes:
    - dckino-data:/app/data
    - dckino-backups:/app/data_backup
    - dckino-posters:/app/posters
    - ./frontend/src/data:/app/frontend_data
  environment:
    - TMDB_API_KEY=${TMDB_API_KEY}
    - POSTER_DIR=/app/posters
    - BACKEND_URL=http://backend:3001
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:3001/health', timeout=5)"]
    interval: 30s
```

**API Endpoints:**
- `GET /` - Health check (simple)
- `GET /health` - Detailed health status
- `GET /poster/{title}?year=YYYY` - Fetch/cache poster for a movie
- `POST /api/process-data` - Process raw JSONs
- `POST /api/combine-showings` - Combine all theaters
- `POST /api/backup-data` - Create backups
- `POST /api/run-pipeline` - Full automated pipeline
- `POST /api/prefetch-posters` - Pre-fetch all posters

**Python Utilities:**
- `/backend/utils/process_data.py` - Standardize theater data
- `/backend/utils/combine_showings.py` - Merge into movies.json
- `/backend/utils/backup_data.py` - Create latest/weekly backups
- `/backend/utils/title_normalizer.py` - Shared normalization logic

**Files:**
- `/backend/Dockerfile`
- `/backend/backend_server.py` (FastAPI application)
- `/backend/requirements_minimal.txt` (6 dependencies)

---

### 3. Frontend Container

**Base Image (Production):** `nginx:alpine`
**Base Image (Development):** `node:20-alpine`

**Purpose:** Serve React application to users

**Production Configuration:**
```yaml
frontend:
  build: ./frontend/Dockerfile
  ports: ["80:80"]
  volumes:
    - dckino-posters:/app/public/posters:ro  # Read-only
  depends_on:
    backend:
      condition: service_healthy
  restart: unless-stopped
```

**Development Configuration:**
```yaml
frontend-dev:
  build: ./frontend/Dockerfile.dev
  ports: ["5173:5173"]
  user: node  # Security: runs as non-root (UID 1000)
  volumes:
    - ./frontend:/app:cached
    - /app/node_modules
  command: ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

**Nginx Configuration (Production):**
- Serves static files from `/usr/share/nginx/html`
- Proxies `/api/*` and `/poster/*` to backend:3001
- SPA fallback routing for React Router
- Security headers (X-Frame-Options, X-Content-Type-Options)
- Static asset caching (1 year)

**Files:**
- `/frontend/Dockerfile` (production multi-stage)
- `/frontend/Dockerfile.dev` (development hot-reload)
- `/frontend/package.json`
- `/frontend/src/App.jsx` (main component)
- `/frontend/src/data/movies.json` (scraped data)
- `/frontend/src/data/theaters.json` (theater metadata)

---

## 🛠️ DEVELOPMENT SETUP

### Prerequisites
- **Docker** and **Docker Compose** installed
- **Git** for version control
- **Node.js 20+** (for local frontend development)
- **Python 3.12+** (for local backend development)
- **TMDb API Key** (free account at themoviedb.org)

### Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/DCKino.git
cd DCKino

# 2. Create .env file
cp .env.example .env
# Edit .env and add your TMDB_API_KEY

# 3. Build all containers
docker-compose build

# 4. Start development environment
docker-compose -f docker-compose.dev.yml up -d
```

### Development Workflow

**Run Scraper (Manual Trigger):**
```bash
docker-compose -f docker-compose.dev.yml run --rm scraper-dev
```

**Check Backend Logs:**
```bash
docker-compose -f docker-compose.dev.yml logs -f backend-dev
```

**Access Services:**
- **Frontend Dev Server**: http://localhost:5173
- **Backend API**: http://localhost:3002
- **Backend Health**: http://localhost:3002/health

**Manual Data Pipeline (Backend Container):**
```bash
# Process raw data
docker-compose exec backend-dev python /app/utils/process_data.py

# Combine showings
docker-compose exec backend-dev python /app/utils/combine_showings.py

# Create backups
docker-compose exec backend-dev python /app/utils/backup_data.py
```

### Hot Reloading
- **Frontend**: Vite dev server auto-reloads on file changes
- **Backend**: Uvicorn `--reload` flag reloads on .py file changes
- **Scraper**: No hot reload (run manually after changes)

---

## 🚀 PRODUCTION DEPLOYMENT

### Docker Compose Production

```bash
# 1. Build production images
docker-compose build

# 2. Start all services
docker-compose up -d

# 3. Run scraper (manual or via cron)
docker-compose run --rm scraper
```

### Automated Pipeline Execution Script

**File:** `run_dckino_docker.sh`

```bash
#!/bin/bash
# Complete automated pipeline execution

# 1. Cleanup old containers
docker-compose down

# 2. Build all containers
docker-compose build

# 3. Start backend services
docker-compose up -d backend

# 4. Wait for backend health check
echo "Waiting for backend to be healthy..."
until docker-compose exec backend python -c "import requests; requests.get('http://localhost:3001/health', timeout=5)" 2>/dev/null
do
  sleep 2
done

# 5. Run scraper (writes raw data + triggers backend pipeline)
docker-compose run --rm scraper

# 6. Optional: Rebuild frontend with new data
# docker-compose build frontend
# docker-compose up -d frontend

echo "Pipeline complete!"
```

### Cloud Deployment (Render.com Example)

**Service Configuration:**

1. **Backend Service** (Web Service)
   - Environment: Docker
   - Dockerfile: `./backend/Dockerfile`
   - Port: 3001
   - Persistent Disk: `/app/data` (1GB)
   - Environment Variables: `TMDB_API_KEY`

2. **Scraper Service** (Cron Job)
   - Environment: Docker
   - Dockerfile: `./scraper/Dockerfile`
   - Schedule: `0 */6 * * *` (every 6 hours)
   - Environment Variables: `BACKEND_URL=https://your-backend.onrender.com`

3. **Frontend Service** (Static Site)
   - Build Command: `npm run build`
   - Publish Directory: `./dist`

**Note:** Render doesn't support docker-compose, so services are deployed individually.

---

## 🎯 CURRENT TASKS & ISSUES

### In Progress

**1. Poster Server Migration Fixes (HIGH PRIORITY)**
- **Issue**: Blacklist phrases and year search not fully migrated to production
- **Status**: Backend has `title_normalizer.py` module with identical logic to frontend
- **TODO**:
  - Verify `shared/config/title_processing.json` is being used correctly
  - Test poster pre-fetching in production build
  - Ensure year extraction works in `/api/prefetch-posters`

**2. SQLite Database Migration (LONG TERM)**
- **Current State**: Using JSON files for data storage
- **Goal**: Migrate to SQLite for better querying and scalability
- **Status**: Deferred pending cloud deployment and theater expansion
- **See**: `claude_reports/sqlite_migration_container_strategy.txt`

### Recently Completed

- ✅ Container migration (100% complete)
- ✅ Automated pipeline with backend API triggers
- ✅ Poster pre-fetching system
- ✅ Title normalization consolidation (shared config)
- ✅ Security hardening (non-root users in containers)
- ✅ Data cleanup automation

### Known Limitations

1. **Poster Fetch Reliability**: ~5-10% of posters fail due to TMDb mismatches
2. **Manual Frontend Rebuild**: Production requires rebuild to update data
3. **Theater Coverage**: Missing major chains (AMC, Regal)
4. **Scraping Fragility**: Theater website changes can break spiders
5. **Cold Starts**: Free-tier hosting may have slow initial load

---

## 🎭 THEATER COVERAGE

### Currently Scraped (10 Theaters)

| Theater ID | Name | Spider | Status |
|-----------|------|--------|--------|
| `afisilver` | AFI Silver Theatre | `afisilver_spider.py` | ✅ Active |
| `angelika` | Angelika Film Center | `angelika_spider.py` | ✅ Active |
| `avalon` | Avalon Theatre | `avalon_spider.py` | ✅ Active |
| `greenbeltcinema` | Greenbelt Cinema | `greenbelt_spider.py` | ✅ Active |
| `landmark` | Landmark E Street Cinema | `landmark_spider.py` | ✅ Active |
| `lockheedmartin` | Lockheed Martin IMAX | `lockmart_spider.py` | ✅ Active |
| `lookcinemas` | Look Dine-In Cinemas | `look_spider.py` | ✅ Active |
| `miracle` | Miracle Theatre | `miracle_spider.py` | ✅ Active |
| `suns` | SUNS Cinema | `suns_spider.py` | ✅ Active |

### Theater Metadata

**File:** `frontend/src/data/theaters.json`

```json
{
  "theaterID": "afisilver",
  "name": "AFI Silver Theatre",
  "colorClass": "bg-blue-600/75",
  "address": "8633 Colesville Rd, Silver Spring, MD",
  "screens": 3,
  "online": true
}
```

**Note:** All currently scraped theaters have metadata entries. The `online` flag tracks whether the spider is successfully scraping.

### Planned Additions

**High Priority:**
- AMC Theaters (multiple locations)
- Regal Cinemas (multiple locations)

**Medium Priority:**
- xscape cinemas
- phoenix theaters
- cmx cinemas
- ipic theaters
- cinema arts theater

**Low Priority:**
- cinemark
- university mall cinemas
- cinepolis

---

## 💾 DATA MANAGEMENT

### Volume Architecture

**Named Docker Volumes:**
```yaml
volumes:
  dckino-data:        # Raw + processed JSONs
  dckino-backups:     # Latest + weekly backups
  dckino-posters:     # Cached poster images (.webp)
  dckino-logs:        # Application logs
```

### Backup Strategy

**Latest Backups** (`data_backup/latest/`):
- Created after each successful scrape
- Validates data (minimum 5 entries)
- One file per theater
- Naming: `{theater}_{raw/processed}_{timestamp}_latest_backup.json`

**Weekly Backups** (`data_backup/weekly/`):
- Created if latest backup is >7 days old
- Preserves historical snapshots
- One file per theater per week
- Naming: `{theater}_{raw/processed}_{timestamp}_weekly_backup.json`

### Data Cleanup Policy

**Implemented in** `process_data.py`:
- Keeps only newest raw file per theater
- Keeps only newest processed file per theater
- Automatic cleanup after processing
- Prevents volume bloat
- Reduced file count: ~79 files → ~16 files per cycle

### File Naming Conventions

**Raw Data:**
```
/app/data/angelika/angelika_raw_20251014_180500.json
```

**Processed Data:**
```
/app/data/angelika/angelika_processed_20251014_180530.json
```

**Combined Output:**
```
/app/frontend_data/movies.json
```

**Posters:**
```
/app/posters/the_matrix.webp
/app/posters/wall_e.webp
```

---

## 🔤 TITLE NORMALIZATION SYSTEM

### Purpose
Movie titles come in many forms with special events, formats, and editions:
- `"THE ROOM - 40th ANNIVERSARY Q&A"`
- `"Willy Wonka & the Chocolate Factory in 70mm"`
- `"PARASITE (RE-RELEASE) + Panel Discussion"`

The system must:
1. **Preserve** original titles for display to users
2. **Normalize** titles for TMDb API search
3. **Normalize** titles for poster filename consistency
4. **Group** showings of the same movie across theaters

### Architecture

**Single Source of Truth:** `/shared/config/title_processing.json`

```json
{
  "blacklistPhrases": [
    " w/ A Rarely Seen Short Film",
    "- 40th Anniversary",
    "40th ANNIVERSARY",
    "Q&A",
    "\\+ Q&A",
    "in 70mm",
    "in 35mm",
    "(RE-RELEASE)",
    "(sensory friendly)",
    "... (46+ total)"
  ],
  "blacklistShowings": [
    "CHINATOWN FUNK EXPRESS V",
    "Storytime On Screen",
    "OLA Film Festival",
    "DC Moth StorySLAM",
    "The Elite – Stand Up Comedy"
  ],
  "posterOverrides": [
    {
      "title": "Prime Cut",
      "year": "1972"
    },
    {
      "title": "Wall-E",
      "file": "p_walle_19753_69f7ff00.webp"
    }
  ]
}
```

### Title Processing Flow

**Backend:** `/backend/utils/title_normalizer.py`

```python
# 1. Extract year from title
title_without_year, year = extract_year_from_title("The Matrix (1999)")
# → "The Matrix", "1999"

# 2. Check for manual overrides
override = get_override(title_without_year)
# → {"year": "1999"} or {"file": "custom.webp"}

# 3. Normalize for TMDb search
search_title = normalize_for_tmdb_search(title_without_year)
# "THE ROOM - 40th ANNIVERSARY Q&A" → "the room"

# 4. Normalize for filename
filename_title = normalize_title(title_without_year)
# "THE ROOM - 40th ANNIVERSARY Q&A" → "the_room"

# 5. Create poster filename
poster_filename = create_poster_filename(filename_title)
# "the_room" → "the_room.webp"
```

**Frontend:** `/frontend/src/utils/titleNormalizer.js`

```javascript
// Identical functions to backend (reads from same shared config)
import CONFIG from '@shared/title_processing.json';

const BLACKLIST_PHRASES = CONFIG.blacklistPhrases;

// Same normalization functions as backend
function normalizeForTmdbSearch(title) { /* ... */ }
function normalizeTitle(title) { /* ... */ }
function createPosterFilename(normalized) { /* ... */ }
```

### Normalization Examples

| Original Title | TMDb Search | Filename | Display |
|---------------|-------------|----------|---------|
| `"THE ROOM - 40th ANNIVERSARY Q&A"` | `"the room"` | `"the_room.webp"` | `"THE ROOM - 40th ANNIVERSARY Q&A"` |
| `"Willy Wonka & the Chocolate Factory in 70mm"` | `"willy wonka and the chocolate factory"` | `"willy_wonka_and_the_chocolate_factory.webp"` | `"Willy Wonka & the Chocolate Factory in 70mm"` |
| `"PARASITE (RE-RELEASE)"` | `"parasite"` | `"parasite.webp"` | `"PARASITE (RE-RELEASE)"` |

### Blacklist Systems

**1. Showing Blacklist** (Removes entire showings):
- **Purpose**: Filter out non-movie events
- **Applied**: During `combine_showings.py`
- **Examples**: Comedy shows, festivals, story slams
- **Effect**: Showing never reaches frontend

**2. Poster Phrase Blacklist** (Cleans titles):
- **Purpose**: Remove event details for TMDb matching
- **Applied**: During poster fetching and frontend grouping
- **Examples**: "Q&A", "40th Anniversary", "in 70mm"
- **Effect**: Title cleaned for search, original preserved

### Poster Overrides

**Manual Fixes for Problematic Titles:**

```json
{
  "title": "Prime Cut",
  "year": "1972"  // Force year for better TMDb match
}
```

```json
{
  "title": "Wall-E",
  "file": "p_walle_19753_69f7ff00.webp"  // Use specific file
}
```

**Location:** `/shared/config/title_processing.json` → `posterOverrides` array

---

## 🖼️ POSTER MANAGEMENT

### Poster Pipeline

```
movies.json → /api/prefetch-posters
       ↓
Extract unique titles
       ↓
For each title:
  1. Extract year: "Movie (1999)" → year=1999
  2. Check overrides: Manual year or file specified?
  3. Normalize for TMDb: "Movie Q&A" → "movie"
  4. Check cache: Does the_movie.webp exist?
  5. Query TMDb API: Search by normalized title + year
  6. Download poster: TMDb returns poster URL
  7. Convert to WebP: Pillow saves with quality=80
  8. Save: /app/posters/the_movie.webp
       ↓
Frontend Build:
  - Copies /app/posters → /dist/posters
  - Bakes static paths into React app
  - Serves posters as static assets
```

### Poster Storage Strategy

**Development Mode:**
- Frontend makes **runtime API calls** to backend
- Backend fetches on-demand and caches
- Lazy loading handles missing posters gracefully

**Production Mode:**
- Posters **pre-fetched** before frontend build
- Static file paths baked into React app
- No runtime backend communication needed
- Nginx serves posters from `/dist/posters`

### Poster API Endpoints

**Individual Poster Fetch:**
```bash
GET /poster/{title}?year=2023
```

**Bulk Pre-fetch:**
```bash
POST /api/prefetch-posters
```

**Response:**
```json
{
  "status": "success",
  "fetched": 87,
  "cached": 102,
  "failed": 8,
  "failed_titles": ["Movie X", "Movie Y"],
  "log_file": "/app/logs/poster_failures_20251014_120500.log"
}
```

### Failure Handling

**Log File:** `/app/logs/poster_failures_{timestamp}.log`

**Failure Reasons:**
- `tmdb_no_results`: TMDb has no matching movie
- `tmdb_no_poster`: Movie found but no poster available
- `override_file_missing`: Manual override file doesn't exist
- `network_timeout`: Request to TMDb timed out
- `network_error`: HTTP error from TMDb API
- `unknown_error`: Unexpected exception

**Example Log:**
```
Poster Fetch Failure Report
Generated: 2025-10-14 12:05:00
================================================================================

Summary:
  Total processed: 197
  Fetched: 87
  Cached: 102
  Failed: 8

================================================================================

TMDB NO RESULTS (3 titles):
--------------------------------------------------------------------------------
  • RUN SEOKJIN EP TOUR IN AMSTERDAM LIVE VIEWING
    Search: 'run seokjin ep tour in amsterdam live viewing'
  • SOME OBSCURE FILM FROM 1932
    Search: 'some obscure film from 1932' Year: 1932

TMDB NO POSTER (2 titles):
--------------------------------------------------------------------------------
  • ANGELIKA MEMBERS EXCLUSIVE MYSTERY SCREENING
    Movie found but no poster available
```

### Poster Overrides

**When to Use:**
1. TMDb year mismatch (e.g., re-release vs original)
2. TMDb has wrong movie (e.g., foreign film with same name)
3. Custom poster needed (e.g., theater-specific event)

**How to Add:**

Edit `/shared/config/title_processing.json`:

```json
{
  "posterOverrides": [
    {
      "title": "The Matrix",
      "year": "1999"
    }
  ]
}
```

Or for custom poster:

```json
{
  "title": "ANGELIKA MEMBERS EXCLUSIVE MYSTERY SCREENING",
  "file": "angelikamembers.webp"
}
```

Then place custom file at: `/frontend/public/fixed_posters/angelikamembers.webp`

---

## 🗺️ FUTURE ROADMAP

### Short-Term (Next 3 Months)
- [ ] Complete poster server migration testing
- [ ] Add AMC and Regal theater scrapers
- [ ] Enhanced filtering options (by genre, runtime, rating)
- [ ] Mobile app (React Native or PWA)

### Medium-Term (3-6 Months)
- [ ] SQLite database migration
- [ ] User accounts and favorites
- [ ] Email/SMS notifications for new showings
- [ ] Theater-specific pages

### Long-Term (6+ Months)
- [ ] Multi-city expansion (NYC, LA, Chicago)
- [ ] Community features (reviews, ratings)
- [ ] Integration with ticket purchasing
- [ ] Analytics dashboard for theater trends

---

## 🔧 COMMON OPERATIONS

### Manual Scraping

```bash
# Development environment
docker-compose -f docker-compose.dev.yml run --rm scraper-dev

# Production environment
docker-compose run --rm scraper
```

### Trigger Backend Pipeline

```bash
# Via API
curl -X POST http://localhost:3001/api/run-pipeline

# Manual execution inside container
docker-compose exec backend python /app/utils/process_data.py
docker-compose exec backend python /app/utils/combine_showings.py
docker-compose exec backend python /app/utils/backup_data.py
```

### Pre-fetch All Posters

```bash
curl -X POST http://localhost:3001/api/prefetch-posters
```

### View Container Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f scraper
```

### Rebuild Frontend

```bash
# Development
docker-compose -f docker-compose.dev.yml build frontend-dev
docker-compose -f docker-compose.dev.yml up -d frontend-dev

# Production
docker-compose build frontend
docker-compose up -d frontend
```

### Check Health

```bash
# Backend health
curl http://localhost:3001/health

# Container status
docker-compose ps

# Volume contents
docker volume ls
docker volume inspect dckino-data
```

### Clean Up

```bash
# Stop all containers
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# Total Docker Clean Up
docker system prune -a --volumes
```

---

## 🐛 TROUBLESHOOTING

### Scraper Issues

**Problem:** Scraper fails with browser errors
```
Solution: Verify using Microsoft Playwright image
Check: docker-compose.yml → scraper → image: mcr.microsoft.com/playwright/python:v1.54.0-noble
```

**Problem:** Scraper runs but returns 0 showings
```
Solution: Theater website may have changed structure
Action: Inspect spider code and update selectors
Debug: docker-compose run --rm scraper scrapy shell https://theater-url.com
```

**Problem:** Permission denied writing to /app/data
```
Solution: Ensure scraper runs as pwuser (UID 1000)
Check: docker-compose.yml → scraper → user: pwuser
```

### Backend Issues

**Problem:** Backend can't find movies.json
```
Solution: Check volume mount configuration
Verify: docker-compose exec backend ls /app/frontend_data/movies.json
```

**Problem:** Posters not pre-fetching
```
Solution: Check TMDb API key
Verify: docker-compose exec backend env | grep TMDB
Test: curl "https://api.themoviedb.org/3/search/movie?api_key=YOUR_KEY&query=matrix"
```

**Problem:** Backend API returns 500 errors
```
Solution: Check backend logs for Python exceptions
Debug: docker-compose logs backend
```

### Frontend Issues

**Problem:** Frontend shows no movies
```
Solution: Verify movies.json exists and is valid
Check: cat frontend/src/data/movies.json
Validate: jq . frontend/src/data/movies.json
```

**Problem:** Posters not displaying
```
Solution: Check poster directory and paths
Verify: ls frontend/public/posters/
Check: Browser console for 404 errors
```

**Problem:** Frontend build fails
```
Solution: Check Node modules installation
Fix: cd frontend && npm install
Rebuild: docker-compose build frontend
```

### Volume Issues

**Problem:** Data not persisting between container restarts
```
Solution: Verify named volumes in docker-compose.yml
Check: docker volume ls | grep dckino
Inspect: docker volume inspect dckino-data
```

**Problem:** Volume permission denied
```
Solution: Ensure consistent UID across containers
Check: All services use UID 1000 (pwuser, backend, node)
```

---

## 📚 ADDITIONAL RESOURCES

### Documentation
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Scrapy Docs**: https://docs.scrapy.org/
- **Playwright Docs**: https://playwright.dev/python/
- **Docker Compose**: https://docs.docker.com/compose/
- **React Docs**: https://react.dev/

### Related Files
- `/claude_reports/overall_project_status.txt` - Complete architecture analysis
- `/claude_reports/poster_and_name_function_report.txt` - Title normalization deep dive
- `/claude_reports/container_migration_status.txt` - Migration completion report
- `/claude_reports/sqlite_migration_container_strategy.txt` - Future database plans
- `/claude_reports/title_normalization_audit.md` - Normalization consolidation

### Configuration Files
- `/shared/config/title_processing.json` - Shared blacklist/overrides
- `/frontend/src/data/theaters.json` - Theater metadata
- `/.env` - Environment variables (not committed)
- `/docker-compose.yml` - Production container orchestration
- `/docker-compose.dev.yml` - Development container orchestration

---

## 📝 CHANGE LOG

**2025-10-14:**
- Created NEW_CLAUDE.md to reflect current containerized architecture
- Documented poster server migration status
- Added troubleshooting section
- Included SQLite migration future plans

**2025-10-09:**
- Completed container migration (100%)
- Implemented automated pipeline with backend API
- Added poster pre-fetching system
- Consolidated title normalization to shared config
- Implemented security hardening (non-root users)

**2025-09-29:**
- Fixed scraper container with Microsoft Playwright image
- Added backend API endpoints for data processing
- Implemented automated workflow scraper→backend

**Earlier:**
- Initial monolithic architecture on WSL2 Ubuntu
- Manual execution via `./run_dckino.sh`

---

## 🤝 CONTRIBUTING

When contributing to DCKino, please:

1. **Read this document thoroughly** before making changes
2. **Test in development environment first** (`docker-compose.dev.yml`)
3. **Update documentation** for any architectural changes
4. **Follow existing code patterns** (see Python/JavaScript style)
5. **Ask questions** before major refactors
6. **Explain your changes** in pull request descriptions

---

## 📄 LICENSE

**Project Status:** Private Development Project
**Author:** Reed
**Purpose:** Educational/Portfolio

---

**Last Updated:** 2025-10-14
**Document Version:** 2.0
**Migration Status:** ✅ Complete
**Production Ready:** ✅ Yes

---

*For questions or issues, refer to `/claude_reports/` directory for detailed technical analysis.*
