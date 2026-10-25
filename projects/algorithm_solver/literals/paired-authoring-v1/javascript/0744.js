function upperBound(values, target) {
  let left = 0;
  let right = values.length;
  while (left < right) {
    const middle = left + Math.floor((right - left) / 2);
    if (values[middle] <= target) {
      left = middle + 1;
    } else {
      right = middle;
    }
  }
  return left;
}

class Solution {
  nextGreatestLetter(letters, target) {
    let index = upperBound(letters, target);
    if (index === letters.length) {
      index = 0;
    }
    return letters[index];
  }
}
