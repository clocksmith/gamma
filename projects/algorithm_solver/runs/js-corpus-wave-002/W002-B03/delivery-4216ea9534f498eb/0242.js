function isAnagram(s, t) {
  if (s.length !== t.length) return false;
  const counts = new Map();
  for (const char of s) counts.set(char, (counts.get(char) || 0) + 1);
  for (const char of t) { const count = counts.get(char) || 0; if (!count) return false; counts.set(char, count - 1); }
  return true;
}
