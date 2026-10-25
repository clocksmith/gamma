class Solution {
  maximumSwap(num) {
    const digits = String(num).split("");
    const last = new Array(10).fill(-1);
    for (let index = 0; index < digits.length; index += 1) {
      last[Number(digits[index])] = index;
    }
    for (let index = 0; index < digits.length; index += 1) {
      for (let replacement = 9; replacement > Number(digits[index]); replacement -= 1) {
        const other = last[replacement];
        if (other > index) {
          const saved = digits[index];
          digits[index] = digits[other];
          digits[other] = saved;
          return Number(digits.join(""));
        }
      }
    }
    return num;
  }
}
