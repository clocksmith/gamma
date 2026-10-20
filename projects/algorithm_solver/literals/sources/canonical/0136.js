class Solution {
  singleNumber(values) {
    let result = 0;
    for (const value of values) {
      result ^= value;
    }
    return result;
  }
}
