class Solution {
  plusOne(digits) {
    for (let index = digits.length - 1; index >= 0; index -= 1) {
      if (digits[index] < 9) {
        digits[index] += 1;
        return digits;
      }
      digits[index] = 0;
    }
    digits.unshift(1);
    return digits;
  }
}
