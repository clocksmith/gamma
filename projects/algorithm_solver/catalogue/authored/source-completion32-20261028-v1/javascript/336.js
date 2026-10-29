// 336 — Palindrome Pairs. Original implementation; authored candidate, not independently qualified.
function solve(words) {
  function boundaries(word) {
    const n = word.length, prefix = Array(n+1).fill(false), suffix = Array(n+1).fill(false);
    prefix[0] = suffix[n] = true;
    for (const even of [false,true]) {
      const radius = Array(n).fill(0); let left = 0, right = -1;
      for (let i = 0; i < n; i++) {
        let k = i > right ? (even ? 0 : 1) : Math.min(radius[left + right - i + Number(even)], right - i + 1);
        while (i - k - Number(even) >= 0 && i + k < n && word[i-k-Number(even)] === word[i+k]) k++;
        radius[i] = k;
        const start = i-k+Number(!even), end = i+k-1;
        if (start === 0) prefix[end+1] = true;
        if (end === n-1) suffix[start] = true;
        if (end > right) { left = start; right = end; }
      }
    }
    return [prefix,suffix];
  }
  const make = () => ({children:new Map(), end:-1, pal:[]}), root = make(), flags = [];
  words.forEach((word,index) => {
    const [prefix,suffix] = boundaries(word); flags.push(suffix); let current = root;
    for (let j = word.length-1; j >= 0; j--) {
      if (prefix[j+1]) current.pal.push(index);
      if (!current.children.has(word[j])) current.children.set(word[j],make());
      current = current.children.get(word[j]);
    }
    current.end = index; current.pal.push(index);
  });
  const result = [];
  words.forEach((word,index) => {
    let current = root;
    for (let j = 0; j < word.length; j++) {
      if (current.end >= 0 && current.end !== index && flags[index][j]) result.push([index,current.end]);
      current = current.children.get(word[j]); if (!current) return;
    }
    for (const other of current.pal) if (other !== index) result.push([index,other]);
  });
  return result;
}

module.exports = { solve, palindromePairs: solve };
