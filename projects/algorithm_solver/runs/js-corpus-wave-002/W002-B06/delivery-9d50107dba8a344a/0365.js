function canMeasureWater(x, y, target) {
  if (target === 0) return true;
  if (target > x + y) return false;

  function gcd(left, right) {
    while (right !== 0) {
      const remainder = left % right;
      left = right;
      right = remainder;
    }
    return left;
  }

  const divisor = gcd(x, y);
  return divisor !== 0 && target % divisor === 0;
}
