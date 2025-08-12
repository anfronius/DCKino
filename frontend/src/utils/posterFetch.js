import { fileURLToPath } from 'url';
import { dirname } from 'path';
import path from 'path'; // Added full path module import
import fs from 'fs/promises';
import fetch from 'node-fetch';
import posterOverrides from './posterOverrides.json' with { type: "json" };
import { normalizeTitle, normalizeForTmdbSearch, createPosterFilename } from './titleNormalizer.js';

// Derive __dirname in ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function fetchPoster(title, year = null) {
  // Send the search-normalized title (with spaces) to the server for TMDb API
  const searchTitle = normalizeForTmdbSearch(title);
  const url = new URL(`http://localhost:3001/poster/${encodeURIComponent(searchTitle)}`);
  if (year) url.searchParams.append('year', year);

  // But use the filename version for local file operations
  const normTitle = normalizeTitle(title);
  const override = posterOverrides.find(o => normalizeTitle(o.title) === normTitle);
  const posterDir = path.join(__dirname, '../../public/posters');
  const fixedPosterDir = path.join(__dirname, '../../public/fixed_posters');

  if (override?.file) {
    const fixedPath = path.join(fixedPosterDir, override.file);
    try {
      await fs.access(fixedPath);
      console.log(`Using existing override file: ${override.file}`);
    } catch {
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        if (data.posterUrl) {
          const imageResponse = await fetch(`http://localhost:3001${data.posterUrl}`);
          const buffer = await imageResponse.buffer();
          await fs.mkdir(fixedPosterDir, { recursive: true });
          await fs.writeFile(fixedPath, buffer);
          console.log(`Fetched and saved override: ${override.file}`);
        }
      }
    }
    return;
  }

  const effectiveYear = override?.year || year;
  if (effectiveYear) url.searchParams.set('year', effectiveYear);

  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    const data = await response.json();
    if (data.posterUrl) {
      const imageResponse = await fetch(`http://localhost:3001${data.posterUrl}`);
      if (!imageResponse.ok) throw new Error(`Image fetch failed: ${imageResponse.status}`);
      const buffer = await imageResponse.buffer();
      await fs.mkdir(posterDir, { recursive: true });
      await fs.writeFile(path.join(posterDir, createPosterFilename(normTitle)), buffer);
      console.log(`Fetched and saved: ${data.posterUrl}`);
    } else {
      console.log(`No poster found for: ${title}`);
    }
  } catch (error) {
    console.error(`Error fetching poster for ${title}: ${error.message}`);
  }
}


async function fetchAllPosters() {
  const { default: movies } = await import('../data/movies.json', { with: { type: "json" } });
  for (const movie of movies) {
    const match = movie.title.match(/^(.*?)(?:\s*\((\d{4})\))?$/);
    const title = match?.[1]?.trim() ?? movie.title;
    const year = match?.[2];
    await fetchPoster(title, year);
  }
}

// Execute asynchronously
fetchAllPosters().catch(console.error);