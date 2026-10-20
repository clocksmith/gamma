class Solution {
  firstUniqChar(values) {
    const counts = new Map();
    for (const value of values) {
      if (value >= 'a' && value <= 'z') {
        counts.set(value, (counts.get(value) || 0) + 1);
      }
    }
    for (let index = 0; index < values.length; index++) {
      if (counts.get(values[index]) === 1) return index;
    }
    return -1;
  }
}
