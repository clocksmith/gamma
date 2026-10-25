function isSelfDividing(value) {
  let remaining = value;
  while (remaining > 0) {
    const digit = remaining % 10;
    if (digit === 0 || value % digit !== 0) {
      return false;
    }
    remaining = Math.floor(remaining / 10);
  }
  return true;
}

class Solution {
  selfDividingNumbers(left, right) {
    const result = [];
    for (let value = left; value <= right; value += 1) {
      if (isSelfDividing(value)) {
        result.push(value);
      }
    }
    return result;
  }
}
