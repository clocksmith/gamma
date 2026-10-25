class Solution {
  baseNeg2(n) {
    if (n === 0) return "0";
    const digits = [];
    let value = n;
    while (value !== 0) {
      const remainder = ((value % 2) + 2) % 2;
      digits.push(String(remainder));
      value = (value - remainder) / -2;
    }
    digits.reverse();
    return digits.join("");
  }
}
