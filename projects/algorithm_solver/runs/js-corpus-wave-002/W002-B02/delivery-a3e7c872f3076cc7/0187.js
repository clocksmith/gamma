function findRepeatedDnaSequences(s) {
  const seen = new Set();
  const repeated = new Set();

  for (let start = 0; start + 10 <= s.length; start += 1) {
    const sequence = s.slice(start, start + 10);
    if (seen.has(sequence)) {
      repeated.add(sequence);
    } else {
      seen.add(sequence);
    }
  }

  return Array.from(repeated);
}
