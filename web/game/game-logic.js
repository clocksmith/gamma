import { MathUtils } from '../utils/math.js';

/**
 * Configuration for choice generation
 */
const CHOICE_CONFIG = {
  minProbabilityThreshold: 0.001,  // Minimum probability to be considered (0.1%)
  maxSimilarityScore: 0.8,        // Maximum similarity between choices
  preferWholeWords: true,          // Prefer tokens that look like whole words
};

/**
 * Check if a token is a "good" choice (readable, meaningful)
 */
function isGoodToken(token, engine) {
  const text = token.text;

  // Reject special tokens
  if (engine.isSpecialToken(token.id)) return false;

  // Reject symbols and operators
  if (/^[<>\[\]{}()=+*\/\\|@#$%^&~`]/.test(text)) return false;

  // Reject whitespace-only tokens
  if (!/\S/.test(text)) return false;

  // Reject very low probability tokens
  if (token.prob < CHOICE_CONFIG.minProbabilityThreshold) return false;

  // Reject tokens that are just numbers (usually not interesting)
  if (/^\d+$/.test(text.trim())) return false;

  // Reject tokens that start with special characters (except leading space for subwords)
  if (/^[^\w\s]/.test(text) && !text.startsWith(' ')) return false;

  return true;
}

/**
 * Calculate similarity between two token texts
 * Returns 0-1 where 1 is identical
 */
function calculateSimilarity(text1, text2) {
  const t1 = text1.toLowerCase().trim();
  const t2 = text2.toLowerCase().trim();

  if (t1 === t2) return 1;

  // Check if one is a prefix/suffix of another
  if (t1.includes(t2) || t2.includes(t1)) {
    return 0.8;
  }

  // Simple character-based similarity
  const chars1 = new Set(t1);
  const chars2 = new Set(t2);
  const intersection = new Set([...chars1].filter(c => chars2.has(c)));
  const union = new Set([...chars1, ...chars2]);

  return intersection.size / union.size;
}

/**
 * Score a token for quality as a choice
 * Higher score = better choice
 */
function scoreToken(token, isCorrect) {
  let score = 0;
  const text = token.text.trim();

  // Prefer tokens with higher probability
  score += Math.log(token.prob + 1e-10) * 10;

  // Prefer whole words (start with space or are at sentence start)
  if (text.startsWith(' ') || /^[A-Z]/.test(text)) {
    score += 5;
  }

  // Prefer readable length (3-15 chars)
  if (text.length >= 3 && text.length <= 15) {
    score += 3;
  }

  // Penalize very short tokens (less interesting)
  if (text.length === 1) {
    score -= 5;
  }

  // Bonus for alphabetic tokens
  if (/^[\s]*[a-zA-Z]+$/.test(text)) {
    score += 2;
  }

  return score;
}

/**
 * Select diverse distractors that are different from the correct answer
 */
function selectDiverseDistractors(candidates, correct, numDistractors) {
  const selected = [];
  const correctText = correct.text;

  // Sort candidates by quality score
  const scoredCandidates = candidates
    .filter(c => c !== correct)
    .map(c => ({ token: c, score: scoreToken(c, false) }))
    .sort((a, b) => b.score - a.score);

  for (const { token } of scoredCandidates) {
    if (selected.length >= numDistractors) break;

    // Check similarity with correct answer
    const simToCorrect = calculateSimilarity(token.text, correctText);
    if (simToCorrect > CHOICE_CONFIG.maxSimilarityScore) continue;

    // Check similarity with already selected distractors
    let tooSimilar = false;
    for (const sel of selected) {
      const simToSel = calculateSimilarity(token.text, sel.text);
      if (simToSel > CHOICE_CONFIG.maxSimilarityScore) {
        tooSimilar = true;
        break;
      }
    }

    if (!tooSimilar) {
      selected.push(token);
    }
  }

  return selected;
}

/**
 * Generate choices for a round
 * @param {Array} topTokens - Top predicted tokens from the model
 * @param {Object} engine - The LLM engine
 * @param {number} numChoices - Number of choices to generate (default 4)
 * @returns {Object} - { choices, correctIndex, correctToken }
 */
export function generateChoices(topTokens, engine, numChoices = 4) {
  // Filter to good tokens only
  const filtered = topTokens.filter(token => isGoodToken(token, engine));

  // If we don't have enough good tokens, fall back to raw top tokens
  if (filtered.length < numChoices) {
    console.warn('Not enough good tokens, using raw top tokens');
    const choices = topTokens.slice(0, numChoices).map(t => ({
      ...t,
      text: t.text || '<?>'
    }));

    return {
      choices,
      correctIndex: 0,
      correctToken: choices[0]
    };
  }

  // The correct answer is the highest probability good token
  const correct = filtered[0];

  // Select diverse distractors
  const distractors = selectDiverseDistractors(filtered, correct, numChoices - 1);

  // If we couldn't find enough diverse distractors, use sequential ones
  if (distractors.length < numChoices - 1) {
    const remaining = numChoices - 1 - distractors.length;
    const additional = filtered
      .filter(t => t !== correct && !distractors.includes(t))
      .slice(0, remaining);
    distractors.push(...additional);
  }

  // Combine correct answer with distractors
  const choices = [correct, ...distractors];

  // Shuffle choices
  MathUtils.shuffleArray(choices);

  // Find the correct index after shuffling
  const correctIndex = choices.findIndex(c => c === correct);

  return {
    choices,
    correctIndex,
    correctToken: correct
  };
}

/**
 * Calculate the difficulty of a round based on token probabilities
 * @param {Array} choices - The choices for the round
 * @param {Object} correctToken - The correct token
 * @returns {string} - 'easy', 'medium', or 'hard'
 */
export function calculateDifficulty(choices, correctToken) {
  const correctProb = correctToken.prob;

  // Calculate the probability gap between correct and best distractor
  const distractorProbs = choices
    .filter(c => c !== correctToken)
    .map(c => c.prob);

  const maxDistractorProb = Math.max(...distractorProbs);
  const probGap = correctProb - maxDistractorProb;

  if (correctProb > 0.5 || probGap > 0.3) {
    return 'easy';
  } else if (correctProb > 0.2 || probGap > 0.1) {
    return 'medium';
  } else {
    return 'hard';
  }
}
