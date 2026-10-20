class Solution {
  findMaxAverage(values, length) {
    let count = 0;
    for (let index = 0; index < length; index++) count += values[index];
    let result = count;
    for (let index = length; index < values.length; index++) {
      count += values[index] - values[index - length];
      if (count > result) result = count;
    }
    return result / length;
  }
}
