class Solution {
  maxProfit(values) {
    if (values.length === 0) return 0;
    let minimum = values[0];
    let result = 0;
    for (const value of values) {
      const count = value - minimum;
      if (count > result) result = count;
      if (value < minimum) minimum = value;
    }
    return result;
  }
}
