class Solution {
  findLengthOfLCIS(values) {
    let count = 1;
    let result = 1;
    for (let index = 1; index < values.length; index++) {
      count = values[index - 1] < values[index] ? count + 1 : 1;
      result = Math.max(result, count);
    }
    return result;
  }
}
