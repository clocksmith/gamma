function wordBreak(s, wordDict) {
  const words = new Set(wordDict);
  const maxWordLength = wordDict.reduce(
    (maximum, word) => Math.max(maximum, word.length),
    0
  );
  const reachable = new Array(s.length + 1).fill(false);
  reachable[0] = true;

  for (let end = 1; end <= s.length; end += 1) {
    const earliestStart = Math.max(0, end - maxWordLength);
    for (let start = end - 1; start >= earliestStart; start -= 1) {
      if (reachable[start] && words.has(s.slice(start, end))) {
        reachable[end] = true;
        break;
      }
    }
  }

  return reachable[s.length];
}
