class Solution {
  numberOfSpecialSubstrings(text) {
    const lastSeen = new Map();
    let left = 0;
    let total = 0;
    for (let right = 0; right < text.length; right += 1) {
      const character = text[right];
      const previous = lastSeen.has(character) ? lastSeen.get(character) : -1;
      left = Math.max(left, previous + 1);
      lastSeen.set(character, right);
      total += right - left + 1;
    }
    return total;
  }
}
