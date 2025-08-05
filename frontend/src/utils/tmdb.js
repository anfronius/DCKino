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
  let query = normalizeTitle(match?.[1]?.trim() ?? title);
  let year = match?.[2];

  const override = POSTER_OVERRIDES.find(o => normalizeTitle(o.title) === query);
  if (override?.file) {
    return `/fixed_posters/${override.file}`; // Priority: custom file
  }

  let posterUrl;
  if (process.env.NODE_ENV === 'production') {
    posterUrl = `/posters/${query.replace(/\s+/g, '_')}.webp`;
  } else {
    const url = new URL(`http://localhost:3001/poster/${encodeURIComponent(query)}`);
    const effectiveYear = override?.year || year;
    if (effectiveYear) url.searchParams.append('year', effectiveYear);

    try {
      const response = await fetch(url);
      if (!response.ok) return null;
      const data = await response.json();
      posterUrl = data.posterUrl ? `http://localhost:3001${data.posterUrl}` : null;
    } catch {
      return null;
    }
  }

  return posterUrl || null;
}