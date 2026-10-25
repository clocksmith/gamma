class Solution {
  findLengthOfShortestSubarray(arr) {
    const size = arr.length;
    if (size <= 1) {
      return 0;
    }
    let left = 0;
    while (left + 1 < size && arr[left] <= arr[left + 1]) {
      left += 1;
    }
    if (left === size - 1) {
      return 0;
    }
    let right = size - 1;
    while (right > 0 && arr[right - 1] <= arr[right]) {
      right -= 1;
    }
    let best = Math.min(size - left - 1, right);
    let first = 0;
    let second = right;
    while (first <= left && second < size) {
      if (arr[first] <= arr[second]) {
        best = Math.min(best, second - first - 1);
        first += 1;
      } else {
        second += 1;
      }
    }
    return best;
  }
}
