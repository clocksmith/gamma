class Solution {
  numJewelsInStones(values, other) {
    const counts = {};
    for (const value of values) {
      counts['$' + value] = true;
    }
    let result = 0;
    for (const value of other) {
      if ('$' + value in counts) {
        result += 1;
      }
    }
    return result;
  }
}
