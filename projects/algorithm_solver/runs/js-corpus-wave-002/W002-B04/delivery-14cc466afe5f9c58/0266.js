function canPermutePalindrome(s) {
  const odd = new Set();
  for (const char of s) { if (odd.has(char)) odd.delete(char); else odd.add(char); }
  return odd.size <= 1;
}
