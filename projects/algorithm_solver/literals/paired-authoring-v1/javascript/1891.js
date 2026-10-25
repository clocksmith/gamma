class Solution {
  maxLength(ribbons, k) {
    let low = 0;
    let high = 0;
    for (const ribbon of ribbons) {
      high = Math.max(high, ribbon);
    }
    while (low < high) {
      const length = low + Math.floor((high - low + 1) / 2);
      let pieces = 0;
      for (const ribbon of ribbons) {
        pieces += Math.floor(ribbon / length);
        if (pieces >= k) {
          break;
        }
      }
      if (pieces >= k) {
        low = length;
      } else {
        high = length - 1;
      }
    }
    return low;
  }
}
