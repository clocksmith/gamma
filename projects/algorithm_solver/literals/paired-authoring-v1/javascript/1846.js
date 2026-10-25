class Solution {
  maximumElementAfterDecrementingAndRearranging(arr) {
    const ordered = arr.slice().sort((first, second) => first - second);
    let largest = 0;
    for (const value of ordered) {
      largest = Math.min(value, largest + 1);
    }
    return largest;
  }
}
