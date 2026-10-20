function alienOrder(words) {
  const graph = new Map(), indegree = new Map();
  for (const word of words) for (const char of word) { if (!graph.has(char)) graph.set(char, new Set()); indegree.set(char, 0); }
  for (let i = 1; i < words.length; i++) {
    const before = words[i - 1], after = words[i];
    if (before.length > after.length && before.startsWith(after)) return '';
    for (let j = 0; j < Math.min(before.length, after.length); j++) {
      if (before[j] === after[j]) continue;
      if (!graph.get(before[j]).has(after[j])) { graph.get(before[j]).add(after[j]); indegree.set(after[j], indegree.get(after[j]) + 1); }
      break;
    }
  }
  const queue = [];
  for (const [char, degree] of indegree) if (!degree) queue.push(char);
  let head = 0, result = '';
  while (head < queue.length) {
    const char = queue[head++]; result += char;
    for (const next of graph.get(char)) {
      indegree.set(next, indegree.get(next) - 1);
      if (indegree.get(next) === 0) queue.push(next);
    }
  }
  return result.length === indegree.size ? result : '';
}
