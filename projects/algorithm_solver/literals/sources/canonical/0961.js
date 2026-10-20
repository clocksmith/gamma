class Solution {
  repeatedNTimes(values) {
    const counts = {};
    for (const value of values) {
      if (counts[value]) {
        return value;
      }
      counts[value] = true;
    }
    return null;
  }
}
