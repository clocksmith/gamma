class Solution {
  leastBricks(wall) {
    const edges = new Map();
    let aligned = 0;
    for (const row of wall) {
      let offset = 0;
      for (let index = 0; index < row.length - 1; index += 1) {
        offset += row[index];
        edges.set(offset, (edges.get(offset) || 0) + 1);
        aligned = Math.max(aligned, edges.get(offset));
      }
    }
    return wall.length - aligned;
  }
}
