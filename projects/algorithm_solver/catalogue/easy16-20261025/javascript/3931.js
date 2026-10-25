function solve(s) {
  // O(n) time and O(1) auxiliary space; the contract is ASCII digits.
  for (let index = 1; index < s.length; index++) {
    if (Math.abs(s.charCodeAt(index) - s.charCodeAt(index - 1)) > 2) return false;
  }
  return true;
}
