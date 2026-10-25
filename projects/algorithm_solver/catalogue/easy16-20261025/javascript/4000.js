function solve(n, s) {
  // O(n) time and O(1) auxiliary space; n <= 5 gives exact Number arithmetic.
  if (s > 9 * n) return -1;
  let answer = 0;
  for (let index = 0; index < n; index++) {
    const digit = Math.min(9, s);
    answer = 10 * answer + digit;
    s -= digit;
  }
  return answer;
}
