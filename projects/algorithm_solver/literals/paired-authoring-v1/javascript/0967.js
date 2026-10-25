class Solution {
  numsSameConsecDiff(n, k) {
    let prefixes = [1, 2, 3, 4, 5, 6, 7, 8, 9];
    for (let length = 1; length < n; length += 1) {
      const following = [];
      for (const prefix of prefixes) {
        const last = prefix % 10;
        const lower = last - k;
        const upper = last + k;
        if (lower >= 0) following.push(prefix * 10 + lower);
        if (k !== 0 && upper <= 9) following.push(prefix * 10 + upper);
      }
      prefixes = following;
    }
    return prefixes;
  }
}
