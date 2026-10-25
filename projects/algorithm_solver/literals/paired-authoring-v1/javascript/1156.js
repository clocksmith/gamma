function letterCounts(text) {
  const counts = Array(26).fill(0);
  const firstCode = "a".charCodeAt(0);
  for (const character of text) {
    counts[character.charCodeAt(0) - firstCode] += 1;
  }
  return counts;
}


class Solution {
  maxRepOpt1(text) {
    const totals = letterCounts(text);
    let best = 0;
    for (let letterIndex = 0; letterIndex < 26; letterIndex += 1) {
      if (totals[letterIndex] === 0) {
        continue;
      }
      const letter = String.fromCharCode("a".charCodeAt(0) + letterIndex);
      let left = 0;
      let different = 0;
      for (let right = 0; right < text.length; right += 1) {
        if (text[right] !== letter) {
          different += 1;
        }
        while (different > 1) {
          if (text[left] !== letter) {
            different -= 1;
          }
          left += 1;
        }
        best = Math.max(best, Math.min(right - left + 1, totals[letterIndex]));
      }
    }
    return best;
  }
}
