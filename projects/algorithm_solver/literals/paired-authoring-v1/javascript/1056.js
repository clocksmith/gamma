class Solution {
  confusingNumber(number) {
    const rotation = new Map([["0", "0"], ["1", "1"], ["6", "9"], ["8", "8"], ["9", "6"]]);
    const original = number.toString();
    const digits = [];
    for (let index = original.length - 1; index >= 0; index -= 1) {
      const digit = original[index];
      if (!rotation.has(digit)) {
        return false;
      }
      digits.push(rotation.get(digit));
    }
    const rotated = digits.join("").replace(/^0+/, "") || "0";
    return rotated !== original;
  }
}
