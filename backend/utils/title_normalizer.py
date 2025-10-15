"""
Title normalization utilities for poster fetching and movie grouping.
Ported directly from frontend/src/utils/titleNormalizer.js

Purpose:
  - Normalize titles for TMDb API searches (remove blacklist phrases)
  - Create consistent poster filenames
  - Apply poster overrides for specific titles

Note: This does NOT modify stored titles in movies.json.
      Original titles are preserved. Normalization is only for:
      1. TMDb search queries (cleaner matching)
      2. Poster filename generation (consistent naming)
      3. Frontend stacking/grouping logic
"""

import json
import re
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Load shared configuration
# Single source of truth for blacklist phrases and poster overrides
_config_cache: Optional[Dict] = None

def load_shared_config() -> Dict:
    """
    Load shared configuration from shared/config/title_processing.json
    Cached after first load for performance.

    Returns:
        Dict with 'blacklistPhrases', 'blacklistShowings', 'posterOverrides'
    """
    global _config_cache

    if _config_cache is not None:
        return _config_cache

    # Path relative to this file: backend/utils/title_normalizer.py
    # In container: /app/utils/title_normalizer.py → /app/shared/config/title_processing.json
    # Locally: backend/utils/title_normalizer.py → ../../shared/config/title_processing.json
    current_file = Path(__file__).resolve()

    # In container: /app/utils/ -> /app/shared/
    # Locally: /path/to/DCKino/backend/utils/ -> /path/to/DCKino/shared/
    # Check if we're in container first (parent.parent would be /app/)
    if (current_file.parent.parent / "shared" / "config" / "title_processing.json").exists():
        # Container path: /app/utils/ -> /app/shared/
        config_path = current_file.parent.parent / "shared" / "config" / "title_processing.json"
    else:
        # Local development: backend/utils/ -> ../shared/
        config_path = current_file.parent.parent.parent / "shared" / "config" / "title_processing.json"

    if not config_path.exists():
        print(f"Warning: title_processing.json not found at {config_path}")
        _config_cache = {
            "blacklistPhrases": [],
            "blacklistShowings": [],
            "posterOverrides": []
        }
        return _config_cache

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            _config_cache = json.load(f)
        print(f"Loaded shared config: {len(_config_cache.get('blacklistPhrases', []))} blacklist phrases, "
              f"{len(_config_cache.get('posterOverrides', []))} overrides, "
              f"{len(_config_cache.get('blacklistShowings', []))} showing blacklist")
    except Exception as e:
        print(f"Error loading title_processing.json: {e}")
        _config_cache = {
            "blacklistPhrases": [],
            "blacklistShowings": [],
            "posterOverrides": []
        }

    return _config_cache


# Load blacklist phrases from shared config
BLACKLIST_PHRASES = load_shared_config().get('blacklistPhrases', [])

# Cache for poster overrides
_poster_overrides_cache: Optional[List[Dict]] = None


def load_poster_overrides() -> List[Dict]:
    """
    Load poster overrides from shared config
    Cached after first load for performance.

    Returns:
        List of override dicts with 'title', 'year' (optional), 'file' (optional)
    """
    global _poster_overrides_cache

    if _poster_overrides_cache is not None:
        return _poster_overrides_cache

    config = load_shared_config()
    _poster_overrides_cache = config.get('posterOverrides', [])

    return _poster_overrides_cache


def normalize_for_tmdb_search(title: str) -> str:
    """
    Normalizes title for TMDb search - matches frontend JavaScript exactly.
    Ported from frontend/src/utils/titleNormalizer.js normalizeForTmdbSearch()

    This is what gets sent to TMDb API for searches.

    Process:
      1. Remove all blacklist phrases
      2. Clean up trailing punctuation
      3. Convert to lowercase
      4. Remove special characters (#, :, .)
      5. Standardize spacing

    Args:
        title: Original movie title

    Returns:
        Normalized title ready for TMDb search (with spaces)

    Example:
        "The Matrix: 25th Anniversary Q&A" -> "the matrix"
    """
    cleaned_title = title

    # Apply blacklist phrase removal first (case-insensitive)
    for phrase in BLACKLIST_PHRASES:
        cleaned_title = re.sub(phrase, '', cleaned_title, flags=re.IGNORECASE)
        cleaned_title = cleaned_title.strip()

    # Clean up any trailing punctuation and incomplete patterns left by blacklist removal
    cleaned_title = re.sub(r'[,;:+]\s*$', '', cleaned_title)      # Remove trailing punctuation
    cleaned_title = re.sub(r'\s*\(\s*\)\s*$', '', cleaned_title)  # Remove empty parentheses
    cleaned_title = re.sub(r'\s*\+\s*$', '', cleaned_title)       # Remove trailing plus signs
    cleaned_title = re.sub(r':\s*$', '', cleaned_title)           # Remove trailing colons
    cleaned_title = cleaned_title.strip()

    # Apply normalization: lowercase, remove #:., standardize spacing
    normalized = cleaned_title.lower()
    normalized = normalized.replace('#', '')
    normalized = normalized.replace(':', '')
    normalized = normalized.replace('.', ' ')
    normalized = re.sub(r'\s+', ' ', normalized)  # Collapse multiple spaces
    normalized = normalized.strip()

    return normalized


