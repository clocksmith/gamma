function firstUniqChar(s) {
  const counts = new Map();
  for (const character of s) counts.set(character, (counts.get(character) || 0) + 1);
  for (let index = 0; index < s.length; index++) {
    if (counts.get(s[index]) === 1) return index;
  }
  return -1;
}
