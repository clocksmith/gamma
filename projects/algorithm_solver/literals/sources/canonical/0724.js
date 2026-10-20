class Solution {
  pivotIndex(values) {
    let right = 0;
    for (const value of values) right += value;
    let left = 0;
    for (let index = 0; index < values.length; index++) {
      right -= values[index];
      if (left === right) return index;
      left += values[index];
    }
    return -1;
  }
}
