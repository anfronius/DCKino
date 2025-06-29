import BLACKLIST_PHRASES from './blacklist.js';
import POSTER_OVERRIDES from './posterOverrides.json';

export async function getPosterUrl(title, theaterID) {
  const TMDB_API_KEY = import.meta.env.VITE_TMDB_API_KEY;

  // Extract title and year if in format: "Movie Title (YYYY)"
  const match = title.match(/^(.*?)(?:\s*\((\d{4})\))?$/);
  let query = match?.[1]?.trim() ?? title;
  let year = match?.[2];

  // Apply phrase blacklist cleanup
  for (const phrase of BLACKLIST_PHRASES) {
    const regex = new RegExp(phrase, 'gi');
    query = query.replace(regex, '').trim();
  }

  // Check poster override
  const override = POSTER_OVERRIDES.find(
    entry => entry.title.toLowerCase() === query.toLowerCase()
  );
  if (override?.year) {
    year = override.year;
  }

  const url = new URL("https://api.themoviedb.org/3/search/movie");
  url.searchParams.append("api_key", TMDB_API_KEY);
  url.searchParams.append("query", query);
  if (year) url.searchParams.append("year", year);

  try {
    const res = await fetch(url);
    if (!res.ok) return null;

    const data = await res.json();
    const posterPath = data?.results?.[0]?.poster_path;
    if (!posterPath) return null;

    return `https://image.tmdb.org/t/p/w342${posterPath}`;
  } catch {
    return null;
  }
}
