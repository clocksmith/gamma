class Solution {
  monotoneIncreasingDigits(n) {
    const digits = String(n).split("");
    let boundary = digits.length;
    for (let index = digits.length - 1; index > 0; index -= 1) {
      if (digits[index - 1] > digits[index]) {
        digits[index - 1] = String(Number(digits[index - 1]) - 1);
        boundary = index;
      }
    }
    for (let index = boundary; index < digits.length; index += 1) {
      digits[index] = "9";
    }
    return Number(digits.join(""));
  }
}
