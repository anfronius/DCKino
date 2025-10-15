import { normalizeTitle, normalizeForTmdbSearch, createPosterFilename } from './titleNormalizer.js';
import CONFIG from '@shared/title_processing.json';

const POSTER_OVERRIDES = CONFIG.posterOverrides;

// Get API URL from environment variable or use development default
const getApiUrl = () => {
  return import.meta.env.VITE_API_URL || 'http://localhost:3002';
};

export async function getPosterUrl(title, theaterID) {
  const match = title.match(/^(.*?)(?:\s*\((\d{4})\))?$/);
  const cleanTitle = match?.[1]?.trim() ?? title;
  let year = match?.[2];

  // Use filename version for overrides and static files
  const filenameVersion = normalizeTitle(cleanTitle);
  const override = POSTER_OVERRIDES.find(o => normalizeTitle(o.title) === filenameVersion);
  if (override?.file) {
    return `/fixed_posters/${override.file}`; // Static path for overrides
  }

  // Use override year if available
  const effectiveYear = override?.year || year;

  // Static path in production
  if (process.env.NODE_ENV === 'production') {
    return `/posters/${createPosterFilename(filenameVersion, effectiveYear)}`;
  }

  // Development: Use search version for server API calls
  const searchTitle = normalizeForTmdbSearch(cleanTitle);
  const posterServerUrl = import.meta.env.VITE_API_URL || 'http://localhost:3002';
  const url = new URL(`${posterServerUrl}/poster/${encodeURIComponent(searchTitle)}`);
  if (effectiveYear) url.searchParams.append('year', effectiveYear);

  try {
    const response = await fetch(url);
    if (!response.ok) return null;
    const data = await response.json();
    return data.posterUrl ? `${getApiUrl()}${data.posterUrl}` : null;
  } catch {
    return null;
  }
}