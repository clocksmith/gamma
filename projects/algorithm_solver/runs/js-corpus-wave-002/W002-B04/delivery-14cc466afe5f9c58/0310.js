function findMinHeightTrees(n, edges) {
  if (n <= 1) return n === 1 ? [0] : [];
  const adjacency = Array.from({ length: n }, () => []);
  const degree = Array(n).fill(0);
  for (const [a, b] of edges) {
    adjacency[a].push(b); adjacency[b].push(a); degree[a]++; degree[b]++;
  }
  let leaves = [];
  for (let node = 0; node < n; node++) if (degree[node] === 1) leaves.push(node);
  let remaining = n;
  while (remaining > 2) {
    remaining -= leaves.length;
    const next = [];
    for (const leaf of leaves) for (const neighbor of adjacency[leaf]) {
      degree[neighbor]--;
      if (degree[neighbor] === 1) next.push(neighbor);
    }
    leaves = next;
  }
  return leaves;
}
