class Solution {
  getAncestors(n, edges) {
    const neighbors = Array.from({length: n}, () => []);
    const indegree = Array(n).fill(0);
    for (const [first, second] of edges) {
      neighbors[first].push(second);
      indegree[second] += 1;
    }
    const ancestors = Array.from({length: n}, () => new Set());
    const queue = [];
    for (let node = 0; node < n; node += 1) {
      if (indegree[node] === 0) {
        queue.push(node);
      }
    }
    let head = 0;
    while (head < queue.length) {
      const node = queue[head];
      head += 1;
      for (const neighbor of neighbors[node]) {
        ancestors[neighbor].add(node);
        for (const ancestor of ancestors[node]) {
          ancestors[neighbor].add(ancestor);
        }
        indegree[neighbor] -= 1;
        if (indegree[neighbor] === 0) {
          queue.push(neighbor);
        }
      }
    }
    return ancestors.map(group => Array.from(group).sort((first, second) => first - second));
  }
}
