class Solution {
  bitwiseComplement(n) {
    if (n === 0) return 1;
    let boundary = 1;
    while (boundary <= n) boundary *= 2;
    return boundary - 1 - n;
  }
}
