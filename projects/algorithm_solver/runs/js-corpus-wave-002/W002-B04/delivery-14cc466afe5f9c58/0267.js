function generatePalindromes(s) {
  const counts = new Map();
  for (const char of s) counts.set(char, (counts.get(char) || 0) + 1);
  let middle = '';
  const half = [];
  for (const [char, count] of counts) {
    if (count % 2) { if (middle) return []; middle = char; }
    for (let i = 0; i < Math.floor(count / 2); i++) half.push(char);
  }
  half.sort();
  const result = [], used = Array(half.length).fill(false);
  function search(path) {
    if (path.length === half.length) {
      const left = path.join('');
      result.push(left + middle + [...path].reverse().join(''));
      return;
    }
    for (let i = 0; i < half.length; i++) {
      if (used[i] || (i > 0 && half[i] === half[i - 1] && !used[i - 1])) continue;
      used[i] = true; path.push(half[i]); search(path); path.pop(); used[i] = false;
    }
  }
  search([]);
  return result;
}
