class Solution {
  relativeSortArray(arr1, arr2) {
    const counts = Array(1001).fill(0);
    for (const value of arr1) {
      counts[value] += 1;
    }
    const result = [];
    for (const value of arr2) {
      while (counts[value] > 0) {
        result.push(value);
        counts[value] -= 1;
      }
    }
    for (let value = 0; value <= 1000; value += 1) {
      while (counts[value] > 0) {
        result.push(value);
        counts[value] -= 1;
      }
    }
    return result;
  }
}
