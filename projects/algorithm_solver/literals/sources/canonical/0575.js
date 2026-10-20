class Solution {
  distributeCandies(values) {
    const counts = {};
    let result = 0;
    for (const value of values) {
      if (counts[value] !== true) {
        counts[value] = true;
        result += 1;
      }
    }
    const limit = Math.floor(values.length / 2);
    if (result < limit) {
      return result;
    }
    return limit;
  }
}
