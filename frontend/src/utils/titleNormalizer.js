import BLACKLIST_PHRASES from './blacklistPosterPhrases.js';

/**
 * Normalizes title for TMDb search - matches Python server exactly
 * This is what gets sent to the poster server for TMDb API searches
 * @param {string} title - The title to normalize
 * @returns {string} - Normalized title for TMDb search (with spaces)
 */
export function normalizeForTmdbSearch(title) {
  let cleanedTitle = title;
  
  // Apply blacklist phrase removal first
  for (const phrase of BLACKLIST_PHRASES) {
    const regex = new RegExp(phrase, 'gi');
    cleanedTitle = cleanedTitle.replace(regex, '').trim();
  }
  
  // Clean up any trailing punctuation and incomplete patterns left by blacklist removal
  cleanedTitle = cleanedTitle
    .replace(/[,;:+]\s*$/, '')        // Remove trailing punctuation
    .replace(/\s*\(\s*\)\s*$/, '')    // Remove empty parentheses
    .replace(/\s*\+\s*$/, '')         // Remove trailing plus signs
    .replace(/:\s*$/, '')             // Remove trailing colons
    .trim();
  
  // Apply Python server normalization exactly (lines 47):
  // "remove #, :, standardize case and spacing"
  return cleanedTitle
    .toLowerCase()
    .replace(/#/g, '')
    .replace(/:/g, '')
    .replace(/\./g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Creates filename exactly like Python poster server
 * This matches poster_server.py lines 49 exactly
 * @param {string} searchTitle - Already normalized search title (with spaces)
 * @returns {string} - Safe filename (with underscores)
 */
export function normalizeTitle(title) {
  // Step 1: Get the search title
  const searchTitle = normalizeForTmdbSearch(title);
  
  // Step 2: Create safe filename matching Python server exactly (line 49)
  // Remove ALL special chars and Unicode for web compatibility
  const safeTitle = searchTitle
    .replace(/\?/g, '')
    .replace(/[''']/g, '')         // Remove all apostrophe variants (regular and Unicode)
    .replace(/[,]/g, '')           // Remove commas  
    .replace(/[!]/g, '')           // Remove exclamation marks
    .replace(/[&]/g, 'and')        // Replace & with 'and'
    .replace(/\s+/g, '_');         // Replace spaces with underscores
    
  return safeTitle;
}

/**
 * Creates a poster filename exactly like the Python server
 * @param {string} normalizedTitle - Already normalized title
 * @returns {string} - Filename with .webp extension
 */
export function createPosterFilename(normalizedTitle) {
  return `${normalizedTitle}.webp`;
}