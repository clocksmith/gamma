function shortestDistance(wordsDict, word1, word2) {
  let first = -1, second = -1, best = Infinity;
  for (let i = 0; i < wordsDict.length; i++) {
    if (wordsDict[i] === word1) first = i;
    if (wordsDict[i] === word2) second = i;
    if (first >= 0 && second >= 0) best = Math.min(best, Math.abs(first - second));
  }
  return best;
}
