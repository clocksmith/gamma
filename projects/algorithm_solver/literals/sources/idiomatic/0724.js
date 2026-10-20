class Solution {
  pivotIndex(values) {
    let right = values.reduce((result, value) => result + value, 0);
    let left = 0;
    return values.findIndex(value => {
      right -= value;
      const result = left === right;
      left += value;
      return result;
    });
  }
}
