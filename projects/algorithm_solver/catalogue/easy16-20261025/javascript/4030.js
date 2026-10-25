function solve(s) {
  // O(n) time and O(1) space; compare all eight bits, including leading zeros.
  const bitCount = 8 * s.length;
  for (let left = 0; left < bitCount / 2; left++) {
    const right = bitCount - left - 1;
    const leftBit = (s.charCodeAt(Math.floor(left / 8)) >> (7 - left % 8)) & 1;
    const rightBit = (s.charCodeAt(Math.floor(right / 8)) >> (7 - right % 8)) & 1;
    if (leftBit !== rightBit) return false;
  }
  return true;
}
