class Solution {
  countArrangement(n) {
    const used = new Array(n + 1).fill(false);

    function count_from(position) {
      if (position > n) {
        return 1;
      }
      let total = 0;
      for (let value = 1; value <= n; value += 1) {
        if (used[value] || (value % position !== 0 && position % value !== 0)) {
          continue;
        }
        used[value] = true;
        total += count_from(position + 1);
        used[value] = false;
      }
      return total;
    }

    return count_from(1);
  }
}
