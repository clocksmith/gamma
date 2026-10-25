class Solution {
  findKthBit(n, k) {
    let inverted = false;
    while (n > 1) {
      const middle = 2 ** (n - 1);
      if (k === middle) {
        return inverted ? "0" : "1";
      }
      if (k > middle) {
        k = 2 * middle - k;
        inverted = !inverted;
      }
      n -= 1;
    }
    return inverted ? "1" : "0";
  }
}
