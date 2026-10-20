function encodeTextKey(text) {
  return '$' + text;
}
function indexSimilarWords(similarPairs) {
  const neighborsByKey = {};
  for (const wordPair of similarPairs) {
    const leftKey = encodeTextKey(wordPair[0]);
    const rightKey = encodeTextKey(wordPair[1]);
    if (!(leftKey in neighborsByKey)) {
      neighborsByKey[leftKey] = {};
    }
    if (!(rightKey in neighborsByKey)) {
      neighborsByKey[rightKey] = {};
    }
    neighborsByKey[leftKey][rightKey] = true;
    neighborsByKey[rightKey][leftKey] = true;
  }
  return neighborsByKey;
}
function sentencesAreSimilar(leftWords, rightWords, similarPairs) {
  if (leftWords.length !== rightWords.length) {
    return false;
  }
  const neighborsByKey = indexSimilarWords(similarPairs);
  for (let wordIndex = 0; wordIndex < leftWords.length; wordIndex += 1) {
    if (leftWords[wordIndex] !== rightWords[wordIndex]) {
      const leftKey = encodeTextKey(leftWords[wordIndex]);
      const rightKey = encodeTextKey(rightWords[wordIndex]);
      if (!(leftKey in neighborsByKey) || !(rightKey in neighborsByKey[leftKey])) {
        return false;
      }
    }
  }
  return true;
}
function solve(sentence1, sentence2, similarPairs) {
  return sentencesAreSimilar(sentence1, sentence2, similarPairs);
}
