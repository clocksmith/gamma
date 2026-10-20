function wordBreak(s, wordDict) {
  const words = new Set(wordDict);
  const maxWordLength = wordDict.reduce(
    (maximum, word) => Math.max(maximum, word.length),
    0
  );
  const breakable = new Array(s.length + 1).fill(false);
  breakable[s.length] = true;

  for (let start = s.length - 1; start >= 0; start -= 1) {
    const latestEnd = Math.min(s.length, start + maxWordLength);
    for (let end = start + 1; end <= latestEnd; end += 1) {
      if (words.has(s.slice(start, end)) && breakable[end]) {
        breakable[start] = true;
        break;
      }
    }
  }

  const memo = new Map();

  function build(start) {
    if (start === s.length) {
      return [''];
    }
    if (!breakable[start]) {
      return [];
    }
    if (memo.has(start)) {
      return memo.get(start);
    }

    const sentences = [];
    const latestEnd = Math.min(s.length, start + maxWordLength);

    for (let end = start + 1; end <= latestEnd; end += 1) {
      const word = s.slice(start, end);
      if (!words.has(word) || !breakable[end]) {
        continue;
      }

      for (const suffix of build(end)) {
        sentences.push(suffix.length === 0 ? word : `${word} ${suffix}`);
      }
    }

    memo.set(start, sentences);
    return sentences;
  }

  return build(0);
}
