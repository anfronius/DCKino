# Shared Configuration

This directory contains the single source of truth for all title processing configuration used throughout the DCKino project.

## Files

### `title_processing.json`

**Single configuration file** used by both frontend and backend for title normalization, showing filtering, and poster overrides.

**Structure:**
```json
{
  "blacklistPhrases": [...],     // Phrases to remove during title normalization
  "blacklistShowings": [...],    // Complete showings to exclude (events, non-movies)
  "posterOverrides": [...]       // Custom year/file overrides for specific titles
}
```

## Usage

### Frontend (Vite Alias)

The frontend uses a Vite path alias `@shared` to import the config:

```javascript
// Import shared config
import CONFIG from '@shared/title_processing.json';

// Access config sections
const BLACKLIST_PHRASES = CONFIG.blacklistPhrases;
const POSTER_OVERRIDES = CONFIG.posterOverrides;
```

**Files using shared config:**
- `frontend/src/utils/titleNormalizer.js`
- `frontend/src/utils/tmdb.js`
- `frontend/src/utils/posterFetch.js`

### Backend (Python Path Resolution)

The backend loads the config via relative path resolution:

```python
# Load shared config
config = title_normalizer.load_shared_config()

# Access config sections
BLACKLIST_PHRASES = config.get('blacklistPhrases', [])
BLACKLIST_SHOWINGS = config.get('blacklistShowings', [])
POSTER_OVERRIDES = config.get('posterOverrides', [])
```

**Files using shared config:**
- `backend/utils/title_normalizer.py`
- `backend/utils/combine_showings.py`

## Configuration Sections

### blacklistPhrases

Phrases automatically removed from titles during normalization for TMDb search and poster filename generation.

**Examples:**
- `"40th ANNIVERSARY"` - Anniversary markers
- `"Q&A"` - Special event markers
- `"in 70mm"` - Format specifiers
- `"(RE-RELEASE)"` - Release type markers

**When to add:**
- Theater adds promotional text to titles
- Special events use consistent naming patterns
- Format/language markers need to be stripped

### blacklistShowings

Complete showing titles to exclude from the combined movies.json.

**Examples:**
- `"CHINATOWN FUNK EXPRESS V"` - Live event
- `"Storytime On Screen"` - Non-movie screening
- `"DC Moth StorySLAM: THEMELESS"` - Storytelling event

**When to add:**
- Non-movie events appear in theater listings
- Recurring events that aren't films

### posterOverrides

Custom configurations for specific titles that need manual handling.

**Types:**
1. **Year override** - Force specific year for better TMDb matching
2. **File override** - Use pre-downloaded custom poster file

**Examples:**
```json
{
  "title": "Prime Cut",
  "year": "1972"  // Force year (multiple movies with same name)
},
{
  "title": "Wall-E",
  "file": "p_walle_19753_69f7ff00.webp"  // Use specific TMDb poster
},
{
  "title": "ANGELIKA MEMBERS EXCLUSIVE MYSTERY SCREENING",
  "file": "angelikamembers.webp"  // Custom placeholder poster
}
```

**When to add:**
- TMDb returns wrong movie (common title)
- TMDb has no poster or poor quality poster
- Title requires special handling (mystery screening, etc.)

## Adding New Entries

1. **Edit `title_processing.json`** - Single file to update
2. **Restart containers** - Changes take effect after container restart
3. **Test** - Verify normalization works as expected

## Benefits of Shared Config

✅ **Single source of truth** - Update once, applies everywhere
✅ **No sync issues** - Impossible for frontend/backend to diverge
✅ **Version controlled** - All changes tracked in git
✅ **Easy maintenance** - Clear location for all configuration
✅ **Static build compatible** - Vite bundles config at build time

## Migration Notes

**Deprecated files (removed):**
- ❌ `frontend/src/utils/blacklistPosterPhrases.js`
- ❌ `frontend/src/utils/posterOverrides.json`
- ❌ `backend/utils/posterOverrides.json`
- ❌ `backend/utils/blacklist_showings.py`

**New single file:**
- ✅ `shared/config/title_processing.json`
