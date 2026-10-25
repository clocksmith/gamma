function solve(s) {
  // O(n) time and O(1) space; count nonempty rearrangeable prefixes.
  let balance = 0;
  let answer = 0;
  for (const character of s) {
    balance += character === "1" ? 1 : -1;
    if (Math.abs(balance) <= 1) answer++;
  }
  return answer;
}
