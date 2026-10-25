class Solution {
  findClosestElements(arr, k, x) {
    if (k === 0) {
      return [];
    }

    let left = 0;
    let right = arr.length - k;
    while (left < right) {
      const middle = left + Math.floor((right - left) / 2);
      if (x - arr[middle] > arr[middle + k] - x) {
        left = middle + 1;
      } else {
        right = middle;
      }
    }
    return arr.slice(left, left + k);
  }
}
