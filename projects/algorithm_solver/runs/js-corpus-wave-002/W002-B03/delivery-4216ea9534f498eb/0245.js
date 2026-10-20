function shortestWordDistance(wordsDict, word1, word2) {
  let first = -1, second = -1, previous = -1, best = Infinity;
  for (let i = 0; i < wordsDict.length; i++) {
    if (word1 === word2) {
      if (wordsDict[i] === word1) { if (previous >= 0) best = Math.min(best, i - previous); previous = i; }
    } else {
      if (wordsDict[i] === word1) first = i;
      if (wordsDict[i] === word2) second = i;
      if (first >= 0 && second >= 0) best = Math.min(best, Math.abs(first - second));
    }
  }
  return best;
}
