function countValues(values) {
  const counts = {};
  for (const value of values) {
    counts[value] = (counts[value] || 0) + 1;
  }
  return counts;
}
class Solution {
  isAnagram(values, other) {
    const counts = countValues(values);
    const otherCounts = countValues(other);
    for (const value of values) {
      if (counts[value] !== (otherCounts[value] || 0)) {
        return false;
      }
    }
    for (const value of other) {
      if (otherCounts[value] !== (counts[value] || 0)) {
        return false;
      }
    }
    return true;
  }
}
