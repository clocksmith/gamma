class Solution {
  grayCode(n) {
    const codes = [0];
    let bit = 1;
    for (let step = 0; step < n; step += 1) {
      for (let index = codes.length - 1; index >= 0; index -= 1) {
        codes.push(bit + codes[index]);
      }
      bit *= 2;
    }
    return codes;
  }
}
