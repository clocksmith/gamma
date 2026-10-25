class Solution {
  numKLenSubstrNoRepeats(text, k) {
    const counts = new Map();
    let total = 0;
    for (let right = 0; right < text.length; right += 1) {
      const character = text[right];
      counts.set(character, (counts.get(character) || 0) + 1);
      if (right >= k) {
        const outgoing = text[right - k];
        counts.set(outgoing, counts.get(outgoing) - 1);
        if (counts.get(outgoing) === 0) {
          counts.delete(outgoing);
        }
      }
      if (right + 1 >= k && counts.size === k) {
        total += 1;
      }
    }
    return total;
  }
}
