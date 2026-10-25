class Solution {
  maxSubstringLength(text) {
    const first = new Map();
    const last = new Map();
    for (let index = 0; index < text.length; index += 1) {
      const character = text[index];
      if (!first.has(character)) {
        first.set(character, index);
      }
      last.set(character, index);
    }
    let best = -1;
    for (const left of first.values()) {
      let requiredEnd = left;
      for (let right = left; right < text.length; right += 1) {
        const character = text[right];
        if (first.get(character) < left) {
          break;
        }
        requiredEnd = Math.max(requiredEnd, last.get(character));
        if (right === requiredEnd && right - left + 1 < text.length) {
          best = Math.max(best, right - left + 1);
        }
      }
    }
    return best;
  }
}
