class Solution {
  numTimesAllBlue(flips) {
    let largest = 0;
    let count = 0;
    for (let index = 0; index < flips.length; index += 1) {
      const step = index + 1;
      largest = Math.max(largest, flips[index]);
      if (largest === step) {
        count += 1;
      }
    }
    return count;
  }
}
