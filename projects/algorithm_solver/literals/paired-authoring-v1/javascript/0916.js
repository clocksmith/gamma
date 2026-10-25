function letterCounts(word) {
  const counts = new Array(26).fill(0);
  for (let index = 0; index < word.length; index += 1) {
    counts[word.charCodeAt(index) - 97] += 1;
  }
  return counts;
}

class Solution {
  wordSubsets(words1, words2) {
    const required = new Array(26).fill(0);
    for (const word of words2) {
      const counts = letterCounts(word);
      for (let index = 0; index < 26; index += 1) {
        required[index] = Math.max(required[index], counts[index]);
      }
    }

    const result = [];
    for (const word of words1) {
      const counts = letterCounts(word);
      let qualifies = true;
      for (let index = 0; index < 26; index += 1) {
        if (counts[index] < required[index]) {
          qualifies = false;
          break;
        }
      }
      if (qualifies) {
        result.push(word);
      }
    }
    return result;
  }
}
