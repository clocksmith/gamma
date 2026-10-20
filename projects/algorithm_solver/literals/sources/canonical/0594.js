class Solution {
  findLHS(values) {
    const counts = {};
    for (const value of values) counts[value] = (counts[value] || 0) + 1;
    let result = 0;
    for (const value of values) {
      const count = counts[value + 1] || 0;
      if (count > 0) result = Math.max(result, counts[value] + count);
    }
    return result;
  }
}
