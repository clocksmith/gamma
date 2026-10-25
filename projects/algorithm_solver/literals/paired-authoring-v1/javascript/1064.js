class Solution {
  fixedPoint(values) {
    let low = 0;
    let high = values.length;
    while (low < high) {
      const middle = low + Math.floor((high - low) / 2);
      if (values[middle] < middle) {
        low = middle + 1;
      } else {
        high = middle;
      }
    }
    return low < values.length && values[low] === low ? low : -1;
  }
}