def normalize_title(title: str) -> str:
    """
    Creates filename-safe version for poster files.
    Ported from frontend/src/utils/titleNormalizer.js normalizeTitle()

    Process:
      1. Get search-normalized title (via normalize_for_tmdb_search)
      2. Remove special chars for web compatibility
      3. Replace spaces with underscores

    Args:
        title: Original movie title

    Returns:
        Filename-safe version (with underscores)

    Example:
        "The Matrix: 25th Anniversary Q&A" -> "the_matrix"
    """
    # Step 1: Get the search title
    search_title = normalize_for_tmdb_search(title)

    # Step 2: Create safe filename
    # Remove ALL special chars for web compatibility
    # Match JavaScript: .replace(/[''']/g, '')
    # The three characters are: ' (apostrophe), ' (left single quote), ' (right single quote)
    safe_title = search_title
    safe_title = safe_title.replace('?', '')
    safe_title = safe_title.replace("'", '')  # Regular apostrophe
    safe_title = safe_title.replace("'", '')  # Left single quotation mark (U+2018)
    safe_title = safe_title.replace("'", '')  # Right single quotation mark (U+2019)
    safe_title = safe_title.replace(',', '')
    safe_title = safe_title.replace('!', '')
    safe_title = safe_title.replace('&', 'and')
    safe_title = re.sub(r'\s+', '_', safe_title)  # Replace spaces with underscores

    return safe_title


def create_poster_filename(normalized_title: str, year: Optional[str] = None) -> str:
    """
    Creates a poster filename with .webp extension.
    Optionally includes year to handle movies with same title from different years.

    Args:
        normalized_title: Already normalized title (from normalize_title)
        year: Optional year to append (e.g., "1953")

    Returns:
        Filename with .webp extension

    Example:
        "the_matrix" -> "the_matrix.webp"
        "inferno", "1953" -> "inferno_(1953).webp"
    """
    if year:
        return f"{normalized_title}_({year}).webp"
    return f"{normalized_title}.webp"


def get_override(title: str) -> Optional[Dict]:
    """
    Check if a title has a poster override.

    Overrides can specify:
      - year: Force specific year for TMDb search
      - file: Use specific pre-downloaded file instead of fetching

    Args:
        title: Original movie title (can be unnormalized)

    Returns:
        Override dict with 'title', 'year' (optional), and/or 'file' (optional) keys,
        or None if no override exists

    Example:
        get_override("Prime Cut") -> {"title": "Prime Cut", "year": "1972"}
        get_override("Wall-E") -> {"title": "Wall-E", "file": "p_walle_19753_69f7ff00.webp"}
    """
    overrides = load_poster_overrides()
    normalized = normalize_title(title)

    for override in overrides:
        override_normalized = normalize_title(override['title'])
        if override_normalized == normalized:
            return override

    return None


def extract_year_from_title(title: str) -> Tuple[str, Optional[str]]:
    """
    Extract year from title if present in format: "Title (YYYY)" or "Title (YYYY) extra text"

    The year is extracted even if there's additional text after it (e.g., "INFERNO (1953) in 3D").
    The returned title will have the year removed, but any text before/after is preserved.

    Args:
        title: Movie title potentially with year

    Returns:
        Tuple of (title_without_year, year_or_none)

    Example:
        "The Matrix (1999)" -> ("The Matrix", "1999")
        "INFERNO (1953) in 3D" -> ("INFERNO in 3D", "1953")
        "The Matrix" -> ("The Matrix", None)
    """
    # Match year anywhere in title, not just at the end
    match = re.search(r'\((\d{4})\)', title)
    if match:
        year = match.group(1)
        # Remove the (YYYY) from the title
        title_without_year = title[:match.start()] + title[match.end():]
        # Clean up any double spaces created by removal
        title_without_year = re.sub(r'\s+', ' ', title_without_year).strip()
        return title_without_year, year
    return title, None


# Test function for development
def _test_normalization():
    """Test cases to verify exact match with JavaScript version"""
    test_cases = [
        ("The Matrix: 25th Anniversary Q&A", "the_matrix", "the_matrix.webp"),
        ("Willy Wonka & the Chocolate Factory", "willy_wonka_and_the_chocolate_factory", "willy_wonka_and_the_chocolate_factory.webp"),
        ("Movie Q&A + Panel Discussion", "movie", "movie.webp"),
        ("Film: 50th Anniversary", "film", "film.webp"),
        ("THE ROOM (RE-RELEASE)", "the_room", "the_room.webp"),
        ("Test in 70mm", "test", "test.webp"),
        ("Something (TAMIL)", "something", "something.webp"),
        ("AFTER HOURS", "after_hours", "after_hours.webp"),
    ]

    print("Testing title normalization:")
    print("-" * 80)

    all_passed = True
    for original, expected_normalized, expected_filename in test_cases:
        search = normalize_for_tmdb_search(original)
        normalized = normalize_title(original)
        filename = create_poster_filename(normalized)

        passed = (normalized == expected_normalized and filename == expected_filename)
        status = "✓" if passed else "✗"

        print(f"{status} Original: {original}")
        print(f"  Search:     {search}")
        print(f"  Normalized: {normalized} (expected: {expected_normalized})")
        print(f"  Filename:   {filename} (expected: {expected_filename})")

        if not passed:
            all_passed = False
            print(f"  ERROR: Mismatch!")
        print()

    # Test overrides
    print("\nTesting poster overrides:")
    print("-" * 80)

    test_overrides = ["Prime Cut", "Wall-E", "THE ROOM", "Nonexistent Movie"]
    for title in test_overrides:
        override = get_override(title)
        print(f"Title: {title}")
        print(f"  Override: {override}")
        print()

    print("-" * 80)
    print(f"Result: {'All tests passed!' if all_passed else 'Some tests failed!'}")
    return all_passed


if __name__ == '__main__':
    _test_normalization()
