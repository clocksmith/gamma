class Solution {
  findLengthOfLCIS(values) {
    let count = 1;
    let result = 1;
    for (let index = 1; index < values.length; index++) {
      if (values[index - 1] < values[index]) {
        count++;
        if (count > result) result = count;
      } else count = 1;
    }
    return result;
  }
}
