class Solution {
  numSpecialEquivGroups(words) {
    const groups = new Set();
    for (const word of words) {
      const counts = new Array(52).fill(0);
      for (let index = 0; index < word.length; index += 1) {
        const slot = 26 * (index % 2) + word.charCodeAt(index) - 97;
        counts[slot] += 1;
      }
      groups.add(counts.join(","));
    }
    return groups.size;
  }
}
