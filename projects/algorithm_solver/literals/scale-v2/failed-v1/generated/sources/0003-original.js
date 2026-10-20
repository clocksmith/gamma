function lengthOfLongestSubstring(s) {
  const lastSeen = new Map();
  let leftIndex = 0;
  let index = 0;
  let maximumLength = 0;

  // Iteration counts Unicode code points, not UTF-16 code units.
  for (const character of s) {
    const previousIndex = lastSeen.get(character);
    if (previousIndex !== undefined && previousIndex >= leftIndex) {
      leftIndex = previousIndex + 1;
    }
    lastSeen.set(character, index);
    maximumLength = Math.max(maximumLength, index - leftIndex + 1);
    index++;
  }
  return maximumLength;
}
