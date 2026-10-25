function greatestCommonDivisor(left, right) {
  while (right !== 0) {
    const remainder = left % right;
    left = right;
    right = remainder;
  }
  return left;
}

class Solution {
  hasGroupsSizeX(deck) {
    if (deck.length === 0) {
      return false;
    }

    const counts = new Map();
    for (const value of deck) {
      counts.set(value, (counts.get(value) || 0) + 1);
    }
    let common = 0;
    for (const count of counts.values()) {
      common = greatestCommonDivisor(common, count);
      if (common === 1) {
        return false;
      }
    }
    return common >= 2;
  }
}
