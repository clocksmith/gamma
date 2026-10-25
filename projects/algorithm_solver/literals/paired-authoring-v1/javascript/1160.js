function letterCounts(text) {
  const counts = Array(26).fill(0);
  const firstCode = "a".charCodeAt(0);
  for (const character of text) {
    counts[character.charCodeAt(0) - firstCode] += 1;
  }
  return counts;
}


class Solution {
  countCharacters(words, chars) {
    const available = letterCounts(chars);
    let total = 0;
    for (const word of words) {
      const required = letterCounts(word);
      let possible = true;
      for (let index = 0; index < 26; index += 1) {
        if (required[index] > available[index]) {
          possible = false;
          break;
        }
      }
      if (possible) {
        total += word.length;
      }
    }
    return total;
  }
}
