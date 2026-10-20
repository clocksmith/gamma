function lengthOfLongestSubstringKDistinct(s, k) {
  if (k <= 0) return 0;
  const counts = new Map();
  let left = 0;
  let longest = 0;

  for (let right = 0; right < s.length; right++) {
    const character = s[right];
    counts.set(character, (counts.get(character) || 0) + 1);
    while (counts.size > k) {
      const removed = s[left++];
      const remaining = counts.get(removed) - 1;
      if (remaining === 0) counts.delete(removed);
      else counts.set(removed, remaining);
    }
    longest = Math.max(longest, right - left + 1);
  }
  return longest;
}
