class Solution {
  shortestAlternatingPaths(n, redEdges, blueEdges) {
    const edges = Array.from({length: 2}, () => Array.from({length: n}, () => []));
    for (const [first, second] of redEdges) {
      edges[0][first].push(second);
    }
    for (const [first, second] of blueEdges) {
      edges[1][first].push(second);
    }
    const distance = Array.from({length: n}, () => [-1, -1]);
    distance[0] = [0, 0];
    const queue = [[0, 0], [0, 1]];
    let head = 0;
    while (head < queue.length) {
      const [node, previousColor] = queue[head];
      head += 1;
      const nextColor = 1 - previousColor;
      for (const neighbor of edges[nextColor][node]) {
        if (distance[neighbor][nextColor] === -1) {
          distance[neighbor][nextColor] = distance[node][previousColor] + 1;
          queue.push([neighbor, nextColor]);
        }
      }
    }
    const output = [];
    for (const [redDistance, blueDistance] of distance) {
      if (redDistance === -1) {
        output.push(blueDistance);
      } else if (blueDistance === -1) {
        output.push(redDistance);
      } else {
        output.push(Math.min(redDistance, blueDistance));
      }
    }
    return output;
  }
}
