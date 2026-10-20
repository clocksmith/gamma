function palindromePairs(words) {
  const indexByWord = new Map();
  for (let index = 0; index < words.length; index++) indexByWord.set(words[index], index);
  const result = [];
  const seen = new Set();

  function isPalindrome(word, start, end) {
    while (start < end) {
      if (word[start++] !== word[end--]) return false;
    }
    return true;
  }

  function addPair(left, right) {
    if (left === undefined || right === undefined || left === right) return;
    const key = `${left},${right}`;
    if (seen.has(key)) return;
    seen.add(key);
    result.push([left, right]);
  }

  for (let index = 0; index < words.length; index++) {
    const word = words[index];
    for (let cut = 0; cut <= word.length; cut++) {
      if (isPalindrome(word, 0, cut - 1)) {
        const reversedSuffix = word.slice(cut).split('').reverse().join('');
        addPair(indexByWord.get(reversedSuffix), index);
      }
      if (cut < word.length && isPalindrome(word, cut, word.length - 1)) {
        const reversedPrefix = word.slice(0, cut).split('').reverse().join('');
        addPair(index, indexByWord.get(reversedPrefix));
      }
    }
  }
  return result;
}
