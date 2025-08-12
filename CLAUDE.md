# DCKino - DC Area Theater Scraping System

## CRITICAL DIRECTIVES

- **ALWAYS ASK QUESTIONS**: Never assume implementation details
- **MAINTAIN PORTABILITY**: Ensure OS and system compatibility 
- **EXPLAIN ALL CHANGES**: Thoroughly document any code modifications with reasoning
- **GET APPROVAL FIRST**: Ask permission before major architectural changes
- **FOLLOW EXISTING PATTERNS**: Maintain current coding styles and conventions
- **BE EXPERIMENTAL BUT SAFE**: Use complex solutions but always ask first

## Main Pipeline (./run_dckino)

Clean Leftover JSON Data → Activate Virtual Env for Python → Scrapy Spiders → Raw JSON Data → Python-based Processing → Sorted/Formatted JSON Data → Python-Based Backup Creation and Managment → Python-based Combination of Data → Deactivate Virtual Env → NPM Options

Due to the windowed nature of the Ubuntu CLI in WSL, the Uvicorn/Python-based poster server must be run in a separate terminal window than the NPM dev/build server and (to my knowledge) can't be automated along with NPM without additianal GUI apps

## Architecture Overview

**Backend**: Scrapy + Playwright scraping → processing script → backup script → combination script → Uvicorn poster server
**Frontend**: React + Vite + Tailwind → Hosted on Render  
**Data Flow**: raw JSONs scraped by Scrapy/Playwright → processed JSONs with unified date/time per theater → singular combined JSON hosted in frontend
**Poster Flow**: receive combined JSON → titles normalized in tmdb.js and posterFetch.js with blacklist phrases from blacklistPosterPhrases.js applied → poster URLs fetched from TMDb via poster_server.py and resolved by tmdb.js → overrides applied from posterOverrides.json → posters pre-fetched by posterFetch.js to `public/posters/` as WebP → served statically in `dist/` or dynamically via poster_server.py in dev

## Standard Data Format

All scraped data MUST follow this exact format:
{"title": "", "date": "", "time": "", "status": "", "theaterID": ""}

The data processing unifies the formats of date, time, and theaterID into:
"date": "Mmm DD", "time": "H:MM TT", "theaterID": "xxxxx" (all lowercase)

## Tech Stack Versions

- **Host OS**: Windows 11 Pro, **WSL2**: Ubuntu 24.04

- **Node**: 20.19.4, **npm**: 10.8.2
- **React**: 19.1.0, **Vite**: 7.0.0, **Postcss**: 8.5.6
- **Tailwind**: 3.4.17, **React-Datepicker**: 8.4.0, **Date-fns**: 4.1, **Node-Fetch**: 2.7.0, **Line-Clamp**: 0.4.4

- **Python (in venv)**: 3.12.3, **Scrapy**: 2.13.2
- **Scrapy-Playwright**: 0.0.43, **Playwright**: 1.54.0, **Uvicorn**: 0.35.0

## Key Commands

**Frontend Development**
- npm run dev  # Start frontend development server
- npm run build  # Create /dist/ build
- npm run preview  # Run /dist/ locally

**Backend Util Operations** 
- python run_spiders.py  # Run all theater scrapers
- python process_data.py  # Process raw data into unified format
- python backup_data.py  # Backup latest data and check if weekly backup is done and up to date
- python combine_showings.py  # Combine all theaters into single JSON
- python poster_server.py --reload  # Start poster API server

**Setup Commands**
- ./setup.sh  # Initial project setup
- ./run_dckino.sh  # Run complete scraping pipeline

## Theaters Included

**Theaters already scraped**: afisilver, angelika, avalon, greenbelt, landmark, lockmart, miracle, suns
**Theaters that need spiders**: lookcinemas, amc, regal
**Theaters that I may add spiders for**: xscape, phoenix, cmx, ipic, cinema arts, cinemark, university mall, cinepolis

## Current Hosting

- **Frontend**: Render (free tier)
- **Backend**: Local Windows/WSL2 laptop (planned migration to Render)

## Development Standards

**Python**:
- Follow existing spider patterns in `spiders/` directory unless more efficient method is found
- Use type hints where appropriate
- Maintain error handling for network requests
- Keep data processing modular in `utils/`

**React**:
- Use functional components with hooks
- Tailwind CSS for all styling
- Maintain responsive design patterns
- Handle loading states gracefully
- Always try to move styling code onto the index.css to allow for easier change
- Try to keep lightweight to heed maintenance cost while also providing for all functionality required or asked for
- Keep in mind both dark mode and light mode stylings

**Data Handling**:
- Always validate against standard JSON format
- Graceful fallbacks for missing poster images
- Efficient date/time parsing and formatting
- WebP conversion for all poster images
- Understand and manage around the ephemeral nature of free Render sites and services

**Data Preservation**:
- Checks each data JSON to see if its valid (which means it contains at least 5 entries as of now)
- Saves all valid JSON Data in `data/` into `latest/`
- Checks to see if each JSON backup in `latest/` has a current or historical backup from within 7 days in `weekly/`
- Replaces or adds new JSON backup data to `weekly/` if needed, or doesn't touch anything else if not

## Common Tasks
- **Adding new theaters**: Follow existing spider patterns, update theater.json mapping, update backend utils especially process script
- **UI improvements**: Focus on showtime display, filtering, mobile responsiveness, light/dark mode compatibility 
- **Poster optimization**: WebP conversion, fallback handling, TMDb integration, ephemeral / persistence
- **Performance**: Efficient data structures, minimize API calls
- **Deployment prep**: Environment configuration, dependency management

## File Naming Conventions
- Raw data: `{theater}_raw_{date}_{time}.json`
- Processed data: `{theater}_processed_{date}_{time}.json`
- Backups: `{theater}_{type}_{date}_{time}_{backup type}_backup.json`

## Important Notes
- `.env` files contain TMDb API keys (never commit)
- Poster server converts images to WebP format
- Cross-browser compatibility required
- Mobile-first responsive design approach

## Future Goals
- Converting backend JSONs into better data management system, like sqlite with JSON compatibility
- Adding more specific filter and sorting options to the timeline on frontend site
- Convert entire project into a docker container
- Move backend entirely to render or some other cloud based host
- Try to run everything locally and connect to greater internet from local network (cannot do until later when friend get back)
- Create scrapers for remaining theaters