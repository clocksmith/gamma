class Solution {
  singleNumber(values) {
    return values.reduce((result, value) => result ^ value, 0);
  }
}
