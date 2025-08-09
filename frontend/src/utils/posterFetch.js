const fs = require('fs').promises;
const path = require('path');
const fetch = require('node-fetch');
const posterOverrides = require('../data/posterOverrides.json');
const BLACKLIST_PHRASES = require('../data/blacklistPosterPhrases.js');

async function fetchPoster(title, year = null) {
  const url = new URL(`http://localhost:3001/poster/${encodeURIComponent(title)}`);
  if (year) url.searchParams.append('year', year);

  const normTitle = normalizeTitle(title);
  const override = posterOverrides.find(o => normalizeTitle(o.title) === normTitle);
  const posterDir = path.join(__dirname, '../../public/posters');
  const fixedPosterDir = path.join(__dirname, '../../public/fixed_posters');

  if (override?.file) {
    // Handle file override
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
    return; // Skip default fetch for file overrides
  }

  // Handle year-based override or default fetch
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
      await fs.writeFile(path.join(posterDir, `${normTitle.replace(/\s+/g, '_')}.webp`), buffer);
      console.log(`Fetched and saved: ${data.posterUrl}`);
    } else {
      console.log(`No poster found for: ${title}`);
    }
  } catch (error) {
    console.error(`Error fetching poster for ${title}: ${error.message}`);
  }
}

function normalizeTitle(title) {
  let cleanedTitle = title;
  for (const phrase of BLACKLIST_PHRASES) {
    const regex = new RegExp(phrase, 'gi');
    cleanedTitle = cleanedTitle.replace(regex, '').trim();
  }
  // Preserve special characters, only collapse multiple spaces
  return cleanedTitle.toLowerCase().replace(/\s+/g, ' ').trim();
}

async function fetchAllPosters() {
  const movies = require('../data/movies.json');
  for (const movie of movies) {
    const match = movie.title.match(/^(.*?)(?:\s*\((\d{4})\))?$/);
    const title = match?.[1]?.trim() ?? movie.title;
    const year = match?.[2];
    await fetchPoster(title, year);
  }
}

fetchAllPosters().catch(console.error);