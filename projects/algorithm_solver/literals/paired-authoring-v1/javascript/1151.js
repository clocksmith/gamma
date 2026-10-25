class Solution {
  minSwaps(data) {
    let width = 0;
    for (const value of data) {
      width += value;
    }
    if (width <= 1) {
      return 0;
    }
    let ones = 0;
    let best = 0;
    for (let index = 0; index < data.length; index += 1) {
      ones += data[index];
      if (index >= width) {
        ones -= data[index - width];
      }
      if (index + 1 >= width) {
        best = Math.max(best, ones);
      }
    }
    return width - best;
  }
}
