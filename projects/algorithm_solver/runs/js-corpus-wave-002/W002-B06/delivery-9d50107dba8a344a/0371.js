function getSum(a, b) {
  let left = a | 0;
  let right = b | 0;
  while (right !== 0) {
    const carry = (left & right) << 1;
    left ^= right;
    right = carry;
  }
  return left;
}
