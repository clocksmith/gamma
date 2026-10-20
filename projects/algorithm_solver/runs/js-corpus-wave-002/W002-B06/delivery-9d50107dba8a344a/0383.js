function canConstruct(ransomNote, magazine) {
  const available = new Map();
  for (const character of magazine) {
    available.set(character, (available.get(character) || 0) + 1);
  }
  for (const character of ransomNote) {
    const count = available.get(character) || 0;
    if (count === 0) return false;
    available.set(character, count - 1);
  }
  return true;
}
