function groupStrings(strings) {
  const groups = new Map();
  for (const word of strings) {
    const offsets = [];
    for (let i = 1; i < word.length; i++) offsets.push((word.charCodeAt(i) - word.charCodeAt(i - 1) + 26) % 26);
    const key = JSON.stringify(offsets);
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(word);
  }
  return [...groups.values()];
}
