import BLACKLIST_PHRASES from './blacklist.js';
import POSTER_OVERRIDES from './posterOverrides.json';

function normalizeTitle(title) {
  let cleanedTitle = title;
  for (const phrase of BLACKLIST_PHRASES) {
    const regex = new RegExp(phrase, 'gi');
    cleanedTitle = cleanedTitle.replace(regex, '').trim();
  }
  return cleanedTitle.toLowerCase().replace(/[^\w\s]/g, '').replace(/\s+/g, ' ').trim();
}

export async function getPosterUrl(title, theaterID) {
  const match = title.match(/^(.*?)(?:\s*\((\d{4})\))?$/);
  let query = normalizeTitle(match?.[1]?.trim() ?? title); // Normalize here
  let year = match?.[2];

  for (const phrase of BLACKLIST_PHRASES) {
    const regex = new RegExp(phrase, 'gi');
    query = query.replace(regex, '').trim(); // Additional cleanup (optional)
  }

  const override = POSTER_OVERRIDES.find(
    entry => entry.title.toLowerCase() === query.toLowerCase()
  );
  if (override?.year) {
    year = override.year;
  }

  const backendUrl = new URL(`http://localhost:3001/poster/${encodeURIComponent(query)}`);
  if (year) {
    backendUrl.searchParams.append('year', year);
  }

  try {
    const response = await fetch(backendUrl);
    if (!response.ok) return null;
    const data = await response.json();
    return data.posterUrl ? `http://localhost:3001${data.posterUrl}` : null;
  } catch {
    return null;
  }
}