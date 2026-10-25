class Solution {
  clumsy(n) {
    function productGroup(first) {
      if (first >= 3) return Math.floor(first * (first - 1) / (first - 2));
      return first;
    }

    let total = productGroup(n);
    let current = n - 3;
    while (current >= 1) {
      total += current;
      current -= 1;
      if (current >= 1) {
        total -= productGroup(current);
        current -= 3;
      }
    }
    return total;
  }
}
