class Solution {
  search(values, value) {
    let left = 0;
    let right = values.length;
    while (left < right) {
      const index = left + Math.floor((right - left) / 2);
      if (values[index] < value) left = index + 1;
      else right = index;
    }
    return left < values.length && values[left] === value ? left : -1;
  }
}
