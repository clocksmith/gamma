function lengthOfLongestSubstringTwoDistinct(s) {
  const counts = new Map();
  let left = 0;
  let best = 0;

  for (let right = 0; right < s.length; right += 1) {
    const character = s[right];
    counts.set(character, (counts.get(character) ?? 0) + 1);

    while (counts.size > 2) {
      const removed = s[left];
      const nextCount = counts.get(removed) - 1;
      if (nextCount === 0) {
        counts.delete(removed);
      } else {
        counts.set(removed, nextCount);
      }
      left += 1;
    }

    best = Math.max(best, right - left + 1);
  }

  return best;
}
