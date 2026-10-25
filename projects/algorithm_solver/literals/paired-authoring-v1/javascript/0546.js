class Solution {
  removeBoxes(boxes) {
    const memo = new Map();

    function score(left, right, joined) {
      if (left > right) {
        return 0;
      }
      const key = left + "," + right + "," + joined;
      if (memo.has(key)) {
        return memo.get(key);
      }
      while (left < right && boxes[right] === boxes[right - 1]) {
        right -= 1;
        joined += 1;
      }

      const group = joined + 1;
      let best = score(left, right - 1, 0) + group * group;
      for (let index = left; index < right; index += 1) {
        if (boxes[index] === boxes[right]) {
          const candidate = score(left, index, group) + score(index + 1, right - 1, 0);
          best = Math.max(best, candidate);
        }
      }
      memo.set(key, best);
      return best;
    }

    return score(0, boxes.length - 1, 0);
  }
}
