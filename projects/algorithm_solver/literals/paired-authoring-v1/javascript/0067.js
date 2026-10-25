class Solution {
  addBinary(a, b) {
    let left = a.length - 1;
    let right = b.length - 1;
    let carry = 0;
    const digits = [];
    while (left >= 0 || right >= 0 || carry > 0) {
      let total = carry;
      if (left >= 0) {
        total += a[left] === "1" ? 1 : 0;
        left -= 1;
      }
      if (right >= 0) {
        total += b[right] === "1" ? 1 : 0;
        right -= 1;
      }
      digits.push(total % 2 === 1 ? "1" : "0");
      carry = Math.floor(total / 2);
    }
    digits.reverse();
    return digits.join("");
  }
}
