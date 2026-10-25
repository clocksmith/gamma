function letterCounts(text) {
  const counts = Array(26).fill(0);
  const firstCode = "a".charCodeAt(0);
  for (const character of text) {
    counts[character.charCodeAt(0) - firstCode] += 1;
  }
  return counts;
}


class Solution {
  rearrangeCharacters(s, target) {
    const available = letterCounts(s);
    const required = letterCounts(target);
    let copies = s.length;
    for (let index = 0; index < 26; index += 1) {
      if (required[index] > 0) {
        copies = Math.min(copies, Math.floor(available[index] / required[index]));
      }
    }
    return copies;
  }
}
