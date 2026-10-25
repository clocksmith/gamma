class Solution {
  numDistinct(s, t) {
    const counts = new Array(t.length + 1).fill(0);
    counts[0] = 1;
    for (let source_index = 0; source_index < s.length; source_index += 1) {
      const character = s[source_index];
      for (let index = t.length - 1; index >= 0; index -= 1) {
        if (character === t[index]) {
          counts[index + 1] += counts[index];
        }
      }
    }
    return counts[counts.length - 1];
  }
}
