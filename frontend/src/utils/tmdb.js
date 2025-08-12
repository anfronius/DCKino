import { normalizeTitle, normalizeForTmdbSearch, createPosterFilename } from './titleNormalizer.js';
import POSTER_OVERRIDES from './posterOverrides.json';

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

  // Static path in production
  if (process.env.NODE_ENV === 'production') {
    return `/posters/${createPosterFilename(filenameVersion)}`;
  }

  // Development: Use search version for server API calls
  const searchTitle = normalizeForTmdbSearch(cleanTitle);
  const url = new URL(`http://localhost:3001/poster/${encodeURIComponent(searchTitle)}`);
  const effectiveYear = override?.year || year;
  if (effectiveYear) url.searchParams.append('year', effectiveYear);

  try {
    const response = await fetch(url);
    if (!response.ok) return null;
    const data = await response.json();
    return data.posterUrl ? `http://localhost:3001${data.posterUrl}` : null;
  } catch {
    return null;
  }
}