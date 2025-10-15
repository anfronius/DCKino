import { fileURLToPath } from 'url';
import { dirname } from 'path';
import path from 'path'; // Added full path module import
import fs from 'fs/promises';
import fetch from 'node-fetch';
import CONFIG from '@shared/title_processing.json' with { type: "json" };
import { normalizeTitle, normalizeForTmdbSearch, createPosterFilename } from './titleNormalizer.js';

const posterOverrides = CONFIG.posterOverrides;

// Derive __dirname in ESM
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Use environment variable for server URL, fallback to local
const POSTER_SERVER_URL = process.env.POSTER_SERVER_URL || 'http://localhost:3002';

console.log(`🎬 Starting poster fetch from server: ${POSTER_SERVER_URL}`);

async function fetchPoster(title, year = null) {
  // Send the search-normalized title (with spaces) to the server for TMDb API
  const searchTitle = normalizeForTmdbSearch(title);
  const url = new URL(`${POSTER_SERVER_URL}/poster/${encodeURIComponent(searchTitle)}`);
  if (year) url.searchParams.append('year', year);

  // But use the filename version for local file operations
  const match = title.match(/^(.*?)(?:\s*\((\d{4})\))?$/);
  const titleWithoutYear = match?.[1]?.trim() ?? title;
  const normTitle = normalizeTitle(titleWithoutYear);
  const override = posterOverrides.find(o => normalizeTitle(o.title) === normTitle);
  const posterDir = path.join(__dirname, '../../public/posters');
  const fixedPosterDir = path.join(__dirname, '../../public/fixed_posters');

  if (override?.file) {
    const fixedPath = path.join(fixedPosterDir, override.file);
    try {
      await fs.access(fixedPath);
      console.log(`✅ Using existing override file: ${override.file}`);
      return 'cached';
    } catch {
      console.log(`📥 Fetching override for: ${title}`);
      const response = await fetch(url);
      if (response.ok) {
        const data = await response.json();
        if (data.posterUrl) {
          const imageResponse = await fetch(`${POSTER_SERVER_URL}${data.posterUrl}`);
          if (imageResponse.ok) {
            const buffer = await imageResponse.buffer();
            await fs.mkdir(fixedPosterDir, { recursive: true });
            await fs.writeFile(fixedPath, buffer);
            console.log(`✅ Fetched and saved override: ${override.file}`);
            return 'fetched';
          }
        }
      }
      console.log(`❌ Failed to fetch override for: ${title}`);
      return 'failed';
    }
  }

  const effectiveYear = override?.year || year;
  if (effectiveYear) url.searchParams.set('year', effectiveYear);

  const posterPath = path.join(posterDir, createPosterFilename(normTitle));

  // Check if poster already exists
  try {
    await fs.access(posterPath);
    console.log(`✅ Poster already exists: ${createPosterFilename(normTitle)}`);
    return 'cached';
  } catch {
    // Poster doesn't exist, fetch it
  }

  try {
    console.log(`📥 Fetching poster for: ${title}`);
    const response = await fetch(url);
    if (!response.ok) {
      console.log(`❌ Server error for ${title}: ${response.status}`);
      return 'failed';
    }

    const data = await response.json();
    if (data.posterUrl) {
      const imageResponse = await fetch(`${POSTER_SERVER_URL}${data.posterUrl}`);
      if (!imageResponse.ok) {
        console.log(`❌ Image fetch failed for ${title}: ${imageResponse.status}`);
        return 'failed';
      }

      const buffer = await imageResponse.buffer();
      await fs.mkdir(posterDir, { recursive: true });
      await fs.writeFile(posterPath, buffer);
      console.log(`✅ Saved: ${createPosterFilename(normTitle)}`);
      return 'fetched';
    } else {
      console.log(`⚠️  No poster found for: ${title}`);
      return 'failed';
    }
  } catch (error) {
    console.error(`❌ Error fetching poster for ${title}: ${error.message}`);
    return 'failed';
  }
}

async function fetchAllPosters() {
  try {
    console.log('🎬 Starting poster fetch process...');

    // Test server connectivity first
    try {
      const healthResponse = await fetch(`${POSTER_SERVER_URL}/health`, { timeout: 10000 });
      if (!healthResponse.ok) {
        throw new Error(`Server health check failed: ${healthResponse.status}`);
      }
      console.log('✅ Poster server is healthy');
    } catch (error) {
      console.error(`❌ Cannot connect to poster server at ${POSTER_SERVER_URL}`);
      console.error('Please ensure the poster server is running or set POSTER_SERVER_URL environment variable');
      process.exit(1);
    }

    const { default: movies } = await import('../data/movies.json', { with: { type: "json" } });
    console.log(`📊 Processing ${movies.length} movie entries...`);

    let processed = 0;
    let fetchedCount = 0;
    let cachedCount = 0;
    let failedCount = 0;
    const failedDetails = [];

    for (const movie of movies) {
      const match = movie.title.match(/^(.*?)(?:\s*\((\d{4})\))?$/);
      const title = match?.[1]?.trim() ?? movie.title;
      const year = match?.[2];

      const result = await fetchPoster(title, year);
      if (result === 'fetched') fetchedCount++;
      else if (result === 'cached') cachedCount++;
      else if (result === 'failed') {
        failedCount++;
        failedDetails.push({ title: movie.title, reason: result.reason || 'unknown' });
      }

      processed++;

      if (processed % 10 === 0) {
        console.log(`📊 Progress: ${processed}/${movies.length} processed (${fetchedCount} fetched, ${cachedCount} cached, ${failedCount} failed)`);
      }
    }

    console.log('\n' + '='.repeat(80));
    console.log(`🎉 Poster fetch complete! Processed ${processed} movies`);
    console.log(`   ✅ Fetched: ${fetchedCount}`);
    console.log(`   💾 Cached: ${cachedCount}`);
    console.log(`   ❌ Failed: ${failedCount}`);

    if (failedCount > 0) {
      console.log('\n⚠️  FAILED POSTERS:');
      console.log('-'.repeat(80));
      failedDetails.forEach(fail => {
        console.log(`   • ${fail.title}`);
      });
      console.log('-'.repeat(80));
      console.log(`\n💡 TIP: Add failed titles to posterOverrides.json with correct year or file path`);
    }
    console.log('='.repeat(80));
    console.log('✅ Exiting poster fetch process...\n');

    // Force exit to ensure build continues
    process.exit(0);

  } catch (error) {
    console.error('❌ Fatal error in fetchAllPosters:', error.message);
    process.exit(1);
  }
}

// Execute asynchronously
fetchAllPosters().catch(error => {
  console.error('❌ Unhandled error:', error);
  process.exit(1);
});