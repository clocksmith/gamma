class Solution {
  minimumBuckets(hamsters) {
    const cells = Array.from(hamsters);
    let buckets = 0;
    for (let index = 0; index < cells.length; index += 1) {
      if (cells[index] !== "H") {
        continue;
      }
      if (index > 0 && cells[index - 1] === "B") {
        continue;
      }
      if (index + 1 < cells.length && cells[index + 1] === ".") {
        cells[index + 1] = "B";
      } else if (index > 0 && cells[index - 1] === ".") {
        cells[index - 1] = "B";
      } else {
        return -1;
      }
      buckets += 1;
    }
    return buckets;
  }
}
