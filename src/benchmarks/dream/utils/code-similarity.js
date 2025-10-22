/**
 * Code Similarity Utilities
 * Tools for detecting duplicate code and measuring similarity between outputs
 */

import crypto from 'crypto';

/**
 * Normalize code by removing comments and excess whitespace
 * for fairer comparison
 */
export function normalizeCode(code) {
  if (!code) return '';

  return code
    // Remove single-line comments
    .replace(/\/\/.*$/gm, '')
    // Remove multi-line comments
    .replace(/\/\*[\s\S]*?\*\//g, '')
    // Remove excess whitespace
    .replace(/\s+/g, ' ')
    // Trim
    .trim();
}

/**
 * Generate a hash of code for quick duplicate detection
 */
export function hashCode(code) {
  if (!code) return null;

  const normalized = normalizeCode(code);
  return crypto.createHash('sha256').update(normalized).digest('hex');
}

/**
 * Calculate Levenshtein distance between two strings
 * Returns the minimum number of edits needed to transform s1 into s2
 */
export function levenshteinDistance(s1, s2) {
  if (!s1 || !s2) return Math.max(s1?.length || 0, s2?.length || 0);

  const len1 = s1.length;
  const len2 = s2.length;

  // Create a 2D array for dynamic programming
  const matrix = Array(len1 + 1).fill(null).map(() => Array(len2 + 1).fill(0));

  // Initialize first column and row
  for (let i = 0; i <= len1; i++) matrix[i][0] = i;
  for (let j = 0; j <= len2; j++) matrix[0][j] = j;

  // Fill the matrix
  for (let i = 1; i <= len1; i++) {
    for (let j = 1; j <= len2; j++) {
      const cost = s1[i - 1] === s2[j - 1] ? 0 : 1;
      matrix[i][j] = Math.min(
        matrix[i - 1][j] + 1,      // deletion
        matrix[i][j - 1] + 1,      // insertion
        matrix[i - 1][j - 1] + cost // substitution
      );
    }
  }

  return matrix[len1][len2];
}

/**
 * Calculate similarity ratio between two code strings (0-1)
 * Uses normalized Levenshtein distance
 */
export function codeSimilarity(code1, code2) {
  if (!code1 && !code2) return 1.0;
  if (!code1 || !code2) return 0.0;

  const normalized1 = normalizeCode(code1);
  const normalized2 = normalizeCode(code2);

  if (normalized1 === normalized2) return 1.0;

  const distance = levenshteinDistance(normalized1, normalized2);
  const maxLength = Math.max(normalized1.length, normalized2.length);

  if (maxLength === 0) return 1.0;

  return 1.0 - (distance / maxLength);
}

/**
 * Detect duplicate code in a set of code samples
 * Returns groups of identical code
 */
export function findDuplicates(codeSamples) {
  const hashGroups = new Map();

  codeSamples.forEach((sample, index) => {
    const hash = hashCode(sample.code);
    if (!hash) return;

    if (!hashGroups.has(hash)) {
      hashGroups.set(hash, []);
    }
    hashGroups.get(hash).push({ ...sample, index });
  });

  // Filter to only groups with duplicates
  const duplicateGroups = [];
  hashGroups.forEach((group, hash) => {
    if (group.length > 1) {
      duplicateGroups.push({
        hash,
        count: group.length,
        samples: group
      });
    }
  });

  return duplicateGroups;
}

/**
 * Calculate statistics about code variation across runs
 */
export function analyzeCodeVariation(codeSamples) {
  if (!codeSamples || codeSamples.length === 0) {
    return {
      totalSamples: 0,
      uniqueOutputs: 0,
      duplicateRate: 0,
      avgSimilarity: 0,
      duplicateGroups: []
    };
  }

  const duplicateGroups = findDuplicates(codeSamples);
  const totalSamples = codeSamples.length;
  const uniqueHashes = new Set(codeSamples.map(s => hashCode(s.code))).size;
  const duplicateRate = totalSamples > 0 ? (totalSamples - uniqueHashes) / totalSamples : 0;

  // Calculate average pairwise similarity
  let totalSimilarity = 0;
  let comparisons = 0;

  for (let i = 0; i < codeSamples.length; i++) {
    for (let j = i + 1; j < codeSamples.length; j++) {
      totalSimilarity += codeSimilarity(codeSamples[i].code, codeSamples[j].code);
      comparisons++;
    }
  }

  const avgSimilarity = comparisons > 0 ? totalSimilarity / comparisons : 0;

  return {
    totalSamples,
    uniqueOutputs: uniqueHashes,
    duplicateRate,
    avgSimilarity,
    duplicateGroups
  };
}

/**
 * Calculate variance and standard deviation for a numeric array
 */
export function calculateVariance(values) {
  if (!values || values.length === 0) {
    return { mean: 0, variance: 0, stdDev: 0, min: 0, max: 0 };
  }

  const n = values.length;
  const mean = values.reduce((sum, val) => sum + val, 0) / n;
  const variance = values.reduce((sum, val) => sum + Math.pow(val - mean, 2), 0) / n;
  const stdDev = Math.sqrt(variance);
  const min = Math.min(...values);
  const max = Math.max(...values);

  return {
    mean,
    variance,
    stdDev,
    min,
    max,
    coefficientOfVariation: mean !== 0 ? stdDev / mean : 0
  };
}
